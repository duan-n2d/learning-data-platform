---
title: Mô hình hóa dữ liệu phân tích
description: Thiết kế fact, dimension, grain và lịch sử cho phân tích đáng tin cậy.
order: 1
tags: [mô hình dữ liệu, kho dữ liệu, dimensional modeling]
---

# Mô hình hóa dữ liệu phân tích

Model phân tích tốt làm rõ ý nghĩa và grain của dữ liệu. Nó không chỉ là tập bảng tình cờ trả lời được dashboard hiện tại.

## Bắt đầu từ grain

Viết một câu mô tả một dòng đại diện cho điều gì trước khi chọn cột. Ví dụ:

- Một dòng cho mỗi dòng hàng đơn như hệ thống nguồn ghi nhận.
- Một dòng cho mỗi khách hàng mỗi ngày có ít nhất một hoạt động hợp lệ.
- Một dòng cho mỗi số dư tài khoản tại cuối ngày UTC.

Grain quyết định measure nào cộng an toàn và join nào giữ nguyên ý nghĩa. Khóa chính phải định danh một dòng ở grain đó; nếu không, cần giải thích khóa ghép hoặc quy tắc loại trùng.

## Fact và dimension

Fact lưu sự kiện hoặc phép đo định kỳ. Dimension mô tả ngữ cảnh của fact.

| Model | Grain ví dụ | Nội dung thường gặp |
|---|---|---|
| `fct_order_lines` | Một dòng mỗi dòng đơn | Số lượng, tiền hàng, giảm giá, timestamp sự kiện |
| `fct_daily_inventory` | Một dòng mỗi sản phẩm, địa điểm, ngày | Số lượng còn, số lượng giữ chỗ |
| `dim_customer` | Một dòng mỗi phiên bản khách hàng | Phân khúc, khu vực, trạng thái tài khoản |
| `dim_date` | Một dòng mỗi ngày lịch | Tuần, tháng, kỳ tài chính, ngày lễ |

Dùng surrogate key khi định danh trong kho khác khóa nguồn hoặc cần giữ lịch sử. Giữ khóa nguồn để truy vết. Tránh lặp thuộc tính mô tả vào mọi fact trừ khi có chủ đích snapshot hoặc lý do hiệu năng.

## Thuộc tính biến đổi chậm

Với Type 1, ghi đè thuộc tính nếu không cần giá trị lịch sử. Với Type 2, giữ các phiên bản có `valid_from`, `valid_to` và cờ `is_current`. Fact cần join tới phiên bản dimension có hiệu lực tại thời điểm sự kiện nếu báo cáo lịch sử phụ thuộc vào thuộc tính lúc đó.

Định nghĩa timezone và ranh giới khoảng rõ ràng. Quy ước phổ biến là khoảng nửa mở: `valid_from <= event_time AND event_time < valid_to`, tránh chồng lấn hai phiên bản liền kề.

## An toàn khi join

Trước khi join, nêu grain của hai phía và cardinality dự kiến. Join một-nhiều có thể nhân bản dòng fact; khi phù hợp, tổng hợp phía nhiều về grain đích trước. Với quan hệ nhiều-nhiều, dùng bridge tường minh và định nghĩa quy tắc phân bổ nếu measure được chia theo quan hệ.

## Các tầng mô hình và ERD

- **Mô hình khái niệm** gọi tên khái niệm nghiệp vụ và quan hệ, chưa quyết định chi tiết lưu trữ.
- **Mô hình logic** định nghĩa entity, thuộc tính, định danh và cardinality quan hệ.
- **Mô hình vật lý** ánh xạ quyết định đó thành bảng, cột, kiểu, khóa, partition và ràng buộc theo engine.

Sơ đồ thực thể-quan hệ (ERD) chỉ hữu ích khi định nghĩa entity và cardinality rõ ràng. Đánh dấu quan hệ tùy chọn, khóa định danh và grain của entity sự kiện. Dùng mô hình khái niệm để giải quyết ý nghĩa nghiệp vụ trước khi tối ưu schema vật lý.

## Chuẩn hóa và phi chuẩn hóa

Chuẩn hóa tách các dữ kiện thuộc về entity khác nhau và giảm bất thường cập nhật trong hệ thống vận hành. Dạng chuẩn một, hai, ba là cách hữu ích để suy nghĩ về nhóm lặp và phụ thuộc; không phải yêu cầu chia mọi model phân tích thành số bảng tối đa.

Mart phân tích thường phi chuẩn hóa dimension hoặc tính trước giá trị dẫn xuất để mẫu truy cập phổ biến đơn giản và nhất quán hơn. Phi chuẩn hóa tạo trạng thái lặp, cần chủ sở hữu, cách refresh và đối soát rõ. Chọn theo workload và ngữ nghĩa, không xem một phong cách là luôn đúng.

## Lập kế hoạch dimensional và Data Vault

Bus matrix liệt kê quy trình nghiệp vụ theo các dimension dùng chung. Nó giúp nhóm thống nhất dimension như ngày, khách hàng, sản phẩm, địa điểm nào cần conform giữa các fact trước khi tạo nhiều mart độc lập.

Dimensional modeling phù hợp phân tích ổn định, hướng quyết định. Data Vault tách khóa nghiệp vụ và quan hệ thành hub/link, còn satellite lưu lịch sử mô tả và ngữ cảnh nguồn. Cách này có thể hỗ trợ tích hợp nhiều nguồn thay đổi và giữ khả năng kiểm toán, nhưng thêm nhiều cấu trúc và bước biến đổi. Chỉ chọn khi tích hợp nguồn và truy vết lịch sử xứng đáng với độ phức tạp; không mặc định nó tốt hơn mô hình báo cáo. Một số nền tảng dùng tầng tích hợp historized rồi công bố mart dimensional cho người dùng.

## Các hướng modeling khác

- **Mô hình doanh nghiệp kiểu Inmon** thường tích hợp warehouse chuẩn hóa toàn doanh nghiệp trước rồi mới công bố mart downstream. Cách này ưu tiên nhất quán chung nhưng có thể cần nhiều phối hợp và thiết kế ban đầu.
- **Dimensional modeling kiểu Kimball** xây quanh quy trình nghiệp vụ, fact và dimension conform, thường bàn giao mart có ích theo từng bước. Bus matrix giúp các mart nhất quán.
- **Anchor Modeling** là hướng quan hệ có lịch sử, tách định danh ổn định khỏi thuộc tính/quan hệ thay đổi. Nó hỗ trợ tiến hóa schema thường xuyên nhưng thêm khái niệm và join; chỉ dùng khi linh hoạt thời gian giải quyết vấn đề thực.
- **Activity schema** biểu diễn sự kiện nghiệp vụ thành activity thiên về ghi nối tiếp, có timestamp, actor và entity liên quan. Nó làm phân tích theo sự kiện linh hoạt, nhưng consumer vẫn cần định nghĩa event, quy tắc khử trùng và trạng thái dẫn xuất khi cần snapshot hiện tại.

Đây là các họ thiết kế, không phải quy tắc loại trừ nhau. Platform có thể dùng tầng tích hợp chuẩn hóa, cấu trúc historized và mart dimensional phục vụ các nhu cầu khác nhau. Chọn cách đơn giản nhất đáp ứng tích hợp, lịch sử, thay đổi và tiêu thụ.

## Dữ liệu chủ và dữ liệu tham chiếu

Dữ liệu chủ mô tả entity nghiệp vụ dùng chung như khách hàng/sản phẩm; dữ liệu tham chiếu cung cấp giá trị kiểm soát như mã quốc gia/trạng thái. Xác định nguồn chuẩn, khóa liên hệ giữa hệ thống, quy tắc match/merge và chủ thể giải quyết xung đột. Giữ định danh nguồn và lịch sử để entity hợp nhất không xóa mất nguồn gốc.

## Checklist rà soát

- [ ] Mỗi model có câu mô tả grain và khóa ổn định.
- [ ] Measure được phân loại cộng được, bán cộng được hay không cộng được.
- [ ] Timestamp có timezone và quy tắc ngày nghiệp vụ.
- [ ] Cách giữ lịch sử thuộc tính thay đổi được xác định.
- [ ] Khóa và cardinality join được kiểm thử.
- [ ] Cách xử lý NULL, unknown và dữ liệu đến muộn có tài liệu.
- [ ] Quyết định khái niệm, logic và vật lý được tách riêng, rà soát đúng cấp độ.
- [ ] Chuẩn hóa hoặc phi chuẩn hóa được biện minh bằng hành vi cập nhật và workload tiêu thụ.
- [ ] Dimension dùng chung và định danh dữ liệu chủ/tham chiếu có chủ sở hữu rõ.

## Bài tập

Mô hình hóa doanh nghiệp thuê bao gồm subscription, invoice, invoice line, customer và plan. Nêu grain từng bảng, tìm một metric sẽ bị đếm trùng khi join ngây thơ và chọn thuộc tính khách hàng nào cần giữ lịch sử.