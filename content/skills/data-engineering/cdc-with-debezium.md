---
title: CDC with Debezium and Kafka Connect
description: Capture database changes from logs, move them through Kafka Connect into Iceberg, and compare CDC with replication and zero-ETL integrations.
order: 32
tags: [CDC, Debezium, Kafka Connect, replication, zero-ETL, Iceberg, ingestion]
---

# CDC with Debezium and Kafka Connect

Change data capture (CDC) turns committed database changes into a stream of events. The [ingestion, CDC, and streaming](ingestion-cdc-and-streaming.html) lesson explains when CDC is worth its complexity; this lesson shows how a common open-source implementation works and where it breaks.

Assumptions: a PostgreSQL database `shop` with tables `public.orders` and `public.customers`, each with a primary key; a Kafka cluster with Schema Registry; an Iceberg REST catalog. All configurations are **illustrative**: property names change between Debezium and connector versions, so check the documentation for yours.

## Kafka Connect

**What it is.** Kafka Connect is Apache Kafka's framework for moving data between Kafka and other systems using reusable *connectors*, so teams configure pipelines instead of writing producer and consumer code.

**How it works.**

- **Workers** are JVM processes that run in a cluster (distributed mode) and share work. Configuration, offsets, and status are stored in internal Kafka topics, so a worker can die and its tasks move elsewhere.
- **Source connectors** (Debezium, JDBC, files) write into Kafka; **sink connectors** (Iceberg, S3, Elasticsearch) read from Kafka.
- A connector is split into **tasks**, the unit of parallelism.
- **Converters** serialize records (Avro, Protobuf, JSON Schema with Schema Registry); **single message transforms (SMTs)** apply light per-record changes such as renaming fields or unwrapping CDC envelopes.
- Connectors are created and inspected through a REST API.

**Iceberg sink (illustrative).** The Apache Iceberg project ships a Kafka Connect sink that writes topic records to Iceberg tables and coordinates commits across tasks through a control topic, committing on an interval.

```json
{
  "name": "orders-iceberg-sink",
  "config": {
    "connector.class": "org.apache.iceberg.connect.IcebergSinkConnector",
    "tasks.max": "3",
    "topics": "shop.public.orders",
    "iceberg.tables": "raw.orders_cdc",
    "iceberg.tables.auto-create-enabled": "true",
    "iceberg.tables.evolve-schema-enabled": "true",
    "iceberg.control.commit.interval-ms": "300000",
    "iceberg.catalog.type": "rest",
    "iceberg.catalog.uri": "http://iceberg-rest:8181",
    "iceberg.catalog.warehouse": "s3://lake/warehouse",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "dlq.orders-iceberg-sink",
    "errors.deadletterqueue.context.headers.enable": "true"
  }
}
```

```bash
curl -s -X POST -H "Content-Type: application/json" --data @orders-iceberg-sink.json http://connect:8083/connectors
curl -s http://connect:8083/connectors/orders-iceberg-sink/status   # check every task is RUNNING
```

**Failure modes.** A task can be `FAILED` while the connector reports `RUNNING`, so check task status, not only connector status. `errors.tolerance=all` without a DLQ silently drops bad records. The built-in DLQ applies to sink connectors and to conversion/transform errors; errors inside the external write may still fail the task. Too many tasks for too few partitions leaves tasks idle.

## Debezium

**What it is.** Debezium is an open-source CDC platform that reads a database's transaction log (PostgreSQL logical decoding, MySQL binlog, SQL Server CDC tables, Oracle LogMiner, MongoDB change streams, and others) and emits one event per row change. It usually runs as Kafka Connect source connectors; Debezium Server and an embedded engine can send to other destinations.

**How it works.**

1. **Initial snapshot.** On first start the connector reads existing rows (events with `op = "r"`), then switches to streaming from the log position recorded at snapshot time. Incremental snapshots can re-read tables later without stopping streaming.
2. **Streaming.** Each committed insert, update, or delete becomes an event with `op` = `c`, `u`, or `d`.
3. **Offsets.** The connector stores its log position (an LSN for PostgreSQL, binlog file and position or GTID for MySQL) in Kafka Connect offsets, so restarts resume where they left off.
4. **Topics.** By default each table goes to `<topic.prefix>.<schema>.<table>`, keyed by the table's primary key so changes to one row stay ordered.

**Inspectable example: source connector (illustrative).**

```json
{
  "name": "shop-postgres-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "pg-primary",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${file:/opt/secrets/pg.properties:password}",
    "database.dbname": "shop",
    "topic.prefix": "shop",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_shop",
    "publication.name": "dbz_shop",
    "table.include.list": "public.orders,public.customers",
    "snapshot.mode": "initial",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "key.converter.schema.registry.url": "http://schema-registry:8081",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081"
  }
}
```

**Event envelope (illustrative, simplified).**

```json
{
  "before": {"order_id": 42, "status": "pending", "amount_cents": 1999},
  "after":  {"order_id": 42, "status": "paid",    "amount_cents": 1999},
  "source": {"connector": "postgresql", "db": "shop", "table": "orders",
             "lsn": 24023128, "txId": 5521, "ts_ms": 1763370192000},
  "op": "u",
  "ts_ms": 1763370192450
}
```

`source.ts_ms` is when the change committed in the database; the outer `ts_ms` is when Debezium processed it. Use the log position (`lsn`) or a source version, not processing time, to order changes for one key.

**Landing in Iceberg.** Two common designs:

- **Change log table (append).** Store every event with `op`, `lsn`, and `source.ts_ms`. This keeps full history and makes replays and audits possible; build the current state downstream with a `MERGE` that keeps the latest `lsn` per key.
- **Mirror table (upsert).** Use an unwrap SMT (`io.debezium.transforms.ExtractNewRecordState`) to flatten the envelope and an upsert-capable sink (Flink with a primary key, or a sink configured for upserts) so the table mirrors the source. Configure how deletes are represented (tombstones, a `__deleted` flag, or real deletes).

```sql
-- Illustrative: rebuild current state from an append-only change log.
MERGE INTO lake.silver.orders t
USING (
  SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY lsn DESC) AS rn
    FROM lake.raw.orders_cdc
    WHERE ingest_date = DATE '2026-11-17'
  ) WHERE rn = 1
) s
ON t.order_id = s.order_id
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED AND s.lsn > t.lsn THEN UPDATE SET *
WHEN NOT MATCHED AND s.op <> 'd' THEN INSERT *;
```

**Failure modes.**

- *Replication slot growth.* While the connector is stopped, PostgreSQL keeps WAL for the slot; a long outage can fill the database disk. Alert on slot lag (`pg_replication_slots`), and drop abandoned slots deliberately.
- *Duplicates after restart.* Offsets are committed periodically, so a crash replays recent changes. Sinks must be idempotent by key and log position.
- *Ordering.* Order is guaranteed per key (partition), not across tables. A join of `orders` and `customers` changes may observe them in different orders than the source transaction.
- *Schema drift.* A column added in the source changes the event schema; a dropped or renamed column may break consumers or the Iceberg sink. Route DDL through review and test with Schema Registry compatibility.
- *Partial updates.* With PostgreSQL default replica identity, `before` may be empty and unchanged large (TOAST) values may appear as a placeholder; set `REPLICA IDENTITY FULL` on tables where you need full before-images, accepting the extra WAL.
- *Snapshot cost.* Initial snapshots of large tables load the source; schedule them and consider incremental snapshots.

**Validation and recovery.** Reconcile row counts and checksums per key range between source and the Iceberg mirror daily; compare the highest captured `lsn` with the database's current position to measure lag; for a lost or corrupt target, re-snapshot (incremental snapshot or a new connector with a new slot) into a new table and swap after reconciliation.

## Data Replication

**What it is.** Data replication continuously copies data from one system to others to provide availability, disaster recovery, read scaling, or locality. CDC is one way to implement replication across different systems; databases also replicate natively between their own nodes.

**How it works.**

- **Synchronous** replication acknowledges a write only after replicas confirm it: no data loss on failover, higher write latency.
- **Asynchronous** replication acknowledges first and ships changes later: faster writes, but a failover can lose the most recent changes (the replication lag window).
- **Physical** replication copies storage-level changes (PostgreSQL streaming replication); **logical** replication copies row changes and can target a different version, subset, or system.
- Topologies include single-leader (one writer, many readers), multi-leader, and leaderless quorum systems.

Kafka replicates partitions the same way: `replication.factor=3`, `min.insync.replicas=2`, and producer `acks=all` give durability as long as two replicas are healthy.

**Failure modes.** Readers on an asynchronous replica see stale data (read-your-writes violations); multi-leader setups need conflict resolution; a replica faithfully copies accidental deletes, so **replication is not a backup**. Analytics queries pointed at a replica can still slow the primary through replication conflicts or held resources.

**Validation.** Monitor replication lag in time and bytes, test failover regularly, and keep point-in-time backups independent of replicas.

## Zero-ETL

**What it is.** Zero-ETL is a vendor approach where an operational database is connected to an analytics system without the customer building or running pipeline code. Examples include managed integrations from operational databases into cloud warehouses and "mirroring" features in analytics platforms.

**How it works.** Under the hood the vendor runs CDC or replication, manages offsets and schema mapping, and lands near-real-time, source-shaped tables in the destination. The "zero" refers to the pipeline you maintain, not to extraction, loading, or transformation disappearing.

**Relation to ELT and reverse ETL.** Zero-ETL is effectively managed EL with replication semantics: you still model, test, and govern data after it lands (the T in ELT). Reverse ETL goes the other direction, from analytics back to operational tools, and is unaffected.

**Trade-offs and failure modes.** Fewer moving parts and fast setup, but supported sources, destinations, table types, and DDL changes are limited to what the vendor implements; filtering and masking before landing may not be possible, which matters for sensitive columns; cost and lag are less visible; and moving away later means building the pipeline anyway.

**Validation.** Treat a zero-ETL target like any other source: check freshness, reconcile counts with the source, test how deletes and schema changes appear, and document what happens during source maintenance or failover.

## Practice

1. Run PostgreSQL, Kafka, Kafka Connect, and Schema Registry locally (for example with Docker Compose). Deploy the Debezium source connector for one table and inspect the snapshot (`op = r`) and streaming (`c/u/d`) events.
2. Update one row three times and delete it. Show the events in order with their `lsn` values.
3. Land the change log in an Iceberg table with the sink connector and build a current-state table with `MERGE`. Prove a deleted row is gone and a replayed batch does not change the result.
4. Stop the connector for 15 minutes while writing to the source, then measure replication slot lag before and after restart.
5. Add a nullable column and then rename a column in the source. Record what happens in Schema Registry, the topic, and the Iceberg table.
6. Write a half-page decision note comparing Debezium + Kafka Connect, native database replication, and a vendor zero-ETL integration for your source.

## Completion criteria

- You can explain snapshot vs streaming phases, offsets, and why ordering holds per key only.
- Your current-state table is idempotent under replay and handles deletes correctly, verified by a reconciliation query.
- You monitor replication slot or connector lag and have a written recovery procedure (re-snapshot into a new table, validate, swap).
- Your decision note distinguishes replication for availability from CDC for analytics and states zero-ETL limits for your source.
