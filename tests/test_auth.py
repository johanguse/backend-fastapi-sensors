import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash
from tests.factories import UserFactory

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
def user(db):
    user = UserFactory(hashed_password=get_password_hash("testpassword"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_register_user(client):
    response = client.post(
        "/api/v1/register",
        json={"email": "test@example.com", "password": "testpassword", "name": "Test User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data

def test_register_existing_user(client, user):
    response = client.post(
        "/api/v1/register",
        json={"email": user.email, "password": "testpassword", "name": "Existing User"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_for_access_token(client, user):
    response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_with_incorrect_credentials(client):
    response = client.post(
        "/api/v1/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_refresh_token(client, user):
    login_response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    refresh_token = login_response.json()["refresh_token"]
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_with_invalid_token(client):
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": "invalid_token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"


def test_refresh_token_with_invalid_token(client):
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": "invalid_token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"
