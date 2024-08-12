from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None


class CompanyInDBBase(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime


class Company(CompanyInDBBase):
    pass


class CompanyInDB(CompanyInDBBase):
    pass


class CompanyOut(CompanyInDBBase):
    pass
