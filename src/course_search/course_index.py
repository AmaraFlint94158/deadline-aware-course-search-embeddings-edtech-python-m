"""Domain index for course delivery, deadlines, and educator reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import sqrt
from typing import Callable, Sequence


Embedder = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class CourseDocument:
    document_id: str
    course_id: str
    learner_id: str
    title: str
    content: str
    due_date: date
    completed: bool = False


@dataclass(frozen=True)
class SearchHit:
    document: CourseDocument
    semantic_score: float
    priority_score: float
    overdue: bool


class CourseIndex:
    """In-memory index suitable for a small migration slice or local example."""

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._documents: dict[str, CourseDocument] = {}
        self._embeddings: dict[str, list[float]] = {}

    def upsert(self, documents: Sequence[CourseDocument]) -> int:
        if not documents:
            return 0
        vectors = self._embedder([document.content for document in documents])
        if len(vectors) != len(documents):
            raise ValueError("embedding count must match document count")
        for document, embedding in zip(documents, vectors, strict=True):
            self._documents[document.document_id] = document
            self._embeddings[document.document_id] = embedding
        return len(documents)

    def search(
        self,
        query: str,
        *,
        course_id: str,
        as_of: date,
        limit: int = 5,
    ) -> list[SearchHit]:
        query_embedding = self._embedder([query])[0]
        hits: list[SearchHit] = []
        for document_id, document in self._documents.items():
            if document.course_id != course_id:
                continue
            semantic_score = _cosine(query_embedding, self._embeddings[document_id])
            overdue = document.due_date < as_of and not document.completed
            priority_score = semantic_score + (0.15 if overdue else 0.0)
            hits.append(SearchHit(document, semantic_score, priority_score, overdue))
        return sorted(hits, key=lambda hit: hit.priority_score, reverse=True)[:limit]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("embeddings must have equal non-zero dimensions")
    denominator = sqrt(sum(value * value for value in left)) * sqrt(
        sum(value * value for value in right)
    )
    return sum(a * b for a, b in zip(left, right, strict=True)) / denominator if denominator else 0.0
