"""
Binary policy for hackathon: FOCUS-ONLY control → binary drone altitude.
Only FOCUS determines takeoff/land. Other metrics monitored but don't affect decisions.
YAW is controlled passively by the EEG (head turning), not by commands.
Partner's drone step names: ["TAKEOFF", "LAND", "FLAND"]
"""

from typing import Dict, Any, List


class CognitivePolicy:
    """
    Binary policy: FOCUS is the ONLY determinant for altitude control.
    
    HIGH FOCUS (≥0.6) → TAKEOFF to 1m
    LOW FOCUS (≤0.4) → LAND (go to ground)
    MID FOCUS (0.4 < focus < 0.6) → MAINTAIN ALTITUDE (no action)
    
    Other metrics (fatigue, overload, stress) are tracked for display but don't affect decisions.
    YAW is controlled passively by EEG (head position), not by commands.
    """
    
    def __init__(self):
        # Thresholds for "high" and "low"
        self.FOCUS_HIGH = 0.6
        self.FOCUS_LOW = 0.4
        self.NEGATIVE_HIGH = 0.6  # fatigue/overload/stress above this = bad
        self.NEGATIVE_LOW = 0.4   # fatigue/overload/stress below this = good
    
    def evaluate(self, cognitive_state: Dict[str, float], current_altitude: float = 0.0) -> Dict[str, Any]:
        """
        Evaluate cognitive state using FOCUS as the sole determinant.
        Other metrics (fatigue, overload, stress) are tracked but don't affect decisions.
        
        Args:
            cognitive_state: Current cognitive metrics
            current_altitude: Current drone altitude (for grounded check)
        
        Returns:
            Policy evaluation with recommendations
        """
        focus = cognitive_state.get('focus', 0.5)
        fatigue = cognitive_state.get('fatigue', 0.5)
        overload = cognitive_state.get('overload', 0.5)
        stress = cognitive_state.get('stress', 0.5)
        
        recommendations = []
        severity = "normal"
        reasoning = []
        
        # FOCUS is the ONLY determinant for altitude control
        # High focus (≥0.6) → takeoff
        # Low focus (≤0.4) → land
        # Mid-range → no action
        
        all_good = focus >= self.FOCUS_HIGH
        all_bad = focus <= self.FOCUS_LOW
        
        if all_good:
            # High focus → TAKEOFF to 1m (automatic, just inform pilot)
            severity = "good"
            recommendations.append({
                "action": "takeoff",
                "reason": "High focus detected - operator performing excellently",
                "parameters": {},
                "urgent": True  # Automatic takeoff - no confirmation needed, just inform
            })
            reasoning.append(f"✅ Focus: {focus:.2f} (≥{self.FOCUS_HIGH}) - PRIMARY DETERMINANT")
            reasoning.append(f"📊 Fatigue: {fatigue:.2f} (monitoring only)")
            reasoning.append(f"📊 Overload: {overload:.2f} (monitoring only)")
            reasoning.append(f"📊 Stress: {stress:.2f} (monitoring only)")
            reasoning.append("High focus → TAKEOFF to 1m")
        
        elif all_bad:
            # Low focus → different response if grounded vs airborne
            severity = "critical"
            
            if current_altitude <= 0.1:  # Already grounded
                # Don't recommend any action, just inform that they need to regain focus
                recommendations = []  # No action needed
                reasoning.append(f"❌ Focus: {focus:.2f} (≤{self.FOCUS_LOW}) - PRIMARY DETERMINANT")
                reasoning.append(f"📊 Fatigue: {fatigue:.2f} (monitoring only)")
                reasoning.append(f"📊 Overload: {overload:.2f} (monitoring only)")
                reasoning.append(f"📊 Stress: {stress:.2f} (monitoring only)")
                reasoning.append("🔴 Drone is GROUNDED - Regain focus to fly again")
                severity = "grounded"  # Special status
            else:
                # In air → LAND immediately (low focus)
                recommendations.append({
                    "action": "land",
                    "reason": "Low focus detected - operator needs to regain concentration",
                    "parameters": {},
                    "urgent": False  # Always ask for permission before landing
                })
                reasoning.append(f"❌ Focus: {focus:.2f} (≤{self.FOCUS_LOW}) - PRIMARY DETERMINANT")
                reasoning.append(f"📊 Fatigue: {fatigue:.2f} (monitoring only)")
                reasoning.append(f"📊 Overload: {overload:.2f} (monitoring only)")
                reasoning.append(f"📊 Stress: {stress:.2f} (monitoring only)")
                reasoning.append("Low focus → LAND immediately")
        
        else:
            # Mid-range focus (0.4 < focus < 0.6) → maintain altitude (no action)
            severity = "normal"
            recommendations = []  # No action for mid-range focus
            
            if current_altitude > 0.1:
                reasoning.append("✈️ Drone is in the air")
            else:
                reasoning.append("⏸️ Drone on ground - waiting for high focus")
            
            reasoning.append(f"⚖️ Focus: {focus:.2f} (mid-range: {self.FOCUS_LOW} < focus < {self.FOCUS_HIGH})")
            reasoning.append(f"📊 Fatigue: {fatigue:.2f}, Overload: {overload:.2f}, Stress: {stress:.2f} (monitoring only)")
        
        return {
            "severity": severity,
            "all_good": all_good,
            "all_bad": all_bad,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "metrics": {
                "focus": focus,
                "fatigue": fatigue,
                "overload": overload,
                "stress": stress
            }
        }
    
    def reset(self) -> None:
        """Reset policy state."""
        pass  # No state to reset in this simplified version
