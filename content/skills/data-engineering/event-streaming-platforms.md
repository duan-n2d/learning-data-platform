---
title: Event Streaming Platforms
description: Compare queues, pub/sub, and retained event logs, then operate Kafka-family platforms and schemas without losing order or meaning.
order: 30
tags: [streaming, Kafka, pub/sub, message queue, schema registry, Pulsar, Redpanda, Confluent, Fluss, ZooKeeper]
---

# Event Streaming Platforms

This lesson covers the messaging layer that sits between operational systems and a lakehouse. It extends the [ingestion, CDC, and streaming](ingestion-cdc-and-streaming.html) lesson: read that first for delivery semantics, event time, and backfills.

Assumptions used in the examples: an `orders` service emits one event per order state change, the event key is `order_id`, timestamps are UTC, and the analytical target is an Apache Iceberg table. Commands and configs are **illustrative**; check the documentation of the exact version you run.

## Event Streaming

**What it is.** Event streaming treats business facts ("order 42 was paid at 10:03:12Z") as an ordered, continuously growing sequence of immutable records. Producers append events; any number of consumers read them, at their own pace, now or later.

**How it works.** A streaming platform stores events durably in an append-only log for a retention period (time, size, or forever with tiered storage). Each consumer tracks its own position (an offset). Because the log is retained, a new consumer can start from the beginning and a broken consumer can rewind and replay.

**Why it matters for data teams.** The same event stream can feed a fraud service, a search index, and a raw lakehouse table without the source system knowing about any of them. The cost is that you now own a second copy of business truth whose ordering, retention, and schema must be managed.

**Failure modes.** Events published before the transaction that caused them commits (phantom events), events lost when the service writes to its database but crashes before publishing (the dual-write problem; use an outbox table or CDC), and consumers that assume global order when the platform guarantees order only per partition or key.

**Validation.** Compare event counts per business key and hour with the source system, check that every state transition is legal (no `shipped` before `paid` for the same key within one partition), and alert on consumer lag.

## Pub/Sub Architecture

**What it is.** Publish/subscribe is a messaging pattern: publishers send messages to a named topic without knowing who receives them; subscribers register interest in topics and each receives its own copy.

**How it works.** A broker sits in the middle. Fan-out is the defining property: one published event can reach many independent subscriber groups. Delivery can be *push* (broker calls the subscriber, as with webhooks or push subscriptions) or *pull* (subscriber fetches, as with Kafka consumers). Within one subscriber group, work is usually shared across instances.

**Example (illustrative).** `orders` publishes `OrderPaid`. Three subscriptions exist: `billing` (sends invoices), `lake-ingest` (writes to Iceberg), and `notifications` (emails the customer). Adding a fourth subscriber requires no change to the publisher.

**Failure modes.** Hidden coupling through payload shape (subscribers break when a field changes), slow subscribers accumulating backlog, and subscribers that need ordering when the system only offers best-effort or per-key ordering. Pub/sub decouples *who* and *when*, not *what the message means*; that still needs a contract.

## Message Queue

**What it is.** A message queue is a buffer where producers place messages for asynchronous processing by consumers. Its typical semantics are *competing consumers*: each message is handled by one consumer, then acknowledged and removed.

**How it works.** A consumer receives a message, which becomes invisible to others for a lease (visibility timeout). If the consumer acknowledges within that time the message is deleted; otherwise it reappears and is retried. Systems such as RabbitMQ and Amazon SQS follow this model; many add priorities, delays, and dead letter queues.

**Queue vs event stream.**

| Property | Message queue | Event stream (log) |
|---|---|---|
| After processing | Message is deleted | Record stays until retention expires |
| Consumers | Compete for messages | Each group reads the full stream |
| Replay | Usually not possible | Rewind the offset |
| Ordering | Often best-effort; FIFO variants exist | Per partition |
| Good fit | Task distribution, jobs, commands | Shared facts, multiple consumers, replay |

**Failure modes.** A slow handler exceeds the visibility timeout, so the message is processed twice; poison messages retry forever without a DLQ (see [streaming architectures and recovery](streaming-architectures-and-recovery.html)); a queue used as a system of record loses history once messages are acknowledged.

## Apache Kafka

**What it is.** Apache Kafka is an open-source distributed event streaming platform. It stores records in *topics*, split into *partitions*, replicated across *brokers*.

**How it works.**

- A **producer** sends a record with an optional key. The default partitioner hashes the key, so all records for `order_id=42` land in the same partition and keep their relative order.
- Each partition is an ordered log; each record gets a monotonically increasing **offset**.
- Partitions have a **leader** and **follower replicas**. With `acks=all` and `min.insync.replicas=2`, a write is acknowledged only after at least two in-sync replicas have it.
- A **consumer group** divides partitions among its members. Committed offsets record each group's progress, which is what makes restart and replay possible.
- Current Kafka uses **KRaft** (a built-in Raft-based controller quorum) for metadata; ZooKeeper mode was removed in Kafka 4.0.
- **Log compaction** keeps at least the latest record per key, which suits changelog topics; time retention suits event topics.

**Inspectable example (illustrative).**

```bash
# Six partitions bound the maximum parallelism of one consumer group.
kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic shop.orders --partitions 6 --replication-factor 3 \
  --config min.insync.replicas=2 --config retention.ms=604800000

# Check how far the lake ingestion group is behind.
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group orders-to-iceberg
# Columns to read: PARTITION, CURRENT-OFFSET, LOG-END-OFFSET, LAG
```

Producer settings worth stating explicitly: `acks=all`, `enable.idempotence=true` (prevents duplicates from producer retries within a session), and a key that matches the entity whose order matters.

**Failure modes.**

- *Duplicates*: a consumer writes to Iceberg, crashes before committing its offset, and re-reads the batch. Make the sink idempotent (merge on `event_id`) or use a sink that commits offsets and data together.
- *Ordering*: changing the partition count changes the key-to-partition mapping for new records, so events for one key can be split across partitions. Plan partition counts up front.
- *Hot partitions*: a skewed key (one huge tenant) limits throughput to one partition.
- *Retention loss*: a consumer down longer than `retention.ms` silently skips data once it resumes from the earliest available offset.
- *Backpressure*: Kafka buffers on disk, so a slow consumer shows up as growing lag, not as producer failure. Lag is the primary health signal.

**Recovery.** Reset a consumer group to a timestamp or offset (`kafka-consumer-groups.sh --reset-offsets --to-datetime ... --execute` while the group is stopped) and rely on an idempotent sink to absorb the replayed range.

## Apache ZooKeeper

**What it is.** Apache ZooKeeper is a coordination service for distributed systems. It stores small pieces of metadata in a tree of *znodes* and provides strong ordering for updates.

**How it works.** An ensemble (usually 3 or 5 servers) elects a leader and replicates writes with the ZAB protocol; a write succeeds when a majority acknowledges it. Clients use *ephemeral znodes* (deleted when the session dies) for liveness and leader election, and *watches* to be notified of changes.

**Who still needs it.** Kafka used ZooKeeper for cluster metadata and controller election until KRaft replaced it; Kafka 4.0 and later run without it, and older clusters must migrate to KRaft before upgrading. ZooKeeper still appears in HBase, Hadoop HDFS high-availability failover, Apache Solr (SolrCloud), some Flink high-availability setups (Kubernetes HA is an alternative), and as one of the metadata store options for Apache Pulsar.

**Failure modes.** Losing quorum (2 of 3 nodes down) blocks all writes; session timeouts set too low cause flapping leader elections during garbage-collection pauses; storing large data in znodes degrades the whole ensemble. **Validation:** use the `ruok`/`mntr` four-letter commands (if whitelisted) or the admin server to check leader/follower state and outstanding requests.

For a new lakehouse stack, the practical question is usually "do any of my components still require ZooKeeper?" rather than "should I deploy it?".

## Schema Registry

**What it is.** A schema registry is a service that stores versioned schemas (Avro, Protobuf, JSON Schema) for messages and enforces compatibility rules when producers register a new version. Confluent Schema Registry is the most common; Apicurio Registry and AWS Glue Schema Registry fill the same role.

**How it works.** Schemas are grouped under *subjects*; with the default naming strategy the value schema of topic `shop.orders` lives under subject `shop.orders-value`. A serializer registers or looks up the schema and writes a small header with the schema ID before the payload, so consumers fetch the exact writer schema. Compatibility modes decide what changes are accepted:

| Mode | Guarantee | Typical safe change |
|---|---|---|
| `BACKWARD` (common default) | New readers can read data written with the previous schema | Delete a field, add an optional field with a default |
| `FORWARD` | Old readers can read data written with the new schema | Add a field, delete an optional field |
| `FULL` | Both directions | Add/remove optional fields with defaults |
| `*_TRANSITIVE` | Checked against all prior versions, not only the last | Same, stricter |
| `NONE` | No check | Anything, including breaking changes |

**Inspectable example (illustrative).**

```bash
# Test a candidate schema before deploying the producer.
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @candidate-schema.json \
  http://schema-registry:8081/compatibility/subjects/shop.orders-value/versions/latest
# => {"is_compatible": false}  -> block the release in CI
```

**Failure modes.** A registry check proves structural compatibility only: renaming `amount` to `amount_cents` with a default is "compatible" but changes meaning. JSON producers that bypass the serializer skip the check entirely. Setting `NONE` "temporarily" during an incident often becomes permanent. When the sink is Iceberg, a compatible Avro change must still map to a legal Iceberg schema evolution (for example, widening `int` to `long` is allowed; narrowing is not).

**Validation.** Run the compatibility endpoint in CI for every schema change, review semantic changes in the data contract, and alert when a topic receives records with an unknown or unregistered schema ID.

## Apache Pulsar

**What it is.** Apache Pulsar is an open-source messaging and streaming platform that separates serving from storage: stateless **brokers** handle clients, while **Apache BookKeeper** nodes (bookies) store data as replicated *ledgers*.

**How it works.** A topic is a sequence of ledger segments spread across bookies, so adding storage does not require rebalancing whole partitions. Pulsar supports multi-tenancy (tenants and namespaces), built-in geo-replication, tiered storage to object stores, and several subscription types on the same topic: *exclusive*, *failover*, *shared* (queue-like competing consumers), and *key_shared* (parallelism with per-key ordering). Metadata lives in a pluggable store such as ZooKeeper, etcd, or Oxia depending on version and deployment.

**Pulsar vs Kafka for lakehouse ingestion.** Pulsar combines queue and stream semantics in one system and scales storage independently of brokers; Kafka has the larger connector ecosystem, more managed offerings, and broader engine support (Flink, Spark, Kafka Connect sinks to Iceberg). Pulsar can feed Iceberg through Pulsar IO sinks, Flink's Pulsar connector, or Kafka-protocol compatibility layers; verify the maturity of the specific sink you plan to use.

**Failure modes.** More moving parts (brokers, bookies, metadata store) to monitor; *shared* subscriptions trade away ordering; message acknowledgment is per message, so unacknowledged backlogs can grow silently. Validate with subscription backlog metrics and end-to-end count reconciliation.

## Redpanda

**What it is.** Redpanda is a streaming platform that implements the Kafka API in C++, without a JVM or ZooKeeper. Existing Kafka clients, Kafka Connect, and most tooling work against it unchanged.

**How it works.** Each partition is replicated with Raft, and a thread-per-core architecture aims for low and predictable tail latency with fewer nodes. It ships as a single binary with a built-in schema registry and HTTP proxy. *Iceberg Topics* can write a topic's records into an Iceberg table registered in a catalog, so a topic is queryable as a table without a separate sink job; check which catalogs, schema mappings, and editions your release supports.

**Choosing it.** Treat "Kafka-compatible" as a claim to test: run your producers, consumers, transactions, and admin scripts against it in staging. Compatibility at the protocol level does not guarantee identical behavior for every configuration or edge case.

**Failure modes.** Topic-to-table writing still needs a schema (registered Avro/Protobuf or a declared format); records that fail translation must go somewhere visible (a DLQ table or topic). Table commits happen on an interval, so table freshness lags topic freshness.

## Confluent

**What it is.** Confluent is the company founded by Kafka's original creators. It sells **Confluent Platform** (self-managed) and **Confluent Cloud** (fully managed Kafka, connectors, Schema Registry, Flink, and governance features). IBM announced an agreement to acquire Confluent in late 2025; check current ownership, packaging, and licensing when you evaluate it.

**Tableflow.** Confluent Cloud's Tableflow materializes Kafka topics as Apache Iceberg or Delta Lake tables in object storage, using the topic's registered schema, and publishes them to catalogs so engines can query them. It removes the need to operate a separate sink connector for straightforward topic-to-table cases.

**When it fits.** Teams that want Kafka without running brokers, upgrades, and connector clusters. The trade is cost (throughput, storage, and connector pricing), vendor-specific features, and data residency constraints.

**Failure modes and checks.** Managed does not mean correct: you still own keys, schemas, retention, and consumer idempotency. Before relying on a materialized table, confirm how deletes and upserts are represented, how often snapshots are committed, what happens to records that fail schema conversion, and how you would rebuild the table if needed.

## Apache Fluss

**What it is.** Apache Fluss (incubating) is open-source streaming storage designed for real-time analytics, built around Apache Flink. It originated at Alibaba and entered the Apache Incubator in 2025.

**How it works.** Fluss offers *log tables* (append-only streams) and *primary-key tables* that accept updates, emit a changelog, and support point lookups. Log data is stored in a columnar, Arrow-based format, so a reader that needs 3 of 40 columns can avoid transferring the rest. A tiering service continuously compacts data into lake table formats (Apache Paimon first; Iceberg support was added in later releases), and readers can combine the recent Fluss data with the tiered lake data.

**Fluss vs Kafka.**

| Aspect | Kafka | Fluss |
|---|---|---|
| Storage layout | Row-oriented byte records | Columnar log, projection pushdown |
| Updates | Compacted topics, consumer applies upserts | Primary-key tables with changelog |
| Lookups by key | Not supported | Supported |
| Lake integration | Separate sink or vendor feature | Built-in tiering to lake formats |
| Ecosystem maturity | Very broad | Young, Flink-centric |

**When to evaluate it.** Flink-heavy analytics that need fresh, updatable tables and key lookups. Validate maturity, operational tooling, and engine support before choosing it for a platform others depend on.

## Practice

1. Create a local Kafka (or Redpanda) topic with 3 partitions. Produce 30 order events across 5 keys, consume them, and show that ordering holds per key but not across keys.
2. Stop the consumer, produce 10 more events, then describe the consumer group and record the lag. Restart and confirm the lag returns to zero.
3. Register an Avro schema for `shop.orders-value` with `BACKWARD` compatibility. Test one compatible change and one breaking change through the compatibility endpoint and capture both responses.
4. Write a one-page comparison of Kafka, Pulsar, Redpanda, Confluent Cloud, and Fluss for a team of three engineers that needs a raw Iceberg table refreshed every five minutes. Include operational burden, cost drivers, and the exit path.
5. Explain in your own words when you would use a message queue instead of an event stream, with one example of each.

## Completion criteria

- You can explain partitions, keys, offsets, consumer groups, and replication settings, and predict what ordering a consumer will see.
- You have measured consumer lag and recovered from a stopped consumer without duplicating rows in the sink.
- Your schema change process checks compatibility automatically and reviews meaning separately.
- Your platform comparison names concrete trade-offs and states which claims you verified versus took from documentation.
