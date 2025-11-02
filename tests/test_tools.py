"""
Test suite for DroneTools - Binary control functions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import DroneTools


def test_takeoff():
    """Test takeoff tool - should go to 1.0m."""
    tools = DroneTools()
    
    # Start at ground
    assert tools.current_altitude == 0.0, "Should start at ground level"
    
    # Execute takeoff
    result = tools.takeoff()
    
    assert result["success"] == True, "Takeoff should succeed"
    assert result["action"] == "takeoff", "Action should be 'takeoff'"
    assert tools.current_altitude == 1.0, f"Should be at 1.0m, got {tools.current_altitude}"
    assert result["new_altitude_m"] == 1.0, "Result should show 1.0m"
    assert len(tools.action_history) == 1, "Should log action"
    
    print("✅ test_takeoff PASSED")


def test_land():
    """Test land tool - should go to 0.0m."""
    tools = DroneTools()
    
    # Start at 1m
    tools.current_altitude = 1.0
    
    # Execute land
    result = tools.land()
    
    assert result["success"] == True, "Land should succeed"
    assert result["action"] == "land", "Action should be 'land'"
    assert tools.current_altitude == 0.0, f"Should be at ground level, got {tools.current_altitude}"
    assert result["new_altitude_m"] == 0.0, "Result should show 0.0m"
    
    print("✅ test_land PASSED")


def test_turn_around():
    """Test turn_around tool - should rotate 180°."""
    tools = DroneTools()
    
    # Start at 0°
    assert tools.current_rotation == 0.0, "Should start at 0°"
    
    # First rotation
    result = tools.turn_around()
    assert result["success"] == True, "Turn should succeed"
    assert result["action"] == "turn_around", "Action should be 'turn_around'"
    assert tools.current_rotation == 180.0, f"Should be at 180°, got {tools.current_rotation}"
    
    # Second rotation (should wrap to 360/0)
    result = tools.turn_around()
    assert tools.current_rotation == 0.0, f"Should wrap to 0°, got {tools.current_rotation}"
    
    print("✅ test_turn_around PASSED")


def test_execute_tool():
    """Test execute_tool dispatcher."""
    tools = DroneTools()
    
    # Test takeoff via execute_tool
    result = tools.execute_tool("takeoff", {})
    assert result["action"] == "takeoff", "Should execute takeoff"
    assert tools.current_altitude == 1.0, "Should be at 1m"
    
    # Test land via execute_tool
    result = tools.execute_tool("land", {})
    assert result["action"] == "land", "Should execute land"
    assert tools.current_altitude == 0.0, "Should be at ground"
    
    # Test turn_around via execute_tool
    result = tools.execute_tool("turn_around", {})
    assert result["action"] == "turn_around", "Should execute turn_around"
    assert tools.current_rotation == 180.0, "Should be at 180°"
    
    # Test invalid tool
    result = tools.execute_tool("invalid_tool", {})
    assert result["success"] == False, "Invalid tool should fail"
    
    print("✅ test_execute_tool PASSED")


def test_action_history():
    """Test that all actions are logged."""
    tools = DroneTools()
    
    tools.takeoff()
    tools.turn_around()
    tools.land()
    
    assert len(tools.action_history) == 3, f"Should have 3 actions, got {len(tools.action_history)}"
    assert tools.action_history[0]["action"] == "takeoff", "First action should be takeoff"
    assert tools.action_history[1]["action"] == "turn_around", "Second should be turn_around"
    assert tools.action_history[2]["action"] == "land", "Third should be land"
    
    print("✅ test_action_history PASSED")


def test_binary_altitude_constraint():
    """Test that altitude stays binary (0m or 1m only)."""
    tools = DroneTools()
    
    # Takeoff always goes to exactly 1.0m
    tools.takeoff()
    assert tools.current_altitude == 1.0, "Takeoff should be exactly 1.0m"
    
    # Land always goes to exactly 0.0m
    tools.land()
    assert tools.current_altitude == 0.0, "Land should be exactly 0.0m"
    
    # Multiple takeoffs should stay at 1.0m
    tools.takeoff()
    tools.takeoff()
    assert tools.current_altitude == 1.0, "Should stay at 1.0m"
    
    print("✅ test_binary_altitude_constraint PASSED")


def run_all_tests():
    """Run all tool tests."""
    print("\n" + "="*60)
    print("TESTING: DroneTools (Binary Controls)")
    print("="*60 + "\n")
    
    try:
        test_takeoff()
        test_land()
        test_turn_around()
        test_execute_tool()
        test_action_history()
        test_binary_altitude_constraint()
        
        print("\n" + "="*60)
        print("✅ ALL TOOL TESTS PASSED!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

