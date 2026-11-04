---
title: Dự án 5 - Nền tảng dữ liệu AI
description: Kết hợp kho dữ liệu, Text2SQL, RAG, trích xuất, giám sát và tài liệu.
order: 5
tags: [nền tảng, AI, portfolio]
---

# Dự án 5 - Nền tảng dữ liệu AI

## Mục tiêu

Kết hợp Dự án 1-4 thành một nền tảng portfolio mạch lạc và có thể vận hành. Thành công khi dữ liệu vẫn đáng tin cậy và các thành phần AI có thể được kiểm tra, đánh giá, giới hạn và tắt độc lập.

## Các thành phần

- Website tài liệu học tập tĩnh
- Kho dữ liệu phân tích
- Chatbot Text2SQL
- Trợ lý kiến thức RAG
- Pipeline trích xuất LLM
- Dashboard giám sát
- Tài liệu dự án

## Kiến trúc tham khảo

```text
Hệ thống nguồn -> lưu trữ raw -> biến đổi -> mart được quản trị
                                           |                 |
                                           |                 +-> Text2SQL (chỉ đọc)
                                           +-> kiểm tra chất lượng và lineage

Tài liệu + glossary -> truy xuất theo quyền -> câu trả lời RAG có trích dẫn
Tài liệu -> trích xuất + kiểm định -> người duyệt -> bản ghi được chấp nhận

Mọi dịch vụ -> metric, trace, audit event, lượt đánh giá và cảnh báo
```

Lưu hợp đồng chung (định nghĩa metric, schema, định danh và chủ sở hữu) trong version control. Kho dữ liệu, chỉ mục RAG và đầu ra trích xuất có đặc tính freshness/chất lượng khác nhau; hãy làm rõ thay vì gộp chúng thành một trợ lý không phân biệt.

## Kịch bản đồ án và quyết định kiến trúc

Dùng một kịch bản xuyên suốt portfolio: nhà bán lẻ trực tuyến có đơn hàng, dòng hàng, khách hàng, danh mục sản phẩm, runbook nội bộ và một nhóm tài liệu dạng hóa đơn. Dữ liệu tổng hợp là đủ; không dùng dữ liệu cá nhân hoặc thanh toán thật. Tái sử dụng cùng ID đơn hàng và sản phẩm trong warehouse, BI, Text2SQL và ví dụ tài liệu để chứng minh tích hợp.

Viết architecture decision record ngắn trước khi triển khai:

| Quyết định | Lựa chọn baseline | Khi nào mở rộng |
|---|---|---|
| Ingestion | Snapshot batch mỗi ngày kèm lookback incremental | Thêm CDC khi volume hoặc freshness đủ để cần đọc log nguồn |
| Lưu trữ | File raw bất biến, sau đó bảng phân tích curated | Chọn lakehouse/table format khi cần snapshot, ghi đồng thời hoặc tiến hóa schema |
| Biến đổi | Staging, logic trung gian và mart dimensional phục vụ | Thêm model tích hợp historized nếu cần đối soát nhiều nguồn |
| Phân tầng | Định nghĩa rõ cam kết raw, validated và serving | Chỉ dùng nhãn bronze/silver/gold khi mỗi tầng có contract rõ |
| Chủ sở hữu | Một nhóm platform nhỏ với chủ data product được chỉ định | Cân nhắc quyền sở hữu liên kết theo domain khi nhiều nhóm duy trì được chuẩn chung |
| Serving | Một góc nhìn BI và Text2SQL chỉ đọc dùng chung định nghĩa metric | Chỉ thêm API/federation khi có consumer chứng minh nhu cầu |
| Tự động hóa AI | RAG và trích xuất có người duyệt; agent chỉ đọc và soạn thảo | Bắt buộc duyệt trước ghi dữ liệu, deploy, rerun hoặc hành động tốn kém |

Không áp dụng streaming, Data Mesh, Data Vault hay agent tự chủ chỉ để kiến trúc trông hiện đại. Nêu yêu cầu nào biện minh cho từng phần mở rộng và chúng thay đổi vận hành, chi phí, ownership, khôi phục thế nào.

## Artifact học tập trong capstone

- Dùng bài [kiến trúc platform](../skills/data-engineering/platform-architecture-and-lifecycle.html) và [lưu trữ/table format](../skills/data-engineering/storage-warehousing-and-formats.html) để tạo sơ đồ kiến trúc, contract từng tầng và ghi chú chọn format/lưu trữ.
- Dùng [ingestion, CDC và streaming](../skills/data-engineering/ingestion-cdc-and-streaming.html) để tài liệu hóa batch, khử trùng, cập nhật muộn, replay và ngưỡng chuyển sang CDC.
- Dùng [mô hình dữ liệu](../skills/data-engineering/data-modeling.html) để công bố phác thảo khái niệm, ERD, grain và model dimensional. Giải thích vì sao baseline không cần Data Vault hay pattern khác nếu chúng không thêm giá trị.
- Dùng [governance và data product](../skills/data-engineering/governance-and-data-products.html) để định nghĩa owner, metadata catalog, lineage, vai trò truy cập, retention và chính sách thay đổi.
- Dùng [BI/analytics serving](../skills/data-engineering/analytics-serving-and-bi.html) và [hiệu năng query engine](../skills/data-engineering/query-engines-and-performance.html) để thể hiện một metric nhất quán ở BI/Text2SQL và kèm ghi chú query plan đã đo.
- Dùng [orchestration](../skills/data-engineering/orchestration.html) để định nghĩa DAG/asset workflow có thể khôi phục, đầu ra idempotent, bước backfill và chủ sở hữu production.
- Chỉ dùng [AI agent trong công việc dữ liệu](../skills/ai/ai-agents-for-data-work.html) cho workflow đọc-soạn thảo có giới hạn; ghi rõ tool agent không được gọi và lúc nào cần người duyệt.
- Dùng [vòng đời Data Engineering](../skills/data-engineering/lifecycle-and-practice.html) để xác định trách nhiệm hỗ trợ, thay đổi và ngừng sử dụng sau demo.

## Thứ tự tích hợp

1. Làm cho Dự án 1 tái tạo được và công bố một tập mart ổn định, nhỏ.
2. Thêm định nghĩa metric và chạy Dự án 2 bằng vai trò chỉ đọc.
3. Lập chỉ mục corpus tài liệu được tuyển chọn cho Dự án 3; xác minh quyền trước khi generation.
4. Xử lý một loại tài liệu giới hạn trong Dự án 4, bắt buộc duyệt trường hợp không chắc chắn/tác động cao.
5. Thêm trang trạng thái chung, báo cáo đánh giá, runbook và demo end-to-end.

## Bảng điều khiển vận hành

| Mảng | Tín hiệu cần báo cáo | Hành động ví dụ |
|---|---|---|
| Chất lượng dữ liệu | Freshness, test lỗi, dòng bị từ chối | Giữ công bố và báo chủ model |
| Text2SQL | Độ đúng, từ chối chính sách, độ trễ, chi phí scan | Tắt thực thi nhưng vẫn ghi nhận câu hỏi |
| RAG | Chất lượng truy xuất, citation hợp lệ, tỷ lệ từ chối | Dựng lại hoặc rollback index |
| Trích xuất | Độ đúng trường, tỷ lệ duyệt, tuổi hàng đợi, chi phí | Tạm dừng công bố, giữ nguồn trong hàng đợi |
| Nền tảng | Tính sẵn sàng, sức khỏe dependency, chi tiêu, truy cập | Theo quy trình sự cố và rollback đã định |

Chọn ngưỡng theo baseline và tác động với người dùng; không cảnh báo mỗi khi model dao động. Mỗi cảnh báo cần chủ sở hữu và hành động tiếp theo.

## Rà soát bảo mật và quản trị

- Dùng danh tính quyền tối thiểu riêng cho ingestion, biến đổi và thực thi truy vấn.
- Phân loại trường nhạy cảm, định nghĩa thời hạn lưu trước khi gửi dữ liệu tới model bên ngoài.
- Lưu bí mật trong secret manager hoặc cấu hình môi trường, không để trong prompt hay source control.
- Áp dụng authorization trước truy xuất và trước truy vấn database, không chỉ ở UI.
- Ghi đủ provenance để kiểm toán nhưng tránh lưu dữ liệu cá nhân thô không cần thiết.
- Tài liệu hóa phiên bản nhà cung cấp/model, prompt, schema và corpus để tái tạo.
- Có đường chuyển người xử lý và phương án không dùng AI cho quy trình quan trọng.

## Kịch bản demo cuối

Trình diễn một bản ghi nguồn đi vào mart đã kiểm thử; hỏi metric được hỗ trợ và xem định nghĩa cùng SQL; trả lời một câu hỏi tài liệu kèm citation kiểm chứng được; trích xuất một tài liệu và duyệt bằng chứng; sau đó cho xem một test cố ý lỗi cùng cảnh báo/khôi phục tương ứng. Thêm một yêu cầu ngoài phạm vi để minh họa hệ thống từ chối an toàn.

## Thang đánh giá portfolio

| Tiêu chí | Bằng chứng tốt |
|---|---|
| Kỹ nghệ dữ liệu | Grain rõ, tải lặp lại an toàn, model được test, lineage và khôi phục |
| Độ tin cậy AI | Đánh giá có phiên bản, bằng chứng nguồn, từ chối và người duyệt |
| Bảo mật | Ranh giới quyền, quyền tối thiểu, giảm thiểu dữ liệu và khả năng kiểm toán |
| Vận hành | Metric hữu ích, cảnh báo hành động được, runbook, chi phí và rollback |
| Truyền đạt | Kiến trúc, trade-off, hạn chế và demo tái tạo được |

## Kết quả cuối

Một nền tảng portfolio thể hiện cả kỹ nghệ dữ liệu cốt lõi lẫn cách tăng cường AI thực tế. Công bố case study ngắn gồm kiến trúc, kết quả đánh giá, hạn chế đã biết, giả định chi phí vận hành và cải tiến tiếp theo. Không trình bày điểm đánh giá prototype như cam kết production.