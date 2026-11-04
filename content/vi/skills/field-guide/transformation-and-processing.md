---
title: Cẩm nang biến đổi và xử lý dữ liệu
description: Chọn SQL, Python, batch, streaming và orchestration để xây data product đáng tin cậy.
order: 3
tags: [biến đổi, SQL, Python, orchestration, streaming]
---

# Cẩm nang biến đổi và xử lý dữ liệu

Biến đổi đưa dữ liệu đã thu nhận về dạng phù hợp cho consumer. Chọn mô hình thực thi theo phép biến đổi, nguồn/đích, freshness yêu cầu và năng lực vận hành của nhóm.

## SQL, Python và framework biến đổi

SQL hiệu quả cho lọc quan hệ, join, aggregate, window calculation và phép biến đổi khai báo chạy gần dữ liệu phân tích. Học kiểu dữ liệu, ngữ nghĩa NULL, hàm thời gian, query plan và extension của engine mục tiêu. Tính năng SQL nâng cao như window, dữ liệu bán cấu trúc hoặc địa không gian hữu ích nếu làm logic rõ hơn và đủ khả năng chuyển đổi giữa hệ thống.

Python phù hợp ingestion API/file, parse tùy chỉnh, kiểm định, tiện ích orchestration và việc khó biểu diễn quan hệ. Đừng mặc định kéo toàn bộ dữ liệu lớn vào tiến trình Python nếu engine chuyên dụng có thể xử lý theo tập hợp.

dbt và SQLMesh là ví dụ framework tổ chức phép biến đổi phân tích có phiên bản và dependency. Chúng hỗ trợ dựng model, kiểm thử, tài liệu và workflow môi trường. Cú pháp/cam kết khác nhau; hiểu mã nào được compile/chạy ở warehouse và giữ logic nghiệp vụ có thể review.

## Functional Data Engineering

Phép biến đổi functional là hàm dễ dự đoán của đầu vào tường minh, tạo đầu ra. Tách tính toán thuần khỏi gọi mạng và ghi dữ liệu giúp test dễ, retry an toàn. Đặt side effect ở ranh giới rõ: lấy nguồn, kiểm định, biến đổi tất định rồi commit kết quả.

Version hóa đầu vào/đầu ra khi phù hợp. Chạy lại cùng input và mã nên cho kết quả như nhau hoặc chỉ rõ nguồn thay đổi. Functional style không có nghĩa task nào cũng là hàm thuần; đây là cách cô lập bất định để kiểm thử hành vi.

## ETL, ELT và mở rộng SQL

ETL biến đổi trước khi nạp vào đích phân tích. Nó có thể lọc/giảm dữ liệu nhạy cảm sớm và cần thiết nếu đích không xử lý được dạng nguồn. ELT đưa dữ liệu gần nguồn vào trước rồi biến đổi bằng engine đích. Cách này hỗ trợ replay và giữ raw, nhưng cần kiểm soát retention, quyền và chi phí.

Thiết kế lai phổ biến: trích xuất có bảo vệ riêng tư ở biên, nạp biểu diễn truy vết được rồi áp dụng biến đổi dùng lại trong warehouse. Chọn nơi biến đổi theo luân chuyển dữ liệu, compute, quyền, tái sử dụng, xử lý lỗi và khả năng bảo trì.

SQL engine mở rộng chuẩn SQL với kiểu/phép toán riêng dialect. Dùng extension khi có nhu cầu thật; bao bọc hoặc kiểm thử nếu cần khả năng chuyển đổi. Semantic SQL là biểu đạt khái niệm nghiệp vụ qua model/metric được quản trị thay vì lặp lại định nghĩa trong query ad hoc. Đây không phải một dialect chung; cần làm rõ tầng nào phân giải thuật ngữ nghiệp vụ.

## Batch và stream processing

Batch xử lý tập dữ liệu có ranh giới theo lịch; thường dễ replay, test và vận hành khi consumer chấp nhận freshness theo kỳ. Stream xử lý event liên tục, có thể dùng window/watermark để xử lý dữ liệu muộn. Nó đòi hỏi định nghĩa event-time, quản lý state, delivery và giám sát vận hành rõ.

Kiến trúc streaming không tự bảo đảm latency đầu-cuối thấp nếu nguồn phát trễ hoặc consumer phía sau vẫn đọc theo batch. Định nghĩa mục tiêu freshness toàn luồng và đo thực tế.

## Pushdown và vị trí truy vấn

Pushdown thực thi filter, projection hoặc aggregate đủ điều kiện gần storage/nguồn, giảm di chuyển dữ liệu. Có xảy ra hay không tùy connector, biểu thức, kiểu, quyền và khả năng engine. Kiểm tra plan và byte thực đọc; đừng giả định filter viết sớm trong SQL được push xuống.

Chọn nơi biến đổi bằng cách cân nhắc tải nguồn, egress, riêng tư, compute, tái dùng và cô lập lỗi. Chạy gần nguồn có thể hiệu quả nhưng tăng phụ thuộc hoặc ảnh hưởng database vận hành.

## Orchestration declarative và imperative

Workflow imperative nêu bước cần chạy và thứ tự. Hệ thống declarative mô tả đầu ra, phụ thuộc, điều kiện mong muốn rồi sinh execution plan. Imperative làm control flow rõ; declarative có thể làm asset/trạng thái dễ kiểm tra. Cả hai cần ranh giới side effect, idempotency, test và khôi phục.

DAG mô hình hóa phụ thuộc task. Workflow hướng asset mô hình hóa dataset được tạo cùng lineage/freshness. Chọn dựa trên đơn vị nhóm cần suy luận chính là thao tác hay data asset bền vững; nhiều hệ thống kết hợp cả hai.

## Chọn orchestrator

Airflow thường dùng lập lịch/giám sát task DAG. Dagster nhấn mạnh asset dữ liệu được định nghĩa bằng phần mềm và khả năng quan sát asset. Kestra cung cấp orchestration workflow theo hướng cấu hình với các tích hợp. Tính năng đổi theo thời gian; hãy so triển khai hiện tại, tích hợp, ngữ nghĩa lịch, quyền, backfill và gánh nặng vận hành.

Notebook hữu ích cho khám phá và truyền đạt phân tích. Khi đưa vào production theo lịch, cần version control, kiểm định tham số, test, quản lý bí mật, môi trường tái tạo, logging và retry; phiên notebook tương tác không phải contract production.

## Mẫu xử lý đáng tin cậy

1. Định nghĩa khoảng đầu vào và ngữ nghĩa event time.
2. Kiểm định schema và định danh bắt buộc trước biến đổi.
3. Áp dụng phép biến đổi tất định cùng quy tắc nghiệp vụ tường minh.
4. Ghi nguyên tử hoặc idempotent tại grain đã định.
5. Đối soát số dòng và measure chính.
6. Chỉ công bố sau khi vượt cổng chất lượng bắt buộc.
7. Ghi run ID, phiên bản mã/nguồn và hướng dẫn khôi phục.

## Bài tập

Xây pipeline đơn hàng chạy ngày có correction tới muộn. Nạp nguồn bằng Python, biến đổi bằng SQL, thêm quality check và orchestration backfill. So DAG task với thiết kế asset. Kiểm tra query plan cho filter ngày và ghi lại pushdown có xảy ra không.

## Học tiếp

- [Python cho pipeline dữ liệu](../python/data-pipelines.html)
- [Điều phối pipeline](../data-engineering/orchestration.html)
- [Ingestion, CDC và streaming](../data-engineering/ingestion-cdc-and-streaming.html)
- [Tối ưu truy vấn SQL](../sql/query-optimization.html)