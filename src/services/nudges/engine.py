"""
Nudge Engine
Determines when and what nudges to send
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, and_

from src.models.user import User
from src.models.session import Session as SessionModel
from src.models.goal import Goal
from src.models.nudge import Nudge
from src.services.nudges.personalization import NudgePersonalization
from src.config.settings import settings


class NudgeEngine:
    """Service for determining and sending nudges"""
    
    def __init__(self, db: DBSession):
        self.db = db
        self.personalization = NudgePersonalization(db)
    
    def should_send_nudge(
        self,
        user_id: str,
        check_type: str  # "inactivity", "goal_completion", "login"
    ) -> Dict[str, any]:
        """
        Check if a nudge should be sent
        
        Returns:
            dict with 'should_send' (bool) and 'nudge' data if True
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"should_send": False, "reason": "user_not_found"}
        
        # Check frequency cap
        today = datetime.utcnow().date()
        nudge_count_today = self.db.query(Nudge).filter(
            Nudge.user_id == user_id,
            func.date(Nudge.sent_at) == today
        ).count()
        
        nudge_cap = user.profile.get("preferences", {}).get("nudge_frequency_cap", settings.default_nudge_frequency_cap)
        
        if nudge_count_today >= nudge_cap:
            return {
                "should_send": False,
                "reason": "frequency_cap_reached",
                "next_available": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
            }
        
        # Check based on type
        if check_type == "inactivity":
            return self._check_inactivity_nudge(user_id, user)
        elif check_type == "goal_completion":
            return self._check_goal_completion_nudge(user_id, user)
        elif check_type == "login":
            return self._check_login_nudge(user_id, user)
        else:
            return {"should_send": False, "reason": "unknown_check_type"}
    
    def _check_inactivity_nudge(self, user_id: str, user: User) -> Dict:
        """Check if inactivity nudge should be sent"""
        # Check days since signup
        days_since_signup = (datetime.utcnow() - user.created_at).days
        
        # Count sessions
        session_count = self.db.query(SessionModel).filter(
            SessionModel.student_id == user_id
        ).count()
        
        # Check if threshold met
        if days_since_signup >= settings.nudge_inactivity_threshold_days and \
           session_count < settings.nudge_min_sessions_threshold:
            
            # Get personalized message and suggestions
            insights = self.personalization.get_student_insights(user_id)
            base_message = f"Hi! We noticed you've only completed {session_count} session(s) so far. Regular practice is key to success!"
            message = self.personalization.personalize_nudge_message(
                base_message=base_message,
                nudge_type="inactivity",
                student_id=user_id,
                insights=insights
            )
            
            suggestions = self.personalization.get_personalized_suggestions(
                student_id=user_id,
                nudge_type="inactivity",
                insights=insights
            )
            
            # Ensure "book next session" is always included
            book_session_suggestion = "Schedule your next tutoring session"
            if not suggestions:
                suggestions = [book_session_suggestion, "Try some practice problems", "Set up study goals"]
            elif book_session_suggestion not in suggestions:
                # Add it as the first suggestion
                suggestions = [book_session_suggestion] + suggestions
            
            message += "\n\nWould you like to:\n" + "\n".join(f"- {s}" for s in suggestions[:3])
            
            return {
                "should_send": True,
                "nudge": {
                    "type": "inactivity",
                    "channel": "both",
                    "message": message,
                    "personalized": True,
                    "suggestions": suggestions,
                    "trigger_reason": f"Low session count ({session_count} sessions by day {days_since_signup})"
                }
            }
        
        return {"should_send": False, "reason": "threshold_not_met"}
    
    def _check_goal_completion_nudge(self, user_id: str, user: User) -> Dict:
        """Check if goal completion nudge should be sent"""
        # Find recently completed goals
        completed_goals = self.db.query(Goal).filter(
            Goal.student_id == user_id,
            Goal.status == "completed",
            Goal.completed_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        if completed_goals:
            # Get personalized message and suggestions
            insights = self.personalization.get_student_insights(user_id)
            base_message = "Congratulations on completing your goal! 🎉"
            message = self.personalization.personalize_nudge_message(
                base_message=base_message,
                nudge_type="goal_completion",
                student_id=user_id,
                insights=insights
            )
            
            suggestions = self.personalization.get_personalized_suggestions(
                student_id=user_id,
                nudge_type="cross_subject",
                insights=insights
            )
            
            # Add subject suggestions based on preferred subjects
            preferred_subjects = insights.get("preferred_subjects", [])
            if preferred_subjects and len(preferred_subjects) > 1:
                subject_suggestions = [s["name"] for s in preferred_subjects[1:3]]  # Skip first (already doing it)
                suggestions = subject_suggestions + suggestions
            
            if suggestions:
                message += "\n\nBased on your success, you might also enjoy:\n" + "\n".join(f"- {s}" for s in suggestions[:3])
            
            return {
                "should_send": True,
                "nudge": {
                    "type": "cross_subject",
                    "channel": "in_app",
                    "message": message,
                    "personalized": True,
                    "suggestions": suggestions[:3],
                    "trigger_reason": "Goal completion"
                }
            }
        
        return {"should_send": False, "reason": "no_completed_goals"}
    
    def _check_login_nudge(self, user_id: str, user: User) -> Dict:
        """Check if login nudge should be sent"""
        # Get personalized message
        insights = self.personalization.get_student_insights(user_id)
        base_message = "Welcome back! Ready to continue your learning journey?"
        message = self.personalization.personalize_nudge_message(
            base_message=base_message,
            nudge_type="login",
            student_id=user_id,
            insights=insights
        )
        
        # Add personalized suggestions
        suggestions = self.personalization.get_personalized_suggestions(
            student_id=user_id,
            nudge_type="login",
            insights=insights
        )
        
        if suggestions:
            message += "\n\n" + "\n".join(f"- {s}" for s in suggestions[:2])
        
        return {
            "should_send": True,
            "nudge": {
                "type": "login",
                "channel": "in_app",
                "message": message,
                "personalized": True,
                "suggestions": suggestions,
                "trigger_reason": "User login"
            }
        }

