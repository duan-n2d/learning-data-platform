---
title: RAG Pipeline for Internal Data
description: Build retrieval augmented generation over docs, schema, and business glossary.
order: 3
tags: [rag, vector db, documentation]
---

# RAG Pipeline for Internal Data

RAG helps answer questions using internal documentation, data dictionary, schemas, and project notes.

## Separate the pipeline stages

Treat ingestion, parsing, chunking, embedding, retrieval, reranking, and answer generation as independently testable stages. Store a corpus version and document metadata with each chunk. This lets you determine whether a wrong answer came from missing content, a poor retrieval match, or unsupported generation.

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

## Chunk and retrieve deliberately

Begin with section-aware chunks that retain headings and source identifiers. Compare a few chunk sizes against a fixed set of questions; do not assume one size fits runbooks, tables, and long narrative documents. Use metadata filters for source type, recency, project, and permission boundaries. Consider lexical retrieval for exact identifiers and error codes alongside semantic search.

## Grounding and citations

Return the source title and a stable section, page, or URL for each supporting passage. A citation should support the adjacent claim, not merely point to a broadly related document. When sources disagree or retrieval returns weak evidence, surface the conflict or abstain rather than blending unsupported details.

Retrieved content is data, not policy. Treat instructions found inside documents as untrusted text, and enforce user authorization before retrieval results reach the model.

## Measure quality

Keep a small labeled set with the relevant source passages. Track recall of expected passages, citation accuracy, answer faithfulness, abstention quality, latency, and cost. Re-run it after changing chunking, embedding model, corpus, retrieval settings, or prompt. Inspect failures by pipeline stage instead of tuning the prompt for every miss.

## Practice

Index a handful of technical documents and ask questions with exact names, paraphrased wording, no answer in the corpus, and conflicting versions. Verify the retrieved passages and citations manually before judging answer fluency.
