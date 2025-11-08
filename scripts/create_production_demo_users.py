#!/usr/bin/env python3
"""
Create Demo User Accounts in Production Cognito and Database
Creates demo accounts that can be used to test in production environment
"""

import sys
import os
import boto3
import json
from botocore.exceptions import ClientError

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


# Demo account configuration
DEMO_PASSWORD = "Demo123!"  # Must meet Cognito password requirements
DEMO_ACCOUNTS = {
    "demo_goal_complete@demo.com": {
        "name": "Goal Complete Demo",
        "days_ago": 30
    },
    "demo_sat_complete@demo.com": {
        "name": "SAT Complete Demo",
        "days_ago": 30
    },
    "demo_chemistry@demo.com": {
        "name": "Chemistry Demo",
        "days_ago": 30
    },
    "demo_low_sessions@demo.com": {
        "name": "Low Sessions Demo",
        "days_ago": 7
    },
    "demo_multi_goal@demo.com": {
        "name": "Multi-Goal Demo",
        "days_ago": 30
    },
    "demo_qa@demo.com": {
        "name": "Q&A Demo",
        "days_ago": 30
    },
    "demo_tutor@demo.com": {
        "name": "Demo Tutor",
        "days_ago": 365,
        "role": "tutor"
    }
}


def get_cognito_config():
    """Get Cognito configuration from environment or aws-deployment-vars.json"""
    # Try environment variables first
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    region = os.getenv("COGNITO_REGION", "us-east-1")
    
    # Try aws-deployment-vars.json
    if not user_pool_id:
        vars_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aws-deployment-vars.json")
        if os.path.exists(vars_file):
            try:
                with open(vars_file, 'r') as f:
                    vars_data = json.load(f)
                    user_pool_id = vars_data.get("COGNITO_USER_POOL_ID")
                    client_id = vars_data.get("COGNITO_CLIENT_ID")
                    region = vars_data.get("REGION", region)
            except json.JSONDecodeError:
                print(f"[WARNING] Could not parse {vars_file}, using environment variables only")
    
    if not user_pool_id or not client_id:
        raise ValueError(
            "Cognito configuration not found. Set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID "
            "environment variables or add them to aws-deployment-vars.json"
        )
    
    return user_pool_id, client_id, region


def create_cognito_user(cognito_client, user_pool_id, email, name, password, temporary_password=True):
    """Create a user in Cognito User Pool"""
    try:
        # Check if user already exists
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=email
            )
            print(f"  [INFO] User {email} already exists in Cognito, skipping creation")
            # Get the sub from attributes
            for attr in response.get('UserAttributes', []):
                if attr['Name'] == 'sub':
                    return attr['Value']
            return response['Username']
        except ClientError as e:
            if e.response['Error']['Code'] != 'UserNotFoundException':
                raise
        
        # Create user with temporary password first
        create_params = {
            'UserPoolId': user_pool_id,
            'Username': email,
            'UserAttributes': [
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': name}
            ],
            'TemporaryPassword': password,
            'MessageAction': 'SUPPRESS'  # Don't send welcome email
        }
        
        response = cognito_client.admin_create_user(**create_params)
        
        user_sub = None
        for attr in response['User'].get('Attributes', []):
            if attr['Name'] == 'sub':
                user_sub = attr['Value']
                break
        
        if not user_sub:
            user_sub = response['User']['Username']
        
        print(f"  [OK] Created Cognito user: {email}")
        
        # Set permanent password
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            print(f"  [OK] Set permanent password for {email}")
        except ClientError as e:
            print(f"  [WARNING] Could not set permanent password: {e}")
        
        return user_sub
        
    except ClientError as e:
        print(f"  [ERROR] Failed to create Cognito user {email}: {e}")
        raise


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
    
    subjects['Algebra'] = get_or_create_subject(db, "Algebra", "Math")
    subjects['Geometry'] = get_or_create_subject(db, "Geometry", "Math")
    subjects['Pre-Calculus'] = get_or_create_subject(db, "Pre-Calculus", "Math")
    subjects['Chemistry'] = get_or_create_subject(db, "Chemistry", "Science")
    subjects['Physics'] = get_or_create_subject(db, "Physics", "Science")
    subjects['Biology'] = get_or_create_subject(db, "Biology", "Science")
    subjects['SAT Math'] = get_or_create_subject(db, "SAT Math", "Test Prep")
    subjects['College Essays'] = get_or_create_subject(db, "College Essays", "Test Prep")
    subjects['Study Skills'] = get_or_create_subject(db, "Study Skills", "Test Prep")
    subjects['AP Prep'] = get_or_create_subject(db, "AP Prep", "Test Prep")
    subjects['AP Chemistry'] = get_or_create_subject(db, "AP Chemistry", "Test Prep")
    subjects['STEM Prep'] = get_or_create_subject(db, "STEM Prep", "Test Prep")
    
    db.commit()
    return subjects


def create_demo_user_in_db(db: Session, email: str, cognito_sub: str, name: str, role: str, created_days_ago: int) -> User:
    """Create a demo user in the database"""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"  [INFO] User {email} already exists in database, updating cognito_sub")
        existing.cognito_sub = cognito_sub
        db.flush()
        return existing
    
    user = User(
        id=uuid.uuid4(),
        cognito_sub=cognito_sub,
        email=email,
        role=role,
        profile={
            "name": name,
            "grade": 11 if role == "student" else None,
            "preferences": {
                "nudge_frequency_cap": 2
            } if role == "student" else {}
        },
        gamification={
            "xp": 0,
            "level": 1,
            "badges": [],
            "streaks": 0
        } if role == "student" else {},
        analytics={},
        disclaimer_shown=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    )
    db.add(user)
    db.flush()
    return user


def create_demo_goal_complete(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_goal_complete account with completed Algebra goal"""
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
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
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
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
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
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
    """Create demo_low_sessions account with <3 sessions"""
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
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
    db.query(Goal).filter(Goal.student_id == user.id).delete()
    db.query(SessionModel).filter(SessionModel.student_id == user.id).delete()
    
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


def create_demo_qa(db: Session, user: User, subjects: dict, tutor: User):
    """Create demo_qa account with Q&A conversation history"""
    db.query(QAInteraction).filter(QAInteraction.student_id == user.id).delete()
    
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
    
    qa_interactions = [
        {
            "query": "What is photosynthesis?",
            "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy.",
            "confidence": "High",
            "confidence_score": 0.95,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2)
        },
        {
            "query": "Can you explain the light-dependent reactions?",
            "answer": "The light-dependent reactions occur in the thylakoid membranes and capture light energy.",
            "confidence": "High",
            "confidence_score": 0.92,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=45)
        }
    ]
    
    # Check if goal_id column exists in qa_interactions table
    from sqlalchemy import inspect, text
    inspector = inspect(db.bind)
    columns = [col['name'] for col in inspector.get_columns('qa_interactions')]
    has_goal_id = 'goal_id' in columns
    
    for qa_data in qa_interactions:
        if has_goal_id:
            # Use model if column exists
            qa = QAInteraction(
                id=uuid.uuid4(),
                student_id=user.id,
                goal_id=goal.id,
                query=qa_data["query"],
                answer=qa_data["answer"],
                confidence=qa_data["confidence"],
                confidence_score=qa_data["confidence_score"],
                context_subjects=["Biology"],
                created_at=qa_data["created_at"]
            )
            db.add(qa)
        else:
            # Use raw SQL if column doesn't exist
            qa_id = uuid.uuid4()
            db.execute(text("""
                INSERT INTO qa_interactions 
                (id, student_id, query, answer, confidence, confidence_score, context_subjects, 
                 clarification_requested, out_of_scope, tutor_escalation_suggested, escalated_to_tutor_id, 
                 disclaimer_shown, created_at)
                VALUES 
                (:id, :student_id, :query, :answer, :confidence, :confidence_score, :context_subjects,
                 :clarification_requested, :out_of_scope, :tutor_escalation_suggested, :escalated_to_tutor_id,
                 :disclaimer_shown, :created_at)
            """), {
                'id': qa_id,
                'student_id': user.id,
                'query': qa_data["query"],
                'answer': qa_data["answer"],
                'confidence': qa_data["confidence"],
                'confidence_score': qa_data["confidence_score"],
                'context_subjects': ["Biology"],
                'clarification_requested': False,
                'out_of_scope': False,
                'tutor_escalation_suggested': False,
                'escalated_to_tutor_id': None,
                'disclaimer_shown': True,
                'created_at': qa_data["created_at"]
            })
    
    for i in range(3):
        session = SessionModel(
            id=uuid.uuid4(),
            student_id=user.id,
            tutor_id=tutor.id,
            session_date=datetime.now(timezone.utc) - timedelta(days=30-i*7),
            duration_minutes=45,
            subject_id=subjects['Biology'].id,
            transcript_text=f"Biology session {i+1}",
            topics_covered=["Biology", "Photosynthesis"]
        )
        db.add(session)


def main():
    """Create all demo user accounts in Cognito and database"""
    print("=" * 60)
    print("Creating Production Demo User Accounts")
    print("=" * 60)
    print()
    
    # Get Cognito configuration
    try:
        user_pool_id, client_id, region = get_cognito_config()
        print(f"Cognito User Pool ID: {user_pool_id}")
        print(f"Cognito Client ID: {client_id}")
        print(f"Region: {region}")
        print()
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    # Setup functions for each demo account
    setup_functions = {
        "demo_goal_complete@demo.com": create_demo_goal_complete,
        "demo_sat_complete@demo.com": create_demo_sat_complete,
        "demo_chemistry@demo.com": create_demo_chemistry,
        "demo_low_sessions@demo.com": create_demo_low_sessions,
        "demo_multi_goal@demo.com": create_demo_multi_goal,
        "demo_qa@demo.com": create_demo_qa,
    }
    
    with get_db_session() as db:
        # Create subjects
        print("Creating subjects...")
        subjects = create_demo_subjects(db)
        print(f"[OK] Created/found {len(subjects)} subjects")
        
        # Create tutor first
        print("\nCreating demo tutor...")
        tutor_email = "demo_tutor@demo.com"
        tutor_config = DEMO_ACCOUNTS[tutor_email]
        
        try:
            tutor_cognito_sub = create_cognito_user(
                cognito_client, user_pool_id, tutor_email,
                tutor_config["name"], DEMO_PASSWORD, temporary_password=True
            )
        except Exception as e:
            print(f"[ERROR] Failed to create tutor in Cognito: {e}")
            sys.exit(1)
        
        tutor = create_demo_user_in_db(
            db, tutor_email, tutor_cognito_sub,
            tutor_config["name"], "tutor", tutor_config["days_ago"]
        )
        print(f"[OK] Created tutor: {tutor_email}")
        
        # Create demo student accounts
        created_accounts = []
        for email, config in DEMO_ACCOUNTS.items():
            if email == tutor_email:
                continue  # Already created
            
            print(f"\nCreating {email}...")
            
            # Create in Cognito
            try:
                cognito_sub = create_cognito_user(
                    cognito_client, user_pool_id, email,
                    config["name"], DEMO_PASSWORD, temporary_password=True
                )
            except Exception as e:
                print(f"[ERROR] Failed to create {email} in Cognito: {e}")
                continue
            
            # Create in database
            user = create_demo_user_in_db(
                db, email, cognito_sub, config["name"],
                config.get("role", "student"), config["days_ago"]
            )
            
            # Setup demo data
            if email in setup_functions:
                setup_functions[email](db, user, subjects, tutor)
            
            created_accounts.append({
                "email": email,
                "user_id": str(user.id),
                "cognito_sub": cognito_sub
            })
            print(f"[OK] Created {email} with ID: {user.id}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("Demo Accounts Created Successfully!")
        print("=" * 60)
        print("\nAccount Credentials (all use password: Demo123!):")
        print()
        for account in created_accounts:
            print(f"  {account['email']}")
            print(f"    User ID: {account['user_id']}")
            print(f"    Cognito Sub: {account['cognito_sub']}")
        print()
        print("You can now test these accounts in production!")
        print()


if __name__ == "__main__":
    main()

