"""Shared test fixtures and configuration."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import hash_password
from app.models.models import User


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def admin_user(test_db):
    """Create a test admin user."""
    user = User(
        username="test_admin",
        hashed_password=hash_password("admin123"),
        role="admin",
        shop_id=None,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def operator_user(test_db):
    """Create a test operator user."""
    user = User(
        username="test_operator",
        hashed_password=hash_password("op123"),
        role="operator",
        shop_id=1,
    )
    test_db.add(user)
    test_db.commit()
    return user
