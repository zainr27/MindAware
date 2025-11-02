"""
Tool functions that the LLM agent can call to control the drone system.
Binary control: TAKEOFF to 1m or LAND to ground. TURN_AROUND for mixed states.
"""

import json
from typing import Dict, Any


class DroneTools:
    """Binary drone control: takeoff (1m), land (0m), or turn_around (180°)."""
    
    TAKEOFF_ALTITUDE = 1.0  # Takeoff altitude in meters
    
    def __init__(self):
        self.current_altitude = 0.0  # meters
        self.current_rotation = 0.0  # degrees (0-360)
        self.action_history = []
    
    def takeoff(self) -> Dict[str, Any]:
        """
        Takeoff to 1 meter altitude (operator is performing well).
        Used when ALL parameters are good.
        
        Returns:
            Result dictionary
        """
        old_altitude = self.current_altitude
        self.current_altitude = self.TAKEOFF_ALTITUDE
        
        result = {
            "success": True,
            "action": "takeoff",
            "previous_altitude_m": round(old_altitude, 2),
            "new_altitude_m": round(self.current_altitude, 2),
            "message": f"Drone takeoff to {self.TAKEOFF_ALTITUDE}m (from {old_altitude:.2f}m)"
        }
        
        self.action_history.append(result)
        print(f"[TOOL] takeoff: {old_altitude:.2f}m → {self.current_altitude:.2f}m")
        
        return result
    
    def land(self) -> Dict[str, Any]:
        """
        Land drone immediately (return to ground level).
        Used when ALL parameters are bad.
        
        Returns:
            Result dictionary
        """
        old_altitude = self.current_altitude
        self.current_altitude = 0.0
        
        result = {
            "success": True,
            "action": "land",
            "previous_altitude_m": round(old_altitude, 2),
            "new_altitude_m": 0.0,
            "message": f"Drone landed (from {old_altitude:.2f}m to ground level)"
        }
        
        self.action_history.append(result)
        print(f"[TOOL] land: {old_altitude:.2f}m → 0.00m (GROUND)")
        
        return result
    
    def turn_around(self) -> Dict[str, Any]:
        """
        Rotate drone 180 degrees (visual indicator).
        Used for mixed states or when nothing needs to change.
        
        Returns:
            Result dictionary
        """
        old_rotation = self.current_rotation
        self.current_rotation = (self.current_rotation + 180) % 360
        
        result = {
            "success": True,
            "action": "turn_around",
            "previous_rotation_deg": round(old_rotation, 1),
            "new_rotation_deg": round(self.current_rotation, 1),
            "message": f"Drone rotated 180° (from {old_rotation:.1f}° to {self.current_rotation:.1f}°)"
        }
        
        self.action_history.append(result)
        print(f"[TOOL] turn_around: {old_rotation:.1f}° → {self.current_rotation:.1f}°")
        
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
        
        elif tool_name == "turn_around":
            return self.turn_around()
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available tools: takeoff, land, turn_around"
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
                    "description": "Takeoff to 1 meter altitude. Use ONLY when ALL operator parameters are good (focus ≥0.6, fatigue/overload/stress ≤0.4). This is a binary action - drone goes straight to 1m.",
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
                    "description": "Land the drone immediately (return to ground level). Use ONLY when ALL operator parameters are bad (focus ≤0.4, fatigue/overload/stress ≥0.6). This is an emergency response.",
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
                    "name": "turn_around",
                    "description": "Rotate drone 180 degrees as a visual indicator. Use when parameters are mixed (some good, some bad) or when state hasn't changed significantly. This maintains current altitude.",
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
            "rotation_deg": round(self.current_rotation, 1),
            "total_actions": len(self.action_history)
        }
    
    def reset(self) -> None:
        """Reset drone to initial state."""
        self.current_altitude = 0.0
        self.current_rotation = 0.0
        self.action_history = []
        print("[TOOL] Drone reset to ground level")
