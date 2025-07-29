#!/usr/bin/env python3

import requests
import json

# Simplified test with just one question
test_request = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment?"
    ]
}

def test_simple_hackrx():
    url = "http://localhost:8002/hackrx/run"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("Testing simple HackRx request...")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        response = requests.post(url, json=test_request, headers=headers, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_hackrx()
