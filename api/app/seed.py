from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Equipment, User

USERS = [
    ("admin", "admin123", "admin"),
    ("student1", "student123", "student"),
    ("student2", "student123", "student"),
]

EQUIPMENT = [
    ("Laptop Dell Latitude", "INV-001"),
    ("Projektor Epson", "INV-002"),
    ("Arduino komplet", "INV-003"),
    ("Digitalna kamera", "INV-004"),
    ("Raspberry Pi 4", "INV-005"),
]


def seed(db: Session) -> None:
    for username, password, role in USERS:
        exists = db.scalar(select(User).where(User.username == username))
        if exists is None:
            db.add(User(username=username, password_hash=hash_password(password), role=role))

    for name, inventory_number in EQUIPMENT:
        exists = db.scalar(
            select(Equipment).where(Equipment.inventory_number == inventory_number)
        )
        if exists is None:
            db.add(Equipment(name=name, inventory_number=inventory_number))

    db.commit()


if __name__ == "__main__":
    with SessionLocal() as db:
        seed(db)
    print("Početni podaci uneseni.")
