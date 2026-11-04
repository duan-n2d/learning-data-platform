---
title: Phase 2 - Modern Analytics + AI Bridge
description: Month 3-4 connect modern analytics stack with AI analytics patterns.
order: 2
tags: [semantic layer, text2sql, metrics]
---

# Phase 2 - Modern Analytics + AI Bridge

Phase 2 focuses on the bridge between trusted data engineering and AI-assisted analytics. Plan for weeks 9-16. The goal is not to make a model write SQL at any cost; it is to make a narrow, measurable analytics workflow safer and easier to use.

## Outcomes

- Define metrics once and make their grain, filters, time basis, and owner explicit.
- Retrieve only the schema and business context relevant to a question.
- Generate SQL against an allowlisted analytics surface, then validate it before execution.
- Explain results with units, time ranges, and links to the underlying definition.
- Serve consistent, governed metrics across BI, APIs, and Text2SQL.
- Read a query plan well enough to explain major scan, join, and materialization tradeoffs.
- Evaluate the system on a versioned set of realistic questions, including unanswerable ones.

## Eight-week sequence

| Week | Focus | Practice | Evidence of completion |
|---|---|---|---|
| 9 | Analytics architecture and serving | Trace a metric to a BI dashboard or analytics API | Lineage map, users, and freshness contract |
| 10 | Metrics and glossary | Define revenue, active customer, and order count | Reviewed metric contract with edge cases |
| 11 | Semantic model | Describe entities, dimensions, and valid join paths | Example queries generated from definitions |
| 12 | Question routing | Classify metric lookup, comparison, trend, or unsupported requests | Labeled routing fixtures |
| 13 | SQL generation and validation | Generate, parse, and dry-run read-only SQL | Adversarial validation tests |
| 14 | BI and answer presentation | Compare one metric across a dashboard, API, and assistant | Consistency check with units and period labels |
| 15 | Evaluation and query performance | Review result correctness and inspect representative query plans | Versioned evaluation and tuning report |
| 16 | Governance and product hardening | Add ownership, catalog metadata, access boundary, logs, and limits | Project 2 demo and governance/risk register |

## Decision rule

If the question is ambiguous, unsupported, or outside the semantic model, ask a clarifying question or decline to run it. A graceful refusal is a correct result; a plausible but ungrounded number is not.

## Why semantic layer matters

Text2SQL is risky when the LLM does not understand business definitions. A semantic layer gives the model controlled metric definitions, entities, dimensions, and join paths.

For example, “revenue” could mean booked, invoiced, or paid revenue. The definition must specify the source, row grain, status filters, currency treatment, and event date. A glossary entry alone is not enough if executable logic still lives in an ambiguous prompt.

## Focus areas

- Modern Analytics Stack
- Metrics layer and business glossary
- Semantic model design
- Text2SQL prompt patterns
- SQL validation and guardrails
- Evaluation datasets for analytics questions
- Read-only execution identity and query limits
- Audit trail linking each answer to its definition and generated SQL
- Data governance, catalog, lineage, and data product contracts
- BI serving, analytics APIs, OLAP, and federation tradeoffs
- Query plans, pushdown, materialized views, and workload cost

## Companion lessons

- [Data governance and data products](../skills/data-engineering/governance-and-data-products.html)
- [Analytics serving and BI](../skills/data-engineering/analytics-serving-and-bi.html)
- [Query engines and performance](../skills/data-engineering/query-engines-and-performance.html)
- [Semantic layer](../skills/ai/semantic-layer.html)

## Exit checklist

- [ ] Every supported metric has an owner, grain, definition, and tested example.
- [ ] Generated SQL is parsed and constrained before it reaches the warehouse.
- [ ] The database identity cannot modify data or read unrelated schemas.
- [ ] Queries have a timeout and a maximum result size or scan budget.
- [ ] Evaluation includes ambiguous, unsupported, and prompt-injection-style inputs.
- [ ] Users can inspect the metric definition and time range behind an answer.
- [ ] Ownership, classification, catalog entry, and lineage are documented for the supported data product.
- [ ] The chosen metric agrees across its BI, API, and Text2SQL surfaces, or documented differences are visible.
- [ ] A representative query plan and its main cost/performance tradeoffs are documented.

## Deliverable

Build [Project 2: Text2SQL Chatbot](../projects/project-2-text2sql-chatbot.html) on the trusted marts from Phase 1.

## Field guide readings

- [Modern Analytics Approaches](../skills/field-guide/analytics-approaches.html)
- [Data Transformation and Processing](../skills/field-guide/transformation-and-processing.html)
- [Modern Data Infrastructure](../skills/field-guide/infrastructure.html)
