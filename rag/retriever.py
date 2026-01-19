from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List
import numpy as np
from rag.embeddings import EmbeddingsClient
from rag.index import VectorIndex


@dataclass(frozen=True)
class RetrievalResult:
    score: float
    chunk_id: str
    text: str
    metadata: dict[str, Any]


class Retriever:
    def __init__(self, index: VectorIndex, embedder: EmbeddingsClient) -> None:
        if index.model != embedder.model:
            raise ValueError(f'Модель для векторизации базы знаний != модели векторизации запроса: {index.model} vs {embedder.model}')

        self._index = index
        self._embedder = embedder

    def retrieve(self, query: str, top_k: int = 6) -> list[RetrievalResult]:
        k = int(top_k)
        if k <= 0:
            return []

        q_vec = np.array(self._embedder.embed_query(query), dtype=np.float32)
        if q_vec.ndim != 1:
            raise ValueError('Query embedding must be 1D')

        q_norm = float(np.linalg.norm(q_vec))
        if q_norm == 0.0:
            q_norm = 1.0
        q_vec = q_vec / q_norm

        scores = self._index.vectors @ q_vec
        n = int(scores.shape[0])
        if n == 0:
            return []

        k_eff = min(k, n)

        top_idx = np.argpartition(-scores, kth=k_eff - 1)[:k_eff]
        top_idx = top_idx[np.argsort(-scores[top_idx])]

        out: List[RetrievalResult] = []
        for i in top_idx.tolist():
            item = self._index.items[i]
            out.append(
                RetrievalResult(
                    score=float(scores[i]),
                    chunk_id=str(item.get('id')),
                    text=str(item.get('text')),
                    metadata=item.get('metadata') if isinstance(item.get('metadata'), dict) else {},
                )
            )

        return out

    def retrieve_context(self, query: str, top_k: int = 6) -> str:
        hits = self.retrieve(query, top_k=top_k)
        if not hits:
            return ''

        parts: list[str] = []
        for h in hits:
            parts.append(f'[chunk_id={h.chunk_id}]\n{h.text}'.strip())

        return '\n\n---\n\n'.join(parts)
