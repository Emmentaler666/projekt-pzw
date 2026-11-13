import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.db import Base, get_db
from app.main import app
from app.models import Equipment, User
from tests.helpers import PASSWORD, auth_headers

TEST_DB_URL = settings.database_url.rsplit("/", 1)[0] + "/posudba_test"
assert TEST_DB_URL.endswith("/posudba_test")

engine = create_engine(TEST_DB_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)
PASSWORD_HASH = hash_password(PASSWORD)


def override_get_db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestingSession() as session:
        session.add_all(
            [
                User(username="admin", password_hash=PASSWORD_HASH, role="admin"),
                User(username="student1", password_hash=PASSWORD_HASH, role="student"),
                User(username="student2", password_hash=PASSWORD_HASH, role="student"),
                Equipment(name="Laptop", inventory_number="T-001"),
                Equipment(name="Projektor", inventory_number="T-002"),
                Equipment(name="Kamera", inventory_number="T-003"),
                Equipment(name="Arduino", inventory_number="T-004"),
            ]
        )
        session.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_h(client):
    return auth_headers(client, "admin")


@pytest.fixture
def student1_h(client):
    return auth_headers(client, "student1")


@pytest.fixture
def student2_h(client):
    return auth_headers(client, "student2")