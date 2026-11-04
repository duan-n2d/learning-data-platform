---
title: Analytics Data Modeling
description: Design facts, dimensions, grains, and history for reliable analytics.
order: 1
tags: [data modeling, warehouse, dimensional modeling]
---

# Analytics Data Modeling

A good analytical model makes the meaning and grain of data obvious. It is not just a set of tables that happens to answer today's dashboard question.

## Start with grain

Write one sentence describing what one row represents before choosing columns. Examples:

- One row per order line as recorded by the source.
- One row per customer per calendar day with at least one qualifying activity.
- One row per account balance snapshot at the end of each UTC day.

The grain determines which measures can be safely aggregated and which joins preserve meaning. A primary key should identify one row at that grain; if it does not, explain the composite key or deduplication rule.

## Facts and dimensions

A fact table records events or periodic measurements. A dimension describes the context in which facts occurred.

| Model | Example grain | Typical contents |
|---|---|---|
| `fct_order_lines` | One row per order line | Quantity, gross amount, discount, event timestamps |
| `fct_daily_inventory` | One row per product, location, and day | On-hand quantity, reserved quantity |
| `dim_customer` | One row per customer version | Segment, region, account status |
| `dim_date` | One row per calendar date | Week, month, fiscal period, holiday flags |

Use surrogate keys when warehouse identity differs from source identity or when history must be retained. Keep source keys for traceability. Avoid storing descriptive attributes redundantly in every fact unless there is a deliberate performance or snapshotting reason.

## Slowly changing attributes

For a Type 1 change, overwrite an attribute when historical values are not needed. For a Type 2 change, keep versions with `valid_from`, `valid_to`, and an `is_current` flag. Facts must join to the dimension version valid at the event time when historical reporting depends on the attribute as it was then.

Define timezone and interval boundaries explicitly. A common convention is half-open validity intervals: `valid_from <= event_time AND event_time < valid_to`. This avoids overlapping adjacent versions.

## Join safety

Before a join, state the grain on both sides and expected cardinality. A one-to-many join can multiply fact rows; aggregate the many-side to the target grain first when appropriate. For many-to-many relationships, use an explicit bridge and define allocation behavior if measures are distributed across the relationship.

## Modeling levels and ERDs

- A **conceptual model** names business concepts and how they relate, without committing to storage details.
- A **logical model** defines entities, attributes, identifiers, and relationship cardinality.
- A **physical model** maps those decisions to tables, columns, types, keys, partitions, and engine-specific constraints.

An entity-relationship diagram (ERD) is useful only when its entity definitions and cardinalities are clear. Mark optional relationships, identifying keys, and the grain of event entities. Use the conceptual model to resolve business meaning before optimizing the physical schema.

## Normalization and denormalization

Normalization separates facts that belong to different entities and reduces update anomalies in operational systems. First, second, and third normal form are useful ways to reason about repeating groups and dependencies; they are not a requirement to split every analytical model into the maximum number of tables.

Analytical marts often denormalize dimensions or precompute derived values to make common access patterns easier and more consistent. Denormalization adds duplicated state that needs a clear owner, refresh strategy, and reconciliation. Choose based on workload and semantics rather than treating either style as universally correct.

## Dimensional planning and Data Vault

A bus matrix lists business processes against shared dimensions. It helps teams agree which dimensions, such as date, customer, product, or location, should be conformed across facts before building many independent marts.

Dimensional modeling is effective for stable, decision-oriented analytics. Data Vault separates business keys and relationships into hubs and links, with satellites retaining descriptive history and source context. It can help integrate many changing sources and preserve auditability, but it introduces more structures and transformations. Choose it when source integration and historical traceability justify the complexity; it is not automatically a better reporting model. Some platforms use a historized integration layer and publish dimensional marts for consumption.

## Other modeling approaches

- **Inmon-style enterprise modeling** commonly integrates an enterprise-wide, normalized warehouse before publishing downstream marts. It emphasizes shared consistency but may require more upfront coordination and design.
- **Kimball-style dimensional modeling** builds around business processes, facts, and conformed dimensions, often delivering usable marts incrementally. A bus matrix helps keep those marts consistent.
- **Anchor Modeling** is a historized relational approach that separates stable identities from changing attributes and relationships. It can support frequent schema evolution but adds concepts and joins; use it when its temporal flexibility solves a real problem.
- **Activity schemas** represent business events as append-oriented activities with timestamps, actors, and related entities. They can make event-centered analysis flexible, but consumers still need explicit event definitions, deduplication rules, and derived state when they need current snapshots.

These are design families, not competing laws. A platform may use a normalized integration layer, historized structures, and dimensional serving marts for different needs. Choose the simplest approach that supports integration, history, change, and consumption requirements.

## Master and reference data

Master data describes shared business entities such as customer or product; reference data provides controlled values such as country codes or statuses. Identify authoritative sources, cross-system keys, match/merge rules, and conflict ownership. Preserve source identifiers and history so a unified entity does not erase provenance.

## Practical review checklist

- [ ] Every model has a grain statement and stable key.
- [ ] Measures are classified as additive, semi-additive, or non-additive.
- [ ] Timestamps include timezone and business-date rules.
- [ ] History behavior is intentional for changing attributes.
- [ ] Join keys and cardinality are tested.
- [ ] Null, unknown, and late-arriving records have documented treatment.
- [ ] Conceptual, logical, and physical decisions are separated and reviewed at the appropriate level.
- [ ] Normalization or denormalization is justified by update behavior and consumer workload.
- [ ] Shared dimensions and master/reference identifiers have clear ownership.

## Practice

Model a subscription business with subscriptions, invoices, invoice lines, customers, and plans. State each table's grain, identify a metric that would be double-counted by a naive join, and choose which customer attributes need historical versions.