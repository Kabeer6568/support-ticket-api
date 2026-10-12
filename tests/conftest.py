import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret-key-for-local-testing"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.ticket_triage import TicketTriageResult
from app.models.user import User
from app.routes import ai, comment, ticket, user
from app.main import app

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE,
)


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(bind=TEST_ENGINE)
    monkeypatch.setattr(user, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(ticket, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(comment, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(ai, "SessionLocal", TestSessionLocal)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client(db):
    with TestClient(app) as test_client:
        yield test_client


def create_user(db, name, email, role, password="correct-horse-battery"):
    from app.routes.user import password_hash

    user = User(
        name=name,
        email=email,
        password=password_hash.hash(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
