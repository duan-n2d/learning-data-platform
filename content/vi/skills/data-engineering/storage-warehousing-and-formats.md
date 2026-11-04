---
title: Lưu trữ, kho dữ liệu và định dạng bảng
description: Chọn lưu trữ giao dịch và phân tích theo workload, độ bền và nhu cầu truy cập.
order: 6
tags: [lưu trữ, data warehouse, lakehouse, định dạng file]
---

# Lưu trữ, kho dữ liệu và định dạng bảng

Thiết kế lưu trữ bắt đầu từ workload và yêu cầu khôi phục. Định dạng file, database hay table format là phương tiện đáp ứng yêu cầu, không tự nó tạo thành kiến trúc.

## OLTP và OLAP phục vụ workload khác nhau

| Thuộc tính | Hệ thống OLTP | Hệ thống OLAP |
|---|---|---|
| Mục đích | Ghi nhận trạng thái vận hành hiện tại | Phân tích lượng lớn dữ liệu lịch sử |
| Thao tác thường gặp | Nhiều lần đọc/ghi ngắn theo khóa | Ít lượt scan, join, aggregate trên nhiều dòng |
| Xu hướng mô hình | Chuẩn hóa để bảo vệ nhất quán giao dịch | Phi chuẩn hóa hoặc tổ chức cho truy cập phân tích |
| Ví dụ | Cập nhật trạng thái thanh toán của một đơn | So doanh thu đã trả theo tháng và kênh |

Ứng dụng vận hành vẫn là nguồn chuẩn cho giao dịch. Hệ thống phân tích sao chép và tái cấu trúc dữ liệu; không nên âm thầm trở thành đường ghi cạnh tranh cho trạng thái vận hành.

## Warehouse, lake và lakehouse

- **Data warehouse** cung cấp cấu trúc được quản lý, hướng truy vấn và governance cho workload phân tích.
- **Data lake** lưu lượng lớn file, thường có dữ liệu raw và nhiều schema khác nhau.
- **Lakehouse** kết hợp object/file storage với metadata bảng và tính năng giao dịch nhằm tăng độ tin cậy khi truy cập phân tích.

Đây là các hướng thiết kế rộng, không phải cam kết sản phẩm có thể thay thế nhau. Hãy so hành vi giao dịch, concurrency, tích hợp catalog, tiến hóa schema, retention, recovery, cô lập workload và tổng chi phí của cách triển khai cụ thể.

## Định dạng file

| Định dạng | Đặc điểm hữu ích | Đánh đổi cần xét |
|---|---|---|
| CSV | Đơn giản, dễ đọc, hỗ trợ rộng | Kiểu yếu, scan lớn, dễ mơ hồ delimiter/escaping |
| JSON | Linh hoạt với record lồng nhau, phổ biến ở API | Lặp tên trường, schema thiếu nhất quán, scan phân tích tốn kém |
| Avro | Mã hóa dạng dòng gọn, có hỗ trợ schema | Không hiệu quả bằng cột khi phân tích ít cột trên tập lớn |
| Parquet | Mã hóa dạng cột, nén và chỉ đọc cột cần thiết | File quá nhỏ hoặc partition kém vẫn gây workload tốn kém |

Chọn theo cách ghi/đọc, nhu cầu schema, hỗ trợ hệ sinh thái và khả năng debug. Bản thân file format không cung cấp commit nguyên tử cấp bảng hay cập nhật đồng thời an toàn.

## File format và table format

File format định nghĩa cách mã hóa record. Table format bổ sung metadata về file và trạng thái bảng, có thể hỗ trợ snapshot, thay đổi metadata nguyên tử, tiến hóa schema/partition và time travel. Apache Iceberg, Delta Lake và Apache Hudi có tập tính năng/mô hình vận hành khác nhau; kiểm tra hành vi của engine và catalog thực tế.

## Transaction, snapshot và khôi phục

ACID mô tả atomicity, consistency, isolation và durability trong ranh giới của một hệ thống xác định. Không giả định một transaction trải khắp mọi source, object store, catalog và consumer. Hiểu commit protocol, hành vi nhiều writer, thời điểm hết hạn snapshot và ngữ nghĩa khôi phục của nền tảng thực tế.

Snapshot hỗ trợ đọc tái tạo và rollback nhưng tốn lưu trữ, cần chính sách retention. Thử restore và time travel trước khi dựa vào chúng trong sự cố.

## Thiết kế vật lý

Chỉ partition theo trường thường lọc khi partition pruning có ích. Quá nhiều partition/file nhỏ làm tăng overhead metadata và lập lịch. Nén cột và column pruning có thể giảm scan, nhưng còn phụ thuộc hình dạng query, kích thước file, clustering và engine. Tách compute khỏi storage nếu nền tảng hỗ trợ và lợi ích cô lập workload hoặc scale độc lập là đáng kể.

## Bài tập

Với workload phân tích đơn hàng, chọn nơi lưu record OLTP, nơi lưu bản raw bất biến và cách lưu bảng curated. So CSV, JSON, Parquet cho một nguồn. Tài liệu hóa khả năng table format, ranh giới transaction, partition, retention, ghi đồng thời và cách khôi phục khi tải ngày bị hỏng.