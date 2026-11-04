---
title: Kiến trúc nền tảng dữ liệu và vòng đời
description: Theo dấu dữ liệu từ nguồn vận hành tới sản phẩm phục vụ quyết định có quản trị.
order: 5
tags: [kiến trúc, vòng đời dữ liệu, modern data stack]
---

# Kiến trúc nền tảng dữ liệu và vòng đời

Nền tảng dữ liệu là tập hợp hợp đồng và trách nhiệm giữa nhiều hệ thống, không phải một warehouse hay công cụ điều phối đơn lẻ. Bắt đầu thiết kế từ quyết định và người dùng cần phục vụ, rồi lần ngược tới nguồn, phép biến đổi và kiểm soát cần thiết để phục vụ đáng tin cậy.

## Theo dấu một dữ kiện từ đầu tới cuối

Dùng một sự kiện nghiệp vụ, chẳng hạn đơn hàng đã thanh toán, để lập bản đồ vòng đời:

1. **Ghi nhận vận hành:** ứng dụng ghi đơn hàng vào hệ thống OLTP tối ưu cho giao dịch.
2. **Trích xuất và truyền tải:** connector batch hoặc luồng CDC chuyển thay đổi, giữ định danh nguồn và thời điểm sự kiện.
3. **Vùng raw bền vững:** dữ liệu raw bất biến hoặc có phiên bản cho phép phát lại và kiểm toán.
4. **Biến đổi:** staging chuẩn hóa tên/kiểu; model trung gian mã hóa logic dùng lại; mart phục vụ câu hỏi phân tích đã xác định.
5. **Quản trị và chất lượng:** contract, test, lineage, chủ sở hữu, quyền và freshness làm hành vi quan sát được.
6. **Phục vụ:** BI, analytics API, mô hình ngữ nghĩa và ứng dụng được duyệt đưa dữ liệu tới người dùng.
7. **Phản hồi và vận hành:** sự cố, mức sử dụng, chi phí và chất lượng dữ liệu định hướng thay đổi tiếp theo.

Ở mỗi ranh giới, hỏi định danh, timestamp, phiên bản schema và thông tin chủ sở hữu nào cần đi cùng dữ liệu.

## Các tầng thường gặp

| Tầng | Trách nhiệm | Câu hỏi cần trả lời |
|---|---|---|
| Nguồn | Ghi nhận sự kiện vận hành và entity tham chiếu | Hệ thống nào sở hữu từng sự thật? Cách cập nhật ra sao? |
| Ingestion | Chuyển snapshot hoặc thay đổi đáng tin cậy | Batch, CDC hay stream? Xử lý trùng thế nào? |
| Lưu trữ | Giữ dữ liệu raw/curated bền vững | Format, partition, retention và khôi phục là gì? |
| Compute | Biến đổi, truy vấn và kiểm định | Workload nào cần engine và ranh giới tài nguyên nào? |
| Orchestration | Lập lịch và quan sát phụ thuộc | Xử lý retry, backfill, lỗi một phần ra sao? |
| Governance | Định nghĩa ý nghĩa, chất lượng, quyền và lineage | Ai sở hữu dữ liệu và duyệt thay đổi? |
| Serving | Làm dữ liệu đáng tin có thể sử dụng | Người dùng cần giao diện, latency và freshness nào? |

Modern data stack có thể kết hợp dịch vụ quản lý, công cụ mã nguồn mở và hệ thống doanh nghiệp sẵn có. Chọn theo workload, năng lực vận hành, tính di động, bảo mật và tổng chi phí; không áp dụng stack chỉ vì các thành phần đang phổ biến.

## Các pattern kiến trúc

- **Tầng medallion** thường mô tả dữ liệu được tinh chỉnh dần như bronze/raw, silver/validated và gold/serving. Xem đây là ranh giới chất lượng/trách nhiệm, không phải schema bắt buộc hay thay thế cho contract rõ ràng. Định nghĩa mỗi tầng bảo đảm gì và ai được công bố vào đó.
- **Data mesh** tổ chức quyền sở hữu theo domain nghiệp vụ và xem data product là giao diện được hỗ trợ. Cách này tăng ngữ cảnh domain, giảm nút thắt nhóm trung tâm nhưng không loại bỏ nhu cầu về định danh chung, khả năng tương tác, khám phá dữ liệu và kiểm soát platform. Chỉ áp dụng khi quyền sở hữu domain và năng lực vận hành xứng đáng với chi phí phối hợp.
- **Open data stack** là hướng tiếp cận rộng ưu tiên format, interface có thể tương tác và thành phần có thể thay thế. Tính mở có thể tăng khả năng chuyển đổi, nhưng vẫn cần đánh giá tương thích, hỗ trợ, bảo mật và tổng chi phí trên phiên bản thực tế.
- **Declarative data stack** mô tả asset, dependency và check mong muốn để công cụ lập kế hoạch thực thi từ trạng thái khai báo. Nó khác cách mã hóa thủ công mọi bước vận hành. Hệ thống declarative vẫn cần developer hiểu plan sinh ra, side effect và hành vi khôi phục.

## Lịch sử ngắn của xử lý phân tán

MapReduce và Hadoop giúp tiếp cận xử lý batch phân tán quy mô lớn bằng cách chia công việc trên nhiều máy và phối hợp các bước map, shuffle, reduce. Warehouse/engine cloud hiện đại tự động hóa nhiều chi tiết và bổ sung thực thi tương tác hoặc streaming. Bài học bền vững là hiểu di chuyển dữ liệu, partitioning, skew và khôi phục lỗi; chỉ cần học framework cũ nếu nền tảng mục tiêu yêu cầu.

## Đánh đổi kiến trúc

- **Batch và streaming:** batch thường đơn giản/rẻ hơn nếu freshness theo giờ hoặc ngày là đủ. Streaming thêm phức tạp vận hành, chỉ đáng dùng khi cần độ trễ thấp hoặc phản ứng theo sự kiện.
- **ETL và ELT:** ETL biến đổi trước khi nạp để giảm dữ liệu vào kho phân tích; ELT giữ dữ liệu gần nguồn rồi dùng compute của đích để biến đổi. Riêng tư, quy mô, replay và chi phí ảnh hưởng lựa chọn.
- **Quyền sở hữu tập trung và theo domain:** chuẩn tập trung tăng tính nhất quán; nhóm domain có thêm ngữ cảnh và tốc độ. Mô hình liên kết cần giao diện và quyền quyết định rõ.
- **Dịch vụ quản lý và tự vận hành:** dịch vụ quản lý giảm công việc hạ tầng nhưng có thể đổi lại chi phí, tính di động hoặc ranh giới sản phẩm.

## Vẽ hệ thống trước khi chọn công cụ

Với mỗi luồng, ghi nguồn chuẩn, hướng di chuyển, ranh giới tin cậy, vị trí lưu, chủ sở hữu biến đổi, mục tiêu freshness, đường khôi phục và consumer. Đánh dấu dữ liệu nhạy cảm và dịch vụ ngoài. Sơ đồ tốt giải thích sự cố và trách nhiệm, không chỉ có logo sản phẩm.

## Bài tập

Vẽ nền tảng cho đơn hàng trực tuyến và dữ liệu danh mục sản phẩm. Thể hiện nguồn giao dịch, một đường batch hoặc CDC, thời hạn lưu raw, model warehouse curated, quyền BI và ứng dụng Text2SQL. Ghi danh tính nào đọc/ghi từng tầng, chỉnh sửa đơn đến mart ra sao và xử lý thế nào khi tải bị trễ.