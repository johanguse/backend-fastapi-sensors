import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from tests.factories import CompanyFactory, UserFactory

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    del app.dependency_overrides[get_db]

@pytest.fixture(scope="function")
def user(db: Session):
    user = UserFactory()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def company_list(db: Session, user: User):
    companies = [CompanyFactory(admin_user=user) for _ in range(5)]
    db.add_all(companies)
    db.commit()
    for company in companies:
        db.refresh(company)
    return companies

def test_read_companies(client: TestClient, company_list: list[Company]):
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == len(company_list)
    assert data["total"] == len(company_list)
    assert data["page"] == 1
    assert data["size"] == settings.DEFAULT_PAGE_SIZE
    assert "pages" in data

def test_read_companies_pagination(client: TestClient, company_list: list[Company]):
    response = client.get("/api/v1/companies?page=1&size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == len(company_list)
    assert data["page"] == 1
    assert data["size"] == 2

def test_get_company_by_id(client: TestClient, company_list: list[Company]):
    company = company_list[0]
    response = client.get(f"/api/v1/companies/{company.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == company.id
    assert data["name"] == company.name
    assert data["address"] == company.address

def test_get_nonexistent_company(client: TestClient):
    response = client.get("/api/v1/companies/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"
