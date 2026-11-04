---
title: Ingestion, CDC và Streaming
description: Chọn mẫu batch, incremental, capture thay đổi và làm rõ cam kết phân phối.
order: 7
tags: [ingestion, CDC, streaming, Kafka]
---

# Ingestion, CDC và Streaming

Ingestion chuyển dữ liệu qua một ranh giới hệ thống. Thiết kế phải giữ định danh, thời điểm sự kiện, ngữ cảnh schema và đủ thông tin tiến độ để khôi phục mà không mất hoặc nhân đôi record âm thầm.

## Tải đầy đủ, incremental và CDC

- **Snapshot đầy đủ** sao chép trạng thái nguồn hiện tại. Dễ suy luận với dataset nhỏ nhưng có thể tốn kém và không giữ được bản ghi đã xóa hay các trạng thái trung gian.
- **Tải incremental theo watermark** đọc bản ghi mới hơn timestamp hoặc sequence. Hiệu quả khi nguồn có trường cập nhật đáng tin; cập nhật muộn và sai lệch đồng hồ cần lookback hoặc đối soát.
- **Change Data Capture (CDC)** đọc insert, update, delete từ log thay đổi database hoặc cơ chế tương đương. Có thể giữ thứ tự và metadata transaction nhưng cần quản lý offset, schema và ngữ nghĩa xóa cẩn thận.

Chọn theo khả năng nguồn, freshness, volume, nhu cầu lịch sử và năng lực vận hành. CDC không mặc định chính xác hơn snapshot batch thiết kế tốt.

## ETL, ELT và các mẫu di chuyển

ETL biến đổi trước khi nạp vào đích phân tích. ELT đưa dữ liệu gần nguồn vào trước rồi biến đổi bằng compute của đích. Cách kết hợp có thể kiểm định, lọc, token hóa hoặc giảm dữ liệu nhạy cảm trước khi lưu, sau đó mới áp dụng biến đổi dùng lại.

Reverse ETL đẩy thuộc tính phân tích đã chọn và được quản trị về công cụ vận hành. Xem đây là đường serving riêng, cần chủ sở hữu, freshness, quyền ghi, đối soát và cách dừng/rollback rõ.

## Ngữ nghĩa phân phối và idempotency

Connector có thể giao cùng record nhiều lần sau retry hoặc reset offset. Thiết kế consumer khử trùng bằng event/source key ổn định và áp dụng update theo thứ tự hoặc version nguồn. Giữ transaction ID, log position và timestamp ingestion nếu hữu ích cho audit/khôi phục.

“Exactly once” chỉ áp dụng trong ranh giới hệ thống/transaction cụ thể. Pipeline đầu-cuối thường đi qua hệ thống có commit protocol khác nhau; ưu tiên idempotency và đối soát rõ thay vì dựa vào tuyên bố exactly-once rộng.

## Event time, processing time và streaming

Event time là lúc sự kiện xảy ra theo nguồn; processing time là lúc pipeline xử lý. Hệ thống streaming dùng window và watermark để quyết định chờ event muộn bao lâu. Định nghĩa điều gì xảy ra khi event tới sau thời gian cho phép: cập nhật aggregate cũ, phát correction, chuyển duyệt hay từ chối.

Distributed log như Kafka tách producer/consumer và giữ thứ tự record theo partition. Khóa partition ảnh hưởng ordering và parallelism. Hiểu retention, consumer offset, replay, backpressure và xử lý poison message trước khi xem topic là nguồn chuẩn bền vững.

## Thay đổi schema và hợp đồng

Phân loại thay đổi schema là tương thích, có điều kiện hoặc phá vỡ với producer/consumer cụ thể. Thêm trường vẫn có thể làm parser nghiêm ngặt lỗi; đổi tên/kiểu có thể âm thầm thay nghĩa. Dùng contract có version hoặc schema registry khi nhiều bên cần phối hợp tiến hóa. Kiểm định schema đầu vào và làm drift lộ ra trước khi model downstream công bố.

## Backfill và đối soát

Backfill xử lý lại khoảng event time đã khai báo bằng snapshot nguồn đã biết hoặc log có thể replay. Nêu cách thay thế/merge đầu ra, ngăn lịch chạy đồng thời ghi đè nhau và đối soát tổng ra sao. Ghi phiên bản mã và schema để sau này giải thích được kết quả.

## Bài tập

Thiết kế ingestion cho nguồn có thể cập nhật trạng thái đơn và xóa record thử nghiệm. So sánh snapshot ngày, watermark timestamp và log CDC. Xác định khóa, xử lý xóa, offset, dữ liệu muộn, chính sách schema, khoảng replay, khử trùng và bước đối soát. Nêu freshness nào đủ để chọn streaming thay batch.