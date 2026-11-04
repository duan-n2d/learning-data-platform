---
title: Phase 1 - Core Foundation
description: Month 1-2 focus on the core skills that AI cannot replace.
order: 1
tags: [sql, python, dbt, airflow, cloud]
---

# Phase 1 - Core Foundation

Phase 1 is about becoming technically solid before relying on AI. AI can speed up coding, but it cannot replace your understanding of data quality, modeling, orchestration, and debugging. Plan for 8 weeks at roughly 6-8 focused hours per week; adjust the pace, but keep the order because each skill depends on the previous one.

## Outcomes

By the end of this phase, you should be able to:

- Explain the grain and keys of a dataset before joining or aggregating it.
- Trace a datum from an operational system through storage and transformation to an analytical consumer.
- Choose an ingestion and storage pattern that matches freshness, history, and recovery needs.
- Write analytical SQL with explicit time boundaries, null handling, and tested edge cases.
- Build a repeatable Python ingestion job that is safe to rerun.
- Transform raw data into documented staging models and business marts.
- Schedule dependent work with observable failures and intentional retries.
- Describe where data is stored, who can access it, and how a pipeline recovers from failure.

## Eight-week sequence

| Week | Focus | Practice | Evidence of completion |
|---|---|---|---|
| 1 | Platform architecture and SQL grain | Trace an order from OLTP source to an analytical consumer; profile a small dataset | A lifecycle diagram, data dictionary, and row-count profile |
| 2 | Storage, warehouses, and analytical SQL | Compare OLTP/OLAP, file/table formats, and query a representative dataset | A storage decision note and window-function fixtures |
| 3 | Python ingestion, incremental loads, and CDC concepts | Load a file or paginated API; define keys, watermarks, and replay behavior | A rerunnable ingestion job with structured logs and deduplication |
| 4 | Data modeling and ERDs | Design facts/dimensions; compare logical and physical models | Grain statements, keys, an ERD, and justified modeling choices |
| 5 | dbt or equivalent transformations | Add staging, intermediate, and mart models | Tests, generated docs, and a clean build |
| 6 | Quality and contracts | Define accepted schema, freshness, and business rules | Tests that fail on intentionally bad input |
| 7 | Orchestration and recovery | Schedule the pipeline and simulate a failed task | A successful rerun and a failure runbook |
| 8 | Cloud and delivery | Store an immutable raw snapshot and publish a trusted mart | Architecture diagram and project demo |

## Weekly study loop

1. Read one concept and write down the assumptions it makes about the data.
2. Implement the smallest useful example without an AI assistant.
3. Use AI to review the implementation, then verify every suggested change against tests or documentation.
4. Record one failure mode and how you detected it.
5. Commit a working checkpoint with a concise README update.

This keeps AI in the reviewer and accelerator role rather than making it the source of truth.

## Focus areas

| Area | Outcome |
|---|---|
| SQL | Window functions, CTEs, query plans, analytical patterns, and explicit grain |
| Python | File/API ingestion, pagination, validation, logging, and automation |
| Architecture and storage | OLTP/OLAP, warehouse/lake/lakehouse, file/table formats, and recovery boundaries |
| Ingestion | Full snapshots, incremental watermarks, CDC, schema change, streaming concepts, and backfills |
| Data modeling | ERDs, conceptual/logical/physical models, facts, dimensions, normalization tradeoffs, and history |
| Transformations | Staging-to-mart layers, tests, documentation, and lineage in dbt or an equivalent tool |
| Orchestration | Dependencies, idempotency, retries, backfills, and scheduling |
| Cloud fundamentals | Object storage, managed databases, least-privilege access, and deployment |

## Exit checklist

- [ ] A new developer can run the project from a clean checkout using documented steps.
- [ ] Re-running ingestion does not silently duplicate the same source records.
- [ ] Tests cover at least one key constraint, one accepted-value rule, and one business invariant.
- [ ] A deliberately broken input is rejected or quarantined with an actionable error.
- [ ] A failed task can be retried without corrupting already-published data.
- [ ] The warehouse has a documented grain, ownership, and freshness expectation.
- [ ] Storage and ingestion choices have documented tradeoffs for history, freshness, and recovery.
- [ ] The model has a reviewed ERD and explains its normalization or denormalization choices.

## Field guide readings

- [Data Engineering Foundations](../skills/field-guide/foundations.html)
- [Modern Data Infrastructure](../skills/field-guide/infrastructure.html)
- [Data Transformation and Processing](../skills/field-guide/transformation-and-processing.html)

## Deliverable

Use the [platform architecture](../skills/data-engineering/platform-architecture-and-lifecycle.html), [storage and table formats](../skills/data-engineering/storage-warehousing-and-formats.html), [ingestion, CDC, and streaming](../skills/data-engineering/ingestion-cdc-and-streaming.html), and [data modeling](../skills/data-engineering/data-modeling.html) lessons while building [Project 1: Core Analytics Warehouse](../projects/project-1-analytics-warehouse.html). Do not move on because the code runs once; move on when its output is reproducible and its failure modes are understood.
