#!/usr/bin/env python3
"""
Test script to verify CORS is working properly
"""

import requests
import json

def test_cors():
    """Test CORS configuration"""
    api_base = "http://localhost:5001/api"
    
    print("🧪 Testing CORS configuration...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{api_base}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: OPTIONS preflight request
    print("\n2. Testing OPTIONS preflight...")
    try:
        headers = {
            'Origin': 'http://localhost:8000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{api_base}/boats", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: POST request with CORS headers
    print("\n3. Testing POST request...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:8000'
        }
        data = {"boats": []}
        response = requests.post(f"{api_base}/boats", 
                               headers=headers, 
                               json=data)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_cors()
