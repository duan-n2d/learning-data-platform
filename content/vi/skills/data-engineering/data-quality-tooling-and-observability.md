---
title: Công cụ chất lượng dữ liệu và observability
description: Profile dữ liệu trước khi tin dùng, viết check bằng Great Expectations và Soda, giám sát bằng nền tảng observability như Monte Carlo, và hiểu về tính nhất quán dữ liệu.
order: 21
tags: [chất lượng dữ liệu, profiling, great expectations, soda, observability, monte carlo, tính nhất quán]
---

# Công cụ chất lượng dữ liệu và observability

[Chất lượng dữ liệu và hợp đồng](data-quality-contracts.html) giải thích *cần* kiểm tra gì và ở đâu. Trang này đề cập *cách* các team thường triển khai những kiểm tra đó: profiling để khám phá dữ liệu thực sự trông thế nào, framework kiểm thử khai báo (Great Expectations, Soda, dbt test), nền tảng observability theo dõi metadata production (Monte Carlo và tương tự), và các đảm bảo về tính nhất quán quyết định người đọc thấy phiên bản dữ liệu nào.

Giả định cho các ví dụ: một mart Iceberg hoặc warehouse `analytics.fct_orders` có grain một dòng mỗi order line, timestamp theo UTC, batch hằng ngày cần hoàn tất trước 06:00 UTC, và một trợ lý Text2SQL trả lời từ mart đó.

Một cách phân lớp hữu ích:

| Lớp | Câu hỏi được trả lời | Công cụ thường dùng |
|---|---|---|
| Profiling | Dữ liệu này thực sự chứa gì? | SQL, ydata-profiling, profiler của catalog |
| Kiểm thử khai báo | Dữ liệu có đáp ứng các quy tắc đã viết ra không? | dbt test, Great Expectations, Soda |
| Observability | Có điều gì bất thường mà chưa ai viết quy tắc không? | Monte Carlo, anomaly check của Soda, monitor mã nguồn mở |

## Data Profiling

Data profiling là việc xem xét có hệ thống cấu trúc, nội dung và quan hệ của một dataset trước khi dựa vào nó. Profiling biến giả định ("`customer_id` là duy nhất") thành sự thật đo được và là bằng chứng để viết contract và test.

**Cách hoạt động.** Profiling thường được làm qua ba lượt:

1. **Khám phá cấu trúc:** kiểu, định dạng, độ dài, và giá trị có khớp kiểu khai báo hay không (ví dụ ngày được lưu dưới dạng chuỗi).
2. **Khám phá nội dung:** tỷ lệ null, số giá trị phân biệt, min/max, phân phối, giá trị phổ biến nhất, và mẫu như định dạng email hay số điện thoại; đây cũng là lúc phát hiện PII tiềm năng.
3. **Khám phá quan hệ:** khóa ứng viên, phụ thuộc hàm, và mức khớp của khóa ngoại với bảng cha.

**Ví dụ (minh họa SQL profiling, kiểu Trino/ANSI):**

```sql
select
  count(*)                                          as row_count,
  count(distinct order_line_id)                     as distinct_line_ids,
  sum(case when customer_id is null then 1 else 0 end) * 1.0 / count(*) as customer_null_rate,
  min(order_ts)                                     as min_order_ts,
  max(order_ts)                                     as max_order_ts,
  approx_percentile(net_amount, 0.5)                as median_net_amount,
  sum(case when net_amount < 0 then 1 else 0 end)   as negative_amounts
from analytics.fct_orders
where order_date >= date '2026-10-01';
```

```sql
-- Khám phá quan hệ: tỷ lệ dòng mồ côi so với dimension khách hàng.
select count(*) as orphan_lines
from analytics.fct_orders f
left join analytics.dim_customer c on f.customer_id = c.customer_id
where c.customer_id is null;
```

**Lỗi thường gặp.** Chỉ profile một mẫu gần đây và bỏ sót trường hợp biên trong lịch sử; công bố profile kèm giá trị phổ biến thô của cột nhạy cảm; coi profile làm một lần là sự thật vĩnh viễn.

**Kiểm chứng.** Mỗi quy tắc contract phải truy về một quan sát profiling hoặc một quyết định nghiệp vụ. Profile lại sau khi hệ thống nguồn thay đổi và so sánh với profile trước.

**Vị trí trong lakehouse / Text2SQL.** Kết quả profiling (khoảng giá trị, tỷ lệ null, giá trị phân biệt của cột ít giá trị) là ngữ cảnh rất tốt cho trợ lý: nó cho mô hình biết `status` có năm giá trị hợp lệ và `net_amount` có thể âm với hàng trả lại. Loại cột nhạy cảm khỏi mọi profile được đưa vào prompt.

## Great Expectations (GX)

Great Expectations, nay được đóng gói thành **GX Core** (mã nguồn mở, Python) cùng dịch vụ thương mại GX Cloud, biểu diễn kiểm thử dữ liệu dưới dạng *Expectation*: các khẳng định có tên và tham số như "giá trị trong cột này không null" hay "giá trị nằm trong khoảng 0 đến 10.000". Expectation được gom thành suite, chạy trên các batch dữ liệu, và tạo ra kết quả validation cùng tài liệu dễ đọc ("Data Docs").

**Cách hoạt động.** Bạn cấu hình nguồn dữ liệu (pandas, Spark, hoặc SQL qua SQLAlchemy), định nghĩa batch (một bảng, một partition, một truy vấn), gắn expectation suite và chạy validation, thường qua checkpoint để kích hoạt thêm hành động như lưu kết quả hoặc gửi thông báo. API thay đổi đáng kể giữa dòng 0.x và 1.x, nên hãy ghim phiên bản và theo tài liệu của đúng phiên bản bạn cài.

**Ví dụ (minh họa, phong cách GX Core 1.x):**

```python
import great_expectations as gx
import great_expectations.expectations as gxe

context = gx.get_context()
suite = context.suites.add(gx.ExpectationSuite(name="fct_orders_contract"))
suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="order_line_id"))
suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="order_line_id"))
suite.add_expectation(gxe.ExpectColumnValuesToBeInSet(
    column="status", value_set=["placed", "paid", "shipped", "delivered", "returned"]))
suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(
    column="net_amount", min_value=-10000, max_value=100000, mostly=0.999))
```

**So sánh với Soda và dbt test.** dbt test nằm cạnh model và lý tưởng cho khóa, quan hệ và giá trị được chấp nhận trong phép biến đổi SQL. GX hợp với pipeline thiên về Python, dataframe, và team muốn tài liệu kết quả phong phú. Soda có ngôn ngữ YAML gọn và dễ chạy từ CI hoặc orchestrator. Nhiều team dùng dbt test cho logic model và một trong GX hoặc Soda ở ranh giới ingestion; tránh lặp cùng một quy tắc trong ba công cụ.

**Lỗi thường gặp.** Ngưỡng `mostly` đặt quá lỏng nên test không bao giờ fail; suite chạy trên toàn bảng mỗi lần nên ngày càng tốn kém; kết quả được lưu nhưng không cảnh báo ai; nâng cấp phiên bản âm thầm thay đổi hành vi.

**Kiểm chứng.** Tạo một batch lỗi đã biết (khóa trùng, status ngoài tập hợp) và xác nhận suite fail với đúng tên expectation mong đợi. Theo dõi thời gian chạy và chi phí.

**Vị trí trong lakehouse / Text2SQL.** Chạy GX trên batch trước khi commit vào bảng Iceberg (write-audit-publish), để trợ lý không bao giờ thấy snapshot chưa được kiểm định.

## Soda

Soda là công cụ chất lượng dữ liệu có check được viết bằng **SodaCL**, một ngôn ngữ dựa trên YAML. Soda Core (CLI và thư viện Python mã nguồn mở) thực thi check trên warehouse, lakehouse engine và dataframe; Soda Cloud bổ sung phát hiện bất thường, dashboard, workflow sự cố và tính năng contract.

**Cách hoạt động.** File cấu hình định nghĩa kết nối nguồn dữ liệu; file check liệt kê các check cho từng dataset. `soda scan` dịch check thành SQL, chạy chúng và trả về pass, warn hoặc fail cho từng check, với exit code khác 0 khi thất bại để job CI hoặc task của orchestrator có thể dừng.

**Ví dụ (minh họa file check SodaCL):**

```yaml
checks for fct_orders:
  - row_count > 0
  - duplicate_count(order_line_id) = 0
  - missing_count(customer_id) = 0
  - invalid_count(status) = 0:
      valid values: [placed, paid, shipped, delivered, returned]
  - freshness(order_ts) < 1d
  - failed rows:
      name: net amount must not exceed gross amount
      fail query: |
        select order_line_id from fct_orders where net_amount > gross_amount
  - row_count:
      warn: when < 50000
      fail: when < 10000
```

```bash
soda scan -d lakehouse -c configuration.yml checks/fct_orders.yml
```

**Phát hiện bất thường và contract.** Anomaly check học lịch sử của một chỉ số (ví dụ số dòng hằng ngày) và đánh dấu điểm ngoại lai; chúng cần đủ lịch sử và hiểu tính mùa vụ để tránh nhiễu. Tính năng contract của Soda cho phép producer khai báo schema và check chạy trong CI trước khi thay đổi được merge. Hãy xác nhận tính năng nào thuộc gói mã nguồn mở và tính năng nào thuộc dịch vụ thương mại với phiên bản bạn dùng.

**Lỗi thường gặp.** `freshness` tính trên cột có múi giờ khác với dự kiến; mẫu "failed rows" gửi dữ liệu nhạy cảm lên dashboard SaaS; ngưỡng warn không ai theo dõi.

**Kiểm chứng.** Chạy scan trên fixture chứa từng loại lỗi và khẳng định exit code cùng tên check bị fail trong CI.

**Vị trí trong lakehouse / Text2SQL.** Lưu kết quả scan cùng snapshot ID đã được kiểm định, để câu trả lời của trợ lý có thể truy về một snapshot đã qua check.

## Monte Carlo

Monte Carlo là nền tảng **data observability** thương mại. Thay vì chỉ dựa vào quy tắc do kỹ sư viết, nó thu thập metadata và query log từ warehouse, lakehouse engine, orchestrator và công cụ BI, học các mẫu bình thường, và cảnh báo về "data downtime": bảng bị cũ, khối lượng thay đổi bất ngờ, schema thay đổi, phân phối dịch chuyển và đường lineage bị đứt.

**Cách hoạt động.** Nền tảng kết nối với quyền đọc metadata và lịch sử truy vấn (và với một số monitor, quyền đọc mẫu dữ liệu hoặc giá trị tổng hợp). Nó dựng đồ thị lineage từ query log, áp dụng monitor tự động về freshness, volume và schema trên nhiều bảng, và cho phép bạn thêm quy tắc SQL tùy chỉnh cho các trường quan trọng. Sự cố gom các cảnh báo liên quan và chỉ ra nguyên nhân upstream cùng tác động downstream.

**Ví dụ (minh họa định nghĩa monitor, kiểu monitors-as-code):**

```yaml
monitors:
  - type: freshness
    table: analytics.fct_orders
    expect_update_by: "06:00 UTC daily"
    severity: high
  - type: field_health
    table: analytics.fct_orders
    fields: [net_amount, customer_id]
    metrics: [null_rate, mean, negative_rate]
  - type: custom_sql
    name: refunds_never_exceed_sales
    sql: "select count(*) from analytics.fct_orders where net_amount < -gross_amount"
    alert_when: "> 0"
notify: [sales-data-oncall]
```

**Lỗi thường gặp.** Quá tải cảnh báo do giám sát hàng nghìn bảng ít giá trị; tin quá mức vào ngưỡng học được sau một thay đổi nghiệp vụ hợp lệ; cấp cho nhà cung cấp quyền truy cập dữ liệu rộng hơn cần thiết; không định tuyến tới chủ sở hữu nên sự cố ai cũng thấy mà không ai xử lý.

**Kiểm chứng.** Theo dõi độ chính xác (tỷ lệ cảnh báo là vấn đề thật) và thời gian phát hiện sự cố. Rà soát quyền truy cập mà nền tảng nắm giữ theo nguyên tắc đặc quyền tối thiểu.

**Vị trí trong lakehouse / Text2SQL.** Observability bắt được những lỗi không ai dự đoán. Đưa các sự cố đang mở vào trạng thái của trợ lý để nó có thể cảnh báo "dữ liệu đơn hàng hôm nay bị trễ" thay vì tự tin trả lời từ lần nạp dở dang hôm qua. Nếu không có nền tảng thương mại, có thể dựng năng lực tương đương bằng monitor mã nguồn mở cộng với OpenLineage.

## Data Consistency

Tính nhất quán dữ liệu có hai nghĩa liên quan, và cả hai đều quan trọng trong nền tảng dữ liệu:

1. **Nhất quán ở mức hệ thống:** người đọc thấy phiên bản dữ liệu nào khi dữ liệu được nhân bản hoặc cập nhật đồng thời. Với *strong consistency*, mọi lần đọc đều thấy lần ghi đã commit mới nhất; với *eventual consistency*, các bản sao hội tụ theo thời gian và người đọc có thể tạm thấy dữ liệu cũ. Định lý CAP phát biểu rằng khi xảy ra phân vùng mạng, hệ thống phân tán phải chọn giữa tính nhất quán và tính sẵn sàng.
2. **Nhất quán về ngữ nghĩa:** cùng một sự kiện có cùng giá trị giữa các bảng, hệ thống và báo cáo (ví dụ doanh thu trong mart bằng doanh thu trong sổ cái tài chính cho cùng kỳ).

**Cách hoạt động trong lakehouse.** Iceberg cung cấp *snapshot isolation* cho từng bảng: một commit đổi con trỏ metadata một cách nguyên tử trong catalog, và người đọc thấy snapshot cũ hoặc mới, không bao giờ lẫn lộn. Các object store lớn hiện cung cấp strong read-after-write consistency cho object (Amazon S3 đã làm vậy từ cuối năm 2020), giúp mọi thứ đơn giản hơn. Tuy nhiên, tính nhất quán giữa *nhiều* bảng không tự động có: dashboard join `fct_orders` (đã làm mới) với `dim_customer` (chưa làm mới) có thể cho kết quả không nhất quán. Bản sao CDC và cache còn thêm độ trễ.

**Ví dụ (minh họa đối soát giữa các hệ thống):**

```sql
-- Nhất quán ngữ nghĩa: mart so với sổ cái cho kỳ đã khóa, dung sai 0.01.
select
  m.period,
  m.revenue as mart_revenue,
  l.revenue as ledger_revenue,
  abs(m.revenue - l.revenue) as diff
from analytics.monthly_revenue m
join finance.ledger_monthly l using (period)
where m.period = '2026-10'
  and abs(m.revenue - l.revenue) > 0.01;
```

**Lỗi thường gặp.** Người đọc truy vấn bản sao có độ trễ không xác định; bảng dimension và fact được công bố ở các thời điểm khác nhau; cache tiếp tục phục vụ giá trị sau khi đã sửa; báo cáo dựng từ các snapshot khác nhau của cùng một bảng.

**Kiểm chứng.** Công bố các bảng liên quan cùng nhau (ví dụ gắn nhãn một tập snapshot ID nhất quán, hoặc dùng workflow branch-and-merge), ghi lại độ trễ bản sao, và chạy đối soát cho các kỳ đã khóa.

**Vị trí trong lakehouse / Text2SQL.** Cho trợ lý ghi lại snapshot ID hoặc mốc thời gian dữ liệu nó đã truy vấn và hiển thị "dữ liệu tính đến" trong câu trả lời, để có thể giải thích khi hai câu trả lời khác nhau.

## Bài tập

1. Profile `fct_orders` (hoặc mart của Project 1) qua ba lượt và viết ba quy tắc contract có căn cứ từ profile.
2. Cài đặt cùng ba quy tắc đó một lần bằng dbt test và một lần bằng GX hoặc Soda. Quyết định giữ cách nào và ghi lại lý do.
3. Tạo một batch lỗi có khóa trùng, status không hợp lệ và timestamp cũ. Xác nhận mỗi công cụ báo cáo từng lỗi riêng biệt và trả về exit code thất bại.
4. Viết monitor freshness và volume có định tuyến tới chủ sở hữu; mô phỏng một lần nạp trễ và đo thời gian phát hiện.
5. Chạy truy vấn đối soát cho một kỳ đã khóa và ghi lại dung sai cùng người phê duyệt ngoại lệ.

### Tiêu chí hoàn thành

- Mỗi check được giữ lại truy về một quan sát profiling hoặc quy tắc nghiệp vụ, và không quy tắc nào bị lặp giữa các công cụ mà không có lý do.
- Một check thất bại chặn việc công bố snapshot bị ảnh hưởng, và trợ lý không thể đọc snapshot bị chặn.
- Cảnh báo tới được một chủ sở hữu cụ thể, và bạn báo cáo được thời gian phát hiện trong bài mô phỏng.
- Câu trả lời của trợ lý có mốc "dữ liệu tính đến" hoặc tham chiếu snapshot.
