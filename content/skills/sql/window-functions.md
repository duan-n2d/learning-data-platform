---
title: SQL Window Functions
description: Learn ranking, running totals, lag/lead, and analytical SQL patterns.
order: 1
tags: [sql, analytics]
---

# SQL Window Functions

Window functions allow you to calculate values across related rows while keeping row-level detail.

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

## Why it matters

Most analytics engineering work depends on understanding grain, partitions, ordering, and business metric logic.
