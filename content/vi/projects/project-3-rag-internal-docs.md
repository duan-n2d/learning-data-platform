---
title: Dự án 3 - RAG cho tài liệu dữ liệu nội bộ
description: Xây trợ lý trả lời dựa trên tài liệu, schema và từ điển nghiệp vụ.
order: 3
tags: [RAG, tài liệu, trợ lý AI]
---

# Dự án 3 - RAG cho tài liệu dữ liệu nội bộ

## Mục tiêu

Xây trợ lý RAG trên corpus nhỏ có gắn nhãn quyền gồm tài liệu Markdown, dbt docs, ghi chú schema và từ điển nghiệp vụ. Trợ lý giúp tìm tài liệu chuẩn nhanh hơn, không thay thế nguồn sự thật.

## Kiến trúc

```text
Tài liệu
-> parse, gắn metadata nguồn và nhãn truy cập
-> chia đoạn và lập chỉ mục
-> truy xuất trong phạm vi quyền người dùng
-> xếp hạng lại hoặc lọc bằng chứng
-> trả lời kèm nguồn kiểm chứng được hoặc từ chối
```

## Corpus và metadata

Lưu nguồn gốc, URL/đường dẫn chuẩn, tiêu đề, chủ sở hữu, ngày cập nhật, phiên bản tài liệu và nhãn truy cập trên mỗi đoạn. Loại bản nháp cũ và bí mật. Khi tài liệu đổi, thay thế hoặc đánh phiên bản các đoạn để truy xuất không trộn định nghĩa cũ và mới.

Giữ tiêu đề và bảng khi có thể. Bắt đầu với đoạn theo mục nội dung, sau đó thử vài kích thước trên câu hỏi thật. Overlap giúp giữ định nghĩa nằm qua ranh giới đoạn, nhưng quá nhiều overlap gây lặp và tốn context.

## Hành vi truy xuất và trả lời

Dùng bộ lọc metadata trước truy xuất ngữ nghĩa khi đó là ranh giới cứng như dự án, loại nguồn hoặc phạm vi quyền. Đánh giá xem câu hỏi có tìm đúng đoạn không, chứ không chỉ xem câu trả lời cuối có vẻ hợp lý. Trả tiêu đề nguồn và tham chiếu trực tiếp để người đọc kiểm chứng từng khẳng định quan trọng.

Văn bản truy xuất là đầu vào không đáng tin: có thể chứa chỉ thị cũ, nội dung độc hại hoặc ví dụ gây hiểu nhầm. Chỉ xem nó là bằng chứng; chính sách ứng dụng luôn ưu tiên hơn chỉ thị trong tài liệu. Không để lộ tài liệu người dùng không có quyền truy cập. Nếu nguồn mâu thuẫn, nêu rõ và dẫn cả hai; nếu thiếu bằng chứng, từ chối trả lời.

## Đánh giá

Tạo cặp câu hỏi-câu trả lời cùng đoạn nguồn kỳ vọng. Theo dõi recall của đoạn nguồn trong top-k nhỏ, độ chính xác trích dẫn, độ bám sát bằng chứng, chất lượng từ chối, độ trễ và chi phí token. Thêm trường hợp tài liệu cũ, mâu thuẫn, không có quyền và không có câu trả lời. Phân loại lỗi theo parse, index, retrieval, generation hoặc authorization.

## Sản phẩm bàn giao

- Parser tài liệu
- Chiến lược chia đoạn
- Vector index
- API truy xuất
- UI trả lời có căn cứ
- Ví dụ đánh giá
- Bộ lọc metadata theo quyền
- Quản lý phiên bản nguồn và loại bỏ tài liệu cũ
- Test độ chính xác citation và hành vi từ chối
- Quy trình cập nhật corpus và rollback index

## Tiêu chí nghiệm thu

- Người rà soát mở được từng nguồn trích dẫn và tìm thấy đoạn hỗ trợ.
- Người dùng không thể truy xuất tài liệu ngoài quyền.
- Cập nhật hoặc xóa nguồn sẽ loại nội dung cũ khỏi truy xuất.
- Trợ lý từ chối câu hỏi không được corpus hỗ trợ.
- Bộ đánh giá cố định báo cáo riêng chất lượng truy xuất và câu trả lời.