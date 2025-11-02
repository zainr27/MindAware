"""
EEG simulator for generating synthetic cognitive state data.
Simplified scenarios for all-or-nothing logic.
"""

import random
import time
from typing import Dict, Any
from datetime import datetime, timezone


class EEGSimulator:
    """Simulates EEG-derived cognitive states for all-or-nothing testing."""
    
    def __init__(self, scenario: str = "normal"):
        """
        Initialize simulator with a scenario.
        
        Args:
            scenario: One of ['normal', 'critical', 'mixed', 'degrading']
        """
        self.scenario = scenario
        self.time_elapsed = 0
    
    def get_cognitive_state(self) -> Dict[str, Any]:
        """
        Generate a synthetic cognitive state based on scenario.
        
        Scenarios optimized for all-or-nothing thresholds:
        - normal: ALL GOOD (focus ≥0.6, negatives ≤0.4)
        - critical: ALL BAD (focus ≤0.4, negatives ≥0.6)
        - mixed: Some good, some bad (no action)
        - degrading: Transitions from all good to all bad
        
        Returns:
            Dict with focus, fatigue, overload, stress (0-1 scale)
        """
        self.time_elapsed += 1
        
        # Small random noise
        noise = lambda: random.uniform(-0.03, 0.03)
        
        if self.scenario == "normal":
            # ALL GOOD: Triggers takeoff to 1m consistently
            focus = max(0.6, min(1.0, 0.7 + noise()))
            fatigue = max(0.0, min(0.4, 0.2 + noise()))
            overload = max(0.0, min(0.4, 0.25 + noise()))
            stress = max(0.0, min(0.4, 0.25 + noise()))
        
        elif self.scenario == "critical":
            # ALL BAD: Triggers land to ground immediately
            focus = max(0.0, min(0.4, 0.3 + noise()))
            fatigue = max(0.6, min(1.0, 0.7 + noise()))
            overload = max(0.6, min(1.0, 0.7 + noise()))
            stress = max(0.6, min(1.0, 0.75 + noise()))
        
        elif self.scenario == "mixed":
            # MIXED: Some good, some bad (no action - maintains altitude)
            focus = 0.5 + noise()  # Between thresholds
            fatigue = 0.5 + noise()  # Between thresholds
            overload = 0.7 + noise()  # High
            stress = 0.3 + noise()  # Low
        
        elif self.scenario == "degrading":
            # Starts ALL GOOD, gradually becomes ALL BAD
            progress = min(1.0, self.time_elapsed / 15.0)  # 15 iterations to full degradation
            
            focus = max(0.0, min(1.0, 0.7 - 0.5 * progress + noise()))
            fatigue = max(0.0, min(1.0, 0.2 + 0.6 * progress + noise()))
            overload = max(0.0, min(1.0, 0.25 + 0.6 * progress + noise()))
            stress = max(0.0, min(1.0, 0.25 + 0.6 * progress + noise()))
        
        else:
            # Default to normal (all good)
            focus = 0.7 + noise()
            fatigue = 0.2 + noise()
            overload = 0.25 + noise()
            stress = 0.25 + noise()
        
        return {
            "focus": round(focus, 3),
            "fatigue": round(fatigue, 3),
            "overload": round(overload, 3),
            "stress": round(stress, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario": self.scenario,
            "iteration": self.time_elapsed
        }
    
    def reset(self) -> None:
        """Reset the simulator state."""
        self.time_elapsed = 0
    
    def set_scenario(self, scenario: str) -> None:
        """Change the simulation scenario."""
        self.scenario = scenario
        self.time_elapsed = 0


def simulate_eeg_stream(duration: int = 10, interval: float = 2.0, scenario: str = "normal"):
    """
    Simulate a stream of EEG data for testing.
    
    Args:
        duration: How many samples to generate
        interval: Seconds between samples
        scenario: Simulation scenario
    
    Yields:
        Cognitive state dictionaries
    """
    simulator = EEGSimulator(scenario=scenario)
    
    for _ in range(duration):
        state = simulator.get_cognitive_state()
        yield state
        time.sleep(interval)


if __name__ == "__main__":
    print("EEG Simulator Test - All-or-Nothing Scenarios")
    print("=" * 60)
    
    scenarios = ["normal", "critical", "mixed", "degrading"]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"SCENARIO: {scenario.upper()}")
        print(f"{'='*60}")
        
        simulator = EEGSimulator(scenario=scenario)
        
        for i in range(3):
            state = simulator.get_cognitive_state()
            print(f"\nIteration {i+1}:")
            print(f"  Focus:    {state['focus']:.3f} {'✅' if state['focus'] >= 0.6 else '❌' if state['focus'] <= 0.4 else '⚠️'}")
            print(f"  Fatigue:  {state['fatigue']:.3f} {'✅' if state['fatigue'] <= 0.4 else '❌' if state['fatigue'] >= 0.6 else '⚠️'}")
            print(f"  Overload: {state['overload']:.3f} {'✅' if state['overload'] <= 0.4 else '❌' if state['overload'] >= 0.6 else '⚠️'}")
            print(f"  Stress:   {state['stress']:.3f} {'✅' if state['stress'] <= 0.4 else '❌' if state['stress'] >= 0.6 else '⚠️'}")
            
            # Determine state
            all_good = (state['focus'] >= 0.6 and state['fatigue'] <= 0.4 and 
                       state['overload'] <= 0.4 and state['stress'] <= 0.4)
            all_bad = (state['focus'] <= 0.4 and state['fatigue'] >= 0.6 and 
                      state['overload'] >= 0.6 and state['stress'] >= 0.6)
            
            if all_good:
                print("  → ALL GOOD: takeoff() to 1m")
            elif all_bad:
                print("  → ALL BAD: land() to ground")
            else:
                print("  → MIXED: turn_around() 180°")
            
            time.sleep(0.3)
