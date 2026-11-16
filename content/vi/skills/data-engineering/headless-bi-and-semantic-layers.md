---
title: Headless BI và semantic layer phổ quát
description: Định nghĩa metric một lần, bên ngoài mọi dashboard riêng lẻ, rồi phục vụ cùng một logic cho công cụ BI, API và trợ lý AI.
order: 40
tags: [headless BI, semantic layer, metric store, universal semantic layer, Looker, LookML, MetricFlow]
---

# Headless BI và semantic layer phổ quát

Phần lớn bất đồng về metric không phải lỗi SQL. Chúng xảy ra vì "doanh thu" được định nghĩa ba lần: một lần trong calculated field của Tableau, một lần trong measure của Power BI và một lần trong notebook. Bài này trình bày lời giải về kiến trúc — đưa định nghĩa ra khỏi công cụ hiển thị, vào một lớp dùng chung có phiên bản — cùng công cụ đã đưa ý tưởng này trở nên phổ biến.

Hãy đọc [Semantic layer](../ai/semantic-layer.html) trước để nắm từ vựng cốt lõi (entity, dimension, measure, grain). Trang này tập trung vào việc lớp đó nằm ở đâu và ai truy vấn nó.

## Headless BI

**Là gì.** Headless BI tách "phần đầu" (biểu đồ, dashboard, giao diện chat) khỏi "phần thân" (định nghĩa metric, đường join, quy tắc truy cập, cache). Phần thân chạy như một dịch vụ. Bất kỳ "đầu" nào — công cụ BI, bảng tính, ứng dụng nội bộ, trợ lý dùng LLM — đều hỏi dịch vụ đó `paid_revenue theo region cho tháng trước` thay vì tự viết SQL.

**Cách hoạt động.**

1. Kỹ sư khai báo entity, dimension, measure và metric bằng mã (YAML, LookML hoặc DSL tương tự) lưu trong Git.
2. Dịch vụ semantic biên dịch yêu cầu metric thành SQL cho warehouse hoặc engine lakehouse bên dưới, tự chọn đường join và time grain dựa trên khai báo.
3. Bên tiêu thụ truy cập qua một hoặc nhiều giao diện: SQL qua JDBC/ODBC hoặc Arrow Flight SQL, API REST hoặc GraphQL, hay connector gốc cho từng công cụ BI.
4. Quy tắc truy cập (lọc dòng, che cột) và cache hoặc pre-aggregation được áp dụng trong dịch vụ, nên mọi "đầu" đều thừa hưởng.

Thuật ngữ **metric store** thường dùng cho cùng ý tưởng, nhưng nhấn mạnh vào danh mục định nghĩa metric và API của nó hơn là mô hình hóa toàn bộ dataset. Trên thực tế, "headless BI", "metric store" và "semantic layer" chồng lấn nhiều; hãy hỏi mỗi sản phẩm thực sự biên dịch, cache và thực thi những gì.

**Ví dụ cụ thể (minh họa, kiểu dbt MetricFlow; kiểm tra spec theo phiên bản bạn dùng).**

```yaml
semantic_models:
  - name: orders
    model: ref('fct_orders')          # grain: mỗi dòng một đơn hàng
    defaults:
      agg_time_dimension: paid_at
    entities:
      - name: order_id
        type: primary
      - name: customer
        type: foreign
        expr: customer_id
    dimensions:
      - name: paid_at
        type: time
        type_params:
          time_granularity: day       # ngày nghiệp vụ theo UTC
      - name: region
        type: categorical
    measures:
      - name: paid_revenue_usd
        agg: sum
        expr: case when payment_status = 'paid' then amount_usd else 0 end

metrics:
  - name: paid_revenue
    label: Paid revenue (USD)
    description: Tổng giá trị đơn đã thanh toán tính bằng USD, không gồm hoàn tiền, theo ngày thanh toán (UTC).
    type: simple
    type_params:
      measure: paid_revenue_usd
```

Một yêu cầu headless cho metric này trông giống nhau bất kể ai gửi, ví dụ `metrics=[paid_revenue], group_by=[region, metric_time__month], where=metric_time >= '2026-10-01'`. Dịch vụ, chứ không phải bên gọi, quyết định cách join và tổng hợp.

**Kiểu lỗi.**

- *Đi vòng*: analyst vẫn nối công cụ BI thẳng vào mart và dựng lại measure tại chỗ, nên "định nghĩa duy nhất" chỉ là một trong nhiều định nghĩa.
- *Mẫu số chung nhỏ nhất*: connector của công cụ BI không biểu diễn được một bộ lọc hoặc time grain mà lớp semantic hỗ trợ, nên công cụ âm thầm xấp xỉ.
- *Độ trễ bất ngờ*: thêm một bước mạng và bước biên dịch SQL làm mỗi ô dashboard chậm thêm vài giây nếu cache chưa được tinh chỉnh.
- *Join mơ hồ*: hai đường join hợp lệ giữa các entity cho ra tổng khác nhau (fan-out), và lớp semantic lặng lẽ chọn một.
- *Khoảng trống sở hữu*: metric là "của chung", nên không ai duyệt thay đổi.

**Kiểm định.**

- Chạy mỗi metric cốt lõi qua mọi bên tiêu thụ (dashboard, API, trợ lý) cho một kỳ cố định và so với fixture tính tay.
- Làm CI thất bại khi định nghĩa metric thay đổi mà không có người duyệt từ domain sở hữu.
- Xem SQL được sinh cho một mẫu yêu cầu; kiểm tra khóa join và grain.
- Theo dõi tỷ lệ truy vấn BI đi qua lớp semantic so với truy cập bảng trực tiếp.

**Liên hệ với trợ lý phân tích có quản trị.** Trong [Dự án 2](../../projects/project-2-text2sql-chatbot.html), thiết kế an toàn nhất là để trợ lý chọn metric, dimension và bộ lọc, rồi nhờ semantic layer biên dịch SQL. Mô hình không bao giờ tự nghĩ ra công thức doanh thu; nó chỉ chọn từ các định nghĩa đã được duyệt. Headless BI là thứ khiến câu trả lời của trợ lý khớp với dashboard.

## Universal Semantic Layer

**Là gì.** Universal semantic layer (semantic layer phổ quát) là một semantic layer headless nhắm tới việc phục vụ *mọi* bên tiêu thụ trong tổ chức — nhiều công cụ BI, bảng tính, notebook, ứng dụng và AI agent — trên một hoặc nhiều engine vật lý. "Phổ quát" là mục tiêu thiết kế, không phải bảo đảm: nó có nghĩa là lớp này độc lập với bất kỳ nhà cung cấp BI nào.

**Cách hoạt động.** Nó kết hợp bốn năng lực:

| Năng lực | Mang lại gì | Câu hỏi cần đặt cho sản phẩm |
|---|---|---|
| Mô hình hóa | Entity, join, measure, metric, hierarchy bằng mã | Có biểu diễn đúng tỷ lệ, measure bán cộng dồn (semi-additive) và metric lũy kế theo thời gian không? |
| Giao diện truy vấn | SQL, REST/GraphQL, endpoint tương thích MDX hoặc DAX, connector riêng cho BI | Công cụ BI *của chúng ta* nào dùng được nguyên bản, công cụ nào mất tính năng? |
| Hiệu năng | Cache, bảng aggregate, viết lại truy vấn | Aggregate được làm mới và vô hiệu hóa thế nào khi dữ liệu đổi? |
| Quản trị | Bảo mật dòng/cột, lineage, trạng thái chứng nhận | Có truyền danh tính người dùng xuống engine không, hay dùng chung một service account? |

Ví dụ các sản phẩm định vị trong mảng này gồm dbt Semantic Layer (MetricFlow), Cube, AtScale và các tính năng semantic trong engine lakehouse như virtual dataset của Dremio. Năng lực thay đổi nhanh; hãy đánh giá dựa trên danh sách bên tiêu thụ của chính bạn.

**Ví dụ cụ thể (ma trận bên tiêu thụ, minh họa).** Trước khi áp dụng, hãy liệt kê mọi bên tiêu thụ và giao diện mà nó sẽ dùng:

```text
consumer                interface            identity passed?  features lost
Tableau dashboards      JDBC/SQL connector   yes (OAuth)       custom period-over-period calc
Power BI reports        vendor connector     service account!  RLS must be re-implemented
Finance Excel models    ODBC                 yes               none
Analytics assistant     REST metric API      yes (end user)    none
Product app widget      GraphQL              app token         per-customer filter enforced in app
```

Dòng "service account!" là rủi ro cần sửa: nếu lớp semantic không thấy người dùng cuối, quy tắc theo dòng không thể áp dụng ở đó.

**Kiểu lỗi.** Hứa hẹn tính phổ quát mà không thử từng connector; một credential dùng chung xóa bỏ bảo mật theo người dùng; bảng aggregate trả số cũ sau khi backfill; lớp semantic thành nút thắt do một nhóm quá tải sở hữu.

**Kiểm định.** Duy trì bộ kiểm tra nhất quán: với mỗi metric được chứng nhận, cùng một yêu cầu qua mọi giao diện phải trả về cùng giá trị (trong một sai số đã ghi rõ cho làm tròn tiền tệ). Chạy lại sau mỗi lần phát hành semantic model và sau mỗi backfill upstream.

**Liên hệ với trợ lý phân tích có quản trị.** Hãy coi trợ lý là một bên tiêu thụ nữa trong ma trận, với yêu cầu khắt khe nhất: danh tính theo từng người dùng, provenance đầy đủ (tên metric, phiên bản, SQL được sinh) và từ chối khi câu hỏi cần một metric chưa được định nghĩa.

## Looker

**Là gì.** Looker là nền tảng BI, thuộc Google Cloud từ năm 2020, xây quanh **LookML**, một ngôn ngữ mô hình hóa dạng mã. Analyst viết view (bảng và các trường của nó), explore (điểm xuất phát có thể join để đặt câu hỏi) và model (tập hợp explore và kết nối). Looker sinh SQL lúc truy vấn và chạy trong cơ sở dữ liệu của khách hàng; nó không bắt buộc trích dữ liệu vào engine riêng. Đây là ví dụ sớm và phổ biến của mô hình "định nghĩa một lần bằng mã, tái sử dụng khắp nơi" — mô hình mà headless BI tổng quát hóa. (Looker Studio, trước đây là Data Studio, là một sản phẩm khác, nhẹ hơn.)

**Cách hoạt động.** File LookML nằm trong một repository Git nối với instance Looker. Lập trình viên làm việc ở development mode trên một nhánh, kiểm định model rồi triển khai lên production. Người dùng khám phá qua bộ chọn trường; Looker ghép SQL từ các join đã khai báo. Persistent derived table (PDT) có thể vật chất hóa kết quả trung gian tốn kém. Google cũng đã mở semantic model của Looker cho công cụ khác (ví dụ qua connector và giao diện SQL), đưa Looker tiến một phần tới vai trò headless — hãy kiểm tra khả năng hiện có với phiên bản của bạn.

**Ví dụ cụ thể (LookML minh họa).**

```text
view: fct_orders {
  sql_table_name: analytics.fct_orders ;;

  dimension: order_id {
    primary_key: yes
    type: string
    sql: ${TABLE}.order_id ;;
  }
  dimension_group: paid {
    type: time
    timeframes: [date, week, month]
    sql: ${TABLE}.paid_at ;;          # lưu theo UTC
  }
  dimension: region {
    type: string
    sql: ${TABLE}.region ;;
  }
  measure: paid_revenue {
    type: sum
    sql: ${TABLE}.amount_usd ;;
    filters: [payment_status: "paid"]
    value_format_name: usd
    description: "Giá trị đơn đã thanh toán (USD), không gồm hoàn tiền."
  }
}

explore: fct_orders {
  access_filter: {
    field: fct_orders.region
    user_attribute: allowed_region
  }
}
```

**Kiểu lỗi.** Join khai báo sai `relationship` gây fan-out (symmetric aggregate của Looker giảm thiểu nhiều nhưng không phải mọi trường hợp); explore phình to phơi ra hàng trăm trường khó hiểu; PDT âm thầm không build lại; sửa trực tiếp trên production không qua code review; lại nhân đôi logic metric trong công cụ BI khác vì chúng không đọc được LookML.

**Kiểm định.** Chạy LookML validator và content validator trong CI trước khi triển khai; viết LookML data test khẳng định giá trị đã biết cho kỳ cố định; xem tab SQL của explore mới; theo dõi log build PDT.

**Liên hệ với trợ lý phân tích có quản trị.** Nếu tổ chức đã duy trì LookML, đó là danh sách measure, dimension và join hợp lệ đã được duyệt sẵn. Trợ lý có thể dùng metadata đó làm catalog — nhưng chỉ khi user attribute và access filter được áp dụng cho truy vấn của trợ lý y như trong Looker.

## Chọn nơi đặt định nghĩa

| Tình huống | Mặc định hợp lý |
|---|---|
| Một công cụ BI, nhóm nhỏ | Mô hình hóa trong semantic model của công cụ đó; ghi rõ giới hạn |
| Nhiều công cụ BI hoặc có trợ lý AI | Semantic layer headless hoặc phổ quát trong Git |
| Đã chuẩn hóa trên Looker | Giữ LookML làm nguồn; kiểm tra bên tiêu thụ khác đọc được gì từ nó |
| Cần metric trong ứng dụng vận hành | API semantic layer cộng reverse ETL (xem [Reverse ETL và kích hoạt dữ liệu](reverse-etl-and-activation.html)) |

## Bài tập

1. Viết `paid_revenue`, `active_customers` (số khách hàng phân biệt có đơn đã thanh toán trong kỳ) và `average_order_value` (một tỷ lệ, không phải trung bình của các trung bình) trong file YAML kiểu MetricFlow.
2. Lập ma trận bên tiêu thụ cho ba bên bạn có thể chạy cục bộ (ví dụ Metabase, một client API Python và trợ lý của bạn).
3. Viết kiểm tra nhất quán yêu cầu `paid_revenue theo region` cho tháng 10/2026 qua hai bên tiêu thụ và so kết quả với fixture.
4. Cố ý làm hỏng: thêm join từ orders sang order items và quan sát doanh thu có bị fan-out không.

**Tiêu chí hoàn thành.**

- Ba định nghĩa metric đã duyệt, có grain, mốc thời gian, đơn vị và chủ sở hữu.
- Ma trận bên tiêu thụ đánh dấu việc truyền danh tính và tính năng bị mất cho từng bên.
- Kiểm tra nhất quán đạt trên dữ liệu đúng và thất bại khi có thay đổi gây fan-out.
- Ghi chú ngắn giải thích trợ lý chọn metric thay vì tự viết công thức như thế nào.
