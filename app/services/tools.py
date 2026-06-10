from langchain_core.tools import tool
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.shipment import Shipment, Status

@tool
async def get_shipment_status(shipment_id: int) -> str:
    """Get the current status of a shipment by its ID.
    
    Args:
        shipment_id: The unique ID of the shipment.
    """
    # WHY: We open an asynchronous database session to query the DB directly.
    # HOW: Using AsyncSessionLocal to fetch the Shipment object by ID.
    async with AsyncSessionLocal() as session:
        shipment = await session.get(Shipment, shipment_id)
        if not shipment:
            return f"Shipment with ID {shipment_id} not found."
        return f"Shipment '{shipment.name}' (ID: {shipment.id}) status is '{shipment.status.value}'."

@tool
async def list_delayed_shipments() -> str:
    """List all delayed shipments. Shipments that are 'placed' or 'shipped' are considered delayed."""
    # WHY: We define "delayed" as any shipment that hasn't been delivered yet.
    # HOW: Querying the DB and filtering for status != Status.delivered.
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Shipment).where(Shipment.status != Status.delivered)
        )
        shipments = result.scalars().all()
        if not shipments:
            return "No delayed shipments found."
        
        lines = []
        for s in shipments:
            lines.append(f"- ID {s.id}: '{s.name}' (Status: {s.status.value})")
        return "Delayed shipments:\n" + "\n".join(lines)