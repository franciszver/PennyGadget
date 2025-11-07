"""
Badge System
Badge definitions and award logic
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.user import User
from src.models.goal import Goal
from src.models.practice import PracticeAssignment
from src.models.qa import QAInteraction
from src.models.session import Session as SessionModel

logger = logging.getLogger(__name__)


class BadgeSystem:
    """Badge system for awarding achievements"""
    
    # Badge definitions
    BADGES = {
        # Level badges
        "level_5": {"name": "Rising Star", "description": "Reached Level 5", "category": "level"},
        "level_10": {"name": "Scholar", "description": "Reached Level 10", "category": "level"},
        "level_20": {"name": "Expert", "description": "Reached Level 20", "category": "level"},
        "level_50": {"name": "Master", "description": "Reached Level 50", "category": "level"},
        
        # Practice badges
        "practice_10": {"name": "Practice Makes Perfect", "description": "Completed 10 practice items", "category": "practice"},
        "practice_50": {"name": "Dedicated Learner", "description": "Completed 50 practice items", "category": "practice"},
        "practice_100": {"name": "Practice Champion", "description": "Completed 100 practice items", "category": "practice"},
        "practice_perfect_10": {"name": "Perfect Score", "description": "Got 10 perfect practice scores", "category": "practice"},
        
        # Goal badges
        "goal_first": {"name": "Goal Setter", "description": "Created your first goal", "category": "goal"},
        "goal_completed_5": {"name": "Goal Achiever", "description": "Completed 5 goals", "category": "goal"},
        "goal_completed_10": {"name": "Goal Master", "description": "Completed 10 goals", "category": "goal"},
        
        # Streak badges
        "streak_7": {"name": "Week Warrior", "description": "7-day streak", "category": "streak"},
        "streak_30": {"name": "Month Master", "description": "30-day streak", "category": "streak"},
        "streak_100": {"name": "Century Streak", "description": "100-day streak", "category": "streak"},
        
        # Session badges
        "session_10": {"name": "Regular Student", "description": "Completed 10 sessions", "category": "session"},
        "session_50": {"name": "Dedicated Student", "description": "Completed 50 sessions", "category": "session"},
        
        # Q&A badges
        "qa_10": {"name": "Curious Mind", "description": "Asked 10 questions", "category": "qa"},
        "qa_50": {"name": "Inquisitive Scholar", "description": "Asked 50 questions", "category": "qa"},
        "qa_helpful_10": {"name": "Helpful Answers", "description": "Found 10 answers helpful", "category": "qa"},
        
        # Exploration badges
        "subject_3": {"name": "Explorer", "description": "Studied 3 different subjects", "category": "exploration"},
        "subject_5": {"name": "Renaissance Learner", "description": "Studied 5 different subjects", "category": "exploration"},
        
        # Collaboration badges
        "tutor_message_10": {"name": "Team Player", "description": "Exchanged 10 messages with tutor", "category": "collaboration"},
        "tutor_engagement": {"name": "Engaged Learner", "description": "Active tutor engagement", "category": "collaboration"},
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_badge_info(self, badge_id: str) -> Optional[Dict]:
        """Get badge information by ID"""
        return self.BADGES.get(badge_id)
    
    def get_all_badges(self) -> Dict:
        """Get all badge definitions"""
        return self.BADGES
    
    def get_user_badges(self, user_id: str) -> List[Dict]:
        """Get all badges earned by a user"""
        # Handle both UUID and string IDs
        try:
            from uuid import UUID as UUIDType
            user_uuid = UUIDType(user_id) if isinstance(user_id, str) else user_id
            user = self.db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, TypeError):
            # Try as string (for test models)
            user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        gamification = user.gamification or {}
        badge_ids = gamification.get("badges", [])
        
        badges = []
        for badge_id in badge_ids:
            badge_info = self.get_badge_info(badge_id)
            if badge_info:
                badges.append({
                    "id": badge_id,
                    **badge_info
                })
        
        return badges
    
    def award_badge(self, user_id: str, badge_id: str) -> bool:
        """
        Award a badge to a user
        
        Returns:
            True if badge was newly awarded, False if already had it
        """
        if badge_id not in self.BADGES:
            logger.warning(f"Unknown badge ID: {badge_id}")
            return False
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        gamification = user.gamification or {}
        badges = gamification.get("badges", [])
        
        if badge_id in badges:
            return False  # Already has badge
        
        badges.append(badge_id)
        gamification["badges"] = badges
        user.gamification = gamification
        self.db.commit()
        
        logger.info(f"Awarded badge {badge_id} to user {user_id}")
        return True
    
    def check_level_badges(self, user_id: str, level: int) -> List[str]:
        """Check and award level-based badges"""
        badges_awarded = []
        
        if level >= 5 and not self.has_badge(user_id, "level_5"):
            if self.award_badge(user_id, "level_5"):
                badges_awarded.append("level_5")
        
        if level >= 10 and not self.has_badge(user_id, "level_10"):
            if self.award_badge(user_id, "level_10"):
                badges_awarded.append("level_10")
        
        if level >= 20 and not self.has_badge(user_id, "level_20"):
            if self.award_badge(user_id, "level_20"):
                badges_awarded.append("level_20")
        
        if level >= 50 and not self.has_badge(user_id, "level_50"):
            if self.award_badge(user_id, "level_50"):
                badges_awarded.append("level_50")
        
        return badges_awarded
    
    def check_action_badges(self, user_id: str, action: str, metadata: Dict) -> List[str]:
        """Check and award action-based badges"""
        badges_awarded = []
        
        if action == "practice_completed":
            # Check practice count badges
            # Handle both UUID and string IDs for practice count
            try:
                from uuid import UUID as UUIDType
                student_uuid = UUIDType(user_id) if isinstance(user_id, str) else user_id
                practice_count = self.db.query(func.count(PracticeAssignment.id)).filter(
                    PracticeAssignment.student_id == student_uuid,
                    PracticeAssignment.completed == True
                ).scalar() or 0
            except (ValueError, TypeError):
                practice_count = self.db.query(func.count(PracticeAssignment.id)).filter(
                    PracticeAssignment.student_id == user_id,
                    PracticeAssignment.completed == True
                ).scalar() or 0
            
            if practice_count >= 10 and not self.has_badge(user_id, "practice_10"):
                if self.award_badge(user_id, "practice_10"):
                    badges_awarded.append("practice_10")
            
            if practice_count >= 50 and not self.has_badge(user_id, "practice_50"):
                if self.award_badge(user_id, "practice_50"):
                    badges_awarded.append("practice_50")
            
            if practice_count >= 100 and not self.has_badge(user_id, "practice_100"):
                if self.award_badge(user_id, "practice_100"):
                    badges_awarded.append("practice_100")
            
            # Check perfect score badge
            if metadata.get("perfect_score"):
                perfect_count = self.db.query(func.count(PracticeAssignment.id)).filter(
                    PracticeAssignment.student_id == user_id,
                    PracticeAssignment.completed == True,
                    PracticeAssignment.performance_score == 1.0
                ).scalar() or 0
                
                if perfect_count >= 10 and not self.has_badge(user_id, "practice_perfect_10"):
                    if self.award_badge(user_id, "practice_perfect_10"):
                        badges_awarded.append("practice_perfect_10")
        
        elif action == "goal_created":
            # Check first goal badge
            goal_count = self.db.query(func.count(Goal.id)).filter(
                Goal.student_id == user_id
            ).scalar() or 0
            
            if goal_count == 1 and not self.has_badge(user_id, "goal_first"):
                if self.award_badge(user_id, "goal_first"):
                    badges_awarded.append("goal_first")
        
        elif action == "goal_completed":
            # Check goal completion badges
            completed_count = self.db.query(func.count(Goal.id)).filter(
                Goal.student_id == user_id,
                Goal.status == "completed"
            ).scalar() or 0
            
            if completed_count >= 5 and not self.has_badge(user_id, "goal_completed_5"):
                if self.award_badge(user_id, "goal_completed_5"):
                    badges_awarded.append("goal_completed_5")
            
            if completed_count >= 10 and not self.has_badge(user_id, "goal_completed_10"):
                if self.award_badge(user_id, "goal_completed_10"):
                    badges_awarded.append("goal_completed_10")
        
        elif action == "qa_query":
            # Check Q&A badges
            qa_count = self.db.query(func.count(QAInteraction.id)).filter(
                QAInteraction.student_id == user_id
            ).scalar() or 0
            
            if qa_count >= 10 and not self.has_badge(user_id, "qa_10"):
                if self.award_badge(user_id, "qa_10"):
                    badges_awarded.append("qa_10")
            
            if qa_count >= 50 and not self.has_badge(user_id, "qa_50"):
                if self.award_badge(user_id, "qa_50"):
                    badges_awarded.append("qa_50")
        
        elif action == "session_completed":
            # Check session badges
            session_count = self.db.query(func.count(SessionModel.id)).filter(
                SessionModel.student_id == user_id
            ).scalar() or 0
            
            if session_count >= 10 and not self.has_badge(user_id, "session_10"):
                if self.award_badge(user_id, "session_10"):
                    badges_awarded.append("session_10")
            
            if session_count >= 50 and not self.has_badge(user_id, "session_50"):
                if self.award_badge(user_id, "session_50"):
                    badges_awarded.append("session_50")
        
        return badges_awarded
    
    def has_badge(self, user_id: str, badge_id: str) -> bool:
        """Check if user has a specific badge"""
        # Handle both UUID and string IDs
        try:
            from uuid import UUID as UUIDType
            user_uuid = UUIDType(user_id) if isinstance(user_id, str) else user_id
            user = self.db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, TypeError):
            # Try as string (for test models)
            user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        gamification = user.gamification or {}
        badges = gamification.get("badges", [])
        return badge_id in badges

