from __future__ import annotations
from typing import Any
from langgraph.graph import END, StateGraph
from agent.state import AgentState
from agent.nodes import (
    api_call_contracts,
    clarify,
    compute_metrics,
    generate_answer,
    normalize_contracts,
    parse_query,
    retrieve_kb,
    route,
    route_selector,
)


def build_graph() -> Any:
    g = StateGraph(AgentState)
    g.add_node('parse_query', parse_query)
    g.add_node('route', route)
    g.add_node('clarify', clarify)
    g.add_node('api_call_contracts', api_call_contracts)
    g.add_node('normalize_contracts', normalize_contracts)
    g.add_node('compute_metrics', compute_metrics)
    g.add_node('retrieve_kb', retrieve_kb)
    g.add_node('generate_answer', generate_answer)
    g.set_entry_point('parse_query')
    g.add_edge('parse_query', 'route')
    g.add_conditional_edges(
        'route',
        route_selector,
        {
            'clarify': 'clarify',
            'api': 'api_call_contracts',
            'rag': 'retrieve_kb',
            'both': 'api_call_contracts',
        },
    )
    g.add_edge('clarify', END)
    g.add_edge('api_call_contracts', 'normalize_contracts')
    g.add_edge('normalize_contracts', 'compute_metrics')
    g.add_conditional_edges(
        'compute_metrics',
        route_selector,
        {
            'api': 'generate_answer',
            'both': 'retrieve_kb',
            'rag': 'retrieve_kb',
            'clarify': 'clarify',
        },
    )
    g.add_edge('retrieve_kb', 'generate_answer')
    g.add_edge('generate_answer', END)

    return g.compile()
