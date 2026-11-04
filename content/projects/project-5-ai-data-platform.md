---
title: Project 5 - AI Data Platform
description: Combine warehouse, Text2SQL, RAG, extraction, monitoring, and docs.
order: 5
tags: [platform, ai, portfolio]
---

# Project 5 - AI Data Platform

## Goal

Combine Projects 1-4 into a coherent, operable portfolio platform. The capstone is successful when the data remains trustworthy and the AI components can be inspected, evaluated, limited, and switched off independently.

## Components

- Static learning docs website
- Analytics warehouse
- Text2SQL chatbot
- RAG knowledge assistant
- LLM extraction pipeline
- Monitoring dashboard
- Project documentation

## Reference architecture

```text
Source systems -> raw storage -> transformations -> governed marts
										 |               |
										 |               +-> Text2SQL (read-only)
										 +-> quality checks and lineage

Docs + glossary -> permission-aware retrieval -> cited RAG answers
Documents -> extraction + validation -> human review -> approved records

All services -> metrics, traces, audit events, evaluation runs, and alerts
```

Keep shared contracts (metric definitions, schemas, identifiers, and ownership) in version control. The warehouse, RAG index, and extraction outputs have different freshness and quality characteristics; make those differences visible instead of presenting them as one indistinguishable assistant.

## Capstone scenario and architecture decisions

Use one consistent portfolio scenario: an online retailer with orders, order lines, customers, a product catalog, internal runbooks, and a small set of invoice-like documents. Synthetic data is sufficient; avoid using real personal or payment data. Reuse the same order and product identifiers across the warehouse, BI, Text2SQL, and documentation examples so the integration is demonstrable.

Write a short architecture decision record before implementation:

| Decision | Baseline choice | When to extend |
|---|---|---|
| Ingestion | Daily batch snapshot plus an incremental lookback | Add CDC when source volume or freshness requirements justify log capture |
| Storage | Raw immutable files, then curated analytical tables | Choose a lakehouse/table format when snapshots, concurrent writes, or schema evolution require it |
| Transformations | Staging, intermediate logic, and dimensional serving marts | Add a historized integration model if source reconciliation requires it |
| Layering | Define raw, validated, and serving guarantees explicitly | Use bronze/silver/gold labels only if each layer has a clear contract |
| Ownership | One small platform team with named data-product owners | Consider domain-federated ownership when multiple teams can support shared standards |
| Serving | One BI view and a read-only Text2SQL surface over the same metric definitions | Add an API or federation only for a demonstrated consumer need |
| AI automation | RAG and extraction with review; agents may read and draft | Require approval for writes, deployments, reruns, or costly actions |

Do not adopt streaming, Data Mesh, Data Vault, or an autonomous agent just to make the architecture look advanced. State the requirement that would justify each extension and how it changes operations, cost, ownership, and recovery.

## Learning artifacts in this capstone

- Use [platform architecture](../skills/data-engineering/platform-architecture-and-lifecycle.html) and [storage and table formats](../skills/data-engineering/storage-warehousing-and-formats.html) to produce the architecture diagram, layer contracts, and a format/storage decision note.
- Use [ingestion, CDC, and streaming](../skills/data-engineering/ingestion-cdc-and-streaming.html) to document batch behavior, deduplication, late updates, replay, and the threshold for moving to CDC.
- Use [data modeling](../skills/data-engineering/data-modeling.html) to publish a conceptual sketch, an ERD, grain statements, and a dimensional model. Explain why Data Vault or another pattern is not required for the baseline if it adds no value.
- Use [data governance and data products](../skills/data-engineering/governance-and-data-products.html) to define owners, catalog metadata, lineage, access roles, retention, and change policy.
- Use [analytics serving and BI](../skills/data-engineering/analytics-serving-and-bi.html) plus [query engine performance](../skills/data-engineering/query-engines-and-performance.html) to show one consistent metric in BI and Text2SQL and include a measured query-plan note.
- Use [orchestration](../skills/data-engineering/orchestration.html) to define a recoverable DAG or asset workflow, idempotent outputs, backfill steps, and production ownership.
- Use [AI agents for data work](../skills/ai/ai-agents-for-data-work.html) only for a bounded read-and-draft workflow; document tools the agent cannot call and when a human must approve.
- Use the [Data Engineering lifecycle](../skills/data-engineering/lifecycle-and-practice.html) to define support, change, and deprecation responsibilities after the demo.

## Integration order

1. Make Project 1 reproducible and publish a small set of stable marts.
2. Add metric definitions and launch Project 2 against a read-only role.
3. Index a curated documentation corpus for Project 3; verify authorization before generation.
4. Process a limited document type in Project 4 and require review for uncertain or high-impact fields.
5. Add a shared status page, evaluation reports, runbooks, and a single end-to-end demo.

## Operational scorecard

| Area | Signals to report | Example response |
|---|---|---|
| Data quality | Freshness, test failures, rejected rows | Hold publication and notify the model owner |
| Text2SQL | Correctness, policy rejection, latency, scan cost | Disable execution while preserving question capture |
| RAG | Retrieval quality, citation validity, abstention rate | Rebuild or roll back the index |
| Extraction | Field accuracy, review rate, queue age, cost | Pause publishing and keep sources queued |
| Platform | Availability, dependency health, spend, access events | Follow a documented incident and rollback plan |

Choose thresholds from a baseline and user impact; do not alert on every model variation. Every alert needs an owner and a next action.

## Security and governance review

- Use separate least-privilege identities for ingestion, transformation, and query execution.
- Classify sensitive fields and define retention before sending data to an external model.
- Keep secrets in a secret manager or environment configuration, never in prompts or source control.
- Apply authorization before retrieval and before database access, not only in the UI.
- Log enough provenance for audit while avoiding unnecessary raw personal data.
- Document model/provider, prompt, schema, and corpus versions for reproducibility.
- Maintain a human escalation path and a non-AI fallback for critical workflows.

## Final demo narrative

Demonstrate one source record flowing into a tested mart; ask a supported metric question and inspect its definition and SQL; answer a documentation question with a verifiable citation; extract one document and review its evidence; then show an intentionally failing test and the corresponding alert or recovery action. Include one unsupported request and show the system declining it safely.

## Portfolio rubric

| Dimension | Strong evidence |
|---|---|
| Data engineering | Clear grains, repeatable loads, tested models, lineage, and recovery |
| AI reliability | Versioned evaluations, source evidence, abstention, and review paths |
| Security | Permission boundaries, least privilege, data minimization, and auditability |
| Operations | Useful metrics, actionable alerts, runbooks, cost awareness, and rollback |
| Communication | Architecture, tradeoffs, limitations, and a reproducible demo |

## Final outcome

A portfolio platform that demonstrates core Data Engineering and practical AI augmentation. Publish a short case study with architecture, evaluation results, known limitations, operating cost assumptions, and the next improvement you would make. Never present a prototype's evaluation scores as a production guarantee.
