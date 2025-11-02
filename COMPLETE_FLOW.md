# 🔄 Complete MindAware ↔ Drone Integration Flow

## The Full Loop (Every 2-3 Seconds)

```
┌─────────────────────────────────────────────────────────────────┐
│ PARTNER'S COMPUTER                                              │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │ EEG Hardware │ ──────▶ │ BrainFlow    │                    │
│  │ (Headset)    │         │ Board        │                    │
│  └──────────────┘         └──────┬───────┘                    │
│                                   │                             │
│                                   │ raw_eeg_string             │
│                                   ▼                             │
│  ┌─────────────────────────────────────────────┐               │
│  │ Her Python Code:                            │               │
│  │                                             │               │
│  │ 1. Get EEG:                                 │               │
│  │    raw = "F[focus:0.12] Y[...] B[...]"     │               │
│  │                                             │               │
│  │ 2. Send to MindAware:                       │               │
│  │    POST http://localhost:8000/eeg/ingest   │ ──┐           │
│  │    {"raw_string": raw}                      │   │           │
│  │                                             │   │           │
│  │ 3. Get command from MindAware:              │   │           │
│  │    GET http://localhost:8000/drone/command │◀──┼─┐         │
│  │    → {'command': 'takeoff'}                 │   │ │         │
│  │                                             │   │ │         │
│  │ 4. Execute on drone:                        │   │ │         │
│  │    if cmd == 'takeoff': drone.takeoff()    │   │ │         │
│  │    elif cmd == 'land': drone.land()        │   │ │         │
│  └─────────────────────────────────────────────┘   │ │         │
│                                                     │ │         │
└─────────────────────────────────────────────────────┼─┼─────────┘
                                                      │ │
                           ┌──────────────────────────┘ │
                           │  EEG data                   │
                           │                             │ Command
                           ▼                             │
┌─────────────────────────────────────────────────────────────────┐
│ YOUR COMPUTER (MindAware)                            │           │
│                                                      │           │
│  ┌────────────────────────────────────────────────┐ │           │
│  │ API Server (port 8000)                         │ │           │
│  │                                                │ │           │
│  │  POST /eeg/ingest ────────────────────┐       │ │           │
│  │  GET  /drone/command ◀─────────┐      │       │ │           │
│  └───────────────────────┼─────────┼──────┘       │ │           │
│                          │         │              │ │           │
│                          ▼         │              │ │           │
│  ┌────────────────────────────────────────────┐   │ │           │
│  │ EEG Adapter                                │   │ │           │
│  │ • Parses: "F[focus:0.12]..."              │   │ │           │
│  │ • Buffers: Last 60 readings               │   │ │           │
│  │ • Calibrates: Baseline values             │   │ │           │
│  │ • Transforms:                              │   │ │           │
│  │   - focus (direct)                         │   │ │           │
│  │   - fatigue (from focus history)           │   │ │           │
│  │   - overload (from yaw variance)           │   │ │           │
│  │   - stress (from yaw imbalance)            │   │ │           │
│  └──────────────────┬─────────────────────────┘   │ │           │
│                     │                              │ │           │
│                     ▼                              │ │           │
│  ┌────────────────────────────────────────────┐   │ │           │
│  │ Agent Loop (every 3 seconds)               │   │ │           │
│  │                                            │   │ │           │
│  │  1. Get cognitive state:                   │   │ │           │
│  │     {focus: 0.12, fatigue: 0.87,          │   │ │           │
│  │      overload: 0.45, stress: 0.52}        │   │ │           │
│  │                                            │   │ │           │
│  │  2. Check policy:                          │   │ │           │
│  │     All bad? → recommend 'land'            │   │ │           │
│  │     All good? → recommend 'takeoff'        │   │ │           │
│  │     Mixed? → recommend 'turn_around'       │   │ │           │
│  │                                            │   │ │           │
│  │  3. LLM reasoning (if enabled):            │   │ │           │
│  │     OpenAI analyzes + confirms/overrides   │   │ │           │
│  │                                            │   │ │           │
│  │  4. Store command: ─────────────────────────────┘           │
│  │     set_latest_drone_command('land')       │                 │
│  │                                            │                 │
│  │  5. Broadcast to dashboard via WebSocket   │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                 │
│  ┌────────────────────────────────────────────┐                 │
│  │ Dashboard (port 5173)                      │                 │
│  │ • Shows cognitive metrics in real-time     │                 │
│  │ • Displays drone commands                  │                 │
│  │ • Logs LLM reasoning                       │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Format Examples

### 1. Partner Sends EEG → MindAware
```python
POST http://localhost:8000/eeg/ingest
{
  "raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=-188.587 B[rate0.5=0.00]"
}
```

### 2. MindAware Transforms to Cognitive State
```python
{
  "focus": 0.12,      # Direct from EEG
  "fatigue": 0.87,    # Calculated from sustained low focus
  "overload": 0.45,   # Calculated from yaw instability
  "stress": 0.52,     # Calculated from yaw imbalance + blink rate
  "calibrated": true
}
```

### 3. MindAware Decides Action
```python
# Policy evaluates:
ALL BAD (focus ≤ 0.4 AND fatigue ≥ 0.6 AND overload ≥ 0.6 AND stress ≥ 0.6)
→ Recommendation: LAND

# LLM confirms:
"All cognitive parameters are critical. Operator fatigue is very high (0.87) 
 and focus is extremely low (0.12). Safety requires immediate landing."
→ Action: land()
```

### 4. Partner Gets Command from MindAware
```python
GET http://localhost:8000/drone/command

Response:
{
  "command": "land",
  "reasoning": "All cognitive parameters are critical...",
  "timestamp": "2025-11-02T11:30:45.123Z",
  "metadata": {
    "cognitive_state": {"focus": 0.12, "fatigue": 0.87, ...},
    "altitude": 0.0
  }
}
```

### 5. Partner Executes Command
```python
if command == 'land':
    drone.land()  # Partner's drone API
```

---

## Binary Control Logic

### ✅ ALL GOOD → TAKEOFF to 1m
```
focus ≥ 0.6  AND  fatigue ≤ 0.4  AND  overload ≤ 0.4  AND  stress ≤ 0.4
```

### 🔴 ALL BAD → LAND to 0m
```
focus ≤ 0.4  AND  fatigue ≥ 0.6  AND  overload ≥ 0.6  AND  stress ≥ 0.6
```

### 🔄 MIXED → TURN AROUND 180°
```
Some parameters good, some bad
```

---

## Integration Checklist

- [x] **API Server** running on port 8000
- [x] **Agent Loop** running with `--real-eeg --llm`
- [x] **Frontend** running on port 5173
- [ ] **Partner's EEG code** sending to `/eeg/ingest`
- [ ] **Partner's drone code** polling `/drone/command`
- [ ] **Test full loop** end-to-end

---

## Testing the Integration

### 1. Check API is running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 2. Test EEG ingestion:
```bash
curl -X POST http://localhost:8000/eeg/ingest \
  -H "Content-Type: application/json" \
  -d '{"raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=-188.587 B[rate0.5=0.00]"}'
```

### 3. Check drone command:
```bash
curl http://localhost:8000/drone/command
# Returns: {"command": "maintain", "reasoning": "..."}
```

### 4. Monitor dashboard:
```
Open: http://localhost:5173
```

---

## Troubleshooting

### Partner can't connect
- Check she's using `http://localhost:8000` (not your IP)
- Verify API server is running: `lsof -i :8000`
- Test with curl first before Python

### No commands appearing
- Wait 30 seconds for calibration
- Check agent is running: `ps aux | grep "src/main.py"`
- Check `/drone/status` endpoint for debug info

### Commands not updating
- Make sure EEG data is flowing (check logs)
- Verify cognitive state is changing
- Check dashboard for decision logs

---

## Next Steps

1. Partner adds 2 lines to her EEG code
2. Partner adds 2 lines to her drone code
3. Run both systems
4. Watch the magic happen! 🚀

