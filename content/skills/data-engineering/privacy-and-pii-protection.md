---
title: Privacy and PII Protection
description: Find and protect personal data, meet GDPR and CCPA obligations including true deletion in Iceberg, and choose between tokenization, anonymization, and differential privacy.
order: 23
tags: [privacy, pii, gdpr, ccpa, tokenization, anonymization, differential privacy, iceberg]
---

# Privacy and PII Protection

Privacy is about using personal data lawfully, for a stated purpose, with no more data and no longer retention than needed, and honouring the rights of the people the data describes. Security controls (access, encryption) are necessary for privacy but not sufficient: a perfectly secured table can still be used for a purpose nobody consented to.

This page is an engineering guide, **not legal advice**. Laws differ by jurisdiction and change; confirm obligations with your privacy or legal team. Assumptions for the examples: an Iceberg lakehouse with raw, staging, and mart layers, Spark for maintenance procedures, and a Text2SQL assistant over curated marts.

## PII

Personally identifiable information (PII) is any data that can identify a specific person, either directly (name, email, national ID, phone) or indirectly when combined with other data (postcode + birth date + gender, device ID, precise location, free-text notes). GDPR uses the broader term *personal data*, which also covers online identifiers and pseudonymous IDs that can be linked back to a person.

**How to find it.** Combine (1) declared classification by producers in contracts, (2) automated scanning of column names, value patterns, and sample content, and (3) review of free-text fields, JSON payloads, logs, and files where PII hides. Record results as tags in the catalog so policies can attach to them (see [Data Classification](governance-and-data-products.html#data-classification)).

**Example (illustrative scan query for email-like values in unexpected columns):**

```sql
select 'support_tickets.body' as location, count(*) as hits
from staging.support_tickets
where regexp_like(body, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}');
```

**How to truly delete it in Iceberg.** A `DELETE` in Iceberg creates a new snapshot; older snapshots still reference data files that contain the deleted rows, so time travel can still read them. With merge-on-read, the rows also physically remain in data files until compaction. A complete erasure therefore needs several steps:

```sql
-- 1. Logically delete (Spark SQL).
delete from lake.crm.customers where customer_id = 'C-1042';
delete from lake.analytics.fct_orders where customer_id = 'C-1042';

-- 2. Rewrite data files so merge-on-read delete files are applied.
call lake.system.rewrite_data_files(table => 'crm.customers', options => map('delete-file-threshold', '1'));

-- 3. Expire snapshots that still reference the old files (respect your retention policy).
call lake.system.expire_snapshots(table => 'crm.customers', older_than => timestamp '2026-11-17 00:00:00', retain_last => 1);

-- 4. Remove files no longer referenced by any metadata.
call lake.system.remove_orphan_files(table => 'crm.customers');
```

Then handle copies outside the table: raw landing files, backups, downstream extracts, caches, search and vector indexes, and logs. Illustrative only; check procedure options for your Iceberg version and test on a copy first.

**Failure modes.** PII in free text or JSON that column-name scanners miss; deletes applied to marts but not raw files; snapshot retention of 90 days silently keeping deleted data; PII sent to an external LLM in prompts or stored in assistant logs.

**Validation.** After an erasure, search every layer and index for the subject's identifiers, including time travel to the oldest retained snapshot, and record the evidence.

**Lakehouse / Text2SQL fit.** Keep PII out of the assistant's default schema context and out of prompt logs; route questions that need personal data to an approved, audited path.

## Data Privacy

Data privacy is the discipline of handling personal data according to the individual's rights and the organisation's legal obligations: a lawful basis or consent for processing, purpose limitation, data minimisation, accuracy, storage limitation, security, and transparency.

**How it works in engineering terms.**

| Principle | Engineering control |
|---|---|
| Purpose limitation | Record purpose per dataset; restrict access by purpose, not only by team |
| Minimisation | Do not ingest columns no use case needs; drop or hash identifiers early |
| Storage limitation | Retention jobs per table and layer, including snapshot expiry |
| Rights handling | Searchable subject index, deletion and export workflows, evidence |
| Transparency | Catalog records what personal data exists and why |

**Example (illustrative dataset privacy record):**

```yaml
dataset: crm.customers
personal_data: [name, email, phone, address]
purpose: [order fulfilment, customer support]
lawful_basis: contract
retention: 3 years after last order, then delete
subject_key: customer_id
processors: [email-service-vendor]
```

**Failure modes.** Analytics reuse for a new purpose without review; subject keys inconsistent across systems so requests cannot be fulfilled completely; retention configured in the warehouse but not on object storage.

**Validation.** For a test subject, run access and deletion requests end to end and measure completeness and time.

## Data Privacy by Design

Privacy by design means building privacy protections into systems from the first design decision rather than adding them after launch. Ann Cavoukian's framework describes seven principles, and GDPR Article 25 makes "data protection by design and by default" a legal obligation in the EU.

The seven principles, translated into data platform practice:

1. **Proactive, not reactive:** include a privacy review in design docs for new pipelines.
2. **Privacy as the default setting:** new columns are restricted until classified; new users get no access to personal data.
3. **Privacy embedded into design:** pseudonymise at ingestion; build deletion paths before launch.
4. **Full functionality (positive-sum):** offer aggregated or tokenised marts so analytics still works without raw identifiers.
5. **End-to-end security:** protect data across its life, from collection through deletion, including backups.
6. **Visibility and transparency:** document processing in the catalog and make it auditable.
7. **Respect for user privacy:** honour consent and preferences quickly and completely.

**Example (illustrative design checklist item in a pipeline PR template):**

```markdown
- [ ] New personal data fields listed and classified
- [ ] Purpose and lawful basis recorded in the dataset privacy record
- [ ] Default access: restricted; masking policy attached
- [ ] Deletion path tested for one subject across raw, staging, mart, index
```

**Failure modes.** A checklist that is ticked without evidence; "default restricted" broken by schema-level grants; privacy review after the data is already flowing.

**Validation.** Audit a sample of recent pipelines for the checklist evidence.

## GDPR

The General Data Protection Regulation is the European Union law governing processing of personal data of people in the EU (and EEA). It applies to organisations established in the EU and to those outside it that offer goods or services to, or monitor, people in the EU.

**What it demands of a data platform, in practice:**

- A lawful basis for each processing purpose (such as consent, contract, legal obligation, or legitimate interests).
- Data subject rights: access, rectification, erasure ("right to be forgotten"), restriction, portability, and objection, normally answered within one month.
- Data protection impact assessments (DPIAs) for high-risk processing, which can include large-scale profiling or AI use cases.
- Records of processing activities, processor contracts, and breach notification to the supervisory authority without undue delay and, where feasible, within 72 hours.
- Rules for transferring personal data outside the EEA, which affect where storage buckets, replicas, and AI providers are located (data residency).
- Penalties that can reach the higher of EUR 20 million or 4% of worldwide annual turnover for the most serious infringements.

**Example (illustrative erasure request log):**

```json
{
  "request_id": "DSR-2026-0815",
  "type": "erasure",
  "subject_key": "C-1042",
  "received_at": "2026-11-02T09:14:00Z",
  "systems": {
    "crm.customers": "deleted+expired 2026-11-05",
    "analytics.fct_orders": "deleted+expired 2026-11-05",
    "raw/crm/": "files rewritten 2026-11-05",
    "vector_index.support_docs": "chunks removed 2026-11-06",
    "backups": "expire by 2026-12-05 per backup policy"
  },
  "verified_by": "privacy-ops",
  "completed_at": "2026-11-06T16:30:00Z"
}
```

**Failure modes.** Pseudonymised data treated as out of scope (it is still personal data); replicas or AI processing in a region not covered by transfer safeguards; erasure that misses snapshots or backups.

**Lakehouse / Text2SQL fit.** Use the deletion procedure from the [PII](#pii) section, partition or bucket by region where residency matters, and confirm where the assistant's model provider processes prompts.

## CCPA

The California Consumer Privacy Act, as amended by the California Privacy Rights Act (CPRA), gives California residents rights over personal information held by businesses that meet its revenue or data-volume thresholds. It is enforced by the California Privacy Protection Agency and the Attorney General.

**Key consumer rights:** to know what personal information is collected and how it is used and shared; to delete; to correct; to opt out of the *sale* or *sharing* (for cross-context behavioural advertising) of personal information; to limit use of sensitive personal information; and freedom from discrimination for exercising these rights.

**Compared with GDPR.** CCPA is largely an opt-out model for sale and sharing, whereas GDPR requires a lawful basis before processing. Definitions, timelines, and exemptions differ, so the same platform capabilities (subject index, deletion, export, opt-out flags) are needed but configured per law.

**Example (illustrative opt-out enforcement in a mart feeding an ad partner export):**

```sql
create or replace view exports.ad_partner_audience as
select c.hashed_email, c.segment
from analytics.dim_customer c
left join privacy.consumer_preferences p on c.customer_id = p.customer_id
where coalesce(p.opt_out_sale_share, false) = false;
-- Many companies apply the opt-out to all customers, not only California residents,
-- because residency data is unreliable. Decide this with your privacy team.
```

**Failure modes.** Opt-out flags stored but not joined into every export; "hashed email" treated as non-personal although it is shared to enable matching; deletion requests not propagated to service providers.

**Validation.** Opt out a test consumer and confirm they disappear from every sale or share export at the next run.

## Data Tokenization

Tokenization replaces a sensitive value (card number, national ID, email) with a surrogate token that has no exploitable meaning. The mapping between token and original is kept in a separate, tightly controlled **token vault**, or derived with a key in *vaultless* schemes such as format-preserving encryption (for example NIST FF1).

**How it works.** At ingestion, a tokenization service receives the value and returns a token. Deterministic tokens (same input, same token) allow joins and counts across tables without revealing the value; random tokens are safer but break joins. Detokenization is a separate, audited privilege granted to very few identities.

**Example (illustrative):**

| Original email | Token stored in lakehouse |
|---|---|
| maria@example.com | `tok_em_7Q2XK9` |
| tuan@example.com | `tok_em_P4R1ZB` |

```sql
-- Analysts can count distinct customers and join on the token without seeing emails.
select count(distinct email_token) from analytics.fct_orders where order_date >= date '2026-11-01';
```

**Compared with encryption and masking.** Encrypted values can be decrypted by anyone with the key; tokens can be reversed only through the vault service. Masking typically produces values that cannot be reversed at all and are not meant to be joined.

**Failure modes.** The vault becoming a single point of failure or a high-value target; deterministic tokens enabling linkage across datasets that should stay separate (use different token domains per purpose); original values leaking into logs before tokenization.

**Validation.** Confirm raw values never appear in landing storage or logs; test that detokenization is denied for analyst roles and audited for approved roles.

**Lakehouse / Text2SQL fit.** Tokenised identifiers let the assistant answer "how many distinct customers" without the model ever seeing personal data.

## Data Anonymization

Data anonymization transforms data so individuals can no longer be identified by any means reasonably likely to be used, either directly or by linking with other data. Properly anonymised data falls outside GDPR; **pseudonymised** data (tokens, hashes, masked IDs) does not.

**Techniques.**

- **Generalisation:** replace precise values with ranges (age 34 -> 30-39; postcode -> region).
- **Suppression:** remove rare records or values that would single someone out.
- **Noise addition / perturbation:** alter values slightly while preserving aggregate patterns.
- **Aggregation:** publish only group-level statistics above a minimum group size.
- **k-anonymity:** every combination of quasi-identifiers appears for at least *k* records; extensions such as l-diversity and t-closeness also protect the sensitive attribute within each group.

**Example (illustrative k-anonymity check, k = 10):**

```sql
select age_band, region, gender, count(*) as group_size
from published.customer_profile_anon
group by age_band, region, gender
having count(*) < 10;     -- expect zero rows before release
```

**Failure modes.** Assuming that removing names anonymises data; releasing many overlapping anonymised tables that can be combined to re-identify; small groups in filtered dashboards (a filter for one rare combination shows one person).

**Validation.** Run k-anonymity checks on every release and attempt a linkage attack using a public auxiliary dataset in a controlled review.

**Lakehouse / Text2SQL fit.** Enforce a minimum group size in the semantic layer: the assistant should refuse or suppress results where any group falls below the threshold.

## Differential Privacy

Differential privacy (DP) is a mathematical guarantee that the output of an analysis changes very little whether or not any one individual's data is included. It is achieved by adding carefully calibrated random noise to results.

**How it works.** The privacy parameter **epsilon (ε)** bounds how much one person can influence the output; smaller ε means stronger privacy and more noise. For a count query, adding or removing one person changes the true answer by at most 1 (its *sensitivity*), so the Laplace mechanism adds noise drawn from Laplace(0, 1/ε). Each query spends part of a **privacy budget**; under basic composition, epsilons add up, so repeated queries must be limited.

**Example (illustrative Python, not production-grade):**

```python
import numpy as np

def dp_count(true_count: int, epsilon: float, rng=np.random.default_rng()) -> float:
    sensitivity = 1.0
    return true_count + rng.laplace(loc=0.0, scale=sensitivity / epsilon)

budget = 1.0
for eps in (0.25, 0.25, 0.5):      # three queries spend the whole budget
    budget -= eps
    print(round(dp_count(1240, eps)), "remaining budget:", budget)
```

Use vetted libraries (for example OpenDP or Google's differential privacy libraries) in practice; hand-rolled implementations often have floating-point and composition bugs.

**Failure modes.** Unlimited repeated queries averaging the noise away; ε chosen without justification; noisy results presented as exact; small groups where noise dominates the signal.

**Validation.** Track budget per dataset and consumer; test that queries are refused when the budget is exhausted; report noise scale alongside results.

**Lakehouse / Text2SQL fit.** DP fits published statistics and external data sharing more than internal operational reporting. If an assistant serves DP results, it must state that values are noisy and approximate.

## Practice

1. Scan your staging layer for PII in free-text and JSON columns; tag every finding in the catalog.
2. Write a privacy record (purpose, lawful basis, retention, subject key) for two datasets.
3. Execute a full erasure for one test subject in an Iceberg table, including compaction, snapshot expiry, and orphan file removal, and prove time travel no longer returns the rows.
4. Replace emails with deterministic tokens in one mart; verify distinct counts match the original.
5. Publish an aggregate table that passes a k = 10 check, and compute a DP count with ε = 0.5 for comparison.

### Completion criteria

- Every column containing personal data is tagged, has a purpose, and has a retention rule.
- An erasure request can be executed and evidenced across raw, mart, snapshots, and indexes within the target time.
- The assistant cannot return identifiers or groups below the minimum size, and its logs contain no raw PII.
- You can explain why tokenised data is still personal data while properly anonymised data is not.
