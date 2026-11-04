---
title: Cẩm nang hạ tầng dữ liệu hiện đại
description: So sánh lưu trữ, warehouse, lakehouse, query engine, định dạng mở và hạ tầng phân tích.
order: 2
tags: [hạ tầng, warehouse, lakehouse, query engine]
---

# Cẩm nang hạ tầng dữ liệu hiện đại

Lựa chọn hạ tầng phải dựa trên hình dạng dữ liệu, mẫu truy cập, độ trễ, năng lực nhóm, governance và chi phí. Danh sách sản phẩm không phải kiến trúc đích: cần hiểu ranh giới mỗi thành phần sở hữu và kiểu lỗi nó đưa vào.

## Bắt đầu từ workload

Phân loại workload trước khi chọn hệ thống:

- Ghi giao dịch và đọc ngắn theo khóa thường thuộc database OLTP.
- Scan, join, aggregate lặp lại trên lịch sử là workload phân tích (OLAP).
- Khám phá cục bộ trên file có thể không cần cluster hay warehouse quản lý.
- Phân tích production dùng chung cần concurrency được quản lý, vận hành dự đoán được, quyền và khôi phục.
- Streaming có yêu cầu event-time và dữ liệu đến muộn mà batch có thể không đáp ứng.

Đo dung lượng dự kiến, số người dùng, concurrency, freshness, retention, mục tiêu khôi phục và ranh giới dữ liệu nhạy cảm. Rà lại giả định khi mức sử dụng tăng.

## Warehouse, lake và lakehouse

Cloud data warehouse thường quản lý metadata lưu trữ, lập kế hoạch query và compute cho phân tích SQL. Nhà cung cấp khác nhau về cô lập workload, transaction, tích hợp format mở, governance và giá. So hành vi workload và hợp đồng vận hành thay vì chỉ dựa nhãn tính năng.

Object storage cung cấp lưu file/snapshot bền vững, chi phí tương đối thấp nhưng file đơn lẻ không có transaction bảng, kiểm soát concurrency hay schema được quản trị. Data lake thường chứa nhiều format và giai đoạn dữ liệu. Lakehouse thêm lớp metadata bảng/transaction để file hoạt động gần bảng phân tích được quản lý hơn. Cam kết chính xác phụ thuộc tổ hợp table format, catalog và engine.

Microsoft Fabric là ví dụ nền tảng phân tích quản lý kết hợp di chuyển, lưu trữ, biến đổi và trải nghiệm BI. Hãy đánh giá dịch vụ tích hợp phù hợp với identity, governance, khả năng chuyển đổi, quản lý capacity và công cụ hiện có ra sao; giao diện thống nhất không xóa ranh giới kiến trúc.

## File format và open table format

| Format | Hình dạng và cách dùng thường gặp | Hạn chế quan trọng |
|---|---|---|
| CSV | Trao đổi đơn giản, dễ xem | Kiểu, NULL, escaping và schema là quy ước bên ngoài |
| JSON | Payload API/event lồng nhau | Khóa lặp, record không đồng nhất làm tăng chi phí scan |
| Avro | Record dạng dòng, có schema | Không tối ưu cho truy vấn phân tích chỉ lấy vài cột |
| Parquet | Lưu cột, nén và pruning | File nhỏ, lệch dữ liệu, partition kém vẫn làm giảm hiệu năng |

**File format** mã hóa record. **Table format** theo dõi trạng thái bảng qua nhiều file, có thể hỗ trợ cập nhật metadata nguyên tử, snapshot, tiến hóa schema/partition và time travel. Apache Iceberg và Delta Lake là ví dụ phổ biến, khác nhau về triển khai, tích hợp catalog, hỗ trợ engine và vận hành. Kiểm tra tính năng cần thiết trên tổ hợp cụ thể, không giả định mọi engine hỗ trợ giống nhau.

Open table format có thể giảm phụ thuộc giữa storage và compute. Nó không bảo đảm chuyển đổi dễ dàng: catalog, quyền, kiểu dữ liệu, ngữ nghĩa transaction, job bảo trì và extension vẫn có thể riêng theo engine.

## DuckDB, Arrow và DataFusion

DuckDB là database phân tích nhúng, hữu ích cho khám phá cục bộ, script tái tạo được và truy vấn dữ liệu local/object store mà không vận hành server riêng. Nó không tự động thay thế warehouse nhiều người dùng; concurrency, governance, cô lập workload và nhu cầu triển khai quyết định mức phù hợp.

Apache Arrow định nghĩa biểu diễn cột trong bộ nhớ và nhóm interface tương tác. Mục tiêu là trao đổi dữ liệu hiệu quả giữa hệ thống, không phải tự quản lý bảng bền vững. Dữ liệu Arrow giảm serialize/copy khi các hệ thống tương thích chia sẻ cách biểu diễn.

DataFusion là query engine mở rộng dựa trên Arrow trong hệ Rust. Nó có thể nhúng để xây query service hoặc ứng dụng dữ liệu. Dùng framework engine đồng nghĩa nhóm sở hữu tích hợp, lựa chọn lập kế hoạch, bảo mật và vận hành mà warehouse quản lý có thể đã cung cấp.

## Modern, open và declarative stack

Modern data stack thường kết hợp ingestion, object storage/lakehouse, biến đổi, orchestration, catalog/governance, semantic serving và BI. Vẽ stack dưới dạng luồng dữ liệu và ranh giới ownership; nhóm công cụ có vùng giao nhau, không phải dự án nào cũng cần sản phẩm riêng cho từng tầng.

Open data stack ưu tiên format có thể tương tác và thành phần thay thế được. Tính di động phụ thuộc contract và implementation tương thích, không chỉ giấy phép mã nguồn mở. Declarative stack mô tả asset, dependency, check mong muốn để công cụ lập kế hoạch. Dù cấu hình declarative, vẫn cần xem plan sinh ra và side effect.

## Metrics layer và phục vụ phân tích

Metrics layer tập trung metric và ngữ nghĩa để dashboard, API, ứng dụng dùng chung định nghĩa. Cần nêu grain, filter, cơ sở thời gian, dimension, đơn vị và quy tắc aggregate. Metrics layer không giải quyết bất đồng nghiệp vụ: chủ metric cần thống nhất và duy trì ví dụ.

## Checklist quyết định hạ tầng

- Hệ thống nào là chuẩn, dữ liệu nào cần giữ để replay?
- Mục tiêu latency và concurrency nào thực sự cần cho người dùng?
- Cam kết transaction và tiến hóa schema ở mỗi tầng là gì?
- Engine cần dùng đọc/ghi được format qua catalog đã chọn không?
- Quyền, lineage, retention và xóa được cưỡng chế trên các bản sao ra sao?
- Compute, storage, egress, bảo trì và capacity nhàn rỗi tốn bao nhiêu?
- Ai vận hành nâng cấp, compaction, khôi phục và sự cố?

## Bài tập

Thiết kế hạ tầng cho nhà bán lẻ nhỏ có đơn hàng hằng ngày, danh mục sản phẩm, workflow analyst cục bộ và dịch vụ báo cáo có quản trị. Chọn nguồn OLTP, raw format, table format curated, query engine và BI. Nêu DuckDB có đủ cho trường hợp nào không và kiến trúc đổi ra sao nếu freshness đơn hàng từ hằng ngày xuống vài phút.

## Học tiếp

- [Lưu trữ, warehouse và table format](../data-engineering/storage-warehousing-and-formats.html)
- [Query engine và hiệu năng](../data-engineering/query-engines-and-performance.html)
- [Phục vụ dữ liệu phân tích và BI](../data-engineering/analytics-serving-and-bi.html)
- [Dự án 1: Kho dữ liệu phân tích cốt lõi](../../projects/project-1-analytics-warehouse.html)