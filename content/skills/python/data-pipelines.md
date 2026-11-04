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

## Practice

Extend the starter reader to count malformed files without aborting the whole batch, emit a structured summary, and produce the same output when run twice on unchanged input. Document whether bad files are skipped, quarantined, or fatal and why.
