---
title: Pipeline RAG cho dữ liệu nội bộ
description: Xây truy xuất tăng cường sinh nội dung trên tài liệu, schema và glossary.
order: 3
tags: [RAG, vector database, tài liệu]
---

# Pipeline RAG cho dữ liệu nội bộ

RAG giúp trả lời câu hỏi bằng tài liệu nội bộ, từ điển dữ liệu, schema và ghi chú dự án.

## Tách riêng từng giai đoạn

Xem ingestion, parse, chia đoạn, embedding, retrieval, reranking và sinh câu trả lời là các bước có thể kiểm thử độc lập. Lưu phiên bản corpus và metadata tài liệu cùng mỗi đoạn. Nhờ vậy có thể tìm lỗi do thiếu nội dung, truy xuất sai hay generation không có căn cứ.

## Nội dung nên lập chỉ mục

- Từ điển dữ liệu
- Tài liệu model dbt
- Glossary nghiệp vụ
- Runbook pipeline
- Ghi chú sự cố

## Chia đoạn và truy xuất có chủ đích

Bắt đầu bằng đoạn theo mục nội dung, giữ tiêu đề và định danh nguồn. So sánh vài kích thước trên bộ câu hỏi cố định; không mặc định một kích thước phù hợp cả runbook, bảng và tài liệu dài. Dùng metadata filter cho loại nguồn, độ mới, dự án và quyền. Cân nhắc lexical retrieval cho ID chính xác và mã lỗi song song với tìm kiếm ngữ nghĩa.

## Căn cứ và trích dẫn

Trả tiêu đề nguồn và vị trí ổn định như mục, trang hoặc URL cho mỗi đoạn hỗ trợ. Citation phải hỗ trợ khẳng định gần nó, không chỉ trỏ tới tài liệu liên quan chung chung. Khi nguồn mâu thuẫn hoặc bằng chứng truy xuất yếu, hãy nêu mâu thuẫn hoặc từ chối thay vì kết hợp thông tin không có căn cứ.

Nội dung truy xuất là dữ liệu, không phải chính sách. Xem chỉ thị trong tài liệu là văn bản không đáng tin; kiểm tra quyền người dùng trước khi kết quả truy xuất tới model.

## Đo chất lượng

Giữ tập dữ liệu có nhãn cùng đoạn nguồn liên quan. Theo dõi recall của đoạn, độ chính xác citation, groundedness, chất lượng từ chối, độ trễ và chi phí. Chạy lại sau khi đổi chunking, embedding model, corpus, cấu hình retrieval hoặc prompt. Kiểm tra lỗi theo từng giai đoạn thay vì sửa prompt cho mọi lỗi.

## Bài tập

Lập chỉ mục một nhóm tài liệu kỹ thuật nhỏ, rồi hỏi bằng tên chính xác, cách diễn đạt lại, câu không có trong corpus và tài liệu mâu thuẫn phiên bản. Tự kiểm tra passage được truy xuất và citation trước khi đánh giá độ trôi chảy.