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

## Master and reference data

Master data represents core entities such as customer, product, or supplier shared across systems. Reference data provides controlled lists such as country codes, lifecycle states, or currencies. Define authoritative sources, identifiers, match/merge rules, and conflict resolution. Preserve source identifiers and history so harmonization does not erase provenance.

A centralized master-data process can improve consistency but may add latency and governance overhead. Start with the cross-system problem and required ownership rather than introducing a master data management tool by default.

## Make policy executable

Translate policy into catalog classifications, warehouse permissions, masking, retention jobs, schema checks, and CI review rules. Test both allowed and denied access. For sensitive data, verify where copies travel, which logs include values, which AI providers receive prompts, and how deletion propagates to derived tables and indexes.

## Practice

Choose a customer dataset used by a dashboard and a Text2SQL service. Define its product owner, steward, grain, quality/freshness contract, classification, access roles, lineage, breaking-change policy, and deprecation route. Add one example of a policy enforced automatically and one that still requires human approval.