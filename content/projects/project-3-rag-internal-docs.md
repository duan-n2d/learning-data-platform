---
title: Project 3 - RAG for Internal Data Docs
description: Build an assistant that answers questions from docs, schema, and glossary.
order: 3
tags: [rag, docs, ai assistant]
---

# Project 3 - RAG for Internal Data Docs

## Goal

Build a RAG assistant over Markdown documentation, dbt docs, schema notes, and business glossary.

## Architecture

```txt
Docs
→ chunking
→ embeddings
→ vector DB
→ retrieval API
→ answer with references
```

## Deliverables

- Document parser
- Chunking strategy
- Vector index
- Retrieval API
- Grounded answer UI
- Evaluation examples
