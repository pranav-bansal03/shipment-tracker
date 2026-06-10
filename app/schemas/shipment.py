from pydantic import BaseModel
from typing import Optional

from app.models.shipment import Status


class ShipmentCreate(BaseModel):
    name: str
    status: Status


class ShipmentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Status] = None


class ShipmentRead(BaseModel):
    id: int
    name: str
    status: Status