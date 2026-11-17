---
title: Pipeline Orchestration
description: Schedule data work with clear dependencies, retries, backfills, and recovery.
order: 3
tags: [orchestration, airflow, reliability]
---

# Pipeline Orchestration

An orchestrator coordinates work; it should not hide business logic inside a maze of task definitions. Keep tasks small enough to observe and recover, but not so small that scheduling overhead dominates the pipeline.

## Model the dependency graph

Represent real dependencies explicitly. For example, ingest a source partition, validate it, transform staging, build marts, run reconciliation, then publish. Independent sources can run concurrently if resource limits and downstream expectations allow it.

A task should have a clear input, output, owner, timeout, and failure category. Prefer passing references to durable data over passing large payloads through orchestration metadata.

## DAGs, assets, and execution styles

A task-centric DAG describes operations and their dependencies. An asset-oriented workflow centers on produced datasets or other durable outputs, their lineage, and the checks that make them usable. Both can work; choose the abstraction that makes ownership, freshness, and recovery easiest to understand.

Imperative orchestration spells out how to execute steps. Declarative orchestration describes desired outputs, dependencies, and conditions while a tool plans execution. Functional data engineering favors deterministic transformations of explicit inputs into versioned outputs; isolate side effects such as network calls and writes at the edges. These ideas complement one another but do not remove the need for idempotency and operational checks.

Tools occupy different, overlapping roles. Airflow is commonly used to schedule task graphs; Dagster emphasizes software-defined data assets and their observability; dbt and SQLMesh focus on versioned analytical transformations and model dependencies; notebooks are useful for exploration but need additional controls before production scheduling. Check current product capabilities and deployment constraints instead of selecting by label alone.

## Idempotency and retries

Design tasks so retrying the same input produces the same committed result. Use stable keys, partition replacement, transactional writes, or merge semantics appropriate to the destination. Retries are for transient failures such as timeouts or temporary service errors; deterministic invalid input should fail clearly rather than retry forever.

Use bounded exponential backoff and jitter for transient dependencies. Make retry count and timeout visible. A task that finishes after its caller timed out may still have written data, so use idempotent outputs and reconciliation rather than assuming failure means no side effects.

## Backfills and schedules

Distinguish event time from processing time. A daily run should declare which business interval it processes and which timezone defines the boundary. Backfills should use the same transformation code as scheduled runs, with an explicit date range and controlled concurrency.

For late-arriving data, use a documented lookback or correction process. Do not rely on a single ever-advancing watermark if the source can revise older records.

**Backfill failure modes.** Running a backfill is not the same operation as running a normal scheduled interval repeated many times; it fails in its own ways:

- **Resource overload:** too many backfill tasks running concurrently compete for the cluster or warehouse capacity that regular scheduled runs need, so a backfill can starve the pipelines it was meant to repair. Mitigate with concurrency limits or dedicated pools that cap how many backfill tasks run at once, separate from the capacity reserved for scheduled runs.
- **Cost overload:** reprocessing weeks or months of data at once can spike compute or warehouse cost well beyond what a single scheduled run costs, often without anyone noticing until the bill arrives. Mitigate by chunking the backfill into smaller date ranges and monitoring cost as each chunk completes, instead of launching the full range at once.
- **"Lost in the middle" on partial failure:** a long-running backfill fails partway through, and it becomes unclear which date ranges succeeded, which failed, and which never ran at all. Mitigate with idempotent writes plus an explicit per-chunk completion log or checkpoint, so a retry can determine exactly what is missing and reprocess only that, rather than the whole range or nothing.

## Operational signals

Track run start/end, task attempts, input/output counts, freshness, duration, and failure category. Alert on missed delivery expectations and persistent failures, not on every transient retry. Link alerts to a runbook with an owner, safe retry steps, and escalation guidance.

## Go deeper

- [Cron and orchestrators compared](orchestrators-compared.html): when cron is enough, and Airflow, Dagster, Prefect, and Mage side by side.
- [DataOps, CI/CD, and infrastructure as code](dataops-ci-cd-and-iac.html): CI/CD for data, continuous deployment, data as code, and Terraform.
- [Containers and Kubernetes for data](containers-and-kubernetes-for-data.html): Docker images for pipeline tasks and running them on Kubernetes.

## Practice

Draw a DAG for daily orders and customer data feeding a revenue mart. Mark tasks that may run in parallel, define an idempotency strategy for each write, and simulate a failure after staging but before publication. Show how a retry avoids duplicate facts and how the incident is detected.