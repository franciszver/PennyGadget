"""
Pytest Configuration
Shared fixtures for testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.config.settings import settings
from src.config.database import get_db

# Import test models (SQLite-compatible with JSON instead of ARRAY)
from tests.test_models import (
    TestBase,
    TestUser, TestSubject, TestSession, TestSummary,
    TestQAInteraction, TestPracticeBankItem, TestGoal, TestStudentRating,
    TestMessageThread, TestMessage, TestPracticeAssignment
)


# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with SQLite-compatible models"""
    # Use test models that are SQLite-compatible
    TestBase.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""
    from src.config.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "cognito_sub": "test-user-123",
        "email": "test@example.com",
        "role": "student"
    }

