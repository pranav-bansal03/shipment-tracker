import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import llm

client = TestClient(app)


def test_feedback_complaint_routing(monkeypatch):
    # 1. Mock the LLM classification node to return 'complaint'
    async def fake_classify_query(query, team_id, end_user_id):
        return "complaint"

    # 2. Mock the LLM complaint handler node
    async def fake_generate_complaint_response(query, team_id, end_user_id):
        return "We apologize for the issues with the audit process. We will investigate this immediately."

    monkeypatch.setattr(llm, "classify_query", fake_classify_query)
    monkeypatch.setattr(llm, "generate_complaint_response", fake_generate_complaint_response)

    # 3. Request
    response = client.post(
        "/feedback/analyze",
        json={
            "query": "The audit process was delayed and unprofessional.",
            "team_id": "internship-team",
            "end_user_id": "prana"
        }
    )

    # 4. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "complaint"
    assert "apologize" in data["response"]


def test_feedback_question_routing(monkeypatch):
    # 1. Mock the LLM classification node to return 'question'
    async def fake_classify_query(query, team_id, end_user_id):
        return "question"

    # 2. Mock the LLM question handler node
    async def fake_generate_question_response(query, team_id, end_user_id):
        return "You will need to provide your financial ledgers and vendor invoices."

    monkeypatch.setattr(llm, "classify_query", fake_classify_query)
    monkeypatch.setattr(llm, "generate_question_response", fake_generate_question_response)

    # 3. Request
    response = client.post(
        "/feedback/analyze",
        json={
            "query": "What documents do we need to prepare for the audit?",
            "team_id": "internship-team",
            "end_user_id": "prana"
        }
    )

    # 4. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "question"
    assert "financial ledgers" in data["response"]