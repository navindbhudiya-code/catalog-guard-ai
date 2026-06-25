"""Similarity index abstraction for duplicate detection (R-DUP).

``InMemorySimilarityIndex`` is a dependency-free token-cosine index used by
default and in tests, so duplicate detection works out of the box. A ChromaDB
embedding-backed index (``[llm]`` extra) is the production upgrade — see
``docs/decisions/ADR-002``.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol, runtime_checkable

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> Counter[str]:
    return Counter(_TOKEN.findall(text.lower()))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return dot / norm if norm else 0.0


@runtime_checkable
class SimilarityIndex(Protocol):
    """Minimal vector-store surface the DuplicateAgent depends on."""

    def add(self, doc_id: str, text: str) -> None: ...

    def query(self, text: str, k: int) -> list[tuple[str, float]]: ...


class InMemorySimilarityIndex:
    """Token-cosine similarity index — deterministic, no external services."""

    def __init__(self) -> None:
        self._docs: dict[str, Counter[str]] = {}

    def add(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = _tokenize(text)

    def query(self, text: str, k: int) -> list[tuple[str, float]]:
        query_vec = _tokenize(text)
        scored = [(doc_id, _cosine(query_vec, vec)) for doc_id, vec in self._docs.items()]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]
