---
title: DataOps, CI/CD, and Infrastructure as Code
description: Apply version control, automated testing, continuous deployment, data branching, and Terraform to data pipelines and platforms.
order: 44
tags: [DataOps, CI/CD, continuous deployment, data as code, infrastructure as code, Terraform, GitHub Actions]
---

# DataOps, CI/CD, and Infrastructure as Code

A data platform changes constantly: new models, edited metric definitions, new sources, bigger clusters. DataOps is the discipline of making those changes small, reviewed, tested, and reversible. This page covers the practice, the automation that enforces it (CI/CD), how the same ideas apply to data itself (data as code), and how infrastructure is managed the same way (IaC and Terraform).

Assumption used in examples: a Git repository containing dbt models, semantic-layer YAML, orchestrator code, assistant evaluation fixtures, and a `infra/` folder with Terraform.

## DataOps

**What it is.** DataOps applies DevOps and lean practices to data work: version control for everything, automated testing, continuous integration and deployment, environment separation, observability, and short feedback loops between data producers and consumers. Its goal is to deliver reliable data changes quickly — speed and quality together, not one at the expense of the other.

**How it works.** In practice, a DataOps workflow looks like this:

1. Every change (SQL model, metric, DAG, permission, infrastructure) starts as a branch and a pull request.
2. Automated checks run on the pull request: lint, compile, unit tests, data tests on a sample or isolated environment, and impact analysis on downstream models and dashboards.
3. A reviewer from the owning team approves.
4. Merging deploys automatically to production, with data checks gating publication.
5. Production is observed (freshness, volume, schema, test failures, cost), and incidents feed back into new tests.

**Concrete example (illustrative definition of done for a data change).**

```text
[ ] Model and metric changes in Git, reviewed by domain owner
[ ] CI green: lint, compile, unit tests, data tests on changed models + downstream
[ ] Assistant evaluation suite unchanged or improved for affected metrics
[ ] Backfill plan written if history changes
[ ] Monitors and owner metadata updated
[ ] Rollback step known (revert commit, restore snapshot, or reset branch)
```

**Failure modes.** Buying a tool and calling it DataOps; tests that only check schema, not values; manual hotfixes in production that never reach Git; CI so slow that people bypass it.

**Validation.** Track lead time from pull request to production, change failure rate, mean time to restore after a data incident, and the share of incidents caught by tests before users noticed.

## CI/CD for Data

**What it is.** CI/CD for data applies continuous integration (automatically building and testing every change) and continuous delivery or deployment (automatically releasing tested changes) to pipelines, SQL models, semantic definitions, and platform code.

**How it works.** Data CI differs from application CI because correctness depends on data, not just code. Common techniques:

- **Isolated environments**: build changed models into a per-pull-request schema or a branch of the catalog.
- **Slim builds**: build only modified models and their downstream dependents, deferring unchanged upstream references to production artifacts.
- **Data tests**: uniqueness, not-null, accepted values, relationships, row-count and reconciliation tests.
- **Diffs**: compare the changed model's output to production (row counts, changed values, distribution shifts).
- **Semantic and AI checks**: validate metric YAML and run the assistant's golden-question suite when metrics change.

**Concrete example (illustrative GitHub Actions workflow).**

```yaml
name: data-ci
on:
  pull_request:
    paths: ["models/**", "semantic/**", "evals/**"]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    env:
      DBT_TARGET: ci
      CI_SCHEMA: pr_${{ github.event.pull_request.number }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.lock
      - name: Lint SQL
        run: sqlfluff lint models/
      - name: Fetch production manifest for state comparison
        run: ./scripts/download_prod_manifest.sh prod-artifacts/
      - name: Build and test changed models plus downstream
        run: dbt build --select state:modified+ --defer --state prod-artifacts/
      - name: Validate semantic definitions
        run: ./scripts/validate_semantic_layer.sh      # e.g. MetricFlow config validation
      - name: Assistant golden questions
        run: python -m evals.run --suite text2sql_golden --fail-under 0.95
      - name: Drop CI schema
        if: always()
        run: ./scripts/drop_schema.sh "$CI_SCHEMA"
```

**Failure modes.** CI that uses tiny fixtures and misses production-scale issues; tests passing on an empty table; secrets for production exposed to pull-request jobs from forks; leftover CI schemas accumulating cost; flaky tests that teach people to re-run until green.

**Validation.** Introduce a known bad change (duplicate key, renamed column used downstream, metric formula error) and confirm CI blocks it; review CI duration and cost monthly; use least-privilege credentials for CI.

## Continuous Deployment (CD)

**What it is.** Continuous deployment releases every change that passes the automated pipeline to production with no manual approval step. It differs from **continuous delivery**, where every change is kept *releasable* but a person decides when to release.

**How it works.** For data, deployment means more than copying code: new model versions must be built, possibly backfilled, validated, and then made visible. Safe patterns include:

- **Blue/green or write-audit-publish**: build into a staging schema or branch, run checks, then swap or merge atomically.
- **Versioned models**: publish `fct_orders_v2` alongside `v1` and migrate consumers before retiring `v1`.
- **Feature flags for metrics**: ship a new metric definition hidden, compare, then expose.

**Concrete example (illustrative deploy job on merge).**

```yaml
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production        # holds prod secrets; add required reviewers here for continuous *delivery*
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.lock
      - run: dbt build --target prod_staging --select state:modified+ --state prod-artifacts/
      - run: python scripts/audit_staging.py --max-row-change-pct 5
      - run: python scripts/publish.py --from prod_staging --to prod   # atomic swap
      - run: python scripts/upload_manifest.py prod-artifacts/
```

**Failure modes.** Fully automatic deployment of changes that rewrite history (a changed revenue definition silently alters last year's numbers); deployment succeeding while the backfill fails; no rollback path for data.

**Validation.** Decide explicitly which change types may deploy continuously (new columns, new tests) and which require continuous delivery with a human gate (metric definition changes, backfills, deletions). Practise rollback.

## Data as Code

**What it is.** Data as code applies Git-like workflows — branches, commits, tags, merges, and reverts — to the data itself, not only to the code that produces it. With a versioned catalog or table format you can build on an isolated branch, validate, and merge atomically into the production view.

**How it works.** Several layers provide this:

- **Table formats**: Apache Iceberg supports snapshots, branches, and tags per table; Delta Lake supports time travel by version.
- **Versioned catalogs**: Project Nessie versions a whole catalog of Iceberg tables, so a branch can hold coordinated changes to many tables and merge them together.
- **Object-store versioning**: lakeFS provides Git-like branches over files in object storage.

The common pattern is **write-audit-publish (WAP)**: write to a branch, audit with data tests, publish by merging or fast-forwarding.

**Concrete example (illustrative, Iceberg branch with Spark SQL).**

```sql
-- 0. One-time: allow write-audit-publish on the table
ALTER TABLE lake.analytics.fct_orders SET TBLPROPERTIES ('write.wap.enabled' = 'true');

-- 1. Create an audit branch for today's load
ALTER TABLE lake.analytics.fct_orders CREATE BRANCH audit_20261117;

-- 2. Point writes at the branch (Spark session config), then run the normal job
SET spark.wap.branch = audit_20261117;
INSERT OVERWRITE lake.analytics.fct_orders SELECT * FROM lake.staging.orders_20261117;

-- 3. Audit the branch (read it explicitly)
SELECT count(*), count(distinct order_id)
FROM lake.analytics.fct_orders VERSION AS OF 'audit_20261117';

-- 4. Publish atomically if checks pass
CALL lake.system.fast_forward('analytics.fct_orders', 'main', 'audit_20261117');
```

For changes spanning several tables (facts and dimensions that must stay consistent), a catalog-level branch such as Nessie's is safer than per-table branches.

**Failure modes.** Branches left open forever and diverging; readers accidentally pointed at a non-main branch; retention or snapshot expiry removing the version you planned to roll back to; assuming branching makes copies free for every engine (support varies).

**Validation.** Test the rollback (reset `main` to a previous snapshot) on a non-production table; monitor branch count and age; confirm every consumer, including BI tools and the assistant, reads `main` or a pinned tag explicitly.

**Connection to the governed analytics assistant.** Versioned data lets you pin evaluation runs to a tag (for example `eval_2026_11`) so a change in assistant accuracy can be attributed to the model, the prompt, or the data. It also allows answers to carry provenance such as "computed from snapshot 8812 of `fct_orders`".

## Infrastructure as Code (IaC)

**What it is.** Infrastructure as code defines servers, networks, storage, databases, permissions, and managed services in version-controlled files and applies them with tools, instead of clicking in consoles.

**How it works.** Tools are either **declarative** (you describe the desired end state and the tool works out the changes — Terraform/OpenTofu, AWS CloudFormation, Pulumi in many uses) or **imperative** (scripts that perform steps in order). Declarative tools compare desired state, recorded state, and real state, then plan the difference. Benefits are reproducible environments, code review for infrastructure changes, and an audit trail.

**Failure modes.** **Drift**: someone changes a resource manually and the code no longer reflects reality; secrets committed to the repository; one huge configuration where any change risks everything; production and development defined by copy-paste instead of shared modules.

**Validation.** Run `plan` in CI for every pull request and review it; detect drift on a schedule; scan configurations with policy tools (for example checks that buckets are not public and encryption is on).

## Terraform

**What it is.** Terraform, created by HashiCorp (now part of IBM), is a declarative IaC tool using the HashiCorp Configuration Language (HCL). After a 2023 license change, the community fork **OpenTofu** became an open-source alternative with largely compatible syntax.

**How it works.**

- **Providers** are plugins that talk to APIs (AWS, Google Cloud, Azure, Snowflake, Databricks, Kubernetes, and many more).
- **Resources** declare objects to manage; **data sources** read existing ones; **modules** package reusable groups.
- **State** records which real objects correspond to which resources. Store it in a remote backend with locking, never only on a laptop.
- `terraform plan` shows proposed changes; `terraform apply` executes them.

**Concrete example (illustrative, AWS lakehouse storage and catalog).**

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket       = "acme-tf-state"
    key          = "lakehouse/prod.tfstate"
    region       = "eu-west-1"
    use_lockfile = true      # S3-native state locking in recent versions
  }
}

resource "aws_s3_bucket" "lake" {
  bucket = "acme-lake-prod"
  tags   = { owner = "data-platform", env = "prod" }
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_glue_catalog_database" "analytics" {
  name = "analytics"
}
```

A CI job runs `terraform fmt -check`, `terraform validate`, and `terraform plan`, posts the plan to the pull request, and only an approved merge runs `apply` with production credentials.

**Failure modes.** A plan that shows "destroy and recreate" on a storage bucket or database because a name changed (use `lifecycle { prevent_destroy = true }` on critical data stores); concurrent applies corrupting state without locking; provider version upgrades changing behavior; secrets ending up in state files (state must be encrypted and access-controlled).

**Validation.** Read every plan for `destroy` actions before approving; pin provider versions; test modules in a sandbox account; run scheduled drift detection with `terraform plan -detailed-exitcode`.

**Connection to the governed analytics assistant.** The assistant's access boundary is infrastructure: the read-only database role, network rules, secret storage, and log retention. Define them in Terraform so a reviewer can see exactly what the assistant may touch, and so an accidental grant of write access shows up as a reviewable diff.

## Practice

1. Put your Project 1 dbt project, semantic YAML, and a Terraform folder in one repository.
2. Add a GitHub Actions workflow that lints, builds changed models into a per-PR schema, runs tests, and runs five assistant golden questions.
3. Open three pull requests with deliberate bugs (duplicate key, broken downstream reference, wrong metric filter) and confirm each is blocked.
4. Implement write-audit-publish with an Iceberg branch, Nessie, lakeFS, or a staging-schema swap, and practise one rollback.
5. Manage one storage bucket and one read-only database role with Terraform; change something manually and detect the drift.

**Completion criteria.**

- CI links for one green and three intentionally red pull requests.
- A written policy listing which change types deploy continuously and which need a human gate.
- Evidence of a successful audit failure (bad data never reached `main`) and a successful rollback.
- A Terraform plan output for the assistant's read-only access, reviewed in a pull request, plus a drift detection result.
