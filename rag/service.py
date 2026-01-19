from __future__ import annotations
from rag.config import RAG_INDEX_DIR
from rag.embeddings import EmbeddingsClient
from rag.kb_index_store import get_or_build_kb_index
from rag.retriever import Retriever


def get_retriever() -> Retriever:
    embedder = EmbeddingsClient()
    index = get_or_build_kb_index(RAG_INDEX_DIR, embedder=embedder)
    return Retriever(index=index, embedder=embedder)


