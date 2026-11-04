---
title: Project 4 - LLM Extraction Pipeline
description: Extract structured records from unstructured sources with validation.
order: 4
tags: [llm extraction, unstructured data, validation]
---

# Project 4 - LLM Extraction Pipeline

## Goal

Extract a defined set of business records from a representative collection of PDFs, emails, text files, or semi-structured notes. Preserve enough evidence for a reviewer to verify every high-impact field.

## Pipeline

```txt
Unstructured source
-> file/type checks and text extraction
-> deterministic normalization and page/source tracking
-> schema-constrained model extraction
-> syntax, business, and cross-field validation
-> review / quarantine / approved output
-> versioned warehouse records
```

## Output contract

Define the record before writing prompts. For each field, state its type, whether it is required, allowed values, normalization rules, and what to do when the source does not contain it. Represent absence as null or an explicit status; never encourage the model to fill gaps with plausible guesses.

```json
{
	"record_id": "source-system identifier or generated stable ID",
	"document_type": "invoice",
	"invoice_date": "2026-03-14",
	"currency": "USD",
	"total_amount": 1250.00,
	"supplier_name": "Example Supplier",
	"evidence": {
		"total_amount": {"page": 2, "quote": "Total due: $1,250.00"}
	},
	"review_status": "needs_review"
}
```

This is an illustrative contract, not a universal invoice schema. Keep evidence references tied to source offsets, pages, or stable text spans so corrections can be audited.

## Reliability and review

Make processing idempotent using a stable source identifier and content hash. Store the source version, parser version, prompt version, model identifier, processing time, validation errors, and reviewer decision. Retry transient provider errors with bounded backoff; do not retry permanent schema or input errors indefinitely.

Route records by both uncertainty and impact. A low-confidence supplier alias may need review; a high-value payment amount should be reviewed even when the model is confident. Calibrate confidence against a labeled set rather than treating a model's self-reported score as truth. Quarantine malformed or unsupported documents with a useful reason and a replay path.

Measure field-level precision/recall, exact-match or tolerance-based numeric accuracy, schema failure rate, review rate, correction rate, processing latency, and cost per accepted record. Split evaluation data by source or time to reduce leakage from near-duplicate documents.

## Deliverables

- Extraction schema
- Parser job
- Validation layer
- Error queue
- Review report
- Stable source ID and content hash for idempotent processing
- Field-level source evidence and processing provenance
- Quarantine queue with bounded retry and replay behavior
- Labeled evaluation set with field-level quality metrics

## Acceptance criteria

- Every output validates against a versioned schema before it reaches the warehouse.
- Missing values remain explicitly missing instead of being fabricated.
- A reviewer can trace each critical field to source evidence.
- Reprocessing the same source version does not create duplicate records.
- Low-confidence or high-impact records are routed for review according to documented rules.
- The pipeline can be paused or rolled back without losing source documents or review history.
