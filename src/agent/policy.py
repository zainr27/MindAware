"""
Binary policy for hackathon: All parameters check → binary drone control.
Partner's drone step names: ["TAKEOFF", "YAW RIGHT", "YAW CENTER", "LAND", "FLAND"]
"""

from typing import Dict, Any, List


class CognitivePolicy:
    """
    Binary policy: Check if ALL parameters are good or bad.
    
    ALL GOOD (focus HIGH + fatigue/overload/stress LOW) → TAKEOFF to 1m
    ALL BAD (focus LOW + fatigue/overload/stress HIGH) → LAND (go to ground)
    Otherwise → YAW RIGHT (mixed state indicator, rotate right)
    """
    
    def __init__(self):
        # Thresholds for "high" and "low"
        self.FOCUS_HIGH = 0.6
        self.FOCUS_LOW = 0.4
        self.NEGATIVE_HIGH = 0.6  # fatigue/overload/stress above this = bad
        self.NEGATIVE_LOW = 0.4   # fatigue/overload/stress below this = good
    
    def evaluate(self, cognitive_state: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate cognitive state with simple all-or-nothing logic.
        
        Args:
            cognitive_state: Current cognitive metrics
        
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
        
        # Check if ALL GOOD (focus high, negatives low)
        all_good = (
            focus >= self.FOCUS_HIGH and
            fatigue <= self.NEGATIVE_LOW and
            overload <= self.NEGATIVE_LOW and
            stress <= self.NEGATIVE_LOW
        )
        
        # Check if ALL BAD (focus low, negatives high)
        all_bad = (
            focus <= self.FOCUS_LOW and
            fatigue >= self.NEGATIVE_HIGH and
            overload >= self.NEGATIVE_HIGH and
            stress >= self.NEGATIVE_HIGH
        )
        
        if all_good:
            # All parameters good → TAKEOFF to 1m (automatic, just inform pilot)
            severity = "good"
            recommendations.append({
                "action": "takeoff",
                "reason": "All parameters optimal - operator performing excellently",
                "parameters": {},
                "urgent": True  # Automatic takeoff - no confirmation needed, just inform
            })
            reasoning.append(f"✅ Focus: {focus:.2f} (≥{self.FOCUS_HIGH})")
            reasoning.append(f"✅ Fatigue: {fatigue:.2f} (≤{self.NEGATIVE_LOW})")
            reasoning.append(f"✅ Overload: {overload:.2f} (≤{self.NEGATIVE_LOW})")
            reasoning.append(f"✅ Stress: {stress:.2f} (≤{self.NEGATIVE_LOW})")
            reasoning.append("All parameters good → TAKEOFF to 1m")
        
        elif all_bad:
            # All parameters bad → LAND (go to ground) - ASK FOR CONFIRMATION
            severity = "critical"
            recommendations.append({
                "action": "land",
                "reason": "All parameters critical - operator needs immediate support",
                "parameters": {},
                "urgent": False  # Always ask for permission before landing
            })
            reasoning.append(f"❌ Focus: {focus:.2f} (≤{self.FOCUS_LOW})")
            reasoning.append(f"❌ Fatigue: {fatigue:.2f} (≥{self.NEGATIVE_HIGH})")
            reasoning.append(f"❌ Overload: {overload:.2f} (≥{self.NEGATIVE_HIGH})")
            reasoning.append(f"❌ Stress: {stress:.2f} (≥{self.NEGATIVE_HIGH})")
            reasoning.append("All parameters bad → LAND immediately")
        
        else:
            # Mixed state → yaw right as visual indicator (non-urgent)
            severity = "normal"
            recommendations.append({
                "action": "yaw_right",
                "reason": "Mixed parameters - visual indicator without altitude change",
                "parameters": {},
                "urgent": False  # Non-urgent: can ask for confirmation
            })
            reasoning.append("🔄 Mixed parameters - executing YAW RIGHT (rotate 90°)")
            reasoning.append(f"Focus: {focus:.2f}, Fatigue: {fatigue:.2f}, Overload: {overload:.2f}, Stress: {stress:.2f}")
        
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
