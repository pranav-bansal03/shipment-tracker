from fastapi import FastAPI
from sqlmodel import SQLModel

from app.db.session import engine
from app.middleware.logging import LoggingMiddleware
from app.routers.shipments import router as shipments_router
from app.routers.summary import router as summary_router
from app.routers.agent import router as agent_router

app = FastAPI(
    title="Shipment Tracker API",
    description=(
        "Internship Day 5 API with shipment CRUD, "
        "LLM summary integration, tests, and polished docs."
    ),
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Shipments",
            "description": "Create, view, update, and delete shipments."
        },
        {
            "name": "AI Summary",
            "description": "LLM-powered text and shipment risk summaries."
        }
    ]
)

app.add_middleware(LoggingMiddleware)

app.include_router(shipments_router)
app.include_router(summary_router)
app.include_router(agent_router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)