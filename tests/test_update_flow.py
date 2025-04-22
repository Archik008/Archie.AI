import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_update_flow(client: AsyncClient):
    set_response = await client.post("/set_updated", json={"is_updated": True})
    assert set_response.status_code == 200
    assert set_response.json().get("ok") is True

    get_response = await client.get("/need_update")
    assert get_response.status_code == 200
    data = get_response.json()
    assert "updated" in data
    assert data["updated"] is True