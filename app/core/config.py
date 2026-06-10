import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///shipments.db")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    os.getenv("OPENAI_API_KEY")
)

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

