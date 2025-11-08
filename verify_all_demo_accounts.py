#!/usr/bin/env python3
"""
Verify all demo accounts work correctly and show intended demo scenarios
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
HEADERS = {"Authorization": "Bearer mock-token-123"}

# Demo accounts and their expected scenarios
DEMO_ACCOUNTS = {
    "demo_goal_complete@demo.com": {
        "user_id": "180bcad6-380e-4a2f-809b-032677fcc721",
        "scenario": "Goal completion → related subject suggestions",
        "checks": {
            "has_completed_goals": True,
            "has_related_suggestions": True,
            "suggestions_include_related_subjects": True
        }
    },
    "demo_sat_complete@demo.com": {
        "user_id": "0281a3c5-e9aa-4d65-ad33-f49a80a77a23",
        "scenario": "SAT → College Essays, Study Skills, AP Prep",
        "checks": {
            "has_completed_sat_goal": True,
            "suggestions_include": ["College Essays", "Study Skills", "AP Prep"]
        }
    },
    "demo_chemistry@demo.com": {
        "user_id": "063009da-20a4-4f53-8f67-f06573f7195e",
        "scenario": "Chemistry → Physics, STEM suggestions",
        "checks": {
            "has_completed_chemistry_goal": True,
            "suggestions_include": ["Physics", "Biology", "AP Chemistry", "STEM Prep"]
        }
    },
    "demo_low_sessions@demo.com": {
        "user_id": "e8bf67c3-57e6-405b-a1b5-80ac75aaf034",
        "scenario": "<3 sessions by Day 7 → inactivity nudge",
        "checks": {
            "has_inactivity_nudge": True,
            "session_count": "< 3",
            "days_since_signup": ">= 7"
        }
    },
    "demo_multi_goal@demo.com": {
        "user_id": "c02cb7f8-e63c-4945-9406-320e1d9046f3",
        "scenario": "Multiple goals progress tracking",
        "checks": {
            "goal_count": ">= 3",
            "all_goals_visible": True
        }
    },
    "demo_qa@demo.com": {
        "user_id": "c0227285-166a-4a90-b7fd-d4d7e7ff4e39",
        "scenario": "Conversational Q&A with persistent history",
        "checks": {
            "has_qa_history": True,
            "can_query": True
        }
    }
}

def test_progress_endpoint(user_id, account_name):
    """Test progress endpoint for goal completion suggestions"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/progress/{user_id}",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                progress_data = data.get("data", {})
                goals = progress_data.get("goals", [])
                suggestions = progress_data.get("suggestions", [])
                
                completed_goals = [g for g in goals if g.get("status") == "completed"]
                active_goals = [g for g in goals if g.get("status") == "active"]
                
                return {
                    "success": True,
                    "goals_count": len(goals),
                    "completed_count": len(completed_goals),
                    "active_count": len(active_goals),
                    "suggestions_count": len(suggestions),
                    "suggestions": suggestions,
                    "goals": goals
                }
            else:
                return {"success": False, "error": data.get("error")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_goals_endpoint(user_id, account_name):
    """Test goals endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/goals/?student_id={user_id}",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                goals = data.get("data", [])
                return {
                    "success": True,
                    "goals_count": len(goals),
                    "goals": goals
                }
            else:
                return {"success": False, "error": data.get("error")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_nudges_endpoint(user_id, account_name):
    """Test nudges endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/nudges/users/{user_id}",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                nudges = data.get("data", {}).get("nudges", [])
                return {
                    "success": True,
                    "nudges_count": len(nudges),
                    "nudges": nudges
                }
            else:
                return {"success": False, "error": data.get("error")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_account(account_email, account_info):
    """Verify a single demo account"""
    user_id = account_info["user_id"]
    scenario = account_info["scenario"]
    checks = account_info["checks"]
    
    print(f"\n{'='*70}")
    print(f"Testing: {account_email}")
    print(f"Scenario: {scenario.replace('→', '->')}")
    print(f"User ID: {user_id}")
    print(f"{'='*70}")
    
    results = {
        "account": account_email,
        "scenario": scenario,
        "user_id": user_id,
        "tests": {}
    }
    
    # Test progress endpoint
    print("\n[1] Testing Progress Endpoint...")
    progress_result = test_progress_endpoint(user_id, account_email)
    results["tests"]["progress"] = progress_result
    
    if progress_result.get("success"):
        print(f"  [OK] Progress endpoint working")
        print(f"    - Goals: {progress_result.get('goals_count', 0)} total "
              f"({progress_result.get('completed_count', 0)} completed, "
              f"{progress_result.get('active_count', 0)} active)")
        print(f"    - Suggestions: {progress_result.get('suggestions_count', 0)}")
        if progress_result.get('suggestions'):
            print(f"    - Suggestion subjects: {[s.get('subject', s.get('name', 'N/A')) for s in progress_result.get('suggestions', [])]}")
    else:
        print(f"  [FAIL] Progress endpoint failed: {progress_result.get('error')}")
    
    # Test goals endpoint
    print("\n[2] Testing Goals Endpoint...")
    goals_result = test_goals_endpoint(user_id, account_email)
    results["tests"]["goals"] = goals_result
    
    if goals_result.get("success"):
        print(f"  [OK] Goals endpoint working")
        print(f"    - Goals returned: {goals_result.get('goals_count', 0)}")
        if goals_result.get('goals'):
            print(f"    - Goal titles: {[g.get('title', 'N/A') for g in goals_result.get('goals', [])]}")
    else:
        print(f"  [FAIL] Goals endpoint failed: {goals_result.get('error')}")
    
    # Test nudges endpoint
    print("\n[3] Testing Nudges Endpoint...")
    nudges_result = test_nudges_endpoint(user_id, account_email)
    results["tests"]["nudges"] = nudges_result
    
    if nudges_result.get("success"):
        print(f"  [OK] Nudges endpoint working")
        print(f"    - Nudges returned: {nudges_result.get('nudges_count', 0)}")
        if nudges_result.get('nudges'):
            for nudge in nudges_result.get('nudges', []):
                print(f"    - Nudge: {nudge.get('type', 'N/A')} - {nudge.get('message', 'N/A')[:60]}...")
    else:
        print(f"  [FAIL] Nudges endpoint failed: {nudges_result.get('error')}")
    
    # Verify scenario-specific checks
    print("\n[4] Verifying Scenario-Specific Checks...")
    all_passed = True
    
    if account_email == "demo_goal_complete@demo.com":
        if progress_result.get("success"):
            completed = progress_result.get("completed_count", 0)
            suggestions = progress_result.get("suggestions_count", 0)
            if completed > 0 and suggestions > 0:
                print(f"  [OK] Has completed goals ({completed}) and suggestions ({suggestions})")
            else:
                print(f"  [FAIL] Missing: completed goals ({completed}) or suggestions ({suggestions})")
                all_passed = False
    
    elif account_email == "demo_sat_complete@demo.com":
        if progress_result.get("success"):
            suggestions = progress_result.get("suggestions", [])
            suggestion_subjects = [s.get("subject", s.get("name", "")) for s in suggestions]
            expected = ["College Essays", "Study Skills", "AP Prep"]
            found = [exp for exp in expected if any(exp.lower() in str(subj).lower() for subj in suggestion_subjects)]
            if found:
                print(f"  [OK] Found expected suggestions: {found}")
            else:
                print(f"  [FAIL] Missing expected suggestions. Found: {suggestion_subjects}")
                all_passed = False
    
    elif account_email == "demo_chemistry@demo.com":
        if progress_result.get("success"):
            suggestions = progress_result.get("suggestions", [])
            suggestion_subjects = [s.get("subject", s.get("name", "")) for s in suggestions]
            expected = ["Physics", "Biology", "AP Chemistry", "STEM Prep"]
            found = [exp for exp in expected if any(exp.lower() in str(subj).lower() for subj in suggestion_subjects)]
            if found:
                print(f"  [OK] Found expected suggestions: {found}")
            else:
                print(f"  [FAIL] Missing expected suggestions. Found: {suggestion_subjects}")
                all_passed = False
    
    elif account_email == "demo_low_sessions@demo.com":
        if nudges_result.get("success"):
            nudges = nudges_result.get("nudges", [])
            inactivity_nudges = [n for n in nudges if n.get("type") == "inactivity"]
            if inactivity_nudges:
                print(f"  [OK] Has inactivity nudge")
            else:
                print(f"  [FAIL] Missing inactivity nudge")
                all_passed = False
    
    elif account_email == "demo_multi_goal@demo.com":
        if goals_result.get("success"):
            goal_count = goals_result.get("goals_count", 0)
            if goal_count >= 3:
                print(f"  [OK] Has multiple goals ({goal_count})")
            else:
                print(f"  [FAIL] Expected >= 3 goals, found {goal_count}")
                all_passed = False
    
    elif account_email == "demo_qa@demo.com":
        print(f"  [INFO] Q&A history check requires manual testing")
    
    if all_passed:
        print(f"\n[PASS] All checks passed for {account_email}")
    else:
        print(f"\n[FAIL] Some checks failed for {account_email}")
    
    return results

def main():
    print("="*70)
    print("Demo Account Verification")
    print("="*70)
    print(f"Testing {len(DEMO_ACCOUNTS)} demo accounts...")
    print(f"Base URL: {BASE_URL}")
    
    all_results = []
    for account_email, account_info in DEMO_ACCOUNTS.items():
        try:
            result = verify_account(account_email, account_info)
            all_results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Error testing {account_email}: {str(e)}")
            all_results.append({
                "account": account_email,
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    for result in all_results:
        account = result.get("account", "Unknown")
        if "error" in result:
            print(f"[ERROR] {account}: {result['error']}")
        else:
            tests = result.get("tests", {})
            progress_ok = tests.get("progress", {}).get("success", False)
            goals_ok = tests.get("goals", {}).get("success", False)
            nudges_ok = tests.get("nudges", {}).get("success", False)
            
            status = "[OK]" if (progress_ok and goals_ok and nudges_ok) else "[PARTIAL]"
            print(f"{status} {account}: Progress={progress_ok}, Goals={goals_ok}, Nudges={nudges_ok}")
    
    print(f"\n{'='*70}")
    print("Verification complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

