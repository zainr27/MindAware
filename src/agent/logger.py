"""
Decision logging system for audit trail.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class DecisionLogger:
    """Logs all agent decisions to JSONL format."""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "decisions.jsonl"
    
    def log_decision(self, decision: Dict[str, Any]) -> None:
        """
        Log a decision to the JSONL file.
        
        Args:
            decision: Decision dictionary with cognitive state, actions, reasoning
        """
        # Add timestamp if not present
        if "timestamp" not in decision or decision["timestamp"] is None:
            decision["timestamp"] = datetime.utcnow().isoformat()
        
        # Write to JSONL
        with open(self.log_file, "a") as f:
            f.write(json.dumps(decision) + "\n")
        
        print(f"[LOGGER] Decision logged at {decision['timestamp']}")
    
    def get_recent_decisions(self, count: int = 10) -> list:
        """
        Retrieve recent decisions from log.
        
        Args:
            count: Number of recent decisions to retrieve
        
        Returns:
            List of decision dictionaries
        """
        if not self.log_file.exists():
            return []
        
        decisions = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))
        
        return decisions[-count:]
    
    def get_all_decisions(self) -> list:
        """Get all decisions from log."""
        if not self.log_file.exists():
            return []
        
        decisions = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))
        
        return decisions
    
    def clear_log(self) -> None:
        """Clear the decision log."""
        if self.log_file.exists():
            self.log_file.unlink()
        print("[LOGGER] Decision log cleared")

