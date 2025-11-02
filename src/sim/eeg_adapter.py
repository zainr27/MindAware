"""
Real EEG adapter for processing live BCI data.
Transforms raw EEG readings into cognitive state metrics.
"""

import re
import statistics
from typing import Dict, Any, Optional, List
from collections import deque
from datetime import datetime, timezone
import time


class EEGReading:
    """Single parsed EEG reading."""
    
    def __init__(self, focus: float, not_focus: float, yaw_left: float, 
                 yaw_right: float, yaw_absolute: float, blink_rate: float):
        self.focus = focus
        self.not_focus = not_focus
        self.yaw_left = yaw_left
        self.yaw_right = yaw_right
        self.yaw_absolute = yaw_absolute
        self.blink_rate = blink_rate
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "not_focus": self.not_focus,
            "yaw_left": self.yaw_left,
            "yaw_right": self.yaw_right,
            "yaw_absolute": self.yaw_absolute,
            "blink_rate": self.blink_rate,
            "timestamp": self.timestamp
        }


class RealEEGAdapter:
    """
    Adapter for real EEG hardware data.
    
    Parses raw EEG strings and transforms them into cognitive state metrics
    compatible with MindAware agent.
    """
    
    def __init__(self, buffer_size: int = 60, calibration_samples: int = 30):
        """
        Initialize the EEG adapter.
        
        Args:
            buffer_size: Number of readings to keep in rolling buffer
            calibration_samples: Number of samples needed for calibration
        """
        # Rolling buffers for statistics
        self.buffer_size = buffer_size
        self.readings_buffer = deque(maxlen=buffer_size)
        
        # Calibration
        self.calibration_samples = calibration_samples
        self.is_calibrated = False
        self.baseline_focus = 0.5
        self.baseline_yaw_variance = 100.0
        self.baseline_blink_rate = 0.0
        self.max_observed_yaw_variance = 500.0
        
        # Last computed state (for API access)
        self.last_cognitive_state: Optional[Dict[str, Any]] = None
        self.iteration_count = 0
        
        print("[EEG] Real EEG Adapter initialized")
        print(f"[EEG] Buffer size: {buffer_size}, Calibration samples: {calibration_samples}")
    
    def parse_eeg_string(self, raw_string: str) -> Optional[EEGReading]:
        """
        Parse raw EEG string into structured data.
        
        Example input:
        "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
        
        Args:
            raw_string: Raw EEG data string
        
        Returns:
            EEGReading object or None if parsing fails
        """
        try:
            # Strip any prefix before the actual data (e.g. "not_focus | " or "yaw_left | ")
            if " | " in raw_string:
                raw_string = raw_string.split(" | ", 1)[1]
            # Extract focus values
            focus_match = re.search(r'focus:([\d.]+)', raw_string)
            not_focus_match = re.search(r'not_focus:([\d.]+)', raw_string)
            
            # Extract yaw values
            yaw_left_match = re.search(r'yaw_left:([\d.]+)', raw_string)
            yaw_right_match = re.search(r'yaw_right:([\d.]+)', raw_string)
            yaw_abs_match = re.search(r'yaw=(-?[\d.]+)', raw_string)  # Allow negative yaw
            
            # Extract blink rate
            blink_match = re.search(r'rate[\d.]+=([\d.]+)', raw_string)
            
            if not all([focus_match, not_focus_match, yaw_left_match, 
                       yaw_right_match, yaw_abs_match, blink_match]):
                print(f"[EEG] Warning: Could not parse all fields from: {raw_string}")
                return None
            
            reading = EEGReading(
                focus=float(focus_match.group(1)),
                not_focus=float(not_focus_match.group(1)),
                yaw_left=float(yaw_left_match.group(1)),
                yaw_right=float(yaw_right_match.group(1)),
                yaw_absolute=float(yaw_abs_match.group(1)),
                blink_rate=float(blink_match.group(1))
            )
            
            return reading
        
        except Exception as e:
            print(f"[EEG] Error parsing EEG string: {e}")
            return None
    
    def add_reading(self, raw_string: str) -> bool:
        """
        Add a new raw EEG reading to the buffer.
        
        Args:
            raw_string: Raw EEG data string
        
        Returns:
            True if successfully parsed and added
        """
        reading = self.parse_eeg_string(raw_string)
        if reading:
            self.readings_buffer.append(reading)
            
            # Auto-calibrate after collecting enough samples
            if not self.is_calibrated and len(self.readings_buffer) >= self.calibration_samples:
                self._calibrate()
            
            return True
        return False
    
    def _calibrate(self) -> None:
        """Calibrate baseline values from initial readings."""
        if len(self.readings_buffer) < self.calibration_samples:
            print(f"[EEG] Not enough samples for calibration: {len(self.readings_buffer)}/{self.calibration_samples}")
            return
        
        # Calculate baseline values
        focus_values = [r.focus for r in list(self.readings_buffer)[:self.calibration_samples]]
        yaw_values = [r.yaw_absolute for r in list(self.readings_buffer)[:self.calibration_samples]]
        blink_values = [r.blink_rate for r in list(self.readings_buffer)[:self.calibration_samples]]
        
        self.baseline_focus = statistics.mean(focus_values)
        self.baseline_yaw_variance = statistics.stdev(yaw_values) if len(yaw_values) > 1 else 100.0
        self.baseline_blink_rate = statistics.mean(blink_values)
        
        # Set max variance threshold (start with 3x baseline)
        self.max_observed_yaw_variance = max(self.baseline_yaw_variance * 3, 500.0)
        
        self.is_calibrated = True
        
        print(f"[EEG] ✅ Calibration complete!")
        print(f"[EEG]    Baseline focus: {self.baseline_focus:.3f}")
        print(f"[EEG]    Baseline yaw variance: {self.baseline_yaw_variance:.2f}")
        print(f"[EEG]    Baseline blink rate: {self.baseline_blink_rate:.3f}")
    
    def _calculate_fatigue(self) -> float:
        """
        Calculate fatigue from focus history and blink rate.
        
        Formula: fatigue = (1 - avg_focus_last_minute) * 0.7 + blink_rate_normalized * 0.3
        """
        if len(self.readings_buffer) < 2:
            return 0.2
        
        # Get last 60 seconds worth (assuming ~1 reading per second)
        recent_readings = list(self.readings_buffer)
        
        # Average focus over last minute
        focus_values = [r.focus for r in recent_readings]
        avg_focus = statistics.mean(focus_values)
        
        # Normalize blink rate (assume 0-1 range, higher = more fatigue)
        blink_values = [r.blink_rate for r in recent_readings]
        avg_blink = statistics.mean(blink_values)
        normalized_blink = min(avg_blink / max(self.baseline_blink_rate * 2, 0.1), 1.0)
        
        # Combined fatigue score
        fatigue = (1 - avg_focus) * 0.7 + normalized_blink * 0.3
        
        return max(0.0, min(1.0, fatigue))
    
    def _calculate_overload(self) -> float:
        """
        Calculate cognitive overload from yaw instability.
        
        Formula: overload = std_deviation(last_20_yaw_values) / calibrated_max
        """
        if len(self.readings_buffer) < 3:
            return 0.3
        
        # Get last 20 readings for variance calculation
        recent_readings = list(self.readings_buffer)[-20:]
        yaw_values = [r.yaw_absolute for r in recent_readings]
        
        if len(yaw_values) < 2:
            return 0.3
        
        # Calculate standard deviation
        yaw_variance = statistics.stdev(yaw_values)
        
        # Update max observed variance
        if yaw_variance > self.max_observed_yaw_variance:
            self.max_observed_yaw_variance = yaw_variance
        
        # Normalize to 0-1 range
        overload = yaw_variance / self.max_observed_yaw_variance
        
        return max(0.0, min(1.0, overload))
    
    def _calculate_stress(self) -> float:
        """
        Calculate stress from yaw imbalance, blink anomaly, and focus instability.
        
        Formula: stress = yaw_imbalance * 0.4 + blink_anomaly * 0.3 + focus_variance * 0.3
        """
        if len(self.readings_buffer) < 3:
            return 0.3
        
        recent_readings = list(self.readings_buffer)[-30:]
        
        # 1. Yaw imbalance (extreme left/right preference)
        latest = recent_readings[-1]
        yaw_imbalance = abs(latest.yaw_left - latest.yaw_right)
        
        # 2. Blink anomaly (deviation from baseline)
        blink_values = [r.blink_rate for r in recent_readings]
        avg_blink = statistics.mean(blink_values)
        blink_anomaly = abs(avg_blink - self.baseline_blink_rate) / max(self.baseline_blink_rate + 0.1, 0.1)
        blink_anomaly = min(blink_anomaly, 1.0)
        
        # 3. Focus instability (variance in focus)
        focus_values = [r.focus for r in recent_readings]
        focus_variance = statistics.stdev(focus_values) if len(focus_values) > 1 else 0.0
        # Normalize (assume max variance of 0.3 for focus)
        focus_variance_normalized = min(focus_variance / 0.3, 1.0)
        
        # Combined stress score
        stress = yaw_imbalance * 0.4 + blink_anomaly * 0.3 + focus_variance_normalized * 0.3
        
        return max(0.0, min(1.0, stress))
    
    def get_cognitive_state(self) -> Dict[str, Any]:
        """
        Get current cognitive state (compatible with EEGSimulator interface).
        
        Returns:
            Dict with focus, fatigue, overload, stress (0-1 scale)
        """
        self.iteration_count += 1
        
        # If not enough data yet, return safe defaults
        if len(self.readings_buffer) < 2:
            print(f"[EEG] Insufficient data: {len(self.readings_buffer)} readings")
            return {
                "focus": 0.5,
                "fatigue": 0.2,
                "overload": 0.3,
                "stress": 0.3,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "real_eeg",
                "status": "insufficient_data",
                "calibrated": self.is_calibrated,
                "buffer_size": len(self.readings_buffer)
            }
        
        # Get latest reading for direct values
        latest = self.readings_buffer[-1]
        
        # Calculate derived metrics
        focus = latest.focus  # Direct from hardware
        fatigue = self._calculate_fatigue()
        overload = self._calculate_overload()
        stress = self._calculate_stress()
        
        state = {
            "focus": round(focus, 3),
            "fatigue": round(fatigue, 3),
            "overload": round(overload, 3),
            "stress": round(stress, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "real_eeg",
            "calibrated": self.is_calibrated,
            "buffer_size": len(self.readings_buffer),
            "raw_data": {
                "yaw_left": latest.yaw_left,
                "yaw_right": latest.yaw_right,
                "yaw_absolute": latest.yaw_absolute,
                "blink_rate": latest.blink_rate
            }
        }
        
        self.last_cognitive_state = state
        return state
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status information."""
        return {
            "is_calibrated": self.is_calibrated,
            "buffer_size": len(self.readings_buffer),
            "buffer_capacity": self.buffer_size,
            "readings_received": self.iteration_count,
            "baseline_focus": self.baseline_focus,
            "baseline_yaw_variance": self.baseline_yaw_variance,
            "baseline_blink_rate": self.baseline_blink_rate
        }
    
    def reset(self) -> None:
        """Reset the adapter state."""
        self.readings_buffer.clear()
        self.is_calibrated = False
        self.last_cognitive_state = None
        self.iteration_count = 0
        print("[EEG] Adapter reset")


# Global adapter instance
_adapter_instance: Optional[RealEEGAdapter] = None


def get_adapter() -> RealEEGAdapter:
    """Get or create the global adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = RealEEGAdapter()
    return _adapter_instance


if __name__ == "__main__":
    # Test the adapter with sample data
    print("EEG Adapter Test")
    print("=" * 60)
    
    adapter = RealEEGAdapter(buffer_size=60, calibration_samples=10)
    
    # Simulate incoming data
    test_samples = [
        "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]",
        "F[not_focus:0.85 focus:0.15] Y[yaw_left:0.31 yaw_right:0.69] yaw=3420.123 B[rate0.5=0.02]",
        "F[not_focus:0.82 focus:0.18] Y[yaw_left:0.28 yaw_right:0.72] yaw=3418.456 B[rate0.5=0.01]",
        "F[not_focus:0.80 focus:0.20] Y[yaw_left:0.30 yaw_right:0.70] yaw=3422.789 B[rate0.5=0.03]",
        "F[not_focus:0.78 focus:0.22] Y[yaw_left:0.32 yaw_right:0.68] yaw=3419.012 B[rate0.5=0.02]",
        "F[not_focus:0.75 focus:0.25] Y[yaw_left:0.29 yaw_right:0.71] yaw=3421.345 B[rate0.5=0.01]",
        "F[not_focus:0.73 focus:0.27] Y[yaw_left:0.31 yaw_right:0.69] yaw=3417.678 B[rate0.5=0.04]",
        "F[not_focus:0.70 focus:0.30] Y[yaw_left:0.28 yaw_right:0.72] yaw=3423.901 B[rate0.5=0.02]",
        "F[not_focus:0.68 focus:0.32] Y[yaw_left:0.30 yaw_right:0.70] yaw=3420.234 B[rate0.5=0.03]",
        "F[not_focus:0.65 focus:0.35] Y[yaw_left:0.29 yaw_right:0.71] yaw=3418.567 B[rate0.5=0.01]",
    ]
    
    print("\nAdding test samples...")
    for i, sample in enumerate(test_samples):
        success = adapter.add_reading(sample)
        print(f"Sample {i+1}: {'✅' if success else '❌'}")
        time.sleep(0.1)
    
    print(f"\n{'-'*60}")
    print("Computing cognitive state...")
    state = adapter.get_cognitive_state()
    
    print(f"\n📊 Cognitive State:")
    print(f"  Focus:    {state['focus']:.3f}")
    print(f"  Fatigue:  {state['fatigue']:.3f}")
    print(f"  Overload: {state['overload']:.3f}")
    print(f"  Stress:   {state['stress']:.3f}")
    print(f"\n  Status: {state.get('status', 'ok')}")
    print(f"  Calibrated: {state['calibrated']}")
    print(f"  Buffer: {state['buffer_size']} readings")

