import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

from app.main import app
from app.services import agent
from app.models.shipment import Shipment, Status
from app.db.session import AsyncSessionLocal

client = TestClient(app)

@pytest.mark.asyncio
async def test_agent_get_shipment_status(monkeypatch):
    # 1. Seed the DB with a test shipment
    async with AsyncSessionLocal() as session:
        test_shipment = Shipment(name="Urgent Box", status=Status.placed)
        session.add(test_shipment)
        await session.commit()
        await session.refresh(test_shipment)
        shipment_id = test_shipment.id

    # 2. Mock model responses
    # Turn 1: Model requests a tool call to get shipment status
    response_1 = AIMessage(
        content="",
        tool_calls=[{
            "name": "get_shipment_status",
            "args": {"shipment_id": shipment_id},
            "id": "call_1",
            "type": "tool_call"
        }]
    )
    # Turn 2: Model reads the tool result and answers in plain text
    response_2 = AIMessage(
        content=f"Shipment 'Urgent Box' (ID: {shipment_id}) is in placed status."
    )

    call_count = 0
    async def mock_ainvoke(self, messages, stop=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return response_1
        return response_2

    # Patch the model's invoke function
    monkeypatch.setattr("langchain_openai.ChatOpenAI.ainvoke", mock_ainvoke)

    # 3. Call the API
    response = client.post(
        "/agent/chat",
        json={
            "message": f"What is the status of shipment {shipment_id}?",
            "thread_id": "test-thread-1",
            "team_id": "test-team",
            "end_user_id": "test-user"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "placed" in data["response"]
    assert data["history"][1]["role"] == "assistant"
    # Verify that the tool was successfully called
    assert any(h["role"] == "tool" and "Urgent Box" in h["content"] for h in data["history"])


@pytest.mark.asyncio
async def test_agent_memory_persistence(monkeypatch):
    # Verify that thread_id maintains history across multiple turns.
    call_count = 0
    
    async def mock_ainvoke(self, messages, stop=None, **kwargs):
        nonlocal call_count
        call_count += 1
        # Simply echo memory length to check if history exists
        history_len = len(messages)
        return AIMessage(content=f"History length is {history_len}")

    monkeypatch.setattr("langchain_openai.ChatOpenAI.ainvoke", mock_ainvoke)

    # Turn 1
    client.post(
        "/agent/chat",
        json={
            "message": "Hello!",
            "thread_id": "thread-memory-1",
            "team_id": "test-team",
            "end_user_id": "test-user"
        }
    )

    # Turn 2 (with same thread_id)
    response_turn2 = client.post(
        "/agent/chat",
        json={
            "message": "How are you?",
            "thread_id": "thread-memory-1",
            "team_id": "test-team",
            "end_user_id": "test-user"
        }
    )

    # Output message history should include: Turn 1 User, Turn 1 Assistant, and Turn 2 User
    # Therefore, Turn 2 receives 3 messages in its context history
    assert "History length is 3" in response_turn2.json()["response"]


@pytest.mark.asyncio
async def test_agent_max_step_guard(monkeypatch):
    # Mock LLM to return tool calls continuously (infinite loop condition)
    async def mock_ainvoke(self, messages, stop=None, **kwargs):
        return AIMessage(
            content="",
            tool_calls=[{
                "name": "list_delayed_shipments",
                "args": {},
                "id": "loop_call",
                "type": "tool_call"
            }]
        )

    monkeypatch.setattr("langchain_openai.ChatOpenAI.ainvoke", mock_ainvoke)

    response = client.post(
        "/agent/chat",
        json={
            "message": "List all delayed shipments.",
            "thread_id": "loop-thread-1",
            "team_id": "test-team",
            "end_user_id": "test-user"
        }
    )

    # The max step cap (steps >= 5) prevents it from executing forever
    assert response.status_code == 200