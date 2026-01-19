from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentState:
    user_message: str
    subject_inn: str | None = None
    years: list[int] = None
    statuses: list[str] = None
    role: str | None = None
    route: str | None = None
    clarification_question: str | None = None
    api_raw: dict[str, Any] | None = None
    records: list[dict[str, Any]] | None = None
    metrics: dict[str, Any] | None = None
    rag_context: str | None = None
    answer: str | None = None
