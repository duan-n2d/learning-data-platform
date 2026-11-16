---
title: Managed and Open Ingestion Tools
description: Compare Airbyte, Fivetran, and dlt for loading SaaS and database data into warehouses and Iceberg, and verify what each tool actually guarantees.
order: 33
tags: [ingestion, Airbyte, Fivetran, dlt, ELT, connectors, Iceberg, Python]
---

# Managed and Open Ingestion Tools

Most teams should not hand-write a connector for every SaaS API and database. Connector tools handle authentication, pagination, incremental state, schema mapping, and retries. They do not remove the need to define keys, deletes, freshness, and reconciliation; they move those decisions into configuration.

Assumptions: sources are a CRM API and a PostgreSQL database; destinations are a warehouse or Iceberg tables in object storage. Feature names, destinations, and pricing models change frequently. Configurations below are **illustrative**: verify against current documentation and test with your own data before committing.

## Airbyte

**What it is.** Airbyte is an open-source data integration platform with a large catalog of source and destination connectors. It can be self-hosted or used as a managed cloud service.

**How it works.**

- A **connection** links a source to a destination with a schedule and a set of selected streams (tables or API resources).
- Each stream uses a **sync mode**: full refresh (overwrite or append) or incremental (append, or append + deduped using a primary key and a cursor field).
- Connectors run as containers that follow a common protocol, so connectors are isolated and replaceable. New API connectors can be built with a low-code connector builder or a Python CDK.
- Airbyte adds metadata columns such as a raw record ID, extraction timestamp, and per-record metadata about errors or truncations, which help with deduplication and audits.
- For the lakehouse, Airbyte provides destinations that write Apache Iceberg tables to object storage with a catalog (check which catalogs and whether dedup/upsert is supported for the destination you choose).

**Example configuration choices (illustrative).**

| Stream | Sync mode | Cursor | Primary key | Why |
|---|---|---|---|---|
| `crm.contacts` | Incremental, append + deduped | `updated_at` | `id` | Current state, keeps up with edits |
| `crm.email_events` | Incremental, append | `occurred_at` | `event_id` | Immutable events |
| `crm.pipelines` | Full refresh, overwrite | none | `id` | Tiny reference table, deletions visible |

**Failure modes.** Cursor-based incremental syncs miss hard deletes unless the source exposes them; records updated without changing `updated_at` are missed; a connector version upgrade can change schema mapping; a self-hosted deployment is your responsibility to patch, scale, and monitor.

## Fivetran

**What it is.** Fivetran is a managed ELT service: it operates connectors for SaaS applications, databases, files, and events, and loads data into warehouses and data lakes with little configuration.

**How it works.**

- You authorize a source and pick a destination; Fivetran handles extraction, incremental sync (often log-based CDC for databases), schema creation, and schema changes according to a policy you set (allow all, allow columns, or block new schemas).
- It adds system columns such as a sync timestamp and a soft-delete flag (`_fivetran_synced`, `_fivetran_deleted`) and offers optional history modes that keep prior versions of rows.
- Its managed data lake option writes Iceberg (and Delta) tables to your object storage and registers them in a catalog, so multiple engines can query them.
- Pricing has generally been based on monthly active rows (rows inserted, updated, or deleted per month), so a noisy source can be expensive.

**Failure modes.** Soft deletes (`_fivetran_deleted = true`) are not filtered for you; models must exclude them. Re-syncs of large tables can be costly and slow. Behavior depends on vendor connector logic you cannot inspect or patch, so confirm deletes, history, and schema handling per connector.

## Airbyte vs Fivetran

| Concern | Airbyte | Fivetran |
|---|---|---|
| Deployment | Open source self-hosted, or managed cloud | Managed service (with hybrid options) |
| Custom connectors | Connector builder, CDK, can fork connectors | Limited; request or use function connectors |
| Operations | You run it (self-hosted) | Vendor runs it |
| Cost driver | Infrastructure + engineering time, or cloud credits | Usage-based (active rows) |
| Inspectability | Connector code is visible | Behavior documented, code closed |
| Iceberg output | Iceberg-capable destinations | Managed data lake service |

Choose on the sources you need (connector quality varies per connector, not per vendor), your team's capacity to operate infrastructure, cost at your data volume, and data residency requirements.

## dlt

**What it is.** dlt (data load tool) is an open-source Python library for loading data from APIs, databases, and files into warehouses, DuckDB, and lakes. You write normal Python generators; dlt handles schema inference, normalization of nested JSON into tables, incremental state, and loading.

**How it works.**

- A **resource** is a Python function that yields records. Decorator options set the table name, primary key, and **write disposition**: `append`, `replace`, or `merge` (upsert by key).
- `dlt.sources.incremental` tracks a cursor (for example `updated_at`) and stores its last value in pipeline state, which dlt persists in the destination alongside load metadata tables.
- **Schema contracts** decide what happens when new tables, columns, or types appear (`evolve`, `freeze`, `discard_row`, `discard_value`).
- The `filesystem` destination can write Iceberg or Delta tables to object storage; DuckDB and MotherDuck, Postgres, Snowflake, BigQuery, and others are also supported.

**Inspectable example (illustrative).**

```python
import dlt
from dlt.sources.helpers import requests  # requests wrapper with retries on transient errors


@dlt.resource(name="orders", primary_key="id", write_disposition="merge")
def orders(
    updated_at=dlt.sources.incremental("updated_at", initial_value="2026-01-01T00:00:00Z"),
):
    url = "https://api.example.com/v1/orders"
    params = {"updated_since": updated_at.last_value, "limit": 100}
    while url:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        yield body["data"]
        url = body.get("next")  # cursor pagination: the next URL already carries the cursor
        params = None


pipeline = dlt.pipeline(
    pipeline_name="shop_api",
    destination="duckdb",          # or "filesystem" with table_format="iceberg"
    dataset_name="raw_shop",
)
load_info = pipeline.run(orders(), schema_contract={"columns": "freeze"})
print(load_info)
```

Inspect the results: query `raw_shop.orders`, and the `_dlt_loads` table for load IDs and status. Run the script twice and confirm row counts do not change when the API returns the same records (merge by `id`).

**Failure modes.** Automatic schema inference can create unexpected tables from nested arrays or new columns from typos; use contracts for production. An incremental cursor with equal timestamps at a page boundary can skip records, so prefer `>=` with deduplication. Running two copies of the same pipeline concurrently can conflict over state.

## dlt vs Airbyte vs Fivetran

dlt is a library you embed in code you already orchestrate and test; Airbyte is a platform with a UI, scheduler, and connector catalog; Fivetran is a managed service. A common pattern is to use a managed tool for standard SaaS sources and dlt for internal or niche APIs, with all three landing source-shaped data that downstream models then clean.

## Validation for any connector tool

- **Counts and sums:** compare row counts and key totals for a closed period with the source's own report or API.
- **Deletes:** delete a test record in the source and confirm how (or whether) the destination reflects it.
- **Schema change:** add a field in a test environment and confirm the tool's policy does what you expect.
- **Freshness:** alert on the age of the newest record per table, not only on sync success, because a "successful" sync can load zero rows.
- **Recovery:** document how to re-sync a single table or date range and what that costs.

## Practice

1. Write the dlt pipeline above against a public paginated API (or a local mock). Load into DuckDB, run it twice, and prove idempotency with a count and a duplicate-key query.
2. Switch the destination to `filesystem` with Iceberg table format on a local folder or MinIO. Inspect the produced metadata and data files.
3. Freeze the schema contract, then add a field in the mock API response. Record the error and decide whether to evolve or reject.
4. Configure the same source in Airbyte (open source, locally) using incremental append + deduped. Compare the produced columns and metadata with dlt's.
5. Write a decision record choosing between Airbyte, Fivetran, and dlt for three sources: a CRM SaaS, an internal REST API, and a PostgreSQL database. Include cost drivers, deletes, schema change, and exit strategy.

## Completion criteria

- Your dlt pipeline is idempotent, incremental, and has a schema contract, verified by running it repeatedly.
- You have tested delete handling and schema change in at least one tool and documented the outcome.
- Freshness and reconciliation checks run independently of the tool's own "success" status.
- Your decision record ties each source to a tool with explicit trade-offs.
