import json

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL
)
from app.schemas.summary import ShipmentRisk


async def chat(
    messages: list[dict],
    team_id: str,
    end_user_id: str
) -> str:
    if not LLM_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="LLM_API_KEY or OPENAI_API_KEY is not configured"
        )

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 300,
        "metadata": {
            "team_id": team_id,
            "end_user_id": end_user_id
        }
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
        "team_id": team_id,
        "end_user_id": end_user_id
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM call failed: {exc}"
        ) from exc

    data = response.json()

    return data["choices"][0]["message"]["content"]


async def summarize_text(
    text: str,
    team_id: str,
    end_user_id: str
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You summarize logistics text clearly "
                "in 2 short sentences."
            )
        },
        {
            "role": "user",
            "content": text
        }
    ]

    return await chat(messages, team_id, end_user_id)


async def analyze_shipment(
    name: str,
    status: str,
    team_id: str,
    end_user_id: str
) -> ShipmentRisk:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a shipment audit assistant. "
                "Return ONLY valid JSON. Do not include markdown. "
                "Do not include explanations outside JSON. "
                "The JSON must exactly match this shape: "
                '{"risk_level":"low|medium|high","reasons":["reason 1"],"summary":"short summary"}'
            )
        },
        {
            "role": "user",
            "content": (
                f"Analyze this shipment. "
                f"Shipment name: {name}. "
                f"Current status: {status}."
            )
        }
    ]

    content = await chat(messages, team_id, end_user_id)

    cleaned_content = content.strip()

    if cleaned_content.startswith("```json"):
        cleaned_content = cleaned_content.replace("```json", "", 1).strip()

    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.replace("```", "", 1).strip()

    if cleaned_content.endswith("```"):
        cleaned_content = cleaned_content[:-3].strip()

    try:
        return ShipmentRisk.model_validate(
            json.loads(cleaned_content)
        )

    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned invalid structured JSON: {content}"
        ) from exc