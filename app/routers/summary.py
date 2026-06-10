from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback import run_feedback_flow

from app.schemas.summary import (
    ShipmentRisk,
    ShipmentSummaryRequest,
    TextSummaryRequest,
    TextSummaryResponse
)
from app.services import llm, shipment_service
from app.services.dependencies import get_shipment_service

router = APIRouter(
    prefix="",
    tags=["AI Summary"]
)


@router.post(
    "/summarize",
    response_model=TextSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Summarize text with an LLM",
    description=(
        "Sends plain text to the isolated LLM service "
        "and returns a short summary."
    )
)
async def summarize_text(request: TextSummaryRequest):
    summary = await llm.summarize_text(
        request.text,
        request.team_id,
        request.end_user_id
    )

    return TextSummaryResponse(summary=summary)


@router.post(
    "/shipments/{shipment_id}/summarize",
    response_model=ShipmentRisk,
    status_code=status.HTTP_200_OK,
    summary="Analyze shipment risk with an LLM",
    description=(
        "Loads one shipment, asks the LLM for structured JSON, "
        "and validates it with Pydantic."
    )
)
async def summarize_shipment(
    shipment_id: int,
    request: ShipmentSummaryRequest,
    session: AsyncSession = Depends(get_shipment_service)
):
    shipment = await shipment_service.get_shipment(
        shipment_id,
        session
    )

    return await llm.analyze_shipment(
        shipment.name,
        shipment.status.value,
        request.team_id,
        request.end_user_id
    )


@router.post(
    "/feedback/analyze",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze query using a LangGraph workflow",
    description=(
        "Sends a query through a LangGraph workflow that classifies it "
        "as a complaint or a question and handles it accordingly."
    )
)
async def analyze_feedback(request: FeedbackRequest):
    # Run the compiled LangGraph flow
    final_state = await run_feedback_flow(
        request.query,
        request.team_id,
        request.end_user_id
    )

    # Return the classification and final response from state
    return FeedbackResponse(
        classification=final_state["classification"],
        response=final_state["response"]
    )