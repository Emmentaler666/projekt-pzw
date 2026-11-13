from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Loan, User
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanOut
from app.services import loans as loan_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanOut, status_code=201)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loan_service.create_loan(db, current_user, data.equipment_id)


@router.get("", response_model=Page[LoanOut])
def list_loans(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Loan)
    if current_user.role != "admin":
        query = query.where(Loan.user_id == current_user.id)
    if active is True:
        query = query.where(Loan.returned_at.is_(None))
    elif active is False:
        query = query.where(Loan.returned_at.is_not(None))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(query.order_by(Loan.id).limit(limit).offset(offset)).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{loan_id}", response_model=LoanOut)
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loan_service.get_loan_for_user(db, current_user, loan_id)


@router.post("/{loan_id}/return", response_model=LoanOut)
def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loan_service.return_loan(db, current_user, loan_id)


@router.post("/{loan_id}/extend", response_model=LoanOut)
def extend_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return loan_service.extend_loan(db, current_user, loan_id)