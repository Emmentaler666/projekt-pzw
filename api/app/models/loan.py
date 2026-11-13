from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extended: Mapped[bool] = mapped_column(default=False, server_default="false")

    user: Mapped["User"] = relationship(back_populates="loans")
    equipment: Mapped["Equipment"] = relationship(back_populates="loans")
