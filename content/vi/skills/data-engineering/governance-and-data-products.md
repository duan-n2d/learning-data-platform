---
title: Quản trị dữ liệu và Data Product
description: Vận hành hóa quyền sở hữu, ý nghĩa, chất lượng, quyền truy cập và chính sách thay đổi.
order: 8
tags: [governance, catalog, lineage, data product]
---

# Quản trị dữ liệu và Data Product

Quản trị dữ liệu là tập hợp quyền quyết định, trách nhiệm và kiểm soát để dữ liệu dễ hiểu và được sử dụng đúng mục đích. Governance có hiệu lực khi chính sách đi vào hệ thống và workflow tạo/tiêu thụ dữ liệu, không chỉ nằm trong tài liệu.

## Trách nhiệm quản trị

- **Ownership:** chủ sở hữu nghiệp vụ hoặc kỹ thuật chịu trách nhiệm định nghĩa, kỳ vọng chất lượng và quyết định thay đổi.
- **Stewardship:** người quản lý dữ liệu duy trì thuật ngữ, phân loại và ngữ cảnh sự cố cùng chuyên gia domain.
- **Quyền truy cập:** danh tính được duyệt nhận quyền tối thiểu cho mục đích xác định.
- **Riêng tư và lưu giữ:** trường nhạy cảm có quy tắc xử lý, thời hạn lưu và hành vi xóa.
- **Chất lượng và contract:** producer/consumer thống nhất schema, ý nghĩa, freshness và cách xử lý thay đổi phá vỡ.
- **Vòng đời:** dataset có mục đích, trạng thái hỗ trợ, kỳ vọng khôi phục và lộ trình ngừng dùng.

Quyết định governance cần truy vết được: ai duyệt định nghĩa, chính sách đổi khi nào và hệ thống nào thực thi.

## Catalog và lineage

Data catalog giúp người dùng tìm và đánh giá dataset. Metadata hữu ích gồm định nghĩa nghiệp vụ, chủ sở hữu, domain, phân loại, nguồn, nhịp cập nhật, trạng thái chất lượng, lineage và hạn chế đã biết. Tự động thu thập metadata khi có thể, đồng thời cung cấp đường liên hệ chủ sở hữu để sửa mục cũ/mơ hồ.

Lineage nối nguồn, phép biến đổi và consumer. Nó hỗ trợ phân tích tác động trước khi đổi schema và tìm nguyên nhân metric sai lệch. Phân biệt lineage kỹ thuật suy ra từ mã với lineage nghiệp vụ giải thích vì sao biến đổi tồn tại.

## Hợp đồng Data Product

Data product là giao diện được hỗ trợ cho nhu cầu consumer xác định, có chủ sở hữu và kỳ vọng rõ.

| Trường hợp đồng | Cần chỉ rõ |
|---|---|
| Mục đích và người dùng | Hỗ trợ quyết định hoặc workflow nào? |
| Schema và ngữ nghĩa | Mỗi trường có nghĩa gì, grain nào? |
| Chất lượng và freshness | Check và mục tiêu phân phối nào được cam kết? |
| Giao diện | Bảng, file, event stream, API hay semantic model |
| Truy cập và riêng tư | Danh tính và phân loại dữ liệu nào áp dụng? |
| Chính sách thay đổi | Xử lý thêm mới, breaking change và deprecation ra sao? |
| Hỗ trợ | Chủ sở hữu, đường sự cố và kỳ vọng khôi phục |

Một bảng chưa tự động là Data Product. Không gắn nhãn “product” nếu thiếu consumer, contract được duy trì và đường hỗ trợ.

## Dữ liệu chủ và tham chiếu

Dữ liệu chủ biểu diễn entity cốt lõi như khách hàng, sản phẩm, nhà cung cấp được chia sẻ giữa hệ thống. Dữ liệu tham chiếu là danh sách kiểm soát như mã quốc gia, trạng thái vòng đời hoặc tiền tệ. Định nghĩa nguồn có thẩm quyền, định danh, quy tắc match/merge và xử lý xung đột. Giữ khóa nguồn và lịch sử để hợp nhất không xóa provenance.

Quy trình master data tập trung có thể tăng tính nhất quán nhưng thêm độ trễ và overhead governance. Bắt đầu từ vấn đề liên hệ giữa các hệ thống và quyền sở hữu cần thiết, không mặc định phải cài công cụ MDM.

## Biến chính sách thành thực thi

Chuyển chính sách thành phân loại catalog, quyền warehouse, masking, retention job, schema check và quy tắc duyệt CI. Kiểm thử cả truy cập được phép lẫn bị từ chối. Với dữ liệu nhạy cảm, kiểm tra bản sao đi đâu, log nào chứa giá trị, AI provider nào nhận prompt và thao tác xóa lan tới bảng/index phát sinh ra sao.

## Bài tập

Chọn dataset khách hàng dùng bởi dashboard và dịch vụ Text2SQL. Định nghĩa product owner, steward, grain, contract chất lượng/freshness, phân loại, vai trò truy cập, lineage, chính sách breaking change và đường deprecation. Thêm một ví dụ chính sách được cưỡng chế tự động và một ví dụ vẫn cần người duyệt.