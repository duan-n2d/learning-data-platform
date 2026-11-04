---
title: Phase 3 - AI-Native Workflows
description: Month 5-6 apply RAG, extraction, and AI-assisted coding to daily data work.
order: 3
tags: [rag, extraction, ai coding]
---

# Phase 3 - AI-Native Workflows

Phase 3 adds AI to bounded, reviewable workflows: documentation search, unstructured extraction, code review, and incident investigation. Plan for weeks 17-24. Keep deterministic parsing and validation wherever they work; use an LLM for the parts that genuinely require language understanding.

## Outcomes

- Build retrieval that finds the right source and preserves access boundaries.
- Extract structured records into a versioned schema with evidence and review states.
- Measure quality before rollout and monitor it after model or prompt changes.
- Route uncertain or high-impact outputs to a person rather than silently accepting them.
- Decide when a fixed workflow is preferable to an AI agent and bound any agent tools and side effects.
- Operate the complete portfolio with runbooks, cost controls, and clear ownership.

## Eight-week sequence

| Week | Focus | Practice | Evidence of completion |
|---|---|---|---|
| 17 | Retrieval foundations | Create a small, permission-labeled documentation corpus | Corpus inventory and baseline questions |
| 18 | Chunking and retrieval | Compare chunk sizes, overlap, and metadata filters | Retrieval results with relevance judgments |
| 19 | Grounded answering | Require source references and abstention when evidence is missing | Citation and unanswerable-question tests |
| 20 | Structured extraction | Extract a stable schema from representative documents | Validated records with source spans |
| 21 | Human review | Define confidence and impact-based review queues | Review UI or queue and adjudication notes |
| 22 | Evaluation and monitoring | Track quality, latency, failures, and cost | Dashboard plus alert thresholds |
| 23 | AI-assisted engineering and agents | Compare a deterministic workflow with a bounded tool-using assistant | Agent threat cases, tool policy, and human-approval test |
| 24 | Capstone lifecycle and operations | Integrate projects, rehearse recovery, and review ongoing ownership | Project 5 demo, runbook, service review, and retrospective |

## Safety and quality gates

- Never place secrets or unnecessary personal data in prompts or logs.
- Treat retrieved documents as untrusted input, not as instructions to the system.
- Keep a stable evaluation set and rerun it after model, prompt, parser, or corpus changes.
- Record provenance so a reviewer can trace an output to its source and processing version.
- Have a rollback path that disables AI while leaving the underlying data workflow usable.

## Focus areas

- RAG over internal documentation
- LLM extraction from PDFs, emails, and semi-structured text
- Evaluation and guardrails
- AI-assisted coding workflow
- Monitoring and human review loops
- Prompt and model versioning
- Access control, data minimization, and retention
- Operational runbooks and rollback plans
- Agent tool boundaries, approval gates, traceability, and a kill switch
- Data Engineering lifecycle, support ownership, and portfolio evidence

## Companion lessons

- [AI agents for data work](../skills/ai/ai-agents-for-data-work.html)
- [Data Engineering lifecycle and practice](../skills/data-engineering/lifecycle-and-practice.html)
- [AI evaluation and observability](../skills/ai/evaluation-and-observability.html)

## Exit checklist

- [ ] RAG answers cite sources and abstain when retrieved evidence is insufficient.
- [ ] Extracted records pass schema and business validation before publication.
- [ ] Low-confidence or high-impact records enter a review queue.
- [ ] Evaluation results are reproducible and compared across versions.
- [ ] Cost, latency, error rate, and review rate are observable.
- [ ] AI can be disabled without losing access to canonical data and runbooks.
- [ ] Agent tools have narrow permissions, bounded retries/cost, approval for consequential actions, and a safe stop path.
- [ ] The capstone names an owner, support path, change process, and conditions for deprecation.

## Field guide readings

- [Professional Development](../skills/field-guide/professional-development.html)
- [Specialized Data Technologies](../skills/field-guide/specialized-technologies.html)
- [Data Engineering Foundations](../skills/field-guide/foundations.html)

## Deliverable

Build [Project 3: RAG for Internal Data Docs](../projects/project-3-rag-internal-docs.html), [Project 4: LLM Extraction Pipeline](../projects/project-4-llm-extraction-pipeline.html), and the [Project 5 capstone](../projects/project-5-ai-data-platform.html).
