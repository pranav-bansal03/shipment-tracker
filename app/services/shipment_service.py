from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.shipment import Shipment


async def create_shipment(
    shipment_data,
    session: AsyncSession
):
    shipment = Shipment(
        name=shipment_data.name,
        status=shipment_data.status
    )

    session.add(shipment)

    await session.commit()
    await session.refresh(shipment)

    return shipment


async def get_shipments(
    session: AsyncSession
):
    result = await session.execute(
        select(Shipment)
    )

    return result.scalars().all()


async def get_shipment(
    shipment_id: int,
    session: AsyncSession
):
    shipment = await session.get(
        Shipment,
        shipment_id
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    return shipment


async def update_shipment(
    shipment_id,
    shipment_data,
    session
):
    shipment = await session.get(
        Shipment,
        shipment_id
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    updates = shipment_data.model_dump(
        exclude_unset=True
    )

    for key, value in updates.items():
        setattr(shipment, key, value)

    await session.commit()
    await session.refresh(shipment)

    return shipment


async def delete_shipment(
    shipment_id,
    session
):
    shipment = await session.get(
        Shipment,
        shipment_id
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    await session.delete(shipment)
    await session.commit()

    return {
        "message": "Deleted"
    }