import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.user import SessionToken, User

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000
SESSION_TTL = timedelta(days=30)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(f"{PASSWORD_SCHEME}$"):
        try:
            _, iterations_raw, salt, expected_digest = password_hash.split("$", 3)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_raw),
        ).hex()
        return hmac.compare_digest(digest, expected_digest)

    legacy_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_digest, password_hash)


def needs_password_rehash(password_hash: str) -> bool:
    return not password_hash.startswith(f"{PASSWORD_SCHEME}$")


def create_session_token(db: Session, user: User) -> str:
    token = secrets.token_hex(32)
    db.execute(delete(SessionToken).where(SessionToken.user_id == user.id))
    db.add(
        SessionToken(
            token=token,
            user_id=user.id,
            expires_at=utcnow() + SESSION_TTL,
        )
    )
    db.commit()
    return token


def get_user_by_token(db: Session, token: str) -> User | None:
    session = db.get(SessionToken, token)
    if not session:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= utcnow():
        db.delete(session)
        db.commit()
        return None
    return session.user
