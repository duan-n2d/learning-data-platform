---
title: DataOps, CI/CD và hạ tầng dưới dạng mã
description: Áp dụng version control, kiểm thử tự động, continuous deployment, phân nhánh dữ liệu và Terraform cho pipeline và nền tảng dữ liệu.
order: 44
tags: [DataOps, CI/CD, continuous deployment, data as code, infrastructure as code, Terraform, GitHub Actions]
---

# DataOps, CI/CD và hạ tầng dưới dạng mã

Nền tảng dữ liệu thay đổi liên tục: model mới, định nghĩa metric được sửa, nguồn mới, cluster lớn hơn. DataOps là kỷ luật giúp những thay đổi đó nhỏ, được review, được kiểm thử và có thể đảo ngược. Trang này trình bày thực hành, phần tự động hóa thực thi nó (CI/CD), cách áp dụng cùng ý tưởng cho chính dữ liệu (data as code), và cách quản lý hạ tầng theo cùng lối đó (IaC và Terraform).

Giả định dùng trong ví dụ: một repository Git chứa dbt model, YAML của semantic layer, mã orchestrator, fixture đánh giá trợ lý và thư mục `infra/` chứa Terraform.

## DataOps

**Là gì.** DataOps áp dụng thực hành DevOps và lean vào công việc dữ liệu: version control cho mọi thứ, kiểm thử tự động, tích hợp và triển khai liên tục, tách biệt môi trường, khả năng quan sát và vòng phản hồi ngắn giữa bên tạo và bên dùng dữ liệu. Mục tiêu là đưa thay đổi dữ liệu đáng tin cậy ra nhanh — tốc độ và chất lượng đi cùng nhau, không đánh đổi cái này lấy cái kia.

**Cách hoạt động.** Trên thực tế, quy trình DataOps trông như sau:

1. Mọi thay đổi (SQL model, metric, DAG, quyền, hạ tầng) bắt đầu bằng một nhánh và một pull request.
2. Kiểm tra tự động chạy trên pull request: lint, biên dịch, unit test, data test trên mẫu hoặc môi trường cô lập, và phân tích ảnh hưởng tới model và dashboard downstream.
3. Người review từ nhóm sở hữu phê duyệt.
4. Merge sẽ tự động triển khai lên production, với kiểm tra dữ liệu làm cổng chặn trước khi công bố.
5. Production được quan sát (độ mới, khối lượng, schema, test thất bại, chi phí), và sự cố được chuyển thành test mới.

**Ví dụ cụ thể (định nghĩa "hoàn thành" cho một thay đổi dữ liệu, minh họa).**

```text
[ ] Thay đổi model và metric nằm trong Git, được chủ domain review
[ ] CI xanh: lint, biên dịch, unit test, data test trên model đổi + downstream
[ ] Bộ đánh giá trợ lý giữ nguyên hoặc tốt hơn với các metric bị ảnh hưởng
[ ] Có kế hoạch backfill nếu dữ liệu lịch sử thay đổi
[ ] Cập nhật monitor và metadata chủ sở hữu
[ ] Biết bước rollback (revert commit, khôi phục snapshot hoặc reset nhánh)
```

**Kiểu lỗi.** Mua một công cụ rồi gọi đó là DataOps; test chỉ kiểm tra schema, không kiểm tra giá trị; hotfix thủ công trên production không bao giờ về Git; CI chậm đến mức mọi người đi đường vòng.

**Kiểm định.** Theo dõi lead time từ pull request tới production, tỷ lệ thay đổi gây lỗi, thời gian trung bình để khôi phục sau sự cố dữ liệu, và tỷ lệ sự cố được test bắt trước khi người dùng nhận ra.

## CI/CD for Data

**Là gì.** CI/CD cho dữ liệu áp dụng tích hợp liên tục (tự động build và kiểm thử mọi thay đổi) và continuous delivery hoặc deployment (tự động phát hành thay đổi đã kiểm thử) cho pipeline, SQL model, định nghĩa semantic và mã nền tảng.

**Cách hoạt động.** CI cho dữ liệu khác CI cho ứng dụng vì tính đúng đắn phụ thuộc vào dữ liệu, không chỉ vào mã. Các kỹ thuật phổ biến:

- **Môi trường cô lập**: build model thay đổi vào schema riêng cho mỗi pull request hoặc vào một nhánh của catalog.
- **Slim build**: chỉ build model đã sửa và các model downstream của chúng, các tham chiếu upstream không đổi được trỏ (defer) sang artifact production.
- **Data test**: tính duy nhất, not-null, giá trị chấp nhận, quan hệ, số dòng và đối soát.
- **Diff**: so output của model đã đổi với production (số dòng, giá trị thay đổi, dịch chuyển phân phối).
- **Kiểm tra semantic và AI**: kiểm định YAML metric và chạy bộ câu hỏi chuẩn (golden question) của trợ lý khi metric thay đổi.

**Ví dụ cụ thể (workflow GitHub Actions minh họa).**

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
        run: ./scripts/validate_semantic_layer.sh      # ví dụ kiểm định cấu hình MetricFlow
      - name: Assistant golden questions
        run: python -m evals.run --suite text2sql_golden --fail-under 0.95
      - name: Drop CI schema
        if: always()
        run: ./scripts/drop_schema.sh "$CI_SCHEMA"
```

**Kiểu lỗi.** CI dùng fixture quá nhỏ và bỏ sót vấn đề ở quy mô production; test đạt trên bảng rỗng; secret production lộ cho job pull request từ fork; schema CI còn sót lại gây tốn chi phí; test chập chờn khiến mọi người quen chạy lại cho đến khi xanh.

**Kiểm định.** Đưa vào một thay đổi lỗi đã biết (khóa trùng, cột bị đổi tên mà downstream đang dùng, công thức metric sai) và xác nhận CI chặn được; xem lại thời gian và chi phí CI hằng tháng; dùng credential đặc quyền tối thiểu cho CI.

## Continuous Deployment (CD)

**Là gì.** Continuous deployment phát hành lên production mọi thay đổi đã vượt qua pipeline tự động mà không có bước phê duyệt thủ công. Nó khác **continuous delivery**, nơi mọi thay đổi luôn ở trạng thái *có thể phát hành* nhưng một người quyết định khi nào phát hành.

**Cách hoạt động.** Với dữ liệu, triển khai không chỉ là sao chép mã: phiên bản model mới phải được build, có thể phải backfill, kiểm định rồi mới hiển thị. Các mẫu an toàn gồm:

- **Blue/green hoặc write-audit-publish**: build vào schema hoặc nhánh staging, chạy kiểm tra, rồi hoán đổi hoặc merge một cách nguyên tử.
- **Model có phiên bản**: công bố `fct_orders_v2` song song với `v1` và chuyển bên tiêu thụ trước khi bỏ `v1`.
- **Feature flag cho metric**: phát hành định nghĩa metric mới ở trạng thái ẩn, so sánh, rồi mới mở ra.

**Ví dụ cụ thể (job triển khai khi merge, minh họa).**

```yaml
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production        # giữ secret prod; thêm required reviewer ở đây nếu muốn continuous *delivery*
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.lock
      - run: dbt build --target prod_staging --select state:modified+ --state prod-artifacts/
      - run: python scripts/audit_staging.py --max-row-change-pct 5
      - run: python scripts/publish.py --from prod_staging --to prod   # hoán đổi nguyên tử
      - run: python scripts/upload_manifest.py prod-artifacts/
```

**Kiểu lỗi.** Tự động triển khai hoàn toàn những thay đổi viết lại lịch sử (định nghĩa doanh thu bị đổi âm thầm làm thay đổi số liệu năm ngoái); triển khai thành công trong khi backfill thất bại; không có đường rollback cho dữ liệu.

**Kiểm định.** Quyết định rõ loại thay đổi nào được triển khai liên tục (cột mới, test mới) và loại nào cần continuous delivery có cổng duyệt của con người (đổi định nghĩa metric, backfill, xóa dữ liệu). Diễn tập rollback.

## Data as Code

**Là gì.** Data as code áp dụng quy trình kiểu Git — nhánh, commit, tag, merge và revert — cho chính dữ liệu, không chỉ cho mã tạo ra nó. Với catalog hoặc table format có phiên bản, bạn có thể build trên một nhánh cô lập, kiểm định, rồi merge nguyên tử vào view production.

**Cách hoạt động.** Nhiều lớp cung cấp khả năng này:

- **Table format**: Apache Iceberg hỗ trợ snapshot, nhánh và tag theo từng bảng; Delta Lake hỗ trợ time travel theo phiên bản.
- **Catalog có phiên bản**: Project Nessie đánh phiên bản toàn bộ catalog các bảng Iceberg, nên một nhánh có thể chứa thay đổi phối hợp trên nhiều bảng và merge chúng cùng lúc.
- **Phiên bản trên object store**: lakeFS cung cấp nhánh kiểu Git trên các file trong object storage.

Mẫu phổ biến là **write-audit-publish (WAP)**: ghi vào nhánh, kiểm toán bằng data test, công bố bằng merge hoặc fast-forward.

**Ví dụ cụ thể (minh họa, nhánh Iceberg với Spark SQL).**

```sql
-- 0. Một lần: bật write-audit-publish cho bảng
ALTER TABLE lake.analytics.fct_orders SET TBLPROPERTIES ('write.wap.enabled' = 'true');

-- 1. Tạo nhánh kiểm toán cho lượt nạp hôm nay
ALTER TABLE lake.analytics.fct_orders CREATE BRANCH audit_20261117;

-- 2. Trỏ việc ghi vào nhánh (cấu hình session Spark), rồi chạy job như bình thường
SET spark.wap.branch = audit_20261117;
INSERT OVERWRITE lake.analytics.fct_orders SELECT * FROM lake.staging.orders_20261117;

-- 3. Kiểm toán nhánh (đọc tường minh)
SELECT count(*), count(distinct order_id)
FROM lake.analytics.fct_orders VERSION AS OF 'audit_20261117';

-- 4. Công bố nguyên tử nếu kiểm tra đạt
CALL lake.system.fast_forward('analytics.fct_orders', 'main', 'audit_20261117');
```

Với thay đổi trải trên nhiều bảng (fact và dimension phải nhất quán với nhau), nhánh cấp catalog như của Nessie an toàn hơn nhánh theo từng bảng.

**Kiểu lỗi.** Nhánh để mở mãi và phân kỳ; bên đọc vô tình trỏ vào nhánh không phải main; chính sách lưu giữ hoặc hết hạn snapshot xóa mất phiên bản bạn định rollback về; cho rằng phân nhánh làm bản sao miễn phí với mọi engine (mức hỗ trợ khác nhau).

**Kiểm định.** Thử rollback (đặt lại `main` về snapshot trước) trên một bảng không phải production; giám sát số lượng và tuổi của nhánh; xác nhận mọi bên tiêu thụ, kể cả công cụ BI và trợ lý, đọc tường minh `main` hoặc một tag được ghim.

**Liên hệ với trợ lý phân tích có quản trị.** Dữ liệu có phiên bản cho phép ghim các lượt đánh giá vào một tag (ví dụ `eval_2026_11`) để thay đổi độ chính xác của trợ lý có thể quy về model, prompt hay dữ liệu. Nó cũng cho phép câu trả lời mang provenance như "tính từ snapshot 8812 của `fct_orders`".

## Infrastructure as Code (IaC)

**Là gì.** Infrastructure as code (hạ tầng dưới dạng mã) định nghĩa máy chủ, mạng, lưu trữ, cơ sở dữ liệu, quyền và dịch vụ managed trong các file có version control và áp dụng chúng bằng công cụ, thay vì bấm trên console.

**Cách hoạt động.** Công cụ có loại **declarative** (bạn mô tả trạng thái cuối mong muốn, công cụ tự tính thay đổi — Terraform/OpenTofu, AWS CloudFormation, Pulumi trong nhiều cách dùng) hoặc **imperative** (script thực hiện các bước theo thứ tự). Công cụ declarative so sánh trạng thái mong muốn, trạng thái đã ghi nhận và trạng thái thực, rồi lập kế hoạch cho phần chênh lệch. Lợi ích là môi trường tái lập được, code review cho thay đổi hạ tầng và vết kiểm toán.

**Kiểu lỗi.** **Drift**: ai đó sửa tài nguyên thủ công và mã không còn phản ánh thực tế; secret bị commit vào repository; một cấu hình khổng lồ nơi mọi thay đổi đều có thể ảnh hưởng tất cả; production và development được định nghĩa bằng copy-paste thay vì module dùng chung.

**Kiểm định.** Chạy `plan` trong CI cho mọi pull request và review nó; phát hiện drift theo lịch; quét cấu hình bằng công cụ chính sách (ví dụ kiểm tra bucket không công khai và đã bật mã hóa).

## Terraform

**Là gì.** Terraform, do HashiCorp tạo ra (nay thuộc IBM), là công cụ IaC declarative dùng HashiCorp Configuration Language (HCL). Sau khi đổi giấy phép năm 2023, bản fork cộng đồng **OpenTofu** trở thành lựa chọn mã nguồn mở với cú pháp phần lớn tương thích.

**Cách hoạt động.**

- **Provider** là plugin làm việc với API (AWS, Google Cloud, Azure, Snowflake, Databricks, Kubernetes và nhiều nữa).
- **Resource** khai báo đối tượng cần quản lý; **data source** đọc đối tượng có sẵn; **module** đóng gói nhóm tái sử dụng.
- **State** ghi nhận đối tượng thật nào tương ứng với resource nào. Hãy lưu nó ở remote backend có khóa, không bao giờ chỉ trên laptop.
- `terraform plan` hiển thị thay đổi đề xuất; `terraform apply` thực thi chúng.

**Ví dụ cụ thể (minh họa, lưu trữ và catalog lakehouse trên AWS).**

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket       = "acme-tf-state"
    key          = "lakehouse/prod.tfstate"
    region       = "eu-west-1"
    use_lockfile = true      # khóa state gốc trên S3 ở các phiên bản gần đây
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

Một job CI chạy `terraform fmt -check`, `terraform validate` và `terraform plan`, đăng plan lên pull request, và chỉ khi merge được duyệt mới chạy `apply` với credential production.

**Kiểu lỗi.** Plan hiển thị "hủy và tạo lại" một bucket lưu trữ hoặc cơ sở dữ liệu vì tên bị đổi (dùng `lifecycle { prevent_destroy = true }` cho kho dữ liệu quan trọng); nhiều lượt apply đồng thời làm hỏng state khi không có khóa; nâng phiên bản provider làm đổi hành vi; secret lọt vào file state (state phải được mã hóa và kiểm soát truy cập).

**Kiểm định.** Đọc mọi plan để tìm hành động `destroy` trước khi duyệt; ghim phiên bản provider; thử module trong tài khoản sandbox; chạy phát hiện drift theo lịch với `terraform plan -detailed-exitcode`.

**Liên hệ với trợ lý phân tích có quản trị.** Ranh giới truy cập của trợ lý chính là hạ tầng: role cơ sở dữ liệu chỉ đọc, quy tắc mạng, nơi lưu secret và thời hạn giữ log. Hãy định nghĩa chúng bằng Terraform để người review thấy chính xác trợ lý được chạm vào những gì, và để một lần vô tình cấp quyền ghi hiện ra như một diff cần review.

## Bài tập

1. Đặt dbt project của Dự án 1, YAML semantic và một thư mục Terraform vào cùng một repository.
2. Thêm workflow GitHub Actions để lint, build model đã đổi vào schema riêng cho từng PR, chạy test và chạy năm câu hỏi chuẩn của trợ lý.
3. Mở ba pull request có lỗi cố ý (khóa trùng, tham chiếu downstream bị hỏng, bộ lọc metric sai) và xác nhận mỗi cái bị chặn.
4. Hiện thực write-audit-publish bằng nhánh Iceberg, Nessie, lakeFS hoặc hoán đổi schema staging, và diễn tập một lần rollback.
5. Quản lý một bucket lưu trữ và một role cơ sở dữ liệu chỉ đọc bằng Terraform; sửa thủ công một thứ và phát hiện drift.

**Tiêu chí hoàn thành.**

- Link CI cho một pull request xanh và ba pull request cố ý đỏ.
- Chính sách bằng văn bản liệt kê loại thay đổi nào triển khai liên tục và loại nào cần cổng duyệt của con người.
- Bằng chứng một lần kiểm toán thất bại thành công (dữ liệu lỗi không bao giờ tới `main`) và một lần rollback thành công.
- Output Terraform plan cho quyền truy cập chỉ đọc của trợ lý, được review trong pull request, cùng kết quả phát hiện drift.
