---
title: Stream Processing with Flink
description: Land and analyze streams continuously, understand checkpoints and commits, and choose between micro-batching and continuous processing for Iceberg tables.
order: 31
tags: [streaming, Flink, Spark, micro-batching, Iceberg, streaming analytics, checkpoints]
---

# Stream Processing with Flink

A broker such as Kafka stores events; a stream processor reads them, keeps state, and writes results. This lesson focuses on Apache Flink and on how processing style (micro-batches or record-at-a-time) shapes latency, cost, and table layout in an Iceberg lakehouse.

Assumptions: events come from topic `shop.orders` (see [event streaming platforms](event-streaming-platforms.html)), carry an `event_time` in UTC, and are keyed by `order_id`. SQL and configuration below are **illustrative**; option names vary across Flink, Spark, and Iceberg versions.

## Streaming Ingestion

**What it is.** Streaming ingestion lands data continuously as it is produced, instead of on a schedule. The usual path is source → broker (Kafka, Pulsar, Kinesis) → processor or connector (Flink, Spark, Kafka Connect) → table (Iceberg, Delta, a warehouse).

**How it works.** The ingestion job reads from the broker, optionally parses, validates, deduplicates, or masks records, then appends or upserts them into a raw or bronze table. Progress (offsets) and output (table commits) must move together, or a restart duplicates or skips data.

**Design decisions to write down.**

- Freshness target (for example "raw table at most 5 minutes behind the topic, p95").
- Append-only or upsert. Raw event tables are usually append-only; current-state tables need a key and an upsert or merge strategy.
- What happens to invalid records (DLQ, quarantine table, or job failure).
- Commit interval and compaction plan, because every commit creates files and snapshots.

**Failure modes.** *Small files*: committing every 10 seconds across 20 parallel writers creates thousands of tiny files per hour, slowing every reader. *Snapshot growth*: each commit adds Iceberg metadata; without snapshot expiry, metadata grows indefinitely. *Schema drift*: a new field in the topic is silently dropped if the table schema is not evolved. *Backpressure*: a slow sink stalls the whole pipeline and grows broker lag.

**Validation.** Compare record counts per hour between the topic and the table, track the maximum `event_time` in the table versus wall clock (freshness), monitor files-per-partition and average file size, and run scheduled compaction (`rewrite_data_files`) and snapshot expiry.

## Apache Flink

**What it is.** Apache Flink is an open-source, distributed, stateful stream processing engine. It processes records one at a time as they arrive, keeps keyed state (counts, windows, last-seen values), and treats batch as a bounded stream.

**How it works.**

- A job is a dataflow graph of operators running in parallel *tasks*. Keyed operators partition state by key so each key's state lives on one task.
- **State backends** keep state in memory (heap) or on local disk (RocksDB, and newer disaggregated options), so state can exceed RAM.
- **Checkpoints** periodically take consistent snapshots of all operator state and source positions using barriers that flow through the stream. On failure, Flink restores the last completed checkpoint and rewinds sources to the stored offsets.
- **Watermarks** track event-time progress so windows can close even when events arrive out of order.
- **Savepoints** are user-triggered snapshots used for upgrades, rescaling, or migrations.

**Why Iceberg commits follow checkpoints.** The Flink Iceberg sink writes data files continuously, but only commits them to the table (creating a new snapshot) when a checkpoint completes. That ties table contents to the checkpointed source offsets: after a failure, uncommitted files are discarded and the data is re-read, giving exactly-once results in the table. The consequence is that **table freshness is bounded by the checkpoint interval**: a 60-second checkpoint means readers see new data roughly once a minute at best.

**Inspectable example (illustrative Flink SQL).**

```sql
SET 'execution.checkpointing.interval' = '60s';

CREATE CATALOG lake WITH (
  'type' = 'iceberg',
  'catalog-type' = 'rest',
  'uri' = 'http://iceberg-rest:8181',
  'warehouse' = 's3://lake/warehouse'
);

CREATE TEMPORARY TABLE orders_src (
  event_id     STRING,
  order_id     BIGINT,
  status       STRING,
  amount_cents BIGINT,
  event_time   TIMESTAMP(3),
  WATERMARK FOR event_time AS event_time - INTERVAL '2' MINUTE
) WITH (
  'connector' = 'kafka',
  'topic' = 'shop.orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'flink-orders-to-iceberg',
  'scan.startup.mode' = 'group-offsets',
  'properties.auto.offset.reset' = 'earliest',
  'format' = 'avro-confluent',
  'avro-confluent.url' = 'http://schema-registry:8081'
);

-- Append raw events; dedupe downstream on event_id.
INSERT INTO lake.raw.order_events
SELECT event_id, order_id, status, amount_cents, event_time
FROM orders_src;
```

For a current-state table, declare a primary key on the Iceberg table (format v2) and enable upsert writes; Flink then emits equality deletes plus inserts. Upsert tables produce delete files that readers must merge, so compaction matters even more.

**Flink vs Spark Structured Streaming.** Flink is record-at-a-time with first-class event-time state and low latency; Spark Structured Streaming defaults to micro-batches and fits naturally when the team already runs Spark for batch. Both can write Iceberg; in both, table commit frequency, not engine latency, usually sets end-to-end freshness.

**Failure modes.** Checkpoints that time out (often due to backpressure or huge state) mean no Iceberg commits at all, so the table stops advancing while the job looks "running". Changing a stateful query can make old state incompatible; plan savepoint-based upgrades. Watermarks set too tight drop late events from windows; too loose delays results.

**Recovery.** Restart from the latest checkpoint for crashes; restart from a savepoint for planned changes; for logic bugs, run a new job version from a chosen offset or timestamp into a new table, validate it, then swap readers (see the Kappa pattern in [streaming architectures and recovery](streaming-architectures-and-recovery.html)).

## Streaming Analytics

**What it is.** Streaming analytics computes results continuously over moving data: rolling revenue per minute, fraud scores per card, inventory alerts, live funnel conversion. It differs from streaming ingestion in that the output is an answer, not a copy.

**How it works.** Continuous queries group events into windows:

- **Tumbling**: fixed, non-overlapping (every 5 minutes).
- **Hopping/sliding**: fixed size, overlapping (10-minute window every minute).
- **Session**: closes after a gap of inactivity per key.

Watermarks decide when a window is considered complete. Late events can update prior results (emitting retractions), go to a side output, or be dropped. Results are written to a serving store (a key-value store, an OLAP database, or an Iceberg table for slower consumers).

**Example (illustrative Flink SQL).**

```sql
SELECT window_start, window_end, SUM(amount_cents) AS paid_cents, COUNT(*) AS paid_orders
FROM TABLE(TUMBLE(TABLE orders_src, DESCRIPTOR(event_time), INTERVAL '5' MINUTE))
WHERE status = 'paid'
GROUP BY window_start, window_end;
```

**Failure modes.** Double counting from duplicate events (dedupe on `event_id` before aggregating); results that disagree with the batch warehouse because of different late-data rules or time zones; a dashboard that shows a partial window as if final.

**Validation.** Reconcile streaming aggregates against a batch recomputation of the same closed windows each day; label partial or provisional values in the serving layer; record the watermark and lateness policy alongside the metric definition.

## Micro-Batches

**What it is.** A micro-batch is a small, bounded slice of a stream (for example, all records that arrived in the last 30 seconds, or up to the latest offsets available when the trigger fired) processed as a single mini batch job.

**How it works.** At each trigger the engine records the offset range it will read, processes that range, writes the output, and then commits progress to a checkpoint or write-ahead log. Because each micro-batch has a fixed input range, a failed batch can be re-run with the same input, which makes recovery simple to reason about.

**What it means for Iceberg.** Each micro-batch typically produces one table commit. A 30-second trigger means about 2,880 snapshots per day per table, each adding data and metadata files. Plan compaction and snapshot expiry from day one, and avoid triggers faster than readers actually need.

## Micro-Batching

**What it is.** Micro-batching is the processing model that runs a stream as a series of micro-batches. Spark Structured Streaming uses it by default; Kafka Connect sinks behave similarly by buffering records and flushing on a size or time threshold; the Iceberg Kafka Connect sink commits on a configured interval.

**Inspectable example (illustrative PySpark).**

```python
(spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "shop.orders")
    .option("startingOffsets", "earliest")
    .load()
    .selectExpr("CAST(key AS STRING) AS order_key", "value", "timestamp")
    .writeStream.format("iceberg")
    .outputMode("append")
    .trigger(processingTime="1 minute")
    .option("checkpointLocation", "s3://lake/checkpoints/orders_raw")
    .toTable("lake.raw.order_events"))
```

The `checkpointLocation` stores which offsets each batch consumed. Deleting it or pointing a new query at an old location changes what gets reprocessed, so treat it as production state. A `trigger(availableNow=True)` run processes everything available and stops, which lets the same code run as a scheduled incremental batch.

**Trade-offs.** Higher throughput per unit of compute, simple exactly-once bookkeeping, and natural fit with table commits; latency is at least the trigger interval plus processing time. A batch that takes longer than its trigger interval causes the next batch to start late and lag to grow.

## Continuous Streaming

**What it is.** Continuous streaming processes each record as soon as it arrives, without waiting to fill a batch. Flink is the reference example; Spark's experimental continuous processing mode supported only simple map-like operations with at-least-once guarantees, which is why most Spark streaming runs in micro-batches.

**How it works.** Operators run as long-lived tasks connected by network buffers. Fault tolerance comes from asynchronous checkpoints rather than per-batch commits, so processing latency can be milliseconds while durability is still checkpoint-based.

**What it means for Iceberg.** Continuous processing does not make an Iceberg table continuously fresh. Table visibility is still a commit, and commits are tied to checkpoints. If you need sub-second visibility, serve from a low-latency store or the stream itself, and use Iceberg for the durable, queryable history.

## Continuous Streaming vs Micro-Batching

| Concern | Micro-batching | Continuous streaming |
|---|---|---|
| Processing latency | Trigger interval plus batch time (seconds to minutes) | Milliseconds to seconds |
| Throughput efficiency | High; per-batch overhead amortized | High, but more sensitive to tuning |
| Recovery model | Re-run the failed batch's offset range | Restore checkpoint, rewind sources |
| Event-time state and timers | Supported, coarser timing | Fine-grained, first-class |
| Iceberg freshness | One commit per batch | One commit per checkpoint |
| Operational familiarity | Batch-like, easy for Spark teams | Requires state and checkpoint tuning |

**Choosing.** Start from the consumer's freshness need. If a dashboard refreshes every 15 minutes, a 5-minute micro-batch or even a scheduled incremental batch is cheaper and simpler. Choose continuous processing when the output feeds an automated decision that loses value within seconds (fraud, alerting) or when complex event-time state is central.

## Practice

1. Run the Flink SQL example (or the PySpark one) against a local Kafka and an Iceberg REST catalog. Change the checkpoint or trigger interval from 60 seconds to 10 seconds, run for 30 minutes, and compare snapshot counts and average file sizes in the table metadata.
2. Kill the job mid-run and restart it. Prove there are no duplicate `event_id` values in the table and no gaps compared with the topic.
3. Build a 5-minute tumbling revenue aggregate. Inject one event 10 minutes late and document what happens with your watermark setting.
4. Run compaction and snapshot expiry on the table and record file counts before and after.
5. For three use cases (finance dashboard refreshed hourly, fraud scoring, raw clickstream landing), choose micro-batching or continuous processing and justify the choice with latency, cost, and recovery.

## Completion criteria

- You can explain why Iceberg table freshness follows checkpoint or trigger intervals, and you measured it.
- A forced restart produced neither duplicates nor gaps, verified by a reconciliation query.
- Your streaming aggregate has a documented watermark, lateness policy, and daily batch reconciliation.
- Your table has a compaction and snapshot-expiry plan with measured effect.
