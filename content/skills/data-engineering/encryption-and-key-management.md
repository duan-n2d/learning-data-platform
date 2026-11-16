---
title: Encryption and Key Management
description: Protect lakehouse data at rest and in transit, understand KMS envelope encryption and key rotation, and know when homomorphic encryption is worth its cost.
order: 24
tags: [security, encryption, tls, kms, key management, homomorphic encryption, parquet]
---

# Encryption and Key Management

Encryption turns readable data into ciphertext that only holders of the right key can read. It limits damage when storage media, backups, or network traffic are exposed, but it does **not** decide who should see data once it is decrypted for a legitimate query; that is the job of [access control](access-control-rbac-rls-cls.html). Most real failures involve keys, certificates, and permissions rather than broken algorithms.

Assumptions for the examples: object storage (Amazon S3 or equivalent), an Iceberg REST catalog, Spark and Trino engines, a cloud key management service, and BI and Text2SQL clients connecting over the network.

## Encryption at Rest

Encryption at rest protects stored data (object storage, disks, database files, backups, snapshots) by keeping it as ciphertext on the medium. Modern systems typically use AES-256, often in GCM mode, which also detects tampering.

**Where it can be applied.**

| Level | Example | Who holds the key | Protects against |
|---|---|---|---|
| Disk / volume | Cloud block storage encryption | Provider or KMS | Stolen or discarded media |
| Object storage, server-side | SSE-S3, SSE-KMS | Provider-managed key or your KMS key | Media exposure; with KMS keys, also access via a separate key policy |
| Object storage, customer-provided key | SSE-C | You supply the key per request | Provider-side key custody concerns |
| Client-side / application | Encrypt before upload; Parquet modular encryption | Your application and KMS | Storage administrators and anyone with only bucket access |

Parquet *modular encryption* can encrypt the footer and individual columns with different keys, so a reader without the key for `email` can still read other columns. Iceberg has been adding table-level encryption integration with KMS; check the support level in your engine versions before relying on it.

**Example (illustrative bucket policy requiring KMS server-side encryption):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyUnencryptedUploads",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::lake-prod/*",
    "Condition": {
      "StringNotEquals": { "s3:x-amz-server-side-encryption": "aws:kms" }
    }
  }]
}
```

S3 now encrypts new objects by default with SSE-S3; a policy like this enforces the stronger choice of a customer-managed KMS key, whose own key policy adds a second gate.

**Failure modes.** Believing "encrypted at rest" stops a user with read permission (the storage service decrypts for any authorised caller); temporary spill files, local caches, and notebook exports left unencrypted; backups encrypted with a key that is deleted, making them unrecoverable.

**Validation.** Inventory buckets and volumes with their encryption setting; list objects missing the expected key; restore a backup in a test environment to prove the key is still usable.

**Lakehouse / Text2SQL fit.** Column-level client-side encryption is useful for the most sensitive fields that the assistant should never read; ensure the assistant's execution identity is not granted decrypt on those keys.

## Encryption in Transit

Encryption in transit protects data as it moves across a network, almost always using TLS (1.2 or 1.3). TLS provides confidentiality, integrity, and, through certificate validation, assurance that the client is talking to the real server. Mutual TLS (mTLS) also authenticates the client with a certificate.

**Where TLS applies in a lakehouse.**

- Clients (BI tools, notebooks, the assistant) to query engines over JDBC/ODBC/HTTPS.
- Engines to the catalog (Iceberg REST over HTTPS) and to object storage (HTTPS endpoints).
- Inside engines: coordinator to worker and worker to worker traffic (for example Trino internal communication and Spark RPC/shuffle encryption settings), which is often unencrypted by default.
- Pipelines to sources (database connections, SFTP, APIs) and to LLM or embedding providers.

**Example (illustrative configuration snippets):**

```json
{
  "Sid": "DenyInsecureTransport",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::lake-prod", "arn:aws:s3:::lake-prod/*"],
  "Condition": { "Bool": { "aws:SecureTransport": "false" } }
}
```

```text
# PostgreSQL source connection: encrypt AND verify the server certificate and hostname.
postgresql://ingest@orders-db.internal:5432/orders?sslmode=verify-full&sslrootcert=/etc/ssl/internal-ca.pem
```

**Failure modes.** TLS enabled but certificate verification disabled (`sslmode=require`, `verify=False`, "trust all certificates"), which allows man-in-the-middle attacks; expired certificates causing outages and rushed insecure workarounds; internal cluster traffic left in clear text on the assumption that the network is trusted (see [Zero Trust Architecture](security-posture-and-threat-modeling.html#zero-trust-architecture)).

**Validation.** Scan endpoints for TLS versions and certificate validity; grep configs for disabled verification; alert on certificates expiring within 30 days; attempt plain-HTTP access and confirm it is denied.

**Lakehouse / Text2SQL fit.** The assistant sends questions, schema context, and sometimes result rows to a model endpoint; that hop must be TLS-verified and covered by the provider agreement, just like engine connections.

## Key Management Service (KMS)

A key management service creates, stores, and controls cryptographic keys, and performs cryptographic operations so that master keys never leave it, typically backed by hardware security modules (HSMs). Cloud examples include AWS KMS, Azure Key Vault, and Google Cloud KMS; HashiCorp Vault is a common self-managed option.

**How envelope encryption works.**

1. A **key encryption key (KEK)**, also called the KMS key or master key, stays inside the KMS.
2. To encrypt an object or file, the service asks KMS for a new **data encryption key (DEK)**. KMS returns the DEK in plaintext and also encrypted under the KEK.
3. The data is encrypted locally with the plaintext DEK, which is then discarded; the encrypted DEK is stored alongside the data (for example in object metadata or the Parquet footer).
4. To decrypt, the reader sends the encrypted DEK to KMS, which checks the caller's permission, decrypts it, and returns the DEK.

This keeps bulk encryption fast and local while every decryption remains authorised and logged by the KMS.

**Example (illustrative key policy fragment granting decrypt only to the pipeline and engine roles):**

```json
{
  "Sid": "AllowLakehouseUse",
  "Effect": "Allow",
  "Principal": { "AWS": [
    "arn:aws:iam::111122223333:role/pipeline-prod-writer",
    "arn:aws:iam::111122223333:role/trino-prod-workers"
  ]},
  "Action": ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*"
}
```

**Rotation and crypto-shredding.** Automatic rotation creates new key material for the KEK while keeping old versions available to decrypt existing data. Deliberately deleting a key that encrypts one subject's or one tenant's data makes that data unreadable (crypto-shredding), which can support deletion requirements, but only if keys are scoped that narrowly and no plaintext copies exist elsewhere.

**Failure modes.** Key policies granting `kms:*` to broad roles; scheduled key deletion by mistake (use deletion waiting periods and alerts); one key for every environment, so a dev compromise exposes prod; KMS request quotas throttling large jobs; no monitoring of decrypt calls.

**Validation.** Review key policies against the access matrix; alert on key disable or deletion events; test decrypt is denied for an unauthorised role; review KMS audit logs for unusual decrypt volume.

**Lakehouse / Text2SQL fit.** Separate keys per data domain or sensitivity level let you grant the assistant's execution path decrypt access only to the domains it serves.

## Homomorphic Encryption

Homomorphic encryption (HE) allows computation on encrypted data: a party without the key can add or multiply ciphertexts, and the decrypted result equals the result of the same operations on the plaintexts.

**Kinds of schemes.**

- **Partially homomorphic:** supports one operation without limit, for example Paillier (addition) or unpadded RSA (multiplication).
- **Somewhat / levelled homomorphic:** supports both operations up to a bounded depth.
- **Fully homomorphic (FHE):** supports arbitrary computation, first shown by Craig Gentry in 2009; modern schemes include BFV, BGV (exact integer arithmetic), and CKKS (approximate arithmetic on real numbers). Libraries include Microsoft SEAL and OpenFHE.

**Example (illustrative additive aggregation with the Python `phe` Paillier library):**

```python
from phe import paillier

public_key, private_key = paillier.generate_paillier_keypair()
# Each branch encrypts its revenue before sending it to a shared aggregator.
encrypted = [public_key.encrypt(x) for x in (120_500, 98_200, 143_900)]
encrypted_total = sum(encrypted[1:], encrypted[0])   # aggregator adds ciphertexts, sees no values
print(private_key.decrypt(encrypted_total))          # 362600, only the key holder can read it
```

**Cost and fit.** FHE operations are many orders of magnitude slower than plaintext operations, ciphertexts are much larger, and only certain computations are practical. In analytics it is a niche tool for specific cross-party aggregates or private inference, not a way to run a general SQL warehouse on encrypted data. Alternatives to evaluate first include trusted execution environments (confidential computing), secure multi-party computation, clean rooms, and differential privacy.

**Failure modes.** Leaking information through which queries are run or result sizes; parameter choices that are insecure or that overflow; assuming HE also authenticates who submitted data.

**Validation.** Use reviewed libraries with recommended parameters, benchmark on realistic data volumes, and have the design reviewed by someone with applied cryptography experience.

**Lakehouse / Text2SQL fit.** Generally not on the main path. An assistant over an HE workflow could only invoke pre-defined encrypted computations, not generate arbitrary SQL.

## Practice

1. Inventory your lab storage and record the encryption at rest mode and key for each bucket or volume.
2. Add a deny-insecure-transport policy and confirm an HTTP request fails while HTTPS succeeds.
3. Change one source connection from `sslmode=require` to `verify-full` and document the CA bundle.
4. Draw the envelope encryption flow for one Parquet file and identify where the encrypted DEK is stored.
5. Run the Paillier example and measure how long 10,000 encrypted additions take compared with plaintext.

### Completion criteria

- Every storage location has a documented encryption mode and key owner, and unencrypted uploads are denied.
- No client, engine, or pipeline connection disables certificate verification.
- KMS key policies match the access matrix, and decrypt calls are logged and reviewed.
- You can explain when homomorphic encryption is justified and which simpler alternatives you would try first.
