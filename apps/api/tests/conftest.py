import os
from collections.abc import Generator

os.environ["DATABASE_URL"] = "sqlite:///./vendorbridge.test.db"
os.environ["SECRET_KEY"] = "test-secret-key-with-enough-length"
os.environ["REDIS_URL"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import entities  # noqa: F401,E402

engine = create_engine(
    "sqlite:///./vendorbridge.test.db", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_test_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client() -> TestClient:
    return TestClient(app)
