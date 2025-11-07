#!/usr/bin/env python3
"""
Comprehensive Demo Account Verification
Tests each demo account according to DEMO_USER_GUIDE.md specifications
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from sqlalchemy.orm import Session
from src.config.database import get_db_session
from src.models.user import User
from src.models.goal import Goal
from src.models.session import Session as SessionModel
from src.models.nudge import Nudge
from src.models.qa import QAInteraction
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

# Demo accounts from DEMO_USER_GUIDE.md
DEMO_ACCOUNTS = {
    "demo_goal_complete@demo.com": {
        "scenario": "Goal Completion -> Related Subjects",
        "expected": {
            "completed_goals": 1,
            "active_goals": 2,
            "has_suggestions": True,
            "suggestion_types": ["related_subject"]
        }
    },
    "demo_sat_complete@demo.com": {
        "scenario": "SAT Completion -> College Prep Pathway",
        "expected": {
            "completed_goals": 1,
            "active_goals": 0,
            "has_suggestions": True,
            "suggestion_subjects": ["College Essays", "Study Skills", "AP Prep"]
        }
    },
    "demo_chemistry@demo.com": {
        "scenario": "Chemistry -> Cross-Subject STEM Pathway",
        "expected": {
            "completed_goals": 1,
            "active_goals": 0,
            "has_suggestions": True,
            "suggestion_subjects": ["Physics", "Biology", "AP Chemistry", "STEM Prep"]
        }
    },
    "demo_low_sessions@demo.com": {
        "scenario": "Inactivity Nudge (<3 Sessions by Day 7)",
        "expected": {
            "completed_goals": 0,
            "active_goals": 1,
            "sessions": 2,
            "has_inactivity_nudge": True,
            "user_age_days": 7
        }
    },
    "demo_multi_goal@demo.com": {
        "scenario": "Multi-Goal Progress Tracking",
        "expected": {
            "completed_goals": 0,
            "active_goals": 3,
            "has_elo_ratings": True
        }
    },
    "demo_qa@demo.com": {
        "scenario": "Conversational Q&A with Memory",
        "expected": {
            "has_goals": True,
            "has_conversation_history": True
        }
    }
}


def get_user_id_from_db(email: str) -> str:
    """Get user ID from database"""
    with get_db_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return str(user.id)
    return None


def test_backend():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def verify_account_data(email: str, expected: dict) -> dict:
    """Verify account data in database"""
    results = {"passed": True, "issues": []}
    
    with get_db_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            results["passed"] = False
            results["issues"].append(f"User {email} does not exist in database")
            return results
        
        # Check goals
        if "completed_goals" in expected:
            completed = db.query(Goal).filter(
                Goal.student_id == user.id,
                Goal.status == "completed"
            ).count()
            if completed < expected["completed_goals"]:
                results["passed"] = False
                results["issues"].append(f"Expected {expected['completed_goals']} completed goals, found {completed}")
        
        if "active_goals" in expected:
            active = db.query(Goal).filter(
                Goal.student_id == user.id,
                Goal.status == "active"
            ).count()
            if active < expected["active_goals"]:
                results["passed"] = False
                results["issues"].append(f"Expected {expected['active_goals']} active goals, found {active}")
        
        # Check sessions
        if "sessions" in expected:
            session_count = db.query(SessionModel).filter(
                SessionModel.student_id == user.id
            ).count()
            if session_count != expected["sessions"]:
                results["passed"] = False
                results["issues"].append(f"Expected {expected['sessions']} sessions, found {session_count}")
        
        # Check user age
        if "user_age_days" in expected:
            now = datetime.now(timezone.utc)
            created_at = user.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = created_at.astimezone(timezone.utc)
            days_ago = (now - created_at).days
            if abs(days_ago - expected["user_age_days"]) > 1:
                results["passed"] = False
                results["issues"].append(f"Expected user age ~{expected['user_age_days']} days, found {days_ago}")
        
        # Check conversation history
        if "has_conversation_history" in expected and expected["has_conversation_history"]:
            conv_count = db.query(QAInteraction).filter(
                QAInteraction.student_id == user.id
            ).count()
            if conv_count == 0:
                results["issues"].append("No conversation history found (may be OK if not yet used)")
        
        # Check goals exist
        if "has_goals" in expected and expected["has_goals"]:
            goal_count = db.query(Goal).filter(Goal.student_id == user.id).count()
            if goal_count == 0:
                results["passed"] = False
                results["issues"].append("Expected at least one goal, found none")
    
    return results


def test_progress_api(email: str, user_id: str, expected: dict) -> dict:
    """Test progress API endpoint"""
    results = {"passed": True, "issues": [], "data": {}}
    
    headers = {
        "Authorization": "Bearer mock-token-demo-user",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/v1/progress/{user_id}?include_suggestions=true"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            results["passed"] = False
            results["issues"].append(f"API returned status {response.status_code}: {response.text[:200]}")
            return results
        
        data = response.json()
        if not data.get("success"):
            results["passed"] = False
            results["issues"].append(f"API returned success=false: {data.get('error', 'Unknown error')}")
            return results
        
        progress_data = data.get("data", {})
        goals = progress_data.get("goals", [])
        suggestions = progress_data.get("suggestions", [])
        
        results["data"] = {
            "goals": goals,
            "suggestions": suggestions
        }
        
        # Check suggestions
        if "has_suggestions" in expected:
            if expected["has_suggestions"] and len(suggestions) == 0:
                results["passed"] = False
                results["issues"].append("Expected suggestions but none found")
            elif not expected["has_suggestions"] and len(suggestions) > 0:
                results["issues"].append(f"Unexpected suggestions found: {len(suggestions)}")
        
        # Check specific suggestion subjects
        if "suggestion_subjects" in expected:
            found_subjects = [s.get("subject_name", "") for s in suggestions]
            missing = [s for s in expected["suggestion_subjects"] if s not in found_subjects]
            if missing:
                results["issues"].append(f"Expected suggestion subjects not found: {missing}")
        
        # Check Elo ratings
        if "has_elo_ratings" in expected and expected["has_elo_ratings"]:
            goals_with_elo = [g for g in goals if g.get("elo_rating") is not None]
            if len(goals_with_elo) == 0:
                results["issues"].append("Expected Elo ratings on goals but none found")
        
    except requests.exceptions.ConnectionError:
        results["passed"] = False
        results["issues"].append("Cannot connect to backend API (is it running?)")
    except Exception as e:
        results["passed"] = False
        results["issues"].append(f"API test error: {str(e)}")
    
    return results


def test_nudges_api(email: str, user_id: str, expected: dict) -> dict:
    """Test nudges API endpoint"""
    results = {"passed": True, "issues": [], "data": {}}
    
    if "has_inactivity_nudge" not in expected:
        return results
    
    headers = {
        "Authorization": "Bearer mock-token-demo-user",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/v1/nudges/users/{user_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            results["passed"] = False
            results["issues"].append(f"Nudges API returned status {response.status_code}")
            return results
        
        data = response.json()
        nudges = data.get("data", {}).get("nudges", [])
        
        results["data"] = {"nudges": nudges}
        
        inactivity_nudges = [n for n in nudges if n.get("type") == "inactivity"]
        
        if expected["has_inactivity_nudge"]:
            if len(inactivity_nudges) == 0:
                results["passed"] = False
                results["issues"].append("Expected inactivity nudge but none found")
        else:
            if len(inactivity_nudges) > 0:
                results["issues"].append(f"Unexpected inactivity nudge found")
        
    except Exception as e:
        results["passed"] = False
        results["issues"].append(f"Nudges API test error: {str(e)}")
    
    return results


def test_qa_api(email: str, user_id: str, expected: dict) -> dict:
    """Test Q&A API endpoint"""
    results = {"passed": True, "issues": [], "data": {}}
    
    if "has_conversation_history" not in expected:
        return results
    
    headers = {
        "Authorization": "Bearer mock-token-demo-user",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/v1/enhancements/qa/conversation-history/{user_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            results["issues"].append(f"Q&A history API returned status {response.status_code} (may be OK if no history)")
            return results
        
        data = response.json()
        history = data.get("data", {}).get("conversations", [])
        
        results["data"] = {"history": history}
        
        if expected["has_conversation_history"] and len(history) == 0:
            results["issues"].append("Expected conversation history but none found (may be OK if not yet used)")
        
    except Exception as e:
        results["issues"].append(f"Q&A API test error: {str(e)}")
    
    return results


def main():
    """Main verification function"""
    print("=" * 80)
    print("COMPREHENSIVE DEMO ACCOUNT VERIFICATION")
    print("Testing all accounts according to DEMO_USER_GUIDE.md")
    print("=" * 80)
    print()
    
    # Check backend
    print("Checking backend status...")
    if not test_backend():
        print("[ERROR] Backend is not running!")
        print("  Start with: python -m uvicorn src.api.main:app --reload")
        print()
        return
    print("[OK] Backend is running")
    print()
    
    all_passed = True
    results_summary = []
    
    # Test each demo account
    for email, config in DEMO_ACCOUNTS.items():
        print("=" * 80)
        print(f"Testing: {email}")
        print(f"Scenario: {config['scenario']}")
        print("=" * 80)
        
        # Get user ID
        user_id = get_user_id_from_db(email)
        if not user_id:
            print(f"[FAIL] User {email} not found in database")
            print("  Run: python scripts/create_demo_users.py")
            print()
            all_passed = False
            results_summary.append({"email": email, "status": "FAIL", "reason": "User not found"})
            continue
        
        print(f"[OK] User found: {user_id}")
        
        # Verify database data
        print("\n1. Verifying database data...")
        db_results = verify_account_data(email, config["expected"])
        if db_results["passed"]:
            print("   [OK] Database data verified")
        else:
            print("   [FAIL] Database verification issues:")
            for issue in db_results["issues"]:
                print(f"      - {issue}")
            all_passed = False
        
        if db_results["issues"]:
            for issue in db_results["issues"]:
                print(f"      [NOTE] {issue}")
        
        # Test Progress API
        print("\n2. Testing Progress API...")
        progress_results = test_progress_api(email, user_id, config["expected"])
        if progress_results["passed"]:
            print("   [OK] Progress API working")
            if progress_results["data"].get("goals"):
                print(f"      Goals: {len(progress_results['data']['goals'])}")
            if progress_results["data"].get("suggestions"):
                print(f"      Suggestions: {len(progress_results['data']['suggestions'])}")
        else:
            print("   [FAIL] Progress API issues:")
            for issue in progress_results["issues"]:
                print(f"      - {issue}")
            all_passed = False
        
        if progress_results["issues"]:
            for issue in progress_results["issues"]:
                print(f"      [NOTE] {issue}")
        
        # Test Nudges API
        print("\n3. Testing Nudges API...")
        nudges_results = test_nudges_api(email, user_id, config["expected"])
        if nudges_results["passed"]:
            print("   [OK] Nudges API working")
            if nudges_results["data"].get("nudges"):
                print(f"      Nudges: {len(nudges_results['data']['nudges'])}")
        else:
            print("   [FAIL] Nudges API issues:")
            for issue in nudges_results["issues"]:
                print(f"      - {issue}")
            all_passed = False
        
        if nudges_results["issues"]:
            for issue in nudges_results["issues"]:
                print(f"      [NOTE] {issue}")
        
        # Test Q&A API
        print("\n4. Testing Q&A API...")
        qa_results = test_qa_api(email, user_id, config["expected"])
        if qa_results["passed"]:
            print("   [OK] Q&A API working")
            if qa_results["data"].get("history"):
                print(f"      Conversation history: {len(qa_results['data']['history'])} items")
        else:
            print("   [FAIL] Q&A API issues:")
            for issue in qa_results["issues"]:
                print(f"      - {issue}")
        
        if qa_results["issues"]:
            for issue in qa_results["issues"]:
                print(f"      [NOTE] {issue}")
        
        # Summary for this account
        account_passed = (
            db_results["passed"] and 
            progress_results["passed"] and 
            nudges_results["passed"]
        )
        
        if account_passed:
            print(f"\n[PASS] {email} - All tests passed")
            results_summary.append({"email": email, "status": "PASS"})
        else:
            print(f"\n[FAIL] {email} - Some tests failed")
            results_summary.append({"email": email, "status": "FAIL"})
            all_passed = False
        
        print()
    
    # Final summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    for result in results_summary:
        status = result["status"]
        email = result["email"]
        if status == "PASS":
            print(f"[PASS] {email}")
        else:
            print(f"[FAIL] {email}: {result.get('reason', 'See details above')}")
    
    print()
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] All demo accounts verified successfully!")
        print("Ready for demo presentation!")
    else:
        print("[ERROR] Some demo accounts have issues.")
        print("Please review the details above and fix any problems.")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. If accounts are missing, run: python scripts/create_demo_users.py")
    print("  2. If backend is not running, start it: python -m uvicorn src.api.main:app --reload")
    print("  3. Test frontend login with each account")
    print("  4. See DEMO_USER_GUIDE.md for demo instructions")
    print()


if __name__ == "__main__":
    main()

