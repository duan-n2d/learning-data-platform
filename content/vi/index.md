---
title: Lộ trình Kỹ sư Dữ liệu Tăng cường AI
description: Lộ trình học 24 tuần về kỹ nghệ dữ liệu, phân tích và quy trình AI được đánh giá cẩn thận.
order: 1
tags: [kỹ nghệ dữ liệu, AI, lộ trình]
---

# Lộ trình Kỹ sư Dữ liệu Tăng cường AI

> Không bỏ qua kiến thức nền tảng. Hãy củng cố kiến thức đó trước, rồi mới đặt AI vào đúng chỗ để hỗ trợ thay vì thay thế tư duy kỹ sư.

Đây là chương trình học 24 tuần, lấy dự án làm trọng tâm, nhằm xây dựng hệ thống phân tích đáng tin cậy và bổ sung AI ở những nơi có thể đo lường, giới hạn và kiểm soát. Mỗi giai đoạn kế thừa kết quả của giai đoạn trước; đầu ra của mỗi dự án trở thành đầu vào cho dự án tiếp theo.

<div class="card-grid">
  <div class="card"><h3>Tuần 1-8</h3><p>Xây nền tảng SQL, kiến trúc platform, lưu trữ, ingestion/CDC, modeling, chất lượng, điều phối và cloud.</p><a href="roadmap/phase-1-core-foundation.html">Mở Giai đoạn 1</a></div>
  <div class="card"><h3>Tuần 9-16</h3><p>Kết nối governance, data product, BI/serving, hiệu năng truy vấn, metric ngữ nghĩa và Text2SQL có giới hạn.</p><a href="roadmap/phase-2-modern-analytics-ai.html">Mở Giai đoạn 2</a></div>
  <div class="card"><h3>Tuần 17-24</h3><p>Xây truy xuất có căn cứ, trích xuất có bằng chứng, AI agent được đánh giá, vận hành vòng đời và đồ án tích hợp.</p><a href="roadmap/phase-3-ai-native-workflows.html">Mở Giai đoạn 3</a></div>
</div>

## Lộ trình học

Có thể dùng công cụ khác với ví dụ trong tài liệu; điều cần giữ là hợp đồng dữ liệu, kiểm thử và hành vi vận hành mà các công cụ đó nhằm bảo đảm.

1. **Xây nền tảng dữ liệu.** Học [kiến trúc platform](skills/data-engineering/platform-architecture-and-lifecycle.html), [lưu trữ và table format](skills/data-engineering/storage-warehousing-and-formats.html), [ingestion, CDC và streaming](skills/data-engineering/ingestion-cdc-and-streaming.html), [window function trong SQL](skills/sql/window-functions.html), [pipeline Python](skills/python/data-pipelines.html) và [mô hình hóa dữ liệu phân tích](skills/data-engineering/data-modeling.html).
2. **Làm dữ liệu đáng tin cậy.** Xây [hợp đồng chất lượng](skills/data-engineering/data-quality-contracts.html), thực hành [điều phối pipeline](skills/data-engineering/orchestration.html), tìm hiểu [governance và data product](skills/data-engineering/governance-and-data-products.html), cùng [lưu trữ cloud và kiểm soát truy cập](skills/data-engineering/cloud-storage-and-access.html).
3. **Công bố dữ liệu phân tích đáng tin cậy.** Hoàn thành [Dự án 1](projects/project-1-analytics-warehouse.html) với hợp đồng nguồn, mart được kiểm thử, kỳ vọng về độ mới và phương án khôi phục.
4. **Làm rõ ý nghĩa nghiệp vụ.** Định nghĩa [lớp ngữ nghĩa](skills/ai/semantic-layer.html), phục vụ qua [BI và analytics interface](skills/data-engineering/analytics-serving-and-bi.html), hiểu [query engine và hiệu năng](skills/data-engineering/query-engines-and-performance.html), rồi xây [Dự án 2](projects/project-2-text2sql-chatbot.html) với quyền truy vấn chỉ đọc và bộ đánh giá.
5. **Bổ sung quy trình AI có căn cứ.** Học [RAG](skills/ai/rag-pipeline.html) và [mẫu Text2SQL](skills/ai/text-to-sql.html), rồi hoàn thành [Dự án 3: RAG](projects/project-3-rag-internal-docs.html) và [Dự án 4: trích xuất](projects/project-4-llm-extraction-pipeline.html) với trích dẫn, nguồn gốc dữ liệu, kiểm định và người duyệt.
6. **Vận hành và trình bày hệ thống.** Áp dụng [đánh giá và khả năng quan sát AI](skills/ai/evaluation-and-observability.html), cân nhắc [AI agent trong công việc dữ liệu](skills/ai/ai-agents-for-data-work.html), theo [vòng đời Data Engineering](skills/data-engineering/lifecycle-and-practice.html), tích hợp [đồ án cuối khóa](projects/project-5-ai-data-platform.html), và trình bày hạn chế rõ ràng như những điểm mạnh.
7. **Học qua cẩm nang chuyên đề.** Đọc sáu chương gốc về [nền tảng](skills/field-guide/foundations.html), [hạ tầng](skills/field-guide/infrastructure.html), [biến đổi và xử lý](skills/field-guide/transformation-and-processing.html), [cách tiếp cận phân tích](skills/field-guide/analytics-approaches.html), [công nghệ chuyên biệt](skills/field-guide/specialized-technologies.html) và [phát triển nghề nghiệp](skills/field-guide/professional-development.html).
8. **Đọc thêm nguồn bên ngoài.** Dùng [bản đồ đọc Data Engineering](skills/references/data-engineering-reading-map.html) để duyệt nguồn và chủ đề bổ sung.

## Tiêu chí hoàn thành

- Có thể dựng lại dự án từ bản checkout sạch theo hướng dẫn.
- Mô hình dữ liệu nêu rõ grain, khóa, chủ sở hữu và kỳ vọng về độ mới.
- Kiểm thử bao phủ schema, quan hệ và quy tắc nghiệp vụ; lỗi được hiển thị với thông tin có thể hành động.
- Đầu ra AI có căn cứ từ dữ liệu được phép dùng, bị giới hạn trước khi thực thi và được đánh giá bằng ví dụ có phiên bản.
- Yêu cầu không rõ, ngoài phạm vi hoặc có tác động cao có cơ chế hỏi lại, từ chối hoặc chuyển người duyệt.
- Hệ thống có tín hiệu vận hành cơ bản, runbook và cách tắt AI mà không mất quyền truy cập dữ liệu chuẩn.

## Cách sử dụng

1. Bắt đầu từ Giai đoạn 1 rồi học tuần tự, trừ khi đã có bằng chứng chứng minh thành thạo một kỹ năng.
2. Dùng các trang kỹ năng làm tài liệu tham khảo khi triển khai dự án.
3. Ghi lại giả định, quyết định, kiểm thử thất bại và thay đổi trong nhật ký học tập.
4. Xem đầu ra của mô hình là đề xuất; kiểm tra mã và dữ kiện bằng test, tài liệu nguồn hoặc chuyên gia nghiệp vụ.
5. Thêm ghi chú, sơ đồ và ví dụ dự án dưới dạng Markdown theo frontmatter trong README.

## Mô hình hiệu năng

Markdown được biên dịch một lần lúc build thành HTML tĩnh. Trình duyệt tải trang hiện tại, các tài nguyên dùng chung và chỉ mục tìm kiếm tĩnh nhỏ; không cần cơ sở dữ liệu ứng dụng hay dịch vụ Markdown lúc chạy.