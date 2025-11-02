# MindAware: EEG-Based Cognitive Drone Control

**Binary altitude control system driven by real-time EEG cognitive monitoring.**

MindAware monitors a drone operator's cognitive state via EEG and provides simple binary feedback: **drone in the air (1m) = all parameters optimal**, **grounded (0m) = regain focus**. The system uses AI reasoning with voice confirmation for safety-critical decisions.

---

## 🎯 Quick Start (3 Commands)

**Run these in separate terminal windows:**

### Terminal 1 - Start Backend
```bash
cd /Users/zain/Desktop/MindAware
python3 src/main.py --real-eeg
```

### Terminal 2 - Start EEG Data Feed
```bash
cd /Users/zain/Desktop/MindAware
python3 ai_inferring.py
```

### Terminal 3 - Start Dashboard
```bash
cd /Users/zain/Desktop/MindAware/ui/frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## Overview

MindAware is a **binary control system** that provides real-time cognitive feedback to drone operators:

- **Binary States**: Drone altitude reflects operator wellness (1m = excellent, 0m = needs focus)
- **Real EEG**: Processes live brainwave data from OpenBCI Ganglion hardware
- **Cognitive Metrics**: Extracts focus, fatigue, overload, and stress from raw EEG
- **AI Decision-Making**: Hybrid policy + LLM reasoning with safety guards
- **Voice Confirmation**: Asks operator permission before landing (safety-critical)
- **Passive Yaw**: Head turning controls yaw via EEG (no manual commands needed)
- **Real-time Dashboard**: Live visualization of cognitive state and drone status

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     EEG HARDWARE LAYER                       │
│  OpenBCI Ganglion + ai_inferring.py                         │
│  • Reads raw brainwave data (16 channels @ 250 Hz)          │
│  • Detects focus, yaw (head position), blink rate           │
└───────────────────────────┬──────────────────────────────────┘
                            │ Raw EEG JSON
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   MINDAWARE BACKEND                          │
│  (python3 src/main.py --real-eeg)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. EEG ADAPTER (src/sim/eeg_adapter.py)               │ │
│  │    • Parse raw EEG → extract values                    │ │
│  │    • Buffer readings (30-60 samples)                   │ │
│  │    • Calibrate baselines (20 readings)                 │ │
│  │    • Transform → 4 metrics (0-1 range):                │ │
│  │      - Focus, Fatigue, Overload, Stress                │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. AGENT DECISION PIPELINE (src/agent/)               │ │
│  │    ┌──────────────────────────────────────────────┐    │ │
│  │    │ Policy (Rule-Based - src/agent/policy.py)   │    │ │
│  │    │ • ALL GOOD → recommend takeoff()             │    │ │
│  │    │ • ALL BAD (in air) → recommend land()        │    │ │
│  │    │ • ALL BAD (grounded) → show "regain focus"   │    │ │
│  │    │ • Mixed → no action (waiting)                │    │ │
│  │    └──────────────────────────────────────────────┘    │ │
│  │                            │                             │ │
│  │    ┌──────────────────────────────────────────────┐    │ │
│  │    │ LLM Agent (OpenAI GPT-4 - llm_agent.py)     │    │ │
│  │    │ • Enhances policy with contextual reasoning  │    │ │
│  │    │ • Only acts when policy recommends action    │    │ │
│  │    │ • Guards prevent unnecessary interventions   │    │ │
│  │    └──────────────────────────────────────────────┘    │ │
│  │                            │                             │ │
│  │    ┌──────────────────────────────────────────────┐    │ │
│  │    │ Voice Confirmer (OpenAI TTS/Whisper)         │    │ │
│  │    │ • Speaks: "Should I land?"                   │    │ │
│  │    │ • Listens: "Yes" / "No"                      │    │ │
│  │    │ • Safety: Always confirms landing            │    │ │
│  │    └──────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. DRONE TOOLS (src/agent/tools.py)                   │ │
│  │    • takeoff() → Set altitude to 1.0m                  │ │
│  │    • land() → Set altitude to 0.0m                     │ │
│  │    • Commands sent to partner's drone: TAKEOFF, LAND   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. API SERVER (Built-in, port 8000 - src/api/)        │ │
│  │    • POST /eeg/ingest - Receives EEG data              │ │
│  │    • GET /eeg/state - Returns cognitive metrics        │ │
│  │    • GET /drone/command - Returns current command      │ │
│  │    • GET /tools/status - Returns altitude/actions      │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────┘
                            │ Commands: TAKEOFF, LAND
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   PARTNER'S DRONE HARDWARE                   │
│  • Polls: GET http://localhost:8000/drone/command           │
│  • Executes: TAKEOFF (fly to 1m) or LAND (return to ground) │
│  • Yaw controlled passively by operator's head position     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      DASHBOARD (UI)                          │
│  (npm run dev in ui/frontend)                               │
│  • http://localhost:5173                                     │
│  • Real-time cognitive metrics visualization                 │
│  • Binary drone status: IN THE AIR vs GROUNDED              │
│  • Decision log display                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Binary Control Logic

### ⚠️ FOCUS IS THE ONLY CONTROL PARAMETER

**Other metrics (fatigue, overload, stress) are monitored and displayed but do NOT affect drone decisions.**

| Focus Level | Action | Altitude | Voice |
|------------|--------|----------|-------|
| **HIGH (≥0.6)** | `takeoff()` | 1.0m | "Taking off" (auto) |
| **LOW (≤0.4) in air** | `land()` | 0.0m | "Should I land?" (asks) |
| **LOW (≤0.4) grounded** | No action | 0.0m | "Grounded - regain focus" |
| **MID (0.4 < focus < 0.6)** | No action | Current | "Drone in the air" or "Waiting" |

### Key Features

#### Pure Focus-Based Control
- **In the Air (1m)**: High focus (≥0.6) - operator highly concentrated
- **Grounded (0m)**: Low focus (≤0.4) - operator needs to regain concentration
- **Simple Decision**: Only focus level matters for altitude control
- **Other Metrics**: Fatigue, overload, and stress are monitored for operator awareness but don't affect decisions

#### Passive Yaw Control
- **Head Position = Yaw**: Operator's head turning controls drone rotation via EEG
- **No Manual Commands**: Yaw happens naturally through head movement
- **Altitude Only**: System commands are purely vertical (takeoff/land)

#### Agentic Decision-Making
- **Policy Layer**: Rule-based focus evaluation (≥0.6 = takeoff, ≤0.4 = land)
- **LLM Layer** (OpenAI GPT-4, optional): Enhances policy with contextual reasoning
- **Guard System**: Prevents actions when focus is mid-range (no recommendations)
- **Memory**: Short-term context (recent 10 cognitive states)
- **Focus-Only Logic**: Other metrics monitored but don't trigger actions

#### Voice Confirmation (Safety Critical)
- **Landing Requires Approval**: Always asks "Should I land?" before executing
- **Takeoff is Automatic**: When all good, announces "Taking off" (no confirmation)
- **Status Announcements**: Speaks grounded/in-air messages for awareness
- **OpenAI Integration**: TTS for speaking, Whisper for listening

---

## Setup Instructions

### 1. Prerequisites

```bash
# Check Python version (3.10+ required)
python3 --version

# Check Node.js (18+ required for UI)
node --version
```

### 2. Install Dependencies

```bash
# Navigate to project root
cd /Users/zain/Desktop/MindAware

# Install Python packages
pip install -r requirements.txt

# Install UI dependencies
cd ui/frontend
npm install
cd ../..
```

### 3. Configure API Keys

Create `.env` file in project root:

```bash
# Required for LLM reasoning and voice confirmation
OPENAI_API_KEY=sk-your-key-here

# Optional: Enable voice confirmation (default: false)
VOICE_CONFIRMATION_ENABLED=true
VOICE_CONFIRMATION_TIMEOUT=5
VOICE_DEFAULT_RESPONSE=no
```

**Get your OpenAI API key**: https://platform.openai.com/api-keys

### 4. Verify EEG Hardware

Ensure your partner has:
- OpenBCI Ganglion board connected
- `ai_inferring.py` script ready
- Focus/yaw ML models loaded (`focus_head.joblib`, `yaw_head.joblib`)

---

## Running the System

### ⚠️ IMPORTANT: Start in This Order

The backend MUST be running before the EEG code starts sending data.

---

### **Step 1: Start MindAware Backend**

Open Terminal 1:
```bash
cd /Users/zain/Desktop/MindAware
python3 src/main.py --real-eeg
```

**Wait for this output:**
```
🚀 Starting API server on port 8000...
✅ API server running at http://127.0.0.1:8000
   EEG endpoint: http://127.0.0.1:8000/eeg/ingest
   Command endpoint: http://127.0.0.1:8000/drone/command

[AGENT] Real EEG mode initialized
[EEG] Calibrating... (need 20 readings)
```

---

### **Step 2: Start EEG Data Feed**

Open Terminal 2:
```bash
cd /Users/zain/Desktop/MindAware
python3 ai_inferring.py
```

**Expected output:**
```
EEG OK: 16 ch @ 250 Hz
Stay still ~3s…
👀 Blink hard 3–4 times in ~3s…
Using forehead pair: (16, 15)
{"final": "focus", "focus": {"not_focus": 0.16, "focus": 0.84}, ...}
```

**✅ Data is flowing when you see:**
- Terminal 1: `[EEG] Received reading 1/20 for calibration...`
- Terminal 2: Continuous JSON output with focus/yaw values

---

### **Step 3: Start Dashboard UI**

Open Terminal 3:
```bash
cd /Users/zain/Desktop/MindAware/ui/frontend
npm run dev
```

**Open in browser:**
```
http://localhost:5173
```

**✅ UI is working when you see:**
- Live cognitive metrics updating (Focus, Fatigue, Overload, Stress)
- Drone status showing "IN THE AIR" or "GROUNDED"
- Decision log populating with recent actions

---

### Testing Mode (No EEG Hardware)

For testing without EEG hardware:
```bash
# Simulation mode with fake data
python3 src/main.py --scenario normal --iterations 20

# Available scenarios: normal, fatigue, stress, critical, mixed
```

---

## Understanding Cognitive Metrics

MindAware extracts 4 metrics from raw EEG (normalized 0-1 scale):

### 1. Focus ⚠️ PRIMARY CONTROL METRIC
**What it measures**: Sustained attention and concentration  
**EEG Sources**: Beta/Alpha power ratio (8-30 Hz)  
**Interpretation**:
- **High (≥0.6)**: Strong concentration → **DRONE TAKEOFF** ✅
- **Low (≤0.4)**: Distracted, unfocused → **DRONE LAND** ⚠️
- **Mid (0.4-0.6)**: Moderate focus → **NO ACTION** ⏸️

**THIS IS THE ONLY METRIC THAT CONTROLS DRONE ALTITUDE**

### 2. Fatigue 📊 MONITORING ONLY
**What it measures**: Mental exhaustion level  
**EEG Sources**: Sustained low focus, blink rate, theta power (4-7 Hz)  
**Interpretation**:
- **High (≥0.6)**: Mentally exhausted ⚠️
- **Low (≤0.4)**: Alert and energized ✅

**NOTE: Displayed for operator awareness but DOES NOT affect drone control**

### 3. Overload 📊 MONITORING ONLY
**What it measures**: Cognitive task saturation  
**EEG Sources**: Yaw variance (erratic head movements), beta spikes  
**Interpretation**:
- **High (≥0.6)**: Overwhelmed, task saturation ⚠️
- **Low (≤0.4)**: Comfortable cognitive load ✅

**NOTE: Displayed for operator awareness but DOES NOT affect drone control**

### 4. Stress 📊 MONITORING ONLY
**What it measures**: Stress response activation  
**EEG Sources**: Yaw imbalance (head tension), blink anomalies, focus instability  
**Interpretation**:
- **High (≥0.6)**: Elevated stress ⚠️
- **Low (≤0.4)**: Calm, composed ✅

**NOTE: Displayed for operator awareness but DOES NOT affect drone control**

---

### Focus-Only Decision Logic

**HIGH FOCUS** = Focus ≥0.6  
→ **Action**: Takeoff to 1m

**LOW FOCUS (in air)** = Focus ≤0.4 AND altitude > 0.1m  
→ **Action**: Land (with voice confirmation)

**LOW FOCUS (grounded)** = Focus ≤0.4 AND altitude ≤ 0.1m  
→ **Action**: Show "Grounded - Regain focus to fly"

**MID FOCUS** = 0.4 < Focus < 0.6  
→ **Action**: No change (maintain current altitude)

**Other metrics are displayed but ignored for control decisions.**

---

## Drone Commands

The system has **two altitude commands only**:

### 1. `takeoff()`
**Action**: Drone rises to 1.0m altitude  
**When**: High focus detected  
- **Focus ≥0.6** ← ONLY REQUIREMENT

**Other metrics** (fatigue, overload, stress): Monitored but don't affect decision

**Confirmation**: Automatic (announces "Taking off")  
**Maps to**: Partner's `TAKEOFF` step  
**Voice**: "High focus detected. Taking off to 1 meter."

---

### 2. `land()`
**Action**: Drone lands to 0.0m (ground level)  
**When**: Low focus detected AND in the air  
- **Focus ≤0.4** ← ONLY REQUIREMENT
- Current altitude > 0.1m

**Other metrics** (fatigue, overload, stress): Monitored but don't affect decision

**Confirmation**: ⚠️ ALWAYS ASKS "Should I land?" (safety-critical)  
**Maps to**: Partner's `LAND` step  
**Voice**: "Low focus detected. Should I land?"  
**Response**: Operator says "Yes" (executes) or "No" (cancels)

---

### Passive Control: Yaw (Head Position)

**Yaw is NOT a command** - it's controlled passively by the operator's head position via EEG:
- Turn head left → Drone yaws left
- Turn head right → Drone yaws right
- Measured continuously from EEG yaw sensors
- No voice confirmation needed (not a discrete action)

---

## Dashboard Features

Access at **http://localhost:5173** (runs on Terminal 3)

### Real-Time Displays:

1. **Cognitive Metrics Panel**
   - Focus (0-1 scale, green = good)
   - Fatigue (0-1 scale, red = high)
   - Overload (0-1 scale, red = high)
   - Stress (0-1 scale, red = high)
   - Color-coded bars update live

2. **Binary Drone Status**
   - ✈️ **IN THE AIR**: 1.0m altitude (all parameters optimal)
   - 🔴 **GROUNDED**: 0.0m altitude (regain focus to fly)
   - Current altitude display (0.00m - 1.00m)
   - Visual altitude indicator

3. **Decision Log**
   - Recent actions (takeoff, land, maintain)
   - Reasoning for each decision
   - Timestamp and LLM/policy source
   - Voice confirmation status

4. **System Info**
   - Battery level (simulated)
   - Mission progress
   - Action count
   - Connection status

---

## Decision Logging

All decisions are automatically logged to `logs/decisions.jsonl`:

### Example: Landing Decision

```json
{
  "timestamp": "2024-11-02T14:30:45.123Z",
  "cognitive_state": {
    "focus": 0.35,
    "fatigue": 0.72,
    "overload": 0.68,
    "stress": 0.65
  },
  "policy_recommendations": [
    {
      "action": "land",
      "reason": "All parameters critical - operator needs immediate support",
      "urgent": false
    }
  ],
  "llm_reasoning": "All four parameters are in critical range. Landing necessary for safety.",
  "actions_taken": [
    {
      "tool": "land",
      "result": {
        "success": true,
        "new_altitude_m": 0.0
      },
      "voice_confirmed": true
    }
  ],
  "model": "llm"
}
```

---

## Troubleshooting

### Issue: "Connection Refused" from `ai_inferring.py`

**Problem**: EEG code can't connect to backend  
**Solution**: Start `python3 src/main.py --real-eeg` FIRST, then start `ai_inferring.py`

```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

### Issue: UI Not Updating

**Problem**: Dashboard shows old data or "Waiting for data"  
**Solutions**:

1. **Verify backend is running:**
```bash
curl http://localhost:8000/eeg/state
# Should return current cognitive metrics
```

2. **Check EEG data is flowing:**
```bash
# Terminal 1 should show:
[EEG] Received reading 25/20 for calibration...
[EEG] Calibrated! ✅
```

3. **Restart Vite dev server:**
```bash
# In Terminal 3, press Ctrl+C, then:
npm run dev
```

4. **Clear browser cache** and refresh (Cmd+Shift+R on Mac)

---

### Issue: Voice Confirmation Not Working

**Problem**: System not speaking or not hearing responses  
**Solutions**:

1. **Check if voice is enabled:**
```bash
cat .env | grep VOICE
# Should show: VOICE_CONFIRMATION_ENABLED=true
```

2. **Test microphone:**
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
# Should list your microphone
```

3. **Verify OpenAI API key:**
```bash
python3 -c "import os; print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"
# Should print: Key set: True
```

---

### Issue: "Insufficient Data" Warning

**Problem**: Not enough EEG readings for calibration  
**Solution**: Wait 20+ readings (about 60 seconds)

```bash
# Terminal 1 will show:
[EEG] Received reading 1/20 for calibration...
[EEG] Received reading 2/20 for calibration...
...
[EEG] Calibrated! ✅
```

---

### Issue: Drone Always Grounded

**Problem**: Never takes off even with good focus  
**Solution**: Check focus level in dashboard

Binary takeoff requires:
- **Focus ≥ 0.6** ← ONLY REQUIREMENT ✅

**Other metrics (fatigue, overload, stress) do NOT affect takeoff.**

If focus is below 0.6, drone stays grounded (waiting for high focus).
Check the dashboard's cognitive metrics panel for current focus level.

---

## File Structure

```
MindAware/
├── src/
│   ├── main.py                    # Main orchestrator (start here)
│   ├── agent/
│   │   ├── policy.py              # Rule-based binary logic
│   │   ├── llm_agent.py           # OpenAI GPT-4 reasoning
│   │   ├── tools.py               # Drone commands (takeoff/land)
│   │   ├── voice_confirmer.py     # Voice TTS/STT system
│   │   ├── memory.py              # Short-term context
│   │   └── logger.py              # Decision logging
│   ├── api/
│   │   ├── server.py              # FastAPI REST endpoints
│   │   ├── eeg_ingestion.py       # EEG data ingestion
│   │   └── websocket.py           # Real-time streaming
│   └── sim/
│       ├── eeg_adapter.py         # Real EEG parser/transformer
│       └── eeg_simulator.py       # Simulated EEG generator
├── ui/frontend/
│   ├── src/
│   │   ├── App.jsx                # Main dashboard
│   │   └── components/
│   │       ├── CognitiveMetrics.jsx
│   │       ├── DroneStatus.jsx
│   │       └── DecisionLog.jsx
│   ├── package.json
│   └── vite.config.js
├── logs/
│   └── decisions.jsonl            # Decision audit trail
├── ai_inferring.py                # Partner's EEG hardware script
├── requirements.txt               # Python dependencies
├── .env                           # Configuration (API keys)
└── README.md                      # This file
```

---

## About This Project

**MindAware** is a hackathon project demonstrating **EEG-based cognitive monitoring** for drone operations.

### Key Design Decisions:

1. **Focus-Only Control**: ONLY focus determines altitude (1m = high focus, 0m = low focus). Simple and unambiguous.

2. **Other Metrics Monitored**: Fatigue, overload, and stress are measured and displayed for operator awareness but don't trigger actions.

3. **Binary Thresholds**: Focus ≥0.6 = high, ≤0.4 = low. Clear thresholds reduce sensor noise false positives.

4. **Voice Confirmation**: Safety-critical landing always requires human approval, balancing automation with human oversight.

5. **Passive Yaw**: Head position naturally controls rotation without explicit commands, reducing cognitive load.

6. **Guard Systems**: Prevents AI from acting when focus is mid-range (0.4-0.6), reducing unnecessary interventions.

7. **Hybrid Architecture**: Combines rule-based focus check (fast, predictable) with LLM reasoning (contextual, adaptive).

### Technical Stack:

- **Backend**: Python 3.12, FastAPI, OpenAI API
- **Frontend**: React + Vite, real-time HTTP polling
- **EEG**: OpenBCI Ganglion (16 channels @ 250 Hz)
- **ML Models**: Scikit-learn (focus/yaw classification)
- **Voice**: OpenAI TTS + Whisper STT

---

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, see the troubleshooting section above or check the logs in `logs/decisions.jsonl`.
