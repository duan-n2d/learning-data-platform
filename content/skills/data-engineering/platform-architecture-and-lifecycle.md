---
title: Data Platform Architecture and Lifecycle
description: Trace data from operational sources to governed, decision-ready products.
order: 5
tags: [architecture, data lifecycle, modern data stack]
---

# Data Platform Architecture and Lifecycle

A data platform is a set of contracts and responsibilities across systems, not a single warehouse or orchestration tool. Architecture starts with the decisions and users the platform must serve, then works backward to the sources, transformations, and controls required to serve them reliably.

## Follow one datum end to end

Use one business event, such as a paid order, to map the lifecycle:

1. **Operational capture:** an application records the order in an OLTP system optimized for transactions.
2. **Extraction and transport:** a batch connector or change-data-capture (CDC) stream moves source changes while preserving source identity and event time.
3. **Durable landing:** immutable or versioned raw data allows replay and audit.
4. **Transformation:** staging standardizes names and types; intermediate models encode reusable logic; marts serve defined analytical questions.
5. **Governance and quality:** contracts, tests, lineage, ownership, access policies, and freshness checks make behavior visible.
6. **Serving:** BI, analytics APIs, semantic models, and approved applications expose the data to users.
7. **Feedback and operations:** incidents, usage, cost, and data-quality signals inform the next change.

At every boundary, ask what identifier, timestamp, schema version, and ownership information must travel with the data.

## Common platform layers

| Layer | Responsibility | Questions to answer |
|---|---|---|
| Sources | Record operational events and reference entities | Which system owns each fact? What is its update behavior? |
| Ingestion | Move snapshots or changes reliably | Is delivery batch, CDC, or stream? How are duplicates handled? |
| Storage | Retain raw and curated data durably | What is the format, partitioning, retention, and recovery policy? |
| Compute | Transform, query, and validate data | Which workload needs which engine and resource boundary? |
| Orchestration | Schedule and observe dependencies | How are retries, backfills, and partial failures handled? |
| Governance | Define meaning, quality, access, and lineage | Who owns the data and approves changes? |
| Serving | Make trusted data usable | Which interface, latency, and freshness do users need? |

A modern data stack may combine managed services, open-source tools, and existing enterprise systems. Select tools by workload, operating capacity, portability, security, and total cost; do not adopt a stack merely because its components are popular.

## Architecture patterns

- **Medallion layers** commonly describe progressively refined data such as bronze/raw, silver/validated, and gold/serving. Treat these as quality and responsibility boundaries, not mandatory schemas or a substitute for clear contracts. Define what each layer guarantees and who may publish into it.
- **Data mesh** organizes ownership around business domains and treats data products as supported interfaces. It can improve domain context and reduce a central team's bottleneck, but it does not remove the need for shared identity, interoperability, discoverability, and platform controls. Adopt it when domain ownership and operating maturity justify coordination across teams.
- **Open data stack** is a broad approach that favors interoperable formats, interfaces, and replaceable components. Openness can improve portability, but compatibility, support, security, and total cost still need to be evaluated for the concrete versions in use.
- **Declarative data stack** describes desired data assets, dependencies, and checks so tools can plan execution from the declared state. It contrasts with code that manually dictates every operational step. Declarative systems still require developers to understand generated plans, side effects, and recovery behavior.

## A short history of distributed processing

MapReduce and Hadoop made large-scale distributed batch processing accessible by splitting work across machines and coordinating map, shuffle, and reduce stages. Modern cloud warehouses and engines automate many of these details and add interactive or streaming execution. The durable lesson is to reason about data movement, partitioning, skew, and failure recovery; learning a legacy framework is optional unless a target platform requires it.

## Architecture tradeoffs

- **Batch vs streaming:** batch is often simpler and cheaper when hourly or daily freshness is sufficient. Streaming adds operational complexity and is justified by latency or event-driven needs.
- **ETL vs ELT:** transforming before loading can minimize what enters an analytical store; ELT retains source-shaped data and uses warehouse compute for transformations. Privacy, scale, replay, and cost affect the choice.
- **Centralized vs domain-oriented ownership:** central standards improve consistency; domain teams can improve context and responsiveness. Federated models need clear interfaces and decision rights.
- **Managed vs self-operated services:** managed offerings reduce infrastructure work but can introduce cost, portability, or product-boundary tradeoffs.

## Draw the system before selecting tools

For each flow, document source of truth, direction of movement, trust boundary, storage location, transformation owner, freshness target, recovery path, and consumer. Mark sensitive data and external service boundaries. A useful architecture diagram explains failure and ownership, not only product logos.

## Practice

Draw a platform for online orders and product catalog data. Show the transactional source, one batch or CDC path, raw retention, curated warehouse models, BI access, and a Text2SQL application. Label which identity can read or write each layer, how an order correction reaches the mart, and what happens if a load is delayed.