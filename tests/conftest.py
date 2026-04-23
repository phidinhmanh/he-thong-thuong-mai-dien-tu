import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.models import Base, User, UserRole
from app.core.database import get_db
from app.core.search import setup_fts
from app.core.security import create_access_token
from main import app
from httpx import AsyncClient, ASGITransport

# Use a separate test database (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup FTS after tables are created
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await setup_fts(session)
        await session.close()

    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

import uuid

@pytest.fixture
async def admin_user(db_session):
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"admin_{unique_id}@test.com",
        username=f"admin_{unique_id}",
        hashed_password="hashed_password",
        role=UserRole.ADMIN.value
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def admin_client(client, admin_user):
    token = create_access_token(data={"sub": admin_user.username, "user_id": admin_user.id})
    client.headers["Authorization"] = f"Bearer {token}"
    return client
