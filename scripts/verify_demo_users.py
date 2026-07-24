#!/usr/bin/env python3
"""
Verify Demo User Accounts
Verifies that all demo accounts are set up correctly with expected data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config.database import get_db_session
from src.models.user import User
from src.models.goal import Goal
from src.models.session import Session as SessionModel
from src.models.subject import Subject
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, Dict
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def verify_user_exists(db: Session, email: str) -> Tuple[bool, Optional[User]]:
    """Verify user exists"""
    user = db.query(User).filter(User.email == email).first()
    return (user is not None, user)


def verify_goals(db: Session, user_id, expected_completed: int = 0, expected_active: int = 0) -> bool:
    """Verify user has expected goals"""
    completed = db.query(Goal).filter(
        Goal.student_id == user_id,
        Goal.status == "completed"
    ).count()
    
    active = db.query(Goal).filter(
        Goal.student_id == user_id,
        Goal.status == "active"
    ).count()
    
    return completed >= expected_completed and active >= expected_active


def verify_sessions(db: Session, user_id, min_count: int) -> bool:
    """Verify user has minimum session count"""
    count = db.query(SessionModel).filter(
        SessionModel.student_id == user_id
    ).count()
    return count >= min_count


def verify_user_age(db: Session, user: User, expected_days: int, tolerance: int = 1) -> bool:
    """Verify user was created expected_days ago (with tolerance)"""
    # Handle both timezone-aware and naive datetimes
    now = datetime.now(timezone.utc)
    created_at = user.created_at
    if created_at.tzinfo is None:
        # If naive, assume UTC
        created_at = created_at.replace(tzinfo=timezone.utc)
    else:
        # If timezone-aware, convert to UTC
        created_at = created_at.astimezone(timezone.utc)
    
    days_ago = (now - created_at).days
    return abs(days_ago - expected_days) <= tolerance


def verify_subjects_exist(db: Session) -> bool:
    """Verify required subjects exist"""
    required = ["College Essays", "Study Skills", "AP Prep", "Physics", "Biology", "AP Chemistry", "STEM Prep"]
    for name in required:
        subject = db.query(Subject).filter(Subject.name == name).first()
        if not subject:
            print(f"  [ERROR] Subject '{name}' not found")
            return False
    return True


def test_progress_endpoint(base_url: str, user_id: str) -> Dict:
    """Test progress endpoint returns suggestions"""
    if not HAS_REQUESTS:
        return {"success": False, "error": "requests module not installed"}
    
    try:
        # Note: This would normally require auth, but for demo we'll just check if endpoint exists
        # In real scenario, you'd need to authenticate first
        response = requests.get(
            f"{base_url}/api/v1/progress/{user_id}",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {"success": True, "has_suggestions": "suggestions" in data.get("data", {})}
        else:
            return {"success": False, "status": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Verify all demo accounts"""
    print("=" * 60)
    print("Verifying Demo User Accounts")
    print("=" * 60)
    print()
    
    demo_accounts = {
        "demo_goal_complete@demo.com": {
            "expected_completed_goals": 1,
            "expected_active_goals": 2,
            "min_sessions": 5,
            "expected_age_days": 30
        },
        "demo_sat_complete@demo.com": {
            "expected_completed_goals": 1,
            "expected_active_goals": 0,
            "min_sessions": 5,
            "expected_age_days": 30
        },
        "demo_chemistry@demo.com": {
            "expected_completed_goals": 1,
            "expected_active_goals": 0,
            "min_sessions": 5,
            "expected_age_days": 30
        },
        "demo_low_sessions@demo.com": {
            "expected_completed_goals": 0,
            "expected_active_goals": 1,
            "min_sessions": 2,
            "max_sessions": 2,  # Must be exactly 2
            "expected_age_days": 7
        },
        "demo_multi_goal@demo.com": {
            "expected_completed_goals": 0,
            "expected_active_goals": 3,
            "min_sessions": 5,
            "expected_age_days": 30
        }
    }
    
    all_passed = True
    
    with get_db_session() as db:
        # Verify subjects exist
        print("Verifying subjects...")
        if verify_subjects_exist(db):
            print("[OK] All required subjects exist")
        else:
            print("[ERROR] Some required subjects are missing")
            all_passed = False
        
        print()
        
        # Verify each demo account
        for email, expectations in demo_accounts.items():
            print(f"Verifying {email}...")
            exists, user = verify_user_exists(db, email)
            
            if not exists:
                print(f"  [ERROR] User does not exist")
                all_passed = False
                continue
            
            # Verify user age
            if not verify_user_age(db, user, expectations["expected_age_days"]):
                print(f"  [ERROR] User age incorrect (expected ~{expectations['expected_age_days']} days ago)")
                all_passed = False
            else:
                print(f"  [OK] User age correct")
            
            # Verify goals
            if not verify_goals(
                db, 
                user.id, 
                expectations["expected_completed_goals"],
                expectations["expected_active_goals"]
            ):
                print(f"  [ERROR] Goals incorrect (expected {expectations['expected_completed_goals']} completed, {expectations['expected_active_goals']} active)")
                all_passed = False
            else:
                print(f"  [OK] Goals correct")
            
            # Verify sessions
            min_sessions = expectations["min_sessions"]
            max_sessions = expectations.get("max_sessions")
            
            if max_sessions:
                # Must be exactly this number
                session_count = db.query(SessionModel).filter(SessionModel.student_id == user.id).count()
                if session_count != max_sessions:
                    print(f"  [ERROR] Session count incorrect (expected exactly {max_sessions}, got {session_count})")
                    all_passed = False
                else:
                    print(f"  [OK] Session count correct ({session_count})")
            else:
                if not verify_sessions(db, user.id, min_sessions):
                    print(f"  [ERROR] Session count too low (expected at least {min_sessions})")
                    all_passed = False
                else:
                    session_count = db.query(SessionModel).filter(SessionModel.student_id == user.id).count()
                    print(f"  [OK] Session count correct ({session_count})")
            
            print()
        
        # Summary
        print("=" * 60)
        if all_passed:
            print("[SUCCESS] All demo accounts verified successfully!")
        else:
            print("[ERROR] Some verifications failed. Please review above.")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Test API endpoints with demo accounts")
        print("  2. See DEMO_USER_GUIDE.md for demo instructions")
        print()


if __name__ == "__main__":
    main()

