"""
Parent-Student Assignment Model
"""

from sqlalchemy import Column, DateTime, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.base import Base


class ParentStudentAssignment(Base):
    __tablename__ = "parent_student_assignments"

    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20), default="active", index=True
    )  # active, paused, completed

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (PrimaryKeyConstraint("parent_id", "student_id"),)

    # Relationships
    parent = relationship(
        "User", foreign_keys=[parent_id], backref="parent_assignments"
    )
    student = relationship(
        "User", foreign_keys=[student_id], backref="parent_student_assignments"
    )

    def __repr__(self):
        return f"<ParentStudentAssignment(parent_id={self.parent_id}, student_id={self.student_id}, status={self.status})>"
