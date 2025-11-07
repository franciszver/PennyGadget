"""
Gamification Schemas
Request/response models for gamification endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class GamificationResponse(BaseModel):
    """User gamification state"""
    xp: int
    level: int
    badges: List[Dict]
    streaks: Dict
    meta_rewards: List[Dict]
    total_xp_earned: int
    last_activity: Optional[str] = None
    next_level_info: Optional[Dict] = None


class BadgeInfo(BaseModel):
    """Badge information"""
    id: str
    name: str
    description: str
    category: str


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    user_id: str
    email: str
    total_xp: int
    level: int
    badges_count: int
    current_streak: int
    rank: Optional[int] = None


class LeaderboardResponse(BaseModel):
    """Leaderboard response"""
    entries: List[LeaderboardEntry]
    total_users: int
    user_rank: Optional[int] = None


class AwardXPRequest(BaseModel):
    """Request to award XP"""
    user_id: str
    action: str
    amount: Optional[int] = None
    metadata: Optional[Dict] = None


class AwardXPResponse(BaseModel):
    """Response from awarding XP"""
    xp_awarded: int
    total_xp: int
    total_xp_earned: int
    level: int
    level_up: bool
    badges_awarded: List[str]
    next_level_info: Optional[Dict] = None

