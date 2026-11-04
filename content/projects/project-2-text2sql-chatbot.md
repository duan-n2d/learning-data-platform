---
title: Project 2 - Text2SQL Chatbot
description: Build a chatbot that converts business questions into validated SQL.
order: 2
tags: [text2sql, chatbot, semantic layer]
---

# Project 2 - Text2SQL Chatbot

## Goal

Build a small analytics assistant that answers a bounded set of business questions using the marts from Project 1. Treat it as a read-only product with explicit limits, not as a general-purpose SQL console.

## Why this matters

Text2SQL is not just about generating SQL. It requires correct business logic, trusted metrics, semantic definitions, and validation.

## Architecture

```txt
User question
-> semantic context lookup
-> SQL generation
-> parse and policy validation
-> dry-run / cost estimate
-> read-only warehouse execution
-> result and provenance formatter
```

## Define the supported surface

Start with 3-5 reviewed metrics and a few dimensions. For each metric, capture:

| Field | Example question to settle |
|---|---|
| Name and owner | Who approves a definition change? |
| Grain | Is the metric counted per order, line, customer, or day? |
| Expression | Which trusted model and columns implement it? |
| Filters | Which statuses, channels, or test records are excluded? |
| Time basis | Which timestamp determines the reporting period? |
| Additivity | Can it be summed across time, customers, and currencies? |
| Examples | Which natural-language questions and expected results are canonical? |

Do not let the model invent a join path. Supply only relationships declared in the semantic model, and keep ambiguous metrics out of the supported set until an owner resolves them.

## Validation boundary

Use a SQL parser and a database identity restricted to approved schemas. The validator should reject multiple statements, writes, DDL, unapproved relations, unknown columns, and queries without bounded execution. A keyword check alone is not a security boundary: SQL has dialect features and nested syntax that require parsing and database permissions as defense in depth.

Before execution, apply a timeout and a result-row limit, and use the warehouse's dry-run or query-plan facility where available. Do not expose credentials to the model. Log the question, semantic context identifiers, model/prompt version, validation outcome, query identifier, and latency while minimizing sensitive query and result data.

## Evaluation plan

Build a versioned set of questions with expected metric, filters, time range, and result. Include:

- Direct lookups, time comparisons, rankings, and multi-filter questions.
- Ambiguous wording that should trigger clarification.
- Unsupported metrics and out-of-scope tables that should be declined.
- Boundary dates, empty results, null values, and ties.
- Inputs that attempt to override system rules or request private data.

Track execution success, result correctness, policy violations, clarification quality, latency, and cost separately. Exact SQL matching is usually too strict; compare the returned result and verify that the generated query obeys the intended metric contract.

## Deliverables

- Semantic metric definitions
- Prompt templates
- SQL validator
- Evaluation question set
- Web UI or Streamlit UI
- Error analysis report
- Read-only database role, statement timeout, and bounded results
- Audit events with model, prompt, metric, and query identifiers
- Clear abstention and clarification states in the UI

## Acceptance criteria

- Supported questions return correct results against a fixed test database.
- Ambiguous and unsupported questions do not result in guessed metrics or unsafe execution.
- The execution role cannot write data or read outside approved schemas.
- Every answer shows its metric definition, period, and relevant filters.
- Evaluation can be rerun after changing a prompt, model, or semantic definition.
