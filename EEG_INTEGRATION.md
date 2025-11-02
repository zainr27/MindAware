# 🧠 Real EEG Hardware Integration Guide

Complete guide for integrating real EEG hardware with MindAware.

---

## 📊 What You Get From Partner's Hardware

**Raw EEG String:**
```
F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]
```

**Contains:**
- `focus`: 0.12 (attention level)
- `not_focus`: 0.88 (distraction level)
- `yaw_left`: 0.29 (head turn preference left)
- `yaw_right`: 0.71 (head turn preference right)
- `yaw`: 3416.347 (absolute head rotation angle)
- `blink_rate`: 0.00 (blinks per time period - stress indicator)

**MindAware Transforms Into:**
```json
{
  "focus": 0.12,      // Direct from hardware
  "fatigue": 0.754,   // Computed from focus history + blink rate
  "overload": 0.015,  // Computed from yaw variance (head instability)
  "stress": 0.243     // Computed from yaw imbalance + blinks + focus variance
}
```

---

## 🚀 Quick Start

### Step 1: Start MindAware Server

```bash
cd /Users/zain/Desktop/MindAware/src/api
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Test with Simulator (No Hardware)

```bash
# In another terminal
cd /Users/zain/Desktop/MindAware
python3 test_eeg_partner.py --scenario normal --rate 0.1 --duration 60
```

This simulates partner sending data for 60 seconds at 10Hz.

### Step 3: Run Agent with Real EEG

```bash
python3 src/main.py --real-eeg --llm --iterations 20 --interval 3
```

**Flags:**
- `--real-eeg`: Use real hardware data (not simulator)
- `--llm`: Enable LLM reasoning
- `--iterations 20`: Run for 20 decision cycles
- `--interval 3`: 3 seconds between decisions

---

## 🔌 Partner Integration

### Option A: REST API (Recommended)

**Endpoint:** `POST http://localhost:8000/eeg/ingest`

**Python Example:**
```python
import requests
import time

API_URL = "http://localhost:8000/eeg/ingest"

def send_eeg_reading(raw_string: str):
    """Send a single EEG reading to MindAware."""
    response = requests.post(
        API_URL,
        json={"raw_string": raw_string},
        timeout=1
    )
    return response.json()

# In your EEG reading loop
while True:
    # Get reading from your hardware
    eeg_data = your_eeg_hardware.read()  # Your code here
    
    # Format it as string (if not already)
    raw_string = f"F[not_focus:{eeg_data.not_focus} focus:{eeg_data.focus}] Y[yaw_left:{eeg_data.yaw_left} yaw_right:{eeg_data.yaw_right}] yaw={eeg_data.yaw} B[rate0.5={eeg_data.blink_rate}]"
    
    # Send to MindAware
    result = send_eeg_reading(raw_string)
    print(f"Status: {result['status']}")
    
    time.sleep(0.1)  # 10Hz sampling rate
```

**Request:**
```json
{
  "raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "EEG data ingested",
  "buffer_size": 45,
  "calibrated": true,
  "timestamp": "2025-11-02T10:30:45.123456"
}
```

### Option B: cURL (For Testing)

```bash
curl -X POST http://localhost:8000/eeg/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
  }'
```

### Option C: Batch Upload (Buffered Data)

```bash
curl -X POST http://localhost:8000/eeg/ingest/batch \
  -H "Content-Type: application/json" \
  -d '{
    "readings": [
      "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]",
      "F[not_focus:0.85 focus:0.15] Y[yaw_left:0.31 yaw_right:0.69] yaw=3420.123 B[rate0.5=0.02]"
    ]
  }'
```

---

## 🔢 Data Transformation Details

### Focus (Direct Mapping)
```python
focus = partner_data.focus  # Use directly, already 0-1
```

### Fatigue (Derived)
**Formula:** `fatigue = (1 - avg_focus_last_minute) * 0.7 + blink_rate_normalized * 0.3`

```python
# Moving average of focus over last 60 seconds
avg_focus = mean(last_60_focus_values)

# Normalize blink rate
normalized_blink = blink_rate / (baseline_blink * 2)

# Combined fatigue score
fatigue = (1 - avg_focus) * 0.7 + normalized_blink * 0.3
```

**Logic:** Low sustained focus + high blink rate = high fatigue

### Overload (Derived)
**Formula:** `overload = std_deviation(last_20_yaw_values) / calibrated_max`

```python
# Standard deviation of yaw over last 20 readings
yaw_variance = std_dev(last_20_yaw_values)

# Normalize against max observed
overload = yaw_variance / max_observed_variance
```

**Logic:** Erratic head movements = cognitive overload

### Stress (Derived)
**Formula:** `stress = yaw_imbalance * 0.4 + blink_anomaly * 0.3 + focus_variance * 0.3`

```python
# Yaw imbalance (extreme left/right preference)
yaw_imbalance = abs(yaw_left - yaw_right)

# Blink anomaly (deviation from baseline)
blink_anomaly = abs(current_blink - baseline_blink) / baseline_blink

# Focus instability (variance over time)
focus_variance = std_dev(last_30_focus_values) / 0.3

# Combined stress score
stress = (yaw_imbalance * 0.4) + (blink_anomaly * 0.3) + (focus_variance * 0.3)
```

**Logic:** Tension in posture + abnormal blinking + focus instability = stress

---

## 📡 API Endpoints

### Ingestion
- `POST /eeg/ingest` - Send single reading
- `POST /eeg/ingest/batch` - Send multiple readings

### Monitoring
- `GET /eeg/status` - Check adapter status & calibration
- `GET /eeg/state` - Get current computed cognitive state

### Management
- `POST /eeg/calibrate` - Manually trigger calibration
- `DELETE /eeg/reset` - Reset buffer & recalibrate

### Documentation
- `GET /docs` - Full API documentation (when server running)

---

## 🎯 Calibration

### Automatic Calibration
- Triggers after **30 samples** received
- Records baseline values during "normal" operation:
  - `baseline_focus`: Average focus level
  - `baseline_yaw_variance`: Typical head movement variance
  - `baseline_blink_rate`: Normal blink rate
- Used to normalize all subsequent readings

### Manual Calibration
```bash
curl -X POST http://localhost:8000/eeg/calibrate
```

### Best Practice
Have operator sit calmly for first 30 seconds to establish good baseline.

---

## 📈 Monitoring & Testing

### Check Adapter Status
```bash
curl http://localhost:8000/eeg/status | python3 -m json.tool
```

**Response:**
```json
{
  "status": "operational",
  "adapter": {
    "is_calibrated": true,
    "buffer_size": 60,
    "readings_received": 150,
    "baseline_focus": 0.764,
    "baseline_yaw_variance": 2.33,
    "baseline_blink_rate": 0.019
  },
  "last_state": {
    "focus": 0.650,
    "fatigue": 0.222,
    "overload": 0.015,
    "stress": 0.243
  }
}
```

### Get Current Cognitive State
```bash
curl http://localhost:8000/eeg/state
```

### Test Scenarios (Without Hardware)

```bash
# Normal operation
python3 test_eeg_partner.py --scenario normal --rate 0.1 --duration 60

# Improving focus
python3 test_eeg_partner.py --scenario improving --rate 0.1 --duration 60

# Degrading focus (simulate fatigue)
python3 test_eeg_partner.py --scenario degrading --rate 0.1 --duration 60

# Erratic (simulate overload)
python3 test_eeg_partner.py --scenario erratic --rate 0.1 --duration 60
```

---

## 🎪 Demo Day Setup

### Terminal 1: Backend API
```bash
cd /Users/zain/Desktop/MindAware/src/api
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend Dashboard
```bash
cd /Users/zain/Desktop/MindAware/ui/frontend
npm run dev
```

### Terminal 3: MindAware Agent (Real EEG)
```bash
cd /Users/zain/Desktop/MindAware
python3 src/main.py --real-eeg --llm --no-sim
```

### Terminal 4: Partner's EEG Stream
Partner runs their code that POSTs to `/eeg/ingest`

### Browser
- **Dashboard**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

---

## 🔧 Troubleshooting

### "Cannot connect to server"
```bash
# Check if running
curl http://localhost:8000/health

# Start if not running
cd src/api && uvicorn server:app --reload
```

### "Not calibrated yet"
- Need at least 30 samples
- Check: `curl http://localhost:8000/eeg/status`
- Manual trigger: `curl -X POST http://localhost:8000/eeg/calibrate`

### "Buffer not filling up"
```bash
# Check status
curl http://localhost:8000/eeg/status

# Verify partner is sending data
# Look for "readings_received" count increasing
```

### "Cognitive metrics seem wrong"
```bash
# Get current state with raw data
curl http://localhost:8000/eeg/state | python3 -m json.tool

# Check the "raw_data" field for parsed values
# May need recalibration with better baseline
```

### "Agent not responding to real data"
- Ensure `--real-eeg` flag is set
- Check buffer has data: `curl http://localhost:8000/eeg/status`
- Verify buffer_size > 0
- Check calibration completed

---

## 🗂️ Data Flow

```
Partner's EEG Hardware
    ↓
Partner's Python Script reads data
    ↓
Format as string: "F[not_focus:X focus:Y] Y[...] yaw=Z B[...]"
    ↓
POST to http://localhost:8000/eeg/ingest
    ↓
MindAware parses and buffers (last 60 readings)
    ↓
Auto-calibrates after 30 samples
    ↓
Computes cognitive metrics:
    - Focus (direct from data)
    - Fatigue (from focus history + blink rate)
    - Overload (from yaw variance)
    - Stress (from yaw imbalance + blink + focus variance)
    ↓
Agent uses metrics for decision-making
    ↓
Actions: set_flight_mode, throttle_alerts, etc.
    ↓
Dashboard displays real-time cognitive state
```

---

## 📋 Integration Checklist

### Pre-Demo Testing
- [ ] MindAware server starts without errors
- [ ] Test script successfully sends data: `python3 test_eeg_partner.py`
- [ ] Calibration completes (after 30 samples)
- [ ] Cognitive state shows reasonable values
- [ ] Agent runs with `--real-eeg` flag
- [ ] Dashboard displays metrics in real-time

### Day-of-Demo
- [ ] All 4 terminals running
- [ ] Partner's hardware connected
- [ ] Data flowing (verify with `/eeg/status`)
- [ ] Dashboard showing live updates
- [ ] Agent making decisions based on EEG data
- [ ] Decision log showing EEG-driven actions

---

## 💡 Sampling Rate

**Recommended:** 10Hz (0.1 second intervals)
- Fast enough for real-time response
- Matches human reaction time scale
- MindAware processes every 3 seconds, providing 30 samples per decision

You can send faster (100Hz) but 10Hz is sufficient for cognitive monitoring.

---

## 🔍 Files Created

1. **`src/sim/eeg_adapter.py`** (366 lines)
   - `EEGReading` class - parsed reading structure
   - `RealEEGAdapter` class - main adapter with buffering & calibration
   - Parser, statistics, transformations

2. **`src/api/eeg_ingestion.py`** (126 lines)
   - 6 REST endpoints for EEG data ingestion and management
   - Integration with adapter

3. **`test_eeg_partner.py`** (189 lines)
   - Simulates partner sending data
   - Multiple scenarios, configurable rate
   - Test harness for development

4. **Modified: `src/main.py`**
   - Added `--real-eeg` flag
   - Supports real hardware mode

5. **Modified: `src/api/server.py`**
   - Registered EEG ingestion routes

---

## 📝 What Partner Needs to Do

**Literally 2 things:**

1. **POST raw EEG strings to:** `http://localhost:8000/eeg/ingest`
2. **That's it!** Everything else is automatic.

**Minimal Integration Code:**
```python
import requests
import time

while True:
    eeg_string = hardware.read()  # Your code
    requests.post(
        "http://localhost:8000/eeg/ingest",
        json={"raw_string": eeg_string}
    )
    time.sleep(0.1)  # 10Hz
```

---

## 🎯 Key Features

✅ Automatic parsing of partner's format  
✅ Rolling buffer (60 readings)  
✅ Auto-calibration (30 samples)  
✅ Sophisticated metric derivation  
✅ REST API integration  
✅ Production-ready error handling  
✅ Comprehensive test tools  
✅ Drop-in replacement for simulator  
✅ Real-time processing  
✅ WebSocket streaming to dashboard  

---

## 🚀 Status: Ready for Hackathon

All code written, tested, and documented. Partner just needs to POST data to the API endpoint!

**Questions?** 
- Run test: `python3 test_eeg_partner.py`
- View API docs: http://localhost:8000/docs (when server running)
- Test standalone adapter: `python3 src/sim/eeg_adapter.py`

