from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

async def create_test_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_test_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)