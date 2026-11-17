---
title: Nền tảng event streaming
description: So sánh queue, pub/sub và event log được lưu giữ, rồi vận hành các nền tảng họ Kafka cùng schema mà không làm mất thứ tự hay ý nghĩa dữ liệu.
order: 30
tags: [streaming, Kafka, pub/sub, message queue, schema registry, Pulsar, Redpanda, Confluent, Fluss, ZooKeeper]
---

# Nền tảng event streaming

Bài này nói về lớp messaging nằm giữa hệ thống vận hành và lakehouse. Bài mở rộng từ bài [Ingestion, CDC và Streaming](ingestion-cdc-and-streaming.html): hãy đọc bài đó trước để nắm ngữ nghĩa phân phối, event time và backfill.

Giả định dùng trong các ví dụ: service `orders` phát một event cho mỗi lần đơn hàng đổi trạng thái, khóa event là `order_id`, timestamp theo UTC, và đích phân tích là một bảng Apache Iceberg. Lệnh và cấu hình chỉ mang tính **minh họa**; hãy kiểm tra tài liệu của đúng phiên bản bạn chạy.

## Event Streaming

**Là gì.** Event streaming xem các sự kiện nghiệp vụ ("đơn 42 được thanh toán lúc 10:03:12Z") là một chuỗi record bất biến, có thứ tự và liên tục tăng. Producer ghi nối event; bao nhiêu consumer cũng được, mỗi consumer đọc theo nhịp riêng, ngay bây giờ hoặc sau này.

**Cách hoạt động.** Nền tảng streaming lưu event bền vững trong một log chỉ ghi nối (append-only) trong một khoảng retention (theo thời gian, dung lượng, hoặc vô hạn với tiered storage). Mỗi consumer tự theo dõi vị trí của mình (offset). Vì log được giữ lại, consumer mới có thể đọc từ đầu và consumer bị lỗi có thể tua lại và replay.

**Vì sao quan trọng với đội dữ liệu.** Cùng một event stream có thể nuôi service chống gian lận, chỉ mục tìm kiếm và bảng raw trên lakehouse mà hệ thống nguồn không cần biết đến bất kỳ bên nào. Cái giá là bạn đang sở hữu bản sao thứ hai của sự thật nghiệp vụ, với thứ tự, retention và schema cần được quản lý.

**Kiểu lỗi.** Event được phát trước khi transaction gây ra nó commit (event "ma"); event bị mất khi service ghi vào database nhưng crash trước khi phát (vấn đề dual-write; dùng bảng outbox hoặc CDC); consumer giả định thứ tự toàn cục trong khi nền tảng chỉ bảo đảm thứ tự theo partition hoặc theo key.

**Kiểm định.** So sánh số event theo khóa nghiệp vụ và theo giờ với hệ thống nguồn, kiểm tra mọi chuyển trạng thái đều hợp lệ (không có `shipped` trước `paid` cho cùng một khóa trong một partition), và cảnh báo khi consumer lag tăng.

## Pub/Sub Architecture

**Là gì.** Publish/subscribe là mẫu messaging: publisher gửi message tới một topic có tên mà không cần biết ai nhận; subscriber đăng ký quan tâm tới topic và mỗi subscriber nhận bản sao riêng.

**Cách hoạt động.** Một broker đứng giữa. Đặc tính cốt lõi là fan-out: một event được phát có thể tới nhiều nhóm subscriber độc lập. Việc giao có thể là *push* (broker gọi subscriber, như webhook hay push subscription) hoặc *pull* (subscriber tự lấy, như Kafka consumer). Trong một nhóm subscriber, công việc thường được chia giữa các instance.

**Ví dụ (minh họa).** `orders` phát `OrderPaid`. Có ba subscription: `billing` (gửi hóa đơn), `lake-ingest` (ghi vào Iceberg) và `notifications` (gửi email cho khách). Thêm subscriber thứ tư không đòi hỏi thay đổi gì ở publisher.

**Kiểu lỗi.** Coupling ẩn qua hình dạng payload (subscriber hỏng khi một trường đổi), subscriber chậm tích tụ backlog, và subscriber cần thứ tự trong khi hệ thống chỉ có thứ tự best-effort hoặc theo key. Pub/sub tách rời *ai* và *khi nào*, không tách rời *message mang nghĩa gì*; phần đó vẫn cần hợp đồng.

## Message Queue

**Là gì.** Message queue là bộ đệm nơi producer đặt message để consumer xử lý bất đồng bộ. Ngữ nghĩa điển hình là *competing consumers*: mỗi message được một consumer xử lý, sau đó được acknowledge và xóa.

**Cách hoạt động.** Consumer nhận message, message trở nên vô hình với các consumer khác trong một khoảng lease (visibility timeout). Nếu consumer acknowledge trong khoảng đó thì message bị xóa; nếu không, message xuất hiện lại và được thử lại. RabbitMQ và Amazon SQS theo mô hình này; nhiều hệ thống bổ sung độ ưu tiên, độ trễ và dead letter queue.

**Queue so với event stream.**

| Đặc tính | Message queue | Event stream (log) |
|---|---|---|
| Sau khi xử lý | Message bị xóa | Record giữ đến khi hết retention |
| Consumer | Tranh nhau message | Mỗi nhóm đọc toàn bộ stream |
| Replay | Thường không thể | Tua lại offset |
| Thứ tự | Thường best-effort; có biến thể FIFO | Theo partition |
| Phù hợp | Phân phối tác vụ, job, command | Sự kiện dùng chung, nhiều consumer, replay |

**Kiểu lỗi.** Handler chậm vượt visibility timeout nên message bị xử lý hai lần; poison message thử lại mãi nếu không có DLQ (xem [kiến trúc streaming và khôi phục](streaming-architectures-and-recovery.html)); queue bị dùng như hệ thống ghi nhận chuẩn sẽ mất lịch sử khi message được acknowledge.

## Apache Kafka

**Là gì.** Apache Kafka là nền tảng event streaming phân tán mã nguồn mở. Kafka lưu record trong các *topic*, chia thành *partition*, được nhân bản qua các *broker*.

**Cách hoạt động.**

- **Producer** gửi record kèm khóa (tùy chọn). Partitioner mặc định băm khóa, nên mọi record của `order_id=42` vào cùng partition và giữ thứ tự tương đối.
- Mỗi partition là một log có thứ tự; mỗi record có một **offset** tăng dần.
- Partition có **leader** và các **follower replica**. Với `acks=all` và `min.insync.replicas=2`, một lần ghi chỉ được xác nhận khi ít nhất hai replica đồng bộ đã có dữ liệu.
- **Consumer group** chia partition cho các thành viên. Offset đã commit ghi lại tiến độ của từng group, đây là điều cho phép khởi động lại và replay.
- Kafka hiện tại dùng **KRaft** (quorum controller dựa trên Raft tích hợp sẵn) cho metadata; chế độ ZooKeeper đã bị loại bỏ từ Kafka 4.0.
- **Log compaction** giữ ít nhất record mới nhất cho mỗi khóa, hợp với topic changelog; retention theo thời gian hợp với topic sự kiện.

**Ví dụ kiểm tra được (minh họa).**

```bash
# Sáu partition giới hạn mức song song tối đa của một consumer group.
kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic shop.orders --partitions 6 --replication-factor 3 \
  --config min.insync.replicas=2 --config retention.ms=604800000

# Kiểm tra nhóm ingestion vào lake đang chậm bao xa.
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group orders-to-iceberg
# Các cột cần đọc: PARTITION, CURRENT-OFFSET, LOG-END-OFFSET, LAG
```

Các thiết lập producer nên ghi rõ: `acks=all`, `enable.idempotence=true` (ngăn trùng lặp do producer retry trong một phiên), và một khóa khớp với thực thể cần giữ thứ tự.

**Kiểu lỗi.**

- *Trùng lặp*: consumer ghi vào Iceberg, crash trước khi commit offset, rồi đọc lại batch. Hãy làm sink idempotent (merge theo `event_id`) hoặc dùng sink commit offset và dữ liệu cùng nhau.
- *Thứ tự*: đổi số partition làm thay đổi ánh xạ khóa → partition cho record mới, nên event của một khóa có thể nằm ở nhiều partition. Lên kế hoạch số partition từ đầu.
- *Partition nóng*: khóa lệch (một tenant rất lớn) giới hạn throughput ở một partition.
- *Mất do retention*: consumer ngừng lâu hơn `retention.ms` sẽ âm thầm bỏ qua dữ liệu khi tiếp tục từ offset sớm nhất còn lại.
- *Backpressure*: Kafka đệm trên đĩa, nên consumer chậm biểu hiện bằng lag tăng chứ không phải producer lỗi. Lag là tín hiệu sức khỏe chính.

**Khôi phục.** Reset consumer group về một timestamp hoặc offset (`kafka-consumer-groups.sh --reset-offsets --to-datetime ... --execute` khi group đã dừng) và dựa vào sink idempotent để hấp thụ khoảng được replay.

## Apache ZooKeeper

**Là gì.** Apache ZooKeeper là dịch vụ điều phối cho hệ thống phân tán. ZooKeeper lưu các mẩu metadata nhỏ trong cây *znode* và bảo đảm thứ tự chặt chẽ cho các cập nhật.

**Cách hoạt động.** Một ensemble (thường 3 hoặc 5 server) bầu leader và nhân bản thao tác ghi bằng giao thức ZAB; thao tác ghi thành công khi đa số xác nhận. Client dùng *ephemeral znode* (tự xóa khi session chết) để theo dõi liveness và bầu leader, và dùng *watch* để nhận thông báo thay đổi.

**Ai vẫn cần nó.** Kafka từng dùng ZooKeeper cho metadata cụm và bầu controller cho đến khi KRaft thay thế; Kafka 4.0 trở đi chạy không cần ZooKeeper, và cụm cũ phải migrate sang KRaft trước khi nâng cấp. ZooKeeper vẫn xuất hiện trong HBase, failover high-availability của Hadoop HDFS, Apache Solr (SolrCloud), một số cấu hình high-availability của Flink (Kubernetes HA là lựa chọn thay thế), và là một trong các lựa chọn metadata store của Apache Pulsar.

**Kiểu lỗi.** Mất quorum (2 trên 3 node chết) chặn mọi thao tác ghi; session timeout đặt quá thấp gây bầu leader liên tục khi có garbage-collection pause; lưu dữ liệu lớn trong znode làm suy giảm cả ensemble. **Kiểm định:** dùng lệnh bốn chữ `ruok`/`mntr` (nếu được whitelist) hoặc admin server để kiểm tra trạng thái leader/follower và số request đang chờ.

Với một stack lakehouse mới, câu hỏi thực tế thường là "còn thành phần nào của tôi bắt buộc dùng ZooKeeper không?" chứ không phải "có nên triển khai nó không?".

## Schema Registry

**Là gì.** Schema registry là dịch vụ lưu schema có version (Avro, Protobuf, JSON Schema) cho message và áp dụng quy tắc tương thích khi producer đăng ký version mới. Confluent Schema Registry phổ biến nhất; Apicurio Registry và AWS Glue Schema Registry đảm nhận vai trò tương tự.

**Cách hoạt động.** Schema được nhóm theo *subject*; với chiến lược đặt tên mặc định, schema value của topic `shop.orders` nằm ở subject `shop.orders-value`. Serializer đăng ký hoặc tra cứu schema và ghi một header nhỏ chứa schema ID trước payload, nhờ đó consumer lấy đúng writer schema. Các chế độ tương thích quyết định thay đổi nào được chấp nhận:

| Chế độ | Bảo đảm | Thay đổi an toàn điển hình |
|---|---|---|
| `BACKWARD` (mặc định phổ biến) | Reader mới đọc được dữ liệu ghi bằng schema trước | Xóa trường, thêm trường tùy chọn có default |
| `FORWARD` | Reader cũ đọc được dữ liệu ghi bằng schema mới | Thêm trường, xóa trường tùy chọn |
| `FULL` | Cả hai chiều | Thêm/xóa trường tùy chọn có default |
| `*_TRANSITIVE` | Kiểm tra với mọi version trước, không chỉ version cuối | Như trên, chặt hơn |
| `NONE` | Không kiểm tra | Mọi thứ, kể cả thay đổi phá vỡ |

**Ví dụ kiểm tra được (minh họa).**

```bash
# Kiểm tra schema ứng viên trước khi triển khai producer.
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @candidate-schema.json \
  http://schema-registry:8081/compatibility/subjects/shop.orders-value/versions/latest
# => {"is_compatible": false}  -> chặn release trong CI
```

**Kiểu lỗi.** Kiểm tra của registry chỉ chứng minh tương thích về cấu trúc: đổi tên `amount` thành `amount_cents` kèm default vẫn "tương thích" nhưng đổi nghĩa. Producer JSON bỏ qua serializer sẽ bỏ qua luôn bước kiểm tra. Đặt `NONE` "tạm thời" trong sự cố thường trở thành vĩnh viễn. Khi sink là Iceberg, một thay đổi Avro tương thích vẫn phải ánh xạ được thành schema evolution hợp lệ của Iceberg (ví dụ nới `int` thành `long` được phép; thu hẹp thì không).

**Kiểm định.** Chạy endpoint kiểm tra tương thích trong CI cho mọi thay đổi schema, review thay đổi ngữ nghĩa trong data contract, và cảnh báo khi topic nhận record có schema ID lạ hoặc chưa đăng ký.

## Schema Drift

**Là gì.** Schema drift (trôi schema) là sự phân kỳ không chủ ý, không được điều phối giữa các schema đáng lẽ phải đồng bộ với nhau: ví dụ hai replica của cùng một database nguồn được chụp (snapshot) ở hai thời điểm khác nhau, nhiều nguồn ingestion cùng nạp vào một bảng đích nhưng mỗi nguồn tự quyết định cách biểu diễn một trường theo cách riêng, hoặc một hệ thống nguồn âm thầm đổi kiểu dữ liệu hay ý nghĩa của một cột mà không báo cho ai ở downstream. Không ai lên kế hoạch cho sự phân kỳ này và không ai gắn version cho nó.

**Khác với schema evolution ra sao.** Schema evolution là thay đổi có chủ ý và được quản lý: producer thêm trường, tăng version schema, và registry kiểm tra tương thích trước khi thay đổi được triển khai (xem phần Schema Registry ở trên). Schema drift là kiểu lỗi ngược lại: thay đổi xảy ra ngoài quy trình đó, không được thông báo, và chỉ bị phát hiện khi có gì đó hỏng hoặc dữ liệu bị âm thầm sai lệch.

**Khác với "concept drift" / "data drift" trong ML ra sao.** Tên gọi giống nhau dễ gây nhầm lẫn. Concept drift trong ML (và khái niệm liên quan data drift) mô tả sự dịch chuyển thống kê trong phân phối của input mô hình, hoặc trong mối quan hệ giữa input và target, theo thời gian — ví dụ hành vi chi tiêu của khách hàng thay đổi sau một chương trình khuyến mãi. Đó là vấn đề về giá trị dữ liệu trong mô hình hóa, không phải thay đổi về cấu trúc hay kiểu của schema. Schema drift là vấn đề cấu trúc/metadata: hình dạng hoặc ý nghĩa của một trường không còn khớp với điều mọi consumer đã giả định, bất kể tính chất thống kê của dữ liệu có đổi hay không.

**Ví dụ (minh họa).** Một consumer `lake-ingest` đọc từ ba replica theo vùng của cùng bảng `orders`. DBA của một replica nới `discount_pct` từ `decimal(5,2)` thành `decimal(7,2)` để hỗ trợ quy tắc khuyến mãi mới, mà không báo cho đội dữ liệu; hai replica còn lại vẫn giữ kiểu cũ. Pipeline CDC, vốn giả định một schema dùng chung cho mọi replica, hoặc làm fail batch từ replica đã đổi, hoặc tệ hơn, cắt bớt giá trị khi ghi và âm thầm làm sai tổng chiết khấu cho vùng đó — kiểu sai lệch vẫn vô hình cho đến khi báo cáo đối soát downstream bị vỡ.

**Kiểu lỗi / Kiểm định.** Xem việc phát hiện drift là độc lập với kiểm tra tương thích: so sánh schema quan sát được giữa mọi instance, replica hoặc nguồn đáng lẽ phải giống hệt nhau, theo lịch định kỳ chứ không chỉ tại thời điểm deploy, và cảnh báo khi có bất kỳ phân kỳ nào dù từng schema riêng lẻ vẫn "hợp lệ". Kiểm tra tương thích trong registry chỉ bảo vệ lịch sử version của riêng một producer; nó không nói gì về việc hai producer đáng lẽ phải khớp nhau có đang âm thầm không khớp hay không.

## Apache Pulsar

**Là gì.** Apache Pulsar là nền tảng messaging và streaming mã nguồn mở tách phần phục vụ khỏi phần lưu trữ: **broker** không trạng thái xử lý client, còn các node **Apache BookKeeper** (bookie) lưu dữ liệu dưới dạng *ledger* được nhân bản.

**Cách hoạt động.** Một topic là chuỗi các đoạn ledger phân bố trên nhiều bookie, nên thêm dung lượng lưu trữ không cần cân bằng lại cả partition. Pulsar hỗ trợ multi-tenancy (tenant và namespace), geo-replication tích hợp, tiered storage sang object store, và nhiều kiểu subscription trên cùng một topic: *exclusive*, *failover*, *shared* (competing consumers giống queue) và *key_shared* (song song nhưng giữ thứ tự theo khóa). Metadata nằm trong store có thể thay thế như ZooKeeper, etcd hoặc Oxia tùy phiên bản và cách triển khai.

**Pulsar so với Kafka cho ingestion lakehouse.** Pulsar kết hợp ngữ nghĩa queue và stream trong một hệ thống và mở rộng lưu trữ độc lập với broker; Kafka có hệ sinh thái connector lớn hơn, nhiều dịch vụ managed hơn và được nhiều engine hỗ trợ hơn (Flink, Spark, sink Kafka Connect vào Iceberg). Pulsar có thể nạp Iceberg qua sink Pulsar IO, connector Pulsar của Flink, hoặc lớp tương thích giao thức Kafka; hãy kiểm tra độ trưởng thành của đúng sink bạn định dùng.

**Kiểu lỗi.** Nhiều thành phần hơn (broker, bookie, metadata store) cần giám sát; subscription *shared* đánh đổi thứ tự; acknowledge theo từng message nên backlog chưa ack có thể âm thầm tăng. Kiểm định bằng metric backlog của subscription và đối soát số lượng đầu-cuối.

## Redpanda

**Là gì.** Redpanda là nền tảng streaming hiện thực Kafka API bằng C++, không cần JVM hay ZooKeeper. Client Kafka, Kafka Connect và phần lớn công cụ hiện có chạy với nó mà không cần sửa.

**Cách hoạt động.** Mỗi partition được nhân bản bằng Raft, và kiến trúc thread-per-core nhắm tới độ trễ đuôi thấp, ổn định với ít node hơn. Redpanda phát hành dưới dạng một binary duy nhất, tích hợp sẵn schema registry và HTTP proxy. *Iceberg Topics* có thể ghi record của topic vào một bảng Iceberg đăng ký trong catalog, nên topic có thể được truy vấn như bảng mà không cần job sink riêng; hãy kiểm tra catalog, ánh xạ schema và phiên bản (edition) mà bản phát hành của bạn hỗ trợ.

**Khi chọn nó.** Xem "tương thích Kafka" là một tuyên bố cần kiểm chứng: chạy producer, consumer, transaction và script quản trị của bạn trên staging. Tương thích ở mức giao thức không bảo đảm hành vi giống hệt cho mọi cấu hình hay edge case.

**Kiểu lỗi.** Ghi topic thành bảng vẫn cần schema (Avro/Protobuf đã đăng ký hoặc định dạng khai báo); record dịch lỗi phải đi đến nơi nhìn thấy được (bảng hoặc topic DLQ). Commit bảng diễn ra theo chu kỳ, nên độ tươi của bảng chậm hơn topic.

## Confluent

**Là gì.** Confluent là công ty do những người tạo ra Kafka thành lập. Công ty bán **Confluent Platform** (tự quản lý) và **Confluent Cloud** (Kafka managed hoàn toàn, connector, Schema Registry, Flink và các tính năng quản trị). IBM đã công bố thỏa thuận mua lại Confluent vào cuối 2025; hãy kiểm tra quyền sở hữu, cách đóng gói sản phẩm và giấy phép hiện tại khi đánh giá.

**Tableflow.** Tableflow của Confluent Cloud hiện thực hóa (materialize) topic Kafka thành bảng Apache Iceberg hoặc Delta Lake trên object storage, dùng schema đã đăng ký của topic, và công bố chúng vào catalog để các engine truy vấn. Tính năng này loại bỏ nhu cầu vận hành sink connector riêng cho các trường hợp topic → bảng đơn giản.

**Khi phù hợp.** Đội muốn dùng Kafka mà không phải vận hành broker, nâng cấp và cụm connector. Đánh đổi là chi phí (throughput, lưu trữ, giá connector), tính năng riêng của nhà cung cấp và ràng buộc về vị trí lưu trữ dữ liệu.

**Kiểu lỗi và kiểm tra.** Managed không có nghĩa là đúng: bạn vẫn sở hữu khóa, schema, retention và tính idempotent của consumer. Trước khi dựa vào bảng được materialize, xác nhận delete và upsert được biểu diễn thế nào, snapshot được commit bao lâu một lần, record chuyển đổi schema lỗi đi đâu, và bạn sẽ dựng lại bảng ra sao nếu cần.

## Apache Fluss

**Là gì.** Apache Fluss (incubating) là storage streaming mã nguồn mở thiết kế cho phân tích thời gian thực, xây quanh Apache Flink. Fluss bắt nguồn từ Alibaba và vào Apache Incubator năm 2025.

**Cách hoạt động.** Fluss có *log table* (stream chỉ ghi nối) và *primary-key table* nhận cập nhật, phát changelog và hỗ trợ tra cứu theo khóa. Dữ liệu log được lưu theo định dạng cột dựa trên Arrow, nên reader cần 3 trên 40 cột có thể tránh truyền phần còn lại. Một dịch vụ tiering liên tục compact dữ liệu vào định dạng bảng lake (Apache Paimon trước; hỗ trợ Iceberg được thêm trong các bản phát hành sau), và reader có thể kết hợp dữ liệu Fluss gần đây với dữ liệu đã tier xuống lake.

**Fluss so với Kafka.**

| Khía cạnh | Kafka | Fluss |
|---|---|---|
| Bố cục lưu trữ | Record byte theo hàng | Log dạng cột, projection pushdown |
| Cập nhật | Topic compacted, consumer tự áp upsert | Primary-key table có changelog |
| Tra cứu theo khóa | Không hỗ trợ | Có hỗ trợ |
| Tích hợp lake | Sink riêng hoặc tính năng nhà cung cấp | Tiering tích hợp sang định dạng lake |
| Độ trưởng thành hệ sinh thái | Rất rộng | Còn non, xoay quanh Flink |

**Khi nào nên đánh giá.** Phân tích nặng về Flink cần bảng tươi, cập nhật được và tra cứu theo khóa. Kiểm tra độ trưởng thành, công cụ vận hành và mức hỗ trợ engine trước khi chọn cho một nền tảng mà người khác phụ thuộc.

## Bài tập

1. Tạo topic Kafka (hoặc Redpanda) cục bộ với 3 partition. Phát 30 event đơn hàng trên 5 khóa, tiêu thụ chúng, và chứng minh thứ tự được giữ theo khóa nhưng không giữ giữa các khóa.
2. Dừng consumer, phát thêm 10 event, rồi describe consumer group và ghi lại lag. Khởi động lại và xác nhận lag về 0.
3. Đăng ký schema Avro cho `shop.orders-value` với tương thích `BACKWARD`. Thử một thay đổi tương thích và một thay đổi phá vỡ qua endpoint kiểm tra tương thích, lưu lại cả hai phản hồi.
4. Viết bản so sánh một trang giữa Kafka, Pulsar, Redpanda, Confluent Cloud và Fluss cho một đội ba kỹ sư cần bảng Iceberg raw cập nhật mỗi năm phút. Nêu gánh nặng vận hành, yếu tố chi phí và đường thoát.
5. Giải thích bằng lời của bạn khi nào dùng message queue thay vì event stream, kèm một ví dụ cho mỗi loại.

## Tiêu chí hoàn thành

- Bạn giải thích được partition, khóa, offset, consumer group, thiết lập replication và dự đoán được thứ tự mà consumer sẽ thấy.
- Bạn đã đo consumer lag và khôi phục từ consumer bị dừng mà không nhân đôi dòng ở sink.
- Quy trình thay đổi schema của bạn kiểm tra tương thích tự động và review ý nghĩa riêng.
- Bản so sánh nền tảng nêu đánh đổi cụ thể và chỉ rõ tuyên bố nào bạn đã kiểm chứng, tuyên bố nào lấy từ tài liệu.
