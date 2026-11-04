---
title: Dự án 2 - Chatbot Text2SQL
description: Xây chatbot chuyển câu hỏi nghiệp vụ thành SQL đã kiểm định.
order: 2
tags: [Text2SQL, chatbot, lớp ngữ nghĩa]
---

# Dự án 2 - Chatbot Text2SQL

## Mục tiêu

Xây trợ lý phân tích nhỏ, trả lời một tập câu hỏi nghiệp vụ giới hạn dựa trên mart của Dự án 1. Xem đây là sản phẩm chỉ đọc có giới hạn rõ ràng, không phải giao diện SQL đa năng.

## Vì sao cần dự án này?

Text2SQL không chỉ là sinh SQL. Hệ thống cần logic nghiệp vụ đúng, định nghĩa đáng tin cậy và kiểm định trước khi chạy. Một câu trả lời trôi chảy vẫn có thể sai nếu chọn nhầm metric, ngày hoặc đường join.

## Kiến trúc

```text
Câu hỏi người dùng
-> tra cứu ngữ cảnh ngữ nghĩa
-> sinh SQL
-> parse và kiểm định chính sách
-> dry-run / ước tính chi phí
-> thực thi trên kho dữ liệu chỉ đọc
-> định dạng kết quả kèm provenance
```

## Xác định phạm vi được hỗ trợ

Bắt đầu với 3-5 metric đã được rà soát và một vài dimension. Với mỗi metric, ghi lại:

| Trường | Câu hỏi cần chốt |
|---|---|
| Tên và chủ sở hữu | Ai duyệt thay đổi định nghĩa? |
| Grain | Metric tính theo đơn, dòng hàng, khách hay ngày? |
| Biểu thức | Model và cột đáng tin nào hiện thực metric? |
| Bộ lọc | Loại trạng thái, kênh hay bản ghi thử nghiệm nào? |
| Cơ sở thời gian | Timestamp nào xác định kỳ báo cáo? |
| Tính cộng gộp | Có thể cộng theo thời gian, khách hàng, tiền tệ không? |
| Ví dụ | Câu hỏi tự nhiên nào và kết quả kỳ vọng nào là chuẩn? |

Không để model tự nghĩ ra đường join. Chỉ cung cấp quan hệ đã khai báo trong mô hình ngữ nghĩa; metric mơ hồ phải nằm ngoài phạm vi cho tới khi chủ sở hữu giải quyết.

## Ranh giới kiểm định

Dùng SQL parser và danh tính database chỉ có quyền trên schema được duyệt. Validator phải từ chối nhiều statement, thao tác ghi, DDL, relation ngoài danh sách, cột lạ và truy vấn không giới hạn. Kiểm tra từ khóa đơn thuần không phải ranh giới bảo mật: cú pháp lồng nhau và khác biệt dialect cần parser cùng quyền database làm nhiều lớp phòng vệ.

Trước khi chạy, đặt timeout và giới hạn số dòng; dùng dry-run hoặc query-plan của kho nếu có. Không đưa thông tin xác thực cho model. Ghi log câu hỏi, mã ngữ cảnh ngữ nghĩa, phiên bản model/prompt, kết quả kiểm định, query ID và độ trễ; hạn chế lưu nội dung nhạy cảm trong truy vấn/kết quả.

## Kế hoạch đánh giá

Tạo bộ câu hỏi có phiên bản, kèm metric, bộ lọc, khoảng thời gian và kết quả kỳ vọng. Bao gồm:

- Tra cứu trực tiếp, so sánh thời gian, xếp hạng và nhiều bộ lọc.
- Cách diễn đạt mơ hồ cần hỏi lại.
- Metric không hỗ trợ và bảng ngoài phạm vi cần bị từ chối.
- Ngày biên, kết quả rỗng, NULL và trường hợp đồng hạng.
- Đầu vào tìm cách ghi đè quy tắc hoặc yêu cầu dữ liệu riêng tư.

Theo dõi riêng tỷ lệ thực thi thành công, độ đúng kết quả, vi phạm chính sách, chất lượng hỏi lại, độ trễ và chi phí. So khớp SQL chính xác thường quá khắt khe; hãy so sánh kết quả và xác minh truy vấn tuân thủ hợp đồng metric.

## Sản phẩm bàn giao

- Định nghĩa metric ngữ nghĩa
- Mẫu prompt
- SQL validator
- Bộ câu hỏi đánh giá
- UI web hoặc Streamlit
- Báo cáo phân tích lỗi
- Vai trò database chỉ đọc, timeout và giới hạn kết quả
- Audit event chứa mã model, prompt, metric và truy vấn
- Trạng thái từ chối/hỏi làm rõ rõ ràng trong UI

## Tiêu chí nghiệm thu

- Câu hỏi được hỗ trợ trả kết quả đúng trên database kiểm thử cố định.
- Câu hỏi mơ hồ/ngoài phạm vi không tạo metric đoán mò hoặc chạy không an toàn.
- Vai trò thực thi không thể ghi dữ liệu hoặc đọc ngoài schema được duyệt.
- Mỗi câu trả lời hiển thị định nghĩa metric, kỳ thời gian và bộ lọc liên quan.
- Có thể chạy lại đánh giá sau khi đổi prompt, model hoặc định nghĩa ngữ nghĩa.