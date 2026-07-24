"""Tests for scripts/setup_db.py::get_db_connection_string().

Verifies DATABASE_URL-first precedence (matching src/config/settings.py::
get_database_url()) so migrations against Neon (which requires SSL) work.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.setup_db import get_db_connection_string  # noqa: E402


def test_uses_database_url_verbatim_when_set(monkeypatch):
    """DATABASE_URL should be returned as-is, preserving sslmode and pooler host."""
    neon_dsn = (
        "postgresql://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb" "?sslmode=require"
    )
    monkeypatch.setenv("DATABASE_URL", neon_dsn)

    result = get_db_connection_string()

    assert result == neon_dsn
    assert "sslmode=require" in result
    assert "ep-x-pooler.us-east-2.aws.neon.tech" in result


def test_normalizes_postgres_scheme_to_postgresql(monkeypatch):
    """postgres:// scheme should normalize to postgresql://, query string intact."""
    neon_dsn = (
        "postgres://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb" "?sslmode=require"
    )
    monkeypatch.setenv("DATABASE_URL", neon_dsn)

    result = get_db_connection_string()

    assert result == (
        "postgresql://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb" "?sslmode=require"
    )


def test_falls_back_to_db_star_when_database_url_unset(monkeypatch):
    """With DATABASE_URL unset, existing DB_*-composed behavior is preserved."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    result = get_db_connection_string()

    assert result == "postgresql://postgres:@localhost:5432/elevareai"
