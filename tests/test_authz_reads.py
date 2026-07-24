"""
HTTP-level access-control regression tests for Phase 3 handler fixes
(security remediation, #60).

Covers:
  - GET /summaries/{user_id}
  - GET /enhancements/qa/conversation-context/{student_id}
  - GET /messaging/threads?user_id=
  - GET /dashboards/parent/student/{student_id} and /dashboards/parent/students
  - GET /analytics/advanced/engagement/{user_id}
"""

import pytest

from tests._authz_utils import auth_headers, create_user, make_authed_pair, token_for
from tests.test_models import TestTutorStudentAssignment


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setattr("src.config.settings.settings.jwt_secret", "test-secret")


def _assign(db_session, tutor, student):
    assignment = TestTutorStudentAssignment(
        tutor_id=tutor.id,
        student_id=student.id,
        subject_id=None,
        status="active",
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


class TestSummariesAuthz:
    def test_attacker_returns_403(self, client, db_session):
        owner, _, _, attacker_headers = make_authed_pair(db_session, role="student")

        resp = client.get(f"/api/v1/summaries/{owner.id}", headers=attacker_headers)

        assert resp.status_code == 403

    def test_owner_returns_200(self, client, db_session):
        owner, owner_headers, _, _ = make_authed_pair(db_session, role="student")

        resp = client.get(f"/api/v1/summaries/{owner.id}", headers=owner_headers)

        assert resp.status_code == 200

    def test_tutor_with_assignment_returns_200(self, client, db_session):
        student = create_user(db_session, "sum-student@example.com", role="student")
        tutor = create_user(db_session, "sum-tutor@example.com", role="tutor")
        _assign(db_session, tutor, student)
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(f"/api/v1/summaries/{student.id}", headers=tutor_headers)

        assert resp.status_code == 200


class TestConversationHistoryAuthz:
    def test_attacker_returns_403(self, client, db_session):
        owner, _, _, attacker_headers = make_authed_pair(db_session, role="student")

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-history/{owner.id}",
            headers=attacker_headers,
        )

        assert resp.status_code == 403

    def test_owner_returns_200(self, client, db_session):
        owner, owner_headers, _, _ = make_authed_pair(db_session, role="student")

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-history/{owner.id}",
            headers=owner_headers,
        )

        assert resp.status_code == 200

    def test_tutor_without_assignment_returns_403(self, client, db_session):
        student = create_user(db_session, "hist-student-a@example.com", role="student")
        tutor = create_user(db_session, "hist-tutor-a@example.com", role="tutor")
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-history/{student.id}",
            headers=tutor_headers,
        )

        assert resp.status_code == 403

    def test_tutor_with_assignment_returns_200(self, client, db_session):
        student = create_user(db_session, "hist-student-b@example.com", role="student")
        tutor = create_user(db_session, "hist-tutor-b@example.com", role="tutor")
        _assign(db_session, tutor, student)
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-history/{student.id}",
            headers=tutor_headers,
        )

        assert resp.status_code == 200

    def test_admin_returns_200(self, client, db_session):
        student = create_user(db_session, "hist-student-c@example.com", role="student")
        admin = create_user(db_session, "hist-admin-a@example.com", role="admin")
        admin_headers = auth_headers(token_for(admin))

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-history/{student.id}",
            headers=admin_headers,
        )

        assert resp.status_code == 200


class TestConversationContextAuthz:
    def test_attacker_returns_403(self, client, db_session):
        owner, _, _, attacker_headers = make_authed_pair(db_session, role="student")

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-context/{owner.id}",
            params={"current_query": "hello"},
            headers=attacker_headers,
        )

        assert resp.status_code == 403

    def test_owner_returns_200(self, client, db_session):
        owner, owner_headers, _, _ = make_authed_pair(db_session, role="student")

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-context/{owner.id}",
            params={"current_query": "hello"},
            headers=owner_headers,
        )

        assert resp.status_code == 200

    def test_tutor_with_assignment_returns_200(self, client, db_session):
        student = create_user(db_session, "ctx-student@example.com", role="student")
        tutor = create_user(db_session, "ctx-tutor@example.com", role="tutor")
        _assign(db_session, tutor, student)
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            f"/api/v1/enhancements/qa/conversation-context/{student.id}",
            params={"current_query": "hello"},
            headers=tutor_headers,
        )

        assert resp.status_code == 200


class TestMessagingThreadsAuthz:
    def test_attacker_supplied_user_id_returns_403(self, client, db_session):
        owner, _, _, attacker_headers = make_authed_pair(db_session, role="student")

        resp = client.get(
            "/api/v1/messaging/threads",
            params={"user_id": owner.id},
            headers=attacker_headers,
        )

        assert resp.status_code == 403

    def test_own_user_id_returns_200(self, client, db_session):
        owner, owner_headers, _, _ = make_authed_pair(db_session, role="student")

        resp = client.get(
            "/api/v1/messaging/threads",
            params={"user_id": owner.id},
            headers=owner_headers,
        )

        assert resp.status_code == 200

    def test_omitted_user_id_defaults_to_authenticated_user(self, client, db_session):
        owner, owner_headers, _, _ = make_authed_pair(db_session, role="student")

        resp = client.get("/api/v1/messaging/threads", headers=owner_headers)

        assert resp.status_code == 200

    def test_tutor_with_assignment_returns_200(self, client, db_session):
        student = create_user(db_session, "msg-student@example.com", role="student")
        tutor = create_user(db_session, "msg-tutor@example.com", role="tutor")
        _assign(db_session, tutor, student)
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            "/api/v1/messaging/threads",
            params={"user_id": student.id},
            headers=tutor_headers,
        )

        assert resp.status_code == 200


class TestDashboardsParentLockedToAdmin:
    # As of #68, parents may access dashboards.py's parent routes for
    # students they are linked to via ParentStudentAssignment (admin/seed
    # provisioned). An UNLINKED parent is still denied - not because the
    # route is admin-only anymore, but because assert_can_access_student
    # finds no relationship. See tests/test_authz_parent.py for the
    # linked-parent coverage.

    def test_unlinked_parent_role_returns_403_for_student_dashboard(
        self, client, db_session
    ):
        parent = create_user(db_session, "parent-a@example.com", role="parent")
        student = create_user(db_session, "dash-student-a@example.com", role="student")
        parent_headers = auth_headers(token_for(parent))

        resp = client.get(
            f"/api/v1/dashboards/parent/student/{student.id}", headers=parent_headers
        )

        assert resp.status_code == 403

    # No admin -> 200 case for GET /parent/student/{student_id} here: the
    # handler layers the real src.models.user.User model (which needs a
    # hex-no-dash id to match under SQLite's UUID(as_uuid=True) shim) with
    # AnalyticsAggregator's student lookup (which needs the exact dashed
    # str(UUID) the route produces) against the same TestUser row - no id
    # format satisfies both, so it 404s/500s under this harness regardless
    # of authz. This is a pre-existing test-harness limitation, not an
    # access-control bug; require_role(["parent", "admin"]) is exercised
    # identically by test_admin_returns_200_for_students_list below, since
    # both parent routes share the exact same role dependency.

    def test_unlinked_parent_sees_empty_list_for_students_list(
        self, client, db_session
    ):
        parent = create_user(db_session, "parent-b@example.com", role="parent")
        create_user(db_session, "dash-student-b@example.com", role="student")
        parent_headers = auth_headers(token_for(parent))

        resp = client.get("/api/v1/dashboards/parent/students", headers=parent_headers)

        assert resp.status_code == 200
        assert resp.json()["data"]["students"] == []

    def test_admin_returns_200_for_students_list(self, client, db_session):
        admin = create_user(db_session, "admin-b@example.com", role="admin")
        admin_headers = auth_headers(token_for(admin))

        resp = client.get("/api/v1/dashboards/parent/students", headers=admin_headers)

        assert resp.status_code == 200


class TestEngagementAuthz:
    def test_tutor_without_assignment_returns_403(self, client, db_session):
        tutor = create_user(db_session, "eng-tutor-a@example.com", role="tutor")
        student = create_user(db_session, "eng-student-a@example.com", role="student")
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            f"/api/v1/analytics/advanced/engagement/{student.id}",
            headers=tutor_headers,
        )

        assert resp.status_code == 403

    def test_tutor_with_assignment_returns_200(self, client, db_session):
        tutor = create_user(db_session, "eng-tutor-b@example.com", role="tutor")
        student = create_user(db_session, "eng-student-b@example.com", role="student")
        _assign(db_session, tutor, student)
        tutor_headers = auth_headers(token_for(tutor))

        resp = client.get(
            f"/api/v1/analytics/advanced/engagement/{student.id}",
            headers=tutor_headers,
        )

        assert resp.status_code == 200

    def test_admin_returns_200(self, client, db_session):
        admin = create_user(db_session, "eng-admin-a@example.com", role="admin")
        student = create_user(db_session, "eng-student-c@example.com", role="student")
        admin_headers = auth_headers(token_for(admin))

        resp = client.get(
            f"/api/v1/analytics/advanced/engagement/{student.id}",
            headers=admin_headers,
        )

        assert resp.status_code == 200
