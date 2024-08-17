import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models.equipment import Equipment
from app.models.company import Company
from app.models.user import User
from tests.factories import CompanyFactory, EquipmentFactory, UserFactory

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
def company(db: Session, user: User):
    company = CompanyFactory()
    company.admin_user = user  # Assuming there's an admin_user relationship
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@pytest.fixture(scope="function")
def equipment_list(db: Session, company: Company):
    equipment_list = [EquipmentFactory(company=company) for _ in range(35)]  # Create more than default page size
    db.add_all(equipment_list)
    db.commit()
    for eq in equipment_list:
        db.refresh(eq)
    return equipment_list

def test_read_equipment(client: TestClient, equipment_list: list[Equipment]):
    response = client.get("/api/v1/equipment")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == settings.DEFAULT_PAGE_SIZE
    assert data["total"] == len(equipment_list)
    assert data["page"] == 1
    assert data["size"] == settings.DEFAULT_PAGE_SIZE
    assert "pages" in data

def test_read_equipment_pagination(client: TestClient, equipment_list: list[Equipment]):
    response = client.get("/api/v1/equipment?page=2&size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == len(equipment_list)
    assert data["page"] == 2
    assert data["size"] == 10
    assert "pages" in data

def test_read_equipment_filter_by_company(client: TestClient, equipment_list: list[Equipment], company: Company):
    response = client.get(f"/api/v1/equipment?company_id={company.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == settings.DEFAULT_PAGE_SIZE
    assert data["total"] == len(equipment_list)
    for item in data["items"]:
        assert item["company_id"] == company.id

def test_read_equipment_filter_by_nonexistent_company(client: TestClient):
    response = client.get("/api/v1/equipment?company_id=999999")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["total"] == 0
