---
title: "Kiểm soát truy cập: RBAC, bảo mật cấp dòng và cấp cột"
description: Nối danh tính liên kết (federated identity) với vai trò, lọc dòng và bảo vệ cột tại nơi truy vấn thực thi, và chọn giữa masking tĩnh và động.
order: 22
tags: [bảo mật, kiểm soát truy cập, rbac, row-level security, column-level security, masking, danh tính]
---

# Kiểm soát truy cập: RBAC, bảo mật cấp dòng và cấp cột

Kiểm soát truy cập trả lời ba câu hỏi cho mọi yêu cầu: **ai** đang hỏi (danh tính), họ được chạm vào **cái gì** (bảng, dòng, cột), và quyết định được cưỡng chế **ở đâu** (catalog, engine, công cụ BI, storage). Trong lakehouse, câu hỏi cuối là khó nhất, vì cùng một bộ file Parquet có thể được đọc bởi nhiều engine và bởi bất kỳ ai nắm credential của storage.

Giả định cho các ví dụ: một identity provider (IdP) như Microsoft Entra ID hoặc Okta, một Iceberg REST catalog có thể cấp (vend) credential storage ngắn hạn, Trino và Spark làm engine, và một trợ lý Text2SQL bắt buộc chạy truy vấn *với danh tính của người dùng cuối*, không bao giờ dùng một superuser chung. Xem thêm [Cơ bản về lưu trữ Cloud và quyền truy cập](cloud-storage-and-access.html).

## Federated Identity

Federated identity cho phép người dùng xác thực một lần với một identity provider đáng tin cậy và dùng danh tính đó trên nhiều hệ thống; các hệ thống này tin vào khẳng định đã ký của IdP thay vì tự quản lý mật khẩu.

**Cách hoạt động.** Các giao thức như SAML 2.0 và OpenID Connect (OIDC) mang token đã ký chứa định danh người dùng và nhóm họ thuộc về. SCIM cấp và thu hồi người dùng, nhóm xuống các hệ thống downstream. Workload identity federation áp dụng cùng ý tưởng cho máy: một job CI hoặc pod Kubernetes trình token OIDC và nhận credential cloud ngắn hạn thay vì dùng access key được lưu sẵn.

**Ví dụ (minh họa ánh xạ nhóm sang vai trò):**

```yaml
idp_groups_to_roles:
  grp-sales-analysts:      [analyst_sales]
  grp-finance-analysts:    [analyst_finance]
  grp-privacy-approved:    [pii_reader]
  grp-data-engineers:      [engineer_dev]          # production write only via pipeline identity
workload_identities:
  github-actions:repo:org/pipelines:ref:refs/heads/main: [pipeline_prod_writer]
```

**Lỗi thường gặp.** Claim nhóm không được làm mới nên người đã đổi team vẫn giữ quyền cũ tới lần đăng nhập sau; tài khoản cục bộ tạo ra như giải pháp "tạm thời" rồi không bao giờ xóa; service account dùng key dài hạn; trợ lý xác thực bằng một service identity duy nhất cho mọi người dùng.

**Kiểm chứng.** Thu hồi một người dùng thử trong IdP và xác nhận quyền bị gỡ khỏi catalog, engine và BI trong thời gian đã thống nhất. Kiểm kê tài khoản và key không liên kết với IdP hằng tháng.

**Vị trí trong lakehouse / Text2SQL.** Trợ lý nên chuyển token của người dùng (hoặc token được đổi thay mặt người dùng) tới engine để mọi truy vấn được phân quyền và audit dưới đúng người thật.

## Role-Based Access Control (RBAC)

Role-based access control cấp quyền cho **vai trò (role)** và gán vai trò cho người dùng hoặc nhóm. Người dùng không bao giờ nhận quyền trực tiếp, nhờ đó quyền truy cập có thể rà soát: câu hỏi "ai đọc được `fct_orders`?" trở thành "những vai trò nào có `SELECT`, và ai giữ các vai trò đó?"

**Cách hoạt động.** Vai trò gom các đặc quyền trên đối tượng bảo mật (catalog, schema, bảng, view, hàm). Vai trò có thể kế thừa từ vai trò khác. Ví dụ trong Apache Polaris, *principal role* được gán cho danh tính và được cấp *catalog role* nắm quyền trên namespace và bảng; engine lấy bảng qua catalog chỉ nhận được những gì vai trò của người gọi cho phép. Attribute-based access control (ABAC) mở rộng RBAC bằng điều kiện dựa trên tag hoặc thuộc tính người dùng, và mở rộng tốt hơn khi có nhiều bảng.

**Ví dụ (minh họa câu lệnh grant, kiểu Trino/ANSI):**

```sql
create role analyst_sales;
create role pii_reader;

grant select on analytics.fct_orders   to role analyst_sales;
grant select on analytics.dim_customer to role analyst_sales;   -- masked columns, see below
grant select on analytics.dim_customer_pii to role pii_reader;

grant analyst_sales to user "maria@example.com";
-- Prefer granting to IdP groups where the engine supports it.
```

**Lỗi thường gặp.** Bùng nổ vai trò (mỗi người một vai trò); một vai trò `analyst` rộng tích lũy mọi quyền; cấp quyền trên schema nên bảng mới tự động bị lộ, kể cả bảng nhạy cảm; vai trò được định nghĩa khác nhau ở mỗi engine.

**Kiểm chứng.** Xuất danh sách grant định kỳ và so với ma trận truy cập đã duyệt; chạy kiểm thử truy vấn được phép và bị từ chối cho mỗi vai trò; tổ chức rà soát quyền định kỳ với chủ sở hữu.

**Vị trí trong lakehouse / Text2SQL.** Không cấp cho trợ lý đặc quyền riêng nào ngoài quyền đọc metadata. Quyền hiệu lực của nó là giao giữa vai trò của người dùng và allow-list bảng certified của trợ lý.

## Row-Level Security

Row-level security (RLS) lọc những dòng người dùng được thấy trong một bảng, dựa trên việc họ là ai. Quản lý khu vực truy vấn `fct_orders` chỉ thấy các dòng thuộc khu vực của mình, với cùng câu SQL như mọi người.

**Cách hoạt động.** Một chính sách (row filter) được gắn vào bảng và engine đánh giá nó lúc truy vấn, thường bằng cách so sánh một cột với thuộc tính của người dùng hiện tại hoặc với một bảng ánh xạ. Cách cài đặt khác nhau: PostgreSQL có `CREATE POLICY`; Snowflake có row access policy; Databricks Unity Catalog có hàm row filter; Trino dựa vào plugin kiểm soát truy cập (ví dụ Apache Ranger hoặc Open Policy Agent); một số catalog đang bổ sung định nghĩa chính sách để engine tải về.

**Ví dụ (minh họa, PostgreSQL — chạy được cục bộ):**

```sql
create table sales_orders (order_id bigint, region text, net_amount numeric);
create table user_regions (username text, region text);

alter table sales_orders enable row level security;

create policy region_filter on sales_orders
  for select
  using (region in (select region from user_regions where username = current_user));
```

```sql
-- Kiểm thử với hai người dùng: mỗi người chỉ thấy khu vực của mình; người không có ánh xạ thấy 0 dòng.
set role maria;  select distinct region from sales_orders;   -- kỳ vọng: EU
set role tuan;   select distinct region from sales_orders;   -- kỳ vọng: APAC
```

**Cưỡng chế ở đâu, và bị vượt qua thế nào.** RLS chỉ mạnh bằng đường dẫn tới dữ liệu. Nếu catalog cấp credential storage để engine đọc trực tiếp file Parquet, bất kỳ engine hay script nào nắm credential đó đều đọc được mọi dòng; bộ lọc chỉ tồn tại trong engine tôn trọng chính sách. Biện pháp giảm thiểu: chỉ cấp credential cho engine tin cậy có cưỡng chế chính sách, giới hạn credential ở prefix tối thiểu, chặn con người truy cập bucket trực tiếp, hoặc công bố bảng/view đã lọc sẵn cho engine không cưỡng chế được bộ lọc.

**Lỗi thường gặp.** Kiểm thử bằng chủ sở hữu bảng hoặc superuser, những người bỏ qua RLS của PostgreSQL trừ khi đặt `force row level security`; bảng ánh xạ thiếu khiến người dùng không thấy gì (hoặc, với chính sách viết sai, thấy tất cả); bộ lọc đặt trên view mà người dùng có thể vượt qua bằng cách truy vấn bảng gốc; aggregate hoặc cache được tính bằng danh tính đặc quyền rồi chia sẻ cho mọi người; hiệu năng giảm vì subquery chính sách phức tạp.

**Kiểm chứng.** Duy trì ma trận kiểm thử người dùng × số dòng kỳ vọng theo khu vực, gồm cả một người dùng không có ánh xạ; chạy trên mọi engine đọc được bảng; thử đọc storage trực tiếp bằng credential mà người dùng có thể lấy được.

**Vị trí trong lakehouse / Text2SQL.** Vì trợ lý chạy với danh tính người dùng, RLS tự động giới hạn phạm vi câu hỏi như "tổng doanh số". Câu trả lời nên nói rõ phạm vi ("cho các khu vực bạn được truy cập: EU") để tổng một phần không bị nhầm thành tổng toàn công ty.

## Column-Level Security

Column-level security (CLS) kiểm soát những cột người dùng được đọc. Một analyst hỗ trợ khách hàng thấy `customer_id` và `country` nhưng không thấy `email` hay `date_of_birth`.

**Cách hoạt động.** Có hai kiểu. *Grant theo cột* chặn hoàn toàn quyền truy cập cột, nên `select *` thất bại hoặc bỏ cột đó. *Chính sách cột* (masking động) cho truy vấn chạy nhưng trả về giá trị đã che với người không có quyền, tránh làm hỏng truy vấn và dashboard. Chính sách theo tag gắn quy tắc masking cho mọi cột mang tag, ví dụ `pii.email`, giúp chính sách luôn tập trung khi số bảng tăng.

**Ví dụ (minh họa, quyền theo cột trong PostgreSQL):**

```sql
revoke select on dim_customer from analyst_sales;
grant select (customer_id, country, signup_date, segment) on dim_customer to analyst_sales;
-- select email from dim_customer;  -> permission denied for analyst_sales
```

**Lỗi thường gặp.** Một view làm lộ cột mà không có chính sách; cột phái sinh (như `email_domain` hoặc hash của email) làm rò rỉ giá trị được bảo vệ; bản xuất và extract do job đặc quyền tạo ra; cột được bảo vệ trong warehouse nhưng vẫn có trong extract BI hoặc vector index.

**Kiểm chứng.** Với mọi cột có tag nhạy cảm, xác nhận có chính sách hoặc grant; chạy kiểm thử bằng vai trò không có đặc quyền; quét bảng phái sinh và index để tìm bản sao của giá trị được bảo vệ.

**Vị trí trong lakehouse / Text2SQL.** Loại cột được bảo vệ khỏi ngữ cảnh schema mà trợ lý thấy trừ khi người dùng được phép. Nếu không, mô hình có thể đề xuất truy vấn thất bại, hoặc tệ hơn, nêu tên trường nhạy cảm trong lời giải thích.

## Data Masking

Data masking thay giá trị nhạy cảm bằng giá trị thay thế trông thực tế nhưng không nhạy cảm, để con người và hệ thống làm việc với dữ liệu mà không thấy giá trị thật.

**Tĩnh và động.**

| Khía cạnh | Masking tĩnh | Masking động |
|---|---|---|
| Khi nào áp dụng | Một lần, khi tạo bản sao (ví dụ dataset dev) | Lúc truy vấn, theo người dùng hoặc vai trò |
| Dữ liệu được lưu | Bản sao đã che; bản gốc ở nơi khác | Lưu bản gốc; masking trong engine |
| Phù hợp cho | Môi trường non-production, chia sẻ extract | Phân tích production với nhiều nhóm người dùng |
| Rủi ro | Bản sao bị lệch; masking có thể đảo ngược nếu làm kém | Bị vượt qua qua engine hoặc đường storage không được bảo vệ |

Kỹ thuật phổ biến: che hẳn (`****`), hiện một phần (bốn số cuối), thay thế giữ định dạng, hash (nhất quán nhưng liên kết được), xáo trộn trong cột, và dịch chuyển ngày. Masking không phải [anonymization](privacy-and-pii-protection.html#data-anonymization): dữ liệu đã che thường vẫn nhận diện được người khi kết hợp với cột khác.

**Ví dụ (minh họa chính sách masking động kiểu Snowflake):**

```sql
create masking policy email_mask as (val string) returns string ->
  case
    when is_role_in_session('PII_READER') then val
    else regexp_replace(val, '^[^@]+', '***')     -- ***@example.com
  end;

alter table analytics.dim_customer modify column email set masking policy email_mask;
```

**Lỗi thường gặp.** Hash không có salt của giá trị ít entropy (số điện thoại) có thể bị đảo ngược bằng brute force; masking làm hỏng join vì hai bảng che theo cách khác nhau; bản sao dev đã che được làm mới từ production mà không chạy lại masking; log và thông báo lỗi chứa giá trị chưa che.

**Kiểm chứng.** Truy vấn bằng vai trò không đặc quyền và có đặc quyền rồi so sánh; thử đảo ngược một mẫu hash bằng từ điển; quét bản sao non-production bằng công cụ phát hiện PII để tìm giá trị thật.

**Vị trí trong lakehouse / Text2SQL.** Không bao giờ gửi giá trị đã che cho LLM như thể đó là giá trị thật: nếu trợ lý hiển thị dòng mẫu, hãy dùng view đã che và gắn nhãn rõ.

## Bài tập

1. Viết ma trận truy cập cho ba nhóm IdP và bốn bảng, rồi cài đặt thành vai trò và grant.
2. Trong PostgreSQL, cài đặt ví dụ RLS với hai người dùng và một người dùng không có ánh xạ; lưu lại kết quả kiểm thử.
3. Thêm chính sách cột hoặc masking cho `email` và `date_of_birth`; chứng minh vai trò không đặc quyền nhận kết quả bị che hoặc bị từ chối.
4. Liệt kê mọi đường tới file bên dưới (engine, notebook, credential được cấp, extract BI) và đánh dấu nơi RLS và CLS được cưỡng chế.
5. Cấu hình trợ lý chạy truy vấn bằng danh tính người dùng và hiển thị phạm vi của mỗi câu trả lời.

### Tiêu chí hoàn thành

- Có kiểm thử được phép và bị từ chối cho mọi vai trò và chúng chạy tự động.
- Không danh tính con người nào đọc trực tiếp được file lakehouse trong production, hoặc ngoại lệ được ghi rõ kèm biện pháp kiểm soát bù.
- Thu hồi người dùng trong IdP gỡ quyền ở mọi nơi trong thời gian đã thống nhất.
- Truy vấn của trợ lý xuất hiện trong audit log dưới danh tính người dùng cuối, và câu trả lời có giới hạn phạm vi nói rõ điều đó.
