"""
Tool functions that the LLM agent can call to control the drone system.
Binary control: TAKEOFF to 1m or LAND to ground.

YAW is controlled passively by the EEG (head turning), not by commands.
Partner's drone step names: ["TAKEOFF", "LAND", "FLAND"]
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, Optional


class DroneTools:
    """Binary drone control: TAKEOFF (1m) or LAND (0m). Yaw controlled by EEG."""
    
    TAKEOFF_ALTITUDE = 1.0  # Takeoff altitude in meters
    
    # Drone control authentication (from initial_demo_program.py)
    AUTH_USERNAME = "BCITeam"
    AUTH_PASSWORD = "DronesRCool"
    
    def __init__(self, drone_base_url: Optional[str] = None):
        """
        Initialize DroneTools.
        
        Args:
            drone_base_url: Base URL for drone control API (e.g., "http://192.168.86.139:8080")
                           If None, tries to get from DRONE_BASE_URL environment variable,
                           or defaults to "http://192.168.86.139:8080"
        """
        self.current_altitude = 0.0  # meters
        self.current_yaw = 0.0  # degrees (controlled by EEG, not commands)
        self.action_history = []
        
        # Get drone base URL from parameter, env var, or default
        if drone_base_url:
            self.drone_base_url = drone_base_url
        else:
            self.drone_base_url = os.getenv("DRONE_BASE_URL", "http://192.168.86.139:8080")
        
        # Ensure URL doesn't end with /
        if self.drone_base_url.endswith("/"):
            self.drone_base_url = self.drone_base_url[:-1]
        
        print(f"[TOOL] DroneTools initialized with URL: {self.drone_base_url}")
    
    def _send_drone_command(self, endpoint: str) -> bool:
        """
        Send a command to the actual drone hardware.
        
        Args:
            endpoint: API endpoint (e.g., "/takeoff", "/land", "/fland")
        
        Returns:
            True if command was successfully sent, False otherwise
        """
        url = f"{self.drone_base_url}{endpoint}"
        auth = HTTPBasicAuth(self.AUTH_USERNAME, self.AUTH_PASSWORD)
        
        try:
            print(f"\n🚁 [DRONE] Sending command to: {url}")
            response = requests.get(url, auth=auth, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ [DRONE] Command successful: {response.status_code} - {response.text}")
                return True
            else:
                print(f"⚠️  [DRONE] Command returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ [DRONE] Connection error: {e}")
            print(f"   Make sure drone is running and accessible at {self.drone_base_url}")
            return False
    
    def takeoff(self) -> Dict[str, Any]:
        """
        Takeoff to 1 meter altitude (operator is performing well).
        Used when ALL parameters are good.
        
        This method sends an actual command to the drone hardware via HTTP.
        
        Returns:
            Result dictionary
        """
        old_altitude = self.current_altitude
        
        # Send actual command to drone
        command_success = self._send_drone_command("/takeoff")
        
        # Update internal state if command succeeded
        if command_success:
            self.current_altitude = self.TAKEOFF_ALTITUDE
        else:
            # Even if command failed, log the attempt
            # The drone may not be connected, but we still track the intended action
            print(f"[TOOL] ⚠️  Takeoff command sent but may not have reached drone")
        
        result = {
            "success": command_success,
            "action": "takeoff",
            "previous_altitude_m": round(old_altitude, 2),
            "new_altitude_m": round(self.current_altitude, 2),
            "message": f"Drone takeoff to {self.TAKEOFF_ALTITUDE}m (from {old_altitude:.2f}m)" if command_success else f"Takeoff command sent (drone may not be connected)",
            "drone_command_sent": command_success
        }
        
        self.action_history.append(result)
        print(f"[TOOL] takeoff: {old_altitude:.2f}m → {self.current_altitude:.2f}m (drone: {'✅' if command_success else '⚠️'})")
        
        return result
    
    def land(self) -> Dict[str, Any]:
        """
        Land drone immediately (return to ground level).
        Used when ALL parameters are bad.
        
        This method sends an actual command to the drone hardware via HTTP.
        
        Returns:
            Result dictionary
        """
        old_altitude = self.current_altitude
        
        # Send actual command to drone
        command_success = self._send_drone_command("/land")
        
        # Update internal state if command succeeded
        if command_success:
            self.current_altitude = 0.0
        else:
            # Even if command failed, log the attempt
            print(f"[TOOL] ⚠️  Land command sent but may not have reached drone")
        
        result = {
            "success": command_success,
            "action": "land",
            "previous_altitude_m": round(old_altitude, 2),
            "new_altitude_m": 0.0,
            "message": f"Drone landed (from {old_altitude:.2f}m to ground level)" if command_success else f"Land command sent (drone may not be connected)",
            "drone_command_sent": command_success
        }
        
        self.action_history.append(result)
        print(f"[TOOL] land: {old_altitude:.2f}m → 0.00m (GROUND) (drone: {'✅' if command_success else '⚠️'})")
        
        return result
    
    def maintain_altitude(self) -> Dict[str, Any]:
        """
        Maintain current altitude (no action needed).
        Used for mixed states when operator is neither all good nor all bad.
        Yaw is controlled passively by EEG head position.
        
        Returns:
            Result dictionary
        """
        result = {
            "success": True,
            "action": "maintain_altitude",
            "current_altitude_m": round(self.current_altitude, 2),
            "message": f"Maintaining altitude at {self.current_altitude:.2f}m (mixed parameters)"
        }
        
        self.action_history.append(result)
        print(f"[TOOL] maintain_altitude: {self.current_altitude:.2f}m (no change)")
        
        return result
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
        
        Returns:
            Result from tool execution
        """
        if tool_name == "takeoff":
            return self.takeoff()
        
        elif tool_name == "land":
            return self.land()
        
        elif tool_name == "maintain_altitude":
            return self.maintain_altitude()
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available tools: takeoff, land, maintain_altitude"
            }
    
    def get_tool_definitions(self) -> list:
        """
        Get OpenAI function calling tool definitions.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "takeoff",
                    "description": "Execute TAKEOFF command - drone rises to 1 meter altitude. Use ONLY when ALL operator parameters are good (focus ≥0.6, fatigue/overload/stress ≤0.4). Binary action - goes straight to 1m. Maps to partner's 'TAKEOFF' step.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "land",
                    "description": "Execute LAND command - drone lands immediately (returns to ground). Use ONLY when ALL operator parameters are bad (focus ≤0.4, fatigue/overload/stress ≥0.6). Emergency safety response. Maps to partner's 'LAND' step.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current drone state."""
        return {
            "altitude_m": round(self.current_altitude, 2),
            "yaw_deg": round(self.current_yaw, 1),  # Read from EEG, not set by commands
            "total_actions": len(self.action_history)
        }
    
    def reset(self) -> None:
        """Reset drone to initial state."""
        self.current_altitude = 0.0
        self.current_yaw = 0.0
        self.action_history = []
        print("[TOOL] Drone reset to ground level")
    
    def update_yaw_from_eeg(self, yaw_value: float) -> None:
        """Update yaw value from EEG data (passive control)."""
        self.current_yaw = yaw_value % 360
