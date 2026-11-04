---
title: Data Engineering Foundations Field Guide
description: A practical foundation in the data lifecycle, architecture, modeling, meaning, and the engineering role.
order: 1
tags: [data engineering, foundations, lifecycle, modeling]
---

# Data Engineering Foundations Field Guide

This guide connects the core ideas behind a data platform. It is an original learning note for this curriculum, not a copy of the external reading map. Use the linked lessons for hands-on detail and this guide to understand how the concepts fit together.

## 1. What data engineering does

Data engineering builds and operates systems that make data available, understandable, reliable, and appropriately governed for users and applications. The work includes acquiring data, preserving its history, transforming it into useful forms, serving it through suitable interfaces, and operating the whole path as requirements change.

A successful pipeline is not defined only by whether a task returns exit code zero. Its consumers need to know what each value means, how fresh it is, what quality checks it passed, who owns it, and how the system behaves when a source is late or changes shape.

## 2. The data lifecycle

A useful lifecycle is a feedback loop:

1. **Discover:** identify the user, decision, source, constraints, and expected outcome.
2. **Design:** set the grain, contract, architecture, access policy, freshness target, and failure behavior.
3. **Ingest:** copy snapshots or changes with identifiers, event time, and replay checkpoints.
4. **Transform:** standardize representations and encode reviewed business logic.
5. **Serve:** publish data through a mart, metric model, API, report, or application.
6. **Operate:** observe quality, freshness, latency, cost, and access; respond to incidents.
7. **Evolve or retire:** migrate users safely, communicate changes, and remove obsolete data under retention policy.

The lifecycle is iterative. A production incident may reveal a missing contract; a new consumer may require a different serving model. Record these feedback signals and use them to change the design rather than adding ad hoc fixes indefinitely.

## 3. Architecture: follow the data, not the logos

For one business fact, draw the path from its source to a decision. A paid order might be recorded in an operational database, captured by a daily batch or CDC connector, landed in durable raw storage, transformed into order-line and daily-revenue models, and served to BI or an application.

At each boundary, identify:

- The system of record and who owns the meaning.
- The identifier, event timestamp, ingestion timestamp, and schema version.
- Whether data is copied, transformed, filtered, or joined.
- The trust and access boundary, including external services.
- The expected freshness, retry behavior, and recovery path.
- The consumer and the contract it relies on.

The resulting diagram should explain where failure is detected and who responds. Choosing popular products without defining these boundaries is not an architecture.

## 4. Model at several levels

A **conceptual model** names business concepts and relationships. A **logical model** defines entities, attributes, identifiers, and cardinalities without committing to a database. A **physical model** maps these choices to tables, columns, data types, keys, partitions, and engine-specific constraints.

An ERD is a communication tool for the logical structure. It should show whether a relationship is one-to-one, one-to-many, optional, or many-to-many. Validate that the diagram agrees with observed data and business rules; a neat diagram cannot make an incorrect source assumption true.

### Normalization

Normalization separates facts according to their dependencies. In an operational system, this reduces anomalies such as updating a customer's address in several rows or deleting the only record of a product when an order is removed. First, second, and third normal form are useful reasoning tools for repeating groups and dependencies. They are not a goal to maximize in every analytical schema.

### Dimensional modeling

Dimensional models organize measurements around business processes. A fact table has a declared grain and measures; dimensions provide descriptive context. Conformed dimensions let separate processes use consistent definitions for shared concepts such as customer, date, or product. A bus matrix maps business processes to shared dimensions and helps plan a consistent set of marts.

### Inmon and Kimball as design traditions

Inmon-style approaches commonly begin with an integrated, normalized enterprise warehouse and derive marts for consumption. This emphasizes shared integration but can require more upfront coordination. Kimball-style approaches build around business processes, facts, and conformed dimensions, often delivering usable marts incrementally. They emphasize clarity for analytical questions but require discipline to keep dimensions conformed.

These are useful design traditions, not mutually exclusive rules. A platform can use a normalized integration layer and publish dimensional marts. Choose based on source complexity, history requirements, delivery constraints, and consumer needs.

### Entity-centric and other models

Entity-centric modeling organizes information around durable business entities and their relationships rather than starting from reports. It can help when many use cases need a consistent customer, product, or account view. Its success depends on clear identity resolution and relationship ownership.

Data Vault, Anchor Modeling, activity schemas, and relational models address different change and history problems. Data Vault separates business keys and relationships from historized descriptive context. Anchor Modeling separates stable identities from changing attributes. Activity schemas represent events with time, actor, and related entities. Each adds structures or interpretation requirements; use it when the integration or history problem justifies that cost, not as a badge of sophistication.

## 5. Treat data assets as supported interfaces

A data asset is a maintained output that someone depends on: a table, stream, metric model, API, or curated document collection. A useful asset has a purpose, owner, schema, grain, quality expectations, freshness target, access rules, lineage, and change policy.

A data product is an asset treated as a supported interface for identified consumers. It needs a support path and lifecycle plan, not just a product name. If no consumer, owner, or expectation exists, first determine whether the asset should be maintained at all.

## 6. Meaning, semantics, and lineage

A semantic layer represents business entities, dimensions, metrics, and valid relationships in a reusable form. A metric definition should include its grain, expression, filters, time basis, unit, currency behavior, owner, and examples. A glossary term without executable logic can drift from the actual query; a query without a business definition can be technically correct and still answer the wrong question.

Lineage records how data moves from sources through transformations to consumers. Technical lineage helps identify affected models after a schema change; business lineage explains why the transformation exists and which decision it supports. Use both where possible. Lineage also supports incident diagnosis, audit, and safe deprecation.

## 7. The role of a data engineer

Data engineers combine software development, data modeling, distributed-systems reasoning, security, and operations. They translate between domain users and technical systems, make implicit assumptions explicit, and help consumers use data without guessing how it was produced.

The role overlaps with software engineering in testing, code review, modular design, CI/CD, reliability, and incident response. It differs in the extra attention paid to data meaning, grain, temporal behavior, quality, lineage, and analytical workload. Neither role is only tool administration. Strong practice includes understanding the users, documenting decisions, responding to incidents, and improving the system from evidence.

## Practical review checklist

- Can a new team member trace one value from source to consumer?
- Is each table's grain stated before measures and joins are selected?
- Are ownership, freshness, quality, access, and retention explicit?
- Does the chosen modeling style fit the change and history requirements?
- Can a consumer find a definition, lineage path, and support owner?
- Is there a tested way to replay, correct, or retire the asset?

## Practice

Choose one metric, such as paid revenue by month. Draw the source-to-consumer path, create a conceptual ERD, state the fact grain, identify its shared dimensions, write the metric contract, and mark technical and business lineage. Add one late correction and describe how it changes the published result and how consumers are notified.

## Continue learning

- [Platform architecture and lifecycle](../data-engineering/platform-architecture-and-lifecycle.html)
- [Analytics data modeling](../data-engineering/data-modeling.html)
- [Governance and data products](../data-engineering/governance-and-data-products.html)
- [Semantic layer](../ai/semantic-layer.html)
- [Project 1: Core Analytics Warehouse](../../projects/project-1-analytics-warehouse.html)