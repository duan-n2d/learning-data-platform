---
title: AI Agents for Data Work
description: Understand tool-using AI agents and place them inside bounded, observable data workflows.
order: 5
tags: [AI agents, agentic workflows, data engineering]
---

# AI Agents for Data Work

An AI agent uses a model to choose or sequence actions, often through tools, based on a goal and observed results. A workflow with one model call and fixed steps is usually better described as a chain. Use an agent only when adaptive tool selection adds measurable value over a simpler deterministic workflow.

## A bounded agent loop

```text
User goal
-> policy and scope check
-> model proposes a tool and arguments
-> application validates permissions and arguments
-> tool runs with bounded access and timeout
-> result is returned as untrusted evidence
-> model explains, asks, or proposes the next step
-> human approval for consequential actions
```

The application owns authorization and side effects. The model may suggest a query or action; it must not grant itself broader access or bypass validation based on tool output.

## Suitable data-engineering tasks

- Search approved documentation and return source references.
- Draft a SQL query for a human to review.
- Summarize failed pipeline logs with links to the run and relevant runbook.
- Propose tests or schema documentation for a reviewed change.
- Triage an extraction record into an explicit review queue.

Tasks that alter production data, change permissions, deploy code, or trigger costly jobs require stronger authorization and explicit confirmation. Fully autonomous execution is not the default.

## Tool and state design

Expose a small set of typed tools with narrow parameters and clear outputs. Validate every argument server-side, enforce identity and row/operation limits, and keep secrets outside model context. Make state changes explicit and auditable. Bound tool count, retries, wall-clock time, and spend; define a safe stop condition and a route to a person.

Treat retrieved documents, logs, database results, and tool errors as untrusted input. They may contain incorrect data or prompt injection. Separate policy instructions from evidence, constrain each tool independently, and test attempts to make the agent reveal data or call unauthorized tools.

## Evaluation and operations

Evaluate task success and correct tool choice separately. Include ambiguous goals, unavailable dependencies, misleading results, permission-denied cases, prompt injection, timeout, and actions needing approval. Track tool-call rate, invalid arguments, retries, escalation, latency, cost, and human override. Preserve traces with identifiers and versions while minimizing sensitive content.

Use a deterministic workflow if it is cheaper, more predictable, and easier to audit. If an agent is justified, deploy with staged access, human approval for risky effects, rollback, and a kill switch.

## Practice

Design an assistant that investigates a failed data freshness check. Allow it to read pipeline status, search approved runbooks, and draft a diagnosis. Do not allow it to rerun jobs or modify data without approval. Specify tool schemas, access scope, evaluation cases, logs, escalation, and stop conditions.