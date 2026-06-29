---
title: Text2SQL Patterns
description: Convert business questions into validated SQL with guardrails.
order: 2
tags: [text2sql, llm, sql]
---

# Text2SQL Patterns

Text2SQL is not only prompt engineering. It is a system design problem.

## Recommended flow

```txt
Question
→ intent detection
→ semantic context retrieval
→ SQL generation
→ SQL validation
→ dry-run
→ result explanation
```

## Guardrails

- Only allow SELECT queries.
- Limit scanned tables.
- Validate columns and joins.
- Compare generated SQL against known examples.
- Store failed questions for evaluation.
