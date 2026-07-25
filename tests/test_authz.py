"""
Unit tests for src/api/middleware/authz.py:assert_can_access_student
(security remediation Phase 1, #60).
"""

import pytest
from fastapi import HTTPException

from src.api.middleware.authz import assert_can_access_student
from tests._authz_utils import create_user, make_id
from tests.test_models import TestTutorStudentAssignment


def _current_user(user):
    return {"sub": user.cognito_sub, "email": user.email, "role": user.role}


def _assign(db_session, tutor, student):
    assignment = TestTutorStudentAssignment(
        tutor_id=tutor.id,
        student_id=student.id,
        subject_id=make_id(),
        status="active",
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


class TestAssertCanAccessStudent:
    def test_owner_allowed(self, db_session):
        student = create_user(db_session, "owner@example.com", role="student")

        result = assert_can_access_student(
            db_session, _current_user(student), student.id
        )

        assert result.id.hex == student.id

    def test_unrelated_student_returns_403(self, db_session):
        student_a = create_user(db_session, "a@example.com", role="student")
        student_b = create_user(db_session, "b@example.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(
                db_session, _current_user(student_a), student_b.id
            )

        assert exc_info.value.status_code == 403

    def test_tutor_with_assignment_allowed(self, db_session):
        tutor = create_user(db_session, "tutor@example.com", role="tutor")
        student = create_user(db_session, "student-t@example.com", role="student")
        _assign(db_session, tutor, student)

        result = assert_can_access_student(db_session, _current_user(tutor), student.id)

        assert result.id.hex == tutor.id

    def test_tutor_without_assignment_returns_403(self, db_session):
        tutor = create_user(db_session, "tutor2@example.com", role="tutor")
        student = create_user(db_session, "student-u@example.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(tutor), student.id)

        assert exc_info.value.status_code == 403

    def test_parent_treated_as_non_owner_returns_403(self, db_session):
        parent = create_user(db_session, "parent@example.com", role="parent")
        student = create_user(db_session, "student-v@example.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(parent), student.id)

        assert exc_info.value.status_code == 403

    def test_admin_allowed(self, db_session):
        admin = create_user(db_session, "admin@example.com", role="admin")
        student = create_user(db_session, "student-w@example.com", role="student")

        result = assert_can_access_student(db_session, _current_user(admin), student.id)

        assert result.id.hex == admin.id

    def test_unknown_sub_returns_403(self, db_session):
        student = create_user(db_session, "student-x@example.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(
                db_session, {"sub": "not-in-db", "email": "x@example.com"}, student.id
            )

        assert exc_info.value.status_code == 403

    def test_none_target_returns_403_for_student(self, db_session):
        student = create_user(
            db_session, "none-target-student@example.com", role="student"
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(student), None)

        assert exc_info.value.status_code == 403

    def test_none_target_returns_403_for_tutor(self, db_session):
        tutor = create_user(db_session, "none-target-tutor@example.com", role="tutor")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(tutor), None)

        assert exc_info.value.status_code == 403

    def test_none_target_returns_403_for_admin(self, db_session):
        admin = create_user(db_session, "none-target-admin@example.com", role="admin")

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(admin), None)

        assert exc_info.value.status_code == 403

    def test_malformed_target_returns_403_for_student(self, db_session):
        student = create_user(
            db_session, "malformed-target-student@example.com", role="student"
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(student), "abc")

        assert exc_info.value.status_code == 403

    def test_malformed_target_returns_403_for_tutor(self, db_session):
        tutor = create_user(
            db_session, "malformed-target-tutor@example.com", role="tutor"
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(tutor), "abc")

        assert exc_info.value.status_code == 403

    def test_malformed_target_returns_403_for_admin(self, db_session):
        admin = create_user(
            db_session, "malformed-target-admin@example.com", role="admin"
        )

        with pytest.raises(HTTPException) as exc_info:
            assert_can_access_student(db_session, _current_user(admin), "abc")

        assert exc_info.value.status_code == 403
