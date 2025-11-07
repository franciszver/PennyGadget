"""
Practice Assignment Handler
POST /practice/assign - Assign adaptive practice items
POST /practice/complete - Record practice completion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import Optional
from uuid import UUID

from src.config.database import get_db
from src.api.middleware.auth import get_current_user_optional
from src.models.practice import PracticeBankItem, PracticeAssignment, StudentRating
from src.models.user import User
from src.models.subject import Subject
from src.services.practice.adaptive import AdaptivePracticeService
from src.services.practice.generator import PracticeGenerator
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/assign")
async def assign_practice(
    student_id: str,
    subject: str,
    topic: Optional[str] = None,
    num_items: int = 5,
    goal_tags: Optional[list[str]] = None,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Assign adaptive practice items to a student
    
    Called by Rails app or React frontend
    """
    # Get subject - handle case-insensitive and suggest similar subjects if not found
    subject_obj = db.query(Subject).filter(
        func.lower(Subject.name) == func.lower(subject)
    ).first()
    
    if not subject_obj:
        # Try to find similar subjects
        similar_subjects = db.query(Subject).filter(
            Subject.name.ilike(f"%{subject}%")
        ).limit(5).all()
        
        if similar_subjects:
            suggestions = [s.name for s in similar_subjects]
            raise HTTPException(
                status_code=404,
                detail=f"Subject '{subject}' not found. Did you mean: {', '.join(suggestions)}?"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Subject '{subject}' not found. Please check the subject name and try again."
            )
    
    # Get student
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Initialize adaptive practice service
    adaptive_service = AdaptivePracticeService(db)
    
    # Get student rating for this subject
    student_rating = adaptive_service.get_student_rating(student_id, str(subject_obj.id))
    
    # Select difficulty range
    difficulty_min, difficulty_max = adaptive_service.select_difficulty_range(student_rating)
    
    # Try to find bank items first
    bank_items = adaptive_service.find_bank_items(
        subject_id=str(subject_obj.id),
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        goal_tags=goal_tags,
        limit=num_items
    )
    
    items = []
    assignment_id = uuid.uuid4()
    all_ai_generated = len(bank_items) == 0
    
    # If no bank items found, try expanding difficulty range
    if len(bank_items) == 0:
        logger.info(
            f"No bank items found for subject {subject}, difficulty {difficulty_min}-{difficulty_max}. "
            f"Expanding search range."
        )
        # Expand difficulty range by ±2
        expanded_min = max(1, difficulty_min - 2)
        expanded_max = min(10, difficulty_max + 2)
        bank_items = adaptive_service.find_bank_items(
            subject_id=str(subject_obj.id),
            difficulty_min=expanded_min,
            difficulty_max=expanded_max,
            goal_tags=None,  # Remove goal tag filter for broader search
            limit=num_items
        )
    
    # Use bank items if available
    for bank_item in bank_items:
        assignment = PracticeAssignment(
            id=uuid.uuid4(),
            student_id=uuid.UUID(student_id),
            source="bank",
            bank_item_id=bank_item.id,
            subject_id=subject_obj.id,
            difficulty_level=bank_item.difficulty_level,
            goal_tags=goal_tags or [],
            student_rating_before=student_rating,
            assigned_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(assignment)
        items.append({
            "item_id": str(assignment.id),
            "source": "bank",
            "question": bank_item.question_text,
            "answer": bank_item.answer_text,
            "explanation": bank_item.explanation,
            "difficulty": bank_item.difficulty_level,
            "subject": subject,
            "goal_tags": bank_item.goal_tags or []
        })
    
    # Generate AI items if we need more
    if len(items) < num_items:
        generator = PracticeGenerator()
        needed = num_items - len(items)
        
        logger.info(
            f"Generating {needed} AI practice items for subject {subject}, "
            f"topic {topic or 'general'}, difficulty {difficulty_min}-{difficulty_max}"
        )
        
        for _ in range(needed):
            # Generate AI item
            ai_item_data = generator.generate_practice_item(
                subject=subject,
                topic=topic or subject,
                difficulty_level=(difficulty_min + difficulty_max) // 2,
                goal_tags=goal_tags
            )
            
            assignment = PracticeAssignment(
                id=uuid.uuid4(),
                student_id=uuid.UUID(student_id),
                source="ai_generated",
                ai_question_text=ai_item_data["question_text"],
                ai_answer_text=ai_item_data["answer_text"],
                ai_explanation=ai_item_data["explanation"],
                flagged=True,  # AI items are always flagged
                subject_id=subject_obj.id,
                difficulty_level=(difficulty_min + difficulty_max) // 2,
                goal_tags=goal_tags or [],
                student_rating_before=student_rating,
                assigned_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(assignment)
            
            items.append({
                "item_id": str(assignment.id),
                "source": "ai_generated",
                "flagged": True,
                "question": ai_item_data["question_text"],
                "answer": ai_item_data["answer_text"],
                "explanation": ai_item_data["explanation"],
                "difficulty": (difficulty_min + difficulty_max) // 2,
                "subject": subject,
                "goal_tags": goal_tags or [],
                "requires_tutor_review": True,
                "note": "AI-generated item - flagged for tutor review"
            })
    
    db.commit()
    
    # Build response metadata
    response_metadata = {
        "student_rating_before": student_rating,
        "selected_difficulty_range": f"{difficulty_min}-{difficulty_max}",
        "bank_items_used": len([i for i in items if i.get("source") == "bank"]),
        "ai_items_generated": len([i for i in items if i.get("source") == "ai_generated"]),
        "all_ai_generated": all_ai_generated
    }
    
    if all_ai_generated:
        response_metadata["message"] = (
            f"No bank items available for {subject} at your current level. "
            f"AI-generated items have been created and flagged for tutor review."
        )
    
    return {
        "success": True,
        "data": {
            "assignment_id": str(assignment_id),
            "items": items,
            "adaptive_metadata": response_metadata
        }
    }


@router.post("/complete")
async def complete_practice(
    assignment_id: str,
    item_id: str,
    student_answer: str,
    correct: bool,
    time_taken_seconds: int,
    hints_used: int = 0,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Record completion of a practice item
    
    Updates student rating and calculates performance
    """
    # Get assignment
    assignment = db.query(PracticeAssignment).filter(
        PracticeAssignment.id == assignment_id,
        PracticeAssignment.id == item_id  # item_id should match assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Practice assignment not found")
    
    # Initialize adaptive service
    adaptive_service = AdaptivePracticeService(db)
    
    # Calculate performance score
    performance_score = adaptive_service.calculate_performance_score(
        correct=correct,
        time_taken_seconds=time_taken_seconds,
        hints_used=hints_used
    )
    
    # Get question rating (convert difficulty to Elo scale)
    question_rating = assignment.difficulty_level * 100 if assignment.difficulty_level else 1000
    
    # Update student rating
    student_rating_before = assignment.student_rating_before or adaptive_service.get_student_rating(
        str(assignment.student_id),
        str(assignment.subject_id) if assignment.subject_id else ""
    )
    
    if assignment.subject_id:
        student_rating_after = adaptive_service.update_student_rating(
            str(assignment.student_id),
            str(assignment.subject_id),
            question_rating,
            performance_score
        )
    else:
        student_rating_after = student_rating_before
    
    # Update assignment
    assignment.completed = True
    assignment.performance_score = performance_score
    assignment.student_rating_after = student_rating_after
    assignment.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Award XP for practice completion
    try:
        from src.services.gamification.engine import GamificationEngine
        gamification_engine = GamificationEngine(db)
        
        # Award base XP
        action = "practice_perfect" if performance_score >= 1.0 else "practice_completed"
        xp_result = gamification_engine.award_xp(
            user_id=str(assignment.student_id),
            action=action,
            metadata={
                "perfect_score": performance_score >= 1.0,
                "performance_score": float(performance_score),
                "assignment_id": str(assignment.id)
            }
        )
        
        # Update streak
        streak_info = gamification_engine.update_streak(str(assignment.student_id))
    except Exception as e:
        logger.warning(f"Failed to award XP for practice completion: {str(e)}")
        xp_result = None
        streak_info = None
    
    # Calculate next difficulty suggestion
    if assignment.subject_id:
        next_min, next_max = adaptive_service.select_difficulty_range(student_rating_after)
        next_difficulty = (next_min + next_max) // 2
    else:
        next_difficulty = assignment.difficulty_level or 5
    
    response_data = {
        "performance_score": float(performance_score),
        "student_rating_before": student_rating_before,
        "student_rating_after": student_rating_after,
        "next_difficulty_suggestion": next_difficulty
    }
    
    # Add gamification info if available
    if xp_result:
        response_data["gamification"] = {
            "xp_awarded": xp_result.get("xp_awarded", 0),
            "level_up": xp_result.get("level_up", False),
            "badges_awarded": xp_result.get("badges_awarded", [])
        }
    
    if streak_info:
        response_data["streak"] = streak_info
    
    return {
        "success": True,
        "data": response_data
    }

