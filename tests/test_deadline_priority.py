from datetime import date

from course_search.course_index import CourseDocument, CourseIndex


def test_overdue_incomplete_work_gets_priority_for_educator_review() -> None:
    vectors = {
        "late membrane task": [0.90, 0.10],
        "upcoming membrane task": [0.96, 0.04],
        "membrane help": [1.0, 0.0],
    }
    index = CourseIndex(lambda texts: [vectors[text] for text in texts])
    index.upsert(
        [
            CourseDocument(
                "late",
                "biology-101",
                "learner-42",
                "Late membrane task",
                "late membrane task",
                date(2026, 8, 18),
            ),
            CourseDocument(
                "upcoming",
                "biology-101",
                "learner-42",
                "Upcoming membrane task",
                "upcoming membrane task",
                date(2026, 8, 25),
            ),
        ]
    )

    results = index.search(
        "membrane help", course_id="biology-101", as_of=date(2026, 8, 19)
    )

    assert results[0].document.document_id == "late"
    assert results[0].overdue is True
    assert results[0].priority_score > results[1].priority_score
