import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi_pagination import add_pagination

from app.main import app
from app.models.company import Company
from app.models.user import User, user_company
from tests.factories import CompanyFactory

add_pagination(app)

@pytest.fixture(scope="function")
def company_list(db: Session, user: User):
    companies = [CompanyFactory() for _ in range(5)]
    db.add_all(companies)
    db.commit()
    
    for company in companies:
        db.execute(user_company.insert().values(user_id=user.id, company_id=company.id, role="admin"))
    
    db.commit()
    for company in companies:
        db.refresh(company)
    return companies

def test_read_companies(client: TestClient, company_list: list[Company], token: str):
    response = client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}, Response: {response.text}"
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == len(company_list)
    assert data["total"] == len(company_list)
    assert "page" in data
    assert "size" in data
    assert "pages" in data

def test_read_companies_pagination(client: TestClient, company_list: list[Company], token: str):
    response = client.get("/api/v1/companies?page=1&size=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}, Response: {response.text}"
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == len(company_list)
    assert data["page"] == 1
    assert data["size"] == 2

def test_get_company_by_id(client: TestClient, company_list: list[Company], token: str):
    company = company_list[0]
    response = client.get(f"/api/v1/companies/{company.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}, Response: {response.text}"
    data = response.json()
    assert data["id"] == company.id
    assert data["name"] == company.name
    assert data["address"] == company.address

def test_get_nonexistent_company(client: TestClient, token: str):
    response = client.get("/api/v1/companies/999999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found or user does not have access"