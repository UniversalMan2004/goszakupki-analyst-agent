from __future__ import annotations
import os
from rag.embeddings import EmbeddingsClient
from rag.index import VectorIndex, build_vector_index
from rag.knowledge_base import KNOWLEDGE_BASE


def kb_index_exists(dir_path: str) -> bool:
    vec_path = os.path.join(dir_path, 'vectors.npz')
    meta_path = os.path.join(dir_path, 'meta.json')
    return os.path.exists(vec_path) and os.path.exists(meta_path)


def get_or_build_kb_index(dir_path: str, embedder: EmbeddingsClient) -> VectorIndex:
    if kb_index_exists(dir_path):
        return VectorIndex.load(dir_path)

    items = KNOWLEDGE_BASE
    texts = [item['text'].strip() for item in items]

    for i, t in enumerate(texts):
        if not t:
            raise ValueError(f'Пустой chunk по индексу={i}')

    vectors = embedder.embed_texts(texts)
    index = build_vector_index(items=items, vectors=vectors, model=embedder.model)

    index.save(dir_path)
    return index
