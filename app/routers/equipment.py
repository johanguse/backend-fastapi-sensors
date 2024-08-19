from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
    if company_id:
        user_company_access = (
            db.query(user_company)
            .filter(
                user_company.c.user_id == current_user.id,
                user_company.c.company_id == company_id,
            )
            .first()
        )
        if not user_company_access:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this company's equipment",
            )

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

    result = paginate(query)

    if not result.items:
        if company_id:
            raise HTTPException(
                status_code=404, detail='No equipment found for this company'
            )
        else:
            raise HTTPException(
                status_code=404,
                detail='No equipment found for any of your authorized companies',
            )

    return result
