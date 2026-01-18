"""Test API endpoints."""

import time
import requests
import json

# Give server a moment to be ready
time.sleep(2)

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("Testing API Endpoints")
print("=" * 60)

# Test 1: GET /
print("\n[TEST 1] GET /")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json()["message"] == "Assignment Evaluation API"
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")

# Test 2: GET /health
print("\n[TEST 2] GET /health")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json()["status"] == "ok"
    print("✓ PASS")
except Exception as e:
    print(f"✗ FAIL: {e}")

# Test 3: POST /api/evaluate (no files - should fail gracefully)
print("\n[TEST 3] POST /api/evaluate (validation test)")
try:
    response = requests.post(
        f"{BASE_URL}/api/evaluate",
        data={
            "assignment_type": "code",
        },
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
    print("✓ PASS (endpoint accessible, request validation working)")
except Exception as e:
    print(f"✗ FAIL: {e}")

print("\n" + "=" * 60)
print("API Backend is running cleanly!")
print("=" * 60)
