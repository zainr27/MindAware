"""
Integration code for partner's drone hardware.

ADD THIS TO YOUR DRONE CODE:
"""

import requests
import time

MINDAWARE_API = "http://localhost:8000"

def send_eeg_to_mindaware(raw_eeg_string):
    """
    Send raw EEG data to MindAware.
    
    Call this every time you get a new EEG reading.
    """
    try:
        response = requests.post(
            f"{MINDAWARE_API}/eeg/ingest",
            json={"raw_string": raw_eeg_string},
            timeout=1
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send EEG: {e}")
        return False


def get_drone_command():
    """
    Get the latest drone command from MindAware.
    
    Returns partner's exact step names: 'TAKEOFF', 'LAND', 'YAW RIGHT', or 'maintain'
    """
    try:
        response = requests.get(f"{MINDAWARE_API}/drone/command", timeout=1)
        data = response.json()
        # data['command'] is already in partner's format: "TAKEOFF", "LAND", "YAW RIGHT"
        return data['command'], data.get('reasoning', '')
    except Exception as e:
        print(f"Failed to get command: {e}")
        return 'maintain', ''


# ========================================
# OPTION 1: Simple Integration (Recommended)
# ========================================

def main_loop_simple():
    """
    Simple integration: poll for commands every 2 seconds.
    
    Add this to your existing drone code.
    """
    last_command = None
    
    while True:
        # 1. Get EEG reading (your existing code)
        raw_eeg = get_your_eeg_reading()  # YOUR FUNCTION HERE
        
        # 2. Send to MindAware
        send_eeg_to_mindaware(raw_eeg)
        
        # 3. Get drone command from MindAware
        command, reasoning = get_drone_command()
        
        # 4. Execute command (only if it changed)
        if command != last_command:
            print(f"🚁 NEW COMMAND: {command}")
            print(f"   Reason: {reasoning}")
            
            # Command is already in your exact step name format!
            if command == 'TAKEOFF':
                your_drone.execute_step('TAKEOFF')  # YOUR FUNCTION HERE
            elif command == 'LAND':
                your_drone.execute_step('LAND')  # YOUR FUNCTION HERE
            elif command == 'YAW RIGHT':
                your_drone.execute_step('YAW RIGHT')  # YOUR FUNCTION HERE
            # 'maintain' = do nothing
            
            last_command = command
        
        time.sleep(2)  # Check every 2 seconds


# ========================================
# OPTION 2: Minimal 3-Line Integration
# ========================================

"""
ADD THESE 3 LINES TO YOUR EXISTING CODE:

1. After getting EEG data:
   requests.post("http://localhost:8000/eeg/ingest", json={"raw_string": raw_eeg})

2. In your control loop:
   cmd = requests.get("http://localhost:8000/drone/command").json()['command']

3. Execute command (cmd is already in your exact step format):
   if cmd == 'TAKEOFF': drone.execute_step('TAKEOFF')
   elif cmd == 'LAND': drone.execute_step('LAND')
   elif cmd == 'YAW RIGHT': drone.execute_step('YAW RIGHT')
"""


# ========================================
# FULL EXAMPLE
# ========================================

def complete_example():
    """
    Complete working example showing both EEG sending and command receiving.
    """
    import time
    
    print("🧠 MindAware Drone Integration")
    print("=" * 50)
    
    last_command = None
    
    while True:
        # === YOUR EEG CODE HERE ===
        # Get raw EEG string from your BrainFlow board
        # Example: raw_eeg = board.get_current_data_as_string()
        
        # For demo purposes, using a fake string:
        raw_eeg = "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
        
        # === SEND TO MINDAWARE ===
        success = send_eeg_to_mindaware(raw_eeg)
        if success:
            print("✅ EEG data sent")
        
        # === GET DRONE COMMAND ===
        command, reasoning = get_drone_command()
        
        # === EXECUTE IF CHANGED ===
        if command != last_command and command != 'maintain':
            print(f"\n🚁 DRONE COMMAND: {command}")
            print(f"   Reason: {reasoning}\n")
            
            # === YOUR DRONE CODE HERE ===
            # Command is already in your exact step format!
            if command == 'TAKEOFF':
                print("  → Executing: drone.execute_step('TAKEOFF')")
                # your_drone.execute_step('TAKEOFF')
            
            elif command == 'LAND':
                print("  → Executing: drone.execute_step('LAND')")
                # your_drone.execute_step('LAND')
            
            elif command == 'YAW RIGHT':
                print("  → Executing: drone.execute_step('YAW RIGHT')")
                # your_drone.execute_step('YAW RIGHT')
            
            last_command = command
        
        time.sleep(2)  # Poll every 2 seconds


if __name__ == "__main__":
    # Test the connection
    print("Testing connection to MindAware...")
    
    try:
        response = requests.get(f"{MINDAWARE_API}/health")
        if response.status_code == 200:
            print("✅ Connected to MindAware!")
            print("\nNow running integration loop...")
            complete_example()
        else:
            print("❌ MindAware not responding")
    except Exception as e:
        print(f"❌ Cannot connect to MindAware: {e}")
        print("   Make sure MindAware is running!")

