
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import create_access_token, get_current_user, hash_password, revoke_token
from app.models.models import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(username="admin", hashed_password=hash_password("admin123"), role="admin")
    session.add(user)
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_token_is_rejected_after_logout(db):
    user = db.query(User).first()
    token = create_access_token(user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Token works before logout.
    resolved_user = get_current_user(credentials=credentials, db=db)
    assert resolved_user.id == user.id

    # Revoke it (simulating logout).
    revoke_token(credentials, db)

    # Same token must now be rejected.
    with pytest.raises(Exception):
        get_current_user(credentials=credentials, db=db)
