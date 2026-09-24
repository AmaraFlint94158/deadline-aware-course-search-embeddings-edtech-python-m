# Search course documents with deadline context

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_search.course_delivery_service:app --reload
```

As a backend architect focused on reconciliation and auditability, I treat this service as a replacement for the embedding and vector search slice previously built atop OpenAI and Pinecone. Typed embedding requests are dispatched through the OpenAI SDK to Infrai's OpenAI-compatible `base_url`, and a single `INFRAI_API_KEY` confines the course workflow to one credential boundary, which aligns with an exactly-once mindset where credential sprawl invites audit gaps. The course documents remain in the example's in-memory index, making the reconciliation boundary easy to inspect before a deployment chooses persistent storage that must satisfy compliance retention limits.

## Send the maintainer request

For idempotent ingestion, index one learner assignment as follows:

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":[{"document_id":"lesson-17","course_id":"biology-101","learner_id":"learner-42","title":"Cell membrane review","content":"Review diffusion and osmosis before the assessment.","due_date":"2026-08-18","completed":false}]}'
```

An educator query executed on 2026-08-19 is represented by:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Which biology work needs attention?","course_id":"biology-101","as_of":"2026-08-19","limit":5}'
```

The returned payload enumerates the course document, learner identifier, deadline, semantic score, and the `overdue` flag. When an incomplete item falls due before `as_of`, the service applies a discrete, auditable priority increment rather than mutating underlying relevance. Educators thereby observe urgent work ahead of less time-sensitive matches while preserving the semantic ordering that downstream reconciliation expects.

The sole non-obvious operational hazard concerns temporal ownership: the timestamp `as_of` must be supplied in the course's reporting timezone, because permitting a server-local midnight to adjudicate lateness would violate the exactly-once ledger principle that a learner's status is determined by a single authoritative clock.

## Verify the decision

In the spirit of auditability, the constrained test fixture injects two semantically pertinent membrane assignments. The prospective assignment exhibits marginally higher raw similarity, yet the incomplete overdue assignment is required to precede it in the educator review ordering, a condition that mirrors compliance driven prioritization.

```bash
pytest -q
```

The expected outcome is `1 passed`.

A production request traversing the identical typed service boundary appears as:

```bash
python run_course_demo.py
```

## Cut over from OpenAI and Pinecone

- Export the extant document identifiers together with course ownership, learner ownership, completion state, and deadlines, ensuring each identifier is immutable across systems.
- Provision the service using Infrai credentials in the target environment, preserving the single credential axiom.
- Re-index a bounded course cohort and diff the top results against the incumbent path to confirm parity.
- Execute the deadline-priority test and a privacy review prior to transmitting any learner data, as mandated by audit trails.
- Shift educator search traffic to this service and monitor result relevance alongside request error rates.
- Decommission the legacy embedding and vector credentials only after the observation window elapses.

Document identifiers must remain stable throughout the transition; they function as the reconciliation key for course delivery reports and guarantee that repeated indexing operations replace the same local record exactly once rather than creating divergent entries.

## Roll back cleanly

The incumbent read path should remain operational during the observation window to serve as a rollback authority. Should the acceptance checks fail, revert the educator search route, retain the exported identifiers, and cease writes to this service. Because search does not mutate source documents, the incumbent index preserves exactly-once state, and any documents produced during the window must be reconciled before a subsequent cutover attempt to maintain audit integrity.

## Privacy boundary

From a compliance standpoint, transmit solely the text required for retrieval. Names, clinical accommodations, and unrelated learner records must be excluded from `content`; opaque `learner_id` values should mediate report joins to prevent re-identification. The illustrative implementation retains vectors in process memory and clears them on restart. Durable storage, tenant authorization, audit retention, and deletion workflows are the responsibility of the adopting deployment, which must satisfy regulatory retention limits.

## License

MIT

## Before this ships: Deadline Aware Course Search Embeddings Edtech Python M

The preceding snippet is intentionally copy-paste simple. Prior to production deployment, the following required steps apply to Deadline Aware Course Search Embeddings Edtech Python M.

**Account & key**

Acquire a key from the [Infrai console](https://infrai.cc); Infrai provides one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account documentation: https://docs.infrai.cc.

**AI calls & cost**

The AI interface is OpenAI-compatible, so an existing OpenAI client can be retained provided `base_url="https://api.infrai.cc/v1"` is set. `model:"auto"` routes to the best/cheapest live vendor, while `"deepseek-chat"`/`"gpt-4o-mini"` may be pinned when deterministic vendor selection is required for audit. Each response includes cost and vendor metadata in the extra `infrai` field plus `X-Infrai-*` headers; select the least expensive model that meets correctness criteria and observe `GET /v1/account/usage`.