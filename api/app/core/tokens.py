from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.errors import AppError

ALGORITHM = "HS256"


def _create_token(user_id: int, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.refresh_token_days))


def decode_token(token: str, expected_type: str) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise AppError(401, "invalid_token", "Token je neispravan ili je istekao")
    if payload.get("type") != expected_type:
        raise AppError(401, "invalid_token", "Pogrešna vrsta tokena")
    return int(payload["sub"])
