---
title: SQL Query Optimization
description: Practical performance patterns for analytical queries.
order: 2
tags: [sql, performance]
---

# SQL Query Optimization

Optimization starts with understanding data volume, join cardinality, indexes, partitions, and query plans.

## Checklist

- Filter early when possible.
- Avoid accidental many-to-many joins.
- Check table grain before joining.
- Use partitions or clustering for large fact tables.
- Materialize repeated transformations.
