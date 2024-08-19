import pytest
import logging
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash
from tests.factories import UserFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Created test user: {user.email}")
    return user

@pytest.fixture
def other_user(db):
    user = UserFactory(hashed_password=get_password_hash("testpassword"))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created other test user: {user.email}")
    return user

@pytest.fixture
def token(client, user):
    response = client.post(
        "/api/v1/token",
        data={"username": user.email, "password": "testpassword"},
    )
    if response.status_code != 200:
        logger.error(f"Failed to obtain token. Status code: {response.status_code}")
        logger.error(f"Response content: {response.content}")
        pytest.fail(f"Failed to obtain token. Status code: {response.status_code}, Response: {response.text}")
    
    data = response.json()
    if "access_token" not in data:
        logger.error(f"No access token in response. Response data: {data}")
        pytest.fail(f"No access token in response. Response data: {data}")
    
    logger.info("Successfully obtained access token")
    return data["access_token"]