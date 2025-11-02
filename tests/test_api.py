"""
API endpoint tests for MindAware backend.
Requires backend server to be running.
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test /health endpoint."""
    print("\n[TEST] GET /health")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy", f"Expected healthy, got {data}"
        print("✅ /health endpoint PASSED")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ /health endpoint FAILED - Server not running?")
        return False


def test_root_endpoint():
    """Test / endpoint."""
    print("\n[TEST] GET /")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data, "Should have status field"
        assert "components" in data, "Should have components field"
        assert data["version"] == "1.0.0", "Should have correct version"
        print("✅ / endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ / endpoint FAILED: {e}")
        return False


def test_eeg_ingest_endpoint():
    """Test /eeg/ingest endpoint."""
    print("\n[TEST] POST /eeg/ingest")
    
    try:
        payload = {
            "raw_string": "F[not_focus:0.88 focus:0.12] Y[yaw_left:0.29 yaw_right:0.71] yaw=3416.347 B[rate0.5=0.00]"
        }
        
        response = requests.post(f"{BASE_URL}/eeg/ingest", json=payload, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "success", f"Expected success, got {data}"
        assert "buffer_size" in data, "Should have buffer_size"
        print("✅ /eeg/ingest endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ /eeg/ingest endpoint FAILED: {e}")
        return False


def test_eeg_status_endpoint():
    """Test /eeg/status endpoint."""
    print("\n[TEST] GET /eeg/status")
    
    try:
        response = requests.get(f"{BASE_URL}/eeg/status", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data, "Should have status field"
        assert "adapter" in data, "Should have adapter info"
        print("✅ /eeg/status endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ /eeg/status endpoint FAILED: {e}")
        return False


def test_eeg_state_endpoint():
    """Test /eeg/state endpoint."""
    print("\n[TEST] GET /eeg/state")
    
    try:
        response = requests.get(f"{BASE_URL}/eeg/state", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "focus" in data, "Should have focus metric"
        assert "fatigue" in data, "Should have fatigue metric"
        assert "overload" in data, "Should have overload metric"
        assert "stress" in data, "Should have stress metric"
        print("✅ /eeg/state endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ /eeg/state endpoint FAILED: {e}")
        return False


def test_logs_endpoint():
    """Test /logs endpoint."""
    print("\n[TEST] GET /logs")
    
    try:
        response = requests.get(f"{BASE_URL}/logs?count=5", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "logs" in data, "Should have logs field"
        assert "count" in data, "Should have count field"
        print("✅ /logs endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ /logs endpoint FAILED: {e}")
        return False


def test_memory_endpoint():
    """Test /memory endpoint."""
    print("\n[TEST] GET /memory")
    
    try:
        response = requests.get(f"{BASE_URL}/memory", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "state_count" in data, "Should have state_count"
        assert "decision_count" in data, "Should have decision_count"
        print("✅ /memory endpoint PASSED")
        return True
    except Exception as e:
        print(f"❌ /memory endpoint FAILED: {e}")
        return False


def run_all_tests():
    """Run all API tests."""
    print("\n" + "="*60)
    print("TESTING: API Endpoints")
    print("="*60)
    print("\nNOTE: Backend server must be running on http://localhost:8000")
    print("      Start with: cd src/api && uvicorn server:app --reload\n")
    
    results = []
    results.append(test_health_endpoint())
    
    if not results[0]:
        print("\n" + "="*60)
        print("❌ BACKEND NOT RUNNING - Skipping remaining API tests")
        print("="*60 + "\n")
        return False
    
    results.append(test_root_endpoint())
    results.append(test_eeg_ingest_endpoint())
    results.append(test_eeg_status_endpoint())
    results.append(test_eeg_state_endpoint())
    results.append(test_logs_endpoint())
    results.append(test_memory_endpoint())
    
    all_passed = all(results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL API TESTS PASSED!")
    else:
        print(f"❌ {sum(results)}/{len(results)} API TESTS PASSED")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

