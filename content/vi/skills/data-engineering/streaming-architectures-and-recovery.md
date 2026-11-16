---
title: Kiến trúc streaming và khôi phục
description: So sánh kiến trúc Lambda và Kappa trên lakehouse, cô lập record lỗi bằng dead letter queue, và lên kế hoạch replay và backfill.
order: 35
tags: [streaming, Lambda architecture, Kappa architecture, DLQ, backfill, replay, Iceberg, reliability]
---

# Kiến trúc streaming và khôi phục

Một pipeline streaming chỉ đáng tin bằng câu chuyện khôi phục của nó. Bài này so sánh hai kiến trúc kinh điển để kết hợp dữ liệu thời gian thực và lịch sử, sau đó bàn cách cô lập record lỗi và xử lý lại lịch sử an toàn.

Giả định: event trong Kafka với retention bảy ngày, một job Flink hoặc Spark ghi bảng Iceberg (xem [xử lý luồng với Flink](stream-processing-flink.html)), và một metric doanh thu ngày phải khớp với tài chính. Cấu hình chỉ mang tính **minh họa**.

## Lambda Architecture

**Là gì.** Kiến trúc Lambda tách xử lý thành hai đường: **batch layer** định kỳ tính lại kết quả chính xác từ toàn bộ dữ liệu lịch sử, và **speed layer** xử lý event gần đây theo thời gian thực với bảo đảm chính xác thấp hơn. **Serving layer** gộp cả hai lúc truy vấn: kết quả batch cho các kỳ cũ, kết quả speed cho khoảng trống kể từ lần batch gần nhất.

**Cách hoạt động (ví dụ).** Mỗi đêm, một job Spark tính lại doanh thu ngày từ bảng event raw trên Iceberg. Trong ngày, một job streaming duy trì tổng cộng dồn của hôm nay trong một kho nhanh. Một view trả giá trị batch cho các ngày đã đóng và giá trị streaming cho hôm nay; khi batch đêm hoàn tất, nó thay thế giá trị streaming của hôm qua.

**Điểm mạnh.** Batch layer sửa lỗi của streaming (dữ liệu muộn, trùng lặp, bug) mỗi đêm, và việc xử lý lại lịch sử là công việc batch bình thường.

**Kiểu lỗi.** Hai hiện thực của cùng một logic lệch nhau (khác múi giờ, quy tắc khử trùng hoặc quy đổi tiền tệ), nên con số hôm nay nhảy khi batch tiếp quản; gấp đôi mã, test và bề mặt trực sự cố; chính logic gộp trở thành nguồn bug ở ranh giới ngày.

**Kiểm định.** Mỗi ngày so sánh kết quả speed layer và batch layer cho cùng kỳ đã đóng và cảnh báo khi vượt ngưỡng dung sai; độ chênh lệch là thước đo trực tiếp độ đúng của streaming.

## Kappa Architecture

**Là gì.** Kiến trúc Kappa dùng một đường xử lý luồng duy nhất cho cả dữ liệu trực tiếp và lịch sử. Xử lý lại nghĩa là replay log được lưu giữ qua phiên bản mới của cùng job streaming, không chạy một hệ thống batch riêng.

**Cách hoạt động (ví dụ).**

1. Phiên bản 1 của job đọc `shop.orders` và ghi `lake.gold.revenue_v1`.
2. Phát hiện bug. Triển khai phiên bản 2 đọc từ offset sớm nhất còn giữ (hoặc từ bảng raw Iceberg như một nguồn có giới hạn) vào `lake.gold.revenue_v2`.
3. Khi v2 bắt kịp đầu stream trực tiếp, kiểm định nó với v1 và với số liệu tài chính cho các kỳ đã đóng.
4. Chuyển reader (view hoặc alias trong catalog) sang v2, giữ v1 trong khoảng thời gian rollback, rồi loại bỏ.

**Vai trò của Iceberg.** Kappa thuần túy đòi hỏi log giữ mọi thứ bạn có thể cần replay, điều này tốn kém trong broker. Trên lakehouse, một thỏa hiệp phổ biến là: broker giữ vài ngày dữ liệu, còn bảng event raw Iceberg giữ toàn bộ lịch sử. Engine như Flink và Spark có thể đọc bảng Iceberg như stream có giới hạn cho phần lịch sử rồi chuyển sang broker cho dữ liệu gần đây, giữ một codebase trong khi dựa vào lưu trữ rẻ. Tiered storage của Kafka là lựa chọn thay thế, giữ các segment cũ trên object storage.

**Kiểu lỗi.** Replay hàng tháng event qua job streaming có trạng thái có thể mất rất lâu và cần mức song song cao hơn job trực tiếp; tác dụng phụ bên ngoài (email, gọi API) không được kích hoạt lại khi replay; kết quả replay khác bản gốc nếu job dựa vào processing time hoặc tra cứu dữ liệu đã thay đổi từ đó.

## Lambda vs Kappa

| Vấn đề | Lambda | Kappa |
|---|---|---|
| Codebase | Batch và streaming | Một codebase streaming |
| Cơ chế sửa sai | Tính lại bằng batch mỗi đêm | Replay vào phiên bản đầu ra mới |
| Nguồn lịch sử | Bảng raw hoặc file | Log được giữ, hoặc bảng lake như stream có giới hạn |
| Rủi ro nhất quán | Logic lệch giữa các layer | Thời gian replay và tác dụng phụ |
| Phù hợp | Đội mạnh về batch, nhu cầu realtime vừa phải | Đội đầu tư vào xử lý luồng và nguồn replay được |

Nhiều nền tảng lakehouse rơi vào giữa: streaming ingestion vào bảng raw Iceberg, với cả consumer streaming và batch đọc cùng các bảng đó bằng logic biến đổi dùng chung.

## Dead Letter Queue (DLQ)

**Là gì.** Dead letter queue giữ các message mà consumer không xử lý được, để phần còn lại của stream tiếp tục chảy trong khi record lỗi được giữ lại để kiểm tra và xử lý lại.

**Cách hoạt động.**

- **Kafka Connect:** đặt `errors.tolerance=all`, `errors.deadletterqueue.topic.name` và `errors.deadletterqueue.context.headers.enable=true` cho sink connector; record lỗi đi vào DLQ topic kèm header mô tả lỗi, topic, partition và offset gốc.
- **Flink:** định tuyến record parse hoặc kiểm định lỗi sang một *side output*, rồi sink stream đó vào DLQ topic hoặc bảng.
- **Message queue (ví dụ Amazon SQS):** redrive policy chuyển message sang DLQ sau khi nó được nhận một số lần tối đa mà không bị xóa.
- **Lakehouse:** một bảng Iceberg cách ly chứa payload raw, loại lỗi, thông điệp lỗi, tọa độ nguồn, phiên bản job và timestamp, dễ truy vấn và đếm.

```sql
-- Minh họa bảng cách ly.
CREATE TABLE lake.ops.dlq_orders (
  source_topic     STRING,
  source_partition INT,
  source_offset    BIGINT,
  raw_payload      BINARY,
  error_class      STRING,   -- ví dụ SCHEMA_MISMATCH, INVALID_VALUE, UNKNOWN_KEY
  error_message    STRING,
  job_version      STRING,
  failed_at        TIMESTAMP
) PARTITIONED BY (days(failed_at));
```

**Cái gì nên và không nên vào DLQ.** Vấn đề xác định, riêng của từng record (JSON sai định dạng, giá trị ngoài miền cho phép, schema ID lạ) thuộc về DLQ. Vấn đề mang tính hệ thống (đích sập, credential hết hạn) nên làm pipeline thất bại hoặc tạm dừng: đẩy mọi record vào DLQ trong lúc sự cố chỉ là dời sự cố đi chỗ khác.

**Kiểu lỗi.**

- *DLQ câm lặng:* không ai giám sát, nên dữ liệu "mất" ngay trước mắt. Cảnh báo theo tỷ lệ DLQ so với đầu vào, không chỉ khi có bất kỳ record nào.
- *Thứ tự:* redrive một update cũ của khóa 42 sau khi các update mới hơn đã được áp có thể ghi đè trạng thái hiện tại bằng giá trị cũ. Áp record được redrive theo version nguồn (vị trí log hoặc `updated_at`), không bao giờ áp mù quáng.
- *Trùng lặp:* lần redrive thành công một phần rồi chạy lại sẽ chèn lại record nếu sink không idempotent.
- *Bão schema drift:* một thay đổi ở producer đẩy 100% record vào DLQ; xem đợt tăng đột ngột là sự cố hợp đồng.

**Khôi phục.** Sửa nguyên nhân (mã, schema hoặc dữ liệu tham chiếu), sau đó redrive từ DLQ qua *cùng* đường kiểm định với upsert có xét version, và ghi lại record DLQ nào đã được xử lý lại. Xóa hoặc cho hết hạn record DLQ theo cùng quy tắc retention và quyền riêng tư như dữ liệu chính.

## Replay và backfill

Replay và backfill áp dụng cho cả hai kiến trúc:

- Khai báo khoảng (event time hoặc offset), nguồn (broker, bảng raw Iceberg hoặc snapshot hệ thống nguồn) và đích (ghi đè partition, bảng mới có version, hoặc merge idempotent).
- Ngăn chồng lấn với lần ghi theo lịch hoặc streaming vào cùng partition; optimistic concurrency của Iceberg sẽ từ chối commit xung đột, và bạn nên xem đó là tín hiệu thay vì retry mù quáng.
- Dùng snapshot Iceberg để an toàn: ghi lại snapshot ID trước khi backfill để có thể rollback (`rollback_to_snapshot`) nếu kiểm định thất bại.
- Đối soát số lượng và tổng với nguồn và với đầu ra trước đó trước khi chuyển reader.

## Bài tập

1. Hiện thực cùng metric doanh thu ngày hai lần: streaming (Flink hoặc Spark) và batch (SQL trên bảng raw Iceberg). So sánh kết quả cho ba ngày đã đóng và giải thích mọi chênh lệch.
2. Cài một bug vào job streaming, rồi sửa theo kiểu Kappa: chạy job v2 vào bảng mới từ lịch sử raw, kiểm định, và chuyển một view sang v2.
3. Thêm DLQ (DLQ topic của Kafka Connect hoặc side output của Flink vào bảng Iceberg). Bơm 20 record sai định dạng và một record không tương thích schema, xác nhận stream chính vẫn chảy.
4. Redrive các record DLQ sau khi sửa, bao gồm một update cũ cho khóa đã có dữ liệu mới hơn. Chứng minh kiểm tra version ngăn được việc ghi đè bằng dữ liệu cũ.
5. Thực hiện backfill một ngày có ghi lại snapshot bắt đầu, rồi rollback và áp lại.

## Tiêu chí hoàn thành

- Bạn giải thích được khi nào hai đường của Lambda đáng chi phí và Kappa xử lý lại lịch sử ra sao, bao gồm vai trò của Iceberg như kho để replay.
- Record DLQ mang loại lỗi và tọa độ nguồn, được giám sát theo tỷ lệ, và có thể redrive idempotent theo thứ tự version.
- Một lần replay hoặc backfill đã được kiểm định với tham chiếu trước khi chuyển reader, kèm rollback đã thử nghiệm.
