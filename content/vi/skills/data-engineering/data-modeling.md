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

## Các tầng mô hình hóa xuyên suốt pipeline

Trục khái niệm/logic/vật lý ở trên nói về mức độ model đã cam kết vào chi tiết hiện thực. Một trục thứ hai, bổ sung cho trục trên, nói về *vị trí trong vòng đời dữ liệu* mà quyết định mô hình hóa được đưa ra. Cùng một entity nghiệp vụ hoàn toàn có thể được mô hình hóa khác nhau ở mỗi tầng, và đó không phải là mâu thuẫn cần giải quyết — nó phản ánh đối tượng sử dụng và mối quan tâm khác nhau tại mỗi điểm:

- **Schema database nguồn**: do đội ứng dụng sở hữu, tối ưu cho tính đúng đắn giao dịch và ghi từng dòng. Đội phân tích hiếm khi kiểm soát được nó và nên xem nó như một hợp đồng bên ngoài có thể thay đổi mà không báo trước.
- **Tầng tích hợp / staging**: chuẩn hóa kiểu dữ liệu, tên gọi và khóa giữa các nguồn trước khi áp dụng logic nghiệp vụ. Thường gần với grain của nguồn, chỉ thêm kiểu dữ liệu nhẹ, đổi tên và khử trùng.
- **Tầng ETL / biến đổi**: mô hình hóa xoay quanh chính các bước biến đổi. Các bảng trung gian ở đây tồn tại để pipeline dễ kiểm thử và debug, không phải để consumer nghiệp vụ truy vấn trực tiếp.
- **Schema warehouse / dimensional**: mô hình hóa cho báo cáo conform, có thể kiểm toán — chính là fact và dimension đã mô tả ở trên.
- **Tầng BI / trình bày**: mô hình hóa theo cách người dùng khám phá dữ liệu, thường là một view phi chuẩn hóa thêm hoặc gán nhãn ngữ nghĩa (một bảng rộng duy nhất, hoặc định nghĩa metric của semantic layer) đánh đổi một phần linh hoạt lấy khả năng khám phá.
- **Tầng feature engineering cho ML**: mô hình hóa xoay quanh tính đúng đắn theo thời điểm (point-in-time) giữa lúc huấn luyện và lúc phục vụ. Lỗi thường gặp nhất ở đây là rò rỉ (leakage) thông tin từ tương lai vào một dòng huấn luyện, khác với lỗi join dimensional sai grain, dù cả hai đều là "lỗi mô hình hóa".

Dùng trục vòng đời này để hỏi "quyết định này nằm ở đâu và ai tiêu thụ nó", còn trục khái niệm/logic/vật lý để hỏi "quyết định này cam kết vào chi tiết hiện thực tới mức nào". Một bảng vật lý duy nhất trong warehouse vẫn có thể được mô tả ở mức khái niệm, logic hoặc vật lý; hai trục mô tả hai điều khác nhau và nên dùng cùng nhau, không thay thế cho nhau.

## Chuẩn hóa và phi chuẩn hóa

Chuẩn hóa tách các dữ kiện thuộc về entity khác nhau và giảm bất thường cập nhật trong hệ thống vận hành. Dạng chuẩn một, hai, ba là cách hữu ích để suy nghĩ về nhóm lặp và phụ thuộc; không phải yêu cầu chia mọi model phân tích thành số bảng tối đa.

Mart phân tích thường phi chuẩn hóa dimension hoặc tính trước giá trị dẫn xuất để mẫu truy cập phổ biến đơn giản và nhất quán hơn. Phi chuẩn hóa tạo trạng thái lặp, cần chủ sở hữu, cách refresh và đối soát rõ. Chọn theo workload và ngữ nghĩa, không xem một phong cách là luôn đúng.

## Lập kế hoạch dimensional và Data Vault

Bus matrix liệt kê quy trình nghiệp vụ theo các dimension dùng chung. Nó giúp nhóm thống nhất dimension như ngày, khách hàng, sản phẩm, địa điểm nào cần conform giữa các fact trước khi tạo nhiều mart độc lập.

Dimensional modeling phù hợp phân tích ổn định, hướng quyết định. Data Vault tách khóa nghiệp vụ và quan hệ thành hub/link, còn satellite lưu lịch sử mô tả và ngữ cảnh nguồn. Cách này có thể hỗ trợ tích hợp nhiều nguồn thay đổi và giữ khả năng kiểm toán, nhưng thêm nhiều cấu trúc và bước biến đổi. Chỉ chọn khi tích hợp nguồn và truy vết lịch sử xứng đáng với độ phức tạp; không mặc định nó tốt hơn mô hình báo cáo. Một số nền tảng dùng tầng tích hợp historized rồi công bố mart dimensional cho người dùng.

## Các hướng modeling khác

- **Mô hình doanh nghiệp kiểu Inmon** thường tích hợp warehouse chuẩn hóa toàn doanh nghiệp trước rồi mới công bố mart downstream. Cách này ưu tiên nhất quán chung nhưng có thể cần nhiều phối hợp và thiết kế ban đầu.
- **Dimensional modeling kiểu Kimball** xây quanh quy trình nghiệp vụ, fact và dimension conform, thường bàn giao mart có ích theo từng bước. Bus matrix giúp các mart nhất quán.

Anchor Modeling và Activity Schema đáng xem kỹ hơn vì mỗi cách đều có thuật ngữ riêng, dễ dùng sai nếu không thấy rõ các thành phần được đặt tên.

### Thuật ngữ Anchor Modeling

Anchor Modeling là hướng quan hệ có lịch sử, tách định danh ổn định khỏi thuộc tính/quan hệ thay đổi, dùng bốn loại bảng được đặt tên:

- **Anchors (mỏ neo)** chỉ giữ định danh — một surrogate key và không gì khác, tương tự hub trong Data Vault. Bảng `Anchor_Customer` không có cột mô tả nào cả, chỉ có khóa và metadata về thời điểm dòng được tạo.
- **Attributes (thuộc tính)** giữ một thuộc tính có phiên bản theo thời gian trên mỗi bảng, mỗi bảng khóa ngược về anchor của nó. Email và phân khúc của khách hàng nằm ở hai bảng attribute riêng biệt, để một bên có thể giữ lịch sử độc lập với bên kia thay vì buộc mọi thuộc tính phải đổi phiên bản cùng lúc.
- **Ties (liên kết)** ghi nhận quan hệ giữa các anchor — tương đương bảng link trong Data Vault — và bản thân có thể được versioned theo thời gian khi quan hệ đó thay đổi (ví dụ: sales rep nào phụ trách một tài khoản).
- **Knots (nút)** giữ các giá trị tra cứu nhỏ, cardinality thấp, có thể dùng lại, như mã trạng thái hoặc quốc gia, dùng chung cho nhiều anchor để không phải lặp lại cùng một danh sách mã cho từng entity.

**Ví dụ (minh họa).** Một anchor `Customer` với các bảng attribute `Email` và `Segment`, cùng một knot `Country`, nghĩa là khi đổi segment chỉ ghi một dòng mới vào bảng attribute segment; bảng attribute email, anchor và knot country không bị đụng tới.

**Lỗi thường gặp.** Tách mỗi thuộc tính thành một bảng riêng làm thay đổi schema trở thành thao tác cộng thêm — thêm bảng thay vì alter bảng — nhưng một truy vấn đơn giản "xem thông tin khách hàng này" giờ phải join qua rất nhiều bảng. Hầu hết hiện thực Anchor Modeling tạo sẵn các view báo cáo rộng ở trên để che việc này khỏi consumer phía dưới; truy vấn trực tiếp cấu trúc anchor trong công cụ BI là lỗi áp dụng thường gặp.

### Triết lý thiết kế Activity Schema

Thiết kế Activity Schema (gắn liền với cách tiếp cận Narrator / "activity schema" được Ahmed Elsamadisi phổ biến) xuất phát từ một giả định khác với dimensional modeling: thay vì tách một sự kiện thành fact và dimension rồi join lại lúc truy vấn, mọi sự kiện mà nghiệp vụ quan tâm được append thành một dòng vào một bảng rộng duy nhất, thường gọi là **activity stream**. Mỗi dòng đã mang sẵn actor, activity, timestamp và các cột feature mà activity đó cần, nên phần lớn câu hỏi kiểu "bao nhiêu khách hàng đã làm X" hay "thời gian giữa X và Y" có thể trả lời bằng cách lọc và tự join trên chính bảng đó, thay vì dựng một star schema.

Hai quy tắc thiết kế mang lại phần lớn lợi ích:

- **Một định nghĩa chuẩn duy nhất cho mỗi activity.** "Đã đặt đơn hàng" được định nghĩa một lần, ở một nơi, và mọi team đọc từ cùng định nghĩa đó thay vì tự viết SQL riêng cho việc gì được tính là một đơn hàng. Đây chính là điều làm cho metric kết quả có thể chia sẻ và so sánh được giữa các team — không ai âm thầm định nghĩa lại cùng một activity với bộ lọc hơi khác.
- **Không cần join cho phần lớn phân tích.** Vì grain là "một lần xảy ra activity", phần lớn phân tích funnel, retention và thời gian giữa các sự kiện chỉ cần đọc và tự join activity stream, không cần điều hướng một bus matrix các dimension conform.

**Lỗi thường gặp.** Một snapshot trạng thái hiện tại (ví dụ "gói hiện tại của khách hàng") vẫn phải được suy ra từ lịch sử activity khi consumer cần — activity stream không loại bỏ nhu cầu về trạng thái dẫn xuất đã nói ở phần trước của trang này. Một bảng rộng duy nhất cũng có thể tích lũy rất nhiều cột feature thưa nếu thuộc tính của mọi activity đều giữ trên cùng một dòng; chi phí đó được đánh đổi với sự đơn giản của việc không phải join, và cần cân nhắc có chủ đích chứ không phải mặc định bỏ qua.

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

## Các thực hành data engineering: checklist tổng hợp

Quyết định mô hình hóa không đứng một mình; chúng tương tác với các thực hành ingestion, orchestration và governance đã trình bày ở nơi khác trong roadmap này. Checklist dưới đây gom các thực hành đó thành một lượt rà soát chéo, chạy cùng với checklist rà soát mô hình hóa ở trên. Mỗi mục liên kết tới trang trình bày chi tiết thay vì giải thích lại ở đây.

- [ ] **Nạp dữ liệu thô trước khi mô hình hóa.** Ưu tiên landing kiểu lake / raw-zone-first để một lỗi mô hình hóa có thể tính lại từ bản sao chưa biến đổi của nguồn thay vì bị "đóng cứng" vĩnh viễn. Xem [Lưu trữ, Kho dữ liệu và Table Format](storage-warehousing-and-formats.html) và [Kiến trúc nền tảng và vòng đời](platform-architecture-and-lifecycle.html).
- [ ] **Làm cho biến đổi idempotent.** Chạy lại một pipeline mô hình hóa phải cho cùng kết quả, không nhân đôi hay lệch, nhất là sau một lần retry hoặc backfill. Xem [Điều phối pipeline](orchestration.html).
- [ ] **Ưu tiên khóa nghiệp vụ/tự nhiên ổn định cho join** ở nơi chúng thực sự ổn định, thay vì tạo ra surrogate key trước khi biết định danh nguồn có đáng tin hay không. Chỉ đưa surrogate key vào khi lịch sử hoặc định danh liên hệ thống thực sự cần — xem phần "Fact và dimension" ở trên.
- [ ] **Giữ pipeline khai báo (declarative) khi có thể**, mô tả output và phụ thuộc mong muốn thay vì luồng điều khiển từng bước mệnh lệnh (imperative), để logic phụ thuộc và backfill nằm trong orchestrator thay vì rải rác trong script. Xem [Điều phối pipeline](orchestration.html).
- [ ] **Tập trung metadata vào một catalog** để định danh bảng, schema, chủ sở hữu và lineage có thể tra cứu được thay vì chỉ nằm trong đầu từng người. Xem [Metadata Catalog, khám phá và lineage](metadata-catalogs-and-lineage.html).
- [ ] **Tránh ALTER DDL tại chỗ trên bảng production.** Ưu tiên thay đổi schema theo kiểu cộng thêm, có versioned, hoặc dùng tính năng schema-evolution của chính table format, thay vì alter hình dạng một bảng đang chạy ngay dưới chân các consumer đang đọc. Xem [Lưu trữ, Kho dữ liệu và Table Format](storage-warehousing-and-formats.html).

## Bài tập

Mô hình hóa doanh nghiệp thuê bao gồm subscription, invoice, invoice line, customer và plan. Nêu grain từng bảng, tìm một metric sẽ bị đếm trùng khi join ngây thơ và chọn thuộc tính khách hàng nào cần giữ lịch sử.