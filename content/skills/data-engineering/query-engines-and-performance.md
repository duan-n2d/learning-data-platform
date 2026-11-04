---
title: Query Engines and Performance Internals
description: Understand scans, pushdown, materialization, and distributed query tradeoffs.
order: 10
tags: [query engine, performance, OLAP, materialized views]
---

# Query Engines and Performance Internals

Query performance depends on data layout, SQL shape, engine planning, concurrency, and resource limits. Learn to read evidence from the plan and workload metrics instead of optimizing from syntax alone.

## A simplified query lifecycle

1. **Parse and validate:** check SQL syntax, names, types, permissions, and dialect rules.
2. **Plan:** resolve relations and choose join order, scan strategy, aggregation, and exchanges.
3. **Optimize:** estimate row counts and costs, simplify expressions, and push eligible work toward storage or source systems.
4. **Execute:** scan data, move intermediate results, join, aggregate, sort, and return output.
5. **Observe:** inspect actual rows, bytes read, spills, queue time, memory, and runtime.

The exact pipeline varies by engine. Compare estimates with actuals to locate a cardinality or statistics problem.

## Pushdown and data movement

Predicate pushdown applies filters near the data source; projection pushdown reads only required columns. Partition pruning skips irrelevant partitions, while columnar formats can skip unused columns and use statistics to avoid row groups. These optimizations are conditional: casts, functions, unsupported predicates, or source connectors can prevent pushdown.

Distributed joins may shuffle rows across workers. High-cardinality keys, skew, large intermediate results, and poor join order increase network and memory pressure. Check plans and skew rather than assuming a distributed engine makes every query cheap.

## Materialized views and caches

A materialized view stores a computed result for reuse. It can reduce repeated work but introduces refresh latency, storage cost, invalidation complexity, and possible freshness mismatch. Define who owns it, how it refreshes, which query shapes use it, and how results are reconciled with the base tables.

Caching is effective for repeated reads but may return stale data or produce contention. Make freshness behavior visible and avoid presenting cached results as current without a clear contract.

## Workload isolation and compute/storage

Separating compute from storage can scale workloads independently and isolate interactive BI from batch transformations. It does not remove contention automatically: shared quotas, metadata services, source systems, and concurrency limits can still bottleneck. Use workload classes and resource budgets tied to user impact.

## Read a plan empirically

- Find full scans and estimate bytes read; verify partition filters and selected columns.
- Inspect join input sizes, order, distribution, and actual row counts.
- Look for exchanges, skew, spills, and large intermediate results.
- Compare queue time with execution time to distinguish capacity from query inefficiency.
- Change one factor, compare results and resource use, and keep a reproducible baseline.

A full scan is not inherently wrong for a small table or a full-table aggregate. Optimize for measured workload cost and latency, not for eliminating a plan operator at any price.

## Distributed-system tradeoffs

Distributed systems trade among consistency, availability, latency, and failure tolerance according to the operation and system boundary. CAP is a narrow model about consistency and availability during a network partition, not a checklist for selecting a warehouse. For data platforms, understand the actual guarantees for transactions, replication lag, metadata commits, and reads after writes.

## Practice

Inspect a query joining a large fact table to two dimensions. Record bytes scanned, estimated/actual rows, exchanges, spills, and queue time. Test a partition filter and a pre-aggregation separately; reconcile the output and explain the tradeoff.