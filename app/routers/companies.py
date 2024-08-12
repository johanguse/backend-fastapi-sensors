from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.core.config import Page
from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter()


@router.get('/companies', response_model=Page[CompanyOut])
def read_companies(db: Session = Depends(get_db)):
    query = db.query(Company)
    return paginate(query)


@router.get('/companies/{company_id}', response_model=CompanyOut)
def get_company_by_id(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail='Company not found')
    return company
