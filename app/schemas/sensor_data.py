from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorDataBase(BaseModel):
    equipment_id: str = Field(..., alias='equipmentId')
    timestamp: datetime
    value: float

    class Config:
        allow_population_by_field_name = True


class SensorDataOut(BaseModel):
    id: int
    equipment_id: int
    timestamp: datetime
    value: float

    model_config = ConfigDict(from_attributes=True)


class SensorDataInDB(SensorDataOut):
    pass


SensorData = SensorDataOut
