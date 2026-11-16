---
title: Metadata Catalogs, Discovery, and Lineage
description: Separate table catalogs from discovery catalogs, compare Alation, Collibra, DataHub, and Amundsen, and capture lineage and provenance with OpenLineage and Marquez.
order: 20
tags: [governance, catalog, metadata, lineage, provenance, openlineage, datahub, discovery]
---

# Metadata Catalogs, Discovery, and Lineage

Two different systems are both called a "catalog". A **table catalog** (Iceberg REST catalog, Apache Polaris, Unity Catalog, AWS Glue, Hive Metastore) tells a query engine where a table's current metadata lives so that reads and commits are correct. A **discovery or governance catalog** (Alation, Collibra, DataHub, Amundsen, OpenMetadata) helps people and tools find datasets, understand their meaning, see who owns them, and judge whether to trust them. A lakehouse usually needs the first and benefits from the second; confusing them leads to wrong expectations about what each one enforces.

This page builds on [Data Governance and Data Products](governance-and-data-products.html). Assumptions used in the examples: an Iceberg lakehouse with a REST catalog, Spark and Trino as engines, an orchestrator such as Airflow or Dagster, and a Text2SQL assistant that reads curated marts.

## Metadata Catalog

A metadata catalog is a registry of data assets and facts about them. In the narrow, engine-facing sense it maps a table identifier such as `sales.orders` to the location of its current metadata file and performs atomic commits: when a writer adds a snapshot, the catalog swaps the pointer only if nobody else committed first. In the broad, human-facing sense it stores descriptions, owners, tags, classifications, quality status, and usage.

**How it works.** Iceberg engines call the catalog to load a table, receive the current `metadata.json` location (or the metadata itself via the REST protocol), and then read manifests directly from object storage. Discovery catalogs instead *harvest* metadata: they connect to the table catalog, warehouse, BI tool, and orchestrator on a schedule or through events and build a searchable graph.

**Example (illustrative REST catalog response, trimmed):**

```json
{
  "metadata-location": "s3://lake/warehouse/sales/orders/metadata/00042-6c1e.metadata.json",
  "metadata": {
    "format-version": 2,
    "table-uuid": "6c1e0d2a-...",
    "current-snapshot-id": 8812345501,
    "properties": {"owner": "sales-data-team", "classification": "internal"}
  }
}
```

**Failure modes.** Two table catalogs pointing at the same files (split-brain commits); discovery metadata that is weeks behind the table catalog; descriptions copied once and never maintained; table properties used as the only place a classification lives, so BI tools never see it.

**Validation.** For a sample of tables, compare the schema and snapshot reported by the discovery catalog with the table catalog. Track harvest lag. Check that every published mart has an owner and description, and fail a CI check when a new mart lacks them.

**Lakehouse / Text2SQL fit.** The table catalog is the source of truth for what exists; the discovery catalog supplies descriptions, owners, and certification flags that a Text2SQL assistant can use to choose only approved tables. Never let the assistant infer allowed tables from whatever the engine can list.

## Data Discovery

Data discovery is the process by which a person (or an agent) finds a candidate dataset, understands what it represents, and decides whether it is fit for a purpose. Search is only the first step; trust signals do most of the work.

**How it works.** A useful discovery experience combines keyword and semantic search over names and descriptions, a preview of schema and sample statistics (from [data profiling](data-quality-tooling-and-observability.html#data-profiling)), ownership, freshness, quality status, popularity from query logs, lineage, and certification. Users should be able to see why a result ranks highly.

**Example (illustrative discovery record for one table):**

```yaml
dataset: analytics.fct_orders
grain: one row per order line
owner: sales-data-team
steward: jane.doe
classification: internal
certified: true
freshness: complete through previous UTC day, landed by 06:00 UTC
quality: 14/14 checks passing (last run 2026-11-16T06:05Z)
popular_with: [finance-bi, text2sql-assistant]
known_limitations: "Returns before 2024-01-01 are not linked to original orders."
```

**Failure modes.** Search returns five tables called `orders` with no hint of which is authoritative; popularity rewards a deprecated table that many old dashboards still query; previews leak sensitive sample values to users who cannot query the table.

**Validation.** Run task-based tests: give three users a question ("where is net revenue by region?") and measure whether they find the certified asset. Confirm that previews respect the same access policy as queries.

**Lakehouse / Text2SQL fit.** Discovery metadata is ideal retrieval context for an assistant: a short list of certified assets with grain and limitations is far safer than the full schema dump.

## Alation

Alation is a commercial enterprise data catalog focused on discovery, curation, and governance workflows. It is well known for analysing query logs to surface which tables and columns are actually used, by whom, and in which joins, and for letting stewards curate articles, glossary terms, and trust flags on assets.

**How it works.** Connectors crawl databases, warehouses, lakehouse engines, and BI tools; query-log ingestion feeds usage and popularity; stewards attach business terms, endorsements, and deprecation warnings; policies and workflows route approvals. Alation is not an Iceberg table catalog: it reads from Glue, Unity Catalog, Polaris-backed engines, and similar sources but does not coordinate table commits.

**Example (illustrative curation workflow).** A steward marks `analytics.fct_orders` as *Endorsed*, links it to the glossary term "Net revenue", and adds a warning on `staging.orders_raw`: "Do not use for reporting; contains cancelled lines." An analyst searching "revenue" now sees the endorsed table first with the warning visible on the raw one.

**Failure modes.** Treating the tool purchase as the governance programme; stewardship queues that grow without owners; usage-based ranking that promotes heavily used but incorrect tables; connectors missing the lakehouse engine so the catalog shows only the old warehouse.

**Validation.** Measure coverage (share of production marts with owner, description, and term link), curation latency (time from new table to curated), and accuracy of a sample of descriptions reviewed by domain experts.

**Lakehouse / Text2SQL fit.** Use Alation (or any similar catalog) as the human-curated layer of meaning above the table catalog. Export endorsements and deprecation flags into the semantic model or assistant allow-list instead of having the assistant query the catalog UI.

## Collibra

Collibra is a commercial data intelligence and governance platform. Its strengths are business glossary management, an operating model of domains, communities, and responsibilities, configurable stewardship workflows, policy management, and lineage. It is often chosen where governance processes, approvals, and regulatory evidence matter as much as discovery.

**How it works.** Assets (tables, columns, reports, business terms, policies) live in domains with assigned roles such as owner and steward. Workflows move a term or policy through draft, review, and approval. Integrations harvest technical metadata and lineage from sources, and some editions can push protection policies to supported platforms.

**Example (illustrative glossary term with workflow state):**

```yaml
term: Active Customer
domain: Customer
definition: "A customer with at least one non-cancelled order in the trailing 90 days."
owner: head-of-customer-analytics
steward: customer-data-steward
status: Approved            # Draft -> Under Review -> Approved
related_columns: [analytics.dim_customer.is_active]
related_policies: [Customer PII Handling v3]
```

**Compared with DataHub and Polaris.** Polaris is an Iceberg table catalog that enforces table-level privileges for engines; Collibra does not replace it. DataHub is an open-source metadata platform with strong technical lineage and APIs; Collibra puts more emphasis on business governance workflows. Many organisations run a table catalog plus one discovery or governance catalog, not all three.

**Failure modes.** Glossary terms approved in Collibra but implemented differently in dbt or the semantic layer; workflows so heavy that teams bypass them; policy records that are never connected to an enforcement point.

**Validation.** Reconcile approved term definitions against metric definitions in code at least each release; sample policies and confirm each names the system that enforces it.

**Lakehouse / Text2SQL fit.** Glossary terms become synonyms and definitions in the semantic layer; an assistant should cite the approved term definition when answering "how many active customers".

## DataHub

DataHub is an open-source metadata platform (originally from LinkedIn, now developed by an open-source community alongside a company that sells a managed version) for discovery, lineage, ownership, and governance. It models metadata as entities (datasets, dashboards, pipelines, users) with versioned aspects (schema, ownership, tags, glossary terms), and exposes them through GraphQL and REST APIs.

**How it works.** Ingestion "recipes" pull metadata from sources such as Iceberg catalogs, Trino, Snowflake, dbt, Airflow, and Looker; push-based emitters and OpenLineage integration add runtime lineage. Changes flow as metadata change events, which other systems can subscribe to, which is what makes DataHub useful for [active metadata](#active-metadata).

**Example (illustrative ingestion recipe):**

```yaml
source:
  type: iceberg
  config:
    catalog:
      lake:
        type: rest
        uri: https://catalog.internal/api/catalog
    platform_instance: prod_lake
sink:
  type: datahub-rest
  config:
    server: https://datahub.internal:8080
```

**Compared with OpenMetadata and Collibra.** OpenMetadata is another open-source option with a single unified schema and built-in data quality tests and collaboration features; DataHub has a mature event-driven architecture and broad connector ecosystem. Collibra is commercial and process-centred. Choose on connector coverage for your stack, API needs, and who will operate the service.

**Failure modes.** Running ingestion once and never scheduling it; duplicate dataset entities because two recipes use different platform instances; lineage that only covers SQL models while Python jobs remain invisible.

**Validation.** Check that each production table appears once with the correct platform instance; compare DataHub lineage edges against a hand-drawn map for one pipeline; alert when ingestion runs fail.

**Lakehouse / Text2SQL fit.** Query DataHub's API to build the assistant's allow-list from tags such as `certified` and exclude assets tagged `deprecated` or `restricted`.

## Amundsen

Amundsen is an open-source data discovery catalog created at Lyft. It popularised a simple search-first experience ranked by usage, with table pages showing descriptions, owners, frequent users, and column statistics, backed by a graph database and a search index and fed by a "databuilder" ingestion library.

**Status.** The upstream project saw little activity in recent years, and its repository was archived in 2026. Verify the current repository status before choosing it: an archived project receives no security fixes or new connectors. Treat Amundsen as a useful reference design for search-first discovery rather than a default choice for a new lakehouse.

**Compared with DataHub and OpenMetadata.** Both are actively maintained, cover lineage and governance features Amundsen lacked or added late, and support Iceberg and modern engines. Teams migrating off Amundsen typically map its table, column, owner, and description records into one of them.

**Example (illustrative migration inventory):**

| Amundsen record | Target in DataHub/OpenMetadata | Check after migration |
|---|---|---|
| Table description | Dataset documentation | Count of described tables unchanged |
| Owners | Ownership aspect | Every certified table still has an owner |
| Badges / tags | Tags or glossary terms | Tag names mapped, not duplicated |
| Column stats | Profiling results | Re-run profiling; do not copy stale stats |

**Failure modes.** Keeping an archived service exposed on the network; losing curated descriptions during migration; assuming Amundsen lineage exists when it was never configured.

**Lakehouse / Text2SQL fit.** If Amundsen still holds your best descriptions, export them as the seed for the assistant's table documentation, then move to a maintained catalog.

## Active Metadata

Active metadata is metadata that is collected continuously and *used* to drive actions in other systems, rather than sitting in a catalog page waiting for someone to read it. Passive metadata answers "what is this?"; active metadata changes what happens next.

**How it works.** Events from engines, orchestrators, and quality tools (schema changed, check failed, table not queried in 180 days, PII detected) are published to a stream or API. Rules subscribe and act: add a warning banner in BI, open a ticket for the owner, propagate a PII tag to downstream columns through lineage, or remove a table from the assistant's allow-list.

**Example (illustrative rule):**

```yaml
when:
  event: quality_check_failed
  severity: blocking
  dataset_tag: certified
then:
  - set_dataset_status: degraded
  - notify: dataset.owner
  - text2sql_allowlist: suspend   # assistant answers "data is currently under investigation"
  - bi_banner: "Figures may be incomplete since {{event.time}}"
```

**Failure modes.** Automations that fire on noisy signals and train users to ignore banners; loops where an action generates the event that triggered it; actions with no audit trail.

**Validation.** Replay a recorded failure event in staging and verify each action happens once, is logged, and is reversed when the check recovers.

**Lakehouse / Text2SQL fit.** Active metadata is how an assistant learns that a certified table is currently unhealthy without a human editing its configuration.

## Active Data Governance

Active data governance means that governance rules are enforced by software at the moment data is used, not only described in documents and reviewed periodically. A classification tag set in the catalog causes masking to apply at query time; a retention rule causes a scheduled delete; a contract violation blocks publication.

**How it works.** Policies are written as code or configuration (tag-based masking, row filters, retention jobs, CI rules) and attached to metadata such as tags or domains. Enforcement points include the table catalog, query engines, BI tools, and pipelines. Evidence of enforcement (logs, test results) is collected automatically.

**Example (illustrative tag-based policy):**

```yaml
policy: mask-pii-email
applies_to: { tag: pii.email }
enforced_in: [trino, spark-sql, bi-semantic-layer]
rule: show_full_value_only_to_roles: [pii_reader]
evidence: daily denied-access test result stored in audit bucket
owner: privacy-office
```

**Failure modes.** A policy enforced in one engine but not another reading the same files; tags that are optional, so untagged columns are unprotected by default; nobody testing that the denial actually happens.

**Validation.** Maintain allowed/denied test cases per policy and run them in every engine that can read the data. Report the share of sensitive columns with an enforced policy.

**Lakehouse / Text2SQL fit.** The assistant must execute under the end user's identity so the same active policies apply; see [Access Control: RBAC, Row- and Column-Level Security](access-control-rbac-rls-cls.html).

## OpenLineage

OpenLineage is an open specification for describing lineage at run time. A job emits events saying "this run of this job started/completed/failed, reading these inputs and writing these outputs", with optional *facets* carrying schemas, column-level lineage, SQL text, data quality metrics, and more. Integrations exist for Spark, Airflow, dbt, Flink, and others, and consumers include Marquez, DataHub, and several commercial catalogs.

**How it works.** Each event has an `eventType` (`START`, `RUNNING`, `COMPLETE`, `FAIL`, `ABORT`), a `run` with a unique `runId`, a `job` identified by namespace and name, and lists of input and output datasets identified by namespace and name. Because the identifiers are standardised, lineage from different tools can be joined into one graph.

**Example (illustrative COMPLETE event, trimmed):**

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-11-16T06:04:12.512Z",
  "producer": "https://github.com/OpenLineage/OpenLineage/tree/1.x/integration/spark",
  "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent",
  "run": { "runId": "0193a1f2-7c55-7d1e-9a7e-2f4b9c3e1a10" },
  "job": { "namespace": "airflow-prod", "name": "build_marts.fct_orders" },
  "inputs": [
    { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines" }
  ],
  "outputs": [
    {
      "namespace": "iceberg://catalog.internal",
      "name": "analytics.fct_orders",
      "facets": {
        "columnLineage": {
          "fields": {
            "net_amount": {
              "inputFields": [
                { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines", "field": "gross_amount" },
                { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines", "field": "discount_amount" }
              ]
            }
          }
        }
      }
    }
  ]
}
```

The required facet metadata (`_producer`, `_schemaURL`) is omitted for brevity; check the specification version your integration emits.

**Failure modes.** Different jobs naming the same table differently (`s3://lake/...` versus `iceberg://...`), creating disconnected graphs; integrations that emit `START` but crash before `COMPLETE`; column-level lineage missing for UDFs or Python transformations.

**Validation.** For one pipeline, assert in CI that a test run emits events whose input and output names match the catalog identifiers. Monitor the ratio of `START` to terminal events.

**Lakehouse / Text2SQL fit.** Lineage lets you answer "which assistant answers used data from the partition that was later corrected?" and run impact analysis before changing a column the semantic model depends on.

## Marquez

Marquez is the reference implementation of an OpenLineage server, an LF AI & Data project. It receives OpenLineage events over HTTP, stores jobs, runs, and dataset versions in PostgreSQL, and provides an API and web UI to browse lineage graphs and run history.

**How it works.** Integrations are configured to send events to `POST /api/v1/lineage`. Marquez versions datasets and jobs as their schemas or code change, so you can see which run produced which dataset version.

**Example (illustrative check that lineage arrived):**

```bash
# Send a test event, then read the lineage graph for the output dataset.
curl -s -X POST http://marquez.internal:5000/api/v1/lineage \
  -H 'Content-Type: application/json' -d @complete_event.json
curl -s "http://marquez.internal:5000/api/v1/lineage?nodeId=dataset:iceberg://catalog.internal:analytics.fct_orders"
```

**Compared with DataHub and catalog lineage.** Marquez focuses narrowly on run-level lineage and is simple to stand up for learning or as a lineage backend. DataHub also ingests OpenLineage but adds discovery, ownership, and governance. Catalog-native lineage (for example in Unity Catalog) is convenient but may only see jobs that run on that platform.

**Failure modes.** Running Marquez without authentication on a shared network; no retention plan for event volume; treating Marquez as a full catalog.

**Validation.** Confirm the UI shows each production job with its latest run state and that failed runs appear as failed, not missing.

**Lakehouse / Text2SQL fit.** Marquez is a good lab component for this curriculum: emit events from the Project 1 pipeline and inspect the graph before adding a full catalog.

## Data Lineage vs Data Provenance

The two terms overlap but answer different questions.

| Aspect | Data lineage | Data provenance |
|---|---|---|
| Question | How did this data flow and change? | Where did it originate, who produced it, and under what authority? |
| Typical granularity | Datasets, columns, jobs, runs | Records, files, documents, or datasets with origin attributes |
| Captured by | Parsing SQL, OpenLineage events, orchestrator metadata | Source identifiers, ingestion metadata, signatures, licences, consent records |
| Main uses | Impact analysis, debugging, change management | Trust, audit, legal basis, reproducibility, AI training data due diligence |
| Example | `fct_orders.net_amount` derives from `gross_amount - discount_amount` | Row came from ERP export `orders_2026-11-15.csv`, SHA-256 `ab12...`, received via SFTP from vendor X under contract C-17 |

Lineage is mostly about the *path*; provenance is mostly about the *origin and authority*. A full audit needs both: lineage shows a metric came from a source table, provenance shows that source was authorised and unaltered.

**Validation.** Pick one reported number and try to produce both the lineage chain (jobs and tables) and the provenance record (source file, hash, receipt time, owner). Any gap is an action item.

## Data Provenance

Data provenance is the documented origin and history of data: what source produced it, which agent or system created or modified it, when, and under what authority or licence. The W3C PROV model describes this with *entities* (data), *activities* (processes), and *agents* (people, organisations, software).

**How it works.** At ingestion, record source system, extraction time, file or batch identifier, content hash, contract or legal basis, and the identity that loaded it. Keep these as columns (`_source_file`, `_ingested_at`, `_batch_id`) or in a side table, and preserve them through transformations. For high-trust data, sign files or manifests and store hashes in append-only storage so tampering is detectable.

**Example (illustrative provenance columns and check):**

```sql
-- Every published row must trace back to a recorded batch with a verified hash.
select count(*) as rows_without_provenance
from analytics.fct_orders f
left join ops.ingestion_batches b on f._batch_id = b.batch_id
where b.batch_id is null or b.hash_verified = false;
```

**Failure modes.** Dropping metadata columns in the first transformation; overwriting raw files in place so the hash no longer matches; using scraped or third-party data without recording its licence; RAG corpora with no record of which document version was indexed.

**Validation.** The query above returns zero; raw storage is immutable or versioned; a sample of AI-indexed documents can be traced to source version and owner.

**Lakehouse / Text2SQL fit.** Provenance lets an assistant say "based on ERP data loaded at 06:00 UTC" and lets reviewers prove which inputs informed a given answer.

## Practice

1. Draw two boxes for your lab: the table catalog and the discovery catalog. List which facts each is authoritative for.
2. Run Marquez locally, emit the illustrative OpenLineage event (with your own names), and confirm the lineage graph shows input and output.
3. Write a discovery record (owner, grain, classification, freshness, limitations) for three marts and derive the Text2SQL allow-list from it.
4. Add `_batch_id` and `_ingested_at` to one pipeline and implement the provenance check query.
5. Define one active metadata rule that suspends a table from the assistant when a blocking check fails, and test it with a replayed event.

### Completion criteria

- You can explain, in two sentences, why Polaris or Glue does not replace a discovery catalog and vice versa.
- At least one pipeline emits OpenLineage events whose dataset names match catalog identifiers.
- Every certified mart has an owner, steward, description, classification, and provenance columns.
- A blocking quality failure demonstrably changes what the assistant is allowed to query, and the change is logged.
