#!/usr/bin/env python3
"""
Demo Data Generation Script
Generates realistic test data for AI Study Companion MVP

Usage:
    python scripts/seed_demo_data.py
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# ============================================================================
# Sample Data Templates
# ============================================================================

SUBJECTS = [
    {"name": "Algebra", "category": "Math"},
    {"name": "Geometry", "category": "Math"},
    {"name": "Calculus", "category": "Math"},
    {"name": "Chemistry", "category": "Science"},
    {"name": "Physics", "category": "Science"},
    {"name": "Biology", "category": "Science"},
    {"name": "SAT Math", "category": "Test Prep"},
    {"name": "SAT English", "category": "Test Prep"},
    {"name": "AP Calculus", "category": "Test Prep"},
    {"name": "AP Chemistry", "category": "Test Prep"},
]

STUDENT_NAMES = [
    "Alex Johnson", "Sam Chen", "Jordan Martinez", "Taylor Williams",
    "Casey Brown", "Morgan Davis", "Riley Wilson", "Quinn Anderson",
    "Avery Thompson", "Cameron Lee"
]

TUTOR_NAMES = [
    "Dr. Sarah Mitchell", "Prof. James Rodriguez", "Ms. Emily Chen",
    "Dr. Michael Park", "Ms. Lisa Thompson"
]

# Sample transcripts for different scenarios
TRANSCRIPTS = {
    "normal_algebra": """
    Tutor: "Today we're working on quadratic equations. Can you solve x² + 5x + 6 = 0?"
    Student: "I think I factor it... (x + 2)(x + 3) = 0, so x = -2 or x = -3?"
    Tutor: "Perfect! You've got it. Now let's try a harder one: 2x² - 7x + 3 = 0"
    Student: "Hmm, I need to factor this... (2x - 1)(x - 3) = 0?"
    Tutor: "Excellent work! You're really getting the hang of factoring. For homework, try problems 1-10 in chapter 5."
    """,
    
    "mixed_subjects": """
    Tutor: "Let's start with factoring polynomials. Can you factor x² + 5x + 6?"
    Student: "That would be (x + 2)(x + 3)."
    Tutor: "Great! Now let's switch to chemistry. How do you balance H₂ + O₂ → H₂O?"
    Student: "2H₂ + O₂ → 2H₂O"
    Tutor: "Perfect! We'll continue with both topics next time."
    """,
    
    "short_session": """
    Tutor: "We only have 5 minutes today. Let's quickly review your homework."
    Student: "I finished problems 1-5, but I'm stuck on problem 6."
    Tutor: "Let's tackle that next time. Great work today!"
    """,
    
    "chemistry_advanced": """
    Tutor: "Today we're diving into orbital hybridization. Can you explain sp³ hybridization?"
    Student: "I think it's when one s orbital and three p orbitals combine to form four sp³ orbitals?"
    Tutor: "Exactly! And what shape does this create?"
    Student: "Tetrahedral?"
    Tutor: "Perfect! You've mastered this concept. Let's move on to sp² hybridization next time."
    """,
    
    "calculus_intro": """
    Tutor: "We're starting derivatives today. What's the derivative of x²?"
    Student: "2x?"
    Tutor: "Correct! And what about 3x³?"
    Student: "9x²?"
    Tutor: "Excellent! You're picking this up quickly. Practice the power rule for homework."
    """
}

PRACTICE_QUESTIONS = {
    "algebra": [
        {
            "question": "Factor the quadratic: x² + 7x + 12",
            "answer": "(x + 3)(x + 4)",
            "explanation": "Find two numbers that multiply to 12 and add to 7: 3 and 4.",
            "difficulty": 3
        },
        {
            "question": "Solve for x: 2x² - 8x + 6 = 0",
            "answer": "x = 1 or x = 3",
            "explanation": "Factor to get 2(x - 1)(x - 3) = 0, so x = 1 or x = 3.",
            "difficulty": 5
        },
        {
            "question": "Simplify: (x + 3)(x - 5)",
            "answer": "x² - 2x - 15",
            "explanation": "Use FOIL: x² - 5x + 3x - 15 = x² - 2x - 15",
            "difficulty": 2
        }
    ],
    "chemistry": [
        {
            "question": "Balance the equation: CH₄ + O₂ → CO₂ + H₂O",
            "answer": "CH₄ + 2O₂ → CO₂ + 2H₂O",
            "explanation": "Balance atoms: 1 C, 4 H, 4 O on each side.",
            "difficulty": 4
        },
        {
            "question": "What is the molecular formula for water?",
            "answer": "H₂O",
            "explanation": "Water consists of 2 hydrogen atoms and 1 oxygen atom.",
            "difficulty": 1
        }
    ],
    "calculus": [
        {
            "question": "Find the derivative of f(x) = 3x² + 5x - 2",
            "answer": "f'(x) = 6x + 5",
            "explanation": "Apply power rule: d/dx(3x²) = 6x, d/dx(5x) = 5, d/dx(-2) = 0",
            "difficulty": 4
        }
    ]
}

QA_QUERIES = [
    {
        "query": "I don't understand factoring quadratics",
        "expected_confidence": "Medium",
        "context": "algebra"
    },
    {
        "query": "Explain photosynthesis",
        "expected_confidence": "High",
        "context": "biology"
    },
    {
        "query": "Can you explain the Schrödinger equation in detail?",
        "expected_confidence": "Low",
        "context": "physics"
    },
    {
        "query": "What's the weather tomorrow?",
        "expected_confidence": "N/A",
        "context": "out_of_scope"
    },
    {
        "query": "I don't get this",
        "expected_confidence": "Low",
        "context": "ambiguous"
    }
]


# ============================================================================
# Data Generation Functions
# ============================================================================

def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def generate_subjects() -> List[Dict[str, Any]]:
    """Generate subject records"""
    subjects = []
    for subj in SUBJECTS:
        subjects.append({
            "id": generate_uuid(),
            "name": subj["name"],
            "category": subj["category"],
            "description": f"Study materials for {subj['name']}",
            "related_subjects": [],  # Will be populated based on relationships
            "created_at": (datetime.now() - timedelta(days=30)).isoformat()
        })
    return subjects


def generate_users(subjects: List[Dict]) -> Dict[str, List[Dict[str, Any]]]:
    """Generate users (students, tutors, parents, admins)"""
    users = {
        "students": [],
        "tutors": [],
        "parents": [],
        "admins": []
    }
    
    # Generate 10 students
    for i, name in enumerate(STUDENT_NAMES):
        first_name = name.split()[0]
        email = f"{first_name.lower()}.student@example.com"
        
        # Vary progress levels
        progress_data = []
        if i < 3:  # High progress students
            progress_data = [
                {"subject": "Algebra", "completion": 85, "streak": 7, "xp": 1200},
                {"subject": "Chemistry", "completion": 70, "streak": 5, "xp": 900}
            ]
        elif i < 7:  # Medium progress
            progress_data = [
                {"subject": "Geometry", "completion": 50, "streak": 3, "xp": 600},
                {"subject": "Biology", "completion": 40, "streak": 2, "xp": 400}
            ]
        else:  # Low progress (new students)
            progress_data = [
                {"subject": "Calculus", "completion": 20, "streak": 1, "xp": 150}
            ]
        
        users["students"].append({
            "id": generate_uuid(),
            "cognito_sub": f"cognito-sub-student-{i+1}",
            "email": email,
            "role": "student",
            "profile": {
                "goals": [],  # Will be populated separately
                "subjects": [s["name"] for s in random.sample(subjects, 2)],
                "preferences": {
                    "learning_style": random.choice(["visual", "textual", "mixed"]),
                    "nudge_frequency_cap": 1
                },
                "progress": {
                    "multi_goal_tracking": progress_data
                }
            },
            "gamification": {
                "xp": sum(p["xp"] for p in progress_data),
                "level": random.randint(1, 10),
                "badges": [],
                "streaks": max(p["streak"] for p in progress_data) if progress_data else 0,
                "meta_rewards": []
            },
            "analytics": {
                "override_count": 0,
                "confidence_distribution": {"High": "60%", "Medium": "30%", "Low": "10%"},
                "nudge_engagement": {"opened": "70%", "clicked": "50%"}
            },
            "disclaimer_shown": i < 5,  # First 5 have seen disclaimer
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        })
    
    # Generate 5 tutors
    for i, name in enumerate(TUTOR_NAMES):
        first_name = name.split()[0].replace("Dr.", "").replace("Prof.", "").replace("Ms.", "").strip()
        email = f"{first_name.lower()}.tutor@example.com"
        
        users["tutors"].append({
            "id": generate_uuid(),
            "cognito_sub": f"cognito-sub-tutor-{i+1}",
            "email": email,
            "role": "tutor",
            "profile": {
                "specializations": random.sample([s["name"] for s in subjects], 2),
                "years_experience": random.randint(3, 15)
            },
            "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
        })
    
    # Generate 1 admin
    users["admins"].append({
        "id": generate_uuid(),
        "cognito_sub": "cognito-sub-admin-1",
        "email": "admin@example.com",
        "role": "admin",
        "profile": {},
        "created_at": (datetime.now() - timedelta(days=365)).isoformat()
    })
    
    return users


def generate_goals(users: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    """Generate goals for students"""
    goals = []
    goal_types = ["SAT", "AP", "General"]
    
    for student in users["students"]:
        # Each student has 1-3 goals
        num_goals = random.randint(1, 3)
        subjects_used = []
        
        for _ in range(num_goals):
            goal_type = random.choice(goal_types)
            subject_name = random.choice(["Algebra", "Chemistry", "Calculus", "SAT Math", "AP Chemistry"])
            
            if subject_name not in subjects_used:
                subjects_used.append(subject_name)
                
                completion = random.randint(20, 95) if random.random() > 0.2 else 100
                status = "completed" if completion == 100 else "active"
                
                goals.append({
                    "id": generate_uuid(),
                    "student_id": student["id"],
                    "created_by": student["id"],  # Student created it
                    "subject_name": subject_name,
                    "goal_type": goal_type,
                    "title": f"{goal_type} {subject_name}",
                    "description": f"Master {subject_name} for {goal_type} preparation",
                    "target_completion_date": (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
                    "status": status,
                    "completion_percentage": completion,
                    "current_streak": random.randint(1, 10) if status == "active" else 0,
                    "xp_earned": completion * 10,
                    "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
                    "completed_at": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat() if status == "completed" else None
                })
    
    return goals


def generate_sessions(users: Dict[str, List[Dict]], subjects: List[Dict]) -> List[Dict[str, Any]]:
    """Generate tutoring sessions with transcripts"""
    sessions = []
    transcript_keys = list(TRANSCRIPTS.keys())
    
    for student in users["students"][:8]:  # 8 students have sessions
        # Each student has 2-5 sessions
        num_sessions = random.randint(2, 5)
        tutor = random.choice(users["tutors"])
        
        for i in range(num_sessions):
            session_date = datetime.now() - timedelta(days=random.randint(1, 30))
            transcript_key = random.choice(transcript_keys)
            transcript_text = TRANSCRIPTS[transcript_key]
            
            # Determine subject from transcript
            if "algebra" in transcript_key or "quadratic" in transcript_text.lower():
                subject_name = "Algebra"
            elif "chemistry" in transcript_key or "chemical" in transcript_text.lower():
                subject_name = "Chemistry"
            elif "calculus" in transcript_key:
                subject_name = "Calculus"
            else:
                subject_name = random.choice(["Algebra", "Chemistry", "Geometry"])
            
            subject = next((s for s in subjects if s["name"] == subject_name), subjects[0])
            
            sessions.append({
                "id": generate_uuid(),
                "student_id": student["id"],
                "tutor_id": tutor["id"],
                "session_date": session_date.isoformat(),
                "duration_minutes": random.randint(30, 90),
                "subject_id": subject["id"],
                "transcript_text": transcript_text.strip(),
                "transcript_storage_url": None,
                "transcript_available": True,
                "topics_covered": [subject_name],
                "notes": f"Session {i+1} notes",
                "created_at": session_date.isoformat()
            })
    
    return sessions


def generate_summaries(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate AI summaries for sessions"""
    summaries = []
    
    for session in sessions:
        # Generate summary based on transcript
        transcript = session["transcript_text"].lower()
        
        if "brief" in transcript or "5 minutes" in transcript:
            narrative = "Session was brief. We only had 5 minutes today. Quick review of homework progress."
            next_steps = [
                "Review last practice before next session",
                "Attempt problem 6 and note specific questions"
            ]
            summary_type = "brief"
        elif "algebra" in transcript and "chemistry" in transcript:
            narrative = "We reviewed factoring polynomials, then pivoted to balancing chemical equations. Strong understanding demonstrated in both areas."
            next_steps = [
                "Practice factoring polynomials: x² - 9, x² + 7x + 12",
                "Review balancing equations: CH₄ + O₂ → CO₂ + H₂O"
            ]
            summary_type = "normal"
        else:
            narrative = f"Great session covering {session['topics_covered'][0]}. Student showed strong grasp of concepts and completed practice problems successfully."
            next_steps = [
                f"Continue practicing {session['topics_covered'][0]} problems",
                "Review key concepts before next session"
            ]
            summary_type = "normal"
        
        summaries.append({
            "id": generate_uuid(),
            "session_id": session["id"],
            "student_id": session["student_id"],
            "tutor_id": session["tutor_id"],
            "narrative": narrative,
            "next_steps": next_steps,
            "subjects_covered": session["topics_covered"],
            "summary_type": summary_type,
            "overridden": False,
            "created_at": session["created_at"]
        })
    
    return summaries


def generate_practice_bank_items(subjects: List[Dict]) -> List[Dict[str, Any]]:
    """Generate practice bank items"""
    bank_items = []
    item_id = 1
    
    for subject in subjects:
        subject_name = subject["name"].lower()
        
        # Get questions for this subject
        questions = []
        if "algebra" in subject_name or "math" in subject_name:
            questions = PRACTICE_QUESTIONS.get("algebra", [])
        elif "chemistry" in subject_name:
            questions = PRACTICE_QUESTIONS.get("chemistry", [])
        elif "calculus" in subject_name:
            questions = PRACTICE_QUESTIONS.get("calculus", [])
        
        for q in questions:
            bank_items.append({
                "id": generate_uuid(),
                "question_text": q["question"],
                "answer_text": q["answer"],
                "explanation": q["explanation"],
                "subject_id": subject["id"],
                "difficulty_level": q["difficulty"],
                "goal_tags": ["SAT", "AP"] if "SAT" in subject["name"] or "AP" in subject["name"] else ["General"],
                "topic_tags": [subject["name"].lower()],
                "created_by": None,  # Admin created
                "version": 1,
                "is_active": True,
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            })
            item_id += 1
    
    return bank_items


def generate_qa_interactions(users: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    """Generate Q&A interactions"""
    interactions = []
    
    for student in users["students"][:6]:  # 6 students have Q&A interactions
        num_interactions = random.randint(2, 5)
        
        for _ in range(num_interactions):
            qa = random.choice(QA_QUERIES)
            
            interactions.append({
                "id": generate_uuid(),
                "student_id": student["id"],
                "query": qa["query"],
                "answer": f"Sample answer for: {qa['query']}",
                "confidence": qa["expected_confidence"],
                "confidence_score": random.uniform(0.5, 0.95) if qa["expected_confidence"] != "N/A" else None,
                "context_subjects": [qa["context"]] if qa["context"] != "out_of_scope" else [],
                "clarification_requested": qa["context"] == "ambiguous",
                "out_of_scope": qa["context"] == "out_of_scope",
                "tutor_escalation_suggested": qa["expected_confidence"] == "Low",
                "disclaimer_shown": True,
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat()
            })
    
    return interactions


def generate_nudges(users: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    """Generate nudges"""
    nudges = []
    nudge_types = ["inactivity", "cross_subject", "login"]
    
    for student in users["students"][:5]:  # 5 students receive nudges
        nudge_type = random.choice(nudge_types)
        
        if nudge_type == "inactivity":
            message = "Hi! We noticed you haven't been active recently. Regular practice is key to success!"
        elif nudge_type == "cross_subject":
            message = "Congratulations on your progress! Based on your success, you might enjoy exploring Physics or Biology."
        else:
            message = "Welcome back! Ready to continue your learning journey?"
        
        sent_at = datetime.now() - timedelta(days=random.randint(1, 7))
        opened = random.random() > 0.3  # 70% open rate
        
        nudges.append({
            "id": generate_uuid(),
            "user_id": student["id"],
            "type": nudge_type,
            "channel": random.choice(["in_app", "email", "both"]),
            "message": message,
            "personalized": True,
            "sent_at": sent_at.isoformat(),
            "opened_at": (sent_at + timedelta(hours=random.randint(1, 24))).isoformat() if opened else None,
            "clicked_at": (sent_at + timedelta(hours=random.randint(2, 48))).isoformat() if opened and random.random() > 0.3 else None,
            "trigger_reason": f"{nudge_type} trigger",
            "suggestions_made": ["Physics", "Biology"] if nudge_type == "cross_subject" else []
        })
    
    return nudges


def generate_overrides(users: Dict[str, List[Dict]], summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate tutor overrides"""
    overrides = []
    
    # 3 tutors make overrides
    for tutor in users["tutors"][:3]:
        # Each tutor makes 1-2 overrides
        num_overrides = random.randint(1, 2)
        
        for _ in range(num_overrides):
            summary = random.choice(summaries)
            
            overrides.append({
                "id": generate_uuid(),
                "tutor_id": tutor["id"],
                "student_id": summary["student_id"],
                "override_type": "summary",
                "action": "Modified next steps",
                "summary_id": summary["id"],
                "original_content": {"next_steps": summary["next_steps"]},
                "new_content": {
                    "next_steps": [
                        "Focus on chapter 5 exercises only",
                        "Skip practice problems, review theory instead"
                    ]
                },
                "reason": "AI suggestions too advanced for current level",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat()
            })
    
    return overrides


# ============================================================================
# Main Generation Function
# ============================================================================

def generate_all_demo_data() -> Dict[str, Any]:
    """Generate all demo data"""
    print("Generating demo data...")
    
    subjects = generate_subjects()
    print(f"✓ Generated {len(subjects)} subjects")
    
    users = generate_users(subjects)
    print(f"✓ Generated {len(users['students'])} students, {len(users['tutors'])} tutors, {len(users['admins'])} admins")
    
    goals = generate_goals(users)
    print(f"✓ Generated {len(goals)} goals")
    
    sessions = generate_sessions(users, subjects)
    print(f"✓ Generated {len(sessions)} sessions")
    
    summaries = generate_summaries(sessions)
    print(f"✓ Generated {len(summaries)} summaries")
    
    practice_items = generate_practice_bank_items(subjects)
    print(f"✓ Generated {len(practice_items)} practice bank items")
    
    qa_interactions = generate_qa_interactions(users)
    print(f"✓ Generated {len(qa_interactions)} Q&A interactions")
    
    nudges = generate_nudges(users)
    print(f"✓ Generated {len(nudges)} nudges")
    
    overrides = generate_overrides(users, summaries)
    print(f"✓ Generated {len(overrides)} overrides")
    
    return {
        "subjects": subjects,
        "users": users,
        "goals": goals,
        "sessions": sessions,
        "summaries": summaries,
        "practice_bank_items": practice_items,
        "qa_interactions": qa_interactions,
        "nudges": nudges,
        "overrides": overrides,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    }


def save_to_json(data: Dict[str, Any], filename: str = "demo_data.json"):
    """Save data to JSON file"""
    output_path = f"scripts/{filename}"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Saved demo data to {output_path}")


def generate_sql_inserts(data: Dict[str, Any], filename: str = "demo_data.sql"):
    """Generate SQL INSERT statements"""
    sql_lines = ["-- Demo Data SQL Inserts", "-- Generated automatically\n"]
    
    # Insert subjects
    sql_lines.append("-- Subjects")
    for subj in data["subjects"]:
        sql_lines.append(
            f"INSERT INTO subjects (id, name, category, description, created_at) VALUES "
            f"('{subj['id']}', '{subj['name']}', '{subj['category']}', '{subj['description']}', '{subj['created_at']}');"
        )
    
    # Insert users
    sql_lines.append("\n-- Users")
    for role in ["students", "tutors", "admins"]:
        for user in data["users"][role]:
            profile_json = json.dumps(user["profile"]).replace("'", "''")
            gamification_json = json.dumps(user.get("gamification", {})).replace("'", "''")
            analytics_json = json.dumps(user.get("analytics", {})).replace("'", "''")
            
            sql_lines.append(
                f"INSERT INTO users (id, cognito_sub, email, role, profile, gamification, analytics, disclaimer_shown, created_at) VALUES "
                f"('{user['id']}', '{user['cognito_sub']}', '{user['email']}', '{user['role']}', "
                f"'{profile_json}'::jsonb, '{gamification_json}'::jsonb, '{analytics_json}'::jsonb, "
                f"{user.get('disclaimer_shown', False)}, '{user['created_at']}');"
            )
    
    # Add more INSERT statements for other tables...
    # (Truncated for brevity - full version would include all tables)
    
    output_path = f"scripts/{filename}"
    with open(output_path, 'w') as f:
        f.write('\n'.join(sql_lines))
    print(f"✓ Generated SQL inserts to {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("AI Study Companion - Demo Data Generator")
    print("=" * 60)
    print()
    
    data = generate_all_demo_data()
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Subjects: {len(data['subjects'])}")
    print(f"  Students: {len(data['users']['students'])}")
    print(f"  Tutors: {len(data['users']['tutors'])}")
    print(f"  Goals: {len(data['goals'])}")
    print(f"  Sessions: {len(data['sessions'])}")
    print(f"  Summaries: {len(data['summaries'])}")
    print(f"  Practice Items: {len(data['practice_bank_items'])}")
    print(f"  Q&A Interactions: {len(data['qa_interactions'])}")
    print(f"  Nudges: {len(data['nudges'])}")
    print(f"  Overrides: {len(data['overrides'])}")
    print("=" * 60)
    
    save_to_json(data)
    generate_sql_inserts(data)
    
    print("\n✓ Demo data generation complete!")

