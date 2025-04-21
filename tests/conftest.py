import pytest_asyncio
from tests.test_database import create_test_database, drop_test_database
from httpx import ASGITransport 

from httpx import AsyncClient
from configure.pyconfig import MODE

if MODE == "DEV":
    from dev.dev_main import app
elif MODE == "PROD":
    from app.main import app
else:
    raise Exception("Неизвестный параметр в pyconfig(MODE)")

from database.database import get_db
from tests.test_database import override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    await create_test_database()
    yield
    await drop_test_database()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac