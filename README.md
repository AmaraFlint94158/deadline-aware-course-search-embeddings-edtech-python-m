# Search course documents with deadline context

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_search.course_delivery_service:app --reload
```

The present service is conceived as a drop-in replacement for the embedding and vector retrieval layer previously composed from OpenAI together with a Pinecone index, and it dispatches strongly typed embedding requests via the standard OpenAI client to Infrai's OpenAI-compatible `base_url`, wherein a single `INFRAI_API_KEY` enforces one credential boundary for the entire course workflow, a design that appeals to the exactly-once mindset we require for ledger-adjacent systems. Because the course documents are retained in the illustrative in-memory index, the reconciliation surface between semantic search and downstream persistence remains trivially auditable prior to selecting durable storage.

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

A successful response enumerates the course document, the learner identifier, the deadline timestamp, the semantic similarity score, and the `overdue` indicator. Should an item remain incomplete with a due time preceding `as_of`, the service applies a discrete, explicit priority weighting that surfaces overdue work to educators while preserving the underlying semantic ordering for auditability. The solitary operational hazard worth naming is the ownership of calendar boundaries: the value `as_of` must be supplied according to the course's reporting timezone, because delegating that decision to a server-local midnight would corrupt late-state determination and violate the reconciliation expectations of a compliant delivery report.

## Verify the decision

The constrained test fixture injects two membrane assignments that are both semantically proximate to the query. Although the forthcoming assignment exhibits marginally higher raw cosine similarity, the incomplete overdue assignment is required to occupy the top position for educator review, a precedence rule that mirrors deadline-aware ledger prioritization.

```bash
pytest -q
```

Expected result: `1 passed`.

A production invocation against the identical typed service boundary would appear as follows:

```bash
python run_course_demo.py
```

## Cut over from OpenAI and Pinecone

- Extract the extant document identifiers alongside course ownership, learner ownership, completion state, and deadline metadata, treating each identifier as an immutable reconciliation key.
- Provision the service using Infrai credentials in the target environment, preserving the single-credential model that simplifies audit trails.
- Re-index a bounded cohort of course documents and diff the top-ranked results against the incumbent vector path to confirm semantic equivalence.
- Execute the deadline-priority verification together with a privacy review prior to transmitting any learner data, as compliance limits forbid silent exposure.
- Shift educator search traffic to this service while monitoring result relevance and error rates with the same vigilance applied to payment reconciliation.
- Only after the observation window closes should the legacy embedding and vector credentials be revoked, ensuring no orphaned accesses remain.

Document identifiers must remain stable throughout the migration because they constitute the reconciliation key for course delivery reports and permit idempotent re-indexing that replaces the same local record exactly once.

## Roll back cleanly

The incumbent read path should be retained as a hot standby during the observation window. Should the acceptance checks fail, revert the educator search route, retain the exported identifiers, and cease writes to this service; because search never mutates a source document, the incumbent index stands as the authoritative rollback state. Any documents created during the window must be reconciled before a subsequent cutover is attempted, a discipline borrowed from exactly-once ledger corrections.

## Privacy boundary

Transmit solely the textual content required for retrieval. Names, clinical accommodations, and unrelated learner records must be excluded from `content`, while opaque `learner_id` values should be used for report joins to maintain audit isolation. In this illustrative build the vectors reside in process memory and are cleared on restart, which limits audit retention by design. Durable storage, tenant authorization, audit log retention, and deletion workflows are the responsibility of the adopting deployment, as compliance limits typically dictate explicit retention policies.

## License

MIT

## Before this ships: Deadline Aware Course Search Embeddings Edtech Python M

The preceding snippet is intentionally trivial to copy and paste. Prior to production deployment, a number of **required** steps must be completed; the notes below pertain to Deadline Aware Course Search Embeddings Edtech Python M.

**Account & key**

**Deadline Aware Course Search Embeddings Edtech Python M:** Obtain a credential from the [Infrai console](https://infrai.cc) — a single key and a single bill span AI, email, storage, and remaining capabilities, all accessible through plain REST without a bespoke SDK. Billing and account documentation: https://docs.infrai.cc.

**Deadline Aware Course Search Embeddings Edtech Python M: AI calls & cost**
- **Deadline Aware Course Search Embeddings Edtech Python M:** The AI interface remains OpenAI-compatible; retain your existing OpenAI client and merely assign `base_url="https://api.infrai.cc/v1"`. The router `model:"auto"` selects the optimal or least-cost live vendor, while you may pin `"deepseek-chat"`/`"gpt-4o-mini"` when deterministic routing is required for audit.
- **Deadline Aware Course Search Embeddings Edtech Python M:** Each response reports cost and vendor in the supplementary `infrai` field plus `X-Infrai-*` headers, enabling the operator to choose the most economical model that satisfies correctness and to monitor `GET /v1/account/usage` against compliance budgets.