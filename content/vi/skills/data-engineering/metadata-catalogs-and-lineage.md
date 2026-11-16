---
title: Metadata Catalog, khám phá dữ liệu và lineage
description: Phân biệt table catalog với discovery catalog, so sánh Alation, Collibra, DataHub, Amundsen, và thu thập lineage, provenance bằng OpenLineage và Marquez.
order: 20
tags: [governance, catalog, metadata, lineage, provenance, openlineage, datahub, khám phá dữ liệu]
---

# Metadata Catalog, khám phá dữ liệu và lineage

Có hai loại hệ thống cùng được gọi là "catalog". **Table catalog** (Iceberg REST catalog, Apache Polaris, Unity Catalog, AWS Glue, Hive Metastore) cho query engine biết metadata hiện tại của bảng nằm ở đâu để việc đọc và commit diễn ra đúng. **Discovery catalog hay governance catalog** (Alation, Collibra, DataHub, Amundsen, OpenMetadata) giúp con người và công cụ tìm dataset, hiểu ý nghĩa, biết ai sở hữu và đánh giá có nên tin hay không. Lakehouse thường bắt buộc cần loại thứ nhất và được lợi từ loại thứ hai; nhầm lẫn hai loại sẽ dẫn tới kỳ vọng sai về việc mỗi hệ thống thực sự cưỡng chế điều gì.

Trang này mở rộng từ [Quản trị dữ liệu và Data Product](governance-and-data-products.html). Giả định trong các ví dụ: lakehouse Iceberg với REST catalog, Spark và Trino làm engine, một orchestrator như Airflow hoặc Dagster, và một trợ lý Text2SQL đọc các mart đã được tuyển chọn.

## Metadata Catalog

Metadata catalog là nơi đăng ký các tài sản dữ liệu và thông tin về chúng. Theo nghĩa hẹp, phục vụ engine, nó ánh xạ định danh bảng như `sales.orders` tới vị trí file metadata hiện tại và thực hiện commit nguyên tử: khi một writer thêm snapshot, catalog chỉ đổi con trỏ nếu chưa có ai commit trước. Theo nghĩa rộng, phục vụ con người, nó lưu mô tả, chủ sở hữu, tag, phân loại, trạng thái chất lượng và mức sử dụng.

**Cách hoạt động.** Engine Iceberg gọi catalog để load bảng, nhận vị trí `metadata.json` hiện tại (hoặc chính metadata qua giao thức REST), rồi đọc manifest trực tiếp từ object storage. Discovery catalog thì *thu hoạch* metadata: kết nối tới table catalog, warehouse, công cụ BI và orchestrator theo lịch hoặc qua sự kiện để xây dựng một đồ thị có thể tìm kiếm.

**Ví dụ (minh họa, response của REST catalog đã rút gọn):**

```json
{
  "metadata-location": "s3://lake/warehouse/sales/orders/metadata/00042-6c1e.metadata.json",
  "metadata": {
    "format-version": 2,
    "table-uuid": "6c1e0d2a-...",
    "current-snapshot-id": 8812345501,
    "properties": {"owner": "sales-data-team", "classification": "internal"}
  }
}
```

**Lỗi thường gặp.** Hai table catalog cùng trỏ tới một bộ file (commit split-brain); metadata trong discovery catalog chậm hàng tuần so với table catalog; mô tả được sao chép một lần rồi không ai cập nhật; phân loại chỉ nằm trong table property nên công cụ BI không bao giờ thấy.

**Kiểm chứng.** Với một mẫu bảng, so sánh schema và snapshot mà discovery catalog báo cáo với table catalog. Theo dõi độ trễ thu hoạch. Kiểm tra mọi mart đã công bố đều có chủ sở hữu và mô tả, và cho CI fail khi mart mới thiếu thông tin này.

**Vị trí trong lakehouse / Text2SQL.** Table catalog là nguồn sự thật về những gì tồn tại; discovery catalog cung cấp mô tả, chủ sở hữu và cờ chứng nhận (certified) mà trợ lý Text2SQL dùng để chỉ chọn bảng đã được duyệt. Không bao giờ để trợ lý suy ra danh sách bảng được phép từ những gì engine liệt kê được.

## Data Discovery

Data discovery là quá trình một người (hoặc một agent) tìm dataset ứng viên, hiểu nó biểu diễn điều gì và quyết định nó có phù hợp với mục đích hay không. Tìm kiếm chỉ là bước đầu; phần lớn công việc do các tín hiệu tin cậy đảm nhận.

**Cách hoạt động.** Trải nghiệm discovery tốt kết hợp tìm kiếm theo từ khóa và theo ngữ nghĩa trên tên và mô tả, xem trước schema và thống kê mẫu (từ [data profiling](data-quality-tooling-and-observability.html#data-profiling)), chủ sở hữu, freshness, trạng thái chất lượng, mức phổ biến từ query log, lineage và chứng nhận. Người dùng nên thấy được vì sao một kết quả được xếp hạng cao.

**Ví dụ (minh họa bản ghi discovery cho một bảng):**

```yaml
dataset: analytics.fct_orders
grain: one row per order line
owner: sales-data-team
steward: jane.doe
classification: internal
certified: true
freshness: complete through previous UTC day, landed by 06:00 UTC
quality: 14/14 checks passing (last run 2026-11-16T06:05Z)
popular_with: [finance-bi, text2sql-assistant]
known_limitations: "Returns before 2024-01-01 are not linked to original orders."
```

**Lỗi thường gặp.** Tìm kiếm trả về năm bảng tên `orders` mà không gợi ý bảng nào có thẩm quyền; độ phổ biến ưu tiên một bảng đã deprecated vì nhiều dashboard cũ vẫn truy vấn; bản xem trước làm lộ giá trị mẫu nhạy cảm cho người không có quyền truy vấn bảng.

**Kiểm chứng.** Kiểm thử theo tác vụ: giao cho ba người dùng một câu hỏi ("doanh thu thuần theo vùng nằm ở đâu?") và đo xem họ có tìm ra tài sản đã chứng nhận không. Xác nhận bản xem trước tuân theo cùng chính sách truy cập như truy vấn.

**Vị trí trong lakehouse / Text2SQL.** Metadata discovery là ngữ cảnh truy hồi lý tưởng cho trợ lý: một danh sách ngắn tài sản đã chứng nhận kèm grain và hạn chế an toàn hơn nhiều so với đổ toàn bộ schema.

## Alation

Alation là data catalog doanh nghiệp thương mại, tập trung vào khám phá, tuyển chọn (curation) và workflow quản trị. Alation nổi tiếng với việc phân tích query log để chỉ ra bảng và cột nào thực sự được dùng, bởi ai, trong phép join nào, và cho phép steward biên soạn bài viết, thuật ngữ glossary và cờ tin cậy trên tài sản.

**Cách hoạt động.** Connector quét database, warehouse, lakehouse engine và công cụ BI; việc nạp query log tạo dữ liệu sử dụng và độ phổ biến; steward gắn thuật ngữ nghiệp vụ, xác nhận (endorsement) và cảnh báo deprecated; chính sách và workflow điều hướng phê duyệt. Alation không phải Iceberg table catalog: nó đọc từ Glue, Unity Catalog, engine dùng Polaris và các nguồn tương tự nhưng không điều phối commit bảng.

**Ví dụ (minh họa workflow curation).** Steward đánh dấu `analytics.fct_orders` là *Endorsed*, liên kết với thuật ngữ glossary "Doanh thu thuần" và thêm cảnh báo trên `staging.orders_raw`: "Không dùng để báo cáo; có chứa dòng đã hủy." Analyst tìm "revenue" giờ thấy bảng được xác nhận ở đầu, còn bảng raw hiển thị cảnh báo.

**Lỗi thường gặp.** Coi việc mua công cụ là chương trình governance; hàng đợi stewardship phình ra không ai xử lý; xếp hạng theo mức sử dụng đẩy lên bảng dùng nhiều nhưng sai; connector thiếu lakehouse engine nên catalog chỉ hiển thị warehouse cũ.

**Kiểm chứng.** Đo độ phủ (tỷ lệ mart production có chủ sở hữu, mô tả và liên kết thuật ngữ), độ trễ curation (thời gian từ khi có bảng mới tới khi được biên soạn) và độ chính xác của một mẫu mô tả do chuyên gia domain rà soát.

**Vị trí trong lakehouse / Text2SQL.** Dùng Alation (hoặc catalog tương tự) làm lớp ý nghĩa do con người biên soạn nằm trên table catalog. Xuất cờ endorsement và deprecated vào semantic model hoặc allow-list của trợ lý thay vì để trợ lý truy vấn giao diện catalog.

## Collibra

Collibra là nền tảng data intelligence và governance thương mại. Thế mạnh của Collibra là quản lý business glossary, mô hình vận hành gồm domain, community và trách nhiệm, workflow stewardship cấu hình được, quản lý chính sách và lineage. Collibra thường được chọn ở nơi quy trình governance, phê duyệt và bằng chứng tuân thủ quan trọng ngang với khám phá dữ liệu.

**Cách hoạt động.** Tài sản (bảng, cột, báo cáo, thuật ngữ nghiệp vụ, chính sách) nằm trong domain với các vai trò được gán như owner và steward. Workflow đưa một thuật ngữ hay chính sách qua các bước nháp, rà soát và phê duyệt. Tích hợp thu hoạch metadata kỹ thuật và lineage từ nguồn, và một số phiên bản có thể đẩy chính sách bảo vệ xuống nền tảng được hỗ trợ.

**Ví dụ (minh họa thuật ngữ glossary kèm trạng thái workflow):**

```yaml
term: Active Customer
domain: Customer
definition: "A customer with at least one non-cancelled order in the trailing 90 days."
owner: head-of-customer-analytics
steward: customer-data-steward
status: Approved            # Draft -> Under Review -> Approved
related_columns: [analytics.dim_customer.is_active]
related_policies: [Customer PII Handling v3]
```

**So sánh với DataHub và Polaris.** Polaris là Iceberg table catalog cưỡng chế quyền cấp bảng cho engine; Collibra không thay thế được nó. DataHub là nền tảng metadata mã nguồn mở mạnh về lineage kỹ thuật và API; Collibra nhấn mạnh hơn vào workflow governance nghiệp vụ. Nhiều tổ chức chạy một table catalog cộng với một discovery hoặc governance catalog, không phải cả ba.

**Lỗi thường gặp.** Thuật ngữ glossary được duyệt trong Collibra nhưng triển khai khác trong dbt hoặc semantic layer; workflow nặng nề đến mức các team đi đường vòng; bản ghi chính sách không bao giờ được nối tới điểm cưỡng chế.

**Kiểm chứng.** Đối chiếu định nghĩa thuật ngữ đã duyệt với định nghĩa metric trong mã ít nhất mỗi lần phát hành; lấy mẫu chính sách và xác nhận mỗi chính sách ghi rõ hệ thống nào cưỡng chế.

**Vị trí trong lakehouse / Text2SQL.** Thuật ngữ glossary trở thành từ đồng nghĩa và định nghĩa trong semantic layer; trợ lý nên trích dẫn định nghĩa đã duyệt khi trả lời "có bao nhiêu khách hàng active".

## DataHub

DataHub là nền tảng metadata mã nguồn mở (khởi nguồn từ LinkedIn, hiện được phát triển bởi cộng đồng mã nguồn mở cùng một công ty cung cấp phiên bản managed) cho khám phá, lineage, ownership và governance. DataHub mô hình hóa metadata thành entity (dataset, dashboard, pipeline, user) với các aspect có phiên bản (schema, ownership, tag, glossary term), và cung cấp chúng qua API GraphQL và REST.

**Cách hoạt động.** Các "recipe" ingestion kéo metadata từ nguồn như Iceberg catalog, Trino, Snowflake, dbt, Airflow và Looker; emitter dạng push và tích hợp OpenLineage bổ sung lineage lúc chạy. Thay đổi được truyền dưới dạng sự kiện thay đổi metadata mà hệ thống khác có thể đăng ký nhận, đây là lý do DataHub hữu ích cho [active metadata](#active-metadata).

**Ví dụ (minh họa recipe ingestion):**

```yaml
source:
  type: iceberg
  config:
    catalog:
      lake:
        type: rest
        uri: https://catalog.internal/api/catalog
    platform_instance: prod_lake
sink:
  type: datahub-rest
  config:
    server: https://datahub.internal:8080
```

**So sánh với OpenMetadata và Collibra.** OpenMetadata là lựa chọn mã nguồn mở khác với một schema hợp nhất duy nhất, có sẵn data quality test và tính năng cộng tác; DataHub có kiến trúc hướng sự kiện trưởng thành và hệ sinh thái connector rộng. Collibra là sản phẩm thương mại, xoay quanh quy trình. Hãy chọn dựa trên độ phủ connector cho stack của bạn, nhu cầu API và ai sẽ vận hành dịch vụ.

**Lỗi thường gặp.** Chạy ingestion một lần rồi không lên lịch; entity dataset bị trùng vì hai recipe dùng platform instance khác nhau; lineage chỉ phủ model SQL còn job Python thì vô hình.

**Kiểm chứng.** Kiểm tra mỗi bảng production chỉ xuất hiện một lần với platform instance đúng; so sánh cạnh lineage trong DataHub với bản đồ vẽ tay cho một pipeline; cảnh báo khi ingestion chạy lỗi.

**Vị trí trong lakehouse / Text2SQL.** Truy vấn API của DataHub để xây allow-list cho trợ lý từ các tag như `certified` và loại bỏ tài sản có tag `deprecated` hoặc `restricted`.

## Amundsen

Amundsen là data discovery catalog mã nguồn mở do Lyft tạo ra. Nó phổ biến hóa trải nghiệm ưu tiên tìm kiếm, xếp hạng theo mức sử dụng, với trang bảng hiển thị mô tả, chủ sở hữu, người dùng thường xuyên và thống kê cột, chạy trên graph database và search index, được nạp bởi thư viện ingestion "databuilder".

**Tình trạng.** Dự án upstream ít hoạt động trong những năm gần đây và repository đã được archive trong năm 2026. Hãy kiểm tra tình trạng repository hiện tại trước khi chọn: dự án đã archive không nhận bản vá bảo mật hay connector mới. Hãy xem Amundsen là một thiết kế tham khảo hữu ích cho discovery ưu tiên tìm kiếm, không phải lựa chọn mặc định cho lakehouse mới.

**So sánh với DataHub và OpenMetadata.** Cả hai đều được duy trì tích cực, có lineage và tính năng governance mà Amundsen thiếu hoặc bổ sung muộn, và hỗ trợ Iceberg cùng engine hiện đại. Các team rời Amundsen thường ánh xạ bản ghi bảng, cột, chủ sở hữu và mô tả sang một trong hai.

**Ví dụ (minh họa bảng kiểm kê khi di chuyển):**

| Bản ghi Amundsen | Đích trong DataHub/OpenMetadata | Kiểm tra sau di chuyển |
|---|---|---|
| Mô tả bảng | Tài liệu dataset | Số bảng có mô tả không đổi |
| Chủ sở hữu | Aspect ownership | Mọi bảng certified vẫn có chủ sở hữu |
| Badge / tag | Tag hoặc glossary term | Tên tag được ánh xạ, không trùng lặp |
| Thống kê cột | Kết quả profiling | Chạy lại profiling; không sao chép thống kê cũ |

**Lỗi thường gặp.** Để dịch vụ đã archive tiếp tục mở trên mạng; mất mô tả đã biên soạn khi di chuyển; tưởng có lineage trong Amundsen trong khi chưa từng cấu hình.

**Vị trí trong lakehouse / Text2SQL.** Nếu Amundsen vẫn chứa những mô tả tốt nhất của bạn, hãy xuất chúng làm dữ liệu khởi đầu cho tài liệu bảng của trợ lý, rồi chuyển sang một catalog còn được duy trì.

## Active Metadata

Active metadata là metadata được thu thập liên tục và *được dùng* để kích hoạt hành động ở hệ thống khác, thay vì nằm trên trang catalog chờ người đọc. Metadata thụ động trả lời "đây là gì?"; active metadata thay đổi điều sẽ xảy ra tiếp theo.

**Cách hoạt động.** Sự kiện từ engine, orchestrator và công cụ chất lượng (schema thay đổi, check thất bại, bảng không được truy vấn trong 180 ngày, phát hiện PII) được phát lên stream hoặc API. Các quy tắc đăng ký nhận và hành động: thêm banner cảnh báo trong BI, mở ticket cho chủ sở hữu, lan truyền tag PII xuống cột downstream qua lineage, hoặc gỡ bảng khỏi allow-list của trợ lý.

**Ví dụ (minh họa quy tắc):**

```yaml
when:
  event: quality_check_failed
  severity: blocking
  dataset_tag: certified
then:
  - set_dataset_status: degraded
  - notify: dataset.owner
  - text2sql_allowlist: suspend   # assistant answers "data is currently under investigation"
  - bi_banner: "Figures may be incomplete since {{event.time}}"
```

**Lỗi thường gặp.** Tự động hóa kích hoạt bởi tín hiệu nhiễu khiến người dùng quen bỏ qua banner; vòng lặp khi hành động sinh ra chính sự kiện đã kích hoạt nó; hành động không có dấu vết audit.

**Kiểm chứng.** Phát lại một sự kiện lỗi đã ghi trong môi trường staging và xác nhận mỗi hành động xảy ra đúng một lần, được ghi log và được hoàn tác khi check phục hồi.

**Vị trí trong lakehouse / Text2SQL.** Active metadata là cách trợ lý biết một bảng certified hiện đang không khỏe mà không cần ai sửa cấu hình của nó.

## Active Data Governance

Active data governance nghĩa là quy tắc governance được phần mềm cưỡng chế ngay tại thời điểm dữ liệu được dùng, không chỉ được mô tả trong tài liệu và rà soát định kỳ. Một tag phân loại đặt trong catalog khiến masking áp dụng lúc truy vấn; một quy tắc lưu giữ tạo ra job xóa theo lịch; một vi phạm contract chặn việc công bố.

**Cách hoạt động.** Chính sách được viết dưới dạng mã hoặc cấu hình (masking theo tag, row filter, retention job, quy tắc CI) và gắn với metadata như tag hay domain. Điểm cưỡng chế gồm table catalog, query engine, công cụ BI và pipeline. Bằng chứng cưỡng chế (log, kết quả kiểm thử) được thu thập tự động.

**Ví dụ (minh họa chính sách theo tag):**

```yaml
policy: mask-pii-email
applies_to: { tag: pii.email }
enforced_in: [trino, spark-sql, bi-semantic-layer]
rule: show_full_value_only_to_roles: [pii_reader]
evidence: daily denied-access test result stored in audit bucket
owner: privacy-office
```

**Lỗi thường gặp.** Chính sách được cưỡng chế ở một engine nhưng không ở engine khác đọc cùng bộ file; tag là tùy chọn nên cột không gắn tag mặc nhiên không được bảo vệ; không ai kiểm thử rằng việc từ chối thực sự xảy ra.

**Kiểm chứng.** Duy trì test case được phép/bị từ chối cho mỗi chính sách và chạy chúng trên mọi engine có thể đọc dữ liệu. Báo cáo tỷ lệ cột nhạy cảm có chính sách đang được cưỡng chế.

**Vị trí trong lakehouse / Text2SQL.** Trợ lý phải thực thi dưới danh tính của người dùng cuối để cùng các chính sách active được áp dụng; xem [Kiểm soát truy cập: RBAC, bảo mật cấp dòng và cấp cột](access-control-rbac-rls-cls.html).

## OpenLineage

OpenLineage là đặc tả mở để mô tả lineage lúc chạy. Một job phát sự kiện nói rằng "lần chạy này của job này đã bắt đầu/hoàn thành/thất bại, đọc các input này và ghi các output này", kèm các *facet* tùy chọn mang schema, lineage cấp cột, câu SQL, chỉ số chất lượng dữ liệu và hơn thế. Có tích hợp cho Spark, Airflow, dbt, Flink và nhiều công cụ khác; bên tiêu thụ gồm Marquez, DataHub và một số catalog thương mại.

**Cách hoạt động.** Mỗi sự kiện có `eventType` (`START`, `RUNNING`, `COMPLETE`, `FAIL`, `ABORT`), một `run` với `runId` duy nhất, một `job` định danh bằng namespace và name, cùng danh sách dataset input và output định danh bằng namespace và name. Vì định danh được chuẩn hóa, lineage từ nhiều công cụ có thể ghép thành một đồ thị.

**Ví dụ (minh họa sự kiện COMPLETE, đã rút gọn):**

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-11-16T06:04:12.512Z",
  "producer": "https://github.com/OpenLineage/OpenLineage/tree/1.x/integration/spark",
  "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent",
  "run": { "runId": "0193a1f2-7c55-7d1e-9a7e-2f4b9c3e1a10" },
  "job": { "namespace": "airflow-prod", "name": "build_marts.fct_orders" },
  "inputs": [
    { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines" }
  ],
  "outputs": [
    {
      "namespace": "iceberg://catalog.internal",
      "name": "analytics.fct_orders",
      "facets": {
        "columnLineage": {
          "fields": {
            "net_amount": {
              "inputFields": [
                { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines", "field": "gross_amount" },
                { "namespace": "iceberg://catalog.internal", "name": "staging.order_lines", "field": "discount_amount" }
              ]
            }
          }
        }
      }
    }
  ]
}
```

Metadata bắt buộc của facet (`_producer`, `_schemaURL`) được lược bỏ cho gọn; hãy kiểm tra phiên bản đặc tả mà tích hợp của bạn phát ra.

**Lỗi thường gặp.** Các job đặt tên cùng một bảng khác nhau (`s3://lake/...` so với `iceberg://...`), tạo ra các đồ thị rời rạc; tích hợp phát `START` nhưng crash trước `COMPLETE`; thiếu lineage cấp cột cho UDF hoặc phép biến đổi Python.

**Kiểm chứng.** Với một pipeline, khẳng định trong CI rằng một lần chạy thử phát ra sự kiện có tên input và output khớp định danh trong catalog. Theo dõi tỷ lệ sự kiện `START` so với sự kiện kết thúc.

**Vị trí trong lakehouse / Text2SQL.** Lineage cho phép trả lời "câu trả lời nào của trợ lý đã dùng dữ liệu từ partition sau đó bị sửa?" và phân tích tác động trước khi đổi một cột mà semantic model phụ thuộc.

## Marquez

Marquez là bản cài đặt tham chiếu của máy chủ OpenLineage, một dự án thuộc LF AI & Data. Marquez nhận sự kiện OpenLineage qua HTTP, lưu job, run và phiên bản dataset trong PostgreSQL, và cung cấp API cùng giao diện web để duyệt đồ thị lineage và lịch sử chạy.

**Cách hoạt động.** Tích hợp được cấu hình để gửi sự kiện tới `POST /api/v1/lineage`. Marquez đánh phiên bản dataset và job khi schema hoặc mã thay đổi, nhờ đó bạn biết lần chạy nào tạo ra phiên bản dataset nào.

**Ví dụ (minh họa kiểm tra lineage đã tới):**

```bash
# Gửi một sự kiện thử, rồi đọc đồ thị lineage của dataset output.
curl -s -X POST http://marquez.internal:5000/api/v1/lineage \
  -H 'Content-Type: application/json' -d @complete_event.json
curl -s "http://marquez.internal:5000/api/v1/lineage?nodeId=dataset:iceberg://catalog.internal:analytics.fct_orders"
```

**So sánh với DataHub và lineage của catalog.** Marquez tập trung hẹp vào lineage cấp run và dễ dựng lên cho việc học hoặc làm backend lineage. DataHub cũng nhận OpenLineage nhưng bổ sung discovery, ownership và governance. Lineage gốc của catalog (ví dụ trong Unity Catalog) tiện lợi nhưng có thể chỉ thấy job chạy trên nền tảng đó.

**Lỗi thường gặp.** Chạy Marquez không xác thực trên mạng dùng chung; không có kế hoạch lưu giữ cho khối lượng sự kiện; coi Marquez là một catalog đầy đủ.

**Kiểm chứng.** Xác nhận giao diện hiển thị mỗi job production với trạng thái lần chạy mới nhất, và lần chạy lỗi hiện là lỗi chứ không bị thiếu.

**Vị trí trong lakehouse / Text2SQL.** Marquez là thành phần lab phù hợp cho chương trình học này: phát sự kiện từ pipeline của Project 1 và xem đồ thị trước khi bổ sung một catalog đầy đủ.

## Data Lineage vs Data Provenance

Hai thuật ngữ giao nhau nhưng trả lời các câu hỏi khác nhau.

| Khía cạnh | Data lineage | Data provenance |
|---|---|---|
| Câu hỏi | Dữ liệu đã chảy và biến đổi thế nào? | Dữ liệu bắt nguồn từ đâu, ai tạo ra, dưới thẩm quyền nào? |
| Mức chi tiết thường gặp | Dataset, cột, job, run | Bản ghi, file, tài liệu hoặc dataset kèm thuộc tính nguồn gốc |
| Thu thập bằng | Phân tích SQL, sự kiện OpenLineage, metadata orchestrator | Định danh nguồn, metadata ingestion, chữ ký, giấy phép, bản ghi đồng ý |
| Công dụng chính | Phân tích tác động, gỡ lỗi, quản lý thay đổi | Độ tin cậy, audit, cơ sở pháp lý, khả năng tái lập, thẩm định dữ liệu huấn luyện AI |
| Ví dụ | `fct_orders.net_amount` suy ra từ `gross_amount - discount_amount` | Dòng đến từ file xuất ERP `orders_2026-11-15.csv`, SHA-256 `ab12...`, nhận qua SFTP từ nhà cung cấp X theo hợp đồng C-17 |

Lineage chủ yếu nói về *đường đi*; provenance chủ yếu nói về *nguồn gốc và thẩm quyền*. Một cuộc audit đầy đủ cần cả hai: lineage cho thấy metric đến từ bảng nguồn, provenance cho thấy nguồn đó được phép và không bị thay đổi.

**Kiểm chứng.** Chọn một con số đã báo cáo và thử dựng cả chuỗi lineage (job và bảng) lẫn bản ghi provenance (file nguồn, hash, thời điểm nhận, chủ sở hữu). Mỗi chỗ thiếu là một việc cần làm.

## Data Provenance

Data provenance là nguồn gốc và lịch sử được ghi chép của dữ liệu: nguồn nào tạo ra, agent hay hệ thống nào đã tạo hoặc sửa, khi nào, theo thẩm quyền hay giấy phép nào. Mô hình W3C PROV mô tả điều này bằng *entity* (dữ liệu), *activity* (tiến trình) và *agent* (người, tổ chức, phần mềm).

**Cách hoạt động.** Khi ingestion, ghi lại hệ thống nguồn, thời điểm trích xuất, định danh file hoặc batch, hash nội dung, hợp đồng hoặc cơ sở pháp lý và danh tính đã nạp. Giữ chúng dưới dạng cột (`_source_file`, `_ingested_at`, `_batch_id`) hoặc trong bảng phụ, và bảo toàn qua các phép biến đổi. Với dữ liệu cần độ tin cậy cao, ký file hoặc manifest và lưu hash vào storage chỉ cho phép ghi thêm để phát hiện được giả mạo.

**Ví dụ (minh họa cột provenance và câu kiểm tra):**

```sql
-- Mọi dòng đã công bố phải truy về một batch đã ghi nhận với hash đã xác minh.
select count(*) as rows_without_provenance
from analytics.fct_orders f
left join ops.ingestion_batches b on f._batch_id = b.batch_id
where b.batch_id is null or b.hash_verified = false;
```

**Lỗi thường gặp.** Bỏ các cột metadata ngay ở phép biến đổi đầu tiên; ghi đè file raw tại chỗ nên hash không còn khớp; dùng dữ liệu cào web hoặc bên thứ ba mà không ghi giấy phép; corpus RAG không ghi lại phiên bản tài liệu nào đã được index.

**Kiểm chứng.** Câu truy vấn trên trả về 0; storage raw là bất biến hoặc có versioning; một mẫu tài liệu được index cho AI có thể truy về phiên bản nguồn và chủ sở hữu.

**Vị trí trong lakehouse / Text2SQL.** Provenance cho phép trợ lý nói "dựa trên dữ liệu ERP nạp lúc 06:00 UTC" và cho phép người rà soát chứng minh đầu vào nào đã dùng cho một câu trả lời.

## Bài tập

1. Vẽ hai khối cho lab của bạn: table catalog và discovery catalog. Liệt kê mỗi khối có thẩm quyền về những thông tin nào.
2. Chạy Marquez cục bộ, phát sự kiện OpenLineage minh họa (với tên của bạn) và xác nhận đồ thị lineage hiển thị input và output.
3. Viết bản ghi discovery (chủ sở hữu, grain, phân loại, freshness, hạn chế) cho ba mart và suy ra allow-list Text2SQL từ đó.
4. Thêm `_batch_id` và `_ingested_at` vào một pipeline và cài đặt câu truy vấn kiểm tra provenance.
5. Định nghĩa một quy tắc active metadata tạm gỡ bảng khỏi trợ lý khi một check chặn thất bại, và kiểm thử bằng sự kiện phát lại.

### Tiêu chí hoàn thành

- Bạn giải thích được trong hai câu vì sao Polaris hay Glue không thay thế discovery catalog và ngược lại.
- Ít nhất một pipeline phát sự kiện OpenLineage có tên dataset khớp định danh trong catalog.
- Mọi mart certified có chủ sở hữu, steward, mô tả, phân loại và cột provenance.
- Một lỗi chất lượng loại chặn thay đổi được những gì trợ lý được phép truy vấn, và thay đổi đó được ghi log.
