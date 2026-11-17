---
title: Data Governance and Data Products
description: Make data ownership, meaning, quality, access, and change policies operational.
order: 8
tags: [governance, catalog, lineage, data products]
---

# Data Governance and Data Products

Data governance is the set of decision rights, responsibilities, and controls that keep data understandable and appropriate to use. It works when policies reach the systems and workflows that produce and consume data, not only when they are written in a document.

## Governance responsibilities

- **Ownership:** a named business or technical owner is accountable for definition, quality expectations, and change decisions.
- **Stewardship:** a steward maintains terms, classifications, and issue context with domain experts.
- **Access:** approved identities receive the minimum permissions required for a defined purpose.
- **Privacy and retention:** sensitive fields have handling rules, retention periods, and deletion behavior.
- **Quality and contracts:** producers and consumers agree on schema, meaning, freshness, and breaking-change behavior.
- **Lifecycle:** datasets have an intended use, support status, recovery expectations, and deprecation path.

Governance decisions should be traceable: record who approved a definition, when a policy changed, and which systems enforce it.

## Catalog and lineage

A data catalog should help users find and assess datasets. Useful metadata includes business definition, owner, domain, classification, source, update cadence, quality status, lineage, and known limitations. Automate metadata collection where possible, then provide an ownership path to correct stale or ambiguous entries.

Lineage connects sources, transformations, and consumers. It supports impact analysis before a schema change and helps diagnose a metric discrepancy. Distinguish technical lineage inferred from code from business lineage that explains why a transformation exists.

## Data product contract

A data product is a supported interface for a defined consumer need, with an owner and expectations. A useful contract includes:

| Contract field | What to specify |
|---|---|
| Purpose and users | Which decision or workflow does it support? |
| Schema and semantics | What does each field mean, and at what grain? |
| Quality and freshness | Which checks and delivery targets are promised? |
| Interface | Table, file, event stream, API, or semantic model |
| Access and privacy | Which identities and data classifications apply? |
| Change policy | How are additions, breaking changes, and deprecation handled? |
| Support | Owner, incident route, and recovery expectations |

A table is not automatically a data product. Avoid product labels without a consumer, maintained contract, and support path.

## Data Contracts vs. Data Product vs. Data Mesh vs. Governance

These four terms describe related layers at different altitudes, and are often used loosely as synonyms. They are not:

- **Data contract** - the "what": a specific, technical agreement on schema, semantics, and SLA (freshness, quality, change policy) between one producer and its consumers. See [Data Quality and Contracts](data-quality-contracts.html).
- **Data product** - the "why/for whom": a dataset treated as a product, with a named owner, documentation, and a quality bar, usually implemented through one or more data contracts (the "Data product contract" table above).
- **Data mesh** - an organizational and architectural pattern: domain teams own their data products end to end, under federated governance standards set centrally. Data products and the contracts behind them are building blocks a mesh is assembled from, not a prerequisite for using either term on its own.
- **Data governance** - the overarching policy and compliance layer (ownership, classification, access, retention) that contracts and products operate within, mesh or no mesh.

**A genuine debate, not a settled fact.** Some practitioners argue "data contract" mostly repackages ideas that schema evolution (see [Event Streaming Platforms](event-streaming-platforms.html)) and data quality tooling already covered, under a newer, more marketable name, and that what is actually new is organizational - naming a consumer-facing owner and an SLA, not the enforcement mechanism itself. Treat the term with that skepticism when evaluating a vendor claim or a new internal process: ask what capability is actually new versus relabeled.

## Master and reference data

Master data represents core entities such as customer, product, or supplier shared across systems. Reference data provides controlled lists such as country codes, lifecycle states, or currencies. Define authoritative sources, identifiers, match/merge rules, and conflict resolution. Preserve source identifiers and history so harmonization does not erase provenance.

A centralized master-data process can improve consistency but may add latency and governance overhead. Start with the cross-system problem and required ownership rather than introducing a master data management tool by default.

## Data Stewardship

Data stewardship assigns named people day-to-day accountability for the meaning, quality, and appropriate use of data in a domain. The **owner** decides (what a field means, who may access it, when a breaking change is acceptable); the **steward** keeps those decisions accurate and visible: maintaining glossary terms and descriptions, reviewing classifications, triaging quality issues with producers, and answering consumer questions. Technical custodians (platform or data engineers) operate the systems that enforce the decisions.

**How it works.** Stewards are assigned per domain or data product, not per tool. In a data mesh, each domain team has its own stewards, while a central governance group sets shared standards (classification levels, naming, required metadata) and audits them. Stewardship work flows through queues: new datasets to describe and classify, quality incidents to triage, access requests to review, and definitions to reconcile.

**Example (illustrative stewardship RACI for a customer domain):**

| Activity | Owner | Steward | Platform engineer | Consumers |
|---|---|---|---|---|
| Approve definition of "active customer" | A | R | I | C |
| Classify new columns | A | R | C | I |
| Triage failed quality check | I | A | R | I |
| Approve access to PII columns | A | R | I (implements) | I |
| Deprecate a table | A | R | R | C |

R = responsible, A = accountable, C = consulted, I = informed.

**Failure modes.** Stewardship as an unfunded side task, so queues grow; one central steward for every domain; stewards without authority to block a bad definition; catalog entries edited by anyone with no review.

**Validation.** Every certified asset has a named steward who is still employed in that domain; track queue age and the share of assets with current descriptions and classifications.

**Lakehouse / Text2SQL fit.** Stewards approve the descriptions, synonyms, and examples the assistant uses. Treat changes to that context like code changes, reviewed by the steward. See [Metadata Catalogs, Discovery, and Lineage](metadata-catalogs-and-lineage.html) for the tooling.

## Data Classification

Data classification is the process of identifying data and labelling it by sensitivity and handling requirements so the right controls apply automatically. Labels are only useful when each level maps to concrete rules.

**Example (illustrative classification scheme):**

| Level | Examples | Default handling |
|---|---|---|
| Public | Published product catalogue | No restriction |
| Internal | Order counts, non-personal operational metrics | Employees with a business need |
| Confidential | Customer identifiers, revenue by customer, contracts | Role-based access, masking outside approved roles, encrypted at rest |
| Restricted | National IDs, payment data, health data, credentials | Tokenised or encrypted columns, named approvers, access logged and reviewed |

**How it works.** Producers declare classifications in contracts; automated scanners propose tags for new columns from names and value patterns; stewards confirm or correct them. Tags are stored in the catalog and, where supported, propagated through lineage to derived columns. Tag-based policies (masking, row filters, retention) then attach to the tag rather than to each table.

```yaml
# Illustrative column tags in a model contract
columns:
  - name: email
    tags: [classification.confidential, pii.email]
  - name: national_id
    tags: [classification.restricted, pii.government_id]
  - name: country
    tags: [classification.internal]
```

**Failure modes.** Unclassified columns treated as public by default (make "unclassified" behave like confidential); classification of a table but not of a free-text column inside it; tags not propagated to derived tables, extracts, or vector indexes; scanners trusted without review.

**Validation.** Report the share of columns classified per layer; fail CI when a new mart column lacks a classification; sample derived tables to confirm tags were inherited.

**Lakehouse / Text2SQL fit.** Use classification to filter the schema context and allow-list for the assistant: only `public` and `internal` columns by default, others only when the end user's role permits. Privacy techniques for the higher levels are covered in [Privacy and PII Protection](privacy-and-pii-protection.html), and enforcement in [Access Control](access-control-rbac-rls-cls.html).

## Make policy executable

Translate policy into catalog classifications, warehouse permissions, masking, retention jobs, schema checks, and CI review rules. Test both allowed and denied access. For sensitive data, verify where copies travel, which logs include values, which AI providers receive prompts, and how deletion propagates to derived tables and indexes.

## Related lessons

- [Metadata Catalogs, Discovery, and Lineage](metadata-catalogs-and-lineage.html)
- [Data Quality Tooling and Observability](data-quality-tooling-and-observability.html)
- [Access Control: RBAC, Row- and Column-Level Security](access-control-rbac-rls-cls.html)
- [Privacy and PII Protection](privacy-and-pii-protection.html)
- [Encryption and Key Management](encryption-and-key-management.html)
- [Security Posture and Threat Modeling](security-posture-and-threat-modeling.html)

## Practice

Choose a customer dataset used by a dashboard and a Text2SQL service. Define its product owner, steward, grain, quality/freshness contract, classification, access roles, lineage, breaking-change policy, and deprecation route. Add one example of a policy enforced automatically and one that still requires human approval.