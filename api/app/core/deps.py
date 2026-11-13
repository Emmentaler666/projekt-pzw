from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.tokens import decode_token
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError(401, "not_authenticated", "Prijava je obavezna")
    user_id = decode_token(credentials.credentials, "access")
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "invalid_token", "Korisnik više ne postoji")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise AppError(403, "forbidden", "Potrebna je uloga administratora")
    return current_user
