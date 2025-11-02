"""
Test suite for EEG simulator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sim import EEGSimulator


def test_eeg_simulator_normal():
    """Test EEG simulator in normal scenario."""
    print("\n[TEST] EEG Simulator - Normal scenario")
    
    sim = EEGSimulator(scenario="normal")
    
    for i in range(5):
        state = sim.get_cognitive_state()
        
        # Validate structure
        assert "focus" in state, "Should have focus"
        assert "fatigue" in state, "Should have fatigue"
        assert "overload" in state, "Should have overload"
        assert "stress" in state, "Should have stress"
        assert "timestamp" in state, "Should have timestamp"
        assert "scenario" in state, "Should have scenario"
        
        # Validate normal scenario characteristics
        assert state["focus"] >= 0.6, f"Focus should be high in normal scenario, got {state['focus']}"
        assert state["fatigue"] <= 0.4, f"Fatigue should be low in normal scenario, got {state['fatigue']}"
        assert state["overload"] <= 0.4, f"Overload should be low in normal scenario, got {state['overload']}"
        assert state["stress"] <= 0.4, f"Stress should be low in normal scenario, got {state['stress']}"
    
    print("✅ EEG Simulator - Normal PASSED")


def test_eeg_simulator_critical():
    """Test EEG simulator in critical scenario."""
    print("\n[TEST] EEG Simulator - Critical scenario")
    
    sim = EEGSimulator(scenario="critical")
    
    for i in range(5):
        state = sim.get_cognitive_state()
        
        # Validate critical scenario characteristics
        assert state["focus"] <= 0.4, f"Focus should be low in critical scenario, got {state['focus']}"
        assert state["fatigue"] >= 0.6, f"Fatigue should be high in critical scenario, got {state['fatigue']}"
        assert state["overload"] >= 0.6, f"Overload should be high in critical scenario, got {state['overload']}"
        assert state["stress"] >= 0.6, f"Stress should be high in critical scenario, got {state['stress']}"
    
    print("✅ EEG Simulator - Critical PASSED")


def test_eeg_simulator_mixed():
    """Test EEG simulator in mixed scenario."""
    print("\n[TEST] EEG Simulator - Mixed scenario")
    
    sim = EEGSimulator(scenario="mixed")
    
    state = sim.get_cognitive_state()
    
    # Mixed should have values between thresholds
    assert 0.4 < state["focus"] < 0.6, f"Focus should be mixed, got {state['focus']}"
    assert 0.4 < state["fatigue"] < 0.6, f"Fatigue should be mixed, got {state['fatigue']}"
    
    print("✅ EEG Simulator - Mixed PASSED")


def test_eeg_simulator_degrading():
    """Test EEG simulator degrading over time."""
    print("\n[TEST] EEG Simulator - Degrading scenario")
    
    sim = EEGSimulator(scenario="degrading")
    
    first_state = sim.get_cognitive_state()
    
    # Simulate many iterations
    for _ in range(15):
        sim.get_cognitive_state()
    
    last_state = sim.get_cognitive_state()
    
    # Focus should decrease
    assert last_state["focus"] < first_state["focus"], "Focus should degrade over time"
    # Fatigue should increase
    assert last_state["fatigue"] > first_state["fatigue"], "Fatigue should increase over time"
    
    print("✅ EEG Simulator - Degrading PASSED")


def run_all_tests():
    """Run all simulator tests."""
    print("\n" + "="*60)
    print("TESTING: EEG Simulator")
    print("="*60 + "\n")
    
    try:
        test_eeg_simulator_normal()
        test_eeg_simulator_critical()
        test_eeg_simulator_mixed()
        test_eeg_simulator_degrading()
        
        print("\n" + "="*60)
        print("✅ ALL SIMULATOR TESTS PASSED!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

