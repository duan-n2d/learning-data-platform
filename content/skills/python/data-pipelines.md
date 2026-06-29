---
title: Python for Data Pipelines
description: Use Python for extraction, validation, orchestration helpers, and automation.
order: 1
tags: [python, pipeline]
---

# Python for Data Pipelines

Python is used to glue systems together: APIs, files, validation, batch jobs, and orchestration.

## Starter pattern

```python
from pathlib import Path
import json

def read_json_files(folder: str):
    for path in Path(folder).glob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            yield json.load(f)
```

## Production mindset

Good Python pipeline code should have logging, validation, retries, tests, and clear error messages.
