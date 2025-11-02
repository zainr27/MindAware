"""
Test suite for CognitivePolicy - Binary all-or-nothing logic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import CognitivePolicy


def test_all_good_state():
    """Test ALL GOOD condition - should recommend takeoff."""
    policy = CognitivePolicy()
    
    # Perfect state - all parameters optimal
    state = {
        "focus": 0.8,
        "fatigue": 0.2,
        "overload": 0.3,
        "stress": 0.2
    }
    
    result = policy.evaluate(state)
    
    assert result["severity"] == "good", f"Expected 'good', got {result['severity']}"
    assert result["all_good"] == True, "Should detect all_good state"
    assert result["all_bad"] == False, "Should not detect all_bad state"
    assert len(result["recommendations"]) > 0, "Should have recommendations"
    assert result["recommendations"][0]["action"] == "takeoff", "Should recommend takeoff"
    
    print("✅ test_all_good_state PASSED")


def test_all_bad_state():
    """Test ALL BAD condition - should recommend land."""
    policy = CognitivePolicy()
    
    # Critical state - all parameters bad
    state = {
        "focus": 0.3,
        "fatigue": 0.7,
        "overload": 0.8,
        "stress": 0.9
    }
    
    result = policy.evaluate(state)
    
    assert result["severity"] == "critical", f"Expected 'critical', got {result['severity']}"
    assert result["all_good"] == False, "Should not detect all_good state"
    assert result["all_bad"] == True, "Should detect all_bad state"
    assert len(result["recommendations"]) > 0, "Should have recommendations"
    assert result["recommendations"][0]["action"] == "land", "Should recommend land"
    
    print("✅ test_all_bad_state PASSED")


def test_mixed_state():
    """Test MIXED condition - should recommend turn_around."""
    policy = CognitivePolicy()
    
    # Mixed state - some good, some bad
    state = {
        "focus": 0.5,  # Between thresholds
        "fatigue": 0.5,  # Between thresholds
        "overload": 0.7,  # High
        "stress": 0.3  # Low
    }
    
    result = policy.evaluate(state)
    
    assert result["severity"] == "normal", f"Expected 'normal', got {result['severity']}"
    assert result["all_good"] == False, "Should not detect all_good state"
    assert result["all_bad"] == False, "Should not detect all_bad state"
    assert len(result["recommendations"]) > 0, "Should have recommendations"
    assert result["recommendations"][0]["action"] == "turn_around", "Should recommend turn_around"
    
    print("✅ test_mixed_state PASSED")


def test_threshold_boundaries():
    """Test exact threshold boundaries."""
    policy = CognitivePolicy()
    
    # Test focus at exactly 0.6 (should be good)
    state_at_high_threshold = {
        "focus": 0.6,
        "fatigue": 0.4,
        "overload": 0.4,
        "stress": 0.4
    }
    result = policy.evaluate(state_at_high_threshold)
    assert result["all_good"] == True, "At high threshold should be all_good"
    
    # Test focus at exactly 0.4 (should be bad)
    state_at_low_threshold = {
        "focus": 0.4,
        "fatigue": 0.6,
        "overload": 0.6,
        "stress": 0.6
    }
    result = policy.evaluate(state_at_low_threshold)
    assert result["all_bad"] == True, "At low threshold should be all_bad"
    
    print("✅ test_threshold_boundaries PASSED")


def test_single_parameter_off():
    """Test that if even ONE parameter is off, it's not all_good or all_bad."""
    policy = CognitivePolicy()
    
    # Almost all good, but fatigue too high
    state = {
        "focus": 0.8,
        "fatigue": 0.5,  # Too high for all_good
        "overload": 0.3,
        "stress": 0.2
    }
    result = policy.evaluate(state)
    assert result["all_good"] == False, "One parameter off should not be all_good"
    assert result["all_bad"] == False, "Should not be all_bad"
    assert result["recommendations"][0]["action"] == "turn_around", "Should turn around"
    
    print("✅ test_single_parameter_off PASSED")


def run_all_tests():
    """Run all policy tests."""
    print("\n" + "="*60)
    print("TESTING: CognitivePolicy (Binary Logic)")
    print("="*60 + "\n")
    
    try:
        test_all_good_state()
        test_all_bad_state()
        test_mixed_state()
        test_threshold_boundaries()
        test_single_parameter_off()
        
        print("\n" + "="*60)
        print("✅ ALL POLICY TESTS PASSED!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

