#!/usr/bin/env python3
"""
Create Demo User Accounts for Boss Presentation
Creates 5 specific demo accounts with pre-configured data for each scenario
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config.database import get_db_session
from src.models.user import User
from src.models.subject import Subject
from src.models.goal import Goal
from src.models.session import Session as SessionModel
from src.models.qa import QAInteraction
import uuid
from datetime import datetime, timedelta, timezone
import json


def get_or_create_subject(db: Session, name: str, category: str) -> Subject:
    """Get existing subject or create new one"""
    subject = db.query(Subject).filter(Subject.name == name).first()
    if not subject:
        subject = Subject(
            id=uuid.uuid4(),
            name=name,
            category=category,
            description=f"Study materials for {name}"
        )
        db.add(subject)
        db.flush()
    return subject


def create_demo_subjects(db: Session) -> dict:
    """Create all subjects needed for demo accounts"""
    subjects = {}
    
    # Core subjects
    subjects['Algebra'] = get_or_create_subject(db, "Algebra", "Math")
    subjects['Geometry'] = get_or_create_subject(db, "Geometry", "Math")
    subjects['Pre-Calculus'] = get_or_create_subject(db, "Pre-Calculus", "Math")
    subjects['Chemistry'] = get_or_create_subject(db, "Chemistry", "Science")
    subjects['Physics'] = get_or_create_subject(db, "Physics", "Science")
    subjects['Biology'] = get_or_create_subject(db, "Biology", "Science")
    subjects['SAT Math'] = get_or_create_subject(db, "SAT Math", "Test Prep")
    
    # New subjects for suggestions
    subjects['College Essays'] = get_or_create_subject(db, "College Essays", "Test Prep")
    subjects['Study Skills'] = get_or_create_subject(db, "Study Skills", "Test Prep")
    subjects['AP Prep'] = get_or_create_subject(db, "AP Prep", "Test Prep")
    subjects['AP Chemistry'] = get_or_create_subject(db, "AP Chemistry", "Test Prep")
    subjects['STEM Prep'] = get_or_create_subject(db, "STEM Prep", "Test Prep")
    
    db.commit()
    return subjects


def create_demo_goal_complete(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_goal_complete account with completed Algebra goal"""
    # Delete existing goals and sessions for this demo user
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
    # Create completed goal (2 days ago)
    completed_goal = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Algebra'].id,
        goal_type="Standard",
        title="Improve Algebra Skills",
        description="Master fundamental algebra concepts",
        status="completed",
        completion_percentage=100.00,
        completed_at=datetime.now(timezone.utc) - timedelta(days=2),
        current_streak=5,
        xp_earned=500
    )
    db.add(completed_goal)
    
    # Create 2 active goals in related subjects
    goal1 = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Geometry'].id,
        goal_type="Standard",
        title="Master Geometry",
        description="Learn geometry fundamentals",
        status="active",
        completion_percentage=45.00,
        current_streak=3,
        xp_earned=200
    )
    db.add(goal1)
    
    goal2 = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Pre-Calculus'].id,
        goal_type="Standard",
        title="Pre-Calculus Prep",
        description="Prepare for calculus",
        status="active",
        completion_percentage=30.00,
        current_streak=2,
        xp_earned=150
    )
    db.add(goal2)
    
    # Create 5+ sessions
    for i in range(5):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*5),
            duration_minutes=60,
            subject_id=subjects['Algebra'].id if i < 3 else subjects['Geometry'].id,
            transcript_text=f"Demo session {i+1} transcript",
            topics_covered=["Algebra", "Problem Solving"] if i < 3 else ["Geometry", "Shapes"]
        )
        db.add(session)


def create_demo_sat_complete(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_sat_complete account with completed SAT goal"""
    # Delete existing goals and sessions for this demo user
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
    # Create completed SAT goal (1 day ago)
    completed_goal = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['SAT Math'].id,
        goal_type="SAT",
        title="SAT Math Mastery",
        description="Achieve high score on SAT Math section",
        status="completed",
        completion_percentage=100.00,
        completed_at=datetime.now(timezone.utc) - timedelta(days=1),
        current_streak=7,
        xp_earned=750
    )
    db.add(completed_goal)
    
    # Create 5+ sessions
    for i in range(6):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*4),
            duration_minutes=90,
            subject_id=subjects['SAT Math'].id,
            transcript_text=f"SAT prep session {i+1}",
            topics_covered=["SAT Math", "Test Strategies"]
        )
        db.add(session)


def create_demo_chemistry(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_chemistry account with completed Chemistry goal"""
    # Delete existing goals and sessions for this demo user
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
    # Create completed Chemistry goal (3 days ago)
    completed_goal = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Chemistry'].id,
        goal_type="Standard",
        title="Chemistry Fundamentals",
        description="Master basic chemistry concepts",
        status="completed",
        completion_percentage=100.00,
        completed_at=datetime.now(timezone.utc) - timedelta(days=3),
        current_streak=6,
        xp_earned=600
    )
    db.add(completed_goal)
    
    # Create 5+ sessions
    for i in range(5):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*5),
            duration_minutes=60,
            subject_id=subjects['Chemistry'].id,
            transcript_text=f"Chemistry session {i+1}",
            topics_covered=["Chemistry", "Chemical Reactions"]
        )
        db.add(session)


def create_demo_low_sessions(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_low_sessions account with <3 sessions by Day 7"""
    # Delete existing goals and sessions for this demo user
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
    # Create 1 active goal
    goal = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Algebra'].id,
        goal_type="Standard",
        title="Learn Algebra Basics",
        description="Get started with algebra",
        status="active",
        completion_percentage=25.00,
        current_streak=1,
        xp_earned=50
    )
    db.add(goal)
    
    # Create only 2 sessions (below threshold of 3)
    for i in range(2):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=7-i*3),
            duration_minutes=45,
            subject_id=subjects['Algebra'].id,
            transcript_text=f"Session {i+1}",
            topics_covered=["Algebra", "Basics"]
        )
        db.add(session)


def create_demo_multi_goal(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_multi_goal account with 3+ active goals"""
    # Delete existing goals and sessions for this demo user
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
    # Goal 1: Math (75% complete)
    goal1 = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Algebra'].id,
        goal_type="Standard",
        title="Master Algebra",
        description="Advanced algebra concepts",
        status="active",
        completion_percentage=75.00,
        current_streak=8,
        xp_earned=600
    )
    db.add(goal1)
    
    # Goal 2: Science (50% complete)
    goal2 = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Chemistry'].id,
        goal_type="Standard",
        title="Chemistry Fundamentals",
        description="Learn chemistry basics",
        status="active",
        completion_percentage=50.00,
        current_streak=5,
        xp_earned=400
    )
    db.add(goal2)
    
    # Goal 3: Test Prep (20% complete)
    goal3 = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['SAT Math'].id,
        goal_type="SAT",
        title="SAT Prep",
        description="Prepare for SAT exam",
        status="active",
        completion_percentage=20.00,
        current_streak=2,
        xp_earned=150
    )
    db.add(goal3)
    
    # Create 5+ sessions across different subjects
    session_subjects = [subjects['Algebra'], subjects['Chemistry'], subjects['SAT Math']]
    for i in range(6):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*4),
            duration_minutes=60,
            subject_id=session_subjects[i % 3].id,
            transcript_text=f"Multi-goal session {i+1}",
            topics_covered=[session_subjects[i % 3].name]
        )
        db.add(session)


def create_demo_user(db: Session, email: str, name: str, created_days_ago: int) -> User:
    """Create a demo user account"""
    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"[INFO] User {email} already exists, skipping creation")
        return existing
    
    user = User(
        id=uuid.uuid4(),
        cognito_sub=f"demo-{email.split('@')[0]}",
        email=email,
        role="student",
        profile={
            "name": name,
            "grade": 11,
            "preferences": {
                "nudge_frequency_cap": 2
            }
        },
        gamification={
            "xp": 0,
            "level": 1,
            "badges": [],
            "streaks": 0
        },
        analytics={},
        disclaimer_shown=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    )
    db.add(user)
    db.flush()
    return user


def create_demo_qa(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_qa account with Q&A conversation history"""
    # Delete existing Q&A interactions for this demo user
    db.query(QAInteraction).filter(QAInteraction.student_id == user.id).delete()
    
    # Create a goal for context
    goal = Goal(
        id=uuid.uuid4(),
        student_id=user.id,
        created_by=user.id,
        subject_id=subjects['Biology'].id,
        goal_type="Standard",
        title="Learn Biology",
        description="Study biology fundamentals",
        status="active",
        completion_percentage=40.00,
        current_streak=3,
        xp_earned=200
    )
    db.add(goal)
    
    # Create Q&A interactions to show conversation history
    qa_interactions = [
        {
            "query": "What is photosynthesis?",
            "answer": "Photosynthesis is the process by which plants, algae, and some bacteria convert light energy into chemical energy stored in glucose. It occurs in two main stages: the light-dependent reactions (in the thylakoids) and the light-independent reactions or Calvin cycle (in the stroma).",
            "confidence": "High",
            "confidence_score": 0.95,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2)
        },
        {
            "query": "Can you explain the light-dependent reactions?",
            "answer": "The light-dependent reactions occur in the thylakoid membranes of chloroplasts. They capture light energy and use it to: 1) Split water molecules (photolysis), releasing oxygen as a byproduct, 2) Generate ATP through photophosphorylation, and 3) Produce NADPH by reducing NADP+. These reactions require light and produce ATP and NADPH that are used in the Calvin cycle.",
            "confidence": "High",
            "confidence_score": 0.92,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=45)
        },
        {
            "query": "What about the Calvin cycle?",
            "answer": "The Calvin cycle (light-independent reactions) occurs in the stroma of chloroplasts. It uses ATP and NADPH from the light-dependent reactions to fix carbon dioxide into organic molecules. The cycle has three main phases: 1) Carbon fixation (CO2 + RuBP), 2) Reduction (using ATP and NADPH), and 3) Regeneration of RuBP. The end product is G3P, which can be used to make glucose and other organic compounds.",
            "confidence": "High",
            "confidence_score": 0.90,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=30)
        }
    ]
    
    for qa_data in qa_interactions:
        qa = QAInteraction(
            id=uuid.uuid4(),
            student_id=user.id,
            query=qa_data["query"],
            answer=qa_data["answer"],
            confidence=qa_data["confidence"],
            confidence_score=qa_data["confidence_score"],
            context_subjects=["Biology"],
            created_at=qa_data["created_at"]
        )
        db.add(qa)
    
    # Create a few sessions for context
    for i in range(3):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*7),
            duration_minutes=45,
            subject_id=subjects['Biology'].id,
            transcript_text=f"Biology session {i+1} covering photosynthesis and cellular respiration",
            topics_covered=["Biology", "Photosynthesis"]
        )
        db.add(session)


def create_demo_tutor(db: Session) -> User:
    """Create a demo tutor user for sessions"""
    email = "demo_tutor@demo.com"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    
    tutor = User(
        id=uuid.uuid4(),
        cognito_sub="demo-tutor",
        email=email,
        role="tutor",
        profile={
            "name": "Demo Tutor",
            "specializations": ["Math", "Science", "Test Prep"]
        },
        disclaimer_shown=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=365)
    )
    db.add(tutor)
    db.flush()
    return tutor


def main():
    """Create all demo user accounts"""
    print("=" * 60)
    print("Creating Demo User Accounts for Boss Presentation")
    print("=" * 60)
    print()
    
    with get_db_session() as db:
        # Create subjects first
        print("Creating subjects...")
        subjects = create_demo_subjects(db)
        print(f"[OK] Created/found {len(subjects)} subjects")
        
        # Create demo tutor for sessions
        print("\nCreating demo tutor...")
        tutor = create_demo_tutor(db)
        print(f"[OK] Created tutor: {tutor.email}")
        
        # Create demo users
        demo_users = {
            "demo_goal_complete@demo.com": ("Goal Complete Demo", 30, create_demo_goal_complete),
            "demo_sat_complete@demo.com": ("SAT Complete Demo", 30, create_demo_sat_complete),
            "demo_chemistry@demo.com": ("Chemistry Demo", 30, create_demo_chemistry),
            "demo_low_sessions@demo.com": ("Low Sessions Demo", 7, create_demo_low_sessions),
            "demo_multi_goal@demo.com": ("Multi-Goal Demo", 30, create_demo_multi_goal),
            "demo_qa@demo.com": ("Q&A Demo", 30, create_demo_qa),
        }
        
        created_users = []
        for email, (name, days_ago, setup_func) in demo_users.items():
            print(f"\nCreating {email}...")
            user = create_demo_user(db, email, name, days_ago)
            setup_func(db, user, subjects, tutor)
            created_users.append((email, user.id))
            print(f"[OK] Created {email} with ID: {user.id}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("Demo Accounts Created Successfully!")
        print("=" * 60)
        print("\nAccount Credentials (all use password: demo123):")
        print()
        for email, user_id in created_users:
            print(f"  {email} - ID: {user_id}")
        print()
        print("Next steps:")
        print("  1. Run: python scripts/verify_demo_users.py")
        print("  2. See DEMO_USER_GUIDE.md for demo instructions")
        print()


if __name__ == "__main__":
    main()

