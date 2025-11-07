#!/usr/bin/env python3
"""
Beta Testing Setup Script
Creates test users, data, and configurations for beta testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.user import User
from src.models.subject import Subject
from src.models.goal import Goal
from src.models.session import Session as SessionModel
import uuid
from datetime import datetime, timedelta
import json


def create_beta_users(db: Session):
    """Create test users for beta testing"""
    users = []
    
    # Check if beta users already exist
    existing_beta = db.query(User).filter(
        User.cognito_sub.like("beta-%")
    ).all()
    
    if existing_beta:
        print(f"[INFO] Found {len(existing_beta)} existing beta users, skipping creation")
        return existing_beta
    
    # Create students
    for i in range(20):
        user = User(
            id=uuid.uuid4(),
            cognito_sub=f"beta-student-{i}",
            email=f"student{i}@betatest.com",
            role="student",
            profile={
                "name": f"Student {i+1}",
                "grade": 9 + (i % 4),  # Grades 9-12
                "preferences": {
                    "nudge_frequency_cap": 2
                }
            },
            disclaimer_shown=True
        )
        db.add(user)
        users.append(user)
    
    # Create tutors
    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            cognito_sub=f"beta-tutor-{i}",
            email=f"tutor{i}@betatest.com",
            role="tutor",
            profile={
                "name": f"Tutor {i+1}",
                "subjects": ["Math", "Science", "English"][:i+1]
            }
        )
        db.add(user)
        users.append(user)
    
    # Create parents
    for i in range(10):
        user = User(
            id=uuid.uuid4(),
            cognito_sub=f"beta-parent-{i}",
            email=f"parent{i}@betatest.com",
            role="parent",
            profile={
                "name": f"Parent {i+1}"
            }
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    print(f"[OK] Created {len(users)} beta test users")
    return users


def create_beta_data(db: Session, users: list):
    """Create test data for beta testing"""
    students = [u for u in users if u.role == "student"]
    tutors = [u for u in users if u.role == "tutor"]
    
    # Get or create subjects
    subjects = db.query(Subject).all()
    if not subjects:
        subjects = [
            Subject(id=uuid.uuid4(), name="Math", category="STEM"),
            Subject(id=uuid.uuid4(), name="Science", category="STEM"),
            Subject(id=uuid.uuid4(), name="English", category="Language Arts"),
        ]
        for s in subjects:
            db.add(s)
        db.commit()
    
    # Create goals for students
    goal_types = ["SAT", "AP", "Standard"]
    for student in students[:15]:  # 15 students with goals
        goal = Goal(
            id=uuid.uuid4(),
            student_id=student.id,
            created_by=student.id,  # Student creates their own goal
            title=f"Improve {subjects[0].name}",
            goal_type=goal_types[student.id.int % len(goal_types)],
            target_completion_date=(datetime.utcnow() + timedelta(days=30)).date(),
            status="active"
        )
        db.add(goal)
    
    # Create sessions for students
    for student in students[:10]:  # 10 students with sessions
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=student.id,
            tutor_id=tutors[0].id if tutors else None,
            session_date=datetime.utcnow() - timedelta(days=7 - (student.id.int % 7)),
            duration_minutes=60,
            transcript_text="This is a test transcript for beta testing.",
            topics_covered=["Algebra", "Geometry"]
        )
        db.add(session)
    
    db.commit()
    print("[OK] Created beta test data (goals, sessions)")


def generate_beta_report(db: Session):
    """Generate beta testing setup report"""
    student_count = db.query(User).filter(User.role == "student").count()
    tutor_count = db.query(User).filter(User.role == "tutor").count()
    parent_count = db.query(User).filter(User.role == "parent").count()
    goal_count = db.query(Goal).count()
    session_count = db.query(SessionModel).count()
    
    report = {
        "beta_setup": {
            "students": student_count,
            "tutors": tutor_count,
            "parents": parent_count,
            "goals": goal_count,
            "sessions": session_count
        },
        "ready_for_testing": True
    }
    
    print("\n[REPORT] Beta Testing Setup Report:")
    print(json.dumps(report, indent=2))
    
    return report


def main():
    """Main setup function"""
    print("[SETUP] Setting up Beta Testing Environment...\n")
    
    db = next(get_db())
    
    try:
        # Create users
        users = create_beta_users(db)
        
        # Create test data
        create_beta_data(db, users)
        
        # Generate report
        generate_beta_report(db)
        
        print("\n[OK] Beta testing environment ready!")
        print("\nNext steps:")
        print("1. Share credentials with beta testers")
        print("2. Set up feedback collection")
        print("3. Monitor analytics")
        print("4. Collect user feedback")
        
    except Exception as e:
        print(f"[ERROR] Error setting up beta testing: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

