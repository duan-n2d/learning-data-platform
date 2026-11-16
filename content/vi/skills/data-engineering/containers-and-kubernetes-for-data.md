---
title: Container và Kubernetes cho dữ liệu
description: Đóng gói job dữ liệu bằng Docker để chạy tái lập được, và dùng Kubernetes để lập lịch, cô lập, mở rộng pipeline, Spark và dịch vụ AI.
order: 45
tags: [containerization, Docker, Kubernetes, Spark on Kubernetes, KubernetesPodOperator, tái lập]
---

# Container và Kubernetes cho dữ liệu

"Chạy được trên laptop của tôi" cũng là vấn đề của dữ liệu: một lượt dbt phụ thuộc vào phiên bản adapter cụ thể, một job Python cần thư viện hệ thống, một dịch vụ trợ lý phải dùng cùng bộ kiểm định SQL ở môi trường test và production. Container biến chính môi trường chạy thành một artifact có phiên bản. Kubernetes sau đó chạy nhiều container như vậy một cách tin cậy trên cả cluster.

## Containerization (Docker)

**Là gì.** Containerization (container hóa) đóng gói ứng dụng cùng các phụ thuộc — runtime ngôn ngữ, thư viện, gói hệ thống, cấu hình mặc định — thành một **image** chạy giống nhau trên mọi máy chủ tương thích. **Container** là một instance đang chạy của image. Docker phổ biến hóa bộ công cụ; image tuân theo chuẩn mở OCI, nên các runtime khác (containerd, Podman) cũng chạy được.

**Cách hoạt động.**

- **Dockerfile** liệt kê các bước build; mỗi bước tạo một **layer** được cache.
- Image được đẩy lên **registry** (Docker Hub, GitHub Container Registry, registry trên cloud) và được định danh bằng tag (`1.4.0`) và, một cách bất biến, bằng digest (`sha256:...`).
- Lúc chạy, kernel của máy chủ cô lập tiến trình, hệ thống file và mạng của container bằng namespace, và giới hạn tài nguyên bằng cgroup.

**Container so với máy ảo.**

| | Container | Máy ảo |
|---|---|---|
| Ranh giới cô lập | Dùng chung kernel của máy chủ | Có hệ điều hành và kernel khách riêng trên hypervisor |
| Khởi động | Vài giây hoặc nhanh hơn | Thường vài chục giây trở lên |
| Kích thước | Từ vài megabyte đến vài gigabyte | Nhiều gigabyte |
| Mức cô lập bảo mật | Mặc định yếu hơn; cần gia cố cẩn thận | Mạnh hơn |
| Dùng điển hình cho dữ liệu | Task pipeline, lượt dbt, API, notebook | Cơ sở dữ liệu, ứng dụng cũ, cô lập tenant chặt chẽ |

**Ví dụ cụ thể (Dockerfile cho job dbt + kiểm định, minh họa).**

```dockerfile
FROM python:3.12-slim

# Chỉ cài gói hệ thống khi cần; ghim phiên bản trong lock file, không phải ở đây
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

**Kiểu lỗi.**

- *Không ghim image gốc và phụ thuộc*: `FROM python:latest` và `pip install` không ghim phiên bản khiến hai lần build của "cùng" image khác nhau.
- *Secret nằm trong layer*: file `.env` được copy vào image vẫn còn trong lịch sử dù bị xóa ở bước sau.
- *Chạy bằng root*: tăng mức thiệt hại khi bị xâm nhập.
- *Image cồng kềnh*: kéo image chậm mỗi lần task khởi động.
- *Dữ liệu nằm trong container*: mọi thứ ghi vào hệ thống file của container biến mất khi nó kết thúc; hãy ghi vào object storage hoặc volume được mount.
- *Giả định về múi giờ và locale*: image slim mặc định dùng UTC và locale tối thiểu — tốt cho pipeline, nhưng hãy ghi rõ.

**Kiểm định.** Build trong CI và quét image tìm lỗ hổng đã biết; triển khai theo digest, không theo tag có thể thay đổi; chạy test của container bên trong chính image đó; kiểm tra `docker history` không chứa secret; tiêm credential lúc chạy từ kho secret.

**Liên hệ với trợ lý phân tích có quản trị.** Đóng gói bộ kiểm định SQL, kiểm tra chính sách và trình chạy đánh giá của trợ lý vào cùng image dùng ở CI và production. Khi một lượt đánh giá đạt, bạn biết chính xác digest image đã đạt, và có thể triển khai đúng digest đó — chứ không phải một bản build lại gần giống.

## Kubernetes

**Là gì.** Kubernetes (thường viết "K8s") là nền tảng mã nguồn mở lập lịch và quản lý container trên một cluster nhiều máy. Bạn khai báo trạng thái mong muốn — "chạy ba bản sao của API này", "chạy batch job này đến khi xong" — và các controller của Kubernetes liên tục làm cho thực tế khớp với nó, khởi động lại container lỗi và lập lịch lại công việc khi node biến mất. Các phiên bản managed gồm Amazon EKS, Google GKE và Azure AKS.

**Cách hoạt động.** Các đối tượng cốt lõi mà đội dữ liệu dùng:

| Đối tượng | Mục đích trong nền tảng dữ liệu |
|---|---|
| Pod | Một hoặc nhiều container được lập lịch cùng nhau; đơn vị chạy một task |
| Deployment | Dịch vụ chạy lâu dài: API trợ lý, Superset, coordinator của Trino |
| Job / CronJob | Công việc batch chạy đến khi xong, có thể theo lịch cron |
| Namespace | Tách nhóm hoặc môi trường; gắn quota và chính sách |
| ConfigMap / Secret | Cấu hình và credential được tiêm vào lúc chạy |
| ServiceAccount + RBAC | Workload được làm gì trong cluster; có thể ánh xạ tới role IAM trên cloud |
| Requests / limits | CPU và bộ nhớ được giữ chỗ và giới hạn cho mỗi container |

Các mẫu dùng phổ biến cho dữ liệu:

- **Cô lập task của orchestrator**: `KubernetesPodOperator` hoặc `KubernetesExecutor` của Airflow, run launcher và work pool Kubernetes của Dagster và Prefect — mỗi task chạy trong pod riêng với image và tài nguyên riêng.
- **Spark on Kubernetes**: Spark có thể dùng Kubernetes làm cluster manager, khởi chạy pod driver và executor; các operator như Kubeflow Spark Operator quản lý ứng dụng Spark theo kiểu declarative.
- **Dịch vụ mô hình và AI**: inference server và LLM gateway chạy dưới dạng Deployment có autoscaling.
- **Dịch vụ nền tảng**: query engine, công cụ BI và catalog, thường được cài bằng Helm chart.

**Ví dụ cụ thể (task Airflow chạy trong pod cô lập, minh họa).**

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

build_marts = KubernetesPodOperator(
    task_id="build_marts",
    name="build-marts",
    namespace="data-pipelines",
    image="ghcr.io/acme/dbt-runner@sha256:3f1c...",       # ghim theo digest
    arguments=["build", "--select", "marts", "--vars", "{day: '{{ ds }}'}"],
    service_account_name="dbt-runner",                    # ánh xạ tới role cloud đặc quyền tối thiểu
    container_resources=k8s.V1ResourceRequirements(
        requests={"cpu": "500m", "memory": "1Gi"},
        limits={"memory": "2Gi"},
    ),
    get_logs=True,
    on_finish_action="delete_pod",
    retries=2,
)
```

**Ví dụ cụ thể (CronJob cho một tác vụ bảo trì độc lập, minh họa).**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: iceberg-compaction
  namespace: data-pipelines
spec:
  schedule: "30 3 * * *"
  timeZone: "Etc/UTC"
  concurrencyPolicy: Forbid          # không cho các lượt chạy chồng nhau
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

Lưu ý `concurrencyPolicy: Forbid` và `activeDeadlineSeconds` giải quyết đúng các vấn đề chồng lượt và chạy mất kiểm soát mà cron thuần để bạn tự lo (xem [So sánh cron và các orchestrator](orchestrators-compared.html)).

**Kiểu lỗi.**

- *OOMKilled*: giới hạn bộ nhớ quá thấp khi khối lượng dữ liệu tăng đột biến; pod bị kill và retry, có thể lặp lại nhiều lần.
- *Pod ở trạng thái Pending*: requests vượt quá dung lượng trống; job nằm chờ không được lập lịch trong khi SLA trôi qua.
- *Eviction và preemption*: node spot hoặc preemptible biến mất giữa chừng; task không idempotent để lại dữ liệu ghi dở.
- *Quyền quá rộng*: service account của pipeline đọc được mọi secret trong cluster.
- *Quá tải vận hành*: một nhóm nhỏ tự vận hành cluster chỉ cho ba job.

**Kiểm định.** Theo dõi sự kiện pod và lý do kết thúc (`kubectl describe pod`, `kubectl get events`); cảnh báo khi có OOMKilled và Pending kéo dài; đặt requests dựa trên mức dùng quan sát được; rà soát RBAC và network policy; diễn tập drain node để xác nhận task retry một cách idempotent.

**Khi nào không nên dùng.** Nếu pipeline chỉ là vài job theo lịch, một orchestrator managed, container serverless hoặc một VM chạy Docker thường đơn giản hơn. Kubernetes đáng giá khi bạn có nhiều workload không đồng nhất, cần cô lập và kiểm soát tài nguyên chặt chẽ, hoặc đã có đội platform vận hành.

**Liên hệ với trợ lý phân tích có quản trị.** Chạy API trợ lý trong namespace riêng, với service account chỉ tới được role cơ sở dữ liệu chỉ đọc và dịch vụ semantic layer, network policy chặn các đường ra khác, resource limit để giới hạn chi phí, và số bản sao đủ giữ dịch vụ sẵn sàng. Job đánh giá có thể chạy dưới dạng Kubernetes Job dùng cùng digest image với dịch vụ.

## Bài tập

1. Viết Dockerfile cho dbt project (hoặc job ingestion) của Dự án 1, chạy bằng người dùng không phải root và ghim phụ thuộc.
2. Build hai lần từ cache sạch và xác nhận danh sách gói được cài giống hệt nhau; ghi lại digest của image.
3. Chạy image cục bộ với warehouse development, tiêm credential lúc chạy.
4. Dùng cluster cục bộ (kind, minikube hoặc k3d), chạy nó dưới dạng Kubernetes Job có requests và limits, rồi hạ giới hạn bộ nhớ cho đến khi bị OOMKilled và quan sát lỗi.
5. Chuyển một tác vụ bảo trì thành CronJob với `concurrencyPolicy: Forbid` và deadline.

**Tiêu chí hoàn thành.**

- Một Dockerfile, một digest image và báo cáo quét lỗ hổng với các phát hiện đã được phân loại.
- Bằng chứng không có secret nào trong lịch sử image.
- Log Job cho một lần thành công và một lần lỗi OOMKilled, kèm giải thích và thiết lập tài nguyên đã sửa.
- Ghi chú ngắn quyết định Kubernetes có đáng dùng cho capstone của bạn không, kèm phương án đơn giản hơn đã so sánh.
