import pytest
from app.routes import PASSWORD
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/test_connection", params={"password": PASSWORD})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data