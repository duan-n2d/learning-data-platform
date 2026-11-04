---
title: Vòng đời và thực hành Data Engineering
description: Kết nối khám phá, thiết kế, bàn giao, vận hành và phát triển thành vòng đời kỹ nghệ có thể lặp lại.
order: 11
tags: [vòng đời data engineering, thực hành kỹ nghệ, nghề nghiệp]
---

# Vòng đời và thực hành Data Engineering

Data engineering là vòng đời liên tục, không phải xây pipeline một lần rồi thôi. Công việc đáng tin cậy bắt đầu từ nhu cầu quyết định/sản phẩm và tiếp tục qua hỗ trợ, thay đổi đến khi ngừng sử dụng.

## Các giai đoạn vòng đời

1. **Khám phá:** xác định người dùng, quyết định, hệ thống nguồn, ràng buộc và kết quả đo được.
2. **Thiết kế:** định nghĩa contract, grain, kiến trúc, quyền, freshness, hành vi lỗi và chủ sở hữu.
3. **Ingestion:** lấy snapshot hoặc thay đổi kèm định danh truy vết và checkpoint khôi phục.
4. **Biến đổi:** tạo model được kiểm thử, tài liệu hóa với ngữ nghĩa nghiệp vụ rõ.
5. **Phục vụ:** công bố dữ liệu qua mart, semantic model, BI, API hoặc ứng dụng có kiểm soát.
6. **Vận hành:** quan sát chất lượng, freshness, latency, chi phí, bảo mật và sự cố; xử lý theo runbook.
7. **Phát triển hoặc ngừng:** rà mức sử dụng/phụ thuộc, chuyển consumer, thông báo thay đổi phá vỡ và xóa dữ liệu cũ an toàn.

Đây là các vòng phản hồi. Sự cố production có thể cho thấy contract chưa rõ; dữ liệu sử dụng có thể chỉ ra model đắt tiền không còn phục vụ nhu cầu.

## Thực hành kỹ nghệ

- Quản lý phép biến đổi trong version control và review.
- Tự động hóa build, test và kiểm tra triển khai lặp lại.
- Giữ thay đổi đủ nhỏ để chẩn đoán và rollback.
- Tách quyền truy cập dữ liệu development, test và production.
- Tài liệu hóa quyết định/giả định mà người bảo trì sau cần biết.
- Đo hành vi dịch vụ từ góc nhìn consumer, không chỉ trạng thái task.

## Data Engineer và Software Engineer

Hai vai trò giao nhau ở lập trình, kiểm thử, tư duy hệ thống và vận hành. Data engineering bổ sung trách nhiệm về ý nghĩa dữ liệu, grain, hành vi thời gian, chất lượng, lineage và mẫu truy cập phân tích. Software engineering đóng góp thực hành có giá trị như thiết kế module, code review, CI/CD, API contract và ứng phó sự cố. Không vai trò nào chỉ là vận hành công cụ; cả hai cần hiểu hệ thống và người dùng.

## Xây bằng chứng portfolio

Dự án tốt cho thấy vấn đề, kiến trúc, contract dữ liệu, đánh đổi, test, sự cố quan sát được, khôi phục và hạn chế đã biết. Có hướng dẫn setup tái tạo và demo ngắn. Giải thích lý do chọn công cụ và điều gì thay đổi ở quy mô lớn; danh sách công nghệ dài là bằng chứng yếu hơn hệ thống chạy được, dễ hiểu.

## Bài tập

Viết kế hoạch vòng đời một trang cho đồ án kho dữ liệu: người dùng, quyết định thiết kế, kiểm tra trước phát hành, tín hiệu vận hành, chủ sở hữu sự cố, quy trình breaking change và điều kiện ngừng. Nêu một phản hồi production làm thay đổi thiết kế.