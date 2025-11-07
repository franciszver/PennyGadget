"""
Gamification Engine
Core logic for XP, levels, streaks, and rewards
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.goal import Goal
from src.services.gamification.badges import BadgeSystem

logger = logging.getLogger(__name__)


class GamificationEngine:
    """Core gamification engine for XP, levels, streaks, and rewards"""
    
    # XP values for different actions
    XP_VALUES = {
        "practice_completed": 10,
        "practice_perfect": 25,  # Bonus for 100% correct
        "session_completed": 50,
        "goal_created": 20,
        "goal_milestone": 100,  # 25%, 50%, 75% completion
        "goal_completed": 200,
        "qa_query": 5,
        "qa_helpful": 15,  # When student marks answer as helpful
        "streak_day": 10,  # Daily streak bonus
        "streak_week": 50,  # Weekly streak milestone
        "streak_month": 200,  # Monthly streak milestone
        "cross_subject_exploration": 30,  # Trying new subjects
        "tutor_engagement": 25,  # Responding to tutor messages
    }
    
    # Level progression (XP required per level)
    # Level 1: 0-99, Level 2: 100-249, Level 3: 250-499, etc.
    BASE_XP_PER_LEVEL = 100
    LEVEL_MULTIPLIER = 1.5  # Each level requires 1.5x more XP than previous
    
    def __init__(self, db: Session):
        self.db = db
        self.badge_system = BadgeSystem(db)
    
    def get_user_gamification(self, user_id: str) -> Dict:
        """Get current gamification state for a user"""
        # Handle both UUID and string IDs
        try:
            from uuid import UUID as UUIDType
            user_uuid = UUIDType(user_id) if isinstance(user_id, str) else user_id
            user = self.db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, TypeError):
            # Try as string (for test models)
            user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        gamification = user.gamification or {}
        
        # Ensure all fields exist
        return {
            "xp": gamification.get("xp", 0),
            "level": gamification.get("level", 1),
            "badges": gamification.get("badges", []),
            "streaks": gamification.get("streaks", {}),
            "meta_rewards": gamification.get("meta_rewards", []),
            "total_xp_earned": gamification.get("total_xp_earned", 0),
            "last_activity": gamification.get("last_activity"),
        }
    
    def calculate_level(self, total_xp: int) -> int:
        """Calculate user level based on total XP"""
        if total_xp < self.BASE_XP_PER_LEVEL:
            return 1
        
        level = 1
        xp_required = self.BASE_XP_PER_LEVEL
        xp_accumulated = 0
        
        while xp_accumulated + xp_required <= total_xp:
            xp_accumulated += xp_required
            level += 1
            xp_required = int(xp_required * self.LEVEL_MULTIPLIER)
        
        return level
    
    def get_xp_for_next_level(self, current_level: int) -> Dict:
        """Get XP required for next level"""
        xp_required = self.BASE_XP_PER_LEVEL
        total_xp_for_level = 0
        
        for level in range(1, current_level + 1):
            total_xp_for_level += xp_required
            xp_required = int(xp_required * self.LEVEL_MULTIPLIER)
        
        next_level_xp = total_xp_for_level + xp_required
        return {
            "current_level": current_level,
            "next_level": current_level + 1,
            "xp_for_next_level": xp_required,
            "total_xp_for_next_level": next_level_xp,
        }
    
    def award_xp(
        self,
        user_id: str,
        action: str,
        amount: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Award XP to a user for an action
        
        Args:
            user_id: User ID
            action: Action type (e.g., "practice_completed")
            amount: Optional custom XP amount (uses default if not provided)
            metadata: Optional metadata about the action
        
        Returns:
            Dict with updated gamification state
        """
        # Handle both UUID and string IDs
        try:
            from uuid import UUID as UUIDType
            user_uuid = UUIDType(user_id) if isinstance(user_id, str) else user_id
            user = self.db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, TypeError):
            # Try as string (for test models)
            user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get XP amount
        xp_amount = amount or self.XP_VALUES.get(action, 0)
        if xp_amount == 0:
            logger.warning(f"No XP value defined for action: {action}")
            return self.get_user_gamification(user_id)
        
        # Get current gamification state
        gamification = user.gamification or {}
        current_xp = gamification.get("xp", 0)
        total_xp_earned = gamification.get("total_xp_earned", 0)
        current_level = gamification.get("level", 1)
        
        # Award XP
        new_xp = current_xp + xp_amount
        new_total_xp = total_xp_earned + xp_amount
        
        # Calculate new level
        new_level = self.calculate_level(new_total_xp)
        level_up = new_level > current_level
        
        # Update gamification
        gamification["xp"] = new_xp
        gamification["total_xp_earned"] = new_total_xp
        gamification["level"] = new_level
        gamification["last_activity"] = datetime.utcnow().isoformat()
        
        # Update user
        user.gamification = gamification
        self.db.commit()
        
        # Check for badge awards
        badges_awarded = []
        if level_up:
            badges_awarded.extend(self.badge_system.check_level_badges(user_id, new_level))
        
        # Check for action-based badges
        action_badges = self.badge_system.check_action_badges(user_id, action, metadata or {})
        badges_awarded.extend(action_badges)
        
        # Update badges if any were awarded
        if badges_awarded:
            current_badges = gamification.get("badges", [])
            for badge in badges_awarded:
                if badge not in current_badges:
                    current_badges.append(badge)
            gamification["badges"] = current_badges
            user.gamification = gamification
            self.db.commit()
        
        logger.info(
            f"Awarded {xp_amount} XP to user {user_id} for {action}. "
            f"Level: {current_level} -> {new_level}"
        )
        
        return {
            "xp_awarded": xp_amount,
            "total_xp": new_xp,
            "total_xp_earned": new_total_xp,
            "level": new_level,
            "level_up": level_up,
            "badges_awarded": badges_awarded,
            "next_level_info": self.get_xp_for_next_level(new_level) if level_up else None,
        }
    
    def update_streak(self, user_id: str, activity_type: str = "daily") -> Dict:
        """
        Update user streak based on activity
        
        Args:
            user_id: User ID
            activity_type: Type of activity (daily, weekly, etc.)
        
        Returns:
            Dict with streak information
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        gamification = user.gamification or {}
        streaks = gamification.get("streaks", {})
        
        today = datetime.utcnow().date()
        last_activity_date = None
        
        if "last_activity_date" in streaks:
            try:
                last_activity_date = datetime.fromisoformat(streaks["last_activity_date"]).date()
            except (ValueError, TypeError):
                last_activity_date = None
        
        current_streak = streaks.get("current_streak", 0)
        longest_streak = streaks.get("longest_streak", 0)
        
        # Check if streak should continue or reset
        if last_activity_date:
            days_since = (today - last_activity_date).days
            
            if days_since == 0:
                # Already active today, no change
                pass
            elif days_since == 1:
                # Consecutive day, increment streak
                current_streak += 1
            else:
                # Streak broken, reset
                current_streak = 1
        else:
            # First activity, start streak
            current_streak = 1
        
        # Update longest streak
        if current_streak > longest_streak:
            longest_streak = current_streak
        
        # Award streak bonuses
        streak_bonus_xp = 0
        if current_streak % 7 == 0:  # Weekly milestone
            streak_bonus_xp = self.XP_VALUES["streak_week"]
        elif current_streak % 30 == 0:  # Monthly milestone
            streak_bonus_xp = self.XP_VALUES["streak_month"]
        elif current_streak > 1:
            streak_bonus_xp = self.XP_VALUES["streak_day"]
        
        # Update streaks
        streaks["current_streak"] = current_streak
        streaks["longest_streak"] = longest_streak
        streaks["last_activity_date"] = today.isoformat()
        streaks["last_updated"] = datetime.utcnow().isoformat()
        
        gamification["streaks"] = streaks
        user.gamification = gamification
        
        # Award streak bonus XP if applicable
        if streak_bonus_xp > 0:
            self.award_xp(user_id, "streak_day", amount=streak_bonus_xp)
        else:
            self.db.commit()
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "streak_bonus_xp": streak_bonus_xp,
        }
    
    def get_leaderboard(self, limit: int = 10, subject_id: Optional[str] = None) -> List[Dict]:
        """
        Get leaderboard of top users
        
        Args:
            limit: Number of users to return
            subject_id: Optional filter by subject
        
        Returns:
            List of user gamification stats
        """
        # Query all users with gamification data
        users = self.db.query(User).filter(
            User.role == "student",
            User.gamification.isnot(None)
        ).all()
        
        leaderboard = []
        for user in users:
            gamification = user.gamification or {}
            total_xp = gamification.get("total_xp_earned", 0)
            level = gamification.get("level", 1)
            
            leaderboard.append({
                "user_id": str(user.id),
                "email": user.email,
                "total_xp": total_xp,
                "level": level,
                "badges_count": len(gamification.get("badges", [])),
                "current_streak": gamification.get("streaks", {}).get("current_streak", 0),
            })
        
        # Sort by total XP (descending)
        leaderboard.sort(key=lambda x: x["total_xp"], reverse=True)
        
        return leaderboard[:limit]

