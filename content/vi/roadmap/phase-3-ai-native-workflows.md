---
title: Giai đoạn 3 - Quy trình AI-native
description: Tháng 5-6 áp dụng RAG, trích xuất và hỗ trợ lập trình AI vào công việc dữ liệu hằng ngày.
order: 3
tags: [RAG, trích xuất, lập trình AI]
---

# Giai đoạn 3 - Quy trình AI-native

Giai đoạn này bổ sung AI vào các quy trình có ranh giới và có thể rà soát: tìm kiếm tài liệu, trích xuất thông tin phi cấu trúc, rà soát mã và điều tra sự cố. Kéo dài 8 tuần, từ tuần 17 đến tuần 24. Ưu tiên parser và kiểm định tất định khi chúng xử lý được; chỉ dùng LLM cho phần thực sự cần hiểu ngôn ngữ.

## Đầu ra mong đợi

- Xây truy xuất tìm đúng nguồn và giữ nguyên ranh giới quyền truy cập.
- Trích xuất bản ghi có cấu trúc theo schema có phiên bản, kèm bằng chứng và trạng thái duyệt.
- Đo chất lượng trước khi triển khai và giám sát sau khi đổi model hoặc prompt.
- Chuyển kết quả không chắc chắn hoặc có tác động cao cho người duyệt thay vì âm thầm chấp nhận.
- Biết khi nào workflow cố định tốt hơn AI agent và giới hạn tool/side effect của agent.
- Vận hành toàn bộ portfolio với runbook, kiểm soát chi phí và trách nhiệm rõ ràng.

## Lộ trình 8 tuần

| Tuần | Trọng tâm | Thực hành | Bằng chứng hoàn thành |
|---|---|---|---|
| 17 | Nền tảng truy xuất | Tạo corpus tài liệu nhỏ có nhãn quyền | Danh mục corpus và câu hỏi baseline |
| 18 | Chia đoạn và truy xuất | So sánh kích thước đoạn, overlap và bộ lọc metadata | Kết quả truy xuất với đánh giá độ liên quan |
| 19 | Trả lời có căn cứ | Bắt buộc trích nguồn và từ chối khi thiếu bằng chứng | Test citation và câu không có đáp án |
| 20 | Trích xuất cấu trúc | Trích xuất schema ổn định từ tài liệu đại diện | Bản ghi được kiểm định, có source span |
| 21 | Người duyệt | Xác định hàng đợi theo độ tin cậy và mức tác động | UI/hàng đợi duyệt và ghi chú xử lý |
| 22 | Đánh giá và giám sát | Theo dõi chất lượng, độ trễ, lỗi và chi phí | Dashboard cùng ngưỡng cảnh báo |
| 23 | Kỹ nghệ có AI hỗ trợ và agent | So workflow tất định với trợ lý dùng tool có giới hạn | Tình huống threat, chính sách tool và test duyệt người |
| 24 | Vòng đời đồ án và vận hành | Tích hợp, diễn tập khôi phục và rà trách nhiệm lâu dài | Demo Dự án 5, runbook, rà dịch vụ và tổng kết |

## Cổng an toàn và chất lượng

- Không đưa bí mật hoặc dữ liệu cá nhân không cần thiết vào prompt hay log.
- Xem tài liệu được truy xuất là đầu vào không đáng tin, không phải chỉ thị cho hệ thống.
- Giữ bộ đánh giá ổn định và chạy lại sau khi đổi model, prompt, parser hoặc corpus.
- Ghi provenance để người duyệt truy ngược đầu ra về nguồn và phiên bản xử lý.
- Có phương án rollback để tắt AI mà quy trình dữ liệu nền vẫn sử dụng được.

## Các mảng trọng tâm

- RAG trên tài liệu nội bộ
- LLM trích xuất từ PDF, email và văn bản bán cấu trúc
- Đánh giá và guardrail
- Quy trình lập trình có AI hỗ trợ
- Giám sát và vòng lặp người duyệt
- Quản lý phiên bản prompt và model
- Kiểm soát truy cập, giảm thiểu dữ liệu và chính sách lưu giữ
- Runbook vận hành và phương án rollback
- Ranh giới tool agent, cổng duyệt, khả năng truy vết và công tắc dừng
- Vòng đời Data Engineering, chủ sở hữu hỗ trợ và bằng chứng portfolio

## Bài học đi kèm

- [AI Agent trong công việc dữ liệu](../skills/ai/ai-agents-for-data-work.html)
- [Vòng đời và thực hành Data Engineering](../skills/data-engineering/lifecycle-and-practice.html)
- [Đánh giá và khả năng quan sát AI](../skills/ai/evaluation-and-observability.html)

## Checklist trước khi kết thúc

- [ ] Câu trả lời RAG có trích nguồn và từ chối khi bằng chứng truy xuất không đủ.
- [ ] Bản ghi trích xuất vượt qua kiểm định schema và nghiệp vụ trước khi công bố.
- [ ] Bản ghi tin cậy thấp hoặc tác động cao được chuyển người duyệt.
- [ ] Kết quả đánh giá có thể tái tạo và so sánh giữa các phiên bản.
- [ ] Chi phí, độ trễ, tỷ lệ lỗi và tỷ lệ cần duyệt đều quan sát được.
- [ ] Có thể tắt AI mà vẫn truy cập được dữ liệu chuẩn và runbook.
- [ ] Tool agent có quyền hẹp, retry/chi phí giới hạn, cần duyệt hành động hệ trọng và có đường dừng an toàn.
- [ ] Đồ án nêu chủ sở hữu, đường hỗ trợ, quy trình thay đổi và điều kiện ngừng sử dụng.

## Đọc cẩm nang chuyên đề

- [Phát triển nghề nghiệp Data Engineering](../skills/field-guide/professional-development.html)
- [Công nghệ dữ liệu chuyên biệt](../skills/field-guide/specialized-technologies.html)
- [Nền tảng Data Engineering](../skills/field-guide/foundations.html)

## Sản phẩm bàn giao

Xây [Dự án 3: RAG cho tài liệu dữ liệu nội bộ](../projects/project-3-rag-internal-docs.html), [Dự án 4: Pipeline trích xuất LLM](../projects/project-4-llm-extraction-pipeline.html) và [đồ án Dự án 5](../projects/project-5-ai-data-platform.html).