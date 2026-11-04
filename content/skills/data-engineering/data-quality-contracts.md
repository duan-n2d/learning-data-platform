---
title: Data Quality and Contracts
description: Turn source expectations and business rules into observable checks.
order: 2
tags: [data quality, contracts, testing]
---

# Data Quality and Contracts

A data contract makes expectations explicit between a producer and its consumers. It should describe more than column names: include meaning, ownership, change policy, delivery expectations, and what happens when the contract is violated.

## Contract dimensions

| Dimension | Example expectation |
|---|---|
| Schema | `order_id` is a non-null string; `created_at` is a UTC timestamp |
| Keys | `order_line_id` is unique within the source system |
| Domain | `status` is one of the documented lifecycle values |
| Relationships | Every published order line references a known order |
| Freshness | The latest complete business date arrives by an agreed time |
| Volume | A large deviation from the usual row count triggers investigation |
| Semantics | `net_amount` excludes cancelled lines and includes approved discounts |
| Ownership | A named producer and consumer own changes and incidents |

## Test at the right boundary

Validate incoming shape and required fields at ingestion. Test transformations for keys, relationships, and business logic. Check freshness and volume as operational signals. No single layer replaces the others: a schema-valid dataset can still be semantically wrong, while a business-rule test may not detect a missing partition.

Separate hard failures from warnings. A broken primary key may block publication; a mild volume shift may page an owner or create a review task. Choose behavior based on downstream impact and document it.

## Example SQL checks

```sql
-- Duplicate key check: expect zero rows.
select order_line_id, count(*) as row_count
from stg_order_lines
group by order_line_id
having count(*) > 1;
```

```sql
-- Reconciliation check: investigate any unexplained difference.
select
  sum(source_amount) as source_total,
  sum(model_amount) as model_total,
  sum(source_amount) - sum(model_amount) as difference
from daily_reconciliation;
```

Run checks on representative historical data as well as today's partition. A check that only looks at the latest batch may miss a delayed correction or a broken backfill.

## Failure handling

When a check fails, preserve enough context to diagnose the issue: run ID, source partition, failed rule, affected row count, and a secure sample if permitted. Quarantine invalid rows when safe; otherwise block the affected model. Never silently drop records and report a successful run. Make replay and recovery procedures explicit.

## Practice

Write a contract for a customer event stream. Include a schema change policy, uniqueness expectation, allowed event names, freshness target, and owner. Introduce a duplicate key and a late event in test data; verify the system reports each failure differently.