#!/usr/bin/env python3
"""
Test script for FastAPI Survey Generation API
"""

import requests
import json
import time
import asyncio
import websockets
from typing import Dict, Any

# API configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-12345"
HEADERS = {"api-key": API_KEY}


def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_health():
    """Test health check"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_upload_paper():
    """Test paper upload"""
    print("Testing paper upload...")
    
    # Create a dummy text file
    with open("test_paper.txt", "w") as f:
        f.write("This is a test paper about LLMs and their applications.")
    
    with open("test_paper.txt", "rb") as f:
        files = {"file": ("test_paper.txt", f, "text/plain")}
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=HEADERS
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Paper ID: {data['paper_id']}")
        print(f"Filename: {data['filename']}\n")
        return data["paper_id"]
    else:
        print(f"Error: {response.text}\n")
        return None


def test_create_survey(paper_ids=None):
    """Test survey creation"""
    print("Testing survey creation...")
    
    payload = {
        "topic": "Large Language Models and Their Applications",
        "system_type": "iterative",
        "max_iterations": 3,
        "model_preference": "balanced"
    }
    
    if paper_ids:
        payload["paper_ids"] = paper_ids
    
    response = requests.post(
        f"{BASE_URL}/surveys",
        json=payload,
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Survey ID: {data['survey_id']}")
        print(f"Status: {data['status']}")
        print(f"Topic: {data['topic']}\n")
        return data["survey_id"]
    else:
        print(f"Error: {response.text}\n")
        return None


def test_get_survey_status(survey_id: str):
    """Test getting survey status"""
    print(f"Getting status for survey {survey_id}...")
    
    response = requests.get(
        f"{BASE_URL}/surveys/{survey_id}/status",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Survey Status: {data['status']}")
        print(f"Current Phase: {data.get('current_phase')}")
        print(f"Current Iteration: {data.get('current_iteration')}")
        print(f"Quality Score: {data.get('quality_score')}\n")
        return data
    else:
        print(f"Error: {response.text}\n")
        return None


def test_list_papers():
    """Test listing papers"""
    print("Testing paper listing...")
    
    response = requests.get(
        f"{BASE_URL}/papers",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Papers: {data['total']}")
        print(f"Papers shown: {len(data['papers'])}\n")
        return True
    else:
        print(f"Error: {response.text}\n")
        return False


def test_get_survey(survey_id: str):
    """Test getting completed survey"""
    print(f"Getting survey {survey_id}...")
    
    response = requests.get(
        f"{BASE_URL}/surveys/{survey_id}",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Survey Title: {data.get('title')}")
        print(f"Sections: {len(data.get('sections', []))}")
        print(f"Quality Score: {data.get('quality_score')}\n")
        return True
    elif response.status_code == 400:
        print(f"Survey not ready: {response.json()['detail']}\n")
        return False
    else:
        print(f"Error: {response.text}\n")
        return False


async def test_websocket(survey_id: str):
    """Test WebSocket connection"""
    print(f"Testing WebSocket for survey {survey_id}...")
    
    uri = f"ws://localhost:8000/ws/{survey_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected!")
            
            # Receive updates for 10 seconds
            end_time = time.time() + 10
            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(message)
                    print(f"Update: Status={data['status']}, "
                          f"Phase={data.get('current_phase')}, "
                          f"Score={data.get('quality_score')}")
                    
                    if data["status"] in ["completed", "failed"]:
                        break
                except asyncio.TimeoutError:
                    continue
            
            print("WebSocket test completed!\n")
            return True
            
    except Exception as e:
        print(f"WebSocket error: {e}\n")
        return False


def test_rate_limiting():
    """Test rate limiting"""
    print("Testing rate limiting...")
    
    # Try to exceed rate limit (10 surveys per minute)
    success_count = 0
    rate_limited_count = 0
    
    for i in range(12):
        payload = {
            "topic": f"Test Topic {i}",
            "system_type": "baseline"
        }
        
        response = requests.post(
            f"{BASE_URL}/surveys",
            json=payload,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
            print(f"Rate limited at request {i+1}")
            break
    
    print(f"Successful requests: {success_count}")
    print(f"Rate limited: {rate_limited_count > 0}\n")
    return rate_limited_count > 0


def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("LLM Survey Generator API Test Suite")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Basic tests
    results["Root"] = test_root()
    results["Health"] = test_health()
    
    # Upload test
    paper_id = test_upload_paper()
    results["Upload"] = paper_id is not None
    
    # Survey creation
    survey_id = test_create_survey([paper_id] if paper_id else None)
    results["Create Survey"] = survey_id is not None
    
    if survey_id:
        # Wait a bit for processing
        time.sleep(2)
        
        # Status check
        status = test_get_survey_status(survey_id)
        results["Get Status"] = status is not None
        
        # WebSocket test
        asyncio.run(test_websocket(survey_id))
        results["WebSocket"] = True
        
        # Wait for completion
        print("Waiting for survey to complete...")
        for _ in range(10):
            time.sleep(2)
            status = test_get_survey_status(survey_id)
            if status and status["status"] == "completed":
                break
        
        # Get completed survey
        results["Get Survey"] = test_get_survey(survey_id)
    
    # List papers
    results["List Papers"] = test_list_papers()
    
    # Rate limiting
    results["Rate Limiting"] = test_rate_limiting()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Clean up
    import os
    if os.path.exists("test_paper.txt"):
        os.remove("test_paper.txt")
    
    return passed == total


if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print("API is running!\n")
    except requests.ConnectionError:
        print("Error: API is not running.")
        print("Start it with: uvicorn src.api.main:app --reload")
        exit(1)
    
    # Run tests
    success = run_all_tests()
    exit(0 if success else 1)