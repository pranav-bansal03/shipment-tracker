from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query: str = Field(
        ...,
        examples=["The auditor did not verify the invoice list and was very unprofessional."]
    )
    team_id: str = Field(..., examples=["internship-team"])
    end_user_id: str = Field(..., examples=["prana"])


class FeedbackResponse(BaseModel):
    classification: str = Field(..., examples=["complaint", "question"])
    response: str = Field(..., examples=["We apologize for the inconvenience..."])