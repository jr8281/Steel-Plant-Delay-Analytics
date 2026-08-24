import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.models import TokenBlacklist, User

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "shop_id": user.shop_id,
        "jti": str(uuid.uuid4()),
        "exp": expires,
    }
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def _decode_token(token: str) -> dict:
    return dict(jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    try:
        payload = _decode_token(credentials.credentials)
        user_id = int(payload.get("sub", ""))
        jti = payload.get("jti")
    except (JWTError, TypeError, ValueError):
        logger.warning("Rejected request with an invalid or malformed JWT.")
        raise unauthorized

    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        logger.info("Rejected request using a revoked (logged-out) token.")
        raise unauthorized

    user = db.get(User, user_id)
    if not user:
        raise unauthorized
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator permission is required.")
    return user


def revoke_token(credentials: HTTPAuthorizationCredentials, db: Session) -> None:
    """Blacklist the current token's jti so it can no longer be used, even before it expires."""
    try:
        payload = _decode_token(credentials.credentials)
    except JWTError:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    if not db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        db.add(TokenBlacklist(jti=jti, expires_at=expires_at))
        db.commit()
        logger.info("Token revoked on logout.")
