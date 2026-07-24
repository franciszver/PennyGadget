"""
Tests for Neon.tech Postgres DSN handling (#50 migration prep).

Scope: this module validates DSN *handling* only -- that get_database_url()
passes a Neon-style pooled connection string through unchanged (sslmode and
the -pooler host preserved), that the bare postgres:// scheme some tools use
is normalized to postgresql://, and that SQLAlchemy's create_engine() accepts
the resulting URL without error.

create_engine() is lazy: it validates and parses the DSN but does not open a
network connection until a query is executed. These tests therefore prove the
URL is well-formed -- they do NOT attempt a live connection and do NOT verify
connectivity to a real Neon database. Live Neon connectivity (actual queries,
/health checks, demo login) is verified by the owner during cutover, per
_docs/RUNBOOK-neon-migration.md.
"""

from sqlalchemy import create_engine

from src.config.settings import get_database_url, settings

NEON_POOLED_DSN = (
    "postgresql://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
)


def test_get_database_url_preserves_neon_pooled_dsn_unchanged(monkeypatch):
    """Neon pooled DSN (postgresql://, -pooler host, sslmode=require) passes
    through get_database_url() unchanged."""
    monkeypatch.setattr(settings, "database_url", NEON_POOLED_DSN)

    assert get_database_url() == NEON_POOLED_DSN


def test_get_database_url_normalizes_bare_postgres_scheme_for_neon(monkeypatch):
    """A postgres:// (bare scheme) Neon DSN is normalized to postgresql://
    with the rest of the URL, including the query string, intact."""
    bare_scheme_dsn = (
        "postgres://u:p@ep-x-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
    )
    monkeypatch.setattr(settings, "database_url", bare_scheme_dsn)

    assert get_database_url() == NEON_POOLED_DSN


def test_create_engine_accepts_neon_dsn_without_connecting(monkeypatch):
    """sqlalchemy.create_engine() constructs successfully for a Neon pooled
    DSN. create_engine() is lazy -- no network connection is made here, so
    this proves the URL is well-formed to SQLAlchemy without needing a live
    database."""
    monkeypatch.setattr(settings, "database_url", NEON_POOLED_DSN)

    engine = create_engine(get_database_url(), pool_pre_ping=True)

    assert str(engine.url) == NEON_POOLED_DSN.replace(
        "u:p@", "u:***@"
    )  # SQLAlchemy masks the password by default in str(url)
    engine.dispose()
