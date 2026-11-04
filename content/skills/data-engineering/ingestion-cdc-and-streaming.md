---
title: Ingestion, CDC, and Streaming
description: Select batch, incremental, and change-capture patterns and make their delivery guarantees explicit.
order: 7
tags: [ingestion, CDC, streaming, Kafka]
---

# Ingestion, CDC, and Streaming

Ingestion moves source data across a boundary. The design must preserve identity, event time, schema context, and enough progress information to recover without silently losing or duplicating records.

## Full load, incremental load, and CDC

- A **full snapshot** copies the current source state. It is simple to reason about for small datasets but can be expensive and may not preserve deleted or intermediate records.
- A **watermark-based incremental load** reads records newer than a timestamp or sequence. It is efficient when the source has a reliable update field; late updates and clock issues require a lookback or reconciliation strategy.
- **Change data capture (CDC)** reads inserts, updates, and deletes from database change logs or an equivalent source mechanism. It can preserve change order and transaction metadata, but requires careful offset management, schema handling, and delete semantics.

Choose based on source capability, freshness needs, volume, history requirements, and operational skill. CDC is not automatically more correct than a well-designed batch snapshot.

## ETL, ELT, and movement patterns

ETL transforms before loading into the analytical destination. ELT lands source-shaped data first and transforms it using destination compute. A hybrid approach may validate, filter, tokenize, or minimize sensitive data before landing, then apply reusable transformations later.

Reverse ETL publishes selected, governed analytical attributes back to operational tools. Treat it as a separate serving path with explicit ownership, freshness, write permissions, reconciliation, and a way to stop or roll back updates.

## Delivery semantics and idempotency

A connector may deliver a record more than once, after a retry, or after an offset reset. Design consumers to deduplicate by a stable event or source key and to apply updates using source order or version. Keep source transaction IDs, log positions, and ingestion timestamps where useful for audit and recovery.

“Exactly once” is scoped to a system and transaction boundary. End-to-end pipelines often cross systems with different commit protocols, so prefer explicit idempotency and reconciliation over relying on a broad exactly-once claim.

## Event time, processing time, and streaming

Event time is when an event occurred according to the source; processing time is when the pipeline handled it. Streaming systems use windows and watermarks to decide how long to wait for late events. Define what happens when an event arrives after the allowed lateness: update prior aggregates, emit a correction, route it for review, or reject it.

A distributed log such as Kafka can decouple producers and consumers and retain ordered records per partition. Partition keys affect ordering and parallelism. Understand retention, consumer offsets, replay, backpressure, and poison-message handling before treating a topic as a durable source of truth.

## Schema change and contract handling

Classify schema changes as compatible, conditionally compatible, or breaking for actual producers and consumers. Additive fields can still break strict parsers; renamed or retyped fields can silently change meaning. Use versioned contracts or a schema registry when multiple producers and consumers need coordinated evolution. Validate the incoming schema and make drift visible before downstream models publish.

## Backfills and reconciliation

A backfill reprocesses a declared event-time range using a known source snapshot or replayable log. Specify how outputs are replaced or merged, how concurrent scheduled runs are prevented from overwriting each other, and how totals are reconciled. Record the code and schema versions used so the result can be explained later.

## Practice

Design ingestion for a source that updates order status and can delete test records. Compare a daily snapshot, timestamp watermark, and CDC log. Define keys, delete handling, offsets, late arrivals, schema change policy, replay range, deduplication, and a reconciliation check. State the freshness requirement that would justify streaming over batch.