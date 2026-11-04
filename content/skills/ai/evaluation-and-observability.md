---
title: AI Evaluation and Observability
description: Measure AI workflow quality before release and detect changes after deployment.
order: 4
tags: [evaluation, observability, llm]
---

# AI Evaluation and Observability

A model response can be fluent and still be wrong. Evaluation turns vague quality expectations into testable examples; observability shows how the system behaves with real inputs, changing data, and production constraints.

## Build a useful evaluation set

Collect representative tasks and label the expected behavior, not just a reference answer. Depending on the workflow, record the expected source passages, metric definition, SQL result, extracted fields, abstention decision, or human-review route. Include normal cases, boundary cases, ambiguous requests, unsupported questions, and known failure modes.

Keep evaluation data separate from prompt examples where practical. Version the dataset, labels, model, prompt, retrieval configuration, parser, and relevant corpus snapshot. Review a sample with domain experts; an automatically generated label set can repeat the same hidden assumptions as the model.

## Use task-specific measures

| Workflow | Useful measures |
|---|---|
| Text2SQL | Result correctness, policy violations, clarification quality, query cost |
| RAG | Retrieval recall, citation correctness, groundedness, abstention quality |
| Extraction | Field-level precision/recall, numeric tolerance, schema failures, correction rate |
| All workflows | Latency, error rate, token/provider cost, review rate |

No single score describes the whole product. Keep quality, safety, and operational measures separate so a faster but less reliable change does not look like an overall improvement.

## Release and regression practice

Establish a baseline before changing a model, prompt, tool, parser, corpus, or semantic definition. Run the fixed evaluation set, inspect regressions by failure category, and require review for high-impact changes. Use a staged rollout where possible and keep a rollback path.

## Production observability

Capture request and run identifiers, component versions, timing, validation outcomes, retrieval sources, and human decisions. Avoid storing raw sensitive content unless there is a documented need, access policy, and retention window. Redact secrets and personal data before logs or traces leave the trusted boundary.

Define service indicators users care about: availability, freshness, answer or extraction quality, review queue age, and cost per useful result. Set alert thresholds from observed baselines and impact. Every alert needs a responsible owner and a clear next step.

## Practice

Create a 20-example evaluation set for one workflow. Include at least three examples that should be refused or escalated. Run two prompt versions, compare task-specific quality and latency, inspect every regression, then write a short release decision with known limitations.