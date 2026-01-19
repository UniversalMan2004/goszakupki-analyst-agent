from __future__ import annotations
from typing import List
import os
from dataclasses import dataclass
from openai import OpenAI

@dataclass(frozen=True)
class EmbeddingConfig:
    model: str = 'text-embedding-3-small'
    batch_size: int = 128


class EmbeddingsClient:
    def __init__(self, api_key: str | None = None, config: EmbeddingConfig | None = None) -> None:
        api_key_f = api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key_f:
            raise RuntimeError('Не установлен OPENAI_API_KEY')

        self._client = OpenAI(api_key=api_key_f)
        self._config = config or EmbeddingConfig()

    @property
    def model(self) -> str:
        return self._config.model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        vectors: List[List[float]] = []
        bs = max(1, self._config.batch_size)
        for i in range(0, len(texts), bs):
            batch = texts[i: i+bs]
            batch = [t.strip() for t in batch]
            for t in batch:
                if not t:
                    raise ValueError('Нельзя получить embedding для пустой строки')

            result = self._client.embeddings.create(
                model=self._config.model,
                input=batch
            )
            vectors.extend([row.embedding for row in result.data])

        return vectors


    def embed_query(self, query: str) -> List[float]:
        q = (query or '').strip()
        if not q:
            raise ValueError('Пустой запрос')
        return self.embed_texts([q])[0]