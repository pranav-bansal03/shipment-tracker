"""MCP Server for Shipment Tracker
========================================
A thin MCP layer over the existing Day-4 service functions.
Supports both stdio and HTTP (SSE) transports.
"""

import sys
import asyncio
import json

from fastmcp import FastMCP
from sqlmodel import SQLModel

# ── reuse existing project internals ──
# ── reuse existing project internals ──
from app.db.session import engine, AsyncSessionLocal
from app.services.shipment_service import get_shipment, get_shipments

# Silence SQL logs — they corrupt the MCP stdio protocol
engine.echo = False

# ── Create the MCP server ──
mcp = FastMCP("Shipment Tracker")

# ──────────────────────────────────────
#  DB bootstrap (same as main.py startup)
# ──────────────────────────────────────
async def _init_db():
    """Create tables if they don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# ──────────────────────────────────────
#  TOOL 1 — get_shipment_status
# ──────────────────────────────────────
@mcp.tool()
async def get_shipment_status(id: int) -> str:
    """
    Get the current status of a shipment by its ID.
    Returns the shipment name and status.
    """
    await _init_db()
    async with AsyncSessionLocal() as session:
        shipment = await get_shipment(id, session)
        return json.dumps({
            "id": shipment.id,
            "name": shipment.name,
            "status": shipment.status.value
        })


# ──────────────────────────────────────
#  TOOL 2 — list_delayed_shipments
# ──────────────────────────────────────
@mcp.tool()
async def list_delayed_shipments() -> str:
    """
    List all shipments that are still in 'placed' status
    (i.e. not yet shipped or delivered — considered delayed).
    """
    await _init_db()
    async with AsyncSessionLocal() as session:
        all_shipments = await get_shipments(session)
        delayed = [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status.value
            }
            for s in all_shipments
            if s.status.value == "placed"
        ]
        return json.dumps(delayed)


# ──────────────────────────────────────
#  RESOURCE — shipment://{id}
# ──────────────────────────────────────
@mcp.resource("shipment://{id}")
async def get_shipment_resource(id: int) -> str:
    """
    Read-only resource returning the full shipment record.
    Access via URI: shipment://1, shipment://2, etc.
    """
    await _init_db()
    async with AsyncSessionLocal() as session:
        shipment = await get_shipment(id, session)
        return json.dumps({
            "id": shipment.id,
            "name": shipment.name,
            "status": shipment.status.value
        })


# ──────────────────────────────────────
#  Entry point — stdio or sse
# ──────────────────────────────────────
if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"

    # Only print to stderr — stdout is reserved for MCP protocol
    import sys as _sys
    print(f"Starting MCP server with transport: {transport}", file=_sys.stderr)

    mcp.run(transport=transport)