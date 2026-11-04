---
title: Giai đoạn 2 - Phân tích hiện đại và cầu nối AI
description: Tháng 3-4 kết nối nền tảng phân tích hiện đại với các mẫu phân tích dùng AI.
order: 2
tags: [lớp ngữ nghĩa, Text2SQL, chỉ số]
---

# Giai đoạn 2 - Phân tích hiện đại và cầu nối AI

Giai đoạn này nối kỹ nghệ dữ liệu đáng tin cậy với phân tích có AI hỗ trợ. Kéo dài 8 tuần, từ tuần 9 đến tuần 16. Mục tiêu không phải buộc mô hình viết SQL bằng mọi giá, mà là tạo quy trình phân tích có phạm vi hẹp, đo lường được và an toàn hơn.

## Đầu ra mong đợi

- Định nghĩa chỉ số một lần, nêu rõ grain, bộ lọc, cơ sở thời gian và chủ sở hữu.
- Chỉ truy xuất schema và ngữ cảnh nghiệp vụ phù hợp với câu hỏi.
- Sinh SQL trên bề mặt phân tích được cho phép rồi kiểm định trước khi chạy.
- Giải thích kết quả kèm đơn vị, khoảng thời gian và liên kết tới định nghĩa gốc.
- Phục vụ metric được quản trị nhất quán qua BI, API và Text2SQL.
- Đọc query plan đủ để giải thích đánh đổi scan, join và materialization chính.
- Đánh giá hệ thống trên bộ câu hỏi thực tế có phiên bản, bao gồm cả câu không thể trả lời.

## Lộ trình 8 tuần

| Tuần | Trọng tâm | Thực hành | Bằng chứng hoàn thành |
|---|---|---|---|
| 9 | Kiến trúc và serving phân tích | Theo metric tới dashboard BI hoặc analytics API | Bản đồ lineage, người dùng và contract freshness |
| 10 | Chỉ số và thuật ngữ nghiệp vụ | Định nghĩa doanh thu, khách hàng hoạt động, số đơn | Hợp đồng chỉ số được duyệt, có trường hợp biên |
| 11 | Mô hình ngữ nghĩa | Mô tả entity, dimension và đường join hợp lệ | Ví dụ truy vấn sinh từ định nghĩa |
| 12 | Định tuyến câu hỏi | Phân loại tra cứu, so sánh, xu hướng hoặc ngoài phạm vi | Fixture phân loại có nhãn |
| 13 | Sinh và kiểm định SQL | Sinh, parse và dry-run SQL chỉ đọc | Test kiểm định với đầu vào đối kháng |
| 14 | BI và trình bày câu trả lời | So một metric qua dashboard, API và trợ lý | Kiểm tra nhất quán kèm đơn vị, kỳ thời gian |
| 15 | Đánh giá và hiệu năng truy vấn | Rà độ đúng kết quả, đọc query plan đại diện | Báo cáo đánh giá/tinh chỉnh có phiên bản |
| 16 | Governance và hoàn thiện sản phẩm | Thêm chủ sở hữu, metadata catalog, ranh giới quyền, log, giới hạn | Demo Dự án 2 và danh sách governance/rủi ro |

## Nguyên tắc ra quyết định

Nếu câu hỏi mơ hồ, ngoài phạm vi hoặc không được mô hình ngữ nghĩa hỗ trợ, hãy hỏi làm rõ hoặc từ chối chạy. Từ chối đúng là một kết quả hợp lệ; trả về con số nghe có vẻ hợp lý nhưng không có căn cứ thì không.

## Vì sao cần lớp ngữ nghĩa?

Text2SQL có rủi ro khi LLM không hiểu định nghĩa nghiệp vụ. Lớp ngữ nghĩa cung cấp metric, entity, dimension và đường join đã được kiểm soát. Chẳng hạn “doanh thu” có thể là doanh thu ghi nhận, lập hóa đơn hoặc đã thanh toán. Định nghĩa phải chỉ rõ nguồn, grain, bộ lọc trạng thái, cách xử lý tiền tệ và ngày sự kiện. Một mục từ điển nghiệp vụ là chưa đủ nếu logic thực thi vẫn chỉ nằm trong prompt mơ hồ.

## Các mảng trọng tâm

- Modern Analytics Stack
- Lớp metric và từ điển nghiệp vụ
- Thiết kế mô hình ngữ nghĩa
- Mẫu prompt Text2SQL
- Kiểm định SQL và guardrail
- Bộ dữ liệu đánh giá cho câu hỏi phân tích
- Danh tính thực thi chỉ đọc và giới hạn truy vấn
- Audit trail nối câu trả lời với định nghĩa và SQL được sinh
- Governance dữ liệu, catalog, lineage và contract data product
- BI serving, analytics API, OLAP và đánh đổi federation
- Query plan, pushdown, materialized view và chi phí workload

## Bài học đi kèm

- [Quản trị dữ liệu và Data Product](../skills/data-engineering/governance-and-data-products.html)
- [Phục vụ dữ liệu phân tích và BI](../skills/data-engineering/analytics-serving-and-bi.html)
- [Query Engine và nội bộ hiệu năng](../skills/data-engineering/query-engines-and-performance.html)
- [Lớp ngữ nghĩa](../skills/ai/semantic-layer.html)

## Checklist trước khi chuyển giai đoạn

- [ ] Mỗi metric được hỗ trợ có chủ sở hữu, grain, định nghĩa và ví dụ đã kiểm thử.
- [ ] SQL được sinh phải parse và bị giới hạn trước khi tới kho dữ liệu.
- [ ] Danh tính cơ sở dữ liệu không thể sửa dữ liệu hoặc đọc schema ngoài phạm vi.
- [ ] Truy vấn có timeout và giới hạn số dòng hoặc ngân sách scan.
- [ ] Bộ đánh giá có câu mơ hồ, ngoài phạm vi và đầu vào tìm cách vượt quy tắc.
- [ ] Người dùng xem được định nghĩa metric và khoảng thời gian đứng sau câu trả lời.
- [ ] Chủ sở hữu, phân loại, mục catalog và lineage được tài liệu hóa cho data product hỗ trợ.
- [ ] Metric đã chọn nhất quán giữa BI, API và Text2SQL; nếu khác biệt thì phải hiển thị rõ.
- [ ] Query plan đại diện cùng các đánh đổi chi phí/hiệu năng chính được ghi lại.

## Sản phẩm bàn giao

Xây [Dự án 2: Chatbot Text2SQL](../projects/project-2-text2sql-chatbot.html) dựa trên các mart đáng tin cậy từ Giai đoạn 1.

## Đọc cẩm nang chuyên đề

- [Các cách tiếp cận phân tích hiện đại](../skills/field-guide/analytics-approaches.html)
- [Biến đổi và xử lý dữ liệu](../skills/field-guide/transformation-and-processing.html)
- [Hạ tầng dữ liệu hiện đại](../skills/field-guide/infrastructure.html)