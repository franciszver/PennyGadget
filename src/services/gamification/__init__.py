"""
Gamification Service
XP, levels, badges, streaks, and rewards
"""

from src.services.gamification.engine import GamificationEngine
from src.services.gamification.badges import BadgeSystem

__all__ = ["GamificationEngine", "BadgeSystem"]

