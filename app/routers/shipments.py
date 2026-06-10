from fastapi import APIRouter, Depends
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentRead
)
from app.services import shipment_service
from app.services.dependencies import get_shipment_service

router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"]
)


@router.post(
    "",
    response_model=ShipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create shipment",
    description="Creates a shipment with a name and status."
)
async def create_shipment(
    shipment: ShipmentCreate,
    session: AsyncSession = Depends(get_shipment_service)
):
    return await shipment_service.create_shipment(shipment, session)


@router.get(
    "",
    response_model=list[ShipmentRead],
    summary="List shipments",
    description="Returns all saved shipments."
)
async def get_shipments(
    session: AsyncSession = Depends(get_shipment_service)
):
    return await shipment_service.get_shipments(session)


@router.get(
    "/{shipment_id}",
    response_model=ShipmentRead,
    summary="Get shipment",
    description="Returns one shipment by id."
)
async def get_shipment(
    shipment_id: int,
    session: AsyncSession = Depends(get_shipment_service)
):
    return await shipment_service.get_shipment(shipment_id, session)


@router.patch(
    "/{shipment_id}",
    response_model=ShipmentRead,
    summary="Update shipment",
    description="Updates shipment name, status, or both."
)
async def update_shipment(
    shipment_id: int,
    shipment: ShipmentUpdate,
    session: AsyncSession = Depends(get_shipment_service)
):
    return await shipment_service.update_shipment(
        shipment_id,
        shipment,
        session
    )


@router.delete(
    "/{shipment_id}",
    summary="Delete shipment",
    description="Deletes one shipment by id."
)
async def delete_shipment(
    shipment_id: int,
    session: AsyncSession = Depends(get_shipment_service)
):
    return await shipment_service.delete_shipment(shipment_id, session)