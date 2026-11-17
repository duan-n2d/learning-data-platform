---
title: Phục vụ dữ liệu phân tích và BI
description: Cung cấp metric được quản trị qua dashboard, OLAP, API và giao diện ngữ nghĩa.
order: 9
tags: [BI, OLAP, analytics API, serving]
---

# Phục vụ dữ liệu phân tích và BI

Analytics serving là giao diện giữa dữ liệu đáng tin và quyết định của người dùng. Chọn giao diện theo đối tượng, độ trễ, nhu cầu khám phá, tính nhất quán và trách nhiệm vận hành.

## Business Intelligence

Business Intelligence (BI) là ngành biến dữ liệu vận hành và phân tích thành dashboard, báo cáo và truy vấn ad hoc hỗ trợ quyết định kinh doanh. Vòng đời của nó chạy từ thu thập và biến đổi dữ liệu, qua định nghĩa metric và trực quan hóa, tới phân phối kết quả cho người ra quyết định hành động dựa trên đó.

Dashboard thường đi theo một vòng đời tin tưởng và áp dụng: nó chạy tốt trong demo trên tập dữ liệu nhỏ, kiểm soát được, rồi xuống cấp khi chạm quy mô production — số liệu lệch nhau giữa các nhóm, truy vấn chậm lại khi nhiều người dùng cùng lúc, và stakeholder mất tin tưởng rồi quay sang dùng spreadsheet riêng. Tránh sự xuống cấp đó cần định nghĩa metric được quản trị tập trung và freshness dữ liệu được giám sát, không chỉ cần công cụ dashboard nhanh hơn. Xem [Headless BI và semantic layer phổ quát](headless-bi-and-semantic-layers.html) để biết semantic layer dùng chung giải quyết nửa phần định nghĩa của vấn đề này ra sao.

## Từ báo cáo tới phân tích tương tác

Báo cáo truyền thống thường trình bày metric định sẵn theo lịch. BI hiện đại hỗ trợ lọc, drill-down, khám phá và chia sẻ. Hệ thống OLAP tổ chức/tổng hợp dữ liệu đa chiều để so measure theo thời gian, sản phẩm, khu vực.

Cube là mô hình khái niệm của measure và dimension, không nhất thiết là cấu trúc khối literal. Cube tổng hợp trước giúp câu hỏi lặp chạy nhanh nhưng tăng độ phức tạp lưu trữ/refresh. Engine cột hiện đại có thể tính tương tự trực tiếp, nên đo trước khi materialize.

## Chọn bề mặt phục vụ

| Bề mặt | Phù hợp với | Điểm cần thiết kế |
|---|---|---|
| Mart warehouse curated | Phân tích dùng lại và BI | Grain, quyền, freshness, contract ổn định |
| Mô hình ngữ nghĩa BI | Metric nhất quán và self-service | Chủ sở hữu metric, hành vi filter, version |
| Analytics API | Metric và workflow riêng cho ứng dụng | Xác thực, phân trang, latency, tương thích |
| Truy vấn liên kết (federation) | Truy cập ad hoc nhiều hệ thống | Tải nguồn, ngữ nghĩa lệch, latency, cô lập lỗi |
| Reverse ETL | Kích hoạt dữ liệu warehouse chọn lọc trong công cụ vận hành | Chủ sở hữu ghi, freshness, idempotency, đối soát |

Federation tránh sao chép trong một số trường hợp, nhưng query engine vẫn phải xử lý availability nguồn, khả năng pushdown, quyền và khác biệt schema/ngữ nghĩa. Lớp federation không tự tạo nguồn sự thật duy nhất.

### Analytics API như một kiến trúc hợp nhất

"Analytics API" thường được dùng cho nhiều hơn một endpoint đơn lẻ: nó đặt tên cho một mẫu đóng gói năm thành phần sau một bề mặt API duy nhất, để nhóm ứng dụng nhận metric nhất quán mà không phải đụng vào từng phần riêng lẻ:

1. **Query engine hoặc gateway** nhận request, thường qua REST hoặc GraphQL, và định tuyến tới backend phù hợp.
2. **Metric hoặc semantic layer** giữ định nghĩa metric dùng chung để mọi caller nhận cùng câu trả lời cho cùng câu hỏi.
3. **Data catalog** giúp khám phá được metric và dataset nào có thể truy vấn.
4. **Orchestration** giữ dữ liệu phía sau API luôn mới theo lịch đã biết.
5. **SQL connector hoặc lớp thực thi** bên dưới thực sự chạy truy vấn trên warehouse hoặc engine.

Repository này đã có trang riêng cho từng phần — semantic layer, catalog và orchestration đều được trình bày riêng. Mục đích của việc đặt tên tổ hợp này ở đây là để nhận diện: khi một vendor hay một nhóm mô tả "Analytics API của chúng tôi", hãy kiểm tra họ thực sự đóng gói phần nào trong năm phần trên, và phần nào họ mặc định bạn đã có sẵn.

## Nhất quán metric

Giữ định nghĩa metric trong semantic layer hoặc mô hình BI được duyệt. Định nghĩa grain, cơ sở thời gian, bộ lọc, đơn vị, tiền tệ và tính cộng được một lần. Xác nhận dashboard, API và Text2SQL dùng định nghĩa tương thích. Nếu một bề mặt không thể biểu diễn chính xác định nghĩa, hãy tài liệu hóa khác biệt thay vì âm thầm xấp xỉ.

## Xây workflow BI hữu ích

1. Xác định quyết định, người dùng và hành động mà báo cáo hỗ trợ.
2. Thống nhất định nghĩa metric và freshness với chủ sở hữu domain.
3. Thiết kế cho câu hỏi thường gặp trước rồi mới mở khám phá an toàn.
4. Gắn nhãn kỳ, đơn vị, bộ lọc và freshness nguồn trong giao diện.
5. Đo mức sử dụng và chi phí query; loại bỏ phần phức tạp không dùng.
6. Rà thay đổi metric và kiểm tra dashboard quan trọng với fixture chuẩn.

## Tìm hiểu sâu hơn

- [Headless BI và semantic layer phổ quát](headless-bi-and-semantic-layers.html): headless BI, universal semantic layer và Looker.
- [Công cụ BI, trực quan hóa và phân tích tự phục vụ](bi-tools-and-self-service.html): Tableau, Power BI, Apache Superset, Metabase, thiết kế biểu đồ và năng lực dữ liệu.
- [Reverse ETL, phân tích vận hành và CDP](reverse-etl-and-activation.html): Hightouch, Census và nền tảng dữ liệu khách hàng.

## Bài tập

Lấy doanh thu thanh toán theo ngày và khu vực. Định nghĩa metric, cơ sở ngày; thiết kế một dashboard, một response API và một đường phân tích ad hoc. Nêu cách mỗi bề mặt áp dụng quyền, hiển thị freshness và phát hiện ba bề mặt không khớp.