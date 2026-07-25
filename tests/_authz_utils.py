"""
Shared test utilities for creating authenticated users (security
remediation Phase 1, #60).

Later-phase ownership/access-control tests that need an "owner" and an
unrelated "attacker" authenticated user can import these instead of
duplicating the _create_user/_token/_auth pattern already used in
tests/test_auth_http_ownership.py.
"""

import uuid

from src.services.auth import create_access_token
from tests.test_models import TestUser


def make_id() -> str:
    return uuid.uuid4().hex


def create_user(db_session, email, role="student", cognito_sub=None):
    user = TestUser(
        id=make_id(),
        cognito_sub=cognito_sub or make_id(),
        email=email,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    return user


def token_for(user, **kw):
    return create_access_token(
        sub=user.cognito_sub, email=user.email, role=user.role, **kw
    )


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_authed_pair(db_session, role="student"):
    """Create two distinct authenticated users - an "owner" and an
    unrelated "attacker" - for ownership-boundary tests.

    Returns (owner, owner_headers, attacker, attacker_headers).
    """
    owner = create_user(db_session, f"owner-{make_id()}@example.com", role=role)
    attacker = create_user(db_session, f"attacker-{make_id()}@example.com", role=role)
    return (
        owner,
        auth_headers(token_for(owner)),
        attacker,
        auth_headers(token_for(attacker)),
    )
