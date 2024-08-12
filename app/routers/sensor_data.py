from fastapi import APIRouter, Depends, Query
from fastapi_pagination import LimitOffsetPage
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sensor_data import SensorData as SensorDataModel
from app.schemas.sensor_data import SensorDataOut

router = APIRouter()


@router.get('/sensor-data', response_model=LimitOffsetPage[SensorDataOut])
def read_sensor_data(
    equipment_id: int = Query(..., description='Filter by equipment ID'),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(SensorDataModel)
    query = query.filter(SensorDataModel.equipment_id == equipment_id)

    total = query.count()
    items = (
        query.order_by(SensorDataModel.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return LimitOffsetPage(
        items=items, total=total, limit=limit, offset=offset
    )
