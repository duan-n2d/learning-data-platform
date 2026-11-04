---
title: Tối ưu truy vấn SQL
description: Các mẫu thực tế để cải thiện hiệu năng truy vấn phân tích.
order: 2
tags: [SQL, hiệu năng]
---

# Tối ưu truy vấn SQL

Bắt đầu tối ưu bằng cách hiểu dung lượng dữ liệu, lực lượng kết hợp (cardinality), chỉ mục, phân vùng và query plan.

## Quy trình tinh chỉnh có thể lặp lại

1. Xác định kết quả đúng, lưu truy vấn baseline và đo thời gian trên dữ liệu đại diện.
2. Xem plan để tìm scan, join, sort, spill và ước tính lệch xa số dòng thực tế.
3. Kiểm tra grain và lực lượng join trước khi sửa cú pháp.
4. Mỗi lần chỉ thay đổi một yếu tố và xác minh kết quả không đổi.
5. So thời gian và tài nguyên trong cùng điều kiện; chỉ giữ thay đổi nếu nó giúp workload mục tiêu.

Mỗi SQL engine khác nhau, nên dùng tài liệu và định dạng plan của kho dữ liệu đang dùng, không mặc định một mẫu áp dụng giống nhau ở mọi nơi.

## Checklist

- Lọc sớm khi phù hợp.
- Tránh join nhiều-nhiều ngoài ý muốn.
- Xác định grain bảng trước khi join.
- Dùng partition hoặc clustering cho fact table lớn.
- Materialize phép biến đổi được lặp lại thường xuyên.
- Chỉ chọn cột cần thiết cho các bước sau.
- So sánh số dòng ước tính và thực tế quanh join/filter.
- Dùng partition filter khớp khóa phân vùng và khoảng thời gian cần truy vấn.
- Kiểm tra correlated subquery có thể viết rõ hơn bằng join/window không.
- Đo trước khi thêm index, clustering hoặc materialization; mỗi thứ đều tốn chi phí ghi, lưu trữ và bảo trì.

## Ví dụ fanout khi join

Nếu một đơn có 3 dòng hàng và 2 bản ghi lịch sử trạng thái, join cả hai bảng con trước khi tổng hợp có thể tạo 6 dòng cho đơn đó. Tổng doanh thu cấp đơn bị nhân lên. Hãy tổng hợp từng bảng con về grain join dự kiến trước, hoặc chỉ join quan hệ thực sự cần cho câu hỏi.

## Không nên tối ưu một cách máy móc

- Truy vấn ngắn hơn chưa chắc chạy nhanh hơn.
- CTE có thể được inline hoặc materialize tùy engine.
- Lọc sớm chỉ hữu ích nếu giảm khối lượng xử lý và có thể đẩy xuống scan.
- Aggregate xấp xỉ đánh đổi độ chính xác lấy hiệu năng, cần được sản phẩm phê duyệt rõ.

## Bài tập

Chọn truy vấn chậm gồm một fact table và hai dimension. Ghi grain từng bảng, cardinality join dự kiến và số dòng sau lọc. So sánh plan trước/sau một thay đổi, rồi đối soát kết quả trên fixture nhỏ có đáp án chính xác.