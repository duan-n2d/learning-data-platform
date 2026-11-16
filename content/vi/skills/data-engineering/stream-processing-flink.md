---
title: Xử lý luồng với Flink
description: Nạp và phân tích stream liên tục, hiểu checkpoint và commit, và chọn giữa micro-batching và xử lý liên tục cho bảng Iceberg.
order: 31
tags: [streaming, Flink, Spark, micro-batching, Iceberg, streaming analytics, checkpoints]
---

# Xử lý luồng với Flink

Broker như Kafka lưu event; stream processor đọc chúng, giữ trạng thái và ghi kết quả. Bài này tập trung vào Apache Flink và cách kiểu xử lý (micro-batch hay từng record) định hình độ trễ, chi phí và bố cục bảng trong lakehouse Iceberg.

Giả định: event đến từ topic `shop.orders` (xem [nền tảng event streaming](event-streaming-platforms.html)), mang `event_time` theo UTC và có khóa `order_id`. SQL và cấu hình bên dưới chỉ mang tính **minh họa**; tên tùy chọn thay đổi giữa các phiên bản Flink, Spark và Iceberg.

## Streaming Ingestion

**Là gì.** Streaming ingestion nạp dữ liệu liên tục ngay khi nó được tạo ra, thay vì theo lịch. Đường đi thường gặp là nguồn → broker (Kafka, Pulsar, Kinesis) → processor hoặc connector (Flink, Spark, Kafka Connect) → bảng (Iceberg, Delta, warehouse).

**Cách hoạt động.** Job ingestion đọc từ broker, tùy chọn parse, kiểm định, khử trùng hoặc che dữ liệu, rồi append hoặc upsert vào bảng raw/bronze. Tiến độ (offset) và đầu ra (commit bảng) phải đi cùng nhau, nếu không lần khởi động lại sẽ nhân đôi hoặc bỏ sót dữ liệu.

**Các quyết định thiết kế cần ghi ra.**

- Mục tiêu độ tươi (ví dụ "bảng raw chậm hơn topic tối đa 5 phút, p95").
- Append-only hay upsert. Bảng event raw thường append-only; bảng trạng thái hiện tại cần khóa và chiến lược upsert hoặc merge.
- Record không hợp lệ đi đâu (DLQ, bảng cách ly hay làm job thất bại).
- Chu kỳ commit và kế hoạch compaction, vì mỗi commit tạo file và snapshot.

**Kiểu lỗi.** *File nhỏ*: commit mỗi 10 giây với 20 writer song song tạo hàng nghìn file nhỏ mỗi giờ, làm chậm mọi reader. *Snapshot phình to*: mỗi commit thêm metadata Iceberg; không expire snapshot thì metadata tăng mãi. *Schema drift*: trường mới trong topic bị bỏ qua âm thầm nếu schema bảng không được tiến hóa. *Backpressure*: sink chậm làm nghẽn cả pipeline và tăng lag ở broker.

**Kiểm định.** So sánh số record theo giờ giữa topic và bảng, theo dõi `event_time` lớn nhất trong bảng so với đồng hồ thực (độ tươi), giám sát số file mỗi partition và kích thước file trung bình, và chạy compaction (`rewrite_data_files`) cùng expire snapshot theo lịch.

## Apache Flink

**Là gì.** Apache Flink là engine xử lý luồng có trạng thái, phân tán, mã nguồn mở. Flink xử lý từng record ngay khi đến, giữ keyed state (số đếm, window, giá trị thấy gần nhất) và xem batch là một stream có giới hạn.

**Cách hoạt động.**

- Một job là đồ thị dataflow gồm các operator chạy trong các *task* song song. Operator có khóa phân vùng state theo khóa, nên state của mỗi khóa nằm trên một task.
- **State backend** giữ state trong bộ nhớ (heap) hoặc đĩa cục bộ (RocksDB và các lựa chọn tách rời mới hơn), nên state có thể vượt RAM.
- **Checkpoint** định kỳ chụp snapshot nhất quán của toàn bộ state operator và vị trí nguồn bằng các barrier chạy theo stream. Khi lỗi, Flink khôi phục checkpoint hoàn tất gần nhất và tua nguồn về offset đã lưu.
- **Watermark** theo dõi tiến độ event time để window có thể đóng ngay cả khi event đến không theo thứ tự.
- **Savepoint** là snapshot do người dùng kích hoạt, dùng cho nâng cấp, thay đổi mức song song hoặc migrate.

**Vì sao commit Iceberg đi theo checkpoint.** Sink Iceberg của Flink ghi data file liên tục, nhưng chỉ commit chúng vào bảng (tạo snapshot mới) khi một checkpoint hoàn tất. Điều này gắn nội dung bảng với offset nguồn đã checkpoint: sau sự cố, file chưa commit bị bỏ và dữ liệu được đọc lại, cho kết quả exactly-once trong bảng. Hệ quả là **độ tươi của bảng bị giới hạn bởi chu kỳ checkpoint**: checkpoint 60 giây nghĩa là reader thấy dữ liệu mới tốt nhất khoảng mỗi phút một lần.

**Ví dụ kiểm tra được (Flink SQL minh họa).**

```sql
SET 'execution.checkpointing.interval' = '60s';

CREATE CATALOG lake WITH (
  'type' = 'iceberg',
  'catalog-type' = 'rest',
  'uri' = 'http://iceberg-rest:8181',
  'warehouse' = 's3://lake/warehouse'
);

CREATE TEMPORARY TABLE orders_src (
  event_id     STRING,
  order_id     BIGINT,
  status       STRING,
  amount_cents BIGINT,
  event_time   TIMESTAMP(3),
  WATERMARK FOR event_time AS event_time - INTERVAL '2' MINUTE
) WITH (
  'connector' = 'kafka',
  'topic' = 'shop.orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'flink-orders-to-iceberg',
  'scan.startup.mode' = 'group-offsets',
  'properties.auto.offset.reset' = 'earliest',
  'format' = 'avro-confluent',
  'avro-confluent.url' = 'http://schema-registry:8081'
);

-- Append event raw; khử trùng phía sau theo event_id.
INSERT INTO lake.raw.order_events
SELECT event_id, order_id, status, amount_cents, event_time
FROM orders_src;
```

Với bảng trạng thái hiện tại, khai báo primary key trên bảng Iceberg (format v2) và bật ghi upsert; khi đó Flink phát equality delete kèm insert. Bảng upsert sinh delete file mà reader phải merge, nên compaction càng quan trọng.

**Flink so với Spark Structured Streaming.** Flink xử lý từng record, hỗ trợ state theo event time một cách hạng nhất và độ trễ thấp; Spark Structured Streaming mặc định dùng micro-batch và tự nhiên hơn khi đội đã chạy Spark cho batch. Cả hai đều ghi được Iceberg; ở cả hai, tần suất commit bảng, chứ không phải độ trễ engine, thường quyết định độ tươi đầu-cuối.

**Kiểu lỗi.** Checkpoint bị timeout (thường do backpressure hoặc state quá lớn) nghĩa là không có commit Iceberg nào, nên bảng ngừng tiến trong khi job trông vẫn "running". Thay đổi truy vấn có trạng thái có thể làm state cũ không còn tương thích; lên kế hoạch nâng cấp dựa trên savepoint. Watermark quá chặt làm rơi event muộn khỏi window; quá lỏng làm chậm kết quả.

**Khôi phục.** Khởi động lại từ checkpoint gần nhất khi crash; từ savepoint khi thay đổi có kế hoạch; với lỗi logic, chạy job phiên bản mới từ một offset hoặc timestamp đã chọn vào bảng mới, kiểm định, rồi chuyển reader (xem mẫu Kappa trong [kiến trúc streaming và khôi phục](streaming-architectures-and-recovery.html)).

## Streaming Analytics

**Là gì.** Streaming analytics tính kết quả liên tục trên dữ liệu đang chảy: doanh thu cuốn chiếu theo phút, điểm gian lận theo thẻ, cảnh báo tồn kho, tỷ lệ chuyển đổi funnel trực tiếp. Khác với streaming ingestion ở chỗ đầu ra là câu trả lời, không phải bản sao.

**Cách hoạt động.** Truy vấn liên tục gom event vào window:

- **Tumbling**: cố định, không chồng lấn (mỗi 5 phút).
- **Hopping/sliding**: kích thước cố định, có chồng lấn (window 10 phút, mỗi phút một lần).
- **Session**: đóng sau một khoảng không hoạt động theo từng khóa.

Watermark quyết định khi nào window được xem là đầy đủ. Event muộn có thể cập nhật kết quả trước (phát retraction), đi ra side output, hoặc bị bỏ. Kết quả được ghi vào kho phục vụ (key-value store, database OLAP hoặc bảng Iceberg cho consumer chậm hơn).

**Ví dụ (Flink SQL minh họa).**

```sql
SELECT window_start, window_end, SUM(amount_cents) AS paid_cents, COUNT(*) AS paid_orders
FROM TABLE(TUMBLE(TABLE orders_src, DESCRIPTOR(event_time), INTERVAL '5' MINUTE))
WHERE status = 'paid'
GROUP BY window_start, window_end;
```

**Kiểu lỗi.** Đếm hai lần do event trùng (khử trùng theo `event_id` trước khi tổng hợp); kết quả lệch với warehouse batch do quy tắc dữ liệu muộn hoặc múi giờ khác nhau; dashboard hiển thị window chưa đủ như thể đã chốt.

**Kiểm định.** Mỗi ngày đối soát aggregate streaming với lần tính lại bằng batch cho cùng các window đã đóng; gắn nhãn giá trị tạm thời trong lớp phục vụ; ghi watermark và chính sách dữ liệu muộn cạnh định nghĩa metric.

## Micro-Batches

**Là gì.** Micro-batch là một lát nhỏ, có giới hạn của stream (ví dụ mọi record đến trong 30 giây gần nhất, hoặc đến offset mới nhất có sẵn khi trigger kích hoạt) được xử lý như một job batch mini.

**Cách hoạt động.** Ở mỗi trigger, engine ghi lại khoảng offset sẽ đọc, xử lý khoảng đó, ghi đầu ra, rồi commit tiến độ vào checkpoint hoặc write-ahead log. Vì mỗi micro-batch có khoảng đầu vào cố định, batch lỗi có thể chạy lại với cùng đầu vào, khiến việc khôi phục dễ suy luận.

**Ý nghĩa với Iceberg.** Mỗi micro-batch thường tạo một commit bảng. Trigger 30 giây nghĩa là khoảng 2.880 snapshot mỗi ngày cho mỗi bảng, mỗi snapshot thêm data file và metadata file. Lên kế hoạch compaction và expire snapshot từ ngày đầu, và tránh trigger nhanh hơn mức reader thực sự cần.

## Micro-Batching

**Là gì.** Micro-batching là mô hình xử lý chạy stream thành chuỗi micro-batch. Spark Structured Streaming dùng mặc định; sink Kafka Connect hành xử tương tự khi đệm record và flush theo ngưỡng dung lượng hoặc thời gian; sink Iceberg của Kafka Connect commit theo chu kỳ cấu hình.

**Ví dụ kiểm tra được (PySpark minh họa).**

```python
(spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "shop.orders")
    .option("startingOffsets", "earliest")
    .load()
    .selectExpr("CAST(key AS STRING) AS order_key", "value", "timestamp")
    .writeStream.format("iceberg")
    .outputMode("append")
    .trigger(processingTime="1 minute")
    .option("checkpointLocation", "s3://lake/checkpoints/orders_raw")
    .toTable("lake.raw.order_events"))
```

`checkpointLocation` lưu offset mà mỗi batch đã tiêu thụ. Xóa nó hoặc trỏ truy vấn mới vào vị trí cũ sẽ thay đổi những gì được xử lý lại, nên hãy xem nó là state production. Lần chạy `trigger(availableNow=True)` xử lý mọi thứ đang có rồi dừng, cho phép cùng đoạn mã chạy như batch incremental theo lịch.

**Đánh đổi.** Throughput cao hơn trên mỗi đơn vị compute, quản lý exactly-once đơn giản và khớp tự nhiên với commit bảng; độ trễ ít nhất bằng chu kỳ trigger cộng thời gian xử lý. Batch chạy lâu hơn chu kỳ trigger khiến batch sau bắt đầu muộn và lag tăng dần.

## Continuous Streaming

**Là gì.** Continuous streaming xử lý mỗi record ngay khi đến, không chờ gom đủ batch. Flink là ví dụ tiêu biểu; chế độ continuous processing thử nghiệm của Spark chỉ hỗ trợ thao tác đơn giản kiểu map với bảo đảm at-least-once, vì vậy phần lớn Spark streaming chạy theo micro-batch.

**Cách hoạt động.** Operator chạy như task sống lâu, nối với nhau qua network buffer. Khả năng chịu lỗi đến từ checkpoint bất đồng bộ thay vì commit theo batch, nên độ trễ xử lý có thể tính bằng mili giây trong khi độ bền vẫn dựa trên checkpoint.

**Ý nghĩa với Iceberg.** Xử lý liên tục không làm bảng Iceberg tươi liên tục. Khả năng thấy dữ liệu trong bảng vẫn là một commit, và commit gắn với checkpoint. Nếu cần thấy dữ liệu dưới một giây, hãy phục vụ từ kho độ trễ thấp hoặc từ chính stream, và dùng Iceberg cho lịch sử bền vững, truy vấn được.

## Continuous Streaming vs Micro-Batching

| Vấn đề | Micro-batching | Continuous streaming |
|---|---|---|
| Độ trễ xử lý | Chu kỳ trigger cộng thời gian batch (giây tới phút) | Mili giây tới giây |
| Hiệu quả throughput | Cao; chi phí mỗi batch được chia đều | Cao, nhưng nhạy với tinh chỉnh hơn |
| Mô hình khôi phục | Chạy lại khoảng offset của batch lỗi | Khôi phục checkpoint, tua nguồn |
| State và timer theo event time | Có, độ mịn thô hơn | Mịn, hạng nhất |
| Độ tươi Iceberg | Một commit mỗi batch | Một commit mỗi checkpoint |
| Độ quen thuộc vận hành | Giống batch, dễ cho đội Spark | Cần tinh chỉnh state và checkpoint |

**Cách chọn.** Bắt đầu từ nhu cầu độ tươi của consumer. Nếu dashboard làm mới mỗi 15 phút, micro-batch 5 phút hay thậm chí batch incremental theo lịch rẻ và đơn giản hơn. Chọn xử lý liên tục khi đầu ra nuôi một quyết định tự động mất giá trị sau vài giây (gian lận, cảnh báo) hoặc khi state phức tạp theo event time là trọng tâm.

## Bài tập

1. Chạy ví dụ Flink SQL (hoặc PySpark) với Kafka cục bộ và Iceberg REST catalog. Đổi chu kỳ checkpoint hoặc trigger từ 60 giây xuống 10 giây, chạy 30 phút, và so sánh số snapshot cùng kích thước file trung bình trong metadata của bảng.
2. Kill job giữa chừng và khởi động lại. Chứng minh bảng không có `event_id` trùng và không thiếu so với topic.
3. Xây aggregate doanh thu tumbling 5 phút. Bơm một event muộn 10 phút và ghi lại điều gì xảy ra với thiết lập watermark của bạn.
4. Chạy compaction và expire snapshot trên bảng, ghi lại số file trước và sau.
5. Với ba trường hợp (dashboard tài chính làm mới hằng giờ, chấm điểm gian lận, nạp clickstream raw), chọn micro-batching hay xử lý liên tục và giải thích theo độ trễ, chi phí và khôi phục.

## Tiêu chí hoàn thành

- Bạn giải thích được vì sao độ tươi bảng Iceberg đi theo chu kỳ checkpoint hoặc trigger, và đã đo nó.
- Lần khởi động lại cưỡng bức không tạo trùng lặp hay khoảng trống, được kiểm chứng bằng truy vấn đối soát.
- Aggregate streaming có watermark, chính sách dữ liệu muộn được ghi rõ và đối soát batch hằng ngày.
- Bảng có kế hoạch compaction và expire snapshot với tác động đã đo.
