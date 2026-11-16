---
title: Data Quality Tooling and Observability
description: Profile data before trusting it, express checks in Great Expectations and Soda, monitor with observability platforms such as Monte Carlo, and reason about data consistency.
order: 21
tags: [data quality, profiling, great expectations, soda, observability, monte carlo, consistency]
---

# Data Quality Tooling and Observability

[Data Quality and Contracts](data-quality-contracts.html) explains *what* to check and where. This page covers *how* teams commonly implement those checks: profiling to discover what the data looks like, declarative test frameworks (Great Expectations, Soda, dbt tests), observability platforms that watch production metadata (Monte Carlo and similar), and the consistency guarantees that decide which version of data a reader sees.

Assumptions for the examples: an Iceberg or warehouse mart `analytics.fct_orders` at grain one row per order line, timestamps in UTC, a daily batch that should complete by 06:00 UTC, and a Text2SQL assistant that answers from that mart.

A useful split:

| Layer | Question it answers | Typical tools |
|---|---|---|
| Profiling | What does this data actually contain? | SQL, ydata-profiling, catalog profilers |
| Declared tests | Does it meet the rules we wrote down? | dbt tests, Great Expectations, Soda |
| Observability | Is anything unusual happening that nobody wrote a rule for? | Monte Carlo, Soda anomaly checks, open-source monitors |

## Data Profiling

Data profiling is the systematic examination of a dataset's structure, content, and relationships before relying on it. It turns assumptions ("`customer_id` is unique") into measured facts and is the evidence from which contracts and tests are written.

**How it works.** Profiling is commonly done in three passes:

1. **Structure discovery:** types, formats, lengths, and whether values match the declared type (for example dates stored as strings).
2. **Content discovery:** null rates, distinct counts, min/max, distributions, top values, and patterns such as email or phone formats; this is also where likely PII is spotted.
3. **Relationship discovery:** candidate keys, functional dependencies, and how well foreign keys match their parents.

**Example (illustrative profiling SQL, Trino/ANSI style):**

```sql
select
  count(*)                                          as row_count,
  count(distinct order_line_id)                     as distinct_line_ids,
  sum(case when customer_id is null then 1 else 0 end) * 1.0 / count(*) as customer_null_rate,
  min(order_ts)                                     as min_order_ts,
  max(order_ts)                                     as max_order_ts,
  approx_percentile(net_amount, 0.5)                as median_net_amount,
  sum(case when net_amount < 0 then 1 else 0 end)   as negative_amounts
from analytics.fct_orders
where order_date >= date '2026-10-01';
```

```sql
-- Relationship discovery: orphan rate against the customer dimension.
select count(*) as orphan_lines
from analytics.fct_orders f
left join analytics.dim_customer c on f.customer_id = c.customer_id
where c.customer_id is null;
```

**Failure modes.** Profiling only a recent sample and missing historical edge cases; publishing profiles with raw top values of sensitive columns; treating a one-time profile as permanent truth.

**Validation.** Every contract rule should trace to either a profile observation or a business decision. Re-profile after source system changes and compare with the previous profile.

**Lakehouse / Text2SQL fit.** Profile results (ranges, null rates, distinct values for low-cardinality columns) make excellent assistant context: they let the model know `status` has five valid values and that `net_amount` can be negative for returns. Exclude sensitive columns from any profile that reaches a prompt.

## Great Expectations (GX)

Great Expectations, now packaged as **GX Core** (open source, Python) with a commercial GX Cloud, expresses data tests as *Expectations*: named, parameterised assertions such as "values in this column are not null" or "values are between 0 and 10,000". Expectations are grouped into suites, run against batches of data, and produce validation results and human-readable documentation ("Data Docs").

**How it works.** You configure a data source (pandas, Spark, or SQL via SQLAlchemy), define a batch (a table, a partition, a query), attach an expectation suite, and run a validation, often through a checkpoint that also triggers actions such as storing results or notifying a channel. API details changed significantly between the 0.x line and 1.x, so pin versions and follow the documentation for the version you install.

**Example (illustrative, GX Core 1.x style):**

```python
import great_expectations as gx
import great_expectations.expectations as gxe

context = gx.get_context()
suite = context.suites.add(gx.ExpectationSuite(name="fct_orders_contract"))
suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="order_line_id"))
suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="order_line_id"))
suite.add_expectation(gxe.ExpectColumnValuesToBeInSet(
    column="status", value_set=["placed", "paid", "shipped", "delivered", "returned"]))
suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(
    column="net_amount", min_value=-10000, max_value=100000, mostly=0.999))
```

**Compared with Soda and dbt tests.** dbt tests live next to the models and are ideal for keys, relationships, and accepted values in SQL transformations. GX suits Python-centric pipelines, dataframes, and teams that want rich result documents. Soda offers a compact YAML language and is easy to run from CI and orchestrators. Many teams use dbt tests for model logic and one of GX or Soda at ingestion boundaries; avoid duplicating the same rule in three tools.

**Failure modes.** `mostly` thresholds set loosely so tests never fail; suites validated against the whole table every run, which becomes expensive; results stored but never alerting anyone; version upgrades silently changing behaviour.

**Validation.** Seed a known-bad batch (duplicate key, out-of-set status) and confirm the suite fails with the expected expectation names. Track run duration and cost.

**Lakehouse / Text2SQL fit.** Run GX on the batch before it is committed to the Iceberg table (write-audit-publish), so the assistant never sees an unvalidated snapshot.

## Soda

Soda is a data quality tool whose checks are written in **SodaCL**, a YAML-based language. Soda Core (open-source CLI and Python library) executes checks against warehouses, lakehouse engines, and dataframes; Soda Cloud adds anomaly detection, dashboards, incident workflows, and contract features.

**How it works.** A configuration file defines the data source connection; a checks file lists checks per dataset. `soda scan` translates checks into SQL, runs them, and returns pass, warn, or fail per check, with a non-zero exit code on failure so a CI job or orchestrator task can stop.

**Example (illustrative SodaCL checks file):**

```yaml
checks for fct_orders:
  - row_count > 0
  - duplicate_count(order_line_id) = 0
  - missing_count(customer_id) = 0
  - invalid_count(status) = 0:
      valid values: [placed, paid, shipped, delivered, returned]
  - freshness(order_ts) < 1d
  - failed rows:
      name: net amount must not exceed gross amount
      fail query: |
        select order_line_id from fct_orders where net_amount > gross_amount
  - row_count:
      warn: when < 50000
      fail: when < 10000
```

```bash
soda scan -d lakehouse -c configuration.yml checks/fct_orders.yml
```

**Anomaly detection and contracts.** Anomaly checks learn a metric's history (for example daily row count) and flag outliers; they need enough history and seasonal awareness to avoid noise. Soda's contract features let producers declare schema and checks that run in CI before a change is merged. Confirm which features are in the open-source package versus the commercial service for your version.

**Failure modes.** `freshness` computed on a column with a different timezone than expected; "failed rows" samples sending sensitive data to a SaaS dashboard; warn thresholds that nobody watches.

**Validation.** Run the scan on fixtures with each kind of failure and assert the exit code and failing check names in CI.

**Lakehouse / Text2SQL fit.** Store scan results with the snapshot ID they validated, so an assistant answer can be traced to a snapshot that passed its checks.

## Monte Carlo

Monte Carlo is a commercial **data observability** platform. Rather than relying only on rules that engineers write, it collects metadata and query logs from warehouses, lakehouse engines, orchestrators, and BI tools, learns normal patterns, and alerts on "data downtime": stale tables, unexpected volume changes, schema changes, distribution shifts, and broken lineage paths.

**How it works.** The platform connects with read access to metadata and query history (and, for some monitors, to data samples or aggregates). It builds a lineage graph from query logs, applies automated monitors for freshness, volume, and schema across many tables, and lets you add custom SQL rules for critical fields. Incidents group related alerts and show upstream causes and downstream impact.

**Example (illustrative monitor definition, monitors-as-code style):**

```yaml
monitors:
  - type: freshness
    table: analytics.fct_orders
    expect_update_by: "06:00 UTC daily"
    severity: high
  - type: field_health
    table: analytics.fct_orders
    fields: [net_amount, customer_id]
    metrics: [null_rate, mean, negative_rate]
  - type: custom_sql
    name: refunds_never_exceed_sales
    sql: "select count(*) from analytics.fct_orders where net_amount < -gross_amount"
    alert_when: "> 0"
notify: [sales-data-oncall]
```

**Failure modes.** Alert fatigue from monitoring thousands of low-value tables; over-trusting learned thresholds after a legitimate business change; granting broader data access than needed to the vendor; no owner routing, so incidents are seen by everyone and acted on by no one.

**Validation.** Track precision (share of alerts that were real problems) and time to detection for incidents. Review the access the platform holds against the principle of least privilege.

**Lakehouse / Text2SQL fit.** Observability catches the failures nobody predicted. Feed open incidents into the assistant's status so it can warn that "orders data is delayed today" instead of answering confidently from yesterday's partial load. Equivalent capabilities can be built with open-source monitors plus OpenLineage if a commercial platform is not available.

## Data Consistency

Data consistency has two related meanings, and both matter in data platforms:

1. **System consistency:** which version of data a reader sees when data is replicated or updated concurrently. Under *strong consistency* every read sees the latest committed write; under *eventual consistency* replicas converge over time, and a reader may briefly see stale data. The CAP theorem states that during a network partition a distributed system must choose between consistency and availability.
2. **Semantic consistency:** the same fact has the same value across tables, systems, and reports (for example revenue in the mart equals revenue in the finance ledger for the same period).

**How it works in a lakehouse.** Iceberg gives *snapshot isolation* per table: a commit swaps the metadata pointer atomically in the catalog, and readers see either the old or new snapshot, never a mix. Major object stores now provide strong read-after-write consistency for objects (Amazon S3 has done so since late 2020), which simplifies this. However, consistency across *multiple* tables is not automatic: a dashboard joining `fct_orders` (refreshed) to `dim_customer` (not yet refreshed) can show inconsistent results. CDC replicas and caches add lag.

**Example (illustrative cross-system reconciliation):**

```sql
-- Semantic consistency: mart vs ledger for a closed period, tolerance 0.01.
select
  m.period,
  m.revenue as mart_revenue,
  l.revenue as ledger_revenue,
  abs(m.revenue - l.revenue) as diff
from analytics.monthly_revenue m
join finance.ledger_monthly l using (period)
where m.period = '2026-10'
  and abs(m.revenue - l.revenue) > 0.01;
```

**Failure modes.** Readers querying a replica with unknown lag; dimension and fact tables published at different times; caches that serve values after a correction; reports built from different snapshots of the same table.

**Validation.** Publish related tables together (for example tag a consistent set of snapshot IDs, or use a branch-and-merge workflow), record replica lag, and run reconciliations for closed periods.

**Lakehouse / Text2SQL fit.** Have the assistant record the snapshot IDs or data timestamps it queried and show "data as of" in the answer, so two answers that differ can be explained.

## Practice

1. Profile `fct_orders` (or your Project 1 mart) with the three passes and write three contract rules justified by the profile.
2. Implement the same three rules once in dbt tests and once in either GX or Soda. Decide which one you keep and record why.
3. Create a bad batch with a duplicate key, an invalid status, and a stale timestamp. Confirm each tool reports each failure distinctly and returns a failing exit code.
4. Write a freshness and volume monitor with an owner route; simulate a late load and measure detection time.
5. Run the reconciliation query for a closed period and document the tolerance and who approves exceptions.

### Completion criteria

- Each check you keep traces to a profile observation or business rule, and no rule is duplicated across tools without reason.
- A failing check blocks publication of the affected snapshot, and the assistant cannot read the blocked snapshot.
- Alerts reach a named owner, and you can report how long detection took in your simulation.
- Answers from the assistant include a "data as of" timestamp or snapshot reference.
