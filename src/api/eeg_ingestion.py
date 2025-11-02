"""
EEG data ingestion endpoints for receiving real-time BCI data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.sim.eeg_adapter import get_adapter


router = APIRouter()


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

