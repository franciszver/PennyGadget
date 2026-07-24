"""Tests for scripts/setup_db.py::get_db_connection_string().

Verifies DATABASE_URL-first precedence (matching src/config/settings.py::
get_database_url()) so migrations against Neon (which requires SSL) work.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine  # noqa: E402

from scripts.setup_db import (  # noqa: E402
    _psycopg2_params_from_url,
    get_db_connection_string,
)


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
    monkeypatch.setenv("DB_HOST", "testhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "testuser")
    monkeypatch.setenv("DB_PASSWORD", "testpass")

    result = get_db_connection_string()

    assert result == "postgresql://testuser:testpass@testhost:5433/testdb"


def test_psycopg2_params_from_url_carries_sslmode_and_channel_binding():
    """run_migration's psycopg2.connect() params must honor the DSN's SSL
    query params, not silently drop them (leaving psycopg2 to default to
    sslmode=prefer)."""
    neon_dsn = (
        "postgresql://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    engine = create_engine(neon_dsn)

    params = _psycopg2_params_from_url(engine.url)

    assert params["host"] == "ep-x-pooler.us-east-2.aws.neon.tech"
    assert params["port"] == 5432
    assert params["database"] == "neondb"
    assert params["user"] == "u"
    assert params["password"] == "p"
    assert params["sslmode"] == "require"
    assert params["channel_binding"] == "require"
