---
title: Modern Data Infrastructure Field Guide
description: Compare storage, warehouses, lakehouses, query engines, open formats, and analytics infrastructure.
order: 2
tags: [infrastructure, warehouse, lakehouse, query engines]
---

# Modern Data Infrastructure Field Guide

Infrastructure choices should follow data shape, access patterns, latency, team capacity, governance, and cost. A list of products is not a target architecture: understand the boundary each component owns and the failure modes it introduces.

## Start from the workload

Classify the workload before choosing a system:

- Transactional writes and short key-based reads usually belong in an OLTP database.
- Repeated scans, joins, and aggregations across history are analytical workloads (OLAP).
- Local exploration on files may not need a cluster or managed warehouse.
- Shared production analytics needs governed concurrency, predictable operations, access controls, and recovery.
- Streaming workloads have event-time and lateness requirements that batch systems may not satisfy.

Measure the expected data volume, number of users, concurrency, freshness, retention, recovery objective, and sensitive-data boundaries. Revisit these assumptions as usage grows.

## Warehouses, lakes, and lakehouses

A cloud data warehouse typically manages storage metadata, query planning, and compute for SQL analytics. Providers differ in workload isolation, transaction support, open-format integration, governance, and pricing. Compare the workload behavior and operational contract, not feature labels alone.

Object storage offers durable, relatively low-cost storage for files and snapshots, but files alone do not provide table transactions, concurrency control, or a governed schema. A data lake commonly stores multiple formats and stages of data. A lakehouse adds a table metadata and transaction layer intended to make files behave more like managed analytical tables. Exact guarantees depend on the table format, catalog, and engine combination.

Microsoft Fabric is an example of a managed analytics platform that combines data movement, storage, transformation, and BI experiences. Evaluate how its integrated services fit identity, governance, portability, capacity management, and existing tools; do not assume a unified interface removes architectural boundaries.

## File formats and open table formats

| Format | Shape and common use | Important limitation |
|---|---|---|
| CSV | Simple interchange and human inspection | Types, nulls, escaping, and schema are external conventions |
| JSON | Nested API and event payloads | Repeated keys and inconsistent records can increase scan cost |
| Avro | Row-oriented records with schema support | Column projection is not its primary strength |
| Parquet | Columnar analytical storage with compression and pruning | Small files, skew, and poor partitioning still hurt performance |

A **file format** encodes records. A **table format** tracks table state across files and may provide atomic metadata updates, snapshots, schema/partition evolution, and time travel. Apache Iceberg and Delta Lake are widely used examples; they differ in implementation, catalog integration, engine support, and operational behavior. Test the exact capabilities required rather than assuming every engine supports every feature identically.

Open table formats can reduce coupling between storage and compute. They do not guarantee effortless portability: catalogs, access controls, data types, transaction semantics, maintenance jobs, and extensions can remain engine-specific.

## DuckDB, Arrow, and DataFusion

DuckDB is an embedded analytical database often useful for local exploration, reproducible scripts, and querying local or object-store data without operating a separate server. It is not automatically a replacement for a multi-user warehouse; concurrency, governance, workload isolation, and deployment needs determine fit.

Apache Arrow defines an in-memory columnar representation and a family of interoperability interfaces. Its goal is efficient data exchange between systems, not durable table management by itself. Arrow data can reduce serialization and copying when compatible systems share the representation.

DataFusion is an extensible query engine built around Arrow in the Rust ecosystem. It can be embedded to build query services or data applications. Using an engine framework means owning integration, planning choices, security, and operations that a managed warehouse might otherwise provide.

## Modern, open, and declarative stacks

A modern data stack often combines ingestion, object storage or a lakehouse, transformation, orchestration, catalog/governance, semantic serving, and BI. The stack should be drawn as data flows and ownership boundaries; tool categories overlap, and not every project needs a separate product for each layer.

An open data stack favors interoperable formats and replaceable components. Portability depends on contracts and compatible implementations, not merely on choosing open-source licenses. A declarative stack describes desired assets, dependencies, and checks so tools can plan work. Inspect generated plans and side effects even when the configuration is declarative.

## Metrics layer and analytical serving

A metrics layer centralizes measures and their semantics so different dashboards, APIs, and applications can reuse definitions. It should specify grain, filters, time basis, dimensions, units, and aggregation behavior. A metrics layer does not repair ambiguous business meaning: metric owners must agree on definitions and maintain examples.

## Infrastructure decision checklist

- Which system is authoritative, and what data must be retained for replay?
- Which latency and concurrency targets are real user requirements?
- What are the transaction and schema-evolution guarantees at each layer?
- Can the required engines read and write the chosen format through the chosen catalog?
- How are access, lineage, retention, and deletion enforced across copies?
- What will compute, storage, egress, maintenance, and idle capacity cost?
- Who operates upgrades, compaction, recovery, and incidents?

## Practice

Design infrastructure for a small retailer with daily orders, a product catalog, a local analyst workflow, and a governed reporting service. Choose the OLTP source, raw storage format, curated table format, query engine, and BI serving layer. State why DuckDB is or is not sufficient for each use case and how the design changes if order freshness moves from daily to a few minutes.

## Continue learning

- [Storage, warehousing, and table formats](../data-engineering/storage-warehousing-and-formats.html)
- [Query engines and performance](../data-engineering/query-engines-and-performance.html)
- [Analytics serving and BI](../data-engineering/analytics-serving-and-bi.html)
- [Project 1: Core Analytics Warehouse](../../projects/project-1-analytics-warehouse.html)