---
title: Đánh giá và khả năng quan sát AI
description: Đo chất lượng quy trình AI trước khi phát hành và phát hiện thay đổi sau triển khai.
order: 4
tags: [đánh giá, khả năng quan sát, LLM]
---

# Đánh giá và khả năng quan sát AI

Câu trả lời của model có thể trôi chảy nhưng vẫn sai. Đánh giá biến kỳ vọng chất lượng mơ hồ thành ví dụ kiểm thử; khả năng quan sát cho thấy hệ thống hoạt động ra sao với đầu vào thực, dữ liệu thay đổi và giới hạn production.

## Xây bộ đánh giá hữu ích

Thu thập tác vụ đại diện và gắn nhãn hành vi kỳ vọng, không chỉ đáp án tham chiếu. Tùy workflow, ghi passage nguồn, định nghĩa metric, kết quả SQL, trường trích xuất, quyết định từ chối hoặc tuyến chuyển người duyệt. Bao gồm trường hợp thường gặp, biên, mơ hồ, ngoài hỗ trợ và lỗi đã biết.

Khi phù hợp, tách dữ liệu đánh giá khỏi ví dụ trong prompt. Version hóa dataset, nhãn, model, prompt, cấu hình retrieval, parser và snapshot corpus liên quan. Chuyên gia nghiệp vụ cần rà một phần dữ liệu; bộ nhãn sinh tự động có thể lặp lại chính giả định ẩn của model.

## Dùng thước đo theo tác vụ

| Workflow | Thước đo hữu ích |
|---|---|
| Text2SQL | Độ đúng kết quả, vi phạm chính sách, chất lượng hỏi lại, chi phí truy vấn |
| RAG | Recall truy xuất, độ chính xác citation, groundedness, chất lượng từ chối |
| Trích xuất | Precision/recall từng trường, dung sai số, schema lỗi, tỷ lệ chỉnh sửa |
| Mọi workflow | Độ trễ, tỷ lệ lỗi, chi phí token/nhà cung cấp, tỷ lệ cần duyệt |

Không một điểm số nào mô tả toàn bộ sản phẩm. Tách chất lượng, an toàn và vận hành để thay đổi nhanh hơn nhưng kém tin cậy không bị hiểu nhầm là cải thiện tổng thể.

## Phát hành và hồi quy

Thiết lập baseline trước khi đổi model, prompt, công cụ, parser, corpus hoặc định nghĩa ngữ nghĩa. Chạy bộ đánh giá cố định, kiểm tra hồi quy theo loại lỗi và yêu cầu duyệt với thay đổi tác động cao. Khi có thể, triển khai theo giai đoạn và giữ đường rollback.

## Khả năng quan sát production

Ghi request/run ID, phiên bản thành phần, thời lượng, kết quả kiểm định, nguồn truy xuất và quyết định của người duyệt. Tránh lưu nội dung nhạy cảm thô nếu không có nhu cầu, chính sách truy cập và thời hạn lưu được phê duyệt. Ẩn bí mật và dữ liệu cá nhân trước khi log/trace rời khỏi ranh giới tin cậy.

Định nghĩa chỉ số dịch vụ người dùng quan tâm: tính sẵn sàng, freshness, chất lượng câu trả lời/trích xuất, tuổi hàng đợi duyệt và chi phí mỗi kết quả hữu ích. Đặt ngưỡng cảnh báo theo baseline và tác động. Mỗi cảnh báo cần chủ sở hữu và bước xử lý rõ.

## Bài tập

Tạo bộ đánh giá 20 ví dụ cho một workflow, trong đó ít nhất ba ví dụ cần từ chối hoặc chuyển người. Chạy hai phiên bản prompt, so chất lượng theo tác vụ và độ trễ, kiểm tra mọi hồi quy rồi viết quyết định phát hành ngắn kèm hạn chế đã biết.