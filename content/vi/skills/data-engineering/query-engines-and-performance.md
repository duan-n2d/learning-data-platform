---
title: Query Engine và nội bộ hiệu năng
description: Hiểu scan, pushdown, materialization và các đánh đổi truy vấn phân tán.
order: 10
tags: [query engine, hiệu năng, OLAP, materialized view]
---

# Query Engine và nội bộ hiệu năng

Hiệu năng truy vấn phụ thuộc cách bố trí dữ liệu, hình dạng SQL, kế hoạch của engine, concurrency và giới hạn tài nguyên. Học cách đọc bằng chứng từ plan và metric workload thay vì tối ưu chỉ dựa cú pháp.

## Vòng đời truy vấn đơn giản hóa

1. **Parse và validate:** kiểm tra cú pháp, tên, kiểu, quyền và quy tắc dialect.
2. **Lập kế hoạch:** phân giải relation, chọn thứ tự join, cách scan, aggregate và trao đổi dữ liệu.
3. **Tối ưu:** ước tính số dòng/chi phí, giản lược biểu thức và đẩy công việc phù hợp xuống storage hoặc nguồn.
4. **Thực thi:** scan dữ liệu, chuyển kết quả trung gian, join, aggregate, sort và trả đầu ra.
5. **Quan sát:** kiểm tra số dòng thực tế, byte đọc, spill, thời gian chờ, memory và thời lượng.

Pipeline chính xác tùy engine. So estimate với actual để tìm vấn đề cardinality hoặc thống kê.

## Pushdown và di chuyển dữ liệu

Predicate pushdown áp dụng filter gần nguồn; projection pushdown chỉ đọc cột cần thiết. Partition pruning bỏ qua partition không liên quan, còn định dạng cột có thể bỏ cột/row group dựa trên thống kê. Các tối ưu này có điều kiện: cast, function, predicate không hỗ trợ hoặc connector nguồn có thể chặn pushdown.

Join phân tán có thể shuffle dòng giữa worker. Khóa cardinality cao, lệch dữ liệu, kết quả trung gian lớn và thứ tự join kém làm tăng áp lực mạng/memory. Xem plan và skew thay vì nghĩ engine phân tán khiến mọi truy vấn đều rẻ.

## Materialized view và cache

Materialized view lưu kết quả tính trước để dùng lại. Nó giảm công việc lặp nhưng thêm độ trễ refresh, chi phí lưu trữ, độ phức tạp invalidation và nguy cơ không khớp freshness. Xác định chủ sở hữu, cách refresh, query nào dùng và đối soát với bảng gốc ra sao.

Cache hiệu quả với lượt đọc lặp nhưng có thể trả dữ liệu cũ hoặc gây tranh chấp. Làm rõ freshness và không trình bày kết quả cache như mới nhất nếu contract không đảm bảo.

## Cô lập workload và compute/storage

Tách compute khỏi storage có thể scale workload độc lập và cô lập BI tương tác khỏi biến đổi batch. Điều đó không tự loại tranh chấp: quota chung, metadata service, hệ thống nguồn và giới hạn concurrency vẫn có thể nghẽn. Dùng lớp workload và ngân sách tài nguyên gắn với tác động người dùng.

## Đọc plan bằng dữ liệu thực

- Tìm full scan và byte đọc; xác minh partition filter và cột được chọn.
- Kiểm tra kích thước đầu vào, thứ tự, phân phối và số dòng thực tế ở join.
- Tìm exchange, skew, spill và kết quả trung gian lớn.
- So thời gian chờ với thời gian chạy để phân biệt thiếu năng lực với query kém hiệu quả.
- Thay từng yếu tố, so kết quả/tài nguyên và giữ baseline có thể tái tạo.

Full scan không mặc định sai với bảng nhỏ hoặc phép tính toàn bảng. Tối ưu theo chi phí/latency workload đã đo, không phải xóa operator khỏi plan bằng mọi giá.

## Đánh đổi hệ thống phân tán

Hệ thống phân tán đánh đổi consistency, availability, latency và khả năng chịu lỗi tùy thao tác/ranh giới hệ thống. CAP là mô hình hẹp về consistency và availability khi có network partition, không phải checklist chọn warehouse. Với nền tảng dữ liệu, hãy hiểu cam kết thật về transaction, replication lag, metadata commit và đọc sau ghi.

## Bài tập

Kiểm tra query nối fact lớn với hai dimension. Ghi byte scan, số dòng estimate/actual, exchange, spill và thời gian chờ. Thử partition filter và pre-aggregation riêng, đối soát đầu ra và giải thích đánh đổi.