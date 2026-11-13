from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoanCreate(BaseModel):
    equipment_id: int


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    equipment_id: int
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    extended: bool