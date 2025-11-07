"""
Session Summaries Handler
POST /summaries - Generate summary from session
GET /summaries/:user_id - Get all summaries for user
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from uuid import UUID
import logging

from src.config.database import get_db
from src.api.middleware.auth import get_current_user, get_current_user_optional
from src.models.summary import Summary
from src.models.session import Session as SessionModel
from src.models.user import User
from src.services.ai.summarizer import SessionSummarizer
from src.api.schemas.summaries import CreateSummaryRequest, SummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.post("/", response_model=dict)
async def create_summary(
    request: CreateSummaryRequest,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)  # Service-to-service auth
):
    """
    Generate AI summary from a completed tutoring session
    
    Called by Rails app when a session completes
    """
    try:
        logger.info(f"Generating summary for session {request.session_id}")
        summarizer = SessionSummarizer()
        
        summary = await summarizer.generate_summary(
        session_id=request.session_id,
        student_id=request.student_id,
        tutor_id=request.tutor_id,
        transcript=request.transcript,
        session_duration_minutes=request.session_duration_minutes,
        subject=request.subject,
        topics_covered=request.topics_covered,
        db=db
    )
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
    
    # Award XP for session completion
    try:
        from src.services.gamification.engine import GamificationEngine
        gamification_engine = GamificationEngine(db)
        
        xp_result = gamification_engine.award_xp(
            user_id=request.student_id,
            action="session_completed",
            metadata={
                "session_id": str(request.session_id),
                "duration_minutes": request.session_duration_minutes,
                "subject": request.subject
            }
        )
        
        # Update streak
        streak_info = gamification_engine.update_streak(request.student_id)
    except Exception as e:
        logger.warning(f"Failed to award XP for session completion: {str(e)}")
        xp_result = None
        streak_info = None
    
    response_data = {
        "summary_id": str(summary.id),
        "session_id": str(request.session_id),
        "narrative": summary.narrative,
        "next_steps": summary.next_steps,
        "subjects_covered": summary.subjects_covered,
        "summary_type": summary.summary_type,
        "created_at": summary.created_at.isoformat() if hasattr(summary.created_at, 'isoformat') else str(summary.created_at)
    }
    
    # Add gamification info if available
    if xp_result:
        response_data["gamification"] = {
            "xp_awarded": xp_result.get("xp_awarded", 0),
            "level_up": xp_result.get("level_up", False),
            "badges_awarded": xp_result.get("badges_awarded", [])
        }
    
    return {
        "success": True,
        "data": response_data
    }


@router.get("/{user_id}")
async def get_summaries(
    user_id: UUID,
    role: Optional[str] = Query(None, description="student or tutor view"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all summaries for a user (student or tutor view)
    """
    # Verify user has access
    user_sub = current_user.get("sub")
    db_user = db.query(User).filter(User.cognito_sub == user_sub).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get summaries
    query = db.query(Summary).filter(Summary.student_id == user_id)
    
    if role == "tutor" and db_user.role == "tutor":
        # Tutors can see summaries for their students
        query = query.filter(Summary.tutor_id == db_user.id)
    
    summaries = query.order_by(Summary.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "success": True,
        "data": {
            "summaries": [
                {
                    "summary_id": str(s.id),
                    "session_id": str(s.session_id),
                    "session_date": s.session.session_date if s.session else None,
                    "narrative": s.narrative,
                    "next_steps": s.next_steps,
                    "subjects_covered": s.subjects_covered,
                    "tutor_name": s.tutor.email if s.tutor else None
                }
                for s in summaries
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total
            }
        }
    }

