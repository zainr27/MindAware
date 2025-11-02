"""
Integration tests for the complete MindAware agent flow.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import CognitivePolicy, DroneTools, DecisionLogger, AgentMemory


def test_end_to_end_all_good():
    """Test complete flow with all good parameters."""
    print("\n[TEST] End-to-end: ALL GOOD scenario")
    
    policy = CognitivePolicy()
    tools = DroneTools()
    memory = AgentMemory()
    
    # Simulate perfect cognitive state
    state = {
        "focus": 0.8,
        "fatigue": 0.2,
        "overload": 0.3,
        "stress": 0.2
    }
    
    # Add to memory
    memory.add_cognitive_state(state)
    
    # Get policy recommendation
    policy_result = policy.evaluate(state)
    
    assert policy_result["all_good"] == True, "Should detect all_good"
    assert policy_result["recommendations"][0]["action"] == "takeoff", "Should recommend takeoff"
    
    # Execute action
    action = policy_result["recommendations"][0]
    result = tools.execute_tool(action["action"], action.get("parameters", {}))
    
    assert result["success"] == True, "Action should succeed"
    assert tools.current_altitude == 1.0, "Should be at 1m"
    
    print("✅ End-to-end ALL GOOD test PASSED")


def test_end_to_end_all_bad():
    """Test complete flow with all bad parameters."""
    print("\n[TEST] End-to-end: ALL BAD scenario")
    
    policy = CognitivePolicy()
    tools = DroneTools()
    memory = AgentMemory()
    
    # Simulate critical state
    state = {
        "focus": 0.2,
        "fatigue": 0.8,
        "overload": 0.7,
        "stress": 0.9
    }
    
    # Start at 1m
    tools.current_altitude = 1.0
    
    # Add to memory
    memory.add_cognitive_state(state)
    
    # Get policy recommendation
    policy_result = policy.evaluate(state)
    
    assert policy_result["all_bad"] == True, "Should detect all_bad"
    assert policy_result["recommendations"][0]["action"] == "land", "Should recommend land"
    
    # Execute action
    action = policy_result["recommendations"][0]
    result = tools.execute_tool(action["action"], action.get("parameters", {}))
    
    assert result["success"] == True, "Action should succeed"
    assert tools.current_altitude == 0.0, "Should be at ground"
    
    print("✅ End-to-end ALL BAD test PASSED")


def test_end_to_end_mixed():
    """Test complete flow with mixed parameters."""
    print("\n[TEST] End-to-end: MIXED scenario")
    
    policy = CognitivePolicy()
    tools = DroneTools()
    memory = AgentMemory()
    
    # Simulate mixed state
    state = {
        "focus": 0.5,
        "fatigue": 0.5,
        "overload": 0.7,
        "stress": 0.3
    }
    
    # Add to memory
    memory.add_cognitive_state(state)
    
    # Get policy recommendation
    policy_result = policy.evaluate(state)
    
    assert policy_result["all_good"] == False, "Should not be all_good"
    assert policy_result["all_bad"] == False, "Should not be all_bad"
    assert policy_result["recommendations"][0]["action"] == "turn_around", "Should recommend turn_around"
    
    # Execute action
    action = policy_result["recommendations"][0]
    result = tools.execute_tool(action["action"], action.get("parameters", {}))
    
    assert result["success"] == True, "Action should succeed"
    assert tools.current_rotation == 180.0, "Should be at 180°"
    
    print("✅ End-to-end MIXED test PASSED")


def test_state_transition():
    """Test transitioning from good to bad state."""
    print("\n[TEST] State transition: GOOD → BAD")
    
    policy = CognitivePolicy()
    tools = DroneTools()
    memory = AgentMemory()
    
    # Start with good state
    good_state = {
        "focus": 0.8,
        "fatigue": 0.2,
        "overload": 0.3,
        "stress": 0.2
    }
    
    memory.add_cognitive_state(good_state)
    policy_result = policy.evaluate(good_state)
    action = policy_result["recommendations"][0]
    tools.execute_tool(action["action"], {})
    
    assert tools.current_altitude == 1.0, "Should take off to 1m"
    
    # Transition to bad state
    bad_state = {
        "focus": 0.3,
        "fatigue": 0.7,
        "overload": 0.8,
        "stress": 0.9
    }
    
    memory.add_cognitive_state(bad_state)
    policy_result = policy.evaluate(bad_state)
    action = policy_result["recommendations"][0]
    tools.execute_tool(action["action"], {})
    
    assert tools.current_altitude == 0.0, "Should land to 0m"
    
    # Check memory
    context = memory.get_context_summary()
    assert context["state_count"] == 2, "Should have 2 states in memory"
    
    print("✅ State transition test PASSED")


def test_memory_tracking():
    """Test that memory correctly tracks states and decisions."""
    print("\n[TEST] Memory tracking")
    
    memory = AgentMemory()
    
    # Add multiple states
    states = [
        {"focus": 0.8, "fatigue": 0.2, "overload": 0.3, "stress": 0.2},
        {"focus": 0.5, "fatigue": 0.5, "overload": 0.5, "stress": 0.5},
        {"focus": 0.3, "fatigue": 0.7, "overload": 0.8, "stress": 0.9}
    ]
    
    for state in states:
        memory.add_cognitive_state(state)
    
    # Check context
    context = memory.get_context_summary()
    assert context["state_count"] == 3, f"Should have 3 states, got {context['state_count']}"
    
    # Add decisions
    for i in range(2):
        decision = {"action": f"action_{i}", "result": "success"}
        memory.add_decision(decision)
    
    context = memory.get_context_summary()
    assert context["decision_count"] == 2, f"Should have 2 decisions, got {context['decision_count']}"
    
    # Test recent retrieval
    recent = memory.get_recent_cognitive_states(2)
    assert len(recent) == 2, "Should get last 2 states"
    assert recent[0]["focus"] == 0.5, "First should be second state"
    assert recent[1]["focus"] == 0.3, "Second should be third state"
    
    print("✅ Memory tracking test PASSED")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("TESTING: Integration (End-to-End Flows)")
    print("="*60 + "\n")
    
    try:
        test_end_to_end_all_good()
        test_end_to_end_all_bad()
        test_end_to_end_mixed()
        test_state_transition()
        test_memory_tracking()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
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

