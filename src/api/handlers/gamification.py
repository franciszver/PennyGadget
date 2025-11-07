"""
Gamification Handler
XP, levels, badges, streaks, and leaderboards
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from uuid import UUID

from src.config.database import get_db
from src.api.middleware.auth import get_current_user, require_role
from src.services.gamification.engine import GamificationEngine
from src.services.gamification.badges import BadgeSystem
from src.api.schemas.gamification import (
    GamificationResponse,
    BadgeInfo,
    LeaderboardResponse,
    AwardXPRequest,
    AwardXPResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me")
async def get_my_gamification(
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's gamification state
    """
    user_sub = current_user.get("sub")
    from src.models.user import User
    db_user = db.query(User).filter(User.cognito_sub == user_sub).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    engine = GamificationEngine(db)
    gamification = engine.get_user_gamification(str(db_user.id))
    
    # Get next level info
    next_level_info = engine.get_xp_for_next_level(gamification["level"])
    
    # Get badge details
    badge_system = BadgeSystem(db)
    badge_details = badge_system.get_user_badges(str(db_user.id))
    
    return {
        "success": True,
        "data": {
            **gamification,
            "badges": badge_details,
            "next_level_info": next_level_info
        }
    }


@router.get("/users/{user_id}")
async def get_user_gamification(
    user_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get gamification state for a specific user
    """
    engine = GamificationEngine(db)
    gamification = engine.get_user_gamification(str(user_id))
    
    # Get badge details
    badge_system = BadgeSystem(db)
    badge_details = badge_system.get_user_badges(str(user_id))
    
    # Get next level info
    next_level_info = engine.get_xp_for_next_level(gamification["level"])
    
    return {
        "success": True,
        "data": {
            **gamification,
            "badges": badge_details,
            "next_level_info": next_level_info
        }
    }


@router.get("/badges")
async def get_all_badges(
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all available badges
    """
    badge_system = BadgeSystem(db)
    all_badges = badge_system.get_all_badges()
    
    badges_list = [
        {"id": badge_id, **badge_info}
        for badge_id, badge_info in all_badges.items()
    ]
    
    return {
        "success": True,
        "data": {
            "badges": badges_list,
            "total": len(badges_list)
        }
    }


@router.get("/badges/me")
async def get_my_badges(
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's badges
    """
    user_sub = current_user.get("sub")
    from src.models.user import User
    db_user = db.query(User).filter(User.cognito_sub == user_sub).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    badge_system = BadgeSystem(db)
    badges = badge_system.get_user_badges(str(db_user.id))
    
    return {
        "success": True,
        "data": {
            "badges": badges,
            "total": len(badges)
        }
    }


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get leaderboard of top users
    """
    engine = GamificationEngine(db)
    leaderboard = engine.get_leaderboard(limit=limit)
    
    # Add ranks
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = i
    
    # Get current user's rank
    user_sub = current_user.get("sub")
    from src.models.user import User
    db_user = db.query(User).filter(User.cognito_sub == user_sub).first()
    
    user_rank = None
    if db_user:
        user_gamification = engine.get_user_gamification(str(db_user.id))
        user_total_xp = user_gamification.get("total_xp_earned", 0)
        
        # Find user's rank
        for i, entry in enumerate(leaderboard, 1):
            if entry["user_id"] == str(db_user.id):
                user_rank = i
                break
        
        # If user not in top N, calculate approximate rank
        if user_rank is None:
            users_above = sum(1 for entry in leaderboard if entry["total_xp"] > user_total_xp)
            user_rank = users_above + 1
    
    return {
        "success": True,
        "data": {
            "entries": leaderboard,
            "total_users": len(leaderboard),
            "user_rank": user_rank
        }
    }


@router.post("/award-xp")
async def award_xp(
    request: AwardXPRequest,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "tutor"]))
):
    """
    Award XP to a user (admin/tutor only)
    
    This endpoint is typically called automatically by the system,
    but can be used manually for testing or corrections.
    """
    engine = GamificationEngine(db)
    
    try:
        result = engine.award_xp(
            user_id=request.user_id,
            action=request.action,
            amount=request.amount,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/streak/update")
async def update_streak(
    activity_type: str = Query("daily", description="Type of activity"),
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update user's streak (typically called automatically)
    """
    user_sub = current_user.get("sub")
    from src.models.user import User
    db_user = db.query(User).filter(User.cognito_sub == user_sub).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    engine = GamificationEngine(db)
    streak_info = engine.update_streak(str(db_user.id), activity_type)
    
    return {
        "success": True,
        "data": streak_info
    }

