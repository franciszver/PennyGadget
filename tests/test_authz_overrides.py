"""
HTTP-level authz tests for src/api/handlers/overrides.py (security
remediation Phase 4).

Before this phase, POST /overrides/ trusted the body-supplied tutor_id and
student_id with no check that the caller was actually the student's
assigned tutor, and GET /overrides/{student_id} returned override history
to any authenticated tutor/admin regardless of assignment. These tests
pin the assert_can_access_student boundary on both routes.
"""

import uuid

import pytest

from tests._authz_utils import auth_headers, create_user, make_id, token_for
from tests.test_models import TestPracticeAssignment, TestTutorStudentAssignment


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setattr("src.config.settings.settings.jwt_secret", "test-secret")


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


def _create_practice(db_session, student):
    practice = TestPracticeAssignment(
        id=make_id(),
        student_id=student.id,
        source="ai_generated",
        ai_question_text="What is 2+2?",
        ai_answer_text="4",
    )
    db_session.add(practice)
    db_session.commit()
    return practice


class TestCreateOverrideAuthz:
    def test_unrelated_tutor_returns_403_and_does_not_mutate(self, client, db_session):
        tutor = create_user(db_session, "tutor-unrelated@example.com", role="tutor")
        student = create_user(db_session, "student-ov-a@example.com", role="student")
        practice = _create_practice(db_session, student)
        token = token_for(tutor)

        resp = client.post(
            "/api/v1/overrides/",
            json={
                "tutor_id": tutor.id,
                "student_id": student.id,
                "override_type": "practice",
                "target_id": practice.id,
                "action": "edit",
                "new_content": {"question": "hacked"},
            },
            headers=auth_headers(token),
        )

        assert resp.status_code == 403
        db_session.refresh(practice)
        assert practice.overridden is False
        assert practice.ai_question_text == "What is 2+2?"

    def test_assigned_tutor_success_tutor_id_derived_from_jwt(self, client, db_session):
        # override_type "qa_answer" is used here (rather than "practice" or
        # "summary") to isolate the identity-derivation behavior under test
        # from the target-lookup branches, which round-trip target_id
        # through the real (Postgres-UUID) models and are not exercised by
        # this authz-focused test file.
        tutor = create_user(db_session, "tutor-assigned@example.com", role="tutor")
        other_tutor = create_user(db_session, "tutor-other@example.com", role="tutor")
        student = create_user(db_session, "student-ov-b@example.com", role="student")
        _assign(db_session, tutor, student)
        token = token_for(tutor)

        resp = client.post(
            "/api/v1/overrides/",
            json={
                # attacker-supplied identity - must be ignored in favor of
                # the caller's own JWT-derived id.
                "tutor_id": other_tutor.id,
                "student_id": student.id,
                "override_type": "qa_answer",
                "target_id": make_id(),
                "action": "edit",
                "new_content": {"answer": "corrected answer"},
            },
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["tutor_id"] == str(uuid.UUID(tutor.id))
        assert body["data"]["tutor_id"] != str(uuid.UUID(other_tutor.id))


class TestGetOverridesAuthz:
    def test_unrelated_tutor_returns_403(self, client, db_session):
        tutor = create_user(db_session, "tutor-hist-a@example.com", role="tutor")
        student = create_user(db_session, "student-hist-a@example.com", role="student")
        token = token_for(tutor)

        resp = client.get(
            f"/api/v1/overrides/{student.id}", headers=auth_headers(token)
        )

        assert resp.status_code == 403

    def test_admin_returns_2xx(self, client, db_session):
        admin = create_user(db_session, "admin-hist@example.com", role="admin")
        student = create_user(db_session, "student-hist-b@example.com", role="student")
        token = token_for(admin)

        resp = client.get(
            f"/api/v1/overrides/{student.id}", headers=auth_headers(token)
        )

        assert resp.status_code == 200
