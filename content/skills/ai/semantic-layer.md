---
title: Semantic Layer
description: Control business logic so humans and LLMs query metrics consistently.
order: 1
tags: [semantic layer, metrics, text2sql]
---

# Semantic Layer

A semantic layer defines trusted business entities, dimensions, metrics, and relationships.

## Model the business contract

Start with questions people actually ask. For each measure, record the business meaning, owner, source model, grain, filters, time basis, unit, currency behavior, and whether it is additive. For each dimension, define accepted values and how it relates to entities. Make join paths explicit and reject ambiguous paths instead of letting a consumer guess.

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

This example is intentionally incomplete for production. A useful definition should also identify currency conversion policy, the date used for reporting, treatment of refunds, source ownership, and a tested example. Prefer executable definitions in a reviewed semantic framework over maintaining a parallel prompt-only glossary.

## Grain and additivity

Suppose `fct_order_lines` has one row per line. `net_revenue` can be summed across lines if currency and refund rules are consistent. `distinct_customers` is not additive across days: adding daily distinct counts double-counts returning customers. Label non-additive and semi-additive metrics, and define the allowed aggregation behavior.

## Change management

- Assign an owner to every metric and a review path for definition changes.
- Keep definitions version controlled and link changes to affected reports or questions.
- Add canonical questions with expected results as regression fixtures.
- Communicate breaking changes and, where needed, version or deprecate metrics gradually.
- Check that the generated SQL matches the intended grain and filters.

## Practice

Define “monthly active customer” for a product. Specify the activity event, timezone, month boundary, identity rule, exclusions, and how late events are handled. Then write two questions that should produce the same result and one question that must not be answered from this metric.
