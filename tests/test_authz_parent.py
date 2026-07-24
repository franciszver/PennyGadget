"""
HTTP-level access-control tests for parent<->student linkage (#68).

Parent<->student links are ADMIN/seed-provisioned; there is no
self-service linking endpoint. These tests cover:

  - GET /dashboards/parent/student/{student_id}
  - GET /dashboards/parent/students
  - GET /analytics/advanced/engagement/{user_id}
"""

import uuid

import pytest

from tests._authz_utils import auth_headers, create_user, token_for
from tests.test_models import TestParentStudentAssignment


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setattr("src.config.settings.settings.jwt_secret", "test-secret")


def _link(db_session, parent, student):
    assignment = TestParentStudentAssignment(
        parent_id=parent.id,
        student_id=student.id,
        status="active",
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


class TestParentDashboardAuthz:
    # No linked-parent -> 200 case for GET /parent/student/{student_id}
    # here: same pre-existing test-harness limitation documented in
    # tests/test_authz_reads.py's TestDashboardsParentLockedToAdmin - the
    # handler layers the real src.models.user.User model against
    # AnalyticsAggregator's student lookup, and no id format satisfies
    # both under SQLite. The authz gate itself (assert_can_access_student)
    # runs before that lookup and is exercised by the 403 case below plus
    # TestEngagementParentAuthz, which shares the same helper.

    def test_unlinked_parent_returns_403(self, client, db_session):
        parent = create_user(db_session, "unlink-parent-a@example.com", role="parent")
        student = create_user(
            db_session, "unlink-student-a@example.com", role="student"
        )
        parent_headers = auth_headers(token_for(parent))

        resp = client.get(
            f"/api/v1/dashboards/parent/student/{student.id}",
            headers=parent_headers,
        )

        assert resp.status_code == 403


class TestParentStudentsListAuthz:
    def test_parent_sees_only_linked_students(self, client, db_session):
        parent = create_user(db_session, "list-parent-a@example.com", role="parent")
        linked = create_user(
            db_session, "list-linked-student@example.com", role="student"
        )
        unlinked = create_user(
            db_session, "list-unlinked-student@example.com", role="student"
        )
        _link(db_session, parent, linked)
        parent_headers = auth_headers(token_for(parent))

        resp = client.get("/api/v1/dashboards/parent/students", headers=parent_headers)

        assert resp.status_code == 200
        student_ids = {s["student_id"] for s in resp.json()["data"]["students"]}
        assert str(uuid.UUID(linked.id)) in student_ids
        assert str(uuid.UUID(unlinked.id)) not in student_ids

    def test_admin_sees_all_students(self, client, db_session):
        admin = create_user(db_session, "list-admin-a@example.com", role="admin")
        create_user(db_session, "list-admin-student-a@example.com", role="student")
        create_user(db_session, "list-admin-student-b@example.com", role="student")
        admin_headers = auth_headers(token_for(admin))

        resp = client.get("/api/v1/dashboards/parent/students", headers=admin_headers)

        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 2


class TestEngagementParentAuthz:
    def test_linked_parent_returns_200(self, client, db_session):
        parent = create_user(db_session, "eng-parent-a@example.com", role="parent")
        student = create_user(
            db_session, "eng-parent-student-a@example.com", role="student"
        )
        _link(db_session, parent, student)
        parent_headers = auth_headers(token_for(parent))

        resp = client.get(
            f"/api/v1/analytics/advanced/engagement/{student.id}",
            headers=parent_headers,
        )

        assert resp.status_code == 200

    def test_unlinked_parent_returns_403(self, client, db_session):
        parent = create_user(db_session, "eng-parent-b@example.com", role="parent")
        student = create_user(
            db_session, "eng-parent-student-b@example.com", role="student"
        )
        parent_headers = auth_headers(token_for(parent))

        resp = client.get(
            f"/api/v1/analytics/advanced/engagement/{student.id}",
            headers=parent_headers,
        )

        assert resp.status_code == 403
