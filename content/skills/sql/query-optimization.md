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

## Why the optimizer picks a full table scan

A full scan reads every row in a table instead of using an index or partition pruning to skip rows. The cost-based optimizer chooses one when it estimates that scanning is cheaper than the alternative:

- No usable index exists on the filtered or joined column.
- The table is small enough that an index lookup's extra I/O is not worth it; scanning a few thousand rows can be cheaper than traversing an index structure.
- The query is unselective: it returns a large fraction of the table's rows, for example `WHERE status != 'cancelled'` on a table that is mostly active orders. An index helps when a query excludes most rows, not when it keeps most of them.
- A count or aggregate over the whole table (`SELECT count(*)`, `SELECT sum(amount)` with no filter) must touch every row regardless of indexing.
- Table statistics are stale, so the cost-based optimizer misjudges selectivity and picks a full scan (or an index) where the other would have been faster. Refreshing statistics is often the fix, not rewriting the query.

B-tree indexes and bitmap indexes avoid a scan in different situations. A B-tree index suits range queries, equality lookups, and sorted access on columns with many distinct values. A bitmap index suits low-cardinality columns (few distinct values, such as `status` or `region`) combined with `AND`/`OR` filters, which is common in warehouse fact tables; it is usually a poor fit for columns with frequent single-row updates.

## Common table expressions (CTEs)

A non-recursive CTE is a named, readable subquery you can reference later in the same statement; the engine may inline it into the plan or materialize it, so it does not guarantee a performance change by itself (see "What not to optimize blindly" below).

A recursive CTE walks a hierarchy or graph to any depth. It has two parts combined with `UNION ALL`: an **anchor member** that selects the starting rows, and a **recursive member** that joins the CTE to itself and is re-evaluated until it returns no more rows (the termination condition). Without a termination condition that eventually stops matching, the engine will loop until it hits an internal recursion limit.

Worked example: walking an employee-to-manager hierarchy to find every employee under a given manager, at any depth.

```sql
with recursive org_chart as (
    -- anchor member: the starting employee
    select employee_id, manager_id, full_name, 1 as depth
    from employees
    where employee_id = 100

    union all

    -- recursive member: each employee whose manager is already in the result
    select e.employee_id, e.manager_id, e.full_name, oc.depth + 1
    from employees e
    join org_chart oc on e.manager_id = oc.employee_id
)
select * from org_chart order by depth;
```

The same pattern applies to a bill-of-materials: a `part_id -> parent_part_id` self-reference walked the same way to explode a product into every sub-part at every level.

## What not to optimize blindly

- A shorter query is not necessarily a faster query.
- A CTE may be inlined or materialized depending on the engine.
- Filtering early helps only when it reduces work and can be pushed into the scan.
- Approximate aggregates trade accuracy for performance and need explicit product approval.

## Practice

Take a slow query with one fact table and two dimensions. Write down each table's grain, expected join cardinality, and filtered row count. Compare the plan before and after one change, then reconcile the results on a small exact fixture.
