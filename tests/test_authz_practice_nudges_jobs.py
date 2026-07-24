"""
HTTP-level authz regression tests for Phase 2 of the broken-access-control
remediation (security remediation Phase 2).

practice.py, nudges.py, and jobs.py handlers used to depend on
get_current_user_optional and never actually checked whether the caller was
allowed to touch the target student's data. These tests pin the fix: every
route now requires auth (401 with none) and enforces ownership via
assert_can_access_student (403 for an unrelated authenticated "attacker",
2xx for the resource owner).

Note on IDs: like tests/test_auth_http_ownership.py, rows created through the
SQLite shadow models here use uuid.uuid4().hex (no dashes). The real models
these handlers query (User, PracticeAssignment, Nudge, Job, ...) have
UUID(as_uuid=True) columns whose SQLite bind processor normalizes lookup
values to that same dashless hex form, so a dashed id written via the shadow
model would silently never match. This is a pre-existing quirk of the
SQLite test harness, not an auth bug, and doesn't occur in production
(Postgres does native UUID compares either way).
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from starlette.websockets import WebSocketDisconnect

from tests._authz_utils import make_authed_pair, make_id, token_for
from tests.test_models import TestBase, TestNudge, TestPracticeAssignment, TestSubject


# No TestJob shadow model exists yet in tests/test_models.py, and that file
# is off-limits for this task. Registering one here (before db_session's
# TestBase.metadata.create_all runs) creates the "jobs" table the real
# src.models.job.Job queries against, the same trick the rest of this test
# suite already relies on for practice_assignments/goals/nudges/etc.
class TestJob(TestBase):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=make_id)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    user_id = Column(String(36), nullable=True)
    student_id = Column(String(36), nullable=True)
    parameters = Column(JSON, nullable=False, default={})
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    progress_percent = Column(Integer, default=0)
    progress_message = Column(String(255), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setattr("src.config.settings.settings.jwt_secret", "test-secret")


def _create_subject(db_session, name="Algebra"):
    subject = TestSubject(id=make_id(), name=name, category="Math")
    db_session.add(subject)
    db_session.commit()
    return subject


class TestPracticeAssignAuthz:
    """POST /api/v1/practice/assign"""

    def test_no_auth_returns_401(self, client, db_session):
        subject = _create_subject(db_session)
        resp = client.post(
            f"/api/v1/practice/assign?student_id={uuid.uuid4()}"
            f"&subject={subject.name}&num_items=0"
        )
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        subject = _create_subject(db_session)
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            f"/api/v1/practice/assign?student_id={owner.id}"
            f"&subject={subject.name}&num_items=0",
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_malformed_student_id_returns_403(self, client, db_session):
        subject = _create_subject(db_session)
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            f"/api/v1/practice/assign?student_id=not-a-uuid"
            f"&subject={subject.name}&num_items=0",
            headers=owner_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        subject = _create_subject(db_session)
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)

        # find_bank_items/get_student_rating live in the adaptive-practice
        # *service* layer (src/services/practice/adaptive.py), which is out
        # of scope for this handler-only authz task and also hits real-model
        # UUID columns with raw-string filters that don't work over SQLite.
        # Stub them so this test proves the authz gate + handler wiring
        # without dragging an unrelated service module into scope.
        with patch(
            "src.api.handlers.practice.AdaptivePracticeService.find_bank_items",
            return_value=[],
        ), patch(
            "src.api.handlers.practice.AdaptivePracticeService.get_student_rating",
            return_value=1000,
        ):
            resp = client.post(
                f"/api/v1/practice/assign?student_id={owner.id}"
                f"&subject={subject.name}&num_items=0",
                headers=owner_headers,
            )
        assert resp.status_code < 300


class TestPracticeCompleteAuthz:
    """POST /api/v1/practice/complete"""

    def _make_assignment(self, db_session, student):
        # student_rating_before is set so the handler skips its "or
        # adaptive_service.get_student_rating(...)" fallback, which filters
        # the real StudentRating model on a raw (unconverted) string id and
        # hits the same SQLite/UUID quirk described in the module docstring.
        assignment = TestPracticeAssignment(
            id=make_id(),
            student_id=student.id,
            source="bank",
            student_rating_before=1000,
            assigned_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(assignment)
        db_session.commit()
        return assignment

    def _body(self):
        return {
            "student_answer": "answer",
            "correct": False,
            "time_taken_seconds": 10,
            "hints_used": 0,
        }

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        assignment = self._make_assignment(db_session, owner)
        resp = client.post(
            f"/api/v1/practice/complete?assignment_id={assignment.id}"
            f"&item_id={assignment.id}",
            json=self._body(),
        )
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        assignment = self._make_assignment(db_session, owner)
        resp = client.post(
            f"/api/v1/practice/complete?assignment_id={assignment.id}"
            f"&item_id={assignment.id}",
            json=self._body(),
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        assignment = self._make_assignment(db_session, owner)
        resp = client.post(
            f"/api/v1/practice/complete?assignment_id={assignment.id}"
            f"&item_id={assignment.id}",
            json=self._body(),
            headers=owner_headers,
        )
        assert resp.status_code < 300


class TestPracticeSummaryAuthz:
    """POST /api/v1/practice/summary"""

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            f"/api/v1/practice/summary?assignment_id={uuid.uuid4()}"
            f"&student_id={owner.id}"
        )
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            f"/api/v1/practice/summary?assignment_id={uuid.uuid4()}"
            f"&student_id={owner.id}",
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        # completed + high performance_score keeps needs_tutor_help False,
        # avoiding an unrelated raw-string User.id lookup deeper in the
        # handler's tutor-notification branch (same SQLite/UUID quirk noted
        # in the module docstring).
        assignment = TestPracticeAssignment(
            id=make_id(),
            student_id=owner.id,
            source="bank",
            completed=True,
            performance_score=1.0,
            assigned_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(assignment)
        db_session.commit()

        resp = client.post(
            f"/api/v1/practice/summary?assignment_id={uuid.uuid4()}"
            f"&student_id={owner.id}",
            headers=owner_headers,
        )
        assert resp.status_code < 300


class TestPracticeAssignAsyncAuthz:
    """POST /api/v1/practice/assign/async"""

    def _body(self, student_id):
        return {
            "student_id": str(student_id),
            "subject": "Algebra",
            "num_items": 5,
        }

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post("/api/v1/practice/assign/async", json=self._body(owner.id))
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            "/api/v1/practice/assign/async",
            json=self._body(owner.id),
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        with patch(
            "src.api.handlers.practice.PracticeJobService.process_job",
            return_value={"success": True},
        ):
            resp = client.post(
                "/api/v1/practice/assign/async",
                json=self._body(owner.id),
                headers=owner_headers,
            )
        assert resp.status_code < 300


class TestNudgesCheckAuthz:
    """POST /api/v1/nudges/check"""

    def _body(self, student_id):
        return {"student_id": str(student_id), "check_type": "inactivity"}

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post("/api/v1/nudges/check", json=self._body(owner.id))
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            "/api/v1/nudges/check",
            json=self._body(owner.id),
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.post(
            "/api/v1/nudges/check",
            json=self._body(owner.id),
            headers=owner_headers,
        )
        assert resp.status_code < 300


class TestNudgesGetUserAuthz:
    """GET /api/v1/nudges/users/{user_id}"""

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.get(f"/api/v1/nudges/users/{owner.id}")
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        resp = client.get(f"/api/v1/nudges/users/{owner.id}", headers=attacker_headers)
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        # A recent unopened nudge short-circuits the handler's own
        # "no nudges yet -> compute a login nudge" branch, which otherwise
        # calls into NudgePersonalization.get_student_insights() and hits an
        # unrelated real-vs-shadow-model schema mismatch on qa_interactions
        # (the real QAInteraction model has a goal_id column the SQLite
        # shadow model doesn't define) - not an authz concern.
        db_session.add(
            TestNudge(
                id=make_id(),
                user_id=owner.id,
                type="login",
                channel="in_app",
                message="hi",
                sent_at=datetime.now(timezone.utc),
            )
        )
        db_session.commit()

        resp = client.get(f"/api/v1/nudges/users/{owner.id}", headers=owner_headers)
        assert resp.status_code < 300


class TestNudgesEngageAuthz:
    """POST /api/v1/nudges/{nudge_id}/engage"""

    def _make_nudge(self, db_session, user):
        nudge = TestNudge(
            id=make_id(),
            user_id=user.id,
            type="login",
            channel="in_app",
            message="hi",
            sent_at=datetime.now(timezone.utc),
        )
        db_session.add(nudge)
        db_session.commit()
        return nudge

    def _body(self):
        return {"engagement_type": "opened"}

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        nudge = self._make_nudge(db_session, owner)
        resp = client.post(f"/api/v1/nudges/{nudge.id}/engage", json=self._body())
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        nudge = self._make_nudge(db_session, owner)
        resp = client.post(
            f"/api/v1/nudges/{nudge.id}/engage",
            json=self._body(),
            headers=attacker_headers,
        )
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        nudge = self._make_nudge(db_session, owner)
        resp = client.post(
            f"/api/v1/nudges/{nudge.id}/engage",
            json=self._body(),
            headers=owner_headers,
        )
        assert resp.status_code < 300


class TestJobsGetAuthz:
    """GET /api/v1/jobs/{job_id}"""

    def _make_job(self, db_session, student, status="pending"):
        job = TestJob(
            id=make_id(),
            job_type="practice_generation",
            status=status,
            student_id=student.id,
            parameters={},
        )
        db_session.add(job)
        db_session.commit()
        return job

    def test_no_auth_returns_401(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        job = self._make_job(db_session, owner)
        resp = client.get(f"/api/v1/jobs/{job.id}")
        assert resp.status_code == 401

    def test_attacker_returns_403(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        job = self._make_job(db_session, owner)
        resp = client.get(f"/api/v1/jobs/{job.id}", headers=attacker_headers)
        assert resp.status_code == 403

    def test_owner_returns_2xx(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        job = self._make_job(db_session, owner)
        resp = client.get(f"/api/v1/jobs/{job.id}", headers=owner_headers)
        assert resp.status_code < 300


class TestJobsWebsocketAuthz:
    """WebSocket /api/v1/jobs/{job_id}/ws

    Auth-on-connect only needs to be proven for the reject paths here: the
    handler's DB access for the (pre-existing) streaming/polling logic goes
    through src.config.database.SessionLocal() directly rather than the
    get_db dependency, so it bypasses the client fixture's SQLite
    dependency-override entirely and talks to whatever real DATABASE_URL is
    configured. That's an existing pattern this task didn't touch and isn't
    reachable from this in-memory test harness, so per the task brief we
    only assert the reject path here.
    """

    def _make_job(self, db_session, student, status="pending"):
        job = TestJob(
            id=make_id(),
            job_type="practice_generation",
            status=status,
            student_id=student.id,
            parameters={},
        )
        db_session.add(job)
        db_session.commit()
        return job

    def test_no_token_connection_is_closed(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        job = self._make_job(db_session, owner)

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/jobs/{job.id}/ws") as ws:
                ws.receive_json()

        assert exc_info.value.code == 1008

    def test_attacker_token_connection_is_closed(self, client, db_session):
        owner, owner_headers, attacker, attacker_headers = make_authed_pair(db_session)
        job = self._make_job(db_session, owner)
        attacker_token = token_for(attacker)

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(
                f"/api/v1/jobs/{job.id}/ws?token={attacker_token}"
            ) as ws:
                ws.receive_json()

        assert exc_info.value.code == 1008
