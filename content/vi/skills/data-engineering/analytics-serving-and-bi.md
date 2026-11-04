---
title: Phục vụ dữ liệu phân tích và BI
description: Cung cấp metric được quản trị qua dashboard, OLAP, API và giao diện ngữ nghĩa.
order: 9
tags: [BI, OLAP, analytics API, serving]
---

# Phục vụ dữ liệu phân tích và BI

Analytics serving là giao diện giữa dữ liệu đáng tin và quyết định của người dùng. Chọn giao diện theo đối tượng, độ trễ, nhu cầu khám phá, tính nhất quán và trách nhiệm vận hành.

## Từ báo cáo tới phân tích tương tác

Báo cáo truyền thống thường trình bày metric định sẵn theo lịch. BI hiện đại hỗ trợ lọc, drill-down, khám phá và chia sẻ. Hệ thống OLAP tổ chức/tổng hợp dữ liệu đa chiều để so measure theo thời gian, sản phẩm, khu vực.

Cube là mô hình khái niệm của measure và dimension, không nhất thiết là cấu trúc khối literal. Cube tổng hợp trước giúp câu hỏi lặp chạy nhanh nhưng tăng độ phức tạp lưu trữ/refresh. Engine cột hiện đại có thể tính tương tự trực tiếp, nên đo trước khi materialize.

## Chọn bề mặt phục vụ

| Bề mặt | Phù hợp với | Điểm cần thiết kế |
|---|---|---|
| Mart warehouse curated | Phân tích dùng lại và BI | Grain, quyền, freshness, contract ổn định |
| Mô hình ngữ nghĩa BI | Metric nhất quán và self-service | Chủ sở hữu metric, hành vi filter, version |
| Analytics API | Metric và workflow riêng cho ứng dụng | Xác thực, phân trang, latency, tương thích |
| Truy vấn liên kết (federation) | Truy cập ad hoc nhiều hệ thống | Tải nguồn, ngữ nghĩa lệch, latency, cô lập lỗi |
| Reverse ETL | Kích hoạt dữ liệu warehouse chọn lọc trong công cụ vận hành | Chủ sở hữu ghi, freshness, idempotency, đối soát |

Federation tránh sao chép trong một số trường hợp, nhưng query engine vẫn phải xử lý availability nguồn, khả năng pushdown, quyền và khác biệt schema/ngữ nghĩa. Lớp federation không tự tạo nguồn sự thật duy nhất.

## Nhất quán metric

Giữ định nghĩa metric trong semantic layer hoặc mô hình BI được duyệt. Định nghĩa grain, cơ sở thời gian, bộ lọc, đơn vị, tiền tệ và tính cộng được một lần. Xác nhận dashboard, API và Text2SQL dùng định nghĩa tương thích. Nếu một bề mặt không thể biểu diễn chính xác định nghĩa, hãy tài liệu hóa khác biệt thay vì âm thầm xấp xỉ.

## Xây workflow BI hữu ích

1. Xác định quyết định, người dùng và hành động mà báo cáo hỗ trợ.
2. Thống nhất định nghĩa metric và freshness với chủ sở hữu domain.
3. Thiết kế cho câu hỏi thường gặp trước rồi mới mở khám phá an toàn.
4. Gắn nhãn kỳ, đơn vị, bộ lọc và freshness nguồn trong giao diện.
5. Đo mức sử dụng và chi phí query; loại bỏ phần phức tạp không dùng.
6. Rà thay đổi metric và kiểm tra dashboard quan trọng với fixture chuẩn.

## Bài tập

Lấy doanh thu thanh toán theo ngày và khu vực. Định nghĩa metric, cơ sở ngày; thiết kế một dashboard, một response API và một đường phân tích ad hoc. Nêu cách mỗi bề mặt áp dụng quyền, hiển thị freshness và phát hiện ba bề mặt không khớp.