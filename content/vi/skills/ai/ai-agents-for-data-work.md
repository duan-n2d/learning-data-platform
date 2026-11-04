---
title: AI Agent trong công việc dữ liệu
description: Hiểu agent dùng công cụ và đặt chúng trong workflow dữ liệu có giới hạn, quan sát được.
order: 5
tags: [AI agent, agentic workflow, kỹ nghệ dữ liệu]
---

# AI Agent trong công việc dữ liệu

AI agent dùng model để chọn hoặc sắp xếp hành động, thường thông qua công cụ, dựa trên mục tiêu và kết quả quan sát được. Workflow chỉ có một lần gọi model với bước cố định thường nên gọi là chain. Chỉ dùng agent nếu lựa chọn công cụ thích ứng đem lại giá trị đo được so với quy trình tất định đơn giản hơn.

## Vòng lặp agent có ranh giới

```text
Mục tiêu người dùng
-> kiểm tra chính sách và phạm vi
-> model đề xuất công cụ cùng tham số
-> ứng dụng kiểm định quyền và tham số
-> công cụ chạy với quyền/timeout giới hạn
-> kết quả trả về như bằng chứng không đáng tin
-> model giải thích, hỏi lại hoặc đề xuất bước tiếp
-> cần người duyệt trước hành động có hệ quả
```

Ứng dụng sở hữu authorization và side effect. Model có thể đề xuất query hoặc hành động; không được tự cấp thêm quyền hay vượt kiểm định dựa trên kết quả công cụ.

## Tác vụ phù hợp cho Data Engineering

- Tìm tài liệu được phép dùng và trả tham chiếu nguồn.
- Soạn SQL để người duyệt xem.
- Tóm tắt log pipeline lỗi kèm liên kết run và runbook liên quan.
- Đề xuất test hoặc tài liệu schema cho thay đổi đã review.
- Phân loại bản ghi trích xuất vào hàng đợi duyệt rõ ràng.

Tác vụ sửa dữ liệu production, thay quyền, deploy mã hoặc kích hoạt job tốn kém cần authorization mạnh và xác nhận rõ. Tự động chạy hoàn toàn không phải mặc định.

## Thiết kế tool và trạng thái

Cung cấp một tập tool nhỏ, có kiểu, tham số hẹp và đầu ra rõ. Kiểm định mọi tham số phía server, cưỡng chế danh tính/giới hạn dòng/thao tác và giữ bí mật ngoài ngữ cảnh model. Làm thay đổi trạng thái tường minh, có audit. Giới hạn số lần gọi, retry, thời gian chạy và chi phí; định nghĩa điều kiện dừng an toàn và đường chuyển người.

Xem tài liệu truy xuất, log, kết quả database và lỗi tool là đầu vào không đáng tin. Chúng có thể sai hoặc chứa prompt injection. Tách policy khỏi evidence, giới hạn từng tool độc lập và test các yêu cầu làm agent lộ dữ liệu/gọi tool không được phép.

## Đánh giá và vận hành

Đánh giá riêng thành công tác vụ và chọn tool đúng. Bao gồm mục tiêu mơ hồ, dependency không khả dụng, kết quả gây hiểu nhầm, từ chối quyền, prompt injection, timeout và hành động cần duyệt. Theo dõi tần suất gọi tool, tham số sai, retry, escalation, latency, chi phí và override của con người. Lưu trace có ID/phiên bản nhưng giảm thiểu nội dung nhạy cảm.

Dùng workflow tất định nếu rẻ hơn, dễ dự đoán và kiểm toán hơn. Nếu agent thật sự phù hợp, triển khai theo giai đoạn với quyền hạn tăng dần, người duyệt cho tác động rủi ro, rollback và công tắc dừng.

## Bài tập

Thiết kế trợ lý điều tra lỗi freshness dữ liệu. Cho phép đọc trạng thái pipeline, tìm runbook được duyệt và soạn chẩn đoán. Không cho phép chạy lại job hoặc sửa dữ liệu khi chưa duyệt. Nêu schema tool, phạm vi quyền, trường hợp đánh giá, log, escalation và điều kiện dừng.