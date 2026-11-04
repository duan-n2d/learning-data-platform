---
title: Mẫu thiết kế Text2SQL
description: Chuyển câu hỏi nghiệp vụ thành SQL đã kiểm định bằng guardrail.
order: 2
tags: [Text2SQL, LLM, SQL]
---

# Mẫu thiết kế Text2SQL

Text2SQL không chỉ là prompt engineering; đây là bài toán thiết kế hệ thống.

## Thu hẹp tác vụ

Chỉ công khai một tập model, metric, dimension và quan hệ được tuyển chọn. Với mỗi câu hỏi, truy xuất định nghĩa liên quan thay vì gửi toàn bộ schema kho dữ liệu. Hỏi làm rõ khi thiếu khoảng ngày, entity hoặc metric.

## Luồng khuyến nghị

```text
Câu hỏi
-> nhận diện ý định
-> truy xuất ngữ cảnh ngữ nghĩa
-> sinh SQL
-> kiểm định SQL
-> dry-run
-> trình bày kết quả
```

## Guardrail

- Chỉ cho phép truy vấn SELECT.
- Giới hạn bảng được quét.
- Kiểm định cột và quan hệ join.
- So sánh SQL sinh với ví dụ chuẩn đã biết.
- Lưu câu hỏi thất bại để đánh giá.
- Dùng SQL parser, quyền database, timeout và giới hạn kết quả để cưỡng chế chính sách.
- Giữ credential và quyết định chính sách ngoài mã do model sinh.
- Trả định nghĩa metric, kỳ thời gian, bộ lọc và tham chiếu truy vấn cùng kết quả.

## Trạng thái end-to-end

Mô hình hóa tương tác thành trạng thái rõ: `needs_clarification`, `unsupported`, `invalid_sql`, `query_rejected`, `query_failed`, `answered`. Nhờ vậy, trường hợp không trả lời an toàn có thể quan sát và UI đưa ra bước tiếp theo phù hợp. Không retry SQL bị từ chối bằng cách nới chính sách; chỉ retry sinh trong cùng ràng buộc với số lần giới hạn.

## Trường hợp đánh giá

Với mỗi fixture, ghi câu hỏi tự nhiên, metric kỳ vọng, bộ lọc, cách hiểu ngày tháng, kết quả kỳ vọng và có cần hỏi lại không. Thêm test cho đồng hạng, kết quả rỗng, ranh giới timezone, NULL, join không hợp lệ, bảng ngoài phạm vi và yêu cầu vượt kiểm soát. Đánh giá ngữ nghĩa riêng với định dạng SQL.

## Bài tập

Tạo năm câu hỏi trên một mart đơn hàng. Với mỗi câu, ghi hợp đồng metric và kết quả kỳ vọng trước khi yêu cầu model sinh SQL. Thêm một câu mơ hồ và một câu ngoài phạm vi; cả hai không được chạy database.