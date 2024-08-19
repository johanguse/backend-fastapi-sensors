import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer
from jose import jwt
import time
from datetime import timedelta

from app.core.database import Base, get_db
from app.main import app
from app.core.security import create_refresh_token, get_password_hash
from app.core.config import settings
from app.models.user import User, user_company
from app.models.company import Company

@pytest.fixture(scope="session")
def db_engine():
    with PostgresContainer("postgres:13") as postgres:
        engine = create_engine(postgres.get_connection_url())
        yield engine

@pytest.fixture(scope="function")
def db(db_engine):
    Base.metadata.create_all(db_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(db_engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

@pytest.fixture
def seed_data(db: Session):
    hashed_password = get_password_hash("mE8eAazZ28xmmHG$")
    user1 = User(email="johanguse@gmail.com", hashed_password=hashed_password, name="Johan Guse", is_active=True)
    user2 = User(email="jane.smith@example.com", hashed_password=hashed_password, name="Jane Smith", is_active=True)
    db.add_all([user1, user2])
    db.commit()

    company1 = Company(name="Oil Corp", address="123 Main St")
    company2 = Company(name="Energy Plus", address="456 Elm St")
    db.add_all([company1, company2])
    db.commit()

    db.execute(user_company.insert().values(user_id=user1.id, company_id=company1.id, role="admin"))
    db.execute(user_company.insert().values(user_id=user2.id, company_id=company2.id, role="admin"))
    db.commit()

    return {"users": [user1, user2], "companies": [company1, company2]}

@pytest.fixture
def admin_user_and_token(client: TestClient, db: Session, seed_data):
    admin_user = db.query(User).filter(User.email == "johanguse@gmail.com").first()
    company = db.query(Company).filter(Company.name == "Oil Corp").first()

    response = client.post(
        "/api/v1/token",
        data={"username": admin_user.email, "password": "mE8eAazZ28xmmHG$"},
    )
    tokens = response.json()
    return admin_user, company, tokens["access_token"]

def test_register_user(client: TestClient, admin_user_and_token, db: Session):
    admin_user, company, access_token = admin_user_and_token
    
    response = client.post(
        "/api/v1/register",
        json={
            "email": "newuser@example.com",
            "password": "newuserpassword",
            "name": "New User",
            "role": "user",
            "company_id": company.id
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "id" in data

def test_login_for_access_token(client: TestClient, seed_data):
    response = client.post(
        "/api/v1/token",
        data={"username": "johanguse@gmail.com", "password": "mE8eAazZ28xmmHG$"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_with_incorrect_credentials(client: TestClient):
    response = client.post(
        "/api/v1/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_refresh_token_flow(client: TestClient, db: Session, seed_data):
    login_response = client.post(
        "/api/v1/token",
        data={"username": "johanguse@gmail.com", "password": "mE8eAazZ28xmmHG$"},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    
    login_data = login_response.json()
    assert "access_token" in login_data, "No access token in login response"
    assert "refresh_token" in login_data, "No refresh token in login response"
    
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    refresh_response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"Refresh token response status: {refresh_response.status_code}")
    print(f"Refresh token response body: {refresh_response.json()}")

    assert refresh_response.status_code == 200, f"Refresh token failed: {refresh_response.json()}"
    
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data, "No new access token in refresh response"
    assert "refresh_token" in refresh_data, "No new refresh token in refresh response"

    assert refresh_data["access_token"] != access_token, "New access token is the same as the old one"
    assert refresh_data["refresh_token"] != refresh_token, "New refresh token is the same as the old one"

    second_refresh_response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert second_refresh_response.status_code == 401, "Old refresh token was accepted"
    assert second_refresh_response.json()["detail"] == "Could not validate refresh token"


def test_refresh_token_with_invalid_token(client: TestClient, seed_data):
    login_response = client.post(
        "/api/v1/token",
        data={"username": "johanguse@gmail.com", "password": "mE8eAazZ28xmmHG$"},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": "invalid_token"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"

def test_refresh_token_with_expired_token(client: TestClient, db: Session, seed_data):
    login_response = client.post(
        "/api/v1/token",
        data={"username": "johanguse@gmail.com", "password": "mE8eAazZ28xmmHG$"},
    )
    access_token = login_response.json()["access_token"]

    user = db.query(User).filter(User.email == "johanguse@gmail.com").first()
    expired_token = create_refresh_token(
        user.email,
        expires_delta=timedelta(seconds=-1)
    )
    
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": expired_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"

