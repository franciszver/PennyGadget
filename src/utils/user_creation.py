"""
User Creation Utilities
Automatically create user records for Cognito users on first login
"""

from sqlalchemy.orm import Session
from src.models.user import User
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


def ensure_user_exists(db: Session, cognito_sub: str, email: str, role: str = "student") -> User:
    """
    Ensure a user exists in the database, creating if necessary.
    
    This is called when a Cognito user first authenticates.
    
    Args:
        db: Database session
        cognito_sub: Cognito subject (sub) from JWT token
        email: User email from JWT token
        role: User role (default: "student")
    
    Returns:
        User: The user record (existing or newly created)
    """
    # Check if user already exists
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    
    if user:
        # User exists, update email if it changed
        if user.email != email:
            logger.info(f"Updating email for user {user.id}: {user.email} -> {email}")
            user.email = email
            db.commit()
        return user
    
    # User doesn't exist, create it
    logger.info(f"Creating new user for Cognito sub: {cognito_sub}, email: {email}")
    
    user = User(
        id=uuid4(),
        cognito_sub=cognito_sub,
        email=email,
        role=role,
        profile={},
        gamification={},
        analytics={},
        disclaimer_shown=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Created user {user.id} for email {email}")
    return user

