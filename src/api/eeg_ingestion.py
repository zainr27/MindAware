"""
EEG data ingestion endpoints for receiving real-time BCI data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.sim.eeg_adapter import get_adapter


router = APIRouter()

# Global storage for latest drone command (for partner integration)
_latest_drone_command: Optional[Dict[str, Any]] = None


class EEGDataRequest(BaseModel):
    """Raw EEG data from partner's hardware."""
    raw_string: str
    timestamp: Optional[str] = None


class EEGDataBatchRequest(BaseModel):
    """Batch of EEG readings."""
    readings: list[str]


@router.post("/eeg/ingest")
async def ingest_eeg_data(request: EEGDataRequest):
    """
    Ingest a single raw EEG reading.
    
    Partner's code should POST here with format:
    {
        "raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
    }
    """
    try:
        adapter = get_adapter()
        success = adapter.add_reading(request.raw_string)
        
        if not success:
            return {
                "status": "error",
                "message": "Failed to parse EEG data",
                "raw_string": request.raw_string
            }
        
        return {
            "status": "success",
            "message": "EEG data ingested",
            "buffer_size": len(adapter.readings_buffer),
            "calibrated": adapter.is_calibrated,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eeg/ingest/batch")
async def ingest_eeg_batch(request: EEGDataBatchRequest):
    """
    Ingest multiple EEG readings at once.
    
    Useful for catching up on buffered data.
    """
    try:
        adapter = get_adapter()
        success_count = 0
        
        for raw_string in request.readings:
            if adapter.add_reading(raw_string):
                success_count += 1
        
        return {
            "status": "success",
            "message": f"Ingested {success_count}/{len(request.readings)} readings",
            "success_count": success_count,
            "total_count": len(request.readings),
            "buffer_size": len(adapter.readings_buffer),
            "calibrated": adapter.is_calibrated
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eeg/status")
async def get_eeg_status():
    """Get current EEG adapter status."""
    try:
        adapter = get_adapter()
        status = adapter.get_status()
        
        return {
            "status": "operational",
            "adapter": status,
            "last_state": adapter.last_cognitive_state,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eeg/state")
async def get_current_eeg_state():
    """Get current computed cognitive state from real EEG."""
    try:
        adapter = get_adapter()
        state = adapter.get_cognitive_state()
        return state
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eeg/calibrate")
async def trigger_calibration():
    """Manually trigger calibration (usually automatic)."""
    try:
        adapter = get_adapter()
        adapter._calibrate()
        
        return {
            "status": "success",
            "message": "Calibration triggered",
            "calibrated": adapter.is_calibrated,
            "baseline_focus": adapter.baseline_focus,
            "baseline_yaw_variance": adapter.baseline_yaw_variance,
            "baseline_blink_rate": adapter.baseline_blink_rate
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/eeg/reset")
async def reset_eeg_adapter():
    """Reset the EEG adapter (clears buffer and calibration)."""
    try:
        adapter = get_adapter()
        adapter.reset()
        
        return {
            "status": "success",
            "message": "EEG adapter reset",
            "buffer_size": len(adapter.readings_buffer)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Drone Command Endpoints (for partner integration)

def set_latest_drone_command(command: str, reasoning: str = "", metadata: Optional[Dict[str, Any]] = None):
    """
    Store the latest drone command (called by agent when decision is made).
    
    Maps MindAware commands to partner's drone step names:
    - 'takeoff' → 'TAKEOFF'
    - 'land' → 'LAND'
    - 'yaw_right' → 'YAW RIGHT'
    - 'maintain' → 'maintain' (no action)
    
    Args:
        command: 'takeoff', 'land', 'yaw_right', or 'maintain'
        reasoning: Why this command was chosen
        metadata: Additional context (altitude, cognitive state, etc.)
    """
    global _latest_drone_command
    
    # Map to partner's exact step names
    command_mapping = {
        'takeoff': 'TAKEOFF',
        'land': 'LAND',
        'yaw_right': 'YAW RIGHT',
        'maintain': 'maintain'
    }
    
    partner_command = command_mapping.get(command, command)
    
    _latest_drone_command = {
        "command": partner_command,  # Partner's exact step name
        "mindaware_command": command,  # Our internal command name
        "reasoning": reasoning,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/drone/command")
async def get_drone_command():
    """
    Get the latest drone command from MindAware.
    
    Returns partner's exact step names: ["TAKEOFF", "YAW RIGHT", "LAND", "maintain"]
    
    Partner's drone code should poll this endpoint every 1-3 seconds:
    
    ```python
    response = requests.get("http://localhost:8000/drone/command")
    data = response.json()
    
    # data['command'] will be exact step name: "TAKEOFF", "LAND", or "YAW RIGHT"
    if data['command'] == 'TAKEOFF':
        drone.execute_step('TAKEOFF')
    elif data['command'] == 'LAND':
        drone.execute_step('LAND')
    elif data['command'] == 'YAW RIGHT':
        drone.execute_step('YAW RIGHT')
    # 'maintain' = do nothing
    ```
    
    Returns:
        command: Partner's exact step name ('TAKEOFF', 'LAND', 'YAW RIGHT', or 'maintain')
        mindaware_command: Our internal command name ('takeoff', 'land', 'yaw_right')
        reasoning: Why this command was chosen
        timestamp: When the command was issued
    """
    global _latest_drone_command
    
    if _latest_drone_command is None:
        return {
            "command": "maintain",
            "mindaware_command": "maintain",
            "reasoning": "No decision made yet (calibrating or waiting for data)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return _latest_drone_command


@router.get("/drone/status")
async def get_drone_status():
    """
    Get comprehensive drone status including latest command and cognitive state.
    
    Useful for debugging - shows everything in one place.
    """
    global _latest_drone_command
    
    try:
        adapter = get_adapter()
        cognitive_state = adapter.last_cognitive_state
        
        return {
            "latest_command": _latest_drone_command or {
                "command": "maintain",
                "reasoning": "No command yet"
            },
            "cognitive_state": cognitive_state,
            "eeg_calibrated": adapter.is_calibrated,
            "buffer_size": len(adapter.readings_buffer),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

