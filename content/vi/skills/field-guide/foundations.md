---
title: Cẩm nang nền tảng Data Engineering
description: Nền tảng thực hành về vòng đời dữ liệu, kiến trúc, mô hình hóa, ngữ nghĩa và vai trò kỹ sư.
order: 1
tags: [kỹ nghệ dữ liệu, nền tảng, vòng đời, mô hình hóa]
---

# Cẩm nang nền tảng Data Engineering

Cẩm nang này kết nối các ý tưởng cốt lõi phía sau một nền tảng dữ liệu. Đây là nội dung học nguyên bản của curriculum, không sao chép bản đồ đọc bên ngoài. Dùng các bài liên quan để thực hành chi tiết; dùng trang này để hiểu các khái niệm gắn với nhau thế nào.

## 1. Data Engineering làm gì?

Data Engineering xây dựng và vận hành hệ thống giúp dữ liệu sẵn có, dễ hiểu, đáng tin cậy và được quản trị phù hợp cho người dùng/ứng dụng. Công việc gồm thu nhận dữ liệu, giữ lịch sử, biến đổi thành dạng hữu ích, phục vụ qua giao diện thích hợp và vận hành toàn bộ luồng khi yêu cầu thay đổi.

Pipeline thành công không chỉ là task trả mã thoát bằng zero. Consumer cần biết mỗi giá trị có nghĩa gì, mới tới đâu, vượt qua kiểm tra chất lượng nào, ai sở hữu và hệ thống phản ứng ra sao khi nguồn trễ hoặc đổi cấu trúc.

## 2. Vòng đời dữ liệu

Vòng đời hữu ích là một chu trình phản hồi:

1. **Khám phá:** xác định người dùng, quyết định, nguồn, ràng buộc và kết quả mong đợi.
2. **Thiết kế:** đặt grain, contract, kiến trúc, quyền, mục tiêu freshness và hành vi lỗi.
3. **Ingestion:** lấy snapshot hoặc thay đổi kèm định danh, event time và checkpoint phát lại.
4. **Biến đổi:** chuẩn hóa biểu diễn và mã hóa logic nghiệp vụ đã được duyệt.
5. **Phục vụ:** công bố qua mart, metric model, API, báo cáo hoặc ứng dụng.
6. **Vận hành:** quan sát chất lượng, freshness, latency, chi phí và quyền; xử lý sự cố.
7. **Phát triển hoặc ngừng:** chuyển người dùng an toàn, truyền thông thay đổi và xóa dữ liệu cũ theo chính sách lưu giữ.

Vòng đời mang tính lặp. Sự cố production có thể làm lộ contract thiếu; consumer mới có thể cần mô hình serving khác. Ghi lại tín hiệu phản hồi và dùng chúng để sửa thiết kế thay vì liên tục thêm vá tạm.

## 3. Kiến trúc: theo dấu dữ liệu, không theo logo

Với một sự thật nghiệp vụ, vẽ luồng từ nguồn tới quyết định. Đơn đã thanh toán có thể được ghi trong database vận hành, lấy bằng batch hằng ngày hoặc connector CDC, lưu ở vùng raw bền vững, biến đổi thành model order-line/doanh thu ngày rồi phục vụ BI hoặc ứng dụng.

Ở mỗi ranh giới, xác định:

- Hệ thống chuẩn và ai sở hữu ý nghĩa.
- Định danh, thời điểm sự kiện, thời điểm ingestion và phiên bản schema.
- Dữ liệu được sao chép, biến đổi, lọc hay join ra sao.
- Ranh giới tin cậy/truy cập, kể cả dịch vụ bên ngoài.
- Freshness, hành vi retry và cách khôi phục kỳ vọng.
- Consumer và contract mà consumer dựa vào.

Sơ đồ cuối cần chỉ ra lỗi phát hiện ở đâu và ai xử lý. Chọn sản phẩm phổ biến mà chưa định nghĩa ranh giới thì chưa phải thiết kế kiến trúc.

## 4. Mô hình hóa ở nhiều cấp độ

**Mô hình khái niệm** gọi tên khái niệm nghiệp vụ và quan hệ. **Mô hình logic** định nghĩa entity, thuộc tính, định danh và cardinality mà chưa gắn database. **Mô hình vật lý** ánh xạ thành bảng, cột, kiểu dữ liệu, khóa, partition và ràng buộc theo engine.

ERD là công cụ truyền đạt cấu trúc logic. Nó cần thể hiện quan hệ một-một, một-nhiều, tùy chọn hay nhiều-nhiều. Xác minh sơ đồ với dữ liệu quan sát và quy tắc nghiệp vụ; sơ đồ đẹp không biến giả định sai về nguồn thành sự thật.

### Chuẩn hóa

Chuẩn hóa tách dữ kiện theo phụ thuộc. Trong hệ thống vận hành, nó giảm bất thường như phải cập nhật địa chỉ khách hàng ở nhiều dòng hoặc xóa mất bản ghi sản phẩm duy nhất khi xóa đơn. Dạng chuẩn một, hai, ba là công cụ suy luận về nhóm lặp và phụ thuộc, không phải đích cần tối đa hóa ở mọi schema phân tích.

### Dimensional modeling

Mô hình dimensional tổ chức phép đo quanh quy trình nghiệp vụ. Fact có grain rõ và measure; dimension cung cấp ngữ cảnh mô tả. Dimension conform giúp nhiều quy trình dùng khái niệm chung nhất quán như khách hàng, ngày hay sản phẩm. Bus matrix ánh xạ quy trình vào dimension dùng chung để lập kế hoạch tập mart nhất quán.

### Inmon và Kimball là các truyền thống thiết kế

Cách tiếp cận kiểu Inmon thường bắt đầu bằng warehouse doanh nghiệp tích hợp, chuẩn hóa rồi tạo mart downstream. Nó nhấn mạnh tích hợp chung nhưng có thể cần nhiều phối hợp ban đầu. Cách kiểu Kimball xây quanh quy trình, fact và dimension conform, thường bàn giao mart hữu ích từng bước. Cách này làm rõ câu hỏi phân tích nhưng cần kỷ luật giữ dimension conform.

Đây là truyền thống thiết kế hữu ích, không phải luật loại trừ nhau. Platform có thể dùng tầng tích hợp chuẩn hóa rồi công bố mart dimensional. Chọn theo độ phức tạp nguồn, yêu cầu lịch sử, ràng buộc bàn giao và nhu cầu consumer.

### Entity-centric và các mô hình khác

Mô hình entity-centric tổ chức thông tin quanh entity nghiệp vụ bền vững và quan hệ thay vì bắt đầu từ báo cáo. Cách này hữu ích khi nhiều trường hợp dùng cần góc nhìn khách hàng, sản phẩm hoặc tài khoản nhất quán. Thành công phụ thuộc giải quyết định danh và quyền sở hữu quan hệ rõ.

Data Vault, Anchor Modeling, activity schema và mô hình quan hệ xử lý các bài toán thay đổi/lịch sử khác nhau. Data Vault tách khóa/quan hệ nghiệp vụ khỏi ngữ cảnh mô tả có lịch sử. Anchor Modeling tách định danh ổn định khỏi thuộc tính thay đổi. Activity schema biểu diễn sự kiện theo thời gian, actor và entity liên quan. Mỗi cách thêm cấu trúc hoặc yêu cầu diễn giải; chỉ dùng khi bài toán tích hợp/lịch sử biện minh cho chi phí đó.

## 5. Xem data asset là giao diện được hỗ trợ

Data asset là đầu ra được duy trì mà người khác phụ thuộc: bảng, stream, metric model, API hoặc bộ tài liệu curated. Asset hữu ích có mục đích, chủ sở hữu, schema, grain, kỳ vọng chất lượng, freshness, quyền, lineage và chính sách thay đổi.

Data product là asset được xem như giao diện được hỗ trợ cho consumer xác định. Cần đường hỗ trợ và kế hoạch vòng đời, không chỉ có tên gọi. Nếu không có consumer, owner hay kỳ vọng, trước tiên hãy xác định có nên duy trì asset đó không.

## 6. Ý nghĩa, ngữ nghĩa và lineage

Semantic layer biểu diễn entity, dimension, metric và quan hệ hợp lệ dưới dạng dùng lại. Định nghĩa metric cần grain, biểu thức, bộ lọc, cơ sở thời gian, đơn vị, cách xử lý tiền tệ, owner và ví dụ. Thuật ngữ glossary không có logic thực thi có thể lệch query thật; query không có định nghĩa nghiệp vụ có thể đúng kỹ thuật nhưng trả lời sai câu hỏi.

Lineage ghi cách dữ liệu đi từ nguồn qua phép biến đổi đến consumer. Lineage kỹ thuật giúp tìm model bị ảnh hưởng khi schema đổi; lineage nghiệp vụ giải thích vì sao biến đổi tồn tại và quyết định nào được hỗ trợ. Dùng cả hai khi có thể để chẩn đoán sự cố, kiểm toán và ngừng asset an toàn.

## 7. Vai trò Data Engineer

Data Engineer kết hợp phát triển phần mềm, mô hình hóa, tư duy hệ thống phân tán, bảo mật và vận hành. Họ chuyển đổi giữa người dùng domain và hệ thống kỹ thuật, làm rõ giả định ngầm và giúp consumer dùng dữ liệu mà không cần đoán cách tạo ra nó.

Vai trò này giao với Software Engineering ở test, review mã, thiết kế module, CI/CD, độ tin cậy và ứng phó sự cố. Điểm nhấn riêng là ý nghĩa dữ liệu, grain, hành vi thời gian, chất lượng, lineage và workload phân tích. Không vai trò nào chỉ là quản trị công cụ; thực hành tốt cần hiểu người dùng, ghi quyết định, xử lý sự cố và cải thiện hệ thống dựa trên bằng chứng.

## Checklist rà soát thực tế

- Thành viên mới có thể truy ngược một giá trị từ nguồn tới consumer không?
- Grain của từng bảng có được nêu trước khi chọn measure và join không?
- Ownership, freshness, quality, quyền và retention đã rõ chưa?
- Kiểu modeling có phù hợp yêu cầu thay đổi và lịch sử không?
- Consumer có tìm được định nghĩa, lineage và owner hỗ trợ không?
- Có cách đã kiểm thử để replay, sửa hoặc ngừng asset không?

## Bài tập

Chọn metric như doanh thu đã trả theo tháng. Vẽ luồng nguồn tới consumer, tạo ERD khái niệm, nêu grain fact, xác định dimension dùng chung, viết contract metric và đánh dấu lineage kỹ thuật/nghiệp vụ. Thêm một lần sửa muộn, mô tả kết quả công bố đổi thế nào và thông báo consumer ra sao.

## Học tiếp

- [Kiến trúc platform và vòng đời](../data-engineering/platform-architecture-and-lifecycle.html)
- [Mô hình hóa dữ liệu phân tích](../data-engineering/data-modeling.html)
- [Governance và data product](../data-engineering/governance-and-data-products.html)
- [Lớp ngữ nghĩa](../ai/semantic-layer.html)
- [Dự án 1: Kho dữ liệu phân tích cốt lõi](../../projects/project-1-analytics-warehouse.html)