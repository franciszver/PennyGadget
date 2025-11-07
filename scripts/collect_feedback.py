#!/usr/bin/env python3
"""
Feedback Collection Script
Collects and analyzes user feedback from beta testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.user import User
from src.models.practice import PracticeAssignment
from src.models.qa import QAInteraction
from src.models.session import Session as SessionModel
from datetime import datetime, timedelta
import json


def analyze_user_engagement(db: Session, days: int = 7):
    """Analyze user engagement metrics"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get active users
    active_students = db.query(User).filter(
        User.role == "student"
    ).all()
    
    engagement_data = {
        "total_students": len(active_students),
        "active_students": 0,
        "sessions_completed": 0,
        "practice_completed": 0,
        "qa_queries": 0,
        "engagement_rate": 0.0
    }
    
    for student in active_students:
        # Check recent activity
        recent_sessions = db.query(SessionModel).filter(
            SessionModel.student_id == student.id,
            SessionModel.session_date >= cutoff_date
        ).count()
        
        recent_practice = db.query(PracticeAssignment).filter(
            PracticeAssignment.student_id == student.id,
            PracticeAssignment.completed_at >= cutoff_date
        ).count()
        
        recent_qa = db.query(QAInteraction).filter(
            QAInteraction.student_id == student.id,
            QAInteraction.created_at >= cutoff_date
        ).count()
        
        if recent_sessions > 0 or recent_practice > 0 or recent_qa > 0:
            engagement_data["active_students"] += 1
        
        engagement_data["sessions_completed"] += recent_sessions
        engagement_data["practice_completed"] += recent_practice
        engagement_data["qa_queries"] += recent_qa
    
    if engagement_data["total_students"] > 0:
        engagement_data["engagement_rate"] = (
            engagement_data["active_students"] / engagement_data["total_students"]
        ) * 100
    
    return engagement_data


def generate_feedback_report(db: Session):
    """Generate comprehensive feedback report"""
    print("[REPORT] Generating Feedback Report...\n")
    
    # Engagement metrics
    engagement_7d = analyze_user_engagement(db, days=7)
    engagement_30d = analyze_user_engagement(db, days=30)
    
    report = {
        "engagement_metrics": {
            "last_7_days": engagement_7d,
            "last_30_days": engagement_30d
        },
        "feature_usage": {
            "sessions": engagement_7d["sessions_completed"],
            "practice": engagement_7d["practice_completed"],
            "qa": engagement_7d["qa_queries"]
        },
        "recommendations": []
    }
    
    # Generate recommendations
    if engagement_7d["engagement_rate"] < 50:
        report["recommendations"].append("Low engagement - consider improving onboarding or feature discoverability")
    
    if engagement_7d["practice_completed"] == 0:
        report["recommendations"].append("No practice completion - check practice assignment flow")
    
    if engagement_7d["qa_queries"] == 0:
        report["recommendations"].append("No Q&A usage - check Q&A interface accessibility")
    
    print(json.dumps(report, indent=2))
    return report


def main():
    """Main function"""
    db = next(get_db())
    
    try:
        generate_feedback_report(db)
    except Exception as e:
        print(f"[ERROR] Error generating report: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

