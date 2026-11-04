---
title: Text2SQL Patterns
description: Convert business questions into validated SQL with guardrails.
order: 2
tags: [text2sql, llm, sql]
---

# Text2SQL Patterns

Text2SQL is not only prompt engineering. It is a system design problem.

## Make the task small

Expose a curated set of models, metrics, dimensions, and relationships. Retrieve relevant definitions for each question rather than sending the entire warehouse schema. Ask a clarification question when a date range, entity, or metric is underspecified.

## Recommended flow

```txt
Question
→ intent detection
→ semantic context retrieval
→ SQL generation
→ SQL validation
→ dry-run
→ result explanation
```

## Guardrails

- Only allow SELECT queries.
- Limit scanned tables.
- Validate columns and joins.
- Compare generated SQL against known examples.
- Store failed questions for evaluation.
- Enforce policy with a SQL parser, database permissions, timeouts, and result limits.
- Keep credentials and policy decisions outside model-generated code.
- Return the metric definition, period, filters, and query reference with the result.

## End-to-end states

Model the interaction as explicit states: `needs_clarification`, `unsupported`, `invalid_sql`, `query_rejected`, `query_failed`, and `answered`. This makes safe non-answers observable and gives the interface a clear recovery action. Do not retry rejected SQL by weakening policy; retry generation only within the same constraints and a bounded attempt count.

## Evaluation cases

For each fixture, record the natural-language question, expected metric, filters, date interpretation, expected result, and whether clarification is required. Add tests for ties, empty results, timezone boundaries, nulls, invalid joins, unsupported tables, and requests to bypass controls. Review semantic correctness separately from SQL formatting.

## Practice

Create five questions over a single orders mart. For each, write the expected metric contract and result before asking a model to generate SQL. Add one ambiguous question and one unsupported question; both should avoid database execution.
