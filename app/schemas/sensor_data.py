from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorDataBase(BaseModel):
    equipment_id: int
    timestamp: datetime
    value: float


class SensorDataOut(SensorDataBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SensorDataInDB(SensorDataOut):
    pass


SensorData = SensorDataOut
