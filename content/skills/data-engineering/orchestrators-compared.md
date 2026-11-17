---
title: Cron and Orchestrators Compared
description: Know when cron is enough, and compare Airflow, Dagster, Prefect, and Mage for scheduling lakehouse and warehouse pipelines.
order: 43
tags: [orchestration, cron, Airflow, Dagster, Prefect, Mage, scheduling]
---

# Cron and Orchestrators Compared

[Pipeline orchestration](orchestration.html) covers the principles: dependencies, idempotency, retries, backfills. This page is about tools. It starts with the simplest scheduler that exists, explains exactly what it lacks, and then compares four orchestrators using the same small pipeline:

```text
extract_orders(day) -> validate_orders(day) -> build_marts(day) -> refresh_semantic_cache
```

Each step processes one UTC business day and writes idempotently (partition overwrite), so it can be retried or backfilled safely.

## Cron

**What it is.** Cron is the Unix daemon that runs commands on a time-based schedule. Each line in a crontab has five time fields followed by a command:

```text
┌ minute (0-59)
│ ┌ hour (0-23)
│ │ ┌ day of month (1-31)
│ │ │ ┌ month (1-12)
│ │ │ │ ┌ day of week (0-6, Sunday = 0)
│ │ │ │ │
15 2 * * *  command
```

The same five-field syntax is reused by many systems — Kubernetes CronJobs, GitHub Actions `schedule`, cloud schedulers, and every orchestrator on this page — so it is worth learning precisely.

**How it works.** The cron daemon wakes up every minute, checks which entries match the current time, and starts those commands. That is all. It does not know whether the previous run finished, succeeded, or is still running; it does not retry; it does not know that `build_marts` depends on `extract_orders`.

**Concrete example (illustrative crontab).**

```bash
# Run in UTC regardless of the server's local timezone (supported by cronie and some others;
# otherwise set the system timezone or compute the date inside the script)
CRON_TZ=UTC
# 02:15 UTC daily; flock prevents overlapping runs; output goes to a dated log
15 2 * * * flock -n /tmp/orders.lock /opt/pipelines/run_orders.sh "$(date -u -d yesterday +\%F)" >> /var/log/orders/$(date -u +\%F).log 2>&1
```

Note the escaped `%`: in a crontab, an unescaped `%` is turned into a newline.

**Failure modes.**

- *Overlap*: a slow run is still going when the next one starts; without a lock both write the same partition.
- *Silent failure*: a non-zero exit code goes to a log nobody reads, or to local mail.
- *Missed runs*: if the machine is down at 02:15, that run simply never happens (no catch-up).
- *Timezone and DST*: local-time schedules run twice or not at all around daylight-saving changes.
- *Day-of-month and day-of-week*: when both are restricted, most cron implementations run when *either* matches, which surprises people.
- *Hidden dependencies*: chaining jobs by time ("extract at 2:00, transform at 3:00") breaks the first time extract takes 61 minutes.

**Validation.** Check expressions with a tool that prints the next run times; make scripts exit non-zero on failure and send that to an alert; write a heartbeat (last successful date) that a monitor checks for freshness.

**When cron is enough, and when an orchestrator wins.**

| Cron is fine | Use an orchestrator |
|---|---|
| One self-contained job (e.g. a nightly vacuum or compaction) | Several steps with dependencies |
| Missing a run occasionally is acceptable | Missed runs must be detected and caught up |
| Logs on one machine are enough | Run history, lineage, and a UI are needed by several people |
| No backfills | Backfills over date ranges with controlled concurrency |
| No need to react to data arriving | Event- or data-driven triggers |

A pragmatic path: start with cron plus the guards above for one job, and move to an orchestrator when you add the second dependent step.

## The orchestrator landscape

**Airflow** (Apache) is the most widely deployed orchestrator. You define DAGs of tasks in Python; a scheduler triggers runs per data interval; executors run tasks on workers, Celery, or Kubernetes pods. It has a very large ecosystem of provider packages. Airflow 3 (released 2025) reworked several areas, including DAG versioning and renaming "datasets" to "assets" for data-aware scheduling — confirm which major version your platform runs before copying examples.

**Airflow operator choice.** The same Airflow task can run its business logic through different operators, and the choice is really about where the code executes and what it is coupled to:

- **PythonOperator** runs the task's business logic inline in the Airflow worker process. It is the simplest to write and debug, but it couples your code tightly to the Airflow worker's own Python environment and installed dependencies, so a library version conflict between two tasks becomes an Airflow deployment problem. *Recommendation:* a small team on a single, well-controlled Python stack.
- **DockerOperator** runs the task in its own container, decoupling the task's dependencies from the worker's environment. It needs Docker available to (or reachable from) the worker, and adds image-build and registry steps to the development loop. *Recommendation:* teams that need dependency isolation but already manage container images and don't need full Kubernetes.
- **KubernetesPodOperator** runs the task as its own Kubernetes pod with its own image, resource requests, and lifecycle. It gives the strongest isolation and lets teams contribute tasks in any language or image, not just Python, at the cost of added infrastructure complexity and pod-startup latency on every task run. *Recommendation:* mixed-language teams, or any team hitting heavy dependency conflicts between tasks that DockerOperator alone does not resolve cleanly.

**Dagster** is asset-oriented: you declare the datasets (assets) your code produces, their dependencies, partitions, and checks. Run history is organized around assets, which makes freshness and lineage visible by default.

**Dagster and AI-agent tooling.** Dagster has invested in making its asset graph legible to AI agents and lower-code to maintain. It ships an MCP server that exposes the asset graph, catalog, and run/check status so an AI agent can answer "what feeds this table" or "why did this asset fail" without a human tracing code by hand. It also supports **Dagster Components**: asset definitions expressed in YAML rather than Python, aimed at letting an agent (or a less Python-fluent contributor) declare a new asset without writing a full definition by hand. Treat both as productivity aids, not a replacement for reviewing what gets deployed: a component or an agent-authored asset still needs the same ownership, checks, and change review as hand-written code.

**Dagster deployment options.** Production Dagster can run several ways, each with a different control-versus-effort tradeoff:

- **Self-hosted on Kubernetes via Helm** — full control over infrastructure, versions, and network boundaries, at the cost of operating and upgrading the cluster yourself.
- **Docker Compose** — a lighter self-hosted option for smaller setups or a single host; simpler than Kubernetes but with fewer scaling and isolation guarantees.
- **AWS ECS** — self-hosted on managed container orchestration; less Kubernetes operational overhead, still your AWS account and cost to manage.
- **Dagster+ (managed)** — Dagster's own hosted offering; fastest to stand up and least operational burden, but less control over infrastructure placement, upgrade timing, and network boundaries than self-hosting.

Both are covered conceptually in [Pipeline orchestration](orchestration.html). The two tools below are newer alternatives with different ergonomics.

## Prefect

**What it is.** Prefect is an open-source Python workflow orchestrator (with a commercial cloud offering). Its design goal is to make ordinary Python functions observable, retryable, and schedulable with minimal ceremony.

**How it works.** You decorate functions with `@flow` and `@task`. Flows can call tasks and other flows with normal Python control flow — loops, conditionals, dynamic fan-out — rather than declaring a static graph up front. Retries, timeouts, caching, and result persistence are configured on decorators. A **deployment** attaches a schedule (cron, interval) or event trigger to a flow; **work pools** and **workers** decide where runs execute (a local process, Docker, Kubernetes, serverless containers). Prefect also has an event system and automations (for example "if this flow fails twice, notify and pause").

**Concrete example (illustrative, Prefect 3-style).**

```python
from datetime import date, timedelta
from prefect import flow, task, get_run_logger

@task(retries=3, retry_delay_seconds=[10, 60, 300], timeout_seconds=900)
def extract_orders(day: date) -> str:
    # writes s3://lake/raw/orders/dt=<day>/ with overwrite semantics
    return f"s3://lake/raw/orders/dt={day}"

@task
def validate_orders(path: str) -> None:
    ...  # raise ValueError on contract violation: deterministic, so no retries

@task(retries=1)
def build_marts(day: date) -> None:
    ...  # e.g. dbt build --select marts --vars '{day: ...}'

@flow(log_prints=True)
def daily_orders(day: date | None = None) -> None:
    day = day or date.today() - timedelta(days=1)
    path = extract_orders(day)
    validate_orders(path)
    build_marts(day)
    get_run_logger().info("published %s", day)

if __name__ == "__main__":
    daily_orders.serve(name="daily-orders", cron="15 2 * * *")  # schedule in UTC by default
```

**Failure modes.** Dynamic Python logic that makes the graph hard to reason about; relying on in-memory results that disappear when a worker restarts (persist results or pass references to durable storage); retries on validation errors that can never succeed; deployments drifting from the code in Git.

**Validation.** Unit-test task functions as plain Python; run the flow locally against a fixture day; check that a forced failure in `validate_orders` stops the flow without retries; keep deployment definitions (e.g. `prefect.yaml`) in version control.

## Mage

**What it is.** Mage is an open-source data pipeline tool (with a commercial Pro edition) that combines a notebook-style browser editor with a scheduler. Pipelines are built from **blocks** — data loaders, transformers, data exporters, sensors, and SQL or dbt blocks — that run in sequence and pass data frames between them.

**How it works.** Each block is a Python, SQL, or R file in a project directory, decorated to declare its role, with optional `@test` functions that run after the block. You can run a block interactively and see its output, which suits exploration. **Triggers** run pipelines on a schedule, on an event, or through an API call. Because blocks pass data in memory by default, it is most comfortable for small to medium data or when blocks push work down to an engine.

**Concrete example (illustrative Mage transformer block).**

```python
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def keep_paid_orders(df, *args, **kwargs):
    paid = df[df["payment_status"] == "paid"].drop_duplicates("order_id")
    return paid

@test
def test_unique_and_non_negative(output, *args) -> None:
    assert output["order_id"].is_unique, "duplicate order_id"
    assert (output["amount_usd"] >= 0).all(), "negative amount"
```

**Failure modes.** Notebook-style interactive state that differs from a clean scheduled run; large data frames passed between blocks exhausting memory; business logic in the tool's UI rather than in reviewed code; fewer integrations and a smaller community than Airflow.

**Validation.** Run every pipeline end to end from a clean start in CI; keep block tests meaningful (uniqueness, ranges, row counts); check that the project directory, not the UI, is the source of truth in Git.

## Side-by-side

| | Airflow | Dagster | Prefect | Mage |
|---|---|---|---|---|
| Core abstraction | Task DAG per data interval | Software-defined assets | Python flows and tasks | Blocks in a pipeline |
| Graph definition | Static (dynamic mapping available) | Asset dependencies | Dynamic, runtime Python | Ordered blocks, notebook-style |
| Backfills | Built-in, by data interval | Partition-aware | By parameterized runs | Supported, less central |
| Data awareness | Assets (Airflow 3), sensors | Native (freshness, checks, lineage) | Events and automations | Block tests, sensors |
| Typical strength | Ecosystem, maturity, hiring | Asset lineage and quality | Low-ceremony Python | Fast interactive building |
| Typical risk | Operational complexity, task-centric sprawl | Learning the asset model | Graph clarity with heavy dynamism | Scale and production discipline |

**How to choose.** List your must-haves — backfill style, data awareness, deployment target (Kubernetes, managed service), team skills, existing ecosystem — and build the same three-step pipeline in your top two candidates. Measure how long it takes to add a failing check, run a seven-day backfill, and find out why a run failed. Product capabilities change quickly; verify current documentation rather than relying on comparison tables, including this one.

## Connection to the governed analytics assistant

The assistant is only as trustworthy as its freshest certified data. Whatever orchestrator you choose, make it publish a machine-readable status — "`fct_orders` complete through 2026-11-16, checks passed" — that the assistant reads before answering. If the latest run failed or is late, the assistant should say so ("data is current through 2026-11-15") rather than answer silently from stale tables. Refreshing the semantic-layer cache should be the last step of the pipeline, not a separate clock-based job.

## Practice

1. Schedule `run_orders.sh` with cron, including a lock, UTC handling, failure exit codes, and a heartbeat file. Make it fail once and confirm you would notice.
2. Implement the same four-step pipeline in two of Airflow, Dagster, Prefect, or Mage (all can run locally or in Docker).
3. In each, simulate a transient failure in `extract_orders` (retry succeeds) and a contract failure in `validate_orders` (no retry, clear error).
4. Backfill 2026-11-01 to 2026-11-07 with at most two concurrent days and confirm partitions are not duplicated.
5. Emit a freshness status file or table at the end of each run.

**Completion criteria.**

- A cron setup with documented failure detection, and a written reason for moving beyond it.
- Two working implementations with retries, a non-retried validation failure, and a successful backfill.
- Row counts per partition identical after running the backfill twice.
- A one-page tool decision with the measured times for the three tasks above.
