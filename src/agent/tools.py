"""
Tool functions that the LLM agent can call to control the drone system.
Binary control: TAKEOFF to 1m or LAND to ground. YAW RIGHT for mixed states.

Partner's drone step names: ["TAKEOFF", "YAW RIGHT", "YAW CENTER", "LAND", "FLAND"]
"""

import json
from typing import Dict, Any


class DroneTools:
    """Binary drone control: TAKEOFF (1m), LAND (0m), or YAW RIGHT (rotate)."""
    
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
    
    def yaw_right(self) -> Dict[str, Any]:
        """
        Rotate drone to the right (yaw right command).
        Used for mixed states or when nothing needs to change.
        Partner's drone executes: "YAW RIGHT" step
        
        Returns:
            Result dictionary
        """
        old_rotation = self.current_rotation
        # Yaw right by 90 degrees
        self.current_rotation = (self.current_rotation + 90) % 360
        
        result = {
            "success": True,
            "action": "yaw_right",
            "partner_command": "YAW RIGHT",
            "previous_rotation_deg": round(old_rotation, 1),
            "new_rotation_deg": round(self.current_rotation, 1),
            "message": f"Drone yawed right 90° (from {old_rotation:.1f}° to {self.current_rotation:.1f}°)"
        }
        
        self.action_history.append(result)
        print(f"[TOOL] yaw_right: {old_rotation:.1f}° → {self.current_rotation:.1f}°")
        
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
        
        elif tool_name == "yaw_right":
            return self.yaw_right()
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available tools: takeoff, land, yaw_right"
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
            },
            {
                "type": "function",
                "function": {
                    "name": "yaw_right",
                    "description": "Execute YAW RIGHT command - drone rotates 90° to the right. Use when parameters are MIXED (some good, some bad) or when no altitude change is needed. Visual indicator only, maintains current altitude. Maps to partner's 'YAW RIGHT' step.",
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
