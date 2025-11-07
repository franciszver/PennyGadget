#!/usr/bin/env python3
"""
Test Demo Scenarios
Verifies all demo scenarios work correctly via API calls
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from sqlalchemy.orm import Session
from src.config.database import get_db_session
from src.models.user import User

BASE_URL = "http://localhost:8000"
DEMO_USERS = {
    "demo_goal_complete@demo.com": "180bcad6-380e-4a2f-809b-032677fcc721",
    "demo_sat_complete@demo.com": "0281a3c5-e9aa-4d65-ad33-f49a80a77a23",
    "demo_chemistry@demo.com": "063009da-20a4-4f53-8f67-f06573f7195e",
    "demo_low_sessions@demo.com": "e8bf67c3-57e6-405b-a1b5-80ac75aaf034",
    "demo_multi_goal@demo.com": "c02cb7f8-e63c-4945-9406-320e1d9046f3",
    "demo_qa@demo.com": "c0227285-166a-4a90-b7fd-d4d7e7ff4e39",
}


def get_mock_token():
    """Get mock token for development mode"""
    return "mock-token-demo-user"


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Health check passed: {data}")
            return True
        else:
            print(f"[FAIL] Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Is it running?")
        print("  Start with: python -m uvicorn src.api.main:app --reload")
        return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False


def test_progress_endpoint(user_id, email, scenario_name):
    """Test progress endpoint for a user"""
    print(f"\n--- Testing {scenario_name} ---")
    print(f"User: {email}")
    print(f"User ID: {user_id}")
    
    headers = {
        "Authorization": f"Bearer {get_mock_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test progress endpoint
        url = f"{BASE_URL}/api/v1/progress/{user_id}?include_suggestions=true"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[FAIL] Progress endpoint failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"[FAIL] Progress endpoint returned success=false")
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
            return False
        
        progress_data = data.get("data", {})
        goals = progress_data.get("goals", [])
        suggestions = progress_data.get("suggestions", [])
        
        print(f"[OK] Progress endpoint successful")
        print(f"  Goals found: {len(goals)}")
        print(f"  Suggestions found: {len(suggestions)}")
        
        # Show goal details
        for goal in goals[:3]:
            status = goal.get("status", "unknown")
            completion = goal.get("completion_percentage", 0)
            title = goal.get("title", "Unknown")
            print(f"    - {title}: {status} ({completion}%)")
        
        # Show suggestions
        if suggestions:
            print(f"  Suggestions:")
            for suggestion in suggestions[:5]:
                subjects = suggestion.get("subjects", [])
                if subjects:
                    print(f"    - {', '.join(subjects)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing progress: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nudges_endpoint(user_id, email, scenario_name):
    """Test nudges endpoint for a user"""
    print(f"\n--- Testing Nudges for {scenario_name} ---")
    print(f"User: {email}")
    
    headers = {
        "Authorization": f"Bearer {get_mock_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/v1/nudges/users/{user_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[FAIL] Nudges endpoint failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"[FAIL] Nudges endpoint returned success=false")
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
            return False
        
        nudges = data.get("data", {}).get("nudges", [])
        
        print(f"[OK] Nudges endpoint successful")
        print(f"  Active nudges: {len(nudges)}")
        
        for nudge in nudges[:3]:
            nudge_type = nudge.get("nudge_type", "unknown")
            message = nudge.get("message", "")[:60]
            suggestions = nudge.get("suggestions", [])
            print(f"    - Type: {nudge_type}")
            print(f"      Message: {message}...")
            if suggestions:
                print(f"      Suggestions: {', '.join(suggestions[:3])}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing nudges: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_goals_endpoint(user_id, email):
    """Test goals endpoint"""
    print(f"\n--- Testing Goals Endpoint ---")
    print(f"User: {email}")
    
    headers = {
        "Authorization": f"Bearer {get_mock_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/v1/goals?student_id={user_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[FAIL] Goals endpoint failed: {response.status_code}")
            return False
        
        data = response.json()
        
        # Handle response format: {"success": True, "data": [...]}
        if isinstance(data, dict) and "data" in data:
            goals = data.get("data", [])
            if not isinstance(goals, list):
                goals = []
        elif isinstance(data, list):
            goals = data
        else:
            goals = []
        
        print(f"[OK] Goals endpoint successful")
        print(f"  Goals found: {len(goals)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing goals: {e}")
        return False


def test_qa_endpoint(user_id, email):
    """Test Q&A endpoint"""
    print(f"\n--- Testing Q&A Endpoint ---")
    print(f"User: {email}")
    
    headers = {
        "Authorization": f"Bearer {get_mock_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test Q&A query
        url = f"{BASE_URL}/api/v1/qa/query"
        payload = {
            "student_id": user_id,
            "query": "What is photosynthesis?"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[FAIL] Q&A endpoint failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"[FAIL] Q&A endpoint returned success=false")
            return False
        
        response_text = data.get("data", {}).get("response", "")
        
        print(f"[OK] Q&A endpoint successful")
        print(f"  Response length: {len(response_text)} characters")
        print(f"  Response preview: {response_text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing Q&A: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_practice_endpoint(user_id, email):
    """Test practice assignment endpoint"""
    print(f"\n--- Testing Practice Endpoint ---")
    print(f"User: {email}")
    
    headers = {
        "Authorization": f"Bearer {get_mock_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test practice assignment
        url = f"{BASE_URL}/api/v1/practice/assign"
        params = {
            "student_id": user_id,
            "subject": "Math",
            "num_items": 3
        }
        response = requests.post(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"[FAIL] Practice endpoint failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"[FAIL] Practice endpoint returned success=false")
            return False
        
        assignment = data.get("data", {})
        items = assignment.get("items", [])
        
        print(f"[OK] Practice endpoint successful")
        print(f"  Items assigned: {len(items)}")
        
        if items:
            first_item = items[0]
            has_choices = "choices" in first_item
            has_correct_answer = "correct_answer" in first_item
            print(f"  First item has choices: {has_choices}")
            print(f"  First item has correct_answer: {has_correct_answer}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing practice: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all demo scenario tests"""
    print("="*60)
    print("Testing All Demo Scenarios")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("\n❌ Server is not running. Please start it first.")
        return
    
    results = {}
    
    # Test each demo scenario
    scenarios = {
        "demo_goal_complete@demo.com": "Goal Completion -> Related Subjects",
        "demo_sat_complete@demo.com": "SAT -> College Prep Pathway",
        "demo_chemistry@demo.com": "Chemistry -> STEM Pathway",
        "demo_low_sessions@demo.com": "Inactivity Nudge",
        "demo_multi_goal@demo.com": "Multi-Goal Tracking",
        "demo_qa@demo.com": "Q&A with Persistent History",
    }
    
    for email, scenario_name in scenarios.items():
        user_id = DEMO_USERS.get(email)
        if not user_id:
            print(f"\n[FAIL] User ID not found for {email}")
            continue
        
        # Test progress
        progress_ok = test_progress_endpoint(user_id, email, scenario_name)
        
        # Test nudges (especially for low_sessions)
        nudges_ok = test_nudges_endpoint(user_id, email, scenario_name)
        
        results[email] = {
            "progress": progress_ok,
            "nudges": nudges_ok
        }
    
    # Test Q&A with demo_qa account (has conversation history)
    qa_user_id = DEMO_USERS["demo_qa@demo.com"]
    qa_email = "demo_qa@demo.com"
    qa_ok = test_qa_endpoint(qa_user_id, qa_email)
    
    # Test common endpoints with one user
    test_user_id = DEMO_USERS["demo_multi_goal@demo.com"]
    test_email = "demo_multi_goal@demo.com"
    
    goals_ok = test_goals_endpoint(test_user_id, test_email)
    practice_ok = test_practice_endpoint(test_user_id, test_email)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for email, result in results.items():
        status = "[OK]" if result["progress"] and result["nudges"] else "[FAIL]"
        print(f"{status} {email}")
        if not result["progress"]:
            print(f"  - Progress endpoint failed")
            all_passed = False
        if not result["nudges"]:
            print(f"  - Nudges endpoint failed")
            all_passed = False
    
    print(f"\nCommon Endpoints:")
    print(f"{'[OK]' if goals_ok else '[FAIL]'} Goals endpoint")
    print(f"{'[OK]' if qa_ok else '[FAIL]'} Q&A endpoint")
    print(f"{'[OK]' if practice_ok else '[FAIL]'} Practice endpoint")
    
    if not goals_ok or not qa_ok or not practice_ok:
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILURE] Some tests failed. Check output above.")
    print("="*60)


if __name__ == "__main__":
    main()
