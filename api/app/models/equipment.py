from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    inventory_number: Mapped[str] = mapped_column(String(50), unique=True)

    loans: Mapped[list["Loan"]] = relationship(back_populates="equipment")
