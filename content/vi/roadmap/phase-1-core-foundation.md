---
title: Giai đoạn 1 - Nền tảng cốt lõi
description: Tháng 1-2 tập trung vào các kỹ năng cốt lõi mà AI không thể thay thế.
order: 1
tags: [SQL, Python, dbt, Airflow, cloud]
---

# Giai đoạn 1 - Nền tảng cốt lõi

Giai đoạn này củng cố năng lực kỹ thuật trước khi phụ thuộc vào AI. AI có thể tăng tốc viết mã, nhưng không thay thế được hiểu biết về chất lượng dữ liệu, mô hình hóa, điều phối và gỡ lỗi. Dành khoảng 6-8 giờ tập trung mỗi tuần trong 8 tuần; có thể điều chỉnh tốc độ nhưng nên giữ thứ tự vì kỹ năng sau dựa trên kỹ năng trước.

## Đầu ra mong đợi

Kết thúc giai đoạn, bạn có thể:

- Giải thích grain và khóa của bộ dữ liệu trước khi join hoặc tổng hợp.
- Theo dấu dữ liệu từ hệ thống vận hành qua lưu trữ/biến đổi tới consumer phân tích.
- Chọn mẫu ingestion và lưu trữ phù hợp với freshness, lịch sử và nhu cầu khôi phục.
- Viết SQL phân tích với ranh giới thời gian rõ ràng, xử lý NULL và kiểm thử trường hợp biên.
- Xây job ingestion Python có thể chạy lặp lại an toàn.
- Chuyển dữ liệu thô thành staging và mart nghiệp vụ có tài liệu.
- Lập lịch các bước phụ thuộc, quan sát được lỗi và thiết kế retry có chủ đích.
- Mô tả nơi dữ liệu được lưu, ai có quyền truy cập và pipeline khôi phục sau sự cố thế nào.

## Lộ trình 8 tuần

| Tuần | Trọng tâm | Thực hành | Bằng chứng hoàn thành |
|---|---|---|---|
| 1 | Kiến trúc platform và grain SQL | Theo dấu đơn hàng từ OLTP tới consumer phân tích; khảo sát dataset nhỏ | Sơ đồ vòng đời, từ điển dữ liệu và thống kê số dòng |
| 2 | Lưu trữ, warehouse và SQL phân tích | So OLTP/OLAP, file/table format và truy vấn dataset đại diện | Ghi chú chọn lưu trữ và fixture window function |
| 3 | Ingestion Python, incremental và CDC | Nạp file/API phân trang; định nghĩa khóa, watermark và replay | Job chạy lại an toàn, log cấu trúc và khử trùng |
| 4 | Mô hình dữ liệu và ERD | Thiết kế fact/dimension; so mô hình logic và vật lý | Mô tả grain, khóa, ERD và lựa chọn modeling có lý do |
| 5 | dbt hoặc công cụ biến đổi tương đương | Tạo model staging, trung gian và mart | Test, tài liệu sinh tự động, build sạch |
| 6 | Chất lượng và hợp đồng | Định nghĩa schema, freshness và quy tắc nghiệp vụ | Test thất bại khi cố ý đưa dữ liệu sai |
| 7 | Điều phối và khôi phục | Lập lịch pipeline và mô phỏng task lỗi | Chạy lại thành công và runbook xử lý lỗi |
| 8 | Cloud và bàn giao | Lưu snapshot raw bất biến, công bố mart đáng tin cậy | Sơ đồ kiến trúc và demo dự án |

## Nhịp học mỗi tuần

1. Đọc một khái niệm và ghi lại các giả định về dữ liệu.
2. Tự triển khai ví dụ nhỏ nhất có ích mà chưa dùng trợ lý AI.
3. Nhờ AI rà soát, rồi kiểm tra từng đề xuất bằng test hoặc tài liệu.
4. Ghi lại một kiểu lỗi và cách phát hiện lỗi đó.
5. Commit một mốc chạy được và cập nhật ngắn README.

Cách làm này đặt AI vào vai trò rà soát và tăng tốc, không phải nguồn sự thật.

## Các mảng trọng tâm

| Mảng | Kết quả cần đạt |
|---|---|
| SQL | Window function, CTE, query plan, mẫu phân tích và grain rõ ràng |
| Python | Ingestion file/API, phân trang, kiểm định, logging và tự động hóa |
| Kiến trúc và lưu trữ | OLTP/OLAP, warehouse/lake/lakehouse, file/table format và ranh giới khôi phục |
| Ingestion | Snapshot đầy đủ, watermark incremental, CDC, đổi schema, khái niệm streaming và backfill |
| Mô hình hóa | ERD, mô hình khái niệm/logic/vật lý, fact, dimension, trade-off chuẩn hóa và lịch sử |
| Biến đổi dữ liệu | Tầng staging đến mart, test, tài liệu và lineage bằng dbt hoặc công cụ tương đương |
| Điều phối | Phụ thuộc, idempotency, retry, backfill và lịch chạy |
| Cloud cơ bản | Object storage, managed database, quyền tối thiểu và triển khai |

## Checklist trước khi chuyển giai đoạn

- [ ] Developer mới có thể chạy dự án từ checkout sạch theo tài liệu.
- [ ] Chạy lại ingestion không âm thầm tạo bản ghi trùng.
- [ ] Test bao phủ ít nhất một ràng buộc khóa, một quy tắc giá trị cho phép và một bất biến nghiệp vụ.
- [ ] Dữ liệu đầu vào cố ý sai bị từ chối hoặc đưa vào khu cách ly với lỗi có thể xử lý.
- [ ] Task lỗi có thể retry mà không làm hỏng dữ liệu đã công bố.
- [ ] Kho dữ liệu có tài liệu về grain, chủ sở hữu và kỳ vọng freshness.
- [ ] Lựa chọn lưu trữ/ingestion có ghi rõ đánh đổi về lịch sử, freshness và khôi phục.
- [ ] Model có ERD được rà soát và giải thích lựa chọn chuẩn hóa hoặc phi chuẩn hóa.

## Đọc cẩm nang chuyên đề

- [Nền tảng Data Engineering](../skills/field-guide/foundations.html)
- [Hạ tầng dữ liệu hiện đại](../skills/field-guide/infrastructure.html)
- [Biến đổi và xử lý dữ liệu](../skills/field-guide/transformation-and-processing.html)

## Sản phẩm bàn giao

Dùng bài [kiến trúc platform](../skills/data-engineering/platform-architecture-and-lifecycle.html), [lưu trữ và table format](../skills/data-engineering/storage-warehousing-and-formats.html), [ingestion, CDC và streaming](../skills/data-engineering/ingestion-cdc-and-streaming.html), cùng [mô hình dữ liệu](../skills/data-engineering/data-modeling.html) khi xây [Dự án 1: Kho dữ liệu phân tích cốt lõi](../projects/project-1-analytics-warehouse.html). Đừng chuyển tiếp chỉ vì mã chạy được một lần; hãy chuyển khi đầu ra có thể tái tạo và đã hiểu các kiểu lỗi.