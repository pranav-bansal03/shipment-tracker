from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session


async def get_shipment_service(
    session: AsyncSession = Depends(get_session)
):
    return session