---
title: Python for Data Pipelines
description: Use Python for extraction, validation, orchestration helpers, and automation.
order: 1
tags: [python, pipeline]
---

# Python for Data Pipelines

Python is used to glue systems together: APIs, files, validation, batch jobs, and orchestration.

## Pipeline shape

Keep the stages explicit: acquire input, validate it, transform it, write output, and report a run summary. Separate pure transformation functions from network and filesystem code so business logic can be tested without external services.

## Starter pattern

```python
from pathlib import Path
import json

def read_json_files(folder: str):
    for path in Path(folder).glob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            yield json.load(f)
```

For a paginated API, persist a cursor or watermark only after the corresponding data has been durably written. Respect rate limits, set connect and read timeouts, retry transient failures with bounded exponential backoff, and stop retrying permanent client errors.

## Reliability checklist

- **Idempotency:** use a stable source key or content hash so a retry does not duplicate output.
- **Checkpoints:** record progress only after a batch is committed.
- **Validation:** check required fields, types, key uniqueness, and domain rules at the boundary.
- **Logging:** include run ID, source, batch, row counts, duration, and failure category; avoid logging secrets or full sensitive payloads.
- **Failure handling:** distinguish retryable network failures from invalid data and programming errors.
- **Resource limits:** stream large inputs, bound concurrency, and close files and responses reliably.
- **Testing:** cover empty input, malformed records, duplicate input, partial failure, and rerun behavior.

## Small validation example

```python
def validate_order(record: dict) -> None:
    required = {"order_id", "created_at", "currency", "amount"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if record["amount"] < 0:
        raise ValueError("amount must be non-negative")
```

In production, use typed models or a schema validation library when the contract is larger. Keep error messages actionable and avoid coercions that silently change meaning.

## Production mindset

Good Python pipeline code should have logging, validation, bounded retries, tests, and clear error messages. It should also expose a useful run summary: input rows, accepted rows, rejected rows, output location, and the run's source watermark.

## Notebooks: from exploration to a pipeline step

Notebooks are a reasonable place to explore data, but left unmanaged they produce **notebook sprawl**: each analyst or engineer keeps their own copy of similar exploratory logic in a separate notebook, duplicated and slowly drifting apart, with no single shared source of truth for what the "right" version of a transformation is. The symptom is usually several near-identical notebooks solving the same problem slightly differently, none of them owned or tested, and no way to tell which one produced a given result.

**Papermill** is the concrete mechanism for turning a notebook into a reusable, production pipeline step instead of a one-off manual artifact. It parameterizes a notebook by injecting values into a cell tagged `parameters`, executes the notebook programmatically from the command line or from code, and saves a new output notebook that contains the run's results alongside the original cells. That output notebook is itself the run's record: inputs, code, and rendered results together, inspectable after the fact.

```bash
papermill analysis.ipynb runs/analysis_2026-11-17.ipynb -p run_date 2026-11-17 -p min_amount 0
```

Because a parameterized, programmatically executed notebook is just another command with inputs and outputs, an orchestrator such as Dagster or Airflow can run it as one step in a scheduled pipeline — with the same retries, logging, and dependency tracking as any other task — rather than relying on someone to open and re-run it by hand.

**Failure modes.** Treating the interactively-developed notebook as production-ready without clearing hidden state (variables left over from manual exploration that do not exist on a fresh run); skipping validation inside the notebook because "it ran without errors" is not the same as correct output; letting the output notebooks pile up ungoverned, which recreates notebook sprawl one layer down.

**Validation.** Execute the notebook fresh (no leftover kernel state) as part of the check before scheduling it; assert on the notebook's own output values, not just its exit code; keep the parameterized notebook and its tests in version control like any other pipeline code, and treat the output notebook as a run artifact, not the source of truth.

## Practice

Extend the starter reader to count malformed files without aborting the whole batch, emit a structured summary, and produce the same output when run twice on unchanged input. Document whether bad files are skipped, quarantined, or fatal and why.
