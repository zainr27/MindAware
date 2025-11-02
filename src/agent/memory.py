"""
Short-term memory system for agent context.
Simplified for all-or-nothing decision logic.
"""

from typing import Dict, Any, List
from collections import deque
from datetime import datetime, timezone


class AgentMemory:
    """Maintains short-term memory of cognitive states and decisions."""
    
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.cognitive_history = deque(maxlen=max_history)
        self.decision_history = deque(maxlen=max_history)
    
    def add_cognitive_state(self, state: Dict[str, Any]) -> None:
        """Add a cognitive state to history."""
        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.cognitive_history.append(state)
    
    def add_decision(self, decision: Dict[str, Any]) -> None:
        """Add a decision to history."""
        decision["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.decision_history.append(decision)
    
    def get_recent_cognitive_states(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent cognitive states."""
        return list(self.cognitive_history)[-count:]
    
    def get_recent_decisions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent decisions."""
        return list(self.decision_history)[-count:]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of current context for the agent.
        Simplified for all-or-nothing logic.
        """
        recent_states = self.get_recent_cognitive_states(3)
        recent_decisions = self.get_recent_decisions(3)
        
        return {
            "recent_states": recent_states,
            "recent_decisions": recent_decisions,
            "state_count": len(self.cognitive_history),
            "decision_count": len(self.decision_history)
        }
    
    def clear(self) -> None:
        """Clear all memory."""
        self.cognitive_history.clear()
        self.decision_history.clear()
