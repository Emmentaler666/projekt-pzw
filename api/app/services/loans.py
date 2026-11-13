from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Equipment, Loan, User

MAX_ACTIVE_LOANS = 3
LOAN_DAYS = 14
EXTENSION_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_loan_for_user(db: Session, user: User, loan_id: int) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None or (user.role != "admin" and loan.user_id != user.id):
        raise AppError(404, "loan_not_found", "Posudba nije pronađena")
    return loan


def create_loan(db: Session, user: User, equipment_id: int) -> Loan:
    if db.get(Equipment, equipment_id) is None:
        raise AppError(404, "equipment_not_found", "Oprema nije pronađena")

    active_count = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.user_id == user.id, Loan.returned_at.is_(None))
    )
    if active_count >= MAX_ACTIVE_LOANS:
        raise AppError(409, "loan_limit_reached", "Dosegnut je najveći broj aktivnih posudbi")

    taken = db.scalar(
        select(Loan).where(Loan.equipment_id == equipment_id, Loan.returned_at.is_(None))
    )
    if taken is not None:
        raise AppError(409, "equipment_unavailable", "Oprema je trenutno posuđena")

    now = _now()
    loan = Loan(
        user_id=user.id,
        equipment_id=equipment_id,
        borrowed_at=now,
        due_at=now + timedelta(days=LOAN_DAYS),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def return_loan(db: Session, user: User, loan_id: int) -> Loan:
    loan = get_loan_for_user(db, user, loan_id)
    if loan.returned_at is not None:
        raise AppError(409, "already_returned", "Oprema je već vraćena")
    loan.returned_at = _now()
    db.commit()
    db.refresh(loan)
    return loan


def extend_loan(db: Session, user: User, loan_id: int) -> Loan:
    loan = get_loan_for_user(db, user, loan_id)
    if loan.returned_at is not None:
        raise AppError(409, "already_returned", "Oprema je već vraćena")
    if loan.extended:
        raise AppError(409, "already_extended", "Posudba je već jednom produljena")
    if _now() > loan.due_at:
        raise AppError(409, "loan_overdue", "Rok je istekao, produljenje nije moguće")
    loan.due_at = loan.due_at + timedelta(days=EXTENSION_DAYS)
    loan.extended = True
    db.commit()
    db.refresh(loan)
    return loan