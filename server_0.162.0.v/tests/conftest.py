import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from database.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _fk_on(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture
def db_engine():
    return _engine


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def login_headers(client, email: str, password: str = "TestPass123!") -> dict:
    r = client.post("/login", data={"username": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def test_user(client):
    data = {
        "name": "Vlad",
        "email": "test@example.com",
        "password": "TestPass123!",
    }
    r = client.post("/users", json=data)
    assert r.status_code == 201, r.text
    return {**r.json(), "password": data["password"]}


@pytest.fixture
def auth_headers(client, test_user):
    return login_headers(client, test_user["email"], test_user["password"])


@pytest.fixture
def owner(client, test_user, auth_headers):
    return {**test_user, "headers": auth_headers}


@pytest.fixture
def stranger(client):
    email = "stranger@example.com"
    r = client.post("/users", json={
        "name": "Stranger",
        "email": email,
        "password": "TestPass123!",
    })
    assert r.status_code == 201, r.text
    return {**r.json(), "headers": login_headers(client, email)}


@pytest.fixture
def post(client, owner):
    r = client.post("/posts", json={
        "title": "Seed post",
        "description": "Seed desc",
        "post_img": ["https://example.com/a.jpg"],
    }, headers=owner["headers"])
    assert r.status_code == 201, r.text
    return r.json()