---
title: Reverse ETL, Operational Analytics, and CDPs
description: Push governed warehouse and lakehouse data into operational tools safely, and compare reverse ETL platforms with customer data platforms.
order: 42
tags: [reverse ETL, data activation, operational analytics, CDP, composable CDP, Hightouch, Census]
---

# Reverse ETL, Operational Analytics, and CDPs

Dashboards inform; operational tools act. A support agent sees a customer's lifetime value in the help desk, a sales rep sees product usage in the CRM, a marketing tool receives an audience of lapsed buyers. Getting modeled data from the analytical platform into those tools is called **reverse ETL** or **data activation**. It turns your marts into inputs for live business processes, so the reliability bar goes up.

Assumption used in examples: a mart `analytics.customer_360` with one row per customer (`customer_id`, `email`, `lifetime_paid_revenue_usd`, `last_paid_at`, `region`, `marketing_consent`), rebuilt daily.

## Operational Analytics

**What it is.** Operational analytics delivers metrics and attributes computed on the analytical platform to the tools frontline teams use every day — CRM, help desk, ad platforms, email tools, internal apps — so decisions happen inside the workflow rather than in a separate dashboard.

**How it works.**

1. Model the operational dataset in the warehouse or lakehouse with a stable key and grain.
2. Map columns to fields in the destination (for example `lifetime_paid_revenue_usd` → a custom CRM field).
3. Sync on a schedule or after the upstream pipeline publishes, sending only changed rows.
4. Monitor delivery, rejections, and drift between source and destination.

The main tools are reverse ETL platforms (below), custom sync jobs, analytics APIs that applications call on demand, and CDPs.

**Concrete example (illustrative sync model).**

```sql
-- Model for a CRM sync: one row per customer, only fields the CRM owner approved
select
  customer_id,                                   -- sync key
  email,
  round(lifetime_paid_revenue_usd, 2) as ltv_usd,
  case when last_paid_at < current_date - interval '90' day then 'at_risk' else 'active' end as health,
  region
from analytics.customer_360
where email is not null
```

**Failure modes.**

- *Field ownership conflict*: a sync overwrites a field that sales reps edit by hand.
- *Stale action*: the sync runs before the daily build finishes and pushes yesterday's values.
- *Silent rejections*: the destination API rejects rows (invalid email, field length) and nobody looks.
- *Rate limits*: a full resync of millions of rows exceeds API quotas and takes days.
- *Definition drift*: "health" in the CRM no longer matches the definition in the dashboard.

**Validation.** Reconcile counts and a sample of values between source and destination after each sync; alert on rejection rate above a threshold; record which fields each sync owns; trigger syncs from the orchestrator after data quality checks pass.

**Connection to the governed analytics assistant.** The assistant answers "which customers are at risk?" from the same `customer_360` model and the same `health` definition the CRM receives. If the assistant ever proposes *writing* to an operational tool, that is an action, not an answer: route it through a reviewed sync with human approval, never through free-form tool calls.

## Hightouch

**What it is.** Hightouch is a commercial data activation platform that started as a reverse ETL tool and now positions itself as a "composable CDP". It reads models from your warehouse or lakehouse engine and syncs them to hundreds of SaaS destinations.

**How it works.** You define a **model** (a SQL query, a table, or a dbt model) with a primary key. A **sync** maps model columns to destination fields and chooses a mode such as upsert, update-only, insert, or mirror (also deleting destination records that leave the model). Hightouch computes the difference since the last run so only changed rows are sent; it can keep that change-tracking state inside your warehouse. Additional features cover audience building for marketers, identity resolution, and event collection. It supports engines commonly used on lakehouses, such as Databricks, Snowflake, BigQuery, and Trino-compatible sources — check the current connector list for yours.

**Concrete example (illustrative sync definition; not exact product syntax).**

```yaml
model:
  name: crm_customer_health
  source: warehouse_prod
  sql_file: models/crm_customer_health.sql
  primary_key: customer_id
sync:
  destination: salesforce_prod
  object: Contact
  mode: update_only               # never create contacts; sales owns creation
  match: { source: email, destination: Email }
  fields:
    ltv_usd: LTV_USD__c
    health: Customer_Health__c
  schedule: { trigger: after_dbt_job, job: daily_marts }
  on_failure: { alert: "#data-activation", reject_threshold_pct: 2 }
```

**Failure modes and validation.** Same as operational analytics, plus: mirror mode deleting records when an upstream filter bug empties the model. Guard with a minimum-row-count check before the sync, and prefer update-only until ownership is clear.

## Census

**What it is.** Census is a reverse ETL and data activation tool with a similar model-and-sync design. Fivetran acquired Census in 2025 and now offers its capability as part of the Fivetran platform (branded as activations), pairing ingestion (source → warehouse) and activation (warehouse → apps) in one vendor. Check current naming and packaging before planning a purchase.

**How it works.** You register a warehouse or lakehouse connection, define models or use dbt models, and create syncs with a sync key and behavior (for example update-or-create, update-only, or mirror). Census computes diffs between runs, reports per-record rejections, and can trigger syncs via API or after upstream jobs.

**Concrete example (illustrative orchestration trigger).**

```python
# Airflow task that runs only after marts and quality checks succeed
from airflow.decorators import task
import requests

@task(retries=2)
def trigger_activation_sync(sync_id: str) -> str:
    resp = requests.post(
        f"{ACTIVATION_API}/syncs/{sync_id}/trigger",   # illustrative endpoint
        headers={"Authorization": f"Bearer {ACTIVATION_TOKEN}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["sync_run_id"]
```

**Failure modes and validation.** Triggering by fixed clock instead of upstream success; retrying a trigger that already started a run (check for an in-progress run first); losing per-record rejection details. Store the sync run ID in your run log and reconcile rejections daily.

**Hightouch vs Census.** Both cover the core reverse ETL pattern well; the differences are in destination coverage, audience and identity features, pricing, and — after the acquisition — whether consolidating with your ingestion vendor helps or creates lock-in. Run a proof of concept with your own highest-risk destination.

## Customer Data Platform (CDP)

**What it is.** A customer data platform builds unified customer profiles from many sources — web and app events, CRM, support, purchases — and makes those profiles and audiences available to marketing and service tools.

**How it works.** Core functions are event collection, **identity resolution** (deciding that a cookie ID, an email, and a CRM contact are one person, using deterministic rules or probabilistic matching), profile unification, audience segmentation, consent management, and activation to destinations.

| | Packaged CDP | Composable CDP |
|---|---|---|
| Where data lives | Vendor's own store | Your warehouse or lakehouse |
| Identity resolution | Vendor-managed | Your models or the activation tool's feature |
| Strength | Fast start, marketer-friendly UI, real-time features | One source of truth, reuse of governed models, no extra copy |
| Risk | Second copy of customer data with its own definitions | Requires data engineering capacity and good models |

Examples of packaged CDPs include Twilio Segment, Salesforce Data Cloud, and Adobe Real-Time CDP. A composable CDP combines your platform with tools such as Hightouch or Census.

**Concrete example (illustrative deterministic identity rule).**

```sql
-- Link identifiers that share a verified email; one stable person_id per cluster
select
  coalesce(c.customer_id, w.anonymous_id) as identifier,
  md5(lower(trim(coalesce(c.email, w.login_email)))) as person_id
from staging.crm_contacts c
full outer join staging.web_logins w
  on lower(trim(c.email)) = lower(trim(w.login_email))
where coalesce(c.email, w.login_email) is not null
```

**Failure modes.** Over-merging (shared family or work emails collapse different people into one profile); under-merging (duplicate profiles); activating people who withdrew consent; regulatory exposure from copying personal data into many tools.

**Validation.** Measure merge rates and inspect samples of the largest clusters; test consent filters with fixture customers who opted out; keep an audit trail of which audience went to which destination when.

**Connection to the governed analytics assistant.** Customer-level profiles are sensitive. The assistant should answer aggregate questions about segments by default and only expose individual profiles to users whose role allows it, with every lookup logged.

## Practice

1. Build `customer_360` from your Project 1 marts with grain, key, and owner documented.
2. Write a sync model for a mock CRM (a local PostgreSQL table or a JSON file works) and implement an idempotent upsert job keyed on `customer_id`.
3. Add a pre-sync guard: abort if the model row count drops more than 20% versus the previous run.
4. Inject three bad rows (null email, duplicate key, overlong field) and show how each is rejected and reported.
5. Write a field-ownership table: which fields the sync owns and which humans own.

**Completion criteria.**

- Running the sync twice produces no duplicate or changed records in the destination.
- The row-count guard blocks a deliberately emptied model.
- A reconciliation report lists source count, destination count, and rejected rows with reasons.
- A one-paragraph decision note on packaged versus composable CDP for a hypothetical company.
