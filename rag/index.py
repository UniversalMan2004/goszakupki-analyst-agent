from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, List
import numpy as np


@dataclass
class VectorIndex:
    vectors: np.ndarray
    items: List[dict[str, Any]]
    model: str

    def save(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)

        np.savez_compressed(
            os.path.join(dir_path, 'vectors.npz'),
            vectors=self.vectors.astype(np.float32),
        )

        meta = {
            'model': self.model,
            'size': int(self.vectors.shape[0]),
            'dim': int(self.vectors.shape[1]),
            'items': self.items,
        }
        with open(os.path.join(dir_path, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, dir_path: str) -> VectorIndex:
        vec_path = os.path.join(dir_path, 'vectors.npz')
        meta_path = os.path.join(dir_path, 'meta.json')

        if not os.path.exists(vec_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(f'Файлы не найдены по этому пути: {dir_path}')

        data = np.load(vec_path)
        vectors = data['vectors'].astype(np.float32)

        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        model = meta.get('model')
        items = meta.get('items')
        if not isinstance(model, str) or not isinstance(items, list):
            raise ValueError('Неправильный meta.json')

        return cls(vectors=vectors, items=items, model=model)


def build_vector_index(items: List[dict[str, Any]], vectors: List[list[float]], model: str) -> VectorIndex:
    if len(items) != len(vectors):
        raise ValueError('Кол-во chunks и векторов должно быть одинаковым')

    mat = np.array(vectors, dtype=np.float32)
    if mat.ndim != 2 or mat.shape[0] == 0:
        raise ValueError('Должны быть не ненулевые 2D матрицы')

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    mat = mat / norms

    return VectorIndex(vectors=mat.astype(np.float32), items=items, model=model)
