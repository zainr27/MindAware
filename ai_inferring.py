# live_infer_two_heads.py
# Live predictions combining:
#  - Blink via DSP (event)
#  - Focus via focus_head.joblib (binary)
#  - Yaw via yaw_head.joblib (left/right)
# Final label priority: blink > yaw_(confident) > focus/not_focus

import os, time, json, sys
import numpy as np
from collections import deque
from typing import Tuple
import requests

import joblib
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes

WINDOW_SEC=1.2; STEP_SEC=0.20; PRINT_EVERY_SEC=0.5
EMA_TAU=1.0; VOTE_SEC=1.5

# ---- Small DSP helpers (same as your collector) ----
def moving_average_abs(x,sr,win): 
    w=max(1,int(win*sr)); 
    if w<=1: return np.abs(x)
    return np.convolve(np.abs(x), np.ones(w)/w, "same")
def robust_threshold(env,k=4.5):
    med=float(np.median(env)); mad=float(np.median(np.abs(env-med)))+1e-9
    return med+k*mad
def band_rms(sig,sr,lo,hi):
    x=sig.astype(np.float64).copy()
    DataFilter.perform_bandpass(x,sr,lo,hi,4,FilterTypes.BUTTERWORTH.value,0)
    try: DataFilter.perform_bandstop(x,sr,59.0,61.0,2,FilterTypes.BUTTERWORTH.value,0)
    except: pass
    return float(np.mean(x*x))
def find_segments(mask):
    m=mask.astype(np.int32)
    s=np.where(np.diff(np.concatenate(([0],m)))==1)[0]
    e=np.where(np.diff(np.concatenate((m,[0])))==-1)[0]
    return list(zip(s,e))

class FeatureExtractor:
    def __init__(self,sr,eeg_chs,blink_pair,yaw_pair):
        self.sr=sr; self.eeg_chs=eeg_chs; self.blink_pair=blink_pair; self.yaw_pair=yaw_pair
        self._blink={"peaks":[], "last":-1e9}; self._blink_env_win=0.02; self._yaw_neutral=None
    def _sum_band(self,win,lo,hi): return sum(band_rms(win[ch,:],self.sr,lo,hi) for ch in self.eeg_chs)
    def blink_metrics(self,win):
        now=time.time(); L,R=self.blink_pair
        x=win[L,:].astype(np.float64)+win[R,:].astype(np.float64)
        try: DataFilter.perform_bandpass(x,self.sr,0.5,8.0,2,FilterTypes.BUTTERWORTH.value,0)
        except: pass
        env=moving_average_abs(x,self.sr,self._blink_env_win)
        blink_env95=float(np.percentile(env,95))
        thr=robust_threshold(env); mask=env>thr; segs=find_segments(mask)
        tail=now-len(x)/self.sr; last=self._blink["last"]; add=[]
        for s,e in segs:
            dur=(e-s)/self.sr
            if 0.05<=dur<=0.25:
                p=s+int(np.argmax(env[s:e])); t=tail+p/self.sr
                if t-last>=0.10: add.append(t); last=t
        if add: self._blink["last"]=add[-1]
        hist=[t for t in self._blink["peaks"] if now-t<=0.5]; hist+=add; hist.sort(); self._blink["peaks"]=hist
        blink_rate=len(hist)/0.5
        return blink_env95, blink_rate
    def yaw_centered(self,win):
        L=win[self.yaw_pair[0],:].astype(np.float64).copy()
        R=win[self.yaw_pair[1],:].astype(np.float64).copy()
        try:
            DataFilter.perform_lowpass(L,self.sr,4.0,2,FilterTypes.BUTTERWORTH.value,0)
            DataFilter.perform_lowpass(R,self.sr,4.0,2,FilterTypes.BUTTERWORTH.value,0)
        except: pass
        sig=L-R; k=max(1,int(0.1*len(sig)))
        center=np.mean(np.sort(sig)[k:-k]) if len(sig)>2*k else np.mean(sig)
        if self._yaw_neutral is None: self._yaw_neutral=center
        self._yaw_neutral=0.98*self._yaw_neutral+0.02*center
        return float(center-self._yaw_neutral)
    def compute_all(self,win):
        alpha=self._sum_band(win,8.0,12.0); beta=self._sum_band(win,13.0,30.0); theta=self._sum_band(win,4.0,7.0)
        focus=beta/max(alpha,1e-9)
        b95,brate=self.blink_metrics(win); yawc=self.yaw_centered(win)
        notch=band_rms(win[self.eeg_chs[0],:], self.sr,59.0,61.0)
        return {"focus_ratio":float(focus),"blink_env95":float(b95),"blink_rate_0_5":float(brate),
                "yaw_centered":float(yawc),"alpha_sum":float(alpha),"beta_sum":float(beta),
                "theta_sum":float(theta),"notch_resid":float(notch)}

class ProbEMA:
    def __init__(self,tau=EMA_TAU): self.p=None; self.t=None; self.tau=max(1e-3,tau)
    def update(self,probs):
        now=time.time()
        if self.p is None: self.p=probs.astype(float); self.t=now; return self.p
        dt=max(1e-3, now-self.t); a=1-np.exp(-dt/self.tau)
        self.p=(1-a)*self.p + a*probs; self.t=now; return self.p

def autodetect_forehead_pair(board,sr,eeg_chs):
    print("\n👀 Blink hard 3–4 times in ~3s…"); time.sleep(0.4)
    data=board.get_current_board_data(int(3.0*sr))
    while data.shape[1] < int(0.8*sr):
        time.sleep(0.1); data=board.get_current_board_data(int(3.0*sr))
    scores=[]
    for ch in eeg_chs:
        x=data[ch,:].astype(np.float64).copy()
        try: DataFilter.perform_bandpass(x,sr,0.5,8.0,2,FilterTypes.BUTTERWORTH.value,0)
        except: pass
        env=moving_average_abs(x,sr,0.02); scores.append((np.percentile(env,95), ch))
    scores.sort(reverse=True)
    return (scores[0][1],scores[1][1]) if len(scores)>=2 else (eeg_chs[0],eeg_chs[1] if len(eeg_chs)>1 else eeg_chs[0])

def main():
    # Load models + features
    focus_pipe = joblib.load("focus_head.joblib")
    yaw_pipe   = joblib.load("yaw_head.joblib")
    focus_feats = json.load(open("focus_features.json"))
    yaw_feats   = json.load(open("yaw_features.json"))
    focus_classes = json.load(open("focus_classes.json"))
    yaw_classes   = json.load(open("yaw_classes.json"))
    print("Loaded heads:", focus_classes, yaw_classes)

    # BrainFlow setup
    BoardShim.enable_dev_board_logger()
    params=BrainFlowInputParams(); board_id=BoardIds.SYNTHETIC_BOARD.value
    board=BoardShim(board_id,params); board.prepare_session(); board.start_stream()
    sr=BoardShim.get_sampling_rate(board_id); eeg_chs=BoardShim.get_eeg_channels(board_id)
    need=max(int(WINDOW_SEC*sr),256); print(f"EEG OK: {len(eeg_chs)} ch @ {sr} Hz | {eeg_chs}")
    print("Stay still ~3s…"); time.sleep(3.0)
    fp1,fp2=autodetect_forehead_pair(board,sr,eeg_chs); yaw_pair=(fp1,fp2)
    print("Using forehead pair:", yaw_pair)
    fx=FeatureExtractor(sr,eeg_chs,(fp1,fp2),yaw_pair)

    # Smoothing
    focus_ema = ProbEMA(); yaw_ema = ProbEMA()
    vote_focus = deque(maxlen=int(VOTE_SEC/STEP_SEC))
    vote_yaw   = deque(maxlen=int(VOTE_SEC/STEP_SEC))

    last=0.0
    try:
        while True:
            data=board.get_current_board_data(need)
            if data.shape[1] < need: time.sleep(0.01); continue
            win=data[:, -need:]
            feats=fx.compute_all(win)

            # 1) Blink as an event
            blink_env95, blink_rate = feats["blink_env95"], feats["blink_rate_0_5"]
            blink_event = (blink_rate > 2.0)  # tune threshold based on your stream

            # 2) Focus head (binary)
            x_focus = np.array([[feats[k] for k in focus_feats]], dtype=np.float32)
            if hasattr(focus_pipe, "predict_proba"):
                pf = focus_pipe.predict_proba(x_focus)[0]
            else:
                idxf = int(focus_pipe.predict(x_focus)[0]); pf = np.zeros(2, dtype=np.float32); pf[idxf]=1.0
            pf = focus_ema.update(pf)
            idxf = int(np.argmax(pf))
            vote_focus.append(idxf)
            idxf = max(set(vote_focus), key=vote_focus.count)
            focus_label = focus_classes[idxf]

            # 3) Yaw head (left/right)
            yaw_centered = feats["yaw_centered"]; yaw_abs = abs(yaw_centered)
            yaw_feature_row = {**feats, "yaw_abs": yaw_abs}  # add derived
            x_yaw = np.array([[yaw_feature_row[k] for k in yaw_feats]], dtype=np.float32)
            if hasattr(yaw_pipe, "predict_proba"):
                py = yaw_pipe.predict_proba(x_yaw)[0]
            else:
                idxy = int(yaw_pipe.predict(x_yaw)[0]); py = np.zeros(2, dtype=np.float32); py[idxy]=1.0
            py = yaw_ema.update(py)
            idxy = int(np.argmax(py))
            vote_yaw.append(idxy)
            idxy = max(set(vote_yaw), key=vote_yaw.count)
            yaw_label = yaw_classes[idxy]
            yaw_conf = float(np.max(py))

            # 4) Final decision (priority: blink > confident yaw > focus/not_focus)
            if blink_event: 
                final = "blink" 
            elif yaw_conf >= 0.65 and yaw_abs > 0.02:   # small guard against near-neutral
                final = yaw_label
            else:
                final = focus_label

            now=time.time()
            if now-last>=PRINT_EVERY_SEC:
                focus_str = f"F[{focus_classes[0]}:{pf[0]:.2f} {focus_classes[1]}:{pf[1]:.2f}]"
                yaw_str   = f"Y[{yaw_classes[0]}:{py[0]:.2f} {yaw_classes[1]}:{py[1]:.2f}] yaw={yaw_centered:.3f}"
                blink_str = f"B[rate0.5={blink_rate:.2f}]"
                print(f"{final:>10} | {focus_str} {yaw_str} {blink_str}      ", end="\r")
                eeg_string = f"{final:>10} | {focus_str} {yaw_str} {blink_str}      "
                # Output JSON-structured data to stderr for easy parsing
                json_data = {
                    "final": final,
                    "focus": {
                        focus_classes[0]: float(pf[0]),
                        focus_classes[1]: float(pf[1])
                    },
                    "yaw": {
                        yaw_classes[0]: float(py[0]),
                        yaw_classes[1]: float(py[1]),
                        "centered": float(yaw_centered),
                        "confidence": float(yaw_conf)
                    },
                    "blink": {
                        "rate": float(blink_rate),
                        "env95": float(blink_env95),
                        "event": bool(blink_event)
                    },
                    "timestamp": now
                }
                print(json.dumps(json_data), file=sys.stderr)
                requests.post(
                    "http://localhost:8000/eeg/ingest",
                    json={"raw_string": eeg_string}, timeout=1
                    )
                time.sleep(0.1)# Send at 10H
                last=now
                
            time.sleep(max(0, STEP_SEC-0.005))
    except KeyboardInterrupt:
        print("\nStopping…")
    finally:
        try: board.stop_stream(); board.release_session()
        except: pass
        print("Closed.")

if __name__=="__main__":
    main()
