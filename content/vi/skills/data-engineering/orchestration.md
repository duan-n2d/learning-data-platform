---
title: Điều phối pipeline
description: Lập lịch công việc dữ liệu với phụ thuộc, retry, backfill và khôi phục rõ ràng.
order: 3
tags: [điều phối, Airflow, độ tin cậy]
---

# Điều phối pipeline

Orchestrator điều phối công việc; không nên giấu logic nghiệp vụ trong mê cung task. Giữ task đủ nhỏ để quan sát và khôi phục, nhưng không nhỏ đến mức chi phí lập lịch lấn át xử lý.

## Mô hình hóa đồ thị phụ thuộc

Khai báo rõ phụ thuộc thật: ingestion partition nguồn, kiểm định, biến đổi staging, dựng mart, đối soát rồi công bố. Các nguồn độc lập có thể chạy song song nếu giới hạn tài nguyên và kỳ vọng downstream cho phép.

Mỗi task cần đầu vào, đầu ra, chủ sở hữu, timeout và nhóm lỗi rõ ràng. Ưu tiên truyền tham chiếu tới dữ liệu bền vững thay vì payload lớn qua metadata của orchestrator.

## DAG, asset và kiểu thực thi

DAG hướng task mô tả thao tác và phụ thuộc. Workflow hướng asset tập trung vào dataset hoặc đầu ra bền vững được tạo ra, lineage và các check để đầu ra có thể sử dụng. Cả hai đều phù hợp; chọn abstraction giúp hiểu rõ chủ sở hữu, freshness và khôi phục.

Điều phối imperative viết rõ cách chạy từng bước. Điều phối declarative mô tả đầu ra, phụ thuộc và điều kiện mong muốn để công cụ lập kế hoạch thực thi. Functional data engineering ưu tiên phép biến đổi tất định từ đầu vào tường minh sang đầu ra có phiên bản; cô lập side effect như gọi mạng và ghi dữ liệu ở rìa. Các ý tưởng này bổ trợ nhau nhưng không thay thế idempotency và kiểm tra vận hành.

Công cụ có vai trò khác nhau và có vùng giao nhau. Airflow thường dùng lập lịch đồ thị task; Dagster nhấn mạnh data asset được định nghĩa bằng phần mềm và khả năng quan sát; dbt và SQLMesh tập trung biến đổi phân tích có phiên bản cùng phụ thuộc model; notebook hữu ích cho khám phá nhưng cần kiểm soát bổ sung trước khi lập lịch production. Hãy kiểm tra tính năng hiện tại và ràng buộc triển khai thay vì chọn chỉ theo nhãn.

## Idempotency và retry

Thiết kế task sao cho cùng đầu vào chạy lại sẽ tạo kết quả đã commit giống nhau. Dùng khóa ổn định, thay thế partition, ghi transaction hoặc merge phù hợp với đích. Retry dành cho lỗi tạm thời như timeout/dịch vụ chập chờn; dữ liệu sai xác định phải báo lỗi rõ, không retry vô hạn.

Dùng exponential backoff có giới hạn và jitter cho dependency tạm thời. Làm số lần retry và timeout dễ quan sát. Task hoàn tất sau khi caller timeout vẫn có thể đã ghi dữ liệu; cần output idempotent và đối soát, không mặc định lỗi nghĩa là không có side effect.

## Backfill và lịch chạy

Phân biệt event time với processing time. Lượt chạy hằng ngày cần khai báo khoảng nghiệp vụ và timezone xác định ranh giới. Backfill phải dùng cùng mã biến đổi với lịch chạy, có khoảng ngày tường minh và concurrency được kiểm soát.

Với dữ liệu đến muộn, dùng lookback hoặc quy trình sửa dữ liệu đã tài liệu hóa. Đừng dựa vào một watermark chỉ tiến lên nếu nguồn có thể sửa dữ liệu cũ.

## Tín hiệu vận hành

Theo dõi thời điểm bắt đầu/kết thúc, số lần thử task, số bản ghi vào/ra, freshness, thời lượng và nhóm lỗi. Cảnh báo khi trễ cam kết phân phối hoặc lỗi kéo dài, không cảnh báo mọi lần retry tạm thời. Nối cảnh báo với runbook có chủ sở hữu, bước retry an toàn và hướng escalation.

## Bài tập

Vẽ DAG cho dữ liệu đơn hàng và khách hàng hằng ngày cấp cho mart doanh thu. Đánh dấu task chạy song song, chọn chiến lược idempotency cho từng lần ghi, mô phỏng lỗi sau staging nhưng trước công bố. Chỉ ra retry tránh nhân đôi fact và sự cố được phát hiện ra sao.