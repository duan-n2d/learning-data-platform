---
title: Dự án 4 - Pipeline trích xuất LLM
description: Trích xuất bản ghi có cấu trúc từ nguồn phi cấu trúc cùng bước kiểm định.
order: 4
tags: [trích xuất LLM, dữ liệu phi cấu trúc, kiểm định]
---

# Dự án 4 - Pipeline trích xuất LLM

## Mục tiêu

Trích xuất một tập bản ghi nghiệp vụ xác định từ PDF, email, file văn bản hoặc ghi chú bán cấu trúc đại diện. Giữ đủ bằng chứng để người duyệt xác minh từng trường có tác động cao.

## Pipeline

```text
Nguồn phi cấu trúc
-> kiểm tra loại file và trích xuất văn bản
-> chuẩn hóa tất định, theo dõi trang/nguồn
-> model trích xuất theo schema
-> kiểm định cú pháp, nghiệp vụ và liên trường
-> duyệt / cách ly / chấp nhận
-> bản ghi kho dữ liệu có phiên bản
```

## Hợp đồng đầu ra

Định nghĩa bản ghi trước khi viết prompt. Với từng trường, nêu kiểu, bắt buộc hay không, giá trị hợp lệ, quy tắc chuẩn hóa và xử lý khi nguồn không có thông tin. Biểu diễn thiếu dữ liệu bằng null hoặc trạng thái rõ ràng; không khuyến khích model đoán nội dung có vẻ hợp lý.

```json
{
  "record_id": "mã nguồn hoặc ID ổn định được tạo",
  "document_type": "invoice",
  "invoice_date": "2026-03-14",
  "currency": "USD",
  "total_amount": 1250.00,
  "supplier_name": "Example Supplier",
  "evidence": {
    "total_amount": {"page": 2, "quote": "Total due: $1,250.00"}
  },
  "review_status": "needs_review"
}
```

Đây là hợp đồng minh họa, không phải schema hóa đơn áp dụng chung. Gắn bằng chứng với offset, trang hoặc span văn bản ổn định để kiểm toán được chỉnh sửa.

## Độ tin cậy và quy trình duyệt

Làm xử lý idempotent bằng ID nguồn ổn định và content hash. Lưu phiên bản nguồn, parser, prompt, model, thời gian xử lý, lỗi kiểm định và quyết định người duyệt. Retry lỗi nhà cung cấp tạm thời với backoff có giới hạn; không retry vô hạn lỗi đầu vào hoặc schema cố định.

Chuyển bản ghi dựa trên cả độ không chắc chắn lẫn mức tác động. Tên nhà cung cấp ít tin cậy có thể cần duyệt; khoản thanh toán giá trị cao cần duyệt ngay cả khi model tự tin. Hiệu chỉnh độ tin cậy bằng tập dữ liệu có nhãn, không coi điểm model tự báo là sự thật. Cách ly tài liệu sai định dạng hoặc ngoài hỗ trợ kèm lý do và đường replay.

Đo precision/recall theo trường, độ chính xác tuyệt đối hoặc theo dung sai cho số, tỷ lệ schema lỗi, tỷ lệ cần duyệt, tỷ lệ chỉnh sửa, độ trễ và chi phí mỗi bản ghi được chấp nhận. Chia tập đánh giá theo nguồn hoặc thời gian để giảm rò rỉ từ tài liệu gần trùng lặp.

## Sản phẩm bàn giao

- Schema trích xuất
- Job parser
- Tầng kiểm định
- Hàng đợi lỗi
- Báo cáo duyệt
- ID nguồn ổn định và content hash để xử lý idempotent
- Bằng chứng theo trường và provenance xử lý
- Hàng đợi cách ly với retry có giới hạn và khả năng replay
- Tập đánh giá có nhãn cùng metric chất lượng theo trường

## Tiêu chí nghiệm thu

- Mọi đầu ra được kiểm định theo schema có phiên bản trước khi vào kho dữ liệu.
- Giá trị thiếu vẫn được biểu diễn là thiếu, không bị bịa.
- Người duyệt truy ngược được trường quan trọng về bằng chứng nguồn.
- Xử lý lại cùng phiên bản nguồn không sinh bản ghi trùng.
- Bản ghi tin cậy thấp hoặc tác động cao được chuyển duyệt theo quy tắc đã tài liệu hóa.
- Có thể tạm dừng hoặc rollback mà không mất tài liệu nguồn và lịch sử duyệt.