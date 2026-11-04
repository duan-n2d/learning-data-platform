---
title: Dự án 1 - Kho dữ liệu phân tích cốt lõi
description: Xây nền tảng kho dữ liệu cho các dự án phân tích AI tiếp theo.
order: 1
tags: [kho dữ liệu, dbt, SQL]
---

# Dự án 1 - Kho dữ liệu phân tích cốt lõi

## Mục tiêu

Xây kho dữ liệu phân tích sạch, có thể tái tạo từ dữ liệu thô đến mart nghiệp vụ. Dùng bộ dữ liệu đơn hàng công khai hoặc tổng hợp; giữ phạm vi đủ nhỏ để hiểu được mọi bước biến đổi.

## Mục tiêu học tập

- Nêu grain, khóa và cách cập nhật của từng bảng quan trọng.
- Tách ingestion khỏi biến đổi nghiệp vụ, đồng thời giữ lại tầng raw có thể truy vết.
- Làm cho phép biến đổi tất định và an toàn khi chạy lại.
- Kiểm thử riêng ràng buộc kỹ thuật và kỳ vọng nghiệp vụ.

## Kiến trúc

```text
File/API nguồn
-> snapshot raw bất biến
-> staging (đổi tên, ép kiểu, loại trùng)
-> logic nghiệp vụ trung gian
-> mart (fact và dimension)
-> metric, dashboard và Dự án 2
```

### Ví dụ hợp đồng model

```text
Model: fct_orders
Grain: một dòng cho mỗi dòng hàng trong đơn nguồn
Khóa chính: order_line_id
Cơ sở thời gian: order_created_at theo UTC
Measures: quantity, gross_amount, discount_amount, net_amount
Cập nhật muộn: nguồn có thể sửa trạng thái trong 7 ngày
Chủ sở hữu: nhóm analytics engineering
Freshness mục tiêu: có dữ liệu trước 07:00 UTC ngày làm việc
```

Viết hợp đồng này trước khi chọn cách join. Nếu join làm thay đổi grain đã nêu, hãy tổng hợp phía còn lại trước hoặc giải thích vì sao grain mới là chủ đích.

## Trình tự triển khai gợi ý

1. Kiểm kê file hoặc endpoint API; ghi schema, dung lượng và nhịp cập nhật.
2. Đưa bản ghi nguồn vào vùng raw kèm thời điểm ingestion và mã nguồn; giữ payload gốc để gỡ lỗi.
3. Thống kê NULL, khóa trùng, khoảng timestamp và danh mục bất thường.
4. Xây staging để thống nhất kiểu dữ liệu và cách đặt tên mà không che mất ý nghĩa nguồn.
5. Tạo model trung gian cho logic dùng lại, chẳng hạn lịch sử trạng thái đơn hàng.
6. Công bố fact và dimension có grain, quan hệ được tài liệu hóa.
7. Kiểm thử build sạch, build incremental và chạy lại cùng đầu vào.
8. Tài liệu hóa cách backfill khoảng ngày và khôi phục sau lỗi một phần.

## Kiểm tra phân tích ví dụ

Trước khi công bố doanh thu theo ngày, quyết định có tính đơn bị hủy, hoàn tiền và đa tiền tệ hay không. Sau đó so sánh một fixture được tính tay với kết quả model. Test có thể chứng minh phép tính khớp quy tắc đã định nghĩa; test không thể tự chọn quy tắc nghiệp vụ thay bạn.

## Sản phẩm bàn giao

- Hợp đồng dữ liệu nguồn
- Snapshot raw kèm metadata ingestion
- Model staging
- Mart fact và dimension có tài liệu grain
- Test khóa, quan hệ, giá trị cho phép, freshness và quy tắc nghiệp vụ
- Tài liệu model và lineage
- Báo cáo chất lượng dữ liệu cùng các giới hạn đã biết
- Hướng dẫn thiết lập sạch và sơ đồ kiến trúc đơn giản

## Tiêu chí nghiệm thu

- Checkout sạch có thể nạp dữ liệu mẫu và build mọi model theo lệnh đã tài liệu hóa.
- Chạy lại ingestion hoặc phép biến đổi không đếm trùng bản ghi nguồn không đổi.
- Mỗi model được công bố có grain, khóa và chủ sở hữu.
- Ít nhất một dòng nguồn không hợp lệ được báo cáo hoặc cách ly, không bị bỏ âm thầm.
- Báo cáo mẫu đối soát với kết quả đã kiểm tra thủ công.
- Test thất bại khi cố ý tạo khóa trùng hoặc trạng thái nghiệp vụ không hợp lệ.

## Mở rộng

- Thêm xử lý incremental với lookback giới hạn cho dữ liệu đến muộn.
- Thêm kiểm tra freshness nguồn và báo cáo data-diff nhỏ giữa các lần chạy.
- So sánh query plan có và không phân vùng trên dữ liệu đại diện.

## Đầu ra dùng cho dự án sau

Dự án 2 dùng các mart này làm bề mặt SQL đáng tin cậy, được cho phép. Đặt định nghĩa ngữ nghĩa cạnh model để logic metric không lệch giữa kho dữ liệu và chatbot.