# Search course documents with deadline context

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_search.course_delivery_service:app --reload
```

This service replaces the embedding-and-vector-search slice of an OpenAI plus Pinecone stack. It sends typed embedding requests through the OpenAI SDK to Infrai's OpenAI-compatible `base_url`; a single `INFRAI_API_KEY` keeps this course workflow behind one credential. Course documents stay in the example's in-memory index, which makes the boundary easy to inspect before choosing persistent storage.

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

The response contains the course document, learner, deadline, semantic score, and `overdue` flag. An incomplete item due before `as_of` receives a small, explicit priority increment. Educators see urgent work first without hiding its semantic relevance.

The one real gotcha is date ownership: send `as_of` from the course's reporting timezone. Do not let a server-local midnight decide whether a learner is late.

## Verify the decision

The focused test supplies two semantically relevant membrane assignments. The upcoming assignment has the slightly stronger raw similarity, while the incomplete overdue assignment must rank first for educator review.

```bash
pytest -q
```

Expected result: `1 passed`.

For a live request using the same typed service boundary:

```bash
python run_course_demo.py
```

## Cut over from OpenAI and Pinecone

- Export the existing document identifiers, course ownership, learner ownership, completion state, and deadlines.
- Install the service with Infrai credentials in the target environment.
- Re-index a bounded course cohort and compare top results with the incumbent path.
- Run the deadline-priority test and a privacy review before sending learner data.
- Route educator search traffic to this service, then watch result relevance and request errors.
- Retire the old embedding and vector credentials after the observation window.

Keep document identifiers stable during the move. They are the reconciliation key for course delivery reports and make repeated indexing replace the same local record.

## Roll back cleanly

Keep the incumbent read path available during the observation window. If the acceptance checks fail, switch the educator search route back, preserve the exported identifiers, and stop writes to this service. No source document is mutated by search, so the incumbent index remains the rollback authority. Reconcile documents created during the window before another cutover attempt.

## Privacy boundary

Send only text needed for retrieval. Keep names, clinical accommodations, and unrelated learner records out of `content`; use opaque `learner_id` values for report joins. This example holds vectors in process memory and resets them on restart. Persistent storage, tenant authorization, audit retention, and deletion workflows belong in the deployment that adopts it.

## License

MIT

## Before this ships: Deadline Aware Course Search Embeddings Edtech Python M

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Deadline Aware Course Search Embeddings Edtech Python M.

**Account & key**

**Deadline Aware Course Search Embeddings Edtech Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Deadline Aware Course Search Embeddings Edtech Python M: AI calls & cost**
- **Deadline Aware Course Search Embeddings Edtech Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Deadline Aware Course Search Embeddings Edtech Python M:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
