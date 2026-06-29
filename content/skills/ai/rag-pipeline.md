---
title: RAG Pipeline for Internal Data
description: Build retrieval augmented generation over docs, schema, and business glossary.
order: 3
tags: [rag, vector db, documentation]
---

# RAG Pipeline for Internal Data

RAG helps answer questions using internal documentation, data dictionary, schemas, and project notes.

## Pipeline

```txt
Markdown docs
→ chunking
→ embeddings
→ vector database
→ retrieval
→ grounded answer
```

## What to index

- Data dictionary
- dbt model docs
- Business glossary
- Pipeline runbooks
- Incident notes
