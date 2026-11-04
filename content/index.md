---
title: AI-Augmented Data Engineering Roadmap
description: A detailed 24-week learning path for data engineering, analytics, and carefully evaluated AI workflows.
order: 1
tags: [data engineering, ai, roadmap]
---

# AI-Augmented Data Engineering Roadmap

> Core knowledge is not removed. It is solidified first. AI is then added in the right places to augment, not replace, the data engineering workflow.

This platform is a 24-week, project-led curriculum for building reliable analytics systems and adding AI where it can be evaluated and controlled. Each phase builds on the previous one; each project produces artifacts the next project can reuse.

<div class="card-grid">
  <div class="card"><h3>Weeks 1-8</h3><p>Build SQL, platform architecture, storage, ingestion/CDC, modeling, quality, orchestration, and cloud fundamentals.</p><a href="roadmap/phase-1-core-foundation.html">Open Phase 1</a></div>
  <div class="card"><h3>Weeks 9-16</h3><p>Connect governance, data products, BI/serving, query performance, semantic metrics, and bounded Text2SQL.</p><a href="roadmap/phase-2-modern-analytics-ai.html">Open Phase 2</a></div>
  <div class="card"><h3>Weeks 17-24</h3><p>Build grounded retrieval, evidence-backed extraction, evaluated AI agents, lifecycle operations, and an integrated capstone.</p><a href="roadmap/phase-3-ai-native-workflows.html">Open Phase 3</a></div>
</div>

## The learning path

Follow the sequence below. You can use different tools from the examples; preserve the data contracts, tests, and operational behavior that the tools are meant to support.

1. **Establish the data foundation.** Learn [platform architecture](skills/data-engineering/platform-architecture-and-lifecycle.html), [storage and table formats](skills/data-engineering/storage-warehousing-and-formats.html), [ingestion, CDC, and streaming](skills/data-engineering/ingestion-cdc-and-streaming.html), [SQL window functions](skills/sql/window-functions.html), [Python pipelines](skills/python/data-pipelines.html), and [analytics data modeling](skills/data-engineering/data-modeling.html).
2. **Make data dependable.** Define [quality contracts](skills/data-engineering/data-quality-contracts.html), practice [orchestration](skills/data-engineering/orchestration.html), and understand [governance and data products](skills/data-engineering/governance-and-data-products.html) as well as [cloud storage and access](skills/data-engineering/cloud-storage-and-access.html).
3. **Publish trusted analytics.** Build [Project 1](projects/project-1-analytics-warehouse.html), including source contracts, tested marts, freshness expectations, and a recovery path.
4. **Expose business meaning.** Define a [semantic layer](skills/ai/semantic-layer.html), serve it through [BI and analytics interfaces](skills/data-engineering/analytics-serving-and-bi.html), understand [query engines and performance](skills/data-engineering/query-engines-and-performance.html), then build [Project 2](projects/project-2-text2sql-chatbot.html) with a read-only query path and an evaluation set.
5. **Add grounded AI workflows.** Study [RAG](skills/ai/rag-pipeline.html) and [Text2SQL patterns](skills/ai/text-to-sql.html), then complete [Project 3: RAG](projects/project-3-rag-internal-docs.html) and [Project 4: extraction](projects/project-4-llm-extraction-pipeline.html) with citations, provenance, validation, and human review.
6. **Operate and communicate the system.** Apply [AI evaluation and observability](skills/ai/evaluation-and-observability.html), assess [AI agents for data work](skills/ai/ai-agents-for-data-work.html), use the [Data Engineering lifecycle](skills/data-engineering/lifecycle-and-practice.html), integrate the [capstone](projects/project-5-ai-data-platform.html), and publish its limitations as clearly as its strengths.
7. **Study the field guides.** Read the original [foundations](skills/field-guide/foundations.html), [infrastructure](skills/field-guide/infrastructure.html), [transformation and processing](skills/field-guide/transformation-and-processing.html), [analytics approaches](skills/field-guide/analytics-approaches.html), [specialized technologies](skills/field-guide/specialized-technologies.html), and [professional development](skills/field-guide/professional-development.html) chapters.
8. **Continue with external references.** Browse the [Data Engineering reading map](skills/references/data-engineering-reading-map.html) for source material and additional topics.

## What “done” means

- A clean checkout can reproduce the project from documented instructions.
- Data models state their grain, keys, owners, and freshness expectations.
- Tests cover schema, relationships, and business rules; failures are visible and actionable.
- AI outputs are grounded in approved data, constrained before execution, and evaluated against versioned examples.
- Uncertain, unsupported, or high-impact work has a clarification, abstention, or human-review path.
- The system has basic operational signals, a runbook, and a way to disable AI without losing access to canonical data.

## How to use this site

1. Start with Phase 1, then continue in order unless you already have evidence for a skill.
2. Use the skill pages as reference material while building the projects.
3. Keep a small work log: assumptions, decisions, failed tests, and what changed.
4. Treat model output as a proposal. Verify code and facts with tests, source documentation, or a domain owner.
5. Add project notes, diagrams, and examples as Markdown with the frontmatter format in the README.

## Performance model

Markdown files are compiled once at build time into static HTML. The browser loads the current page, shared assets, and a small static search index; no application database or runtime Markdown service is required.
