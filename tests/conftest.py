import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import os
from typing import Generator
from urllib.parse import quote_plus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.db import get_session
from app.main import app
from app.models import Accommodation, Address, FoodCost

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Ujjwal123@@")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("TEST_DB_NAME", "smart_travel_test")

TEST_DB_URL = f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(TEST_DB_URL, echo=False)


def override_get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(setup_db) -> Generator[Session, None, None]:
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session) -> Generator[TestClient, None, None]:
    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_addresses(session: Session) -> list[Address]:
    addrs = [
        Address(province="Bagmati", district="Kathmandu", place="Kathmandu", latitude=27.71, longitude=85.32, altitude=1400),
        Address(province="Gandaki", district="Kaski", place="Pokhara", latitude=28.20, longitude=83.98, altitude=822),
    ]
    session.add_all(addrs)
    session.commit()
    for a in addrs:
        session.refresh(a)
    return addrs


@pytest.fixture
def test_accommodation(session: Session) -> Accommodation:
    a = Accommodation(budget_price=10, standard_price=30, luxury_price=100)
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


@pytest.fixture
def test_food_cost(session: Session) -> FoodCost:
    f = FoodCost(budget_price=500, standard_price=1200, luxury_price=2500)
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@pytest.fixture
def admin_token(session: Session, client: TestClient) -> str:
    from app.core.auth import create_access_token
    from app.core.security import hash_password
    from app.models import User

    admin = User(
        name="Admin", email="admin@test.com", password=hash_password("admin123"),
        role="admin", nationality="Nepal", phone="+977-9800000001",
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return create_access_token({"sub": str(admin.id)})


@pytest.fixture
def user_token(session: Session, client: TestClient) -> str:
    from app.core.auth import create_access_token
    from app.core.security import hash_password
    from app.models import User

    user = User(
        name="User", email="user@test.com", password=hash_password("user123"),
        role="traveler", nationality="USA", phone="+977-9800000002",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return create_access_token({"sub": str(user.id)})


@pytest.fixture
def test_image() -> io.BytesIO:
    return io.BytesIO(b"fake-image-data-for-testing")
