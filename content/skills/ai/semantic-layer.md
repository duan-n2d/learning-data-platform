---
title: Semantic Layer
description: Control business logic so humans and LLMs query metrics consistently.
order: 1
tags: [semantic layer, metrics, text2sql]
---

# Semantic Layer

A semantic layer defines trusted business entities, dimensions, metrics, and relationships.

## Why it matters for LLMs

LLMs can generate SQL, but they need controlled context. Without a semantic layer, the model may use the wrong table, wrong join path, or wrong metric definition.

## Example metric definition

```yaml
metrics:
  total_revenue:
    type: sum
    expression: revenue_amount
    entity: order
    filters:
      - payment_status = 'paid'
```
