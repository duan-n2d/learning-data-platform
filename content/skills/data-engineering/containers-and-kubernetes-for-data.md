---
title: Containers and Kubernetes for Data
description: Package data jobs with Docker for reproducible runs, and use Kubernetes to schedule, isolate, and scale pipelines, Spark, and AI services.
order: 45
tags: [containerization, Docker, Kubernetes, Spark on Kubernetes, KubernetesPodOperator, reproducibility]
---

# Containers and Kubernetes for Data

"It works on my laptop" is a data problem too: a dbt run that depends on a specific adapter version, a Python job that needs a system library, an assistant service that must use the same SQL validator in tests and production. Containers make the runtime itself a versioned artifact. Kubernetes then runs many such containers reliably across a cluster.

## Containerization (Docker)

**What it is.** Containerization packages an application together with its dependencies — language runtime, libraries, system packages, configuration defaults — into an **image** that runs the same way on any compatible host. A **container** is a running instance of an image. Docker popularized the tooling; images follow the open OCI standard, so other runtimes (containerd, Podman) can run them too.

**How it works.**

- A **Dockerfile** lists build steps; each step creates a cached **layer**.
- Images are pushed to a **registry** (Docker Hub, GitHub Container Registry, a cloud registry) and identified by tag (`1.4.0`) and, immutably, by digest (`sha256:...`).
- At run time, the host kernel isolates the container's processes, filesystem, and network using namespaces and limits its resources using cgroups.

**Containers vs virtual machines.**

| | Container | Virtual machine |
|---|---|---|
| Isolation boundary | Shares the host kernel | Own guest OS and kernel on a hypervisor |
| Startup | Seconds or less | Typically tens of seconds or more |
| Size | Megabytes to a few gigabytes | Gigabytes |
| Security isolation | Weaker by default; harden carefully | Stronger |
| Typical data use | Pipeline tasks, dbt runs, APIs, notebooks | Databases, legacy apps, strong tenant isolation |

**Concrete example (illustrative Dockerfile for a dbt + validation job).**

```dockerfile
FROM python:3.12-slim

# System packages only if needed; pin versions in the lock file, not here
RUN useradd --create-home --uid 10001 runner
WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY --chown=runner:runner models/ models/
COPY --chown=runner:runner semantic/ semantic/
COPY --chown=runner:runner dbt_project.yml profiles.yml ./
COPY --chown=runner:runner scripts/ scripts/

USER runner
ENTRYPOINT ["dbt"]
CMD ["build", "--target", "prod"]
```

```bash
docker build -t ghcr.io/acme/dbt-runner:1.4.0 .
docker run --rm --env-file .env.ci ghcr.io/acme/dbt-runner:1.4.0 build --select marts
```

**Failure modes.**

- *Unpinned bases and dependencies*: `FROM python:latest` and unpinned `pip install` make two builds of the "same" image differ.
- *Secrets baked into layers*: an `.env` file copied into the image stays in its history even if deleted in a later step.
- *Running as root*: increases the impact of a compromise.
- *Bloated images*: slow pulls on every task start.
- *Data inside the container*: anything written to the container filesystem disappears when it exits; write to object storage or a mounted volume.
- *Timezone and locale assumptions*: slim images default to UTC and minimal locales — good for pipelines, but make it explicit.

**Validation.** Build in CI and scan images for known vulnerabilities; deploy by digest, not by mutable tag; run the container's tests inside the image itself; check that `docker history` shows no secrets; inject credentials at run time from a secret store.

**Connection to the governed analytics assistant.** Package the assistant's SQL validator, policy checks, and evaluation runner into the same image used in CI and production. When an evaluation passes, you know the exact image digest that passed, and you can deploy that digest — not a rebuilt approximation.

## Kubernetes

**What it is.** Kubernetes (often "K8s") is an open-source platform that schedules and manages containers across a cluster of machines. You declare the desired state — "run three replicas of this API", "run this batch job to completion" — and Kubernetes controllers continuously work to make reality match it, restarting failed containers and rescheduling work when nodes disappear. Managed versions include Amazon EKS, Google GKE, and Azure AKS.

**How it works.** Core objects that data teams use:

| Object | Purpose in a data platform |
|---|---|
| Pod | One or more containers scheduled together; the unit a task runs in |
| Deployment | Long-running services: the assistant API, Superset, Trino coordinators |
| Job / CronJob | Run-to-completion batch work, optionally on a cron schedule |
| Namespace | Separate teams or environments; attach quotas and policies |
| ConfigMap / Secret | Configuration and credentials injected at run time |
| ServiceAccount + RBAC | What a workload may do in the cluster; can map to cloud IAM roles |
| Requests / limits | CPU and memory reserved and capped per container |

Common data patterns:

- **Orchestrator task isolation**: Airflow's `KubernetesPodOperator` or `KubernetesExecutor`, Dagster's and Prefect's Kubernetes run launchers and work pools — each task runs in its own pod with its own image and resources.
- **Spark on Kubernetes**: Spark can use Kubernetes as its cluster manager, launching driver and executor pods; operators such as the Kubeflow Spark Operator manage Spark applications declaratively.
- **Model and AI services**: inference servers and LLM gateways run as Deployments with autoscaling.
- **Platform services**: query engines, BI tools, and catalogs, often installed with Helm charts.

**Concrete example (illustrative Airflow task running in an isolated pod).**

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

build_marts = KubernetesPodOperator(
    task_id="build_marts",
    name="build-marts",
    namespace="data-pipelines",
    image="ghcr.io/acme/dbt-runner@sha256:3f1c...",       # pinned by digest
    arguments=["build", "--select", "marts", "--vars", "{day: '{{ ds }}'}"],
    service_account_name="dbt-runner",                    # mapped to a least-privilege cloud role
    container_resources=k8s.V1ResourceRequirements(
        requests={"cpu": "500m", "memory": "1Gi"},
        limits={"memory": "2Gi"},
    ),
    get_logs=True,
    on_finish_action="delete_pod",
    retries=2,
)
```

**Concrete example (illustrative CronJob for a self-contained maintenance task).**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: iceberg-compaction
  namespace: data-pipelines
spec:
  schedule: "30 3 * * *"
  timeZone: "Etc/UTC"
  concurrencyPolicy: Forbid          # no overlapping runs
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600
      template:
        spec:
          restartPolicy: Never
          serviceAccountName: compaction
          containers:
            - name: compact
              image: ghcr.io/acme/lake-maintenance@sha256:9ab2...
              args: ["compact", "--table", "analytics.fct_orders"]
              resources:
                requests: { cpu: "1", memory: "2Gi" }
                limits: { memory: "4Gi" }
```

Note that `concurrencyPolicy: Forbid` and `activeDeadlineSeconds` solve exactly the overlap and runaway problems plain cron leaves to you (see [Cron and orchestrators compared](orchestrators-compared.html)).

**Failure modes.**

- *OOMKilled*: memory limit too low for a data volume spike; the pod is killed and retried, possibly repeatedly.
- *Pending pods*: requests exceed free capacity; jobs sit unscheduled while their SLA passes.
- *Eviction and preemption*: spot or preemptible nodes vanish mid-task; non-idempotent tasks leave partial writes.
- *Over-broad permissions*: a pipeline service account that can read every secret in the cluster.
- *Operational overload*: a small team running a self-managed cluster for three jobs.

**Validation.** Watch pod events and exit reasons (`kubectl describe pod`, `kubectl get events`); alert on OOMKilled and long Pending durations; size requests from observed usage; review RBAC and network policies; run a node-drain drill to confirm tasks retry idempotently.

**When not to use it.** If your pipelines are a few scheduled jobs, a managed orchestrator, serverless containers, or a single VM with Docker is often simpler. Kubernetes pays off when you have many heterogeneous workloads, need strict isolation and resource control, or already operate a platform team.

**Connection to the governed analytics assistant.** Run the assistant API in its own namespace, with a service account that can only reach the read-only database role and the semantic-layer service, network policies that block other egress, resource limits that cap cost, and replica counts that keep it available. Evaluation jobs can run as Kubernetes Jobs using the same image digest as the service.

## Practice

1. Write a Dockerfile for your Project 1 dbt project (or ingestion job) that runs as a non-root user and pins dependencies.
2. Build it twice from a clean cache and confirm the installed package list is identical; record the image digest.
3. Run the image locally against your development warehouse with credentials injected at run time.
4. Using a local cluster (kind, minikube, or k3d), run it as a Kubernetes Job with requests and limits, then lower the memory limit until it is OOMKilled and observe the failure.
5. Convert one maintenance task to a CronJob with `concurrencyPolicy: Forbid` and a deadline.

**Completion criteria.**

- A Dockerfile, an image digest, and a vulnerability scan report with findings triaged.
- Evidence that no secret appears in the image history.
- Job logs for one success and one OOMKilled failure, with your explanation and the corrected resource settings.
- A short note deciding whether Kubernetes is justified for your capstone, with the simpler alternative you compared.
