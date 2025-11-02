# 🧠 MindAware - Cognitive Co-Pilot for BCI-Driven Drones

An agentic AI system that monitors operator cognitive state via EEG/BCI and provides real-time visual feedback through altitude-based drone control.

## 🎯 Overview

MindAware is a real-time cognitive monitoring and decision-making system designed for BCI (Brain-Computer Interface) controlled drones. It continuously analyzes operator mental state and adjusts drone altitude to provide a **visual representation of operator wellness** - the drone rises when the operator is performing well and descends when they're struggling.

### Key Features

- **Real-time Cognitive Monitoring**: Continuous EEG analysis for focus, fatigue, overload, and stress
- **Visual Wellness Feedback**: Drone altitude reflects operator cognitive state in real-time
- **Agentic Decision Making**: Rule-based policy + optional LLM reasoning for adaptive responses
- **Intuitive Control**: Simple UP/DOWN altitude adjustments based on composite cognitive score
- **Live Dashboard**: React-based visualization with altitude indicator and rotation compass
- **Comprehensive Logging**: JSONL audit trail for all decisions and actions
- **Simulation Mode**: Fully functional without hardware (simulated EEG + drone)
- **Real EEG Support**: Seamless integration with hardware via REST API

## 🏗️ Architecture

```
┌─────────────────┐
│   EEG Sensor    │ (Simulated or Real Hardware)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cognitive State │ Focus, Fatigue, Overload, Stress (0-1 scale)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Policy Engine  │ Check: ALL good? ALL bad? Mixed?
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Agent     │ (Optional: OpenAI GPT-4 Reasoning)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Binary Controls │ takeoff(1m) / land(0m) / turn_around(180°)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────┐
│  Drone Control  │────▶│  Live Dashboard      │
│  (Altitude +    │     │  • Altitude Bar      │
│   Rotation)     │     │  • Rotation Compass  │
└────────┬────────┘     │  • Wellness Status   │
         │              └──────────────────────┘
         ▼
┌─────────────────┐
│  Decision Log   │ (JSONL Audit Trail)
└─────────────────┘
```

### How It Works

1. **EEG data** is captured from the operator (simulated or real hardware)
2. **Cognitive metrics** are calculated: focus, fatigue, overload, stress
3. **Policy engine** checks if ALL parameters are good or bad
4. **Binary Decision**: 
   - ALL GOOD (focus ≥0.6 + negatives ≤0.4) → **TAKEOFF to 1m**
   - ALL BAD (focus ≤0.4 + negatives ≥0.6) → **LAND to ground**
   - MIXED (some good, some bad) → **TURN AROUND 180°** (visual indicator)
5. **Drone responds instantly** with binary altitude control
6. **Dashboard updates** with live altitude bar, rotation, and wellness indicator

## 📁 Project Structure

```
mindaware/
├── src/
│   ├── agent/
│   │   ├── policy.py          # Rule-based cognitive policy
│   │   ├── llm_agent.py       # OpenAI-powered reasoning
│   │   ├── tools.py           # Drone control functions
│   │   ├── logger.py          # Decision logging
│   │   └── memory.py          # Short-term context memory
│   ├── api/
│   │   ├── server.py          # FastAPI REST endpoints
│   │   └── websocket.py       # WebSocket streaming
│   ├── sim/
│   │   ├── eeg_simulator.py   # Mock EEG data generator
│   │   └── drone_simulator.py # Mock telemetry generator
│   └── main.py                # Main orchestrator
├── ui/frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.jsx            # Main app component
│   │   └── main.jsx           # Entry point
│   ├── package.json
│   └── vite.config.js
├── data/logs/
│   └── decisions.jsonl        # Decision audit trail
├── requirements.txt
├── run.sh                     # One-command startup script
└── README.md
```

## 🚀 Quick Start

**New user?** See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions.

**Integrating EEG hardware?** See [EEG_INTEGRATION.md](EEG_INTEGRATION.md) for hardware integration guide.

### 5-Minute Quick Start

1. **Install dependencies**
```bash
pip3 install -r requirements.txt
cd ui/frontend && npm install && cd ../..
```

2. **Run everything**
```bash
./run.sh
```

3. **Open browser**
- Dashboard: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Manual Start (Alternative)

**Backend:**
```bash
pip install -r requirements.txt
cd src/api
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd ui/frontend
npm install
npm run dev
```

**Simulation:**
```bash
python src/main.py --scenario fatigue --iterations 20 --interval 3
```

## 🎮 Usage

### Command Line Options

```bash
python src/main.py [OPTIONS]

Options:
  --scenario      Simulation scenario: normal, fatigue, stress, degrading
  --iterations    Number of simulation cycles (default: 10)
  --interval      Seconds between cycles (default: 3.0)
  --llm           Enable LLM reasoning (requires OPENAI_API_KEY)
  --real-eeg      Use real EEG hardware (data via /eeg/ingest API)
  --no-sim        Skip simulation (API-only mode)
```

### Example Commands

**Run normal scenario (policy-only):**
```bash
python src/main.py --scenario normal --iterations 15
```

**Run with LLM reasoning:**
```bash
python src/main.py --scenario stress --iterations 20 --llm
```

**Run degrading scenario with fast updates:**
```bash
python src/main.py --scenario degrading --iterations 30 --interval 2
```

**Run with real EEG hardware:**
```bash
python src/main.py --real-eeg --llm --iterations 100 --interval 3
```

**Demo mode (best for presentations):**
```bash
python src/main.py --scenario fatigue --iterations 20 --interval 2 --llm
# Watch the drone altitude drop as simulated operator fatigues
```

## 🎯 Hackathon Demo Guide

### Why Binary Control?

Traditional BCI systems are complex and hard to visualize. MindAware uses an **ultra-simple binary visual metaphor**:

- **Drone at 1m** = ALL parameters optimal 🟢
- **Drone at ground** = ALL parameters critical 🔴
- **Drone rotating** = Mixed state (some good, some bad) 🔄

**Binary control** makes it instantly clear: the drone is either up (operator excelling), down (operator struggling), or spinning (mixed state). No gradients, no complexity - just **three clear visual states** that anyone can understand at a glance.

### Demo Flow (5 minutes)

1. **Setup** (30 seconds)
   ```bash
   # Terminal 1: Start backend + agent
   python src/main.py --scenario normal --iterations 15 --interval 2 --llm
   
   # Terminal 2: Start dashboard
   cd ui/frontend && npm run dev
   ```

2. **Show Normal Operation** (1 minute)
   - Point out cognitive metrics on dashboard
   - Explain binary logic: ALL good → 1m, ALL bad → 0m, MIXED → rotate
   - Show drone starting at ground level

3. **Simulate High Performance** (1.5 minutes)
   - Restart with `--scenario normal` (generates optimal parameters)
   - Watch drone instantly **takeoff to 1 meter**
   - Show altitude bar at 1m (green)
   - Wellness indicator: 🟢 "Performing Well"
   - Explain: ALL parameters optimal → binary takeoff to 1m!

4. **Simulate Critical State** (1.5 minutes)
   - Restart with `--scenario critical`
   - Watch drone instantly **land to ground**
   - Show altitude bar at 0m (red)
   - Wellness indicator: 🔴 "Critical State"
   - Explain: ALL parameters bad → emergency landing to ground!

5. **Show Mixed State** (30 seconds)
   - Use `--scenario mixed`
   - Watch drone **rotate 180°** while maintaining altitude
   - Rotation compass spins
   - Explain: Some parameters good, some bad → visual indicator

6. **Show Real EEG** (1 minute)
   - If hardware available: `python src/main.py --real-eeg`
   - Partner sends live data to `/eeg/ingest`
   - Drone responds to real cognitive changes with binary control
   - Ultimate demo of integration

### Key Talking Points

✅ **Binary Control**: Three clear states - up, down, or rotating  
✅ **Instant Response**: Drone instantly goes to 1m or 0m (no gradual movement)  
✅ **Visual Clarity**: At 1m = excellent, at ground = critical, rotating = mixed  
✅ **Real-time**: Immediate response when ALL parameters cross thresholds  
✅ **Autonomous**: Agent decides, no human confirmation needed  
✅ **Clear Thresholds**: Focus ≥0.6 & negatives ≤0.4 = all good  
✅ **Safe**: Binary landing to ground when all parameters indicate danger  
✅ **Scalable**: Works with simulated OR real EEG hardware  

### Troubleshooting During Demo

**Drone not moving?**
- Most likely in **MIXED** state (some parameters good, some bad)
- It should be **rotating 180°** instead
- Check individual metrics - need ALL good or ALL bad for altitude change
- Use `--scenario normal` for instant takeoff to 1m
- Use `--scenario critical` for instant landing to 0m

**Drone stuck at 1m or 0m?**
- This is correct for binary control!
- Once at 1m, it stays there until parameters change
- Once at 0m, it stays there until parameters improve
- Use `--scenario degrading` to see transitions between states

**Dashboard not updating?**
- Refresh browser page
- Check browser console for WebSocket errors
- Verify backend is running on port 8000

**No LLM responses?**
- Falls back to policy-only automatically
- Still fully functional, just no AI reasoning text

## 🔌 API Endpoints

### REST API

**Core Endpoints:**
- `GET /` - API status
- `GET /health` - Health check
- `POST /agent` - Process cognitive state and get decision
- `GET /logs?count=10` - Retrieve recent decision logs
- `GET /memory` - Get agent memory summary
- `GET /tools/status` - Get current tool states
- `POST /tools/execute` - Manually execute a tool
- `DELETE /logs` - Clear decision logs
- `DELETE /memory` - Clear agent memory

**EEG Hardware Endpoints:**
- `POST /eeg/ingest` - Ingest single raw EEG reading
- `POST /eeg/ingest/batch` - Ingest batch of raw EEG readings
- `GET /eeg/status` - Get adapter status (buffer, calibration)
- `GET /eeg/state` - Get latest computed cognitive state
- `POST /eeg/calibrate` - Manually trigger calibration
- `DELETE /eeg/reset` - Reset adapter buffer and calibration

### WebSocket

- `ws://localhost:8000/ws` - Real-time streaming endpoint

**Subscriptions:**
- `cognitive_state` - EEG-derived cognitive metrics
- `telemetry` - Drone telemetry data
- `decision` - Agent decision notifications
- `alert` - System alerts

## 🧠 Agent Tools

The agent controls the drone through a **binary all-or-nothing system**:

### 1. **takeoff()** ✅
**When**: ALL parameters optimal
- Focus ≥ 0.6 (HIGH)
- Fatigue ≤ 0.4 (LOW)
- Overload ≤ 0.4 (LOW)
- Stress ≤ 0.4 (LOW)

**Effect**: Drone instantly goes to **1 meter altitude**  
**Meaning**: 🟢 Operator performing excellently - all systems go!

### 2. **land()** 🔴
**When**: ALL parameters critical
- Focus ≤ 0.4 (LOW)
- Fatigue ≥ 0.6 (HIGH)
- Overload ≥ 0.6 (HIGH)
- Stress ≥ 0.6 (HIGH)

**Effect**: Drone instantly returns to **ground (0m)**  
**Meaning**: 🔴 Critical state - operator needs immediate support

### 3. **turn_around()** 🔄
**When**: Mixed parameters (some good, some bad)  
**Effect**: Drone rotates **180°** while maintaining current altitude  
**Meaning**: ⚠️ Mixed state - visual indicator that parameters aren't uniform

### Visual Feedback
The drone provides **instant binary feedback**:
- **At 1m altitude**: All parameters optimal → operator excelling
- **At ground (0m)**: All parameters critical → operator struggling
- **Rotating 180°**: Mixed state → some parameters good, some bad

## 📊 Cognitive Metrics

The system monitors four key cognitive dimensions (each 0-1 scale):

- **Focus** (0-1): Attention and concentration level
- **Fatigue** (0-1): Mental exhaustion and tiredness
- **Overload** (0-1): Cognitive load and task saturation
- **Stress** (0-1): Psychological stress and pressure

### All-or-Nothing Decision Logic

The agent uses simple thresholds to check if ALL parameters are good or bad:

```python
# ALL GOOD thresholds
FOCUS_HIGH = 0.6        # Focus must be ≥ this
NEGATIVE_LOW = 0.4      # Fatigue/overload/stress must be ≤ this

# ALL BAD thresholds  
FOCUS_LOW = 0.4         # Focus must be ≤ this
NEGATIVE_HIGH = 0.6     # Fatigue/overload/stress must be ≥ this
```

### Decision Flow

1. **Check if ALL GOOD**: 
   ```python
   if (focus >= 0.6 and fatigue <= 0.4 and 
       overload <= 0.4 and stress <= 0.4):
       → takeoff()  # Binary jump to 1m
   ```

2. **Check if ALL BAD**:
   ```python
   elif (focus <= 0.4 and fatigue >= 0.6 and 
         overload >= 0.6 and stress >= 0.6):
       → land()  # Binary drop to 0m
   ```

3. **Otherwise (MIXED)**:
   ```python
   else:
       → turn_around()  # Rotate 180°, maintain altitude
   ```

### Example Scenarios

**✅ Scenario 1: ALL GOOD → TAKEOFF**
```
Focus: 0.8 ✅ (≥ 0.6)
Fatigue: 0.2 ✅ (≤ 0.4)
Overload: 0.3 ✅ (≤ 0.4)
Stress: 0.2 ✅ (≤ 0.4)

→ ALL parameters optimal
→ takeoff(): 0m → 1.0m (BINARY TAKEOFF)
```

**🔴 Scenario 2: ALL BAD → LAND**
```
Focus: 0.2 ❌ (≤ 0.4)
Fatigue: 0.8 ❌ (≥ 0.6)
Overload: 0.7 ❌ (≥ 0.6)
Stress: 0.9 ❌ (≥ 0.6)

→ ALL parameters critical
→ land(): 1.0m → 0.0m (BINARY LANDING)
```

**🔄 Scenario 3: MIXED → TURN AROUND**
```
Focus: 0.5 ⚠️ (between thresholds)
Fatigue: 0.5 ⚠️ (between thresholds)
Overload: 0.7 ❌ (high)
Stress: 0.3 ✅ (low)

→ Mixed parameters (some good, some bad)
→ turn_around(): 0° → 180° (VISUAL INDICATOR)
```

## 🎨 Dashboard

The frontend dashboard (`http://localhost:5173`) displays:

### Real-time Visualizations

- **System Status**: Overall cognitive health (Normal/Warning/Critical)
- **Cognitive Metrics**: Live focus, fatigue, overload, stress with trend graphs
- **Altitude Indicator**: Vertical bar showing drone altitude (0-3m range)
  - Color-coded: 🟢 Green (high) → 🔵 Blue (medium) → 🟡 Yellow (low)
  - Smooth transitions as operator state changes
- **Rotation Compass**: Circular display with rotating arrow showing drone orientation
  - Spins 180° when significant cognitive changes detected
- **Wellness Indicator**: Text-based status with emoji indicators
  - 🟢 "Performing Well" (altitude >1.5m)
  - 🔵 "Normal" (altitude 0.5-1.5m)
  - 🟡 "Struggling" (altitude 0-0.5m)
  - ⚪ "At Ground" (altitude 0m)
- **Decision Log**: Chronological feed of agent decisions and altitude changes
- **Connection Status**: WebSocket connection health

### Dashboard Features

- **Live Updates**: WebSocket-powered real-time data streaming (no refresh needed)
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Visual Feedback**: Smooth animations for altitude and rotation changes
- **Historical Context**: Recent cognitive trends and decision history

## 📚 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Quick setup, usage, commands, troubleshooting
- **[EEG_INTEGRATION.md](EEG_INTEGRATION.md)** - Real EEG hardware integration guide
- **[README.md](README.md)** - This file (comprehensive overview)

## 📝 Decision Logging

All decisions are logged to `data/logs/decisions.jsonl` in JSONL format:

```json
{
  "timestamp": "2025-11-02T10:30:45.123456+00:00",
  "cognitive_state": {
    "focus": 0.8,
    "fatigue": 0.2,
    "overload": 0.3,
    "stress": 0.2
  },
  "policy_recommendations": [
    {
      "action": "takeoff",
      "reason": "All parameters optimal - operator performing excellently",
      "parameters": {}
    }
  ],
  "llm_reasoning": "All cognitive parameters are within optimal ranges. Binary takeoff to 1 meter.",
  "actions_taken": [
    {
      "tool": "takeoff",
      "arguments": {},
      "result": {
        "success": true,
        "action": "takeoff",
        "previous_altitude_m": 0.00,
        "new_altitude_m": 1.00,
        "message": "Drone takeoff to 1.0m (from 0.00m)"
      }
    }
  ],
  "model": "gpt-4-turbo-preview"
}
```

**Example: Critical State Landing**
```json
{
  "timestamp": "2025-11-02T10:35:12.987654+00:00",
  "cognitive_state": {
    "focus": 0.2,
    "fatigue": 0.8,
    "overload": 0.7,
    "stress": 0.9
  },
  "policy_recommendations": [
    {
      "action": "land",
      "reason": "All parameters critical - operator needs immediate support",
      "parameters": {}
    }
  ],
  "llm_reasoning": "Critical state detected. All cognitive parameters indicate severe distress. Binary landing to ground.",
  "actions_taken": [
    {
      "tool": "land",
      "arguments": {},
      "result": {
        "success": true,
        "action": "land",
        "previous_altitude_m": 1.00,
        "new_altitude_m": 0.00,
        "message": "Drone landed (from 1.00m to ground level)"
      }
    }
  ],
  "model": "gpt-4-turbo-preview"
}
```

**Example: Mixed State Rotation**
```json
{
  "timestamp": "2025-11-02T10:40:30.456789+00:00",
  "cognitive_state": {
    "focus": 0.5,
    "fatigue": 0.5,
    "overload": 0.7,
    "stress": 0.3
  },
  "policy_recommendations": [
    {
      "action": "turn_around",
      "reason": "Mixed parameters - some good, some bad",
      "parameters": {}
    }
  ],
  "llm_reasoning": "Parameters are mixed. Maintaining current altitude and rotating for visual indication.",
  "actions_taken": [
    {
      "tool": "turn_around",
      "arguments": {},
      "result": {
        "success": true,
        "action": "turn_around",
        "previous_rotation_deg": 0.0,
        "new_rotation_deg": 180.0,
        "message": "Drone rotated 180° (from 0.0° to 180.0°)"
      }
    }
  ],
  "model": "gpt-4-turbo-preview"
}
```

### Log Analysis

Each log entry contains:
- **Cognitive state**: Raw metrics from EEG (focus, fatigue, overload, stress)
- **All good/bad flags**: Boolean flags indicating if ALL parameters met thresholds
- **Policy recommendations**: What the rule-based system suggests (move_up, land, or nothing)
- **LLM reasoning**: Why the AI decided to act (if LLM enabled)
- **Actions taken**: Which tools were executed and their results
- **Altitude changes**: Before/after altitude in meters

## 🧪 Testing

**Run EEG simulator standalone:**
```bash
python src/sim/eeg_simulator.py
```

**Run drone simulator standalone:**
```bash
python src/sim/drone_simulator.py
```

**Test API endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Process cognitive state
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"focus": 0.5, "fatigue": 0.7, "overload": 0.6, "stress": 0.4}'

# Get logs
curl http://localhost:8000/logs?count=5
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key for LLM reasoning
- `AGENT_MODE` - `simulation` or `production`
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Simulation Scenarios

- **normal**: Stable cognitive state with minor variations
- **fatigue**: Gradual increase in fatigue and decrease in focus
- **stress**: High stress and cognitive overload
- **degrading**: Cyclic degradation pattern over time

## 📦 Dependencies

### Python
- fastapi - Web framework
- uvicorn - ASGI server
- openai - LLM integration
- websockets - Real-time communication
- pydantic - Data validation

### Node.js
- react - UI framework
- vite - Build tool
- recharts - Data visualization

## 🛣️ 24-Hour Build Roadmap

### Phase 1: Core Setup (Hours 0-2)
✅ Project structure
✅ Agent components (policy, tools, memory)
✅ Simulators (EEG, drone)

### Phase 2: Intelligence (Hours 3-6)
✅ LLM agent integration
✅ Function calling implementation
✅ Decision logging system

### Phase 3: API Layer (Hours 7-10)
✅ FastAPI server
✅ WebSocket streaming
✅ REST endpoints

### Phase 4: Frontend (Hours 11-16)
✅ React dashboard
✅ Real-time visualizations
✅ WebSocket client

### Phase 5: Integration (Hours 17-20)
✅ End-to-end testing
✅ Startup scripts
✅ Documentation

### Phase 6: Polish (Hours 21-24)
✅ Error handling
✅ Performance optimization
✅ Demo scenarios

## 🚨 Troubleshooting

**Backend won't start:**
- Check Python version: `python3 --version` (need 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is available: `lsof -i :8000`

**Frontend won't start:**
- Check Node version: `node --version` (need 18+)
- Install dependencies: `cd ui/frontend && npm install`
- Check port 5173 is available: `lsof -i :5173`

**LLM not working:**
- Check your `.env` file contains `OPENAI_API_KEY=sk-...`
- Verify API key format: Should start with `sk-`
- System falls back to policy-only mode automatically

**WebSocket connection fails:**
- Ensure backend is running on port 8000
- Check browser console for error messages
- Try manual reconnection (5-second auto-retry enabled)

## 📚 Further Development

### Current System (v1.0 - Binary Control ✅)
- ✅ Binary control (3 clear states: 1m, 0m, or rotating)
- ✅ Instant altitude response (no gradual movement)
- ✅ takeoff() to 1m when ALL parameters good
- ✅ land() to 0m when ALL parameters bad
- ✅ turn_around() 180° for mixed states
- ✅ Real EEG integration via REST API
- ✅ LLM-enhanced decision making (optional)
- ✅ Real-time dashboard with altitude + rotation indicators
- ✅ Guard system (no unnecessary actions)

### Planned Enhancements

**Phase 1: Enhanced Visualizations**
- 3D drone position rendering
- Historical altitude graph with trend lines
- Predictive trajectory based on cognitive trends
- Audio alerts for altitude changes
- Mobile app for remote monitoring

**Phase 2: Advanced Control**
- Gradient thresholds (beyond binary all-or-nothing)
- Incremental altitude adjustments (10cm, 20cm, 30cm steps)
- Composite score formula for nuanced states
- Multiple altitude zones (0-3m range with zones)
- Smooth altitude transitions (not instant binary jumps)
- Variable movement speed based on state severity
- Pattern recognition for common cognitive states
- Machine learning for personalized thresholds

**Phase 3: Human-in-the-Loop**
- Voice confirmation for actions (Coval integration)
- Operator override capabilities
- Configurable automation levels
- Emergency stop mechanism
- Multi-operator collaboration

**Phase 4: Production Features**
- Replace `DroneSimulator` with real drone API (DJI SDK, etc.)
- Hardware health monitoring and failsafes
- Multi-drone fleet management
- Historical analytics and performance tracking
- Integration with mission planning systems

**Phase 5: Deployment & Scale**
- Docker containerization
- Cloud deployment (AWS/GCP/Azure)
- Load balancing for multiple operators
- Kubernetes orchestration
- CI/CD pipeline
- Production monitoring (Datadog, New Relic)

### Research Directions
- Predictive fatigue modeling with ML
- Transfer learning across operators
- Stress pattern recognition
- Context-aware threshold adjustment
- Multi-modal sensing (EEG + eye tracking + heart rate)

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

## 🏆 About This Version

This is the **binary hackathon version** of MindAware, optimized for:
- **Three clear states**: At 1m, at ground, or rotating
- **Instant response**: No gradual movement - binary jumps to 1m or 0m
- **Visual clarity**: Height + rotation = instant state comprehension
- **Easy explanation**: No complex formulas, just clear binary thresholds
- **Quick setup**: Runs in seconds, demos in minutes

The binary control approach makes cognitive monitoring **crystal clear** for hackathon judges and audiences. The drone has only three states: up (excellent), down (critical), or spinning (mixed). No gradients, no confusion.

**Why binary control?**
- Three visual states are universally understood
- Instant altitude changes are dramatic and clear
- At 1m = good, at 0m = bad, rotating = mixed
- Perfect for 5-minute hackathon presentations
- Judges can see state changes instantly

**Future versions** will include gradient control, multiple altitude zones, and smooth transitions. See [Further Development](#-further-development) for the roadmap.

---

**Built with ❤️ for safer, smarter human-machine collaboration**  
*Optimized for HackNYU 2025 🎓*

