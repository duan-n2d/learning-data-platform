---
title: CDC với Debezium và Kafka Connect
description: Capture thay đổi database từ log, đưa qua Kafka Connect vào Iceberg, và so sánh CDC với replication và tích hợp zero-ETL.
order: 32
tags: [CDC, Debezium, Kafka Connect, replication, zero-ETL, Iceberg, ingestion]
---

# CDC với Debezium và Kafka Connect

Change data capture (CDC) biến các thay đổi đã commit trong database thành một stream event. Bài [Ingestion, CDC và Streaming](ingestion-cdc-and-streaming.html) giải thích khi nào CDC đáng với độ phức tạp của nó; bài này cho thấy một hiện thực mã nguồn mở phổ biến hoạt động ra sao và hỏng ở đâu.

Giả định: database PostgreSQL `shop` có bảng `public.orders` và `public.customers`, mỗi bảng có primary key; một cụm Kafka có Schema Registry; một Iceberg REST catalog. Mọi cấu hình chỉ mang tính **minh họa**: tên thuộc tính thay đổi giữa các phiên bản Debezium và connector, nên hãy kiểm tra tài liệu của phiên bản bạn dùng.

## Kafka Connect

**Là gì.** Kafka Connect là framework của Apache Kafka để di chuyển dữ liệu giữa Kafka và hệ thống khác bằng các *connector* dùng lại được, nhờ đó đội ngũ cấu hình pipeline thay vì viết mã producer và consumer.

**Cách hoạt động.**

- **Worker** là các tiến trình JVM chạy thành cụm (chế độ distributed) và chia việc với nhau. Cấu hình, offset và trạng thái được lưu trong các topic Kafka nội bộ, nên một worker có chết thì task của nó chuyển sang nơi khác.
- **Source connector** (Debezium, JDBC, file) ghi vào Kafka; **sink connector** (Iceberg, S3, Elasticsearch) đọc từ Kafka.
- Một connector được chia thành các **task**, là đơn vị song song.
- **Converter** tuần tự hóa record (Avro, Protobuf, JSON Schema cùng Schema Registry); **single message transform (SMT)** thực hiện thay đổi nhẹ trên từng record như đổi tên trường hoặc bóc envelope CDC.
- Connector được tạo và kiểm tra qua REST API.

**Iceberg sink (minh họa).** Dự án Apache Iceberg cung cấp một sink Kafka Connect ghi record của topic vào bảng Iceberg và điều phối commit giữa các task qua một control topic, commit theo chu kỳ.

```json
{
  "name": "orders-iceberg-sink",
  "config": {
    "connector.class": "org.apache.iceberg.connect.IcebergSinkConnector",
    "tasks.max": "3",
    "topics": "shop.public.orders",
    "iceberg.tables": "raw.orders_cdc",
    "iceberg.tables.auto-create-enabled": "true",
    "iceberg.tables.evolve-schema-enabled": "true",
    "iceberg.control.commit.interval-ms": "300000",
    "iceberg.catalog.type": "rest",
    "iceberg.catalog.uri": "http://iceberg-rest:8181",
    "iceberg.catalog.warehouse": "s3://lake/warehouse",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "dlq.orders-iceberg-sink",
    "errors.deadletterqueue.context.headers.enable": "true"
  }
}
```

```bash
curl -s -X POST -H "Content-Type: application/json" --data @orders-iceberg-sink.json http://connect:8083/connectors
curl -s http://connect:8083/connectors/orders-iceberg-sink/status   # kiểm tra mọi task đều RUNNING
```

**Kiểu lỗi.** Một task có thể `FAILED` trong khi connector báo `RUNNING`, nên hãy kiểm tra trạng thái task, không chỉ trạng thái connector. `errors.tolerance=all` mà không có DLQ sẽ âm thầm bỏ record lỗi. DLQ tích hợp áp dụng cho sink connector và cho lỗi chuyển đổi/transform; lỗi trong quá trình ghi ra hệ thống ngoài vẫn có thể làm task thất bại. Quá nhiều task so với số partition khiến task ngồi không.

## Debezium

**Là gì.** Debezium là nền tảng CDC mã nguồn mở đọc transaction log của database (logical decoding của PostgreSQL, binlog của MySQL, bảng CDC của SQL Server, LogMiner của Oracle, change stream của MongoDB và nhiều loại khác) và phát một event cho mỗi thay đổi dòng. Debezium thường chạy dưới dạng source connector của Kafka Connect; Debezium Server và engine nhúng có thể gửi tới đích khác.

**Cách hoạt động.**

1. **Snapshot ban đầu.** Lần đầu chạy, connector đọc các dòng hiện có (event với `op = "r"`), rồi chuyển sang streaming từ vị trí log ghi nhận lúc snapshot. Incremental snapshot cho phép đọc lại bảng sau này mà không dừng streaming.
2. **Streaming.** Mỗi insert, update hoặc delete đã commit trở thành một event với `op` = `c`, `u` hoặc `d`.
3. **Offset.** Connector lưu vị trí log (LSN với PostgreSQL, file và vị trí binlog hoặc GTID với MySQL) trong offset của Kafka Connect, nên khởi động lại sẽ tiếp tục từ chỗ đã dừng.
4. **Topic.** Mặc định mỗi bảng đi vào `<topic.prefix>.<schema>.<table>`, có khóa là primary key của bảng để thay đổi của một dòng giữ thứ tự.

**Ví dụ kiểm tra được: source connector (minh họa).**

```json
{
  "name": "shop-postgres-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "pg-primary",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${file:/opt/secrets/pg.properties:password}",
    "database.dbname": "shop",
    "topic.prefix": "shop",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_shop",
    "publication.name": "dbz_shop",
    "table.include.list": "public.orders,public.customers",
    "snapshot.mode": "initial",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "key.converter.schema.registry.url": "http://schema-registry:8081",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081"
  }
}
```

**Envelope của event (minh họa, đã rút gọn).**

```json
{
  "before": {"order_id": 42, "status": "pending", "amount_cents": 1999},
  "after":  {"order_id": 42, "status": "paid",    "amount_cents": 1999},
  "source": {"connector": "postgresql", "db": "shop", "table": "orders",
             "lsn": 24023128, "txId": 5521, "ts_ms": 1763370192000},
  "op": "u",
  "ts_ms": 1763370192450
}
```

`source.ts_ms` là lúc thay đổi được commit trong database; `ts_ms` bên ngoài là lúc Debezium xử lý. Dùng vị trí log (`lsn`) hoặc version nguồn, không dùng processing time, để sắp thứ tự thay đổi của một khóa.

**Đưa vào Iceberg.** Hai thiết kế thường gặp:

- **Bảng change log (append).** Lưu mọi event cùng `op`, `lsn` và `source.ts_ms`. Cách này giữ đầy đủ lịch sử, giúp replay và audit; dựng trạng thái hiện tại phía sau bằng `MERGE` giữ `lsn` mới nhất cho mỗi khóa.
- **Bảng mirror (upsert).** Dùng SMT unwrap (`io.debezium.transforms.ExtractNewRecordState`) để làm phẳng envelope và một sink hỗ trợ upsert (Flink với primary key, hoặc sink được cấu hình upsert) để bảng phản chiếu nguồn. Cấu hình cách biểu diễn delete (tombstone, cờ `__deleted` hoặc xóa thật).

```sql
-- Minh họa: dựng lại trạng thái hiện tại từ change log append-only.
MERGE INTO lake.silver.orders t
USING (
  SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY lsn DESC) AS rn
    FROM lake.raw.orders_cdc
    WHERE ingest_date = DATE '2026-11-17'
  ) WHERE rn = 1
) s
ON t.order_id = s.order_id
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED AND s.lsn > t.lsn THEN UPDATE SET *
WHEN NOT MATCHED AND s.op <> 'd' THEN INSERT *;
```

**Kiểu lỗi.**

- *Replication slot phình to.* Khi connector dừng, PostgreSQL giữ WAL cho slot; sự cố kéo dài có thể làm đầy đĩa database. Cảnh báo theo lag của slot (`pg_replication_slots`) và chủ động xóa slot bị bỏ rơi.
- *Trùng lặp sau khởi động lại.* Offset được commit định kỳ, nên crash sẽ replay các thay đổi gần đây. Sink phải idempotent theo khóa và vị trí log.
- *Thứ tự.* Thứ tự được bảo đảm theo khóa (partition), không phải giữa các bảng. Join thay đổi của `orders` và `customers` có thể thấy chúng theo thứ tự khác với transaction nguồn.
- *Schema drift.* Cột thêm ở nguồn làm đổi schema event; cột bị xóa hoặc đổi tên có thể làm hỏng consumer hoặc sink Iceberg. Đưa DDL qua review và kiểm tra bằng tương thích của Schema Registry.
- *Update thiếu phần.* Với replica identity mặc định của PostgreSQL, `before` có thể rỗng và giá trị lớn (TOAST) không đổi có thể xuất hiện dưới dạng placeholder; đặt `REPLICA IDENTITY FULL` cho bảng cần before-image đầy đủ, chấp nhận WAL tăng thêm.
- *Chi phí snapshot.* Snapshot ban đầu của bảng lớn tạo tải lên nguồn; lên lịch và cân nhắc incremental snapshot.

**Kiểm định và khôi phục.** Đối soát số dòng và checksum theo dải khóa giữa nguồn và bảng mirror Iceberg hằng ngày; so sánh `lsn` cao nhất đã capture với vị trí hiện tại của database để đo lag; khi đích bị mất hoặc hỏng, snapshot lại (incremental snapshot hoặc connector mới với slot mới) vào bảng mới và chuyển đổi sau khi đối soát.

## Data Replication

**Là gì.** Data replication sao chép dữ liệu liên tục từ một hệ thống sang hệ thống khác để có tính sẵn sàng, khôi phục thảm họa, mở rộng đọc hoặc gần người dùng hơn. CDC là một cách hiện thực replication giữa các hệ thống khác nhau; database cũng tự replicate giữa các node của chính nó.

**Cách hoạt động.**

- Replication **đồng bộ** chỉ xác nhận ghi sau khi replica xác nhận: không mất dữ liệu khi failover, độ trễ ghi cao hơn.
- Replication **bất đồng bộ** xác nhận trước rồi gửi thay đổi sau: ghi nhanh hơn, nhưng failover có thể mất các thay đổi gần nhất (khoảng replication lag).
- Replication **vật lý** sao chép thay đổi ở mức lưu trữ (streaming replication của PostgreSQL); replication **logic** sao chép thay đổi dòng và có thể nhắm tới phiên bản, tập con hoặc hệ thống khác.
- Topology gồm single-leader (một nơi ghi, nhiều nơi đọc), multi-leader và hệ thống quorum không leader.

Kafka replicate partition theo cách tương tự: `replication.factor=3`, `min.insync.replicas=2` và producer `acks=all` cho độ bền miễn là hai replica còn khỏe.

**Kiểu lỗi.** Reader trên replica bất đồng bộ thấy dữ liệu cũ (vi phạm read-your-writes); multi-leader cần giải quyết xung đột; replica sao chép trung thành cả lần xóa nhầm, nên **replication không phải backup**. Truy vấn phân tích trỏ vào replica vẫn có thể làm chậm primary qua xung đột replication hoặc tài nguyên bị giữ.

**Kiểm định.** Giám sát replication lag theo thời gian và byte, diễn tập failover định kỳ, và giữ backup point-in-time độc lập với replica.

## Zero-ETL

**Là gì.** Zero-ETL là cách tiếp cận của nhà cung cấp, kết nối database vận hành với hệ thống phân tích mà khách hàng không phải xây hay vận hành mã pipeline. Ví dụ gồm các tích hợp managed từ database vận hành vào cloud warehouse và tính năng "mirroring" trong nền tảng phân tích.

**Cách hoạt động.** Bên dưới, nhà cung cấp chạy CDC hoặc replication, quản lý offset và ánh xạ schema, và đưa bảng gần thời gian thực, giữ hình dạng nguồn vào đích. "Zero" chỉ phần pipeline bạn phải bảo trì, không có nghĩa extract, load hay transform biến mất.

**Quan hệ với ELT và reverse ETL.** Zero-ETL thực chất là EL managed với ngữ nghĩa replication: bạn vẫn phải mô hình hóa, kiểm thử và quản trị dữ liệu sau khi nạp (chữ T trong ELT). Reverse ETL đi chiều ngược lại, từ phân tích về công cụ vận hành, và không bị ảnh hưởng.

**Đánh đổi và kiểu lỗi.** Ít thành phần hơn và thiết lập nhanh, nhưng nguồn, đích, loại bảng và thay đổi DDL được hỗ trợ bị giới hạn theo những gì nhà cung cấp hiện thực; có thể không lọc hay che dữ liệu trước khi nạp, điều quan trọng với cột nhạy cảm; chi phí và lag khó thấy hơn; và muốn rời đi sau này thì vẫn phải xây pipeline.

**Kiểm định.** Đối xử với đích zero-ETL như mọi nguồn khác: kiểm tra độ tươi, đối soát số lượng với nguồn, thử xem delete và thay đổi schema hiện ra thế nào, và ghi lại điều xảy ra khi nguồn bảo trì hoặc failover.

## Bài tập

1. Chạy PostgreSQL, Kafka, Kafka Connect và Schema Registry cục bộ (ví dụ bằng Docker Compose). Triển khai source connector Debezium cho một bảng và xem event snapshot (`op = r`) và streaming (`c/u/d`).
2. Cập nhật một dòng ba lần rồi xóa nó. Trình bày các event theo thứ tự cùng giá trị `lsn`.
3. Đưa change log vào bảng Iceberg bằng sink connector và dựng bảng trạng thái hiện tại bằng `MERGE`. Chứng minh dòng đã xóa biến mất và replay một batch không làm đổi kết quả.
4. Dừng connector 15 phút trong khi ghi vào nguồn, rồi đo lag của replication slot trước và sau khi khởi động lại.
5. Thêm một cột nullable rồi đổi tên một cột ở nguồn. Ghi lại điều xảy ra ở Schema Registry, topic và bảng Iceberg.
6. Viết ghi chú quyết định nửa trang so sánh Debezium + Kafka Connect, replication gốc của database và tích hợp zero-ETL của nhà cung cấp cho nguồn của bạn.

## Tiêu chí hoàn thành

- Bạn giải thích được giai đoạn snapshot và streaming, offset, và vì sao thứ tự chỉ được giữ theo khóa.
- Bảng trạng thái hiện tại idempotent khi replay và xử lý delete đúng, được kiểm chứng bằng truy vấn đối soát.
- Bạn giám sát lag của replication slot hoặc connector và có quy trình khôi phục bằng văn bản (snapshot lại vào bảng mới, kiểm định, chuyển đổi).
- Ghi chú quyết định phân biệt replication cho tính sẵn sàng với CDC cho phân tích và nêu giới hạn zero-ETL với nguồn của bạn.
