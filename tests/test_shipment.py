import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.summary import ShipmentRisk
from app.services import llm

client = TestClient(app)


def test_create_shipment():
    response = client.post(
        "/shipments",
        json={
            "name": "Box 1",
            "status": "placed"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Box 1"


def test_get_shipments():
    client.post(
        "/shipments",
        json={
            "name": "Box 2",
            "status": "shipped"
        }
    )

    response = client.get("/shipments")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_shipment():
    created = client.post(
        "/shipments",
        json={
            "name": "Box 3",
            "status": "placed"
        }
    ).json()

    response = client.patch(
        f"/shipments/{created['id']}",
        json={
            "status": "delivered"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "delivered"


@pytest.mark.asyncio
async def test_async_get_missing_shipment():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as async_client:
        response = await async_client.get(
            "/shipments/999999"
        )

    assert response.status_code == 404


def test_llm_structured_endpoint(monkeypatch):
    async def fake_analyze_shipment(
        name,
        status,
        team_id,
        end_user_id
    ):
        return ShipmentRisk(
            risk_level="low",
            reasons=[
                "Shipment is already moving through the normal flow."
            ],
            summary=f"{name} is currently {status}."
        )

    monkeypatch.setattr(
        llm,
        "analyze_shipment",
        fake_analyze_shipment
    )

    created = client.post(
        "/shipments",
        json={
            "name": "Box 4",
            "status": "shipped"
        }
    ).json()

    response = client.post(
        f"/shipments/{created['id']}/summarize",
        json={
            "team_id": "internship-team",
            "end_user_id": "prana"
        }
    )

    assert response.status_code == 200
    assert response.json()["risk_level"] == "low"