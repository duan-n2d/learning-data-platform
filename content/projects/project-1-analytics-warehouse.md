---
title: Project 1 - Core Analytics Warehouse
description: Build the warehouse foundation for later AI analytics projects.
order: 1
tags: [warehouse, dbt, sql]
---

# Project 1 - Core Analytics Warehouse

## Goal

Build a clean, reproducible analytics warehouse from raw data to business marts. Use a public or synthetic orders dataset; keep the project small enough to understand every transformation.

## Learning goals

- State the grain, key, and update behavior of each important table.
- Separate ingestion from business transformations and retain a traceable raw layer.
- Make transformations deterministic and safe to rerun.
- Test technical constraints and business expectations independently.

## Architecture

```txt
Raw files/API
-> immutable raw snapshots
-> staging (rename, cast, deduplicate)
-> intermediate business logic
-> marts (facts and dimensions)
-> metrics, dashboards, and Project 2
```

### Example model contract

```text
Model: fct_orders
Grain: one row per source order line
Primary key: order_line_id
Time basis: order_created_at in UTC
Measures: quantity, gross_amount, discount_amount, net_amount
Late updates: source may correct status for 7 days
Owner: analytics engineering
Freshness target: available by 07:00 UTC on weekdays
```

Write this contract before choosing joins. If a join changes the stated grain, either aggregate the other side first or explain why the new grain is intended.

## Suggested build sequence

1. Inventory source files or API endpoints; record schema, volume, and update cadence.
2. Land source records with ingestion time and source identifier. Preserve the original payload for debugging.
3. Profile nulls, duplicate keys, timestamp ranges, and unexpected categories.
4. Build staging models that make types and naming consistent without hiding source meaning.
5. Add intermediate models for reusable calculations such as order status history.
6. Publish a fact table and dimensions with documented grains and relationships.
7. Test a clean build, an incremental build, and a rerun of the same input.
8. Document how to backfill a date range and how to recover from a partial failure.

## Example analytical check

Before publishing daily revenue, decide whether cancelled orders, refunds, and multiple currencies are included. Then compare a small hand-calculated fixture with the model result. A test can prove that the calculation matches the defined rule; it cannot choose the business rule for you.

## Deliverables

- Source data contracts
- Raw snapshots with ingestion metadata
- Staging models
- Fact and dimension marts with grain documented
- Key, relationship, accepted-value, freshness, and business-rule tests
- Model documentation and lineage
- Data quality report with known limitations
- Clean setup instructions and a simple architecture diagram

## Acceptance criteria

- A clean checkout can load a sample dataset and build all models using documented commands.
- Repeating an ingestion or transformation run does not double-count unchanged source records.
- Every published model has a stated grain, key, and owner.
- At least one invalid source row is surfaced or quarantined rather than silently lost.
- A sample report reconciles to a manually verified result.
- Tests fail when a duplicate key or invalid business status is introduced.

## Stretch work

- Add incremental processing with a bounded lookback for late-arriving records.
- Add a source freshness check and a small data-diff report between runs.
- Compare a partitioned query plan with an unpartitioned baseline using representative data.

## Output used by next project

Project 2 uses these marts as its allowlisted, trusted SQL surface. Keep semantic definitions beside the models so metric logic does not drift between the warehouse and chatbot.
