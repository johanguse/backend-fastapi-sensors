from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.config import Page
from app.core.database import get_db
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentOut

router = APIRouter()


@router.get('/equipment', response_model=Page[EquipmentOut])
def read_equipment(
    company_id: Optional[int] = Query(
        None, description='Filter by company ID'
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Equipment)
    if company_id:
        query = query.filter(Equipment.company_id == company_id)
    return paginate(query)
