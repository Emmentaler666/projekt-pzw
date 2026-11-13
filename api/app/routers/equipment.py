from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.errors import AppError
from app.db import get_db
from app.models import Equipment, Loan, User
from app.schemas.common import Page
from app.schemas.equipment import EquipmentCreate, EquipmentOut, EquipmentUpdate

router = APIRouter(prefix="/equipment", tags=["equipment"])


def _get_or_404(db: Session, equipment_id: int) -> Equipment:
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise AppError(404, "equipment_not_found", "Oprema nije pronađena")
    return equipment


def _check_inventory_number_free(db: Session, inventory_number: str, own_id: int | None = None):
    other = db.scalar(select(Equipment).where(Equipment.inventory_number == inventory_number))
    if other is not None and other.id != own_id:
        raise AppError(409, "inventory_number_taken", "Inventarski broj već postoji")


@router.get("", response_model=Page[EquipmentOut])
def list_equipment(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = db.scalar(select(func.count()).select_from(Equipment))
    items = db.scalars(
        select(Equipment).order_by(Equipment.id).limit(limit).offset(offset)
    ).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_or_404(db, equipment_id)


@router.post("", response_model=EquipmentOut, status_code=201)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    _check_inventory_number_free(db, data.inventory_number)
    equipment = Equipment(name=data.name, inventory_number=data.inventory_number)
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    equipment = _get_or_404(db, equipment_id)
    changes = data.model_dump(exclude_unset=True)
    if "inventory_number" in changes:
        _check_inventory_number_free(db, changes["inventory_number"], own_id=equipment.id)
    for field, value in changes.items():
        setattr(equipment, field, value)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=204)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    equipment = _get_or_404(db, equipment_id)
    has_loans = db.scalar(
        select(func.count()).select_from(Loan).where(Loan.equipment_id == equipment.id)
    )
    if has_loans:
        raise AppError(409, "equipment_has_loans", "Oprema ima posudbe i ne može se obrisati")
    db.delete(equipment)
    db.commit()