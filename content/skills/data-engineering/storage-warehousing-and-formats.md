---
title: Storage, Warehousing, and Table Formats
description: Choose transactional and analytical storage based on workload, durability, and access needs.
order: 6
tags: [storage, data warehouse, lakehouse, file formats]
---

# Storage, Warehousing, and Table Formats

Storage design starts with workload and recovery requirements. A file format, database, or table format is a means to meet those requirements, not an architecture by itself.

## OLTP and OLAP serve different workloads

| Property | OLTP system | OLAP system |
|---|---|---|
| Main purpose | Record current operational state | Analyze large volumes of historical data |
| Typical operation | Many short reads and writes by key | Fewer scans, joins, and aggregations over many rows |
| Modeling tendency | Normalize to protect transaction consistency | Denormalize or organize for analytical access |
| Example | Update one order's payment status | Compare paid revenue by month and channel |

Operational applications remain the source of truth for their transactions. Analytical systems replicate and reshape that data; they should not silently become a competing write path for operational state.

## Warehouse, lake, and lakehouse

- A **data warehouse** provides managed, query-oriented structures and governance for analytical workloads.
- A **data lake** stores large volumes of files, often including raw data and formats with different schemas.
- A **lakehouse** combines file/object storage with table metadata and transaction features intended to improve reliable analytical access.

These labels describe broad design approaches, not interchangeable product guarantees. Compare transaction behavior, concurrency, catalog integration, schema evolution, retention, recovery, workload isolation, and total operating cost for the selected implementation.

## File formats

| Format | Useful characteristics | Tradeoffs to consider |
|---|---|---|
| CSV | Simple, inspectable, widely supported | Weak typing, large scans, escaping and delimiter ambiguity |
| JSON | Flexible nested records and broad API support | Repeated field names, schema inconsistency, expensive analytical scans |
| Avro | Compact row-oriented encoding with schema support | Less efficient than columnar formats for many analytical projections |
| Parquet | Columnar encoding, compression, and column pruning | Small files and poor partitioning can still create expensive workloads |

Choose based on how data is written and read, schema needs, ecosystem support, and debugging requirements. A format alone does not provide table-level atomic commits or safe concurrent updates.

## File format vs table format

A file format defines how records are encoded. A table format adds metadata about files and table state, and may provide capabilities such as snapshots, atomic metadata changes, schema evolution, partition evolution, and time travel. Apache Iceberg, Delta Lake, and Apache Hudi are examples with different feature sets and operational models; verify behavior in the chosen engine and catalog.

## Transactions, snapshots, and recovery

ACID describes atomicity, consistency, isolation, and durability for transactions within a defined system boundary. Do not assume one transaction spans every source, object store, catalog, and consumer. Understand commit protocols, concurrent-writer behavior, snapshot expiration, and recovery semantics for the actual platform.

Snapshots can support reproducible reads and rollback, but they consume storage and need retention policies. Test restore and time-travel behavior before depending on it during an incident.

## Physical design

Partition by commonly filtered fields only when partition pruning is useful. Too many tiny partitions or files increase metadata and scheduling overhead. Columnar compression and column pruning can reduce scans, but query shape, file size, clustering, and engine behavior all matter. Separate compute from storage where the platform supports it and where workload isolation or independent scaling is valuable.

## Practice

For an order analytics workload, choose where OLTP records live, where immutable raw copies land, and how curated tables are stored. Compare CSV, JSON, and Parquet for one source. Document table format capabilities, transaction boundaries, partition choice, retention, concurrent writes, and how a corrupted daily load can be restored.