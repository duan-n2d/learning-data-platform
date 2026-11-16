---
title: "Access Control: RBAC, Row- and Column-Level Security"
description: Connect federated identities to roles, filter rows and protect columns where queries execute, and choose between static and dynamic data masking.
order: 22
tags: [security, access control, rbac, row-level security, column-level security, masking, identity]
---

# Access Control: RBAC, Row- and Column-Level Security

Access control answers three questions for every request: **who** is asking (identity), **what** they may touch (tables, rows, columns), and **where** the decision is enforced (catalog, engine, BI tool, storage). In a lakehouse the last question is the hard one, because the same Parquet files can be read by several engines and by anyone who holds storage credentials.

Assumptions for the examples: an identity provider (IdP) such as Microsoft Entra ID or Okta, an Iceberg REST catalog that can vend short-lived storage credentials, Trino and Spark as engines, and a Text2SQL assistant that must run queries *as the end user*, never as a shared superuser. See also [Cloud Storage and Access](cloud-storage-and-access.html).

## Federated Identity

Federated identity lets a user authenticate once with a trusted identity provider and use that identity across many systems, which trust the IdP's signed assertions instead of managing their own passwords.

**How it works.** Protocols such as SAML 2.0 and OpenID Connect (OIDC) carry signed tokens with the user's identifier and group memberships. SCIM provisions and deprovisions users and groups into downstream systems. Workload identity federation applies the same idea to machines: a CI job or Kubernetes pod presents an OIDC token and receives short-lived cloud credentials instead of a stored access key.

**Example (illustrative group-to-role mapping):**

```yaml
idp_groups_to_roles:
  grp-sales-analysts:      [analyst_sales]
  grp-finance-analysts:    [analyst_finance]
  grp-privacy-approved:    [pii_reader]
  grp-data-engineers:      [engineer_dev]          # production write only via pipeline identity
workload_identities:
  github-actions:repo:org/pipelines:ref:refs/heads/main: [pipeline_prod_writer]
```

**Failure modes.** Group claims not refreshed, so a user who changed teams keeps old access until the next login; local accounts created as a "temporary" workaround and never removed; service accounts with long-lived keys; the assistant authenticating with one service identity for every user.

**Validation.** Deprovision a test user in the IdP and verify access is removed in the catalog, engines, and BI within the agreed time. Inventory non-federated accounts and keys monthly.

**Lakehouse / Text2SQL fit.** The assistant should pass the user's token (or a token exchanged on the user's behalf) to the engine so every query is authorised and audited under the real person.

## Role-Based Access Control (RBAC)

Role-based access control grants permissions to **roles** and assigns roles to users or groups. Users never receive permissions directly, which makes access reviewable: "who can read `fct_orders`?" becomes "which roles have `SELECT`, and who holds them?"

**How it works.** Roles bundle privileges on securables (catalogs, schemas, tables, views, functions). Roles can inherit from other roles. In Apache Polaris, for example, *principal roles* are assigned to identities and are granted *catalog roles* that hold privileges on namespaces and tables; engines that obtain tables through the catalog get only what the caller's roles permit. Attribute-based access control (ABAC) extends RBAC with conditions on tags or user attributes, which scales better when there are many tables.

**Example (illustrative SQL grants, Trino/ANSI-style):**

```sql
create role analyst_sales;
create role pii_reader;

grant select on analytics.fct_orders   to role analyst_sales;
grant select on analytics.dim_customer to role analyst_sales;   -- masked columns, see below
grant select on analytics.dim_customer_pii to role pii_reader;

grant analyst_sales to user "maria@example.com";
-- Prefer granting to IdP groups where the engine supports it.
```

**Failure modes.** Role explosion (one role per person); a broad `analyst` role that accumulates every grant; privileges granted on the schema so new tables are exposed automatically, including sensitive ones; roles defined differently in each engine.

**Validation.** Export grants regularly and diff them against the approved access matrix; run allowed and denied query tests per role; run periodic access reviews with owners.

**Lakehouse / Text2SQL fit.** Give the assistant no privileges of its own beyond metadata reads. Its effective access is the intersection of the user's roles and the assistant's allow-list of certified tables.

## Row-Level Security

Row-level security (RLS) filters which rows a user can see in a table, based on who they are. A regional manager querying `fct_orders` sees only their region's rows, with the same SQL as everyone else.

**How it works.** A policy (row filter) is attached to a table and evaluated by the engine at query time, usually by comparing a column with an attribute of the current user or a mapping table. Implementations differ: PostgreSQL has `CREATE POLICY`; Snowflake has row access policies; Databricks Unity Catalog has row filter functions; Trino relies on access-control plugins (for example Apache Ranger or Open Policy Agent); some catalogs are adding policy definitions that engines fetch.

**Example (illustrative, PostgreSQL — runnable locally):**

```sql
create table sales_orders (order_id bigint, region text, net_amount numeric);
create table user_regions (username text, region text);

alter table sales_orders enable row level security;

create policy region_filter on sales_orders
  for select
  using (region in (select region from user_regions where username = current_user));
```

```sql
-- Test as two users: each must see only their regions; a user with no mapping sees zero rows.
set role maria;  select distinct region from sales_orders;   -- expect: EU
set role tuan;   select distinct region from sales_orders;   -- expect: APAC
```

**Where it is enforced, and how it is bypassed.** RLS is only as strong as the path to the data. If a catalog vends storage credentials so an engine can read Parquet files directly, any engine or script holding those credentials can read every row; the filter exists only in engines that honour the policy. Mitigations: vend credentials only to trusted engines that enforce the policy, scope credentials to the minimum prefixes, deny direct bucket access to humans, or publish pre-filtered tables/views for engines that cannot enforce filters.

**Failure modes.** Testing as the table owner or a superuser, who bypass PostgreSQL RLS unless `force row level security` is set; mapping table gaps causing users to see nothing (or, with a wrongly written policy, everything); filters on views that users can bypass by querying the base table; aggregates or caches computed with a privileged identity and shared with everyone; performance degradation from complex policy subqueries.

**Validation.** Maintain a test matrix of users × expected row counts per region, including an unmapped user; run it in every engine that can read the table; try direct storage reads with the credentials a user can obtain.

**Lakehouse / Text2SQL fit.** Because the assistant runs as the user, RLS keeps a question like "total sales" automatically scoped. The answer should say it is scoped ("for regions you can access: EU") so a partial total is not mistaken for the company total.

## Column-Level Security

Column-level security (CLS) controls which columns a user can read. A support analyst can see `customer_id` and `country` but not `email` or `date_of_birth`.

**How it works.** Two styles exist. *Column grants* deny access to the column entirely, so `select *` fails or omits it. *Column policies* (dynamic masking) let the query run but return a masked value for users without permission, which avoids breaking queries and dashboards. Tag-based policies attach a masking rule to every column tagged, for example, `pii.email`, which keeps policy central as tables multiply.

**Example (illustrative, PostgreSQL column privileges):**

```sql
revoke select on dim_customer from analyst_sales;
grant select (customer_id, country, signup_date, segment) on dim_customer to analyst_sales;
-- select email from dim_customer;  -> permission denied for analyst_sales
```

**Failure modes.** A view exposing the column without the policy; derived columns (such as `email_domain` or a hash of the email) that leak the protected value; exports and extracts created by a privileged job; the column protected in the warehouse but present in a BI extract or vector index.

**Validation.** For every column tagged sensitive, verify a policy or grant exists; run tests as a non-privileged role; scan derived tables and indexes for copies of protected values.

**Lakehouse / Text2SQL fit.** Exclude protected columns from the schema context the assistant sees unless the user is authorised. Otherwise the model may propose queries that fail, or worse, name sensitive fields in its explanation.

## Data Masking

Data masking replaces sensitive values with realistic but non-sensitive substitutes so people and systems can work with data without seeing the real values.

**Static vs dynamic.**

| Aspect | Static masking | Dynamic masking |
|---|---|---|
| When applied | Once, when producing a copy (for example a dev dataset) | At query time, per user or role |
| Stored data | Masked copy; original elsewhere | Original stored; masking in the engine |
| Good for | Non-production environments, sharing extracts | Production analytics with mixed audiences |
| Risk | Copy drifts; masking may be reversible if done poorly | Bypass via unprotected engines or storage paths |

Common techniques: redaction (`****`), partial reveal (last four digits), format-preserving substitution, hashing (consistent but linkable), shuffling within a column, and date shifting. Masking is not [anonymization](privacy-and-pii-protection.html#data-anonymization): masked data can often still identify people when combined with other columns.

**Example (illustrative, Snowflake-style dynamic masking policy):**

```sql
create masking policy email_mask as (val string) returns string ->
  case
    when is_role_in_session('PII_READER') then val
    else regexp_replace(val, '^[^@]+', '***')     -- ***@example.com
  end;

alter table analytics.dim_customer modify column email set masking policy email_mask;
```

**Failure modes.** Unsalted hashes of low-entropy values (phone numbers) that can be reversed by brute force; masking that breaks joins because two tables mask differently; masked dev copies refreshed from production without re-running the masking; logs and error messages containing unmasked values.

**Validation.** Query as unprivileged and privileged roles and compare; attempt to reverse a sample of hashes with a dictionary; scan non-production copies for real values with a PII detector.

**Lakehouse / Text2SQL fit.** Masked values should never be sent to an LLM as if they were real: if the assistant shows sample rows, use masked views and label them.

## Practice

1. Write an access matrix for three IdP groups and four tables, then implement it as roles and grants.
2. In PostgreSQL, implement the RLS example with two users and an unmapped user; capture the test results.
3. Add a column policy or masking policy for `email` and `date_of_birth`; prove a non-privileged role gets masked or denied results.
4. List every path to the underlying files (engines, notebooks, vended credentials, BI extracts) and mark where RLS and CLS are enforced.
5. Configure the assistant to run queries with the user's identity and show the scope of each answer.

### Completion criteria

- Allowed and denied tests exist for every role and run automatically.
- No human identity can read lakehouse files directly in production, or the exception is documented with a compensating control.
- Deprovisioning a user in the IdP removes access everywhere within the agreed time.
- The assistant's queries appear in audit logs under the end user's identity, and scoped answers say so.
