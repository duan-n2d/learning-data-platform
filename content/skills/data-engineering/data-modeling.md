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

## Modeling levels across the pipeline

The conceptual/logical/physical axis above is about how committed a model is to implementation detail. A second, complementary axis is about *where in the data lifecycle* a modeling decision is made. The same business entity is reasonably modeled differently at each stage, and that is not a contradiction to resolve — it reflects a different audience and a different concern at each point:

- **Source database schema**: owned by the application team, optimized for transactional correctness and single-row writes. Analytics teams rarely control it and should treat it as an external contract that can change without notice.
- **Integration / staging layer**: standardizes types, names, and keys across sources before any business logic runs. Usually close to the source grain, with light typing, renaming, and deduplication.
- **ETL / transformation layer**: modeled around the transformation steps themselves. Intermediate tables here exist to make a pipeline testable and debuggable, not to be queried directly by business consumers.
- **Warehouse / dimensional schema**: modeled for conformed, auditable reporting — the facts and dimensions described above.
- **BI / presentation layer**: modeled for how people explore it, often a further-denormalized or semantically labeled view (a single wide table, or a semantic layer's metric definitions) that trades some flexibility for discoverability.
- **ML feature-engineering layer**: modeled around point-in-time correctness between training and serving. The main failure mode here is leakage of information from the future into a training row, which is a different problem from a dimensional join getting the grain wrong, even though both are "modeling mistakes."

Use this lifecycle axis to ask "where does this decision live and who consumes it," and the conceptual/logical/physical axis to ask "how committed is this decision to implementation detail." A single physical warehouse table can still be described at a conceptual, logical, or physical level of detail; the two axes describe different things and are meant to be used together, not in place of each other.

## Normalization and denormalization

Normalization separates facts that belong to different entities and reduces update anomalies in operational systems. First, second, and third normal form are useful ways to reason about repeating groups and dependencies; they are not a requirement to split every analytical model into the maximum number of tables.

Analytical marts often denormalize dimensions or precompute derived values to make common access patterns easier and more consistent. Denormalization adds duplicated state that needs a clear owner, refresh strategy, and reconciliation. Choose based on workload and semantics rather than treating either style as universally correct.

## Dimensional planning and Data Vault

A bus matrix lists business processes against shared dimensions. It helps teams agree which dimensions, such as date, customer, product, or location, should be conformed across facts before building many independent marts.

Dimensional modeling is effective for stable, decision-oriented analytics. Data Vault separates business keys and relationships into hubs and links, with satellites retaining descriptive history and source context. It can help integrate many changing sources and preserve auditability, but it introduces more structures and transformations. Choose it when source integration and historical traceability justify the complexity; it is not automatically a better reporting model. Some platforms use a historized integration layer and publish dimensional marts for consumption.

## Other modeling approaches

- **Inmon-style enterprise modeling** commonly integrates an enterprise-wide, normalized warehouse before publishing downstream marts. It emphasizes shared consistency but may require more upfront coordination and design.
- **Kimball-style dimensional modeling** builds around business processes, facts, and conformed dimensions, often delivering usable marts incrementally. A bus matrix helps keep those marts consistent.

Anchor Modeling and Activity Schema design are worth a closer look because each has specific vocabulary that is easy to misuse without seeing the named parts.

### Anchor Modeling vocabulary

Anchor Modeling is a historized relational approach that separates stable identities from changing attributes and relationships, using four named kinds of tables:

- **Anchors** hold only an identity — a surrogate key and nothing else, similar to a hub in Data Vault. An `Anchor_Customer` table has no descriptive columns at all, only the key and metadata about when the row was created.
- **Attributes** hold one time-versioned property per table, each keyed back to its anchor. A customer's email and a customer's segment live in two separate attribute tables, so one can carry history independently of the other instead of forcing every attribute to version together.
- **Ties** record relationships between anchors — the equivalent of a link table in Data Vault — and can themselves be time-versioned when the relationship changes over time (for example, which sales rep owns an account).
- **Knots** hold small, reusable, low-cardinality lookup values, such as a status code or a country, shared across multiple anchors so the same code list is not duplicated per entity.

**Example (illustrative).** A `Customer` anchor with `Email` and `Segment` attribute tables and a `Country` knot means a segment change writes a new row to the segment attribute table only; the email attribute table, the anchor, and the country knot are untouched.

**Failure mode.** Splitting every attribute into its own table makes schema changes additive — add a table rather than alter one — but a simple "show me this customer" query now joins across many tables. Most Anchor Modeling implementations generate wide reporting views on top specifically to hide this from downstream consumers; querying the anchor structure directly in a BI tool is a common adoption mistake.

### Activity Schema design philosophy

Activity Schema design (closely associated with the Narrator / "activity schema" approach popularized by Ahmed Elsamadisi) starts from a different assumption than dimensional modeling: instead of splitting an event into facts and dimensions that are joined back together at query time, every event the business cares about is appended as one row to a single wide table, usually called an **activity stream**. Each row already carries the actor, the activity, the timestamp, and whatever feature columns that activity needs, so most "how many customers did X" or "time between X and Y" questions can be answered by filtering and self-joining that one table rather than assembling a star schema.

Two design rules carry most of the benefit:

- **One canonical definition per activity.** "Placed an order" is defined once, in one place, and every team reads from that same definition instead of writing their own SQL for what counts as an order. This is what makes the resulting metrics shareable and comparable across a team — nobody quietly redefines the same activity with a slightly different filter.
- **No required joins for most analysis.** Because the grain is "one activity occurrence," a large share of funnel, retention, and time-between-events analysis only needs to read and self-join the activity stream, not navigate a bus matrix of conformed dimensions.

**Failure modes.** A current-state snapshot (for example, "customer's plan today") still has to be derived from the activity history when a consumer needs one — the activity stream does not remove the need for derived state described earlier in this page. A single wide table can also accumulate a very large number of sparse feature columns if every activity's attributes are kept on the same row; that cost is traded against the simplicity of not joining, and should be weighed deliberately rather than assumed away.

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

## Data engineering approaches: a consolidated checklist

Modeling decisions do not stand alone; they interact with ingestion, orchestration, and governance practices covered elsewhere in this roadmap. The checklist below collects those practices into one cross-check to run alongside the modeling-specific checklist above. Each item links to the page that covers it in depth rather than re-explaining it here.

- [ ] **Land raw before you model.** Prefer a lake / raw-zone-first landing so a modeling mistake can be recomputed from an unmodified copy of the source instead of being baked in permanently. See [Storage, Warehousing, and Table Formats](storage-warehousing-and-formats.html) and [Platform Architecture and Lifecycle](platform-architecture-and-lifecycle.html).
- [ ] **Make transformations idempotent.** Re-running a modeling pipeline should produce the same result, not duplicate or drift, especially after a retry or backfill. See [Pipeline Orchestration](orchestration.html).
- [ ] **Prefer stable business/natural keys for joins** where they are genuinely stable, rather than inventing a surrogate key before you know whether source identity is reliable. Introduce a surrogate key once history or cross-system identity actually requires one — see "Facts and dimensions" above.
- [ ] **Keep pipelines declarative where possible**, describing desired outputs and dependencies rather than imperative step-by-step control flow, so dependency and backfill logic stays in the orchestrator rather than scattered across scripts. See [Pipeline Orchestration](orchestration.html).
- [ ] **Centralize metadata in a catalog** so table identity, schema, ownership, and lineage are discoverable instead of tribal knowledge spread across teams. See [Metadata Catalogs, Discovery, and Lineage](metadata-catalogs-and-lineage.html).
- [ ] **Avoid in-place ALTER DDL on production tables.** Prefer additive, versioned schema changes, or a table format's own schema-evolution feature, over altering a live table's shape underneath running consumers. See [Storage, Warehousing, and Table Formats](storage-warehousing-and-formats.html).

## Practice

Model a subscription business with subscriptions, invoices, invoice lines, customers, and plans. State each table's grain, identify a metric that would be double-counted by a naive join, and choose which customer attributes need historical versions.