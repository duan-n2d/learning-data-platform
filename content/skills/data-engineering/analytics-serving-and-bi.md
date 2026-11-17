---
title: Analytics Serving and BI
description: Serve governed metrics through dashboards, OLAP, APIs, and semantic interfaces.
order: 9
tags: [BI, OLAP, analytics API, serving]
---

# Analytics Serving and BI

Analytics serving is the interface between trusted data and the decisions people make. Choose an interface based on users, latency, exploration needs, consistency requirements, and operational ownership.

## Business Intelligence

Business Intelligence (BI) is the discipline of turning operational and analytical data into dashboards, reports, and ad hoc queries that support business decisions. Its lifecycle runs from data collection and transformation, through metric definition and visualization, to distribution of the result to the decision-makers who act on it.

A dashboard commonly follows a trust and adoption lifecycle: it works well in a demo on a small, controlled dataset, then breaks down once it reaches production scale — numbers disagree across teams, queries slow down under concurrent use, and stakeholders lose trust and route around it with spreadsheets. Avoiding that decline takes centrally governed metric definitions and monitored data freshness, not just a faster dashboard tool. See [Headless BI and universal semantic layers](headless-bi-and-semantic-layers.html) for how a shared semantic layer solves the definition half of that problem.

## From reporting to interactive analytics

Traditional reporting often presents scheduled, predefined measures. Modern BI supports filtering, drill-down, exploratory analysis, and sharing. OLAP systems organize and aggregate multidimensional data so users can compare measures across dimensions such as time, product, and region.

A cube is a conceptual model of measures and dimensions; it need not be a literal cube data structure. Pre-aggregated cubes can make repeated questions fast but increase storage and refresh complexity. Modern columnar engines may compute similar aggregations directly, so measure before materializing.

## Choose the serving surface

| Surface | Good fit | Design concerns |
|---|---|---|
| Curated warehouse mart | Reusable analysis and BI | Grain, access, freshness, and stable contracts |
| BI semantic model | Consistent measures and self-service exploration | Metric ownership, filter behavior, and versioning |
| Analytics API | Application-specific metrics and workflows | Authentication, pagination, latency, and compatibility |
| Federated query | Ad hoc access across systems | Source load, inconsistent semantics, latency, and failure isolation |
| Reverse ETL | Activate selected warehouse data in operational tools | Write ownership, freshness, idempotency, and reconciliation |

Federation can avoid copies for some use cases, but query engines still need to handle source availability, pushdown capability, permissions, and inconsistent schema or semantics. A federation layer does not automatically create a single source of truth.

### Analytics API as a unified architecture

"Analytics API" is often used for more than a single endpoint: it names a pattern that bundles five components behind one API surface so application teams get consistent metrics without touching each piece directly:

1. A **query engine or gateway** that accepts requests, typically over REST or GraphQL, and routes them to the right backend.
2. A **metrics or semantic layer** holding shared metric definitions so every caller gets the same answer for the same question.
3. A **data catalog** that makes it discoverable what metrics and datasets are available to query.
4. **Orchestration** that keeps the data behind the API fresh on a known schedule.
5. A **SQL connector or execution layer** underneath that actually runs the query against the warehouse or engine.

This repository already covers each piece on its own page — the semantic layer, the catalog, and orchestration each have dedicated treatment. The point of naming the combination here is recognition: when a vendor or a team describes "our Analytics API," check which of these five components it actually bundles and which it assumes you already have.

## Metric consistency

Keep metric definitions in a reviewed semantic layer or governed BI model. Define grain, time basis, filters, unit, currency, and additive behavior once. Confirm that dashboards, APIs, and Text2SQL use compatible definitions. If a surface cannot express a definition accurately, document the difference rather than silently approximating it.

## Build a useful BI workflow

1. Identify the decision, user, and action the report supports.
2. Agree on metric definitions and data freshness with domain owners.
3. Design for common questions first, then expose safe exploration.
4. Label periods, units, filters, and source freshness in the interface.
5. Measure usage and query cost; remove unused complexity.
6. Review metric changes and test key dashboards against known fixtures.

## Go deeper

- [Headless BI and universal semantic layers](headless-bi-and-semantic-layers.html): headless BI, universal semantic layers, and Looker.
- [BI tools, visualization, and self-service analytics](bi-tools-and-self-service.html): Tableau, Power BI, Apache Superset, Metabase, chart design, and data literacy.
- [Reverse ETL, operational analytics, and CDPs](reverse-etl-and-activation.html): Hightouch, Census, and customer data platforms.

## Practice

Take daily paid revenue by region. Define the metric and its date basis, then design one dashboard, one API response, and one ad hoc analysis path. State how each applies permissions, what freshness users see, and how you detect that the three surfaces disagree.