from __future__ import annotations
import re
from agent.state import AgentState
from rag.service import get_retriever


_INN_RE = re.compile(r'\b\d{10}\b|\b\d{12}\b')
_YEAR_RE = re.compile(r'\b(20\d{2})\b', re.IGNORECASE)


def _parse_inn(text: str) -> str | None:
    m = _INN_RE.search(text)
    return m.group(0) if m else None


def _parse_years(text: str) -> list[int]:
    years: list[int] = []
    for y in _YEAR_RE.findall(text):
        try:
            years.append(int(y))
        except ValueError:
            continue
    return sorted(set(years))


def _parse_role(text: str) -> str | None:
    t = text.lower()
    if 'заказчик' in t:
        return 'customer'
    if 'поставщик' in t:
        return 'supplier'
    return None


def _parse_statuses(text: str) -> list[str]:
    t = text.lower()
    statuses: list[str] = []
    if 'подача' in t and 'заяв' in t:
        statuses.append('Подача заявок')
    if 'комисс' in t:
        statuses.append('Работа комиссии')
    if 'заверш' in t:
        statuses.append('Закупка завершена')
    if 'отмен' in t:
        statuses.append('Закупка отменена')
    return statuses


def parse_query(state: AgentState) -> AgentState:
    text = state.user_message.strip()

    state.subject_inn = _parse_inn(text)
    state.years = _parse_years(text)
    state.role = _parse_role(text)
    state.statuses = _parse_statuses(text)

    return state


def route(state: AgentState) -> AgentState:
    t = state.user_message.lower()

    wants_numbers = any(
        k in t
        for k in [
            'сколько',
            'сумм',
            'объем',
            'объём',
            'динамик',
            'по год',
            'топ',
            'рейтинг',
            'распредел',
            'метрик',
            'контракт',
        ]
    )

    wants_explain = any(
        k in t
        for k in [
            'что такое',
            'почему',
            'как счита',
            'объясни',
            'чем отличается',
            'что значит',
            'правило',
        ]
    )

    needs_inn = wants_numbers or ('контракт' in t)
    if needs_inn and not state.subject_inn:
        state.route = 'clarify'
        state.clarification_question = 'Укажи ИНН (10 или 12 цифр), по которому смотреть контракты.'
        return state

    if wants_numbers and wants_explain:
        state.route = 'both'
        return state

    if wants_numbers:
        state.route = 'api'
        return state

    state.route = 'rag'
    return state


def clarify(state: AgentState) -> AgentState:
    state.answer = state.clarification_question or 'Уточни данные запроса.'
    return state


def api_call_contracts(state: AgentState) -> AgentState:
    # Заглушка: тут будет DamiaClient.get_contracts(...)
    state.api_raw = {}
    return state


def normalize_contracts(state: AgentState) -> AgentState:
    # Заглушка: тут будет нормализация format=1 -> records
    state.records = []
    return state


def compute_metrics(state: AgentState) -> AgentState:
    # Заглушка: тут будет compute_contracts_metrics(records, filters=...)
    state.metrics = {}
    return state


def retrieve_kb(state: AgentState) -> AgentState:
    retriever = get_retriever()

    hits = retriever.retrieve(state.user_message, top_k=6)
    state.rag_hits = [
        {
            'chunk_id': h.chunk_id,
            'score': h.score,
            'text': h.text,
            'metadata': h.metadata,
        }
        for h in hits
    ]

    state.rag_context = retriever.retrieve_context(state.user_message, top_k=6)
    return state


def generate_answer(state: AgentState) -> AgentState:
    # Заглушка (пока без OpenAI ключа). Позже будет gpt-4o-mini.
    parts: list[str] = []

    if state.route == 'clarify':
        state.answer = state.clarification_question or 'Уточни запрос.'
        return state

    parts.append('Черновик ответа (пока без генерации модели).')

    if state.metrics:
        parts.append('\nМетрики: (пока заглушка, подключим compute_contracts_metrics).')

    if state.rag_context:
        parts.append('\nКонтекст из базы знаний (для модели, не для пользователя):')
        parts.append(state.rag_context)

    state.answer = '\n'.join(parts).strip()
    return state


def route_selector(state: AgentState) -> str:
    return state.route or 'rag'
