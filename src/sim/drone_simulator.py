"""
Simplified drone simulator for altitude-based cognitive state visualization.
"""

import random
import time
from typing import Dict, Any
from datetime import datetime, timezone


class DroneSimulator:
    """
    Simulates drone telemetry with altitude and rotation tracking.
    Altitude reflects operator cognitive wellness.
    """
    
    def __init__(self):
        # Core position tracking
        self.altitude_m = 0.0  # meters above ground
        self.rotation_deg = 0.0  # degrees (0-360)
        
        # Mission context
        self.battery = 100.0
        self.mission_progress = 0.0
        self.time_elapsed = 0
        
        # Fixed location (hackathon simplification)
        self.position = {"lat": 37.7749, "lon": -122.4194}
    
    def get_telemetry(self) -> Dict[str, Any]:
        """
        Generate drone telemetry focused on altitude and rotation.
        
        Returns:
            Dict with altitude, rotation, battery, status
        """
        self.time_elapsed += 1
        
        # Decrease battery
        self.battery = max(0, self.battery - random.uniform(0.05, 0.15))
        
        # Update mission progress
        self.mission_progress = min(100, self.mission_progress + random.uniform(0.2, 0.8))
        
        # Add small noise to measurements
        noise = lambda: random.uniform(-0.05, 0.05)
        
        return {
            "altitude_m": round(self.altitude_m + noise(), 2),
            "rotation_deg": round(self.rotation_deg, 1),
            "position": {
                "latitude": round(self.position["lat"], 6),
                "longitude": round(self.position["lon"], 6),
                "altitude": round(self.altitude_m, 2)  # For compatibility
            },
            "battery": round(self.battery, 1),
            "mission_progress": round(self.mission_progress, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active" if self.battery > 10 else "low_battery"
        }
    
    def update_altitude(self, new_altitude: float) -> None:
        """Update drone altitude (called by tools)."""
        MAX_ALTITUDE = 1.0  # Hard cap at 1.0 meter (takeoff altitude)
        self.altitude_m = max(0.0, min(MAX_ALTITUDE, new_altitude))  # Keep between 0 and 1.0m
    
    def update_rotation(self, new_rotation: float) -> None:
        """Update drone rotation (called by tools)."""
        self.rotation_deg = new_rotation % 360  # Keep in 0-360 range
    
    def get_altitude(self) -> float:
        """Get current altitude."""
        return self.altitude_m
    
    def get_rotation(self) -> float:
        """Get current rotation."""
        return self.rotation_deg
    
    def reset(self) -> None:
        """Reset simulator state."""
        self.altitude_m = 0.0
        self.rotation_deg = 0.0
        self.battery = 100.0
        self.mission_progress = 0.0
        self.time_elapsed = 0


def simulate_drone_stream(duration: int = 10, interval: float = 1.0):
    """
    Simulate a stream of drone telemetry for testing.
    
    Args:
        duration: How many samples to generate
        interval: Seconds between samples
    
    Yields:
        Telemetry dictionaries
    """
    simulator = DroneSimulator()
    
    for _ in range(duration):
        telemetry = simulator.get_telemetry()
        yield telemetry
        time.sleep(interval)


if __name__ == "__main__":
    print("Drone Simulator Test (Altitude Control)")
    print("=" * 50)
    
    simulator = DroneSimulator()
    
    # Simulate altitude changes
    test_scenario = [
        (0, "Start at ground"),
        (0.5, "Operator improving"),
        (1.2, "Operator performing well"),
        (1.5, "Peak performance"),
        (1.0, "Slight decline"),
        (0.3, "Significant fatigue"),
        (0.0, "Return to ground")
    ]
    
    for altitude, description in test_scenario:
        simulator.update_altitude(altitude)
        telemetry = simulator.get_telemetry()
        print(f"\n{description}:")
        print(f"  Altitude:  {telemetry['altitude_m']}m")
        print(f"  Rotation:  {telemetry['rotation_deg']}°")
        print(f"  Battery:   {telemetry['battery']}%")
        time.sleep(0.5)
