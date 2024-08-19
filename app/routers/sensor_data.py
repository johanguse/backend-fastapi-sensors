from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import LimitOffsetPage
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.equipment import Equipment
from app.models.sensor_data import SensorData as SensorDataModel
from app.models.user import User, user_company
from app.schemas.sensor_data import SensorDataOut

router = APIRouter()


@router.get('/sensor-data', response_model=LimitOffsetPage[SensorDataOut])
def read_sensor_data(
    equipment_id: int = Query(..., description='Filter by equipment ID'),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if the user has access to the equipment's company
    equipment = (
        db.query(Equipment).filter(Equipment.id == equipment_id).first()
    )
    if not equipment:
        raise HTTPException(status_code=404, detail='Equipment not found')

    user_company_relation = (
        db.query(user_company)
        .filter(
            user_company.c.user_id == current_user.id,
            user_company.c.company_id == equipment.company_id,
        )
        .first()
    )

    if not user_company_relation:
        raise HTTPException(
            status_code=403,
            detail="User does not have access to this equipment's data",
        )

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
