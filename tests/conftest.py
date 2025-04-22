import pytest_asyncio
from tests.test_database import create_test_database, drop_test_database
from httpx import ASGITransport, AsyncClient
from configure.pyconfig import MODE

if MODE == "DEV":
    from dev.dev_main import app
elif MODE == "PROD":
    from app.main import app
else:
    raise Exception("Неизвестный параметр в pyconfig(MODE)")

from database.database import get_db
from tests.test_database import override_get_db

TEST_INIT_DATA = "query_id=AAGgWik8AAAAAKBaKTxyylx5&user=%7B%22id%22%3A1009343136%2C%22first_name%22%3A%22%D0%90%D1%80%D1%82%D0%B5%D0%BC%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22ChristMyLife2008%22%2C%22language_code%22%3A%22ru%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FkU0kiOartWDErtP4oO7VwnNA8yJaO3bJcoGf_DiYuPw.svg%22%7D&auth_date=1745303756&signature=-Hr1Td7P0io1N2Cdp5GV5E-i7Omuv8k2FSIBmxTBXOviCLM5KXEBM9d81XQ3OD49OFKNzUc9n85UV_6NNwRQBw&hash=420898a7c85fc1a143b8ed34ee01356926d975e315dcdc58b51dec2dbdab376c"

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
        ac.headers["init-data"] = TEST_INIT_DATA
        yield ac