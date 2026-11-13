from pydantic import BaseModel, ConfigDict, Field


class EquipmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    inventory_number: str = Field(min_length=1, max_length=50)


class EquipmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    inventory_number: str | None = Field(default=None, min_length=1, max_length=50)


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    inventory_number: str