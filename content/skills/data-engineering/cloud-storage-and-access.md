---
title: Cloud Storage and Access Basics
description: Choose durable data storage and apply least-privilege access patterns.
order: 4
tags: [cloud, object storage, iam, security]
---

# Cloud Storage and Access Basics

Cloud data systems combine object storage, compute, databases, and identity controls. The provider details differ, but the design questions are similar: what is stored, how long it is retained, who can access it, and how it is recovered.

## Storage layers

Object storage is well suited to durable raw files and immutable snapshots. A warehouse or lakehouse provides structures optimized for analytical reads and transformations. Keep raw source artifacts separate from curated outputs so a transformation bug can be corrected without losing the source.

Choose formats and partitioning based on access patterns. Columnar formats can reduce scan cost for analytical workloads. Partition by fields that are commonly filtered and have useful cardinality; excessive tiny partitions can increase overhead. Record schema and ingestion metadata so files remain interpretable over time.

## Identity and least privilege

Use distinct identities for ingestion, transformation, interactive analytics, and application query execution. Grant only the required bucket paths, schemas, and operations. A Text2SQL service should not reuse an administrator or developer credential. Review inherited permissions and service-account impersonation paths, not only direct grants.

Keep secrets out of source control, notebooks, prompts, and logs. Prefer a managed secret store or workload identity. Rotate credentials and audit access according to the sensitivity and retention policy of the data.

## Durability and recovery

Define retention, lifecycle transitions, encryption requirements, backup behavior, and recovery objectives. Test restore procedures; a configured backup is not proof that data can be recovered. For important source data, preserve immutable or versioned copies and verify that deletion policies cannot remove the only recovery copy.

## Cost and operations

Track storage growth, bytes scanned, compute time, egress, and idle resources. Use lifecycle policies for obsolete temporary data, but do not delete data required for reproducibility or compliance. Cost controls should have an owner and thresholds tied to expected workloads.

## Practice

Design storage for a daily event pipeline with raw, staged, and curated data. List the identities and exact actions each needs, identify a sensitive field, and describe how to restore a mistakenly overwritten partition without granting every user broad bucket access.