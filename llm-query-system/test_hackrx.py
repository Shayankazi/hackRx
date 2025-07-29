#!/usr/bin/env python3

import asyncio
import json
import requests
from typing import List

# Test data matching the sample request
test_request = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the waiting period for cataract surgery?",
        "Are the medical expenses for an organ donor covered under this policy?"
    ]
}

def test_hackrx_endpoint():
    """Test the HackRX endpoint"""
    url = "http://localhost:8002/hackrx/run"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer 1bd20a1324c9d950f9c443def58aca75e5b2adb5ea615b3e6e4cd4a786ab1952"
    }
    
    try:
        print("Testing HackRX endpoint...")
        print(f"URL: {url}")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        response = requests.post(url, json=test_request, headers=headers, timeout=120)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def test_health_endpoint():
    """Test the health endpoint"""
    url = "http://localhost:8002/health"
    
    try:
        print("Testing health endpoint...")
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Health Status: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    print("=== Testing API Endpoints ===")
    test_health_endpoint()
    print("\n" + "="*50 + "\n")
    test_hackrx_endpoint()
