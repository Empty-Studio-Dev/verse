import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from app.main import app
from database.database import Base, get_db

# making ARRAY compatible with SQLite
from sqlalchemy import ARRAY as GenericARRAY
from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY

@compiles(GenericARRAY, "sqlite")
def _compile_generic_array_sqlite(element, compiler, **kw):
    return "JSON"

@compiles(PGARRAY, "sqlite")
def _compile_pg_array_sqlite(element, compiler, **kw):
    return "JSON"

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    user_data = {
        "name": "Vlad",
        "email": "test@example.com",
        "password": "TestPass123!",
    }
    res = client.post("/users", json=user_data)
    assert res.status_code == 201
    return {**res.json(), "password": user_data["password"]}