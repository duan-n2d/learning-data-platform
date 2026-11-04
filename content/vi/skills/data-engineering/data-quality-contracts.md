---
title: Chất lượng dữ liệu và hợp đồng
description: Biến kỳ vọng nguồn và quy tắc nghiệp vụ thành kiểm tra quan sát được.
order: 2
tags: [chất lượng dữ liệu, hợp đồng, kiểm thử]
---

# Chất lượng dữ liệu và hợp đồng

Hợp đồng dữ liệu làm rõ kỳ vọng giữa producer và consumer. Không chỉ mô tả tên cột: cần nêu ý nghĩa, chủ sở hữu, chính sách thay đổi, kỳ vọng phân phối và cách xử lý khi vi phạm.

## Các khía cạnh của hợp đồng

| Khía cạnh | Kỳ vọng ví dụ |
|---|---|
| Schema | `order_id` là chuỗi không NULL; `created_at` là timestamp UTC |
| Khóa | `order_line_id` duy nhất trong hệ thống nguồn |
| Miền giá trị | `status` nằm trong danh sách vòng đời đã tài liệu hóa |
| Quan hệ | Mọi order line được công bố tham chiếu tới order đã biết |
| Freshness | Ngày nghiệp vụ hoàn chỉnh mới nhất tới trước thời điểm đã thống nhất |
| Khối lượng | Sai lệch lớn khỏi số dòng thường lệ cần điều tra |
| Ngữ nghĩa | `net_amount` loại đơn hủy và gồm chiết khấu đã duyệt |
| Chủ sở hữu | Producer/consumer cụ thể chịu trách nhiệm thay đổi và sự cố |

## Kiểm thử tại đúng ranh giới

Kiểm định hình dạng đầu vào khi ingestion. Kiểm thử phép biến đổi về khóa, quan hệ và logic nghiệp vụ. Theo dõi freshness và volume như tín hiệu vận hành. Không lớp nào thay thế lớp nào: dữ liệu đúng schema vẫn có thể sai nghĩa, còn test nghiệp vụ có thể không phát hiện thiếu partition.

Phân biệt lỗi chặn với cảnh báo. Khóa chính sai có thể cần chặn công bố; thay đổi volume nhẹ có thể báo chủ sở hữu hoặc tạo tác vụ rà soát. Chọn theo tác động downstream và ghi rõ hành vi.

## Ví dụ kiểm tra SQL

```sql
-- Kiểm tra khóa trùng: kỳ vọng không có dòng trả về.
select order_line_id, count(*) as row_count
from stg_order_lines
group by order_line_id
having count(*) > 1;
```

```sql
-- Đối soát: điều tra mọi chênh lệch không giải thích được.
select
  sum(source_amount) as source_total,
  sum(model_amount) as model_total,
  sum(source_amount) - sum(model_amount) as difference
from daily_reconciliation;
```

Chạy kiểm tra trên dữ liệu lịch sử đại diện lẫn partition mới nhất. Chỉ kiểm tra batch hôm nay có thể bỏ sót sửa đổi đến muộn hoặc backfill lỗi.

## Xử lý thất bại

Khi test lỗi, giữ đủ ngữ cảnh chẩn đoán: run ID, partition nguồn, quy tắc lỗi, số dòng ảnh hưởng và mẫu an toàn nếu được phép. Cách ly dòng sai khi phù hợp; nếu không thì chặn model liên quan. Không âm thầm bỏ dòng rồi báo chạy thành công. Ghi rõ cách replay và khôi phục.

## Bài tập

Viết hợp đồng cho luồng event khách hàng: chính sách đổi schema, kỳ vọng duy nhất, tên event hợp lệ, mục tiêu freshness và chủ sở hữu. Tạo khóa trùng và event đến muộn trong dữ liệu test; xác minh hệ thống báo hai lỗi theo cách khác nhau.