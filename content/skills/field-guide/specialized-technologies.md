---
title: Specialized Data Technologies Field Guide
description: Understand contracts, change capture, history, schema evolution, assets, and analytical engines.
order: 5
tags: [data contracts, CDC, schema evolution, OLAP]
---

# Specialized Data Technologies Field Guide

Specialized technologies solve particular boundary problems. Learn the invariant they provide and what remains your responsibility before adding a tool to a stack.

## Contracts, products, and assets

A data contract is an agreement about schema, meaning, quality, freshness, compatibility, ownership, and change. It should be checked where data is produced or consumed. A schema-valid record can still violate a business rule, so include semantic expectations where they can be expressed and tested.

A data product is a supported data interface for identified consumers. It needs an owner, documentation, access policy, quality expectations, and a support path. A software-defined asset represents a durable data output in code, often with dependencies, metadata, checks, and execution behavior. This can make lineage and freshness visible, but it does not automatically make the output reliable; tests and ownership still matter.

## Snapshots, CDC, and idempotency

A snapshot records a source state at a point in time. It is useful for reproducibility and detecting changes, but a sequence of snapshots may not reveal every intermediate event. CDC captures inserts, updates, and deletes from a source change log; understand offsets, ordering, transaction boundaries, deletes, and schema evolution.

Idempotency means repeating an operation with the same logical input does not create an unintended additional effect. Use stable keys, deterministic partitions, merge rules, or deduplication records. Define the scope: a task may be idempotent while its overall workflow still sends a duplicate external notification.

## Slowly changing dimensions and time travel

A slowly changing dimension preserves changes in descriptive attributes. Type 1 overwrites a value when history is unnecessary. Type 2 adds versions with validity boundaries so a fact can use the description valid at event time. Define timezone and interval boundaries, use non-overlapping validity ranges, and test late-arriving facts and corrections.

Time travel reads or restores a previous table snapshot where the storage system supports it. It is useful for audit, reproducibility, and recovery, but retention, concurrent writes, catalog behavior, and snapshot expiration constrain it. Treat it as a tested recovery feature, not a substitute for backups or source retention.

## ACID and schema change

ACID transactions provide atomicity, consistency, isolation, and durability within a defined transaction boundary. In a data platform, that boundary may not span source databases, object storage, catalogs, transformation jobs, and downstream consumers. Document where a commit becomes visible and what a failed multi-step run leaves behind.

Schema evolution is the controlled change of a data contract over time. Schema drift is an observed difference between expected and incoming shape or meaning, whether planned or accidental. Additive fields can still break strict consumers; changed types, renamed fields, and semantic reuse can silently corrupt meaning. Classify compatibility, version contracts, alert on drift, and coordinate producer and consumer rollout.

### Example order contract

```yaml
contract_version: 1
owner: commerce-data
grain: one record per source order
key: order_id
fields:
	order_id: {type: string, required: true}
	status: {type: string, required: true, allowed: [pending, paid, cancelled, refunded]}
	updated_at: {type: timestamp, required: true, timezone: UTC}
delivery:
	cadence: daily
	expected_by: "07:00 UTC"
change_policy: announce breaking changes before rollout
```

This contract can be checked at ingestion and referenced by downstream models. The business owner still needs to decide whether a new status is valid and how reports should treat it.

| Change | Typical compatibility | Safer rollout |
|---|---|---|
| Add optional field | Often backward compatible, but strict consumers may fail | Deploy tolerant consumers, then publish the field |
| Add required field | Breaking for existing producers | Supply a default or stage producer and consumer changes |
| Rename a field | Breaking | Add the new field, dual-read/write temporarily, migrate consumers, then deprecate the old field |
| Change type or unit | Usually breaking even if values still parse | Introduce a versioned field and reconcile before migration |
| Reuse a field with new meaning | Semantic breaking change | Create a new field/metric and document the sunset plan |

### Snapshot and CDC example

A snapshot represents a complete state only if its extraction is complete and has a clear boundary. Keep a `snapshot_at` timestamp and a stable key. Do not infer deletion from a missing row in a partial extract. For a confirmed full snapshot, define whether absence means delete, soft-delete, or out-of-scope.

A CDC update may look like:

```json
{
	"operation": "update",
	"source_position": "log-offset-or-sequence",
	"transaction_id": "source-transaction-id",
	"event_time": "2026-04-02T10:15:00Z",
	"key": {"order_id": "O-1042"},
	"before": {"status": "pending"},
	"after": {"status": "paid"}
}
```

The consumer should persist its source position with committed output, apply changes in the source's ordering scope, and handle replay idempotently. A delete event needs a defined tombstone or deletion record so downstream history and current-state models can react consistently.

### Type 2 history and idempotent application

When a customer changes region, a Type 2 dimension closes the old version and creates a new one. Use half-open validity intervals so exactly one version matches an event time:

```sql
select f.order_id, d.region
from fct_orders f
join dim_customer_history d
	on f.customer_id = d.customer_id
 and f.order_time >= d.valid_from
 and f.order_time < d.valid_to;
```

For repeatable loads, merge using the stable business key plus source version or event position. Reprocessing an identical event should not add another history version. If an older correction arrives, define whether to rebuild the affected history range and test that the intervals remain non-overlapping.

## Integration CLI tools

Command-line data integration tools can help extract, normalize, validate, and load data in local or automated workflows. Evaluate authentication, secrets handling, incremental state, retries, source coverage, destination semantics, logs, license, and upgrade path. A CLI invocation is not a full pipeline contract until state, errors, idempotency, and operations are defined.

## Analytical engines and serving technologies

Cube is an example of a semantic and analytical serving layer that can pre-aggregate measures and expose governed queries to applications. VertiPaq is a compressed in-memory columnar storage engine used in Microsoft's BI ecosystem. Both illustrate how semantic models, compression, and pre-aggregation affect performance; they are not interchangeable with a general-purpose warehouse. Measure model size, refresh, concurrency, and query patterns in the target environment.

A data engineering toolkit is best treated as a map of capabilities rather than a required shopping list. Classify tools by ingestion, storage, transformation, orchestration, quality, catalog, serving, and observability; select only what a workload and team can operate.

## Technology review questions

- Which guarantee does the technology provide, and at what boundary?
- Which failure modes, state, and operational responsibilities remain?
- How do schema changes and rollback work across producers and consumers?
- Is the integration supported by the actual storage, engine, catalog, and identity setup?
- What is the smallest representative test that would disprove the proposed choice?

## Practice

Design a customer dimension fed by a source database and used in a monthly report. Specify whether the source uses snapshots or CDC, define Type 2 validity ranges, make the load idempotent, test schema drift, and describe recovery from a bad publish using snapshots and retained source data.

## Continue learning

- [Data quality and contracts](../data-engineering/data-quality-contracts.html)
- [Ingestion, CDC, and streaming](../data-engineering/ingestion-cdc-and-streaming.html)
- [Storage, warehousing, and table formats](../data-engineering/storage-warehousing-and-formats.html)
- [Query engines and performance](../data-engineering/query-engines-and-performance.html)