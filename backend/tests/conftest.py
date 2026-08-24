import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.core.database import Base, get_db
from app.main import app

def register_verified_user(
    client,
    *,
    email: str,
    display_name: str,
    password: str,
):
    otp = "123456"

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value=otp,
    ), patch(
        "app.api.v1.auth.send_verification_email",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": display_name,
            },
        )

    assert register_response.status_code == 202

    verify_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": email,
            "otp": otp,
        },
    )

    assert verify_response.status_code == 201

    return verify_response.json()


@pytest.fixture
def register_verified_user_helper():
    return register_verified_user


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()