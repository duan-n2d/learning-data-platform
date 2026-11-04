---
title: SQL Query Optimization
description: Practical performance patterns for analytical queries.
order: 2
tags: [sql, performance]
---

# SQL Query Optimization

Optimization starts with understanding data volume, join cardinality, indexes, partitions, and query plans.

## A repeatable tuning loop

1. Define the expected result and capture a baseline query and runtime on representative data.
2. Inspect the query plan for scans, joins, sorts, spills, and estimates that differ sharply from actual row counts.
3. Check table grain and join cardinality before changing syntax.
4. Make one change at a time and verify results are identical.
5. Compare runtime and resource use under the same conditions; keep the change only if it helps the relevant workload.

SQL engines differ, so use the documentation and plan format for your warehouse rather than assuming a pattern transfers unchanged.

## Checklist

- Filter early when possible.
- Avoid accidental many-to-many joins.
- Check table grain before joining.
- Use partitions or clustering for large fact tables.
- Materialize repeated transformations.
- Select only the columns needed by downstream steps.
- Compare estimated and actual rows around joins and filters.
- Use partition filters that match the table's partition key and required time range.
- Check whether a correlated subquery can be expressed more clearly as a join or window operation.
- Measure before adding indexes, clustering, or materialization; each has write, storage, and maintenance cost.

## Join fanout example

If an order has 3 line items and 2 status-history records, joining both child tables before aggregation can produce 6 rows for that order. A sum of order-level revenue is then multiplied. Aggregate each child to the intended join grain first, or join only the relation needed for the question.

## What not to optimize blindly

- A shorter query is not necessarily a faster query.
- A CTE may be inlined or materialized depending on the engine.
- Filtering early helps only when it reduces work and can be pushed into the scan.
- Approximate aggregates trade accuracy for performance and need explicit product approval.

## Practice

Take a slow query with one fact table and two dimensions. Write down each table's grain, expected join cardinality, and filtered row count. Compare the plan before and after one change, then reconcile the results on a small exact fixture.
