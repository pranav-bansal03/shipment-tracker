from enum import Enum

from sqlmodel import SQLModel, Field


class Status(str, Enum):
    placed = "placed"
    shipped = "shipped"
    delivered = "delivered"


class Shipment(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True
    )

    name: str

    status: Status