---
title: API and Event Ingestion
description: Pull data from REST and GraphQL APIs, receive webhooks safely, and understand event sourcing as a source of analytical history.
order: 34
tags: [ingestion, API, REST, GraphQL, webhook, event sourcing, pagination, rate limits]
---

# API and Event Ingestion

Many sources are not databases you can read directly: they are SaaS products and internal services that expose APIs or push events. This lesson covers pulling (REST, GraphQL), being pushed to (webhooks), and a source design pattern, event sourcing, that changes what "history" means.

Assumptions: a SaaS CRM with a REST API and webhooks, an internal GraphQL service, and a raw landing zone in Iceberg or a warehouse. Endpoints, headers, and payloads are **illustrative**.

## REST API

**What it is.** A REST API is a web interface that exposes *resources* (customers, orders) at URLs and manipulates them with standard HTTP methods. REST is an architectural style with constraints such as client-server separation, statelessness (each request carries everything needed, including authentication), cacheability, and a uniform interface.

**How it works for ingestion.** You mostly use `GET` on collection endpoints and follow the API's conventions for:

- **Authentication:** API keys, OAuth 2.0 tokens that expire and must be refreshed.
- **Pagination:** offset/limit (simple but unstable when data changes during paging), page numbers, or cursors (an opaque token for the next page; stable and preferred).
- **Filtering:** `updated_since`-style parameters for incremental loads.
- **Status codes:** `200` success, `4xx` client errors (`401` auth, `404` missing, `429` rate limited), `5xx` server errors.

```http
GET /v1/contacts?updated_since=2026-11-16T00:00:00Z&limit=100&cursor=eyJpZCI6MTIzfQ HTTP/1.1
Authorization: Bearer <token>
Accept: application/json

HTTP/1.1 200 OK
X-RateLimit-Remaining: 42
{"data": [...], "next_cursor": "eyJpZCI6MjIzfQ"}
```

**Where it falls short for bulk data.** One record set per request, page size limits, and rate limits make full historical loads slow. Many APIs offer bulk export endpoints (async jobs that produce files); prefer them for backfills.

**Failure modes.** Offset pagination skips or duplicates rows when records are inserted during the load; `updated_since` filters with second precision miss records updated within the same second at a boundary; deleted records never appear in a list endpoint; an API version change alters field types.

## GraphQL

**What it is.** GraphQL is an open-source query language and runtime for APIs. A client sends a query to a single endpoint and receives exactly the fields it requested, shaped like the query, validated against a typed schema.

**How it works for ingestion.**

```graphql
query Orders($after: String, $since: DateTime!) {
  orders(first: 100, after: $after, filter: {updatedAt: {gte: $since}}) {
    pageInfo { hasNextPage endCursor }
    edges { node { id status totalCents updatedAt customer { id } } }
  }
}
```

Loop while `pageInfo.hasNextPage` is true, passing `endCursor` as `after`. Many GraphQL APIs follow this cursor "connections" convention.

**Trade-offs.** Fetching only needed fields and related objects in one request reduces over-fetching. But rate limits are often based on *query cost* (points per field and page size) instead of request counts, deeply nested queries can be expensive or rejected, and errors are often returned with HTTP `200` in an `errors` array alongside partial `data`.

**Failure modes.** Treating HTTP 200 as success and loading partial data; schema fields deprecated and later removed; nested lists inside a node silently truncated at their own page limit (for example, only the first 10 line items).

## API Integration

**What it is.** API integration is the practice of connecting systems through their APIs. For data teams it means building and operating reliable extraction from APIs into the lakehouse, including authentication, paging, limits, incremental state, and schema handling.

**How to build it (checklist).**

1. **Credentials:** store secrets in a secret manager; use the least-privilege scope; plan token refresh and rotation.
2. **Incremental state:** persist the cursor or high-water mark *after* the data is durably written, never before.
3. **Rate limits:** respect `429` and `Retry-After`; use exponential backoff with jitter; cap concurrency.
4. **Idempotency:** land raw responses with a stable record key and request metadata (endpoint, parameters, retrieval time), then deduplicate downstream.
5. **Deletes:** use a deleted-records endpoint, webhooks, or periodic full-key reconciliation.
6. **Raw retention:** keep raw JSON (or a typed raw table) so parsing changes can be replayed without calling the API again.

```python
# Illustrative retry loop honoring rate limits.
import random, time, requests

def get_with_backoff(session, url, params, max_attempts=6):
    for attempt in range(max_attempts):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = float(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait + random.uniform(0, 1))
            continue
        resp.raise_for_status()  # 4xx other than 429 should fail loudly, not retry
        return resp.json()
    raise RuntimeError(f"gave up after {max_attempts} attempts: {url}")
```

Libraries and tools such as dlt, Airbyte, and Fivetran implement much of this (see [managed and open ingestion tools](managed-and-open-ingestion-tools.html)); the checklist is still how you evaluate them.

**Validation.** Compare counts for a closed window with the vendor's UI or reporting API; check for duplicate keys; alert on zero-row loads for sources that normally change daily.

## Webhook

**What it is.** A webhook is an HTTP callback: when something happens in a source system, it sends an HTTP `POST` with an event payload to a URL you registered. It reverses the API direction from pull to push.

**How it works.**

1. You register an endpoint and the event types you want.
2. The provider sends events, usually signed with a shared secret (for example an HMAC-SHA256 signature header) and including an event ID and timestamp.
3. Your endpoint verifies the signature, stores the raw event durably (queue or object storage), and returns `2xx` quickly. Processing happens asynchronously.
4. If you do not respond with `2xx` in time, the provider retries with backoff for a limited period, then may disable the endpoint.

```python
# Illustrative receiver: verify, persist, acknowledge. Do not process inline.
import hashlib, hmac

def handle(request, secret: bytes, queue):
    body = request.body  # raw bytes, before JSON parsing
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("X-Signature", "")):
        return 401
    queue.send(body, dedupe_id=request.headers["X-Event-Id"])
    return 200
```

**Failure modes.** Webhooks are typically *at-least-once* and *unordered*: the same event can arrive twice, and `updated` can arrive before `created`. Endpoint downtime longer than the retry window loses events. Slow synchronous processing causes timeouts and retry storms. Missing signature checks or timestamp tolerance allow spoofed or replayed requests.

**Validation and recovery.** Deduplicate on event ID; apply updates by source version or timestamp, not arrival order; run a periodic API reconciliation (pull) to catch missed events; use the provider's event replay or event-list API after an outage.

## Event Sourcing

**What it is.** Event sourcing is an application design pattern where the system of record is an append-only log of domain events (`OrderPlaced`, `ItemAdded`, `OrderPaid`) rather than mutable rows. Current state is derived by replaying (folding) the events for an entity.

**How it works.** Commands are validated against the current state and, if accepted, produce new events appended to the entity's stream with an increasing version number. Read models (*projections*) are built by consuming events, often paired with CQRS (separate write and read models). Snapshots store state at a version to avoid replaying long streams.

```python
# Illustrative fold: state is a function of ordered events.
def apply(state, event):
    match event["type"]:
        case "OrderPlaced": return {"status": "placed", "total": 0}
        case "ItemAdded":   return {**state, "total": state["total"] + event["price_cents"]}
        case "OrderPaid":   return {**state, "status": "paid"}
    return state
```

**Event sourcing vs CDC.** CDC captures row-level effects of transactions on tables (`status` changed from `pending` to `paid`). Event sourcing records *intent and meaning* (`OrderPaid` with payment method). For analytics, an event-sourced system is an excellent source of history, but its events are an internal model: publish curated integration events or a contract rather than exposing every internal event type.

**Failure modes.** Event schemas evolve over years, so old events need upcasting or versioned handlers; projections rebuilt with changed code produce different numbers than before; deleting personal data from an immutable log requires a plan (crypto-shredding or separate PII storage); replay of a large stream can take hours.

**Validation.** Rebuild a projection from scratch in a test environment and compare it with the live projection; check per-stream version sequences for gaps.

## Practice

1. Write an incremental extractor for a paginated REST API (or a local mock) that uses cursor pagination, honors `429` with `Retry-After`, and persists its cursor only after a successful write. Kill it mid-run and show it resumes without gaps or duplicates.
2. Write the same extraction against a GraphQL endpoint with a connections-style query. Make the loader fail when the response contains `errors`, even with HTTP 200.
3. Build a webhook receiver that verifies an HMAC signature, stores raw events, and deduplicates by event ID. Send the same event twice and an `updated` event before `created`; show the final state is correct.
4. Model a small event-sourced order stream, build a projection, change the projection logic, rebuild, and explain the difference.

## Completion criteria

- Your API extractor handles authentication, pagination, rate limits, incremental state, and deletes, and you can explain each choice.
- Your loaders treat partial or error responses as failures and keep raw payloads for replay.
- Your webhook path is verified, idempotent, order-tolerant, and backed by a reconciliation pull.
- You can explain when event-sourced events, CDC events, and API snapshots each give the right history.
