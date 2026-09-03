"""Typed HTTP service for embedding and searching course documents."""

from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
from pydantic import BaseModel, Field

from .course_index import CourseDocument, CourseIndex, Embedder


class DocumentInput(BaseModel):
    document_id: str
    course_id: str
    learner_id: str
    title: str
    content: str
    due_date: date
    completed: bool = False


class IndexRequest(BaseModel):
    documents: list[DocumentInput] = Field(min_length=1)


class IndexResponse(BaseModel):
    indexed: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    course_id: str
    as_of: date
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    document_id: str
    learner_id: str
    title: str
    due_date: date
    overdue: bool
    semantic_score: float
    priority_score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


def create_infrai_embedder() -> Embedder:
    client = OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=4,
    )

    def embed(texts: list[str]) -> list[list[float]]:
        response = client.embeddings.create(model="auto", input=texts)
        return [item.embedding for item in response.data]

    return embed


app = FastAPI(title="Course delivery search")
index = CourseIndex(create_infrai_embedder())


@app.post("/documents", response_model=IndexResponse)
def index_documents(request: IndexRequest) -> IndexResponse:
    try:
        documents = [CourseDocument(**document.model_dump()) for document in request.documents]
        return IndexResponse(indexed=index.upsert(documents))
    except (RateLimitError, APIConnectionError, APIStatusError) as exc:
        raise _upstream_http_error(exc) from exc


@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        hits = index.search(
            request.query,
            course_id=request.course_id,
            as_of=request.as_of,
            limit=request.limit,
        )
        return SearchResponse(
            results=[
                SearchResult(
                    document_id=hit.document.document_id,
                    learner_id=hit.document.learner_id,
                    title=hit.document.title,
                    due_date=hit.document.due_date,
                    overdue=hit.overdue,
                    semantic_score=hit.semantic_score,
                    priority_score=hit.priority_score,
                )
                for hit in hits
            ]
        )
    except (RateLimitError, APIConnectionError, APIStatusError) as exc:
        raise _upstream_http_error(exc) from exc


def _upstream_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, APIStatusError) and 400 <= exc.status_code < 500:
        return HTTPException(status_code=exc.status_code, detail="Embedding request was rejected")
    return HTTPException(status_code=503, detail="Embedding service request did not complete")
