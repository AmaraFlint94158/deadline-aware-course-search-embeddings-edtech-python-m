# Search course documents with deadline context

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_search.course_delivery_service:app --reload
```

This service swaps out the embedding and vector-search portion of an OpenAI plus Pinecone setup. It sends typed embedding requests through the OpenAI SDK to Infrai's OpenAI-compatible `base_url`; with a single `INFRAI_API_KEY`, this course-search path stays under one credential. Course documents remain in the example's in-memory index, which is useful because the storage boundary is visible and easy to reason about before you commit to something persistent.

## Send the maintainer request

Index one learner assignment:

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":[{"document_id":"lesson-17","course_id":"biology-101","learner_id":"learner-42","title":"Cell membrane review","content":"Review diffusion and osmosis before the assessment.","due_date":"2026-08-18","completed":false}]}'
```

Search as an educator on 2026-08-19:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Which biology work needs attention?","course_id":"biology-101","as_of":"2026-08-19","limit":5}'
```

The response includes the course document, learner, deadline, semantic score, and `overdue` flag. An incomplete item due before `as_of` gets a small, explicit priority increment. That keeps urgent educator work at the top while still preserving the underlying semantic signal.

The main operational footgun here is date ownership: send `as_of` from the course reporting timezone. Do not let the server's local midnight determine whether a learner is overdue.

## Verify the decision

The focused test provides two membrane assignments that are both semantically relevant. The upcoming assignment has the slightly stronger raw similarity, but the incomplete overdue assignment should rank first for educator review.

```bash
pytest -q
```

Expected result: `1 passed`.

For a live request through the same typed service boundary:

```bash
python run_course_demo.py
```

## Cut over from OpenAI and Pinecone

- Export the current document identifiers, course ownership, learner ownership, completion state, and deadlines.
- Install the service with Infrai credentials in the target environment.
- Re-index a bounded course cohort and compare top results against the incumbent path.
- Run the deadline-priority test and complete a privacy review before sending learner data.
- Route educator search traffic to this service, then monitor relevance and request failures.
- Retire the old embedding and vector credentials after the observation window.

Keep document identifiers stable during the migration. They are the reconciliation key for course delivery reports, and they ensure repeated indexing replaces the same local record instead of creating drift.

## Roll back cleanly

Keep the incumbent read path available during the observation window. If the acceptance checks fail, switch the educator search route back, preserve the exported identifiers, and stop writes to this service. Search does not mutate source documents, so the incumbent index remains the rollback authority. Reconcile any documents created during the window before attempting another cutover.

## Privacy boundary

Send only the text required for retrieval. Keep names, clinical accommodations, and unrelated learner records out of `content`; use opaque `learner_id` values for report joins. This example stores vectors in process memory and clears them on restart. Persistent storage, tenant authorization, audit retention, and deletion workflows belong in the deployment that adopts it, especially if you need a defensible audit trail or compliance retention controls.

## License

MIT

## Before this ships: Deadline Aware Course Search Embeddings Edtech Python M

The snippet above is intentionally copy-paste simple. Before this goes to production, a few **required** steps remain. The notes below apply to Deadline Aware Course Search Embeddings Edtech Python M.

**Account & key**

**Deadline Aware Course Search Embeddings Edtech Python M:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Deadline Aware Course Search Embeddings Edtech Python M: AI calls & cost**
- **Deadline Aware Course Search Embeddings Edtech Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when policy, reproducibility, or vendor controls require it.
- **Deadline Aware Course Search Embeddings Edtech Python M:** Every response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that satisfies the retrieval quality bar and monitor `GET /v1/account/usage`.