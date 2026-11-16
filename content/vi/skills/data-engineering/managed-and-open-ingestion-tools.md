---
title: Công cụ ingestion managed và mã nguồn mở
description: So sánh Airbyte, Fivetran và dlt khi nạp dữ liệu SaaS và database vào warehouse và Iceberg, và kiểm chứng điều mỗi công cụ thực sự bảo đảm.
order: 33
tags: [ingestion, Airbyte, Fivetran, dlt, ELT, connectors, Iceberg, Python]
---

# Công cụ ingestion managed và mã nguồn mở

Phần lớn đội ngũ không nên tự viết connector cho từng API SaaS và database. Công cụ connector xử lý xác thực, phân trang, trạng thái incremental, ánh xạ schema và retry. Chúng không loại bỏ nhu cầu định nghĩa khóa, delete, độ tươi và đối soát; chúng chỉ chuyển các quyết định đó vào cấu hình.

Giả định: nguồn là một API CRM và một database PostgreSQL; đích là warehouse hoặc bảng Iceberg trên object storage. Tên tính năng, đích hỗ trợ và mô hình giá thay đổi thường xuyên. Cấu hình bên dưới chỉ mang tính **minh họa**: hãy đối chiếu tài liệu hiện hành và thử với dữ liệu của chính bạn trước khi cam kết.

## Airbyte

**Là gì.** Airbyte là nền tảng tích hợp dữ liệu mã nguồn mở với danh mục lớn source và destination connector. Có thể tự host hoặc dùng dịch vụ cloud managed.

**Cách hoạt động.**

- Một **connection** nối source với destination kèm lịch chạy và tập stream được chọn (bảng hoặc tài nguyên API).
- Mỗi stream dùng một **sync mode**: full refresh (overwrite hoặc append) hoặc incremental (append, hoặc append + deduped dựa trên primary key và cursor field).
- Connector chạy dưới dạng container tuân theo một giao thức chung, nên connector được cô lập và thay thế được. Connector API mới có thể xây bằng connector builder low-code hoặc Python CDK.
- Airbyte thêm các cột metadata như raw record ID, timestamp trích xuất và metadata theo record về lỗi hoặc cắt bớt, giúp khử trùng và audit.
- Với lakehouse, Airbyte có các destination ghi bảng Apache Iceberg lên object storage kèm catalog (kiểm tra catalog nào được hỗ trợ và destination bạn chọn có dedup/upsert hay không).

**Ví dụ lựa chọn cấu hình (minh họa).**

| Stream | Sync mode | Cursor | Primary key | Lý do |
|---|---|---|---|---|
| `crm.contacts` | Incremental, append + deduped | `updated_at` | `id` | Trạng thái hiện tại, theo kịp chỉnh sửa |
| `crm.email_events` | Incremental, append | `occurred_at` | `event_id` | Event bất biến |
| `crm.pipelines` | Full refresh, overwrite | không | `id` | Bảng tham chiếu nhỏ, thấy được bản ghi bị xóa |

**Kiểu lỗi.** Sync incremental dựa trên cursor bỏ sót hard delete nếu nguồn không lộ ra; record được cập nhật mà không đổi `updated_at` bị bỏ sót; nâng cấp phiên bản connector có thể thay đổi ánh xạ schema; bản tự host là trách nhiệm của bạn về vá lỗi, mở rộng và giám sát.

## Fivetran

**Là gì.** Fivetran là dịch vụ ELT managed: vận hành connector cho ứng dụng SaaS, database, file và event, và nạp dữ liệu vào warehouse và data lake với rất ít cấu hình.

**Cách hoạt động.**

- Bạn cấp quyền cho nguồn và chọn đích; Fivetran xử lý trích xuất, sync incremental (thường là CDC dựa trên log với database), tạo schema và thay đổi schema theo chính sách bạn đặt (cho phép tất cả, chỉ cho phép cột, hoặc chặn schema mới).
- Fivetran thêm các cột hệ thống như timestamp sync và cờ xóa mềm (`_fivetran_synced`, `_fivetran_deleted`) và có chế độ history tùy chọn giữ các phiên bản trước của dòng.
- Tùy chọn managed data lake ghi bảng Iceberg (và Delta) vào object storage của bạn và đăng ký vào catalog để nhiều engine truy vấn.
- Giá thường dựa trên monthly active rows (số dòng được insert, update hoặc delete mỗi tháng), nên một nguồn "ồn ào" có thể rất tốn.

**Kiểu lỗi.** Xóa mềm (`_fivetran_deleted = true`) không được lọc sẵn; model phải loại chúng. Re-sync bảng lớn có thể tốn kém và chậm. Hành vi phụ thuộc vào logic connector của nhà cung cấp mà bạn không thể xem hay vá, nên hãy xác nhận delete, history và xử lý schema cho từng connector.

## Airbyte vs Fivetran

| Vấn đề | Airbyte | Fivetran |
|---|---|---|
| Triển khai | Mã nguồn mở tự host, hoặc cloud managed | Dịch vụ managed (có lựa chọn hybrid) |
| Connector tùy biến | Connector builder, CDK, có thể fork connector | Hạn chế; yêu cầu hoặc dùng function connector |
| Vận hành | Bạn vận hành (bản tự host) | Nhà cung cấp vận hành |
| Yếu tố chi phí | Hạ tầng + thời gian kỹ sư, hoặc credit cloud | Theo mức dùng (active rows) |
| Khả năng xem xét | Mã connector công khai | Hành vi có tài liệu, mã đóng |
| Đầu ra Iceberg | Destination hỗ trợ Iceberg | Dịch vụ managed data lake |

Hãy chọn theo các nguồn bạn cần (chất lượng connector khác nhau theo từng connector chứ không theo nhà cung cấp), năng lực vận hành hạ tầng của đội, chi phí ở khối lượng dữ liệu của bạn và yêu cầu về vị trí lưu trữ dữ liệu.

## dlt

**Là gì.** dlt (data load tool) là thư viện Python mã nguồn mở để nạp dữ liệu từ API, database và file vào warehouse, DuckDB và lake. Bạn viết generator Python bình thường; dlt lo suy luận schema, chuẩn hóa JSON lồng nhau thành bảng, trạng thái incremental và việc nạp.

**Cách hoạt động.**

- Một **resource** là hàm Python yield record. Tùy chọn của decorator đặt tên bảng, primary key và **write disposition**: `append`, `replace` hoặc `merge` (upsert theo khóa).
- `dlt.sources.incremental` theo dõi cursor (ví dụ `updated_at`) và lưu giá trị cuối trong pipeline state, được dlt lưu ở đích cùng các bảng metadata về lần nạp.
- **Schema contract** quyết định điều gì xảy ra khi xuất hiện bảng, cột hoặc kiểu mới (`evolve`, `freeze`, `discard_row`, `discard_value`).
- Destination `filesystem` có thể ghi bảng Iceberg hoặc Delta lên object storage; DuckDB và MotherDuck, Postgres, Snowflake, BigQuery và nhiều đích khác cũng được hỗ trợ.

**Ví dụ kiểm tra được (minh họa).**

```python
import dlt
from dlt.sources.helpers import requests  # wrapper requests có retry với lỗi tạm thời


@dlt.resource(name="orders", primary_key="id", write_disposition="merge")
def orders(
    updated_at=dlt.sources.incremental("updated_at", initial_value="2026-01-01T00:00:00Z"),
):
    url = "https://api.example.com/v1/orders"
    params = {"updated_since": updated_at.last_value, "limit": 100}
    while url:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        yield body["data"]
        url = body.get("next")  # phân trang cursor: URL kế tiếp đã mang sẵn cursor
        params = None


pipeline = dlt.pipeline(
    pipeline_name="shop_api",
    destination="duckdb",          # hoặc "filesystem" với table_format="iceberg"
    dataset_name="raw_shop",
)
load_info = pipeline.run(orders(), schema_contract={"columns": "freeze"})
print(load_info)
```

Kiểm tra kết quả: truy vấn `raw_shop.orders` và bảng `_dlt_loads` để xem load ID và trạng thái. Chạy script hai lần và xác nhận số dòng không đổi khi API trả về cùng record (merge theo `id`).

**Kiểu lỗi.** Suy luận schema tự động có thể tạo bảng bất ngờ từ mảng lồng nhau hoặc cột mới do lỗi chính tả; dùng contract cho production. Cursor incremental có timestamp bằng nhau ở ranh giới trang có thể bỏ sót record, nên ưu tiên `>=` kèm khử trùng. Chạy song song hai bản của cùng pipeline có thể xung đột state.

## dlt vs Airbyte vs Fivetran

dlt là thư viện bạn nhúng vào mã mà bạn vốn đã điều phối và kiểm thử; Airbyte là nền tảng có UI, scheduler và danh mục connector; Fivetran là dịch vụ managed. Một mẫu phổ biến là dùng công cụ managed cho nguồn SaaS tiêu chuẩn và dlt cho API nội bộ hoặc ngách, cả ba cùng nạp dữ liệu giữ hình dạng nguồn để model phía sau làm sạch.

## Kiểm định cho mọi công cụ connector

- **Số lượng và tổng:** so sánh số dòng và tổng các chỉ số chính cho một kỳ đã đóng với báo cáo hoặc API của chính nguồn.
- **Delete:** xóa một record thử ở nguồn và xác nhận đích phản ánh thế nào (hoặc có phản ánh không).
- **Thay đổi schema:** thêm một trường ở môi trường thử và xác nhận chính sách của công cụ làm đúng như bạn kỳ vọng.
- **Độ tươi:** cảnh báo theo tuổi của record mới nhất mỗi bảng, không chỉ theo trạng thái sync thành công, vì một lần sync "thành công" có thể nạp 0 dòng.
- **Khôi phục:** ghi lại cách re-sync một bảng hoặc một khoảng ngày và chi phí của việc đó.

## Bài tập

1. Viết pipeline dlt ở trên với một API phân trang công khai (hoặc mock cục bộ). Nạp vào DuckDB, chạy hai lần và chứng minh tính idempotent bằng một truy vấn đếm và một truy vấn tìm khóa trùng.
2. Đổi đích sang `filesystem` với định dạng bảng Iceberg trên thư mục cục bộ hoặc MinIO. Xem các file metadata và data được tạo ra.
3. Freeze schema contract, rồi thêm một trường vào phản hồi của mock API. Ghi lại lỗi và quyết định tiến hóa hay từ chối.
4. Cấu hình cùng nguồn trong Airbyte (mã nguồn mở, cục bộ) với incremental append + deduped. So sánh các cột và metadata tạo ra với dlt.
5. Viết decision record chọn giữa Airbyte, Fivetran và dlt cho ba nguồn: một CRM SaaS, một REST API nội bộ và một database PostgreSQL. Nêu yếu tố chi phí, delete, thay đổi schema và chiến lược rời bỏ.

## Tiêu chí hoàn thành

- Pipeline dlt của bạn idempotent, incremental và có schema contract, được kiểm chứng bằng nhiều lần chạy.
- Bạn đã thử xử lý delete và thay đổi schema với ít nhất một công cụ và ghi lại kết quả.
- Kiểm tra độ tươi và đối soát chạy độc lập với trạng thái "thành công" của chính công cụ.
- Decision record gắn mỗi nguồn với một công cụ cùng đánh đổi rõ ràng.
