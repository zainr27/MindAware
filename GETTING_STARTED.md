# 🚀 Getting Started with MindAware

Quick guide to get MindAware running in minutes.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API Key (in `.env` file)

---

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
# Python packages
pip3 install -r requirements.txt

# Frontend packages
cd ui/frontend
npm install
cd ../..
```

### 2. Run a Quick Test

```bash
# Run a short simulation with LLM
python3 src/main.py --scenario stress --iterations 5 --interval 2 --llm
```

**Note**: Your OpenAI API key is already configured in the `.env` file.

**Expected output:**
- `[INIT] LLM agent enabled`
- 5 iterations with EEG states
- Policy recommendations
- LLM decisions and tool executions
- Final summary with trends

---

## Run Full System with Dashboard

### Option 1: One-Command Startup

```bash
./run.sh
```

This will:
1. Start backend API at `http://localhost:8000`
2. Start frontend dashboard at `http://localhost:5173`
3. Optionally start the simulation loop

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd src/api
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd ui/frontend
npm run dev
```

**Terminal 3 - Simulation:**
```bash
python3 src/main.py --scenario fatigue --iterations 20 --interval 3 --llm
```

**Open Browser:**
- Dashboard: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Command Reference

### Basic Usage

```bash
python3 src/main.py [OPTIONS]
```

**Options:**
- `--scenario` - Simulation scenario: `normal`, `fatigue`, `stress`, `degrading`
- `--iterations` - Number of cycles (default: 10)
- `--interval` - Seconds between cycles (default: 3.0)
- `--llm` - Enable LLM reasoning (requires API key)
- `--real-eeg` - Use real EEG hardware (see EEG_INTEGRATION.md)
- `--no-sim` - Skip simulation (API-only mode)

### Example Commands

**Stress scenario with LLM:**
```bash
python3 src/main.py --scenario stress --iterations 15 --interval 2 --llm
```

**Fatigue scenario, fast updates:**
```bash
python3 src/main.py --scenario fatigue --iterations 20 --interval 1 --llm
```

**Policy-only mode (no LLM):**
```bash
python3 src/main.py --scenario degrading --iterations 10 --interval 2
```

**Real EEG hardware mode:**
```bash
python3 src/main.py --real-eeg --llm --iterations 20
```

---

## Scenarios Explained

| Scenario | Behavior | Best For |
|----------|----------|----------|
| `normal` | Stable cognitive state with minor variations | Baseline testing |
| `fatigue` | Gradual increase in fatigue, decrease in focus | Long mission simulation |
| `stress` | High stress and cognitive overload (0.7-0.8) | Emergency scenarios |
| `degrading` | Cyclic up/down pattern over 20 iterations | Realistic fatigue patterns |

---

## API Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Process Cognitive State
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "focus": 0.3,
    "fatigue": 0.8,
    "overload": 0.7,
    "stress": 0.6
  }'
```

### Get Decision Logs
```bash
curl http://localhost:8000/logs?count=10
```

### Get Memory Summary
```bash
curl http://localhost:8000/memory
```

---

## View Results

### Check Decision Logs
```bash
# View all decisions
cat data/logs/decisions.jsonl

# Pretty print last decision
tail -1 data/logs/decisions.jsonl | python3 -m json.tool

# View last 10 decisions
tail -10 data/logs/decisions.jsonl | python3 -m json.tool
```

### System Status
```bash
# Check API status
curl http://localhost:8000/

# Get tool status
curl http://localhost:8000/tools/status
```

---

## What the System Does

### Cognitive Monitoring
The system monitors four key cognitive dimensions:
- **Focus** (0-1): Attention and concentration level
- **Fatigue** (0-1): Mental exhaustion and tiredness
- **Overload** (0-1): Cognitive load and task saturation
- **Stress** (0-1): Psychological pressure

### Agent Actions
The agent can autonomously call these tools:
1. **set_flight_mode** - Switch between manual/assisted/autonomous/return_to_base
2. **change_search_pattern** - Adjust mission complexity
3. **throttle_alerts** - Filter information to reduce cognitive load
4. **send_sitrep** - Notify operators of state changes

### Decision Pipeline
```
EEG State → Policy Rules → LLM Reasoning → Tool Execution → Logging → Dashboard
```

---

## Dashboard Features

The frontend dashboard displays:
- **System Status**: Overall cognitive health (Normal/Warning/Critical)
- **Cognitive Metrics**: Real-time focus, fatigue, overload, stress with trend graphs
- **Drone Status**: Flight mode, battery, mission progress, telemetry
- **Decision Log**: Chronological feed of agent decisions and actions
- **Connection Status**: WebSocket connection indicator

---

## Troubleshooting

### "LLM agent not initialized"
```bash
# Check your .env file has the API key
cat .env | grep OPENAI_API_KEY
```

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill process if needed
kill -9 <PID>
```

### Frontend Won't Connect
1. Ensure backend is running: `curl http://localhost:8000/health`
2. Refresh browser
3. Check browser console for errors
4. Verify WebSocket connection to `ws://localhost:8000/ws`

### Missing Dependencies
```bash
# Reinstall Python packages
pip3 install -r requirements.txt

# Reinstall Node packages
cd ui/frontend && npm install
```

---

## Configuration

### Environment Variables (`.env` file)
- `OPENAI_API_KEY` - Your OpenAI API key (required for LLM)
- `AGENT_MODE` - `simulation` or `production`
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Policy Thresholds (`src/agent/policy.py`)
```python
focus_low = 0.3           # Below this = low attention warning
fatigue_warning = 0.6     # Above this = fatigue warning
fatigue_critical = 0.8    # Above this = critical intervention
overload_warning = 0.7    # Above this = reduce complexity
overload_critical = 0.85  # Above this = full autonomy
```

---

## Next Steps

- **Customize thresholds**: Edit `src/agent/policy.py`
- **Add new tools**: Edit `src/agent/tools.py`
- **Modify dashboard**: Edit components in `ui/frontend/src/components/`
- **Integrate real EEG**: See `EEG_INTEGRATION.md`
- **API Documentation**: View at http://localhost:8000/docs

---

## Quick Reference

### Project Structure
```
MindAware/
├── src/
│   ├── agent/          # AI agent components
│   ├── api/            # FastAPI server & WebSocket
│   ├── sim/            # EEG & drone simulators
│   └── main.py         # Main orchestrator
├── ui/frontend/        # React dashboard
├── data/logs/          # Decision logs
├── .env                # Environment configuration
└── run.sh              # One-command startup
```

### Common Commands
```bash
# Full system
./run.sh

# Simulation only
python3 src/main.py --scenario stress --iterations 10 --llm

# API only
cd src/api && uvicorn server:app --reload

# Frontend only
cd ui/frontend && npm run dev

# View logs
tail -f data/logs/decisions.jsonl | python3 -m json.tool
```

---

**Need more help?** Check the main [README.md](README.md) or [EEG_INTEGRATION.md](EEG_INTEGRATION.md) for hardware integration.

