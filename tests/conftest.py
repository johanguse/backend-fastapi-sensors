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

@pytest.fixture
def other_user(db):
    user = UserFactory(hashed_password=get_password_hash("testpassword"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def token(client, user):
    response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    return response.json()["access_token"]