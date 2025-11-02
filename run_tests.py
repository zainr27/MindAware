#!/usr/bin/env python3
"""
Master test runner for MindAware system.
Runs all test suites and provides summary.
"""

import sys
import os
import subprocess
import time

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{NC}\n")


def run_test_file(filepath, description):
    """Run a single test file and return success status."""
    print(f"{YELLOW}Running: {description}{NC}")
    
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"{RED}❌ Test timed out after 30 seconds{NC}")
        return False
    except Exception as e:
        print(f"{RED}❌ Error running test: {e}{NC}")
        return False


def check_backend_running():
    """Check if backend server is running."""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    """Run all tests."""
    print_header("🧠 MindAware - Complete Test Suite")
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    results = {}
    
    # Test 1: Policy Tests
    print_header("1️⃣  Testing Policy Engine (Binary Logic)")
    results["policy"] = run_test_file("tests/test_policy.py", "CognitivePolicy Tests")
    
    # Test 2: Tools Tests
    print_header("2️⃣  Testing Drone Control Tools")
    results["tools"] = run_test_file("tests/test_tools.py", "DroneTools Tests")
    
    # Test 3: Integration Tests
    print_header("3️⃣  Testing Integration (End-to-End)")
    results["integration"] = run_test_file("tests/test_integration.py", "Integration Tests")
    
    # Test 4: Simulator Tests
    print_header("4️⃣  Testing Simulators (EEG & Drone)")
    results["simulators"] = run_test_file("tests/test_simulators.py", "Simulator Tests")
    
    # Test 5: API Tests (optional if backend running)
    print_header("5️⃣  Testing API Endpoints")
    backend_running = check_backend_running()
    
    if backend_running:
        print(f"{GREEN}✓ Backend server detected on http://localhost:8000{NC}\n")
        results["api"] = run_test_file("tests/test_api.py", "API Endpoint Tests")
    else:
        print(f"{YELLOW}⚠️  Backend server not running - Skipping API tests{NC}")
        print(f"{YELLOW}   Start with: cd src/api && uvicorn server:app --reload{NC}\n")
        results["api"] = None
    
    # Print Summary
    print_header("📊 TEST SUMMARY")
    
    total_suites = len([r for r in results.values() if r is not None])
    passed_suites = sum([1 for r in results.values() if r is True])
    
    print("Test Suite Results:")
    print("-" * 70)
    
    for suite_name, result in results.items():
        if result is None:
            status = f"{YELLOW}SKIPPED{NC}"
            emoji = "⏭️ "
        elif result:
            status = f"{GREEN}PASSED{NC}"
            emoji = "✅"
        else:
            status = f"{RED}FAILED{NC}"
            emoji = "❌"
        
        print(f"  {emoji} {suite_name.capitalize():20s} {status}")
    
    print("-" * 70)
    print(f"\nTotal: {passed_suites}/{total_suites} test suites passed")
    
    # Overall result
    if passed_suites == total_suites:
        print(f"\n{GREEN}{'='*70}")
        print(f"  ✅ ALL TESTS PASSED! System is working correctly.")
        print(f"{'='*70}{NC}\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}")
        print(f"  ❌ SOME TESTS FAILED - Please review errors above")
        print(f"{'='*70}{NC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

