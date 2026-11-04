---
title: Cẩm nang công nghệ dữ liệu chuyên biệt
description: Hiểu contract, change capture, lịch sử, tiến hóa schema, asset và engine phân tích.
order: 5
tags: [data contract, CDC, tiến hóa schema, OLAP]
---

# Cẩm nang công nghệ dữ liệu chuyên biệt

Công nghệ chuyên biệt giải quyết vấn đề ở một ranh giới cụ thể. Trước khi thêm công cụ vào stack, hãy hiểu bất biến mà nó bảo đảm và phần trách nhiệm nào vẫn thuộc về nhóm.

## Contract, product và asset

Data contract là thỏa thuận về schema, ý nghĩa, chất lượng, freshness, tương thích, ownership và thay đổi. Nó cần được kiểm tra ở nơi dữ liệu được tạo/tiêu thụ. Record đúng schema vẫn có thể vi phạm nghiệp vụ, vì vậy thêm kỳ vọng ngữ nghĩa ở nơi biểu đạt và kiểm thử được.

Data product là giao diện dữ liệu được hỗ trợ cho consumer xác định. Cần owner, tài liệu, chính sách quyền, kỳ vọng chất lượng và đường hỗ trợ. Software-defined asset biểu diễn đầu ra dữ liệu bền vững trong mã, thường kèm dependency, metadata, check và hành vi thực thi. Nó giúp quan sát lineage/freshness nhưng không tự làm đầu ra đáng tin; vẫn cần test và owner.

## Snapshot, CDC và idempotency

Snapshot ghi trạng thái nguồn tại một thời điểm. Nó hữu ích để tái tạo và phát hiện thay đổi nhưng chuỗi snapshot có thể không cho biết mọi sự kiện trung gian. CDC bắt insert/update/delete từ change log; cần hiểu offset, thứ tự, ranh giới transaction, thao tác xóa và tiến hóa schema.

Idempotency nghĩa là lặp thao tác với cùng đầu vào logic không tạo thêm side effect ngoài ý muốn. Dùng khóa ổn định, partition xác định, quy tắc merge hoặc record khử trùng. Xác định phạm vi: task có thể idempotent nhưng workflow vẫn gửi thông báo ngoài trùng lặp.

## Slowly changing dimension và time travel

Dimension biến đổi chậm giữ lịch sử thuộc tính mô tả. Type 1 ghi đè khi không cần lịch sử. Type 2 thêm phiên bản với ranh giới hiệu lực để fact dùng mô tả đúng tại event time. Định nghĩa timezone và khoảng hợp lệ, không để khoảng chồng lấn, kiểm thử fact đến muộn và correction.

Time travel đọc hoặc khôi phục snapshot bảng cũ nếu storage hỗ trợ. Nó hữu ích cho audit, tái tạo và khôi phục nhưng bị giới hạn bởi retention, ghi đồng thời, catalog và hết hạn snapshot. Xem đây là tính năng recovery đã kiểm thử, không thay backup hay retention nguồn.

## ACID và thay đổi schema

Transaction ACID bảo đảm atomicity, consistency, isolation và durability trong ranh giới transaction xác định. Trên platform dữ liệu, ranh giới có thể không trải qua database nguồn, object storage, catalog, job biến đổi và consumer. Tài liệu hóa commit nào làm dữ liệu hiển thị và lượt chạy nhiều bước thất bại để lại gì.

Schema evolution là thay đổi contract có kiểm soát theo thời gian. Schema drift là khác biệt quan sát được giữa hình dạng/ý nghĩa dự kiến và dữ liệu vào, có thể có kế hoạch hoặc ngoài ý muốn. Thêm cột vẫn có thể làm consumer nghiêm ngặt lỗi; đổi kiểu, tên hay tái sử dụng ý nghĩa có thể làm sai âm thầm. Phân loại tương thích, version contract, cảnh báo drift và phối hợp rollout producer/consumer.

### Ví dụ contract đơn hàng

```yaml
contract_version: 1
owner: commerce-data
grain: one record per source order
key: order_id
fields:
	order_id: {type: string, required: true}
	status: {type: string, required: true, allowed: [pending, paid, cancelled, refunded]}
	updated_at: {type: timestamp, required: true, timezone: UTC}
delivery:
	cadence: daily
	expected_by: "07:00 UTC"
change_policy: announce breaking changes before rollout
```

Contract này có thể được kiểm tra lúc ingestion và tham chiếu bởi model downstream. Chủ nghiệp vụ vẫn phải quyết định trạng thái mới có hợp lệ không và báo cáo xử lý thế nào.

| Thay đổi | Tương thích thường gặp | Cách triển khai an toàn hơn |
|---|---|---|
| Thêm trường tùy chọn | Thường tương thích ngược nhưng consumer strict có thể lỗi | Triển khai consumer chịu được trước rồi mới công bố trường |
| Thêm trường bắt buộc | Phá vỡ producer hiện tại | Có default hoặc triển khai producer/consumer theo giai đoạn |
| Đổi tên trường | Phá vỡ tương thích | Thêm trường mới, dual-read/write tạm thời, chuyển consumer rồi ngừng trường cũ |
| Đổi kiểu hoặc đơn vị | Thường phá vỡ dù giá trị vẫn parse | Tạo trường có phiên bản và đối soát trước khi chuyển |
| Dùng lại trường với nghĩa mới | Phá vỡ ngữ nghĩa | Tạo trường/metric mới và ghi lộ trình ngừng |

### Ví dụ snapshot và CDC

Snapshot chỉ thể hiện trạng thái đầy đủ nếu trích xuất hoàn tất và có ranh giới rõ. Lưu timestamp `snapshot_at` và khóa ổn định. Không suy ra xóa từ dòng vắng mặt trong lượt trích một phần. Với snapshot đầy đủ, định nghĩa vắng mặt nghĩa là xóa, soft-delete hay ngoài phạm vi.

CDC update có thể như sau:

```json
{
	"operation": "update",
	"source_position": "log-offset-or-sequence",
	"transaction_id": "source-transaction-id",
	"event_time": "2026-04-02T10:15:00Z",
	"key": {"order_id": "O-1042"},
	"before": {"status": "pending"},
	"after": {"status": "paid"}
}
```

Consumer nên lưu source position cùng output đã commit, áp dụng thay đổi theo phạm vi thứ tự của nguồn và xử lý replay idempotent. Event xóa cần tombstone hoặc record xóa xác định để history và model trạng thái hiện tại downstream phản ứng nhất quán.

### Lịch sử Type 2 và áp dụng idempotent

Khi vùng của khách hàng đổi, dimension Type 2 đóng phiên bản cũ rồi tạo phiên bản mới. Dùng khoảng hiệu lực nửa mở để đúng một version khớp event time:

```sql
select f.order_id, d.region
from fct_orders f
join dim_customer_history d
	on f.customer_id = d.customer_id
 and f.order_time >= d.valid_from
 and f.order_time < d.valid_to;
```

Với lượt nạp có thể lặp lại, merge bằng business key ổn định cùng source version/event position. Xử lý lại event giống hệt không được thêm phiên bản history. Nếu correction cũ tới muộn, định nghĩa có dựng lại khoảng lịch sử bị ảnh hưởng không và kiểm thử các khoảng không chồng lấn.

## CLI tích hợp dữ liệu

CLI tích hợp dữ liệu hỗ trợ trích xuất, chuẩn hóa, kiểm định và nạp trong workflow local/tự động. Đánh giá xác thực, quản lý bí mật, incremental state, retry, nguồn/đích hỗ trợ, ngữ nghĩa destination, log, license và nâng cấp. Một lệnh CLI chưa phải contract pipeline đầy đủ nếu state, lỗi, idempotency và vận hành chưa được xác định.

## Engine phân tích và công nghệ serving

Cube là ví dụ lớp semantic/serving có thể aggregate trước measure và cung cấp truy vấn có quản trị cho ứng dụng. VertiPaq là engine lưu trữ cột nén trong bộ nhớ của hệ sinh thái BI Microsoft. Cả hai cho thấy semantic model, nén và aggregate trước ảnh hưởng hiệu năng ra sao; không công nghệ nào thay thế được mọi warehouse. Đo kích thước model, refresh, concurrency và query pattern trên môi trường mục tiêu.

Data Engineering toolkit nên là bản đồ năng lực, không phải danh sách mua bắt buộc. Phân loại công cụ theo ingestion, storage, transformation, orchestration, quality, catalog, serving và observability; chỉ chọn thứ workload và nhóm có thể vận hành.

## Câu hỏi rà soát công nghệ

- Công nghệ bảo đảm điều gì và ở ranh giới nào?
- Kiểu lỗi, state và trách nhiệm vận hành nào vẫn còn?
- Thay đổi schema và rollback hoạt động ra sao qua producer/consumer?
- Tích hợp có được hỗ trợ với storage, engine, catalog và identity thực tế không?
- Thử nghiệm nhỏ nhất nào có thể bác bỏ lựa chọn dự kiến?

## Bài tập

Thiết kế dimension khách hàng từ database nguồn cho báo cáo tháng. Chọn snapshot hay CDC, định nghĩa khoảng hiệu lực Type 2, làm lượt nạp idempotent, kiểm thử schema drift và mô tả khôi phục sau publish lỗi bằng snapshot cùng dữ liệu nguồn lưu giữ.

## Học tiếp

- [Chất lượng dữ liệu và contract](../data-engineering/data-quality-contracts.html)
- [Ingestion, CDC và streaming](../data-engineering/ingestion-cdc-and-streaming.html)
- [Lưu trữ, warehouse và table format](../data-engineering/storage-warehousing-and-formats.html)
- [Query engine và hiệu năng](../data-engineering/query-engines-and-performance.html)