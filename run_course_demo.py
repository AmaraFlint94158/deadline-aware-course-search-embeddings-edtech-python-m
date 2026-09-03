"""Run one course indexing and deadline-aware search request."""

from datetime import date

from fastapi.testclient import TestClient

from course_search.course_delivery_service import app


client = TestClient(app)

documents = {
    "documents": [
        {
            "document_id": "lesson-17",
            "course_id": "biology-101",
            "learner_id": "learner-42",
            "title": "Cell membrane review",
            "content": "Review diffusion and osmosis before the cell membrane assessment.",
            "due_date": "2026-08-18",
            "completed": False,
        },
        {
            "document_id": "lesson-18",
            "course_id": "biology-101",
            "learner_id": "learner-42",
            "title": "Genetics reading",
            "content": "Read the introduction to Mendelian inheritance.",
            "due_date": "2026-08-25",
            "completed": False,
        },
    ]
}

index_response = client.post("/documents", json=documents)
index_response.raise_for_status()
search_response = client.post(
    "/search",
    json={
        "query": "What biology work needs attention?",
        "course_id": "biology-101",
        "as_of": date(2026, 8, 19).isoformat(),
        "limit": 2,
    },
)
search_response.raise_for_status()
print(search_response.json())
