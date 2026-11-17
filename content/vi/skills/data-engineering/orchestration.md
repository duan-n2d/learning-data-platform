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

**Các kiểu lỗi của backfill.** Chạy backfill không giống chạy lặp lại nhiều lần một lượt chạy theo lịch bình thường; nó lỗi theo những cách riêng:

- **Quá tải tài nguyên:** quá nhiều task backfill chạy đồng thời tranh giành năng lực cluster hoặc warehouse mà các lượt chạy theo lịch thường cần, khiến backfill làm đói chính các pipeline mà nó định sửa. Giảm thiểu bằng giới hạn concurrency hoặc pool riêng, giới hạn số task backfill chạy cùng lúc, tách biệt khỏi năng lực dành cho lượt chạy theo lịch.
- **Quá tải chi phí:** xử lý lại nhiều tuần hoặc nhiều tháng dữ liệu cùng lúc có thể làm chi phí compute hoặc warehouse tăng vọt vượt xa một lượt chạy theo lịch thông thường, thường không ai nhận ra cho đến khi hóa đơn tới. Giảm thiểu bằng cách chia backfill thành các khoảng ngày nhỏ hơn và theo dõi chi phí khi từng phần hoàn tất, thay vì chạy toàn bộ khoảng một lúc.
- **"Lạc giữa chừng" khi lỗi một phần:** một backfill chạy lâu bị lỗi giữa chừng, và không rõ khoảng ngày nào đã thành công, khoảng nào lỗi, khoảng nào chưa từng chạy. Giảm thiểu bằng ghi idempotent cộng với log hoàn thành hoặc checkpoint rõ ràng theo từng phần, để lần retry xác định chính xác phần nào còn thiếu và chỉ xử lý lại phần đó, thay vì toàn bộ khoảng hoặc không gì cả.

## Tín hiệu vận hành

Theo dõi thời điểm bắt đầu/kết thúc, số lần thử task, số bản ghi vào/ra, freshness, thời lượng và nhóm lỗi. Cảnh báo khi trễ cam kết phân phối hoặc lỗi kéo dài, không cảnh báo mọi lần retry tạm thời. Nối cảnh báo với runbook có chủ sở hữu, bước retry an toàn và hướng escalation.

## Tìm hiểu sâu hơn

- [So sánh cron và các orchestrator](orchestrators-compared.html): khi nào cron là đủ, và so sánh Airflow, Dagster, Prefect, Mage.
- [DataOps, CI/CD và hạ tầng dưới dạng mã](dataops-ci-cd-and-iac.html): CI/CD cho dữ liệu, continuous deployment, data as code và Terraform.
- [Container và Kubernetes cho dữ liệu](containers-and-kubernetes-for-data.html): Docker image cho task pipeline và chạy chúng trên Kubernetes.

## Bài tập

Vẽ DAG cho dữ liệu đơn hàng và khách hàng hằng ngày cấp cho mart doanh thu. Đánh dấu task chạy song song, chọn chiến lược idempotency cho từng lần ghi, mô phỏng lỗi sau staging nhưng trước công bố. Chỉ ra retry tránh nhân đôi fact và sự cố được phát hiện ra sao.