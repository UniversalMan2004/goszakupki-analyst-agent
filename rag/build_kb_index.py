from __future__ import annotations
import os
from rag.embeddings import EmbeddingsClient
from rag.index import build_vector_index
from rag.knowledge_base import KNOWLEDGE_BASE


def main() -> None:
    out_dir = os.environ.get('RAG_INDEX_DIR') or 'rag/data/contracts_kb'

    embedder = EmbeddingsClient()

    items = KNOWLEDGE_BASE
    texts = [item['text'].strip() for item in items]

    for i, t in enumerate(texts):
        if not t:
            raise ValueError(f'Empty chunk text at index={i}')

    vectors = embedder.embed_texts(texts)

    index = build_vector_index(items=items, vectors=vectors, model=embedder.model)
    index.save(out_dir)

    print(f'OK: сохранили индексы в {out_dir} (chunks={len(items)} model={embedder.model})')


if __name__ == '__main__':
    main()
