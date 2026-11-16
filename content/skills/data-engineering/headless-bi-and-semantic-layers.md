---
title: Headless BI and Universal Semantic Layers
description: Define metrics once, outside any single dashboard, and serve the same logic to BI tools, APIs, and AI assistants.
order: 40
tags: [headless BI, semantic layer, metric store, universal semantic layer, Looker, LookML, MetricFlow]
---

# Headless BI and Universal Semantic Layers

Most metric disagreements are not SQL bugs. They happen because "revenue" was defined three times: once in a Tableau calculated field, once in a Power BI measure, and once in a notebook. This lesson covers the architectural answer — move the definition out of the presentation tool into a shared, versioned layer — and the tool that made the idea mainstream.

Read [Semantic layer](../ai/semantic-layer.html) first for the core vocabulary (entities, dimensions, measures, grain). This page focuses on where that layer lives and who queries it.

## Headless BI

**What it is.** Headless BI separates the "head" (charts, dashboards, chat interfaces) from the "body" (metric definitions, join paths, access rules, caching). The body runs as a service. Any head — a BI tool, a spreadsheet, an internal app, an LLM-powered assistant — asks it for `paid_revenue by region for last month` instead of writing its own SQL.

**How it works.**

1. Engineers declare entities, dimensions, measures, and metrics in code (YAML, LookML, or a similar DSL) stored in Git.
2. The semantic service compiles a metric request into SQL for the underlying warehouse or lakehouse engine, choosing join paths and time grain from the declarations.
3. Consumers reach it through one or more interfaces: SQL over JDBC/ODBC or Arrow Flight SQL, REST or GraphQL APIs, or native connectors to specific BI tools.
4. Access rules (row filters, column masks) and caching or pre-aggregations are applied in the service, so every head inherits them.

The term **metric store** is often used for the same idea with emphasis on the catalog of metric definitions and their API, rather than on modeling the whole dataset. In practice "headless BI", "metric store", and "semantic layer" overlap heavily; ask what each product actually compiles, caches, and enforces.

**Concrete example (illustrative, dbt MetricFlow-style; check the spec for your version).**

```yaml
semantic_models:
  - name: orders
    model: ref('fct_orders')          # grain: one row per order
    defaults:
      agg_time_dimension: paid_at
    entities:
      - name: order_id
        type: primary
      - name: customer
        type: foreign
        expr: customer_id
    dimensions:
      - name: paid_at
        type: time
        type_params:
          time_granularity: day       # UTC business day
      - name: region
        type: categorical
    measures:
      - name: paid_revenue_usd
        agg: sum
        expr: case when payment_status = 'paid' then amount_usd else 0 end

metrics:
  - name: paid_revenue
    label: Paid revenue (USD)
    description: Sum of paid order amounts in USD, excluding refunds, by paid date (UTC).
    type: simple
    type_params:
      measure: paid_revenue_usd
```

A headless request for this metric looks the same no matter who sends it, for example `metrics=[paid_revenue], group_by=[region, metric_time__month], where=metric_time >= '2026-10-01'`. The service, not the caller, decides how to join and aggregate.

**Failure modes.**

- *Bypass*: analysts still connect BI tools straight to marts and rebuild measures locally, so the "single definition" is one of several.
- *Lowest common denominator*: a BI tool's connector cannot express a filter or time grain the layer supports, so the tool quietly approximates.
- *Latency surprise*: an extra network hop and SQL compilation add seconds to every dashboard tile unless caching is tuned.
- *Ambiguous joins*: two valid join paths between entities produce different totals (fan-out), and the layer picks one silently.
- *Ownership vacuum*: metrics are "shared", so nobody approves changes.

**Validation.**

- Run each core metric through every consumer (dashboard, API, assistant) for a fixed period and compare to a hand-computed fixture.
- Fail CI when a metric definition changes without a reviewer from the owning domain.
- Inspect the generated SQL for a sample of requests; check join keys and grain.
- Track the share of BI queries that go through the layer versus direct table access.

**Connection to the governed analytics assistant.** In [Project 2](../../projects/project-2-text2sql-chatbot.html), the safest design lets the assistant select metrics, dimensions, and filters, then asks the semantic layer to compile SQL. The model never invents a revenue formula; it only picks from reviewed definitions. Headless BI is what makes the assistant's answer match the dashboard.

## Universal Semantic Layer

**What it is.** A universal semantic layer is a headless semantic layer that aims to serve *every* consumer in the organization — multiple BI tools, spreadsheets, notebooks, applications, and AI agents — across one or more physical engines. "Universal" is a design goal, not a guarantee: it means the layer is independent of any single BI vendor.

**How it works.** It combines four capabilities:

| Capability | What it provides | Question to ask a product |
|---|---|---|
| Modeling | Entities, joins, measures, metrics, hierarchies in code | Can it express ratios, semi-additive measures, and time-to-date metrics correctly? |
| Query interfaces | SQL, REST/GraphQL, MDX or DAX-compatible endpoints, BI-specific connectors | Which of *our* BI tools can use it natively, and which lose features? |
| Performance | Caching, aggregate tables, query rewrite | How are aggregates refreshed and invalidated when data changes? |
| Governance | Row/column security, lineage, certification status | Does it pass user identity to the engine, or use one shared service account? |

Examples of products positioned in this space include the dbt Semantic Layer (MetricFlow), Cube, AtScale, and semantic features in lakehouse engines such as Dremio's virtual datasets. Capabilities change quickly; evaluate against your own consumer list.

**Concrete example (illustrative consumer matrix).** Before adopting one, write down every consumer and the interface it will use:

```text
consumer                interface            identity passed?  features lost
Tableau dashboards      JDBC/SQL connector   yes (OAuth)       custom period-over-period calc
Power BI reports        vendor connector     service account!  RLS must be re-implemented
Finance Excel models    ODBC                 yes               none
Analytics assistant     REST metric API      yes (end user)    none
Product app widget      GraphQL              app token         per-customer filter enforced in app
```

The "service account!" row is the risk to fix: if the layer cannot see the end user, row-level rules cannot apply there.

**Failure modes.** Promised universality without testing each connector; a single shared credential that erases per-user security; aggregate tables that serve stale numbers after a backfill; the layer becoming a bottleneck owned by one overloaded team.

**Validation.** Maintain a consistency suite: for each certified metric, the same request through each interface must return the same value (within a documented tolerance for currency rounding). Re-run it after every semantic-model release and after upstream backfills.

**Connection to the governed analytics assistant.** Treat the assistant as just another consumer in the matrix, with the strictest requirements: per-user identity, full provenance (metric name, version, generated SQL), and refusal when a question needs a metric that is not defined.

## Looker

**What it is.** Looker is a BI platform, part of Google Cloud since 2020, built around **LookML**, a code-based modeling language. Analysts write views (tables and their fields), explores (joinable starting points for questions), and models (collections of explores and connections). Looker generates SQL at query time and runs it in the customer's database; it does not require extracting data into its own engine. It was an early, widely adopted example of "define once in code, reuse everywhere" — the pattern headless BI generalizes. (Looker Studio, formerly Data Studio, is a separate, lighter product.)

**How it works.** LookML files live in a Git repository connected to the Looker instance. Developers work in a development mode on a branch, validate the model, and deploy to production. Users explore through a field picker; Looker composes the SQL from the declared joins. Persistent derived tables (PDTs) can materialize expensive intermediate results. Google has also exposed the Looker semantic model to other tools (for example through connectors and SQL interfaces), which moves Looker partway toward a headless role — check current availability for your edition.

**Concrete example (illustrative LookML).**

```text
view: fct_orders {
  sql_table_name: analytics.fct_orders ;;

  dimension: order_id {
    primary_key: yes
    type: string
    sql: ${TABLE}.order_id ;;
  }
  dimension_group: paid {
    type: time
    timeframes: [date, week, month]
    sql: ${TABLE}.paid_at ;;          # stored in UTC
  }
  dimension: region {
    type: string
    sql: ${TABLE}.region ;;
  }
  measure: paid_revenue {
    type: sum
    sql: ${TABLE}.amount_usd ;;
    filters: [payment_status: "paid"]
    value_format_name: usd
    description: "Paid order amount in USD, excluding refunds."
  }
}

explore: fct_orders {
  access_filter: {
    field: fct_orders.region
    user_attribute: allowed_region
  }
}
```

**Failure modes.** Joins declared with the wrong `relationship` causing fan-out (Looker's symmetric aggregates mitigate many but not all cases); sprawling explores that expose hundreds of confusing fields; PDTs that silently fail to rebuild; production edits made without code review; duplicating metric logic again in other BI tools because they cannot read LookML.

**Validation.** Run the LookML validator and content validator in CI before deploy; write LookML data tests that assert known values for fixed periods; review the SQL tab for new explores; monitor PDT build logs.

**Connection to the governed analytics assistant.** If your organization already maintains LookML, it is a ready-made, reviewed list of measures, dimensions, and allowed joins. An assistant can use that metadata as its catalog — but only if user attributes and access filters are applied to the assistant's queries exactly as in Looker.

## Choosing where definitions live

| Situation | Reasonable default |
|---|---|
| One BI tool, small team | Model in that tool's semantic model; document the limits |
| Several BI tools or an AI assistant | A headless or universal semantic layer in Git |
| Already standardized on Looker | Keep LookML as the source; test what other consumers can read from it |
| Metrics needed in operational apps | Semantic layer API plus reverse ETL (see [Reverse ETL and activation](reverse-etl-and-activation.html)) |

## Practice

1. Write `paid_revenue`, `active_customers` (distinct customers with a paid order in the period), and `average_order_value` (a ratio, not an average of averages) in a MetricFlow-style YAML file.
2. Build a consumer matrix for three consumers you could realistically run locally (for example Metabase, a Python API client, and your assistant).
3. Write a consistency test that requests `paid_revenue by region` for October 2026 through two consumers and compares the results with a fixture.
4. Break it on purpose: add a join from orders to order items and observe whether revenue fans out.

**Completion criteria.**

- Three reviewed metric definitions with grain, time basis, unit, and owner.
- A consumer matrix that marks identity propagation and lost features for each consumer.
- A consistency test that passes on correct data and fails on the fan-out change.
- A short note explaining how the assistant selects metrics instead of writing formulas.
