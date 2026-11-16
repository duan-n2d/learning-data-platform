---
title: Streaming Architectures and Recovery
description: Compare Lambda and Kappa architectures on a lakehouse, isolate bad records with dead letter queues, and plan replays and backfills.
order: 35
tags: [streaming, Lambda architecture, Kappa architecture, DLQ, backfill, replay, Iceberg, reliability]
---

# Streaming Architectures and Recovery

A streaming pipeline is only as trustworthy as its recovery story. This lesson compares the two classic architectures for combining real-time and historical data, then covers how to isolate bad records and how to reprocess history safely.

Assumptions: events in Kafka with seven days of retention, a Flink or Spark job writing Iceberg tables (see [stream processing with Flink](stream-processing-flink.html)), and a daily revenue metric that must match finance. Configurations are **illustrative**.

## Lambda Architecture

**What it is.** Lambda architecture splits processing into two paths: a **batch layer** that periodically recomputes accurate results from the complete historical dataset, and a **speed layer** that processes recent events in real time with lower accuracy guarantees. A **serving layer** merges both at query time: batch results for older periods, speed results for the gap since the last batch run.

**How it works (example).** Nightly, a Spark job recomputes daily revenue from the raw Iceberg event table. During the day, a streaming job maintains today's running total in a fast store. A view returns batch values for closed days and streaming values for today; when the nightly batch finishes, it replaces the streaming values for yesterday.

**Strengths.** The batch layer corrects streaming mistakes (late data, duplicates, bugs) every night, and historical reprocessing is ordinary batch work.

**Failure modes.** Two implementations of the same logic drift apart (different time zones, dedup rules, or currency conversion), so today's number jumps when the batch takes over; twice the code, tests, and on-call surface; the merge logic itself becomes a source of bugs at day boundaries.

**Validation.** Compare speed-layer and batch-layer results for the same closed period every day and alert above a tolerance; the difference is a direct measure of streaming correctness.

## Kappa Architecture

**What it is.** Kappa architecture uses a single stream processing path for both live and historical data. Reprocessing means replaying the retained log through a new version of the same streaming job, not running a separate batch system.

**How it works (example).**

1. Version 1 of the job reads `shop.orders` and writes `lake.gold.revenue_v1`.
2. A bug is found. Deploy version 2 reading from the earliest retained offset (or from the Iceberg raw table as a bounded source) into `lake.gold.revenue_v2`.
3. When v2 catches up to the live head, validate it against v1 and against finance for closed periods.
4. Switch readers (a view or catalog alias) to v2, keep v1 for a rollback window, then retire it.

**Iceberg's role.** A pure Kappa design requires the log to retain everything you might need to replay, which is costly in a broker. On a lakehouse, a common compromise is: the broker keeps days of data, and the raw Iceberg event table keeps full history. Engines like Flink and Spark can read the Iceberg table as a bounded stream for history and then switch to the broker for recent data, which keeps one codebase while relying on cheap storage. Kafka tiered storage is an alternative that keeps older segments in object storage.

**Failure modes.** Replaying months of events through a stateful streaming job can take a long time and need more parallelism than the live job; external side effects (emails, API calls) must not fire again during replay; replay results differ from the original if the job relies on processing time or lookups against data that has since changed.

## Lambda vs Kappa

| Concern | Lambda | Kappa |
|---|---|---|
| Codebases | Batch and streaming | One streaming codebase |
| Correction mechanism | Nightly batch recompute | Replay into a new output version |
| History source | Raw table or files | Retained log, or lake table as bounded stream |
| Consistency risk | Logic drift between layers | Replay time and side effects |
| Good fit | Teams strong in batch with modest real-time needs | Teams invested in stream processing and replayable sources |

Many lakehouse platforms end up in between: streaming ingestion into raw Iceberg tables, with both streaming and batch consumers reading the same tables using shared transformation logic.

## Dead Letter Queue (DLQ)

**What it is.** A dead letter queue holds messages that a consumer could not process, so the rest of the stream keeps flowing while bad records are kept for inspection and reprocessing.

**How it works.**

- **Kafka Connect:** set `errors.tolerance=all`, `errors.deadletterqueue.topic.name`, and `errors.deadletterqueue.context.headers.enable=true` on a sink connector; failed records go to the DLQ topic with headers describing the error, original topic, partition, and offset.
- **Flink:** route records that fail parsing or validation to a *side output*, then sink that stream to a DLQ topic or table.
- **Message queues (for example Amazon SQS):** a redrive policy moves a message to the DLQ after it has been received a maximum number of times without being deleted.
- **Lakehouse:** a quarantine Iceberg table with the raw payload, error class, error message, source coordinates, job version, and timestamp is easy to query and count.

```sql
-- Illustrative quarantine table.
CREATE TABLE lake.ops.dlq_orders (
  source_topic     STRING,
  source_partition INT,
  source_offset    BIGINT,
  raw_payload      BINARY,
  error_class      STRING,   -- e.g. SCHEMA_MISMATCH, INVALID_VALUE, UNKNOWN_KEY
  error_message    STRING,
  job_version      STRING,
  failed_at        TIMESTAMP
) PARTITIONED BY (days(failed_at));
```

**What should and should not go to a DLQ.** Deterministic, record-specific problems (malformed JSON, a value outside an allowed range, an unknown schema ID) belong there. Systemic problems (destination down, credentials expired) should fail or pause the pipeline instead: sending every record to the DLQ during an outage just moves the incident.

**Failure modes.**

- *Silent DLQ:* nobody monitors it, so data is "lost" in plain sight. Alert on DLQ rate relative to input, not just on any record.
- *Ordering:* redriving an old update for key 42 after newer updates were applied can overwrite current state with stale values. Apply redriven records by source version (log position or `updated_at`), never blindly.
- *Duplicates:* a redrive that partially succeeds and is re-run reinserts records unless the sink is idempotent.
- *Schema drift storms:* a producer change sends 100% of records to the DLQ; treat a sudden spike as a contract incident.

**Recovery.** Fix the cause (code, schema, or reference data), then redrive from the DLQ through the *same* validation path with version-aware upserts, and record which DLQ records were reprocessed. Delete or expire DLQ records according to the same retention and privacy rules as the main data.

## Replay and backfill

Replays and backfills apply to both architectures:

- Declare the range (event time or offsets), the source (broker, raw Iceberg table, or source system snapshot), and the target (overwrite partitions, a new versioned table, or idempotent merge).
- Prevent overlap with scheduled or streaming writes to the same partitions; Iceberg's optimistic concurrency will reject conflicting commits, which you should treat as a signal rather than retry blindly.
- Use Iceberg snapshots for safety: record the snapshot ID before the backfill so you can roll back (`rollback_to_snapshot`) if validation fails.
- Reconcile counts and totals against the source and against the previous output before switching readers.

## Practice

1. Implement the same daily revenue metric twice: streaming (Flink or Spark) and batch (SQL over the raw Iceberg table). Compare results for three closed days and explain any difference.
2. Introduce a bug in the streaming job, then fix it Kappa-style: run a v2 job into a new table from the raw history, validate, and switch a view to v2.
3. Add a DLQ (Kafka Connect DLQ topic or Flink side output to an Iceberg table). Inject 20 malformed records and one schema-incompatible record and confirm the main stream keeps flowing.
4. Redrive the DLQ records after a fix, including one stale update for a key that has newer data. Show your version check prevents the stale overwrite.
5. Perform a one-day backfill with a recorded starting snapshot, then roll back and re-apply it.

## Completion criteria

- You can explain when Lambda's dual paths are worth their cost and how Kappa reprocesses history, including the role of Iceberg as replay storage.
- Your DLQ records carry error class and source coordinates, are monitored by rate, and can be redriven idempotently and in version order.
- A replay or backfill was validated against a reference before readers were switched, with a tested rollback.
