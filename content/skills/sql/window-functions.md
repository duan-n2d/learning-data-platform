---
title: SQL Window Functions
description: Learn ranking, running totals, lag/lead, and analytical SQL patterns.
order: 1
tags: [sql, analytics]
---

# SQL Window Functions

Window functions allow you to calculate values across related rows while keeping row-level detail.

## The mental model

A window function computes over a set of rows related to the current row. Unlike `GROUP BY`, it does not collapse those rows. The `PARTITION BY` clause defines the group, `ORDER BY` defines sequence, and the frame defines which rows in that sequence contribute.

## Common patterns

```sql
select
  customer_id,
  order_date,
  revenue,
  sum(revenue) over (
    partition by customer_id
    order by order_date
  ) as running_revenue
from fact_orders;
```

## Ranking and deterministic latest rows

```sql
with ranked_events as (
  select
    customer_id,
    event_id,
    event_time,
    row_number() over (
      partition by customer_id
      order by event_time desc, event_id desc
    ) as row_num
  from customer_events
)
select customer_id, event_id, event_time
from ranked_events
where row_num = 1;
```

The second sort key makes ties deterministic. Use `row_number` when exactly one row should win, `rank` when ties should share a rank and leave gaps, and `dense_rank` when ties share a rank without gaps.

## Frame boundaries matter

For a running total, state the frame explicitly when the SQL dialect supports it:

```sql
sum(revenue) over (
  partition by customer_id
  order by order_date, order_id
  rows between unbounded preceding and current row
) as running_revenue
```

An ordered aggregate may use a default frame that includes peers with the same ordering value. `ROWS` counts physical rows; `RANGE` groups peers by ordering value. A unique tie-breaker and explicit frame prevent surprising jumps.

## Lag, lead, and change detection

```sql
select
  account_id,
  snapshot_date,
  balance,
  lag(balance) over (
    partition by account_id order by snapshot_date
  ) as prior_balance,
  balance - lag(balance) over (
    partition by account_id order by snapshot_date
  ) as balance_change
from daily_account_balances;
```

Decide what the first row means when no prior value exists. `lag` returns `NULL` by default; replacing it with zero is only correct if zero is the actual business baseline.

## Why it matters

Most analytics engineering work depends on understanding grain, partitions, ordering, and business metric logic.

## Practice

Given one row per order line, write a query that returns each customer's first order, latest order, and cumulative net revenue. Test a customer with one order, two orders at the same timestamp, a refund, and a null revenue value. State the expected result before running the query.
