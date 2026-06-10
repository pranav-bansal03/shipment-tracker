from pydantic import BaseModel, Field


class ShipmentSummaryRequest(BaseModel):
    team_id: str = Field(..., examples=["internship-team"])
    end_user_id: str = Field(..., examples=["prana"])


class ShipmentRisk(BaseModel):
    risk_level: str = Field(..., examples=["low", "medium", "high"])
    reasons: list[str]
    summary: str


class TextSummaryRequest(BaseModel):
    text: str
    team_id: str = Field(..., examples=["internship-team"])
    end_user_id: str = Field(..., examples=["prana"])


class TextSummaryResponse(BaseModel):
    summary: str