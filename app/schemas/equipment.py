from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EquipmentBase(BaseModel):
    equipment_id: str
    name: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    company_id: int


class EquipmentUpdate(EquipmentBase):
    company_id: Optional[int] = None
    equipment_id: Optional[str] = None


class EquipmentInDBBase(EquipmentBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Equipment(EquipmentInDBBase):
    pass


class EquipmentInDB(Equipment):
    pass


class EquipmentOut(EquipmentInDBBase):
    pass
