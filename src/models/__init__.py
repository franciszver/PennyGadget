"""
Database Models
SQLAlchemy ORM models for AI Study Companion
"""

from src.models.user import User
from src.models.subject import Subject
from src.models.goal import Goal
from src.models.session import Session
from src.models.summary import Summary
from src.models.practice import PracticeBankItem, PracticeAssignment, StudentRating
from src.models.qa import QAInteraction
from src.models.nudge import Nudge
from src.models.override import Override
from src.models.tutor_student import TutorStudentAssignment
from src.models.messaging import MessageThread, Message
from src.models.integration import Integration, Webhook, WebhookEvent

__all__ = [
    "User",
    "Subject",
    "Goal",
    "Session",
    "Summary",
    "PracticeBankItem",
    "PracticeAssignment",
    "StudentRating",
    "QAInteraction",
    "Nudge",
    "Override",
    "TutorStudentAssignment",
    "MessageThread",
    "Message",
    "Integration",
    "Webhook",
    "WebhookEvent",
]

