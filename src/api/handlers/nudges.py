"""
Nudges Handler
POST /nudges/check - Check if nudge should be sent
POST /nudges/:nudge_id/engage - Track nudge engagement
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from src.config.database import get_db
from src.api.middleware.auth import get_current_user_optional
from src.models.nudge import Nudge
from src.models.user import User
from src.services.nudges.engine import NudgeEngine
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nudges", tags=["nudges"])


class NudgeCheckRequest(BaseModel):
    student_id: str
    check_type: str  # "inactivity" | "goal_completion" | "login"


class NudgeEngageRequest(BaseModel):
    engagement_type: str  # "opened" | "clicked"


@router.post("/check")
async def check_nudge(
    request: NudgeCheckRequest,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Check if a student should receive a nudge
    
    Called by scheduled job or on login
    """
    engine = NudgeEngine(db)
    result = engine.should_send_nudge(request.student_id, request.check_type)
    
    if result["should_send"]:
        # Create nudge record
        nudge = Nudge(
            id=uuid.uuid4(),
            user_id=uuid.UUID(request.student_id),
            type=result["nudge"]["type"],
            channel=result["nudge"]["channel"],
            message=result["nudge"]["message"],
            personalized=result["nudge"]["personalized"],
            sent_at=datetime.utcnow(),
            trigger_reason=result["nudge"].get("trigger_reason"),
            suggestions_made=result["nudge"].get("suggestions", [])
        )
        
        db.add(nudge)
        db.commit()
        db.refresh(nudge)
        
        # Send email if channel includes email
        if "email" in result["nudge"]["channel"] or result["nudge"]["channel"] == "both":
            try:
                from src.services.notifications.email import EmailService
                email_service = EmailService(db)
                
                user = db.query(User).filter(User.id == request.student_id).first()
                if user:
                    email_service.send_nudge_notification(
                        to_email=user.email,
                        nudge_type=result["nudge"]["type"],
                        message=result["nudge"]["message"],
                        suggestions=result["nudge"].get("suggestions", [])
                    )
            except Exception as e:
                # Log error but don't fail the request
                logger.warning(f"Failed to send nudge email: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "should_send": True,
                "nudge": {
                    "nudge_id": str(nudge.id),
                    "type": nudge.type,
                    "channel": nudge.channel,
                    "message": nudge.message,
                    "personalized": nudge.personalized,
                    "suggestions": nudge.suggestions_made or []
                }
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "should_send": False,
                "reason": result.get("reason", "unknown"),
                "next_available": result.get("next_available")
            }
        }


@router.post("/{nudge_id}/engage")
async def track_nudge_engagement(
    nudge_id: UUID,
    request: NudgeEngageRequest,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Track nudge engagement (opened/clicked)
    
    Called by React frontend when user interacts with nudge
    """
    nudge = db.query(Nudge).filter(Nudge.id == nudge_id).first()
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")
    
    if request.engagement_type == "opened" and not nudge.opened_at:
        nudge.opened_at = datetime.utcnow()
    elif request.engagement_type == "clicked" and not nudge.clicked_at:
        nudge.clicked_at = datetime.utcnow()
        # Also mark as opened if not already
        if not nudge.opened_at:
            nudge.opened_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "data": {
            "nudge_id": str(nudge_id),
            "engagement_logged": True,
            "engagement_type": request.engagement_type
        }
    }

