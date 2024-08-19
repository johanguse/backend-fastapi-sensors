from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import Page
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User, user_company
from app.schemas.company import CompanyOut

router = APIRouter()


@router.get('/companies', response_model=Page[CompanyOut])
def read_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Company)
        .join(user_company)
        .filter(user_company.c.user_id == current_user.id)
    )
    return paginate(query)


@router.get('/companies/{company_id}', response_model=CompanyOut)
def get_company_by_id(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = (
        db.query(Company)
        .join(user_company)
        .filter(
            Company.id == company_id, user_company.c.user_id == current_user.id
        )
        .first()
    )
    if not company:
        raise HTTPException(
            status_code=404,
            detail='Company not found or user does not have access',
        )
    return company
