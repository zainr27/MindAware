# Initial Demo Program for BCI Drone Control
# Uses two-head approach (focus_head.joblib + not_focus detection) for higher accuracy
# Sequence: Focus 1 → takeoff → wait 8s → Not_focus 2 → land → wait 5s → Not_focus 3 → fland → end

import os, time, json
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import joblib
from collections import deque
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes
import asyncio
import websockets
import threading

# Basic Authentication credentials
AUTH_USERNAME = "BCITeam"
AUTH_PASSWORD = "DronesRCool"

# ===== Settings =====
WINDOW_SEC = 1.2
STEP_SEC = 0.20
PRINT_EVERY_SEC = 0.5
EMA_TAU = 1.0
VOTE_SEC = 1.5

# Two-head model paths
FOCUS_MODEL_PATH = "focus_head.joblib"
YAW_MODEL_PATH = "yaw_head.joblib"
FOCUS_FEATURES_JSON = "focus_features.json"
YAW_FEATURES_JSON = "yaw_features.json"
FOCUS_CLASSES_JSON = "focus_classes.json"
YAW_CLASSES_JSON = "yaw_classes.json"

# Drone control (will be set by user input)
DRONE_BASE_URL = None

# WebSocket settings for visualization broadcasting
WS_HOST = "127.0.0.1"
WS_PORT = 8766  # Different port from main web interface
WS_CLIENTS = set()
BROADCAST_SUCCESSFUL_ONLY = True  # Only broadcast successful BCI controls

# ===== DSP Helpers =====
def moving_average_abs(x, sr, win_sec):
    w = max(1, int(win_sec * sr))
    if w <= 1: return np.abs(x)
    kernel = np.ones(w) / w
    return np.convolve(np.abs(x), kernel, mode='same')

def robust_threshold(env, k=4.5):
    med = float(np.median(env))
    mad = float(np.median(np.abs(env - med))) + 1e-9
    return med + k * mad

def band_rms(sig, sr, f_lo, f_hi):
    x = sig.astype(np.float64).copy()
    DataFilter.perform_bandpass(x, sr, f_lo, f_hi, 4, FilterTypes.BUTTERWORTH.value, 0)
    try:
        DataFilter.perform_bandstop(x, sr, 59.0, 61.0, 2, FilterTypes.BUTTERWORTH.value, 0)
    except:
        pass
    return float(np.mean(x * x))

def find_segments(mask):
    m = mask.astype(np.int32)
    starts = np.where(np.diff(np.concatenate(([0], m))) == 1)[0]
    ends = np.where(np.diff(np.concatenate((m, [0]))) == -1)[0]
    return list(zip(starts, ends))

# ===== Feature Extractor =====
class FeatureExtractor:
    def __init__(self, sr, eeg_chs, blink_pair, yaw_pair):
        self.sr = sr
        self.eeg_chs = eeg_chs
        self.blink_pair = blink_pair
        self.yaw_pair = yaw_pair
        self._blink = {"peaks": [], "last": -1e9}
        self._blink_env_win = 0.02
        self._yaw_neutral = None

    def _sum_band(self, win, lo, hi):
        return sum(band_rms(win[ch, :], self.sr, lo, hi) for ch in self.eeg_chs)

    def _blink_metrics(self, win):
        now = time.time()
        L, R = self.blink_pair
        x = win[L, :].astype(np.float64) + win[R, :].astype(np.float64)
        try:
            DataFilter.perform_bandpass(x, self.sr, 0.5, 8.0, 2, FilterTypes.BUTTERWORTH.value, 0)
        except:
            pass
        
        env = moving_average_abs(x, self.sr, self._blink_env_win)
        blink_env95 = float(np.percentile(env, 95))
        thr = robust_threshold(env)
        mask = env > thr
        segs = find_segments(mask)
        
        tail_start = now - len(x) / self.sr
        last = self._blink["last"]
        new_peaks = []
        
        for s, e in segs:
            dur = (e - s) / self.sr
            if 0.05 <= dur <= 0.25:  # Valid blink duration
                p = s + int(np.argmax(env[s:e]))
                t = tail_start + p / self.sr
                if t - last >= 0.10:  # Minimum gap between blinks
                    new_peaks.append(t)
                    last = t
        
        if new_peaks:
            self._blink["last"] = new_peaks[-1]
        
        # Update peak history
        hist = [t for t in self._blink.get("peaks", []) if now - t <= 0.5]
        hist += new_peaks
        hist.sort()
        self._blink["peaks"] = hist
        
        blink_rate = len(hist) / 0.5
        return blink_env95, blink_rate

    def _yaw_centered(self, win):
        L = win[self.yaw_pair[0], :].astype(np.float64).copy()
        R = win[self.yaw_pair[1], :].astype(np.float64).copy()
        try:
            DataFilter.perform_lowpass(L, self.sr, 4.0, 2, FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_lowpass(R, self.sr, 4.0, 2, FilterTypes.BUTTERWORTH.value, 0)
        except:
            pass
        
        sig = L - R
        k = max(1, int(0.1 * len(sig)))
        center = np.mean(np.sort(sig)[k:-k]) if len(sig) > 2 * k else np.mean(sig)
        
        if self._yaw_neutral is None:
            self._yaw_neutral = center
        self._yaw_neutral = 0.98 * self._yaw_neutral + 0.02 * center
        return float(center - self._yaw_neutral)

    def compute_all(self, win):
        alpha = self._sum_band(win, 8.0, 12.0)
        beta = self._sum_band(win, 13.0, 30.0) 
        theta = self._sum_band(win, 4.0, 7.0)
        focus_ratio = beta / max(alpha, 1e-9)
        blink_env95, blink_rate = self._blink_metrics(win)
        yaw_c = self._yaw_centered(win)
        notch = band_rms(win[self.eeg_chs[0], :], self.sr, 59.0, 61.0)
        
        return {
            "focus_ratio": float(focus_ratio),
            "blink_env95": float(blink_env95),
            "blink_rate_0_5": float(blink_rate),
            "yaw_centered": float(yaw_c),
            "yaw_abs": float(abs(yaw_c)),
            "alpha_sum": float(alpha),
            "beta_sum": float(beta),
            "theta_sum": float(theta),
            "notch_resid": float(notch)
        }

# ===== Drone Control =====
def send_drone_command(endpoint):
    url = f"{DRONE_BASE_URL}{endpoint}"
    auth = HTTPBasicAuth(AUTH_USERNAME, AUTH_PASSWORD)
    try:
        print(f"\n🚁 Sending: {url} (with auth)")
        response = requests.get(url, auth=auth, timeout=5)
        print(f"✅ Response: {response.status_code} - {response.text}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

# ===== Probability Smoothing =====
class ProbEMA:
    def __init__(self, tau=EMA_TAU):
        self.tau = max(1e-3, tau)
        self.probs = None
        self.last_time = None

    def update(self, new_probs):
        now = time.time()
        if self.probs is None:
            self.probs = new_probs.astype(float)
            self.last_time = now
            return self.probs
        
        dt = max(1e-3, now - self.last_time)
        alpha = 1 - np.exp(-dt / self.tau)
        self.probs = (1 - alpha) * self.probs + alpha * new_probs
        self.last_time = now
        return self.probs

def get_drone_url():
    """Get drone base URL from user and ensure proper http:// formatting"""
    print("\nDrone Connection Setup")
    print("Enter the drone's base URL (default: 192.168.86.139:8080):")
    print("Press Enter for default, or type custom URL (e.g., 192.168.86.139:8080 or http://192.168.86.139:8080):")
    
    while True:
        user_input = input("> ").strip()
        
        # Use default if user enters nothing
        if not user_input:
            formatted_url = "http://192.168.86.139:8080"
            print(f"Using default drone URL: {formatted_url}")
            return formatted_url
            
        # Remove any existing http:// or https://
        if user_input.startswith("http://"):
            clean_url = user_input[7:]
        elif user_input.startswith("https://"):
            clean_url = user_input[8:]
        else:
            clean_url = user_input
            
        # Ensure we have a properly formatted URL
        formatted_url = f"http://{clean_url}"
        
        # Basic validation
        if ":" not in clean_url:
            print("URL should include port (e.g., 192.168.86.139:8080)")
            continue
            
        print(f"Using drone URL: {formatted_url}")
        return formatted_url

def autodetect_forehead_pair(board, sr, eeg_chs):
    print("\nBlink hard 3-4 times in ~8s to detect electrodes...")
    time.sleep(0.4)
    data = board.get_current_board_data(int(8.0 * sr))
    while data.shape[1] < int(0.8 * sr):
        time.sleep(0.1)
        data = board.get_current_board_data(int(8.0 * sr))
    
    scores = []
    for ch in eeg_chs:
        x = data[ch, :].astype(np.float64).copy()
        try:
            DataFilter.perform_bandpass(x, sr, 0.5, 8.0, 2, FilterTypes.BUTTERWORTH.value, 0)
        except:
            pass
        env = moving_average_abs(x, sr, 0.02)
        scores.append((np.percentile(env, 95), ch))
    
    scores.sort(reverse=True)
    return (scores[0][1], scores[1][1]) if len(scores) >= 2 else (eeg_chs[0], eeg_chs[1] if len(eeg_chs) > 1 else eeg_chs[0])

# ===== WebSocket Broadcasting =====
async def handle_websocket(websocket):
    """Handle new WebSocket connections"""
    WS_CLIENTS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        WS_CLIENTS.discard(websocket)

async def broadcast_data(data):
    """Broadcast data to all connected WebSocket clients"""
    if WS_CLIENTS:
        dead_clients = []
        for client in list(WS_CLIENTS):
            try:
                await client.send(json.dumps(data))
            except:
                dead_clients.append(client)
        
        # Remove dead connections
        for client in dead_clients:
            WS_CLIENTS.discard(client)

def start_websocket_server():
    """Start WebSocket server in a separate thread"""
    async def run_server():
        server = await websockets.serve(handle_websocket, WS_HOST, WS_PORT)
        print(f"WebSocket server started at ws://{WS_HOST}:{WS_PORT}")
        print(f"Open http://127.0.0.1:8765/ai_index.html in browser for visualization")
        await server.wait_closed()
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_server())
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    return thread

# ===== Main Test Sequence =====
def main():
    global DRONE_BASE_URL
    
    print("BCI Initial Demo Program Starting...")
    print("=" * 50)
    
    # Get drone URL from user first
    DRONE_BASE_URL = get_drone_url()
    
    print("\nInstructions (ALL COMMANDS USE FOCUS):")
    print("  Step 1: FOCUS intensely to trigger takeoff")
    print("  Step 2: FOCUS intensely to start yaw movement")
    print("  Step 3: Wait 10 seconds for automatic yaw center")
    print("  Step 4: FOCUS intensely to trigger landing")
    print("  Step 5: FOCUS intensely to trigger force landing")
    print()
    
    # Load two-head models
    if not os.path.exists(FOCUS_MODEL_PATH):
        raise FileNotFoundError(f"Missing {FOCUS_MODEL_PATH}. Run ai_train_bci_skylearn.py first.")
    
    focus_pipe = joblib.load(FOCUS_MODEL_PATH)
    yaw_pipe = joblib.load(YAW_MODEL_PATH)
    focus_feats = json.load(open(FOCUS_FEATURES_JSON))
    yaw_feats = json.load(open(YAW_FEATURES_JSON))
    focus_classes = json.load(open(FOCUS_CLASSES_JSON))
    yaw_classes = json.load(open(YAW_CLASSES_JSON))
    print(f"Loaded two-head models. Focus: {focus_classes}, Yaw: {yaw_classes}")
    
    # BrainFlow setup
    BoardShim.enable_dev_board_logger()
    params = BrainFlowInputParams()
    board_id = BoardIds.GANGLION_NATIVE_BOARD.value
    board = BoardShim(board_id, params)
    board.prepare_session()
    board.start_stream()
    
    sr = BoardShim.get_sampling_rate(board_id)
    eeg_chs = BoardShim.get_eeg_channels(board_id)
    need = max(int(WINDOW_SEC * sr), 256)
    print(f"EEG OK: {len(eeg_chs)} channels @ {sr} Hz")
    
    print("\nCalibrating... stay still for 10 seconds...")
    time.sleep(10.0)
    
    fp1, fp2 = autodetect_forehead_pair(board, sr, eeg_chs)
    yaw_pair = (fp1, fp2)
    print(f"Using electrode pair: {yaw_pair}")
    
    fx = FeatureExtractor(sr, eeg_chs, (fp1, fp2), yaw_pair)
    
    # Two-head smoothing
    focus_ema = ProbEMA()
    yaw_ema = ProbEMA()
    vote_focus = deque(maxlen=int(VOTE_SEC/STEP_SEC))
    vote_yaw = deque(maxlen=int(VOTE_SEC/STEP_SEC))
    
    # Demo sequence state
    sequence_step = 0
    step_names = ["TAKEOFF", "YAW RIGHT", "YAW CENTER", "LAND", "FLAND"]
    endpoints = ["/takeoff", "/send_control?vertical=0&yaw=0.1&pitch=0", "/send_control?vertical=0&yaw=0&pitch=0", "/land", "/fland"]
    wait_times = [5, 10, 2, 5, 0]  # Wait times after each command (LAND has 5s wait before FLAND)
    
    # Using /send_control endpoint for continuous yaw control
    # /send_control?vertical=<float>&yaw=<float>&pitch=<float>
    # - vertical: positive = up, negative = down
    # - yaw: positive = right, negative = left  
    # - pitch: must be positive (forward movement only)
    
    last_command_time = 0
    command_cooldown = 2.0  # Minimum seconds between command detections
    
    print("SEQUENCE: Starting BCI detection...")
    print("Double blink clearly to trigger commands...")
    
    # Start WebSocket server for visualization
    broadcast_mode = "successful BCI controls only" if BROADCAST_SUCCESSFUL_ONLY else "continuous monitoring"
    print(f"Broadcasting mode: {broadcast_mode}")
    ws_thread = start_websocket_server()
    time.sleep(1)  # Give server time to start
    
    last_print = 0.0
    
    try:
        while sequence_step < len(step_names):
            data = board.get_current_board_data(need)
            if data.shape[1] < need:
                time.sleep(0.01)
                continue
            
            win = data[:, -need:]
            feats = fx.compute_all(win)
            
            # Focus/Not_focus detection for command triggering
            x_focus = np.array([[feats[k] for k in focus_feats]], dtype=np.float32)
            if hasattr(focus_pipe, "predict_proba"):
                pf = focus_pipe.predict_proba(x_focus)[0]
            else:
                idxf = int(focus_pipe.predict(x_focus)[0])
                pf = np.zeros(2, dtype=np.float32)
                pf[idxf] = 1.0
            
            pf = focus_ema.update(pf)
            vote_focus.append(int(np.argmax(pf)))
            focus_idx = max(set(vote_focus), key=vote_focus.count)
            focus_label = focus_classes[focus_idx]
            focus_confidence = float(pf[focus_idx])
            
            current_time = time.time()
            
            # Get yaw detection for step 2
            x_yaw = np.array([[feats[k] for k in yaw_feats]], dtype=np.float32)
            if hasattr(yaw_pipe, "predict_proba"):
                py = yaw_pipe.predict_proba(x_yaw)[0]
            else:
                idxy = int(yaw_pipe.predict(x_yaw)[0])
                py = np.zeros(2, dtype=np.float32)
                py[idxy] = 1.0
            
            yaw_idx = int(np.argmax(py))
            yaw_label = yaw_classes[yaw_idx]
            yaw_confidence = float(py[yaw_idx])
            
            # Command detection logic based on sequence step (ALL SET TO FOCUS)
            command_detected = False
            if sequence_step == 0:  # Waiting for TAKEOFF (focus command)
                command_detected = (focus_label == "focus" and 
                                  focus_confidence > 0.7 and
                                  current_time - last_command_time > command_cooldown)
            elif sequence_step == 1:  # Waiting for YAW RIGHT (changed to focus)
                command_detected = (focus_label == "focus" and 
                                  focus_confidence > 0.7 and
                                  current_time - last_command_time > command_cooldown)
            elif sequence_step == 2:  # YAW CENTER (automatic after 10 second wait)
                command_detected = True  # Will be triggered after wait time
            elif sequence_step == 3:  # Waiting for LAND (changed to focus)
                command_detected = (focus_label == "focus" and 
                                  focus_confidence > 0.7 and
                                  current_time - last_command_time > command_cooldown)
            else:  # Waiting for FLAND (changed to focus)
                command_detected = (focus_label == "focus" and 
                                  focus_confidence > 0.7 and
                                  current_time - last_command_time > command_cooldown)
            
            # Broadcast data for visualization (continuous or successful only)
            if not BROADCAST_SUCCESSFUL_ONLY:
                broadcast_msg = {
                    "t": current_time,
                    "armed": True,  # Demo is always "armed"
                    "airborne": sequence_step > 0,  # Airborne after takeoff
                    "label": focus_label,
                    "probs": {focus_classes[0]: float(pf[0]), focus_classes[1]: float(pf[1])},
                    "focus": float(feats["focus_ratio"]),
                    "yaw": float(feats["yaw_centered"]),
                    "blink_rate": float(feats["blink_rate_0_5"]),
                    "battery": None,  # Not available in demo mode
                    "altitude_m": 1.0 if sequence_step > 0 else 0.0,  # Simulated altitude
                    "yaw_deg": None,
                    "executed": "MONITORING",
                    "sequence_step": sequence_step + 1,
                    "step_name": step_names[sequence_step] if sequence_step < len(step_names) else "COMPLETE",
                    "yaw_confidence": yaw_confidence,
                    "focus_confidence": focus_confidence
                }
                
                # Send to WebSocket clients (non-blocking)
                if WS_CLIENTS:
                    try:
                        # Create a new event loop for this thread if needed
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Schedule the broadcast
                        if not loop.is_running():
                            loop.run_until_complete(broadcast_data(broadcast_msg))
                        else:
                            # If loop is running, create a task
                            asyncio.create_task(broadcast_data(broadcast_msg))
                    except:
                        pass  # Ignore WebSocket errors in demo mode
            
            # Status display (removed step x/5 logs for cleaner output)
            # Keeping the timing but removing the print statements
            if current_time - last_print >= PRINT_EVERY_SEC:
                last_print = current_time
            
            # Execute sequence command
            if command_detected:
                if sequence_step == 0:
                    detected_state = "FOCUS"
                elif sequence_step == 1:
                    detected_state = "FOCUS"
                elif sequence_step == 2:
                    detected_state = "CENTER"
                elif sequence_step == 3:
                    detected_state = "FOCUS"
                else:  # sequence_step == 4
                    detected_state = "FOCUS"
                    
                print(f"\nCommand to execute: {step_names[sequence_step]} ({detected_state})")
                
                try:
                    auth = HTTPBasicAuth(AUTH_USERNAME, AUTH_PASSWORD)
                    response = requests.get(f"{DRONE_BASE_URL}{endpoints[sequence_step]}", auth=auth, timeout=3)
                    if response.status_code == 200:
                        # Broadcast successful BCI control (silent)
                        if BROADCAST_SUCCESSFUL_ONLY and WS_CLIENTS:
                            success_msg = {
                                "t": current_time,
                                "armed": True,
                                "airborne": sequence_step > 0,
                                "label": focus_label if sequence_step != 2 else "auto",  # Auto for YAW CENTER
                                "probs": {focus_classes[0]: float(pf[0]), focus_classes[1]: float(pf[1])},
                                "focus": float(feats["focus_ratio"]),
                                "yaw": float(feats["yaw_centered"]),
                                "blink_rate": float(feats["blink_rate_0_5"]),
                                "battery": None,
                                "altitude_m": 1.0 if sequence_step > 0 else 0.0,
                                "yaw_deg": None,
                                "executed": step_names[sequence_step],
                                "sequence_step": sequence_step + 1,
                                "step_name": step_names[sequence_step],
                                "yaw_confidence": yaw_confidence,
                                "focus_confidence": focus_confidence,
                                "bci_trigger": detected_state,
                                "command_success": True
                            }
                            
                            try:
                                try:
                                    loop = asyncio.get_event_loop()
                                except RuntimeError:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                
                                if not loop.is_running():
                                    loop.run_until_complete(broadcast_data(success_msg))
                                else:
                                    asyncio.create_task(broadcast_data(success_msg))
                            except:
                                pass
                        
                        last_command_time = current_time
                        
                        # Wait for specified duration (silent wait)
                        if wait_times[sequence_step] > 0:
                            time.sleep(wait_times[sequence_step])
                        
                        sequence_step += 1
                        
                        # Check if sequence complete
                        if sequence_step >= len(step_names):
                            print("\nInitial demo sequence completed successfully!")
                            break
                            
                    else:
                        print(f"Command failed with status {response.status_code}")
                        
                except requests.RequestException as e:
                    print(f"Connection error: {e}")
            
            time.sleep(max(0, STEP_SEC - 0.005))
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        try:
            board.stop_stream()
            board.release_session()
        except:
            pass
        print("EEG session closed.")

if __name__ == "__main__":
    main()