"""
Shared object-access helper (security remediation Phase 1, #60).

Endpoint handlers were each hand-rolling their own "does this caller own
this student's data" check. This centralizes that access model:

  - student -> may access only their own student_id
  - tutor   -> may access only students they have a TutorStudentAssignment
               with
  - parent  -> not handled here (parent routes are locked to admin
               elsewhere); treated like any other non-owner, i.e. denied
  - admin   -> may access anything
"""

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models.tutor_student import TutorStudentAssignment
from src.models.user import User


def _normalize_uuid(value) -> str:
    """Canonicalize a UUID (or UUID-like string, dashed or hex) for
    comparison, so ids that are equal but differently formatted still
    match."""
    return str(uuid.UUID(str(value)))


def assert_can_access_student(
    db: Session, current_user: dict, target_student_id
) -> User:
    """Raise HTTP 403 unless current_user may access target_student_id.

    Returns the caller's own db_user row on success, since callers
    frequently need it right after the check.
    """
    db_user = db.query(User).filter(User.cognito_sub == current_user.get("sub")).first()
    if not db_user:
        raise HTTPException(status_code=403, detail="Access denied")

    if db_user.role == "admin":
        return db_user

    if _normalize_uuid(db_user.id) == _normalize_uuid(target_student_id):
        return db_user

    if db_user.role == "tutor":
        assignment = (
            db.query(TutorStudentAssignment)
            .filter(
                TutorStudentAssignment.tutor_id == db_user.id,
                TutorStudentAssignment.student_id == uuid.UUID(str(target_student_id)),
            )
            .first()
        )
        if assignment:
            return db_user

    raise HTTPException(status_code=403, detail="Access denied")
