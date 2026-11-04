---
title: Project 3 - RAG for Internal Data Docs
description: Build an assistant that answers questions from docs, schema, and glossary.
order: 3
tags: [rag, docs, ai assistant]
---

# Project 3 - RAG for Internal Data Docs

## Goal

Build a RAG assistant over a small, permission-labeled corpus of Markdown documentation, dbt docs, schema notes, and business glossary entries. The assistant should make it easier to find authoritative material, not replace the source of truth.

## Architecture

```txt
Docs
-> parse and attach source metadata / access labels
-> chunk and index
-> retrieve within the caller's permissions
-> rerank or filter evidence
-> answer with verifiable references or abstain
```

## Corpus and metadata

Keep the original source, canonical URL or path, title, owner, last-updated time, document version, and access label on every chunk. Exclude stale drafts and secrets. When a document changes, replace or version its chunks so retrieval does not mix old and new definitions.

Preserve headings and tables where possible. Start with chunks aligned to meaningful sections, then test a few chunk sizes against real questions. Overlap can help with definitions that cross boundaries, but too much overlap creates duplicates and wastes context.

## Retrieval and answer behavior

Use metadata filters before semantic retrieval when they represent hard boundaries such as project, source type, or access scope. Test whether a query finds the right passage, not only whether the final answer sounds plausible. Return source titles and direct references that let a person verify each important claim.

Retrieved text is untrusted content. It may contain stale instructions, hostile text, or misleading examples. The assistant should treat it only as evidence, follow application policy over document instructions, and avoid revealing content the current user cannot access. If sources conflict, say so and show both references; if evidence is missing, abstain.

## Evaluation

Create question-answer pairs with the expected source passages. Track retrieval recall at a small top-k, citation correctness, answer faithfulness, abstention quality, latency, and token cost. Include stale, conflicting, inaccessible, and no-answer cases. Review failures by stage: parsing, indexing, retrieval, generation, or authorization.

## Deliverables

- Document parser
- Chunking strategy
- Vector index
- Retrieval API
- Grounded answer UI
- Evaluation examples
- Permission-aware metadata filters
- Source versioning and stale-document removal
- Citation correctness and abstention tests
- Corpus refresh and index rollback procedure

## Acceptance criteria

- A reviewer can open each cited source and find the supporting passage.
- Users cannot retrieve documents outside their authorized scope.
- Updating or deleting a source removes stale content from retrieval.
- The assistant abstains on questions not supported by the indexed corpus.
- A fixed evaluation set reports retrieval and answer quality separately.
