import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from jose import jwt
import time
from datetime import timedelta

from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_refresh_token
from app.core.config import settings
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

def test_refresh_token_with_expired_token(client, user):
    expired_token = create_refresh_token(
        user.email,
        expires_delta=timedelta(seconds=-1)
    )
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": expired_token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"

def test_refresh_token_with_non_existent_user(client, db):
    non_existent_user_token = create_refresh_token("non_existent@example.com")
    response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": non_existent_user_token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"

def test_access_token_expiration(client, user):
    response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    access_token = response.json()["access_token"]
    
    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp = payload.get("exp")

    expected_exp = int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert abs(exp - expected_exp) < 5

def test_refresh_token_rotation(client, user):
    login_response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    initial_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": initial_refresh_token},
    )
    assert refresh_response.status_code == 200
    new_refresh_token = refresh_response.json()["refresh_token"]

    assert initial_refresh_token != new_refresh_token

    second_refresh_response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": initial_refresh_token},
    )
    assert second_refresh_response.status_code == 401
    assert second_refresh_response.json()["detail"] == "Could not validate refresh token"

    third_refresh_response = client.post(
        "/api/v1/refresh_token",
        json={"refresh_token": new_refresh_token},
    )
    assert third_refresh_response.status_code == 200

