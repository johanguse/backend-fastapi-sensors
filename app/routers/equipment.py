from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import Page
from app.core.database import get_db
from app.models.company import Company
from app.models.equipment import Equipment
from app.models.user import User, user_company
from app.schemas.equipment import EquipmentOut

router = APIRouter()


@router.get('/equipment', response_model=Page[EquipmentOut])
def read_equipment(
    company_id: Optional[int] = Query(
        None, description='Filter by company ID'
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Equipment)
        .join(Company, Equipment.company_id == Company.id)
        .join(
            user_company,
            and_(
                user_company.c.company_id == Company.id,
                user_company.c.user_id == current_user.id,
            ),
        )
    )

    if company_id:
        query = query.filter(Equipment.company_id == company_id)

    return paginate(query)
