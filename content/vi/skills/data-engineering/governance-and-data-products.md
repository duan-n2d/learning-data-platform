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

Một bảng chưa tự động là Data Product. Không gắn nhãn "product" nếu thiếu consumer, contract được duy trì và đường hỗ trợ.

## So sánh Data Contract, Data Product, Data Mesh và Governance

Bốn thuật ngữ này mô tả các lớp liên quan nhưng ở "độ cao" khác nhau, và thường bị dùng lẫn lộn như từ đồng nghĩa. Thực ra không phải vậy:

- **Data contract (hợp đồng dữ liệu)** - trả lời "cái gì": một thỏa thuận kỹ thuật cụ thể về schema, ngữ nghĩa và SLA (freshness, chất lượng, chính sách thay đổi) giữa một producer và các consumer của nó. Xem [Chất lượng dữ liệu và hợp đồng](data-quality-contracts.html).
- **Data product (sản phẩm dữ liệu)** - trả lời "vì sao/cho ai": một tập dữ liệu được đối xử như sản phẩm, có chủ sở hữu cụ thể, tài liệu và tiêu chuẩn chất lượng, thường được hiện thực qua một hoặc nhiều data contract (bảng "Hợp đồng Data Product" ở trên).
- **Data mesh** - một mẫu hình tổ chức và kiến trúc: các team domain sở hữu data product của mình từ đầu đến cuối, dưới các tiêu chuẩn governance liên bang (federated) do trung tâm đặt ra. Data product và contract đứng sau nó là những khối xây dựng mà một mesh được lắp từ đó, không phải điều kiện bắt buộc để dùng riêng từng thuật ngữ.
- **Data governance (quản trị dữ liệu)** - lớp chính sách và tuân thủ bao trùm (chủ sở hữu, phân loại, truy cập, lưu giữ) mà contract và product vận hành bên trong, dù có mesh hay không.

**Một tranh luận thật sự, chưa phải sự thật đã chốt.** Một số người thực hành cho rằng "data contract" phần lớn chỉ đóng gói lại những ý tưởng mà schema evolution (xem [Nền tảng event streaming](event-streaming-platforms.html)) và công cụ chất lượng dữ liệu đã bao phủ từ trước, dưới một cái tên mới dễ bán hơn, và điều thực sự mới chỉ là về mặt tổ chức: đặt tên một chủ sở hữu hướng tới consumer và một SLA, chứ không phải cơ chế thực thi. Hãy giữ sự hoài nghi đó khi đánh giá tuyên bố của vendor hay một quy trình nội bộ mới - hỏi xem năng lực nào thực sự mới so với chỉ là đổi tên.

## Dữ liệu chủ và tham chiếu

Dữ liệu chủ biểu diễn entity cốt lõi như khách hàng, sản phẩm, nhà cung cấp được chia sẻ giữa hệ thống. Dữ liệu tham chiếu là danh sách kiểm soát như mã quốc gia, trạng thái vòng đời hoặc tiền tệ. Định nghĩa nguồn có thẩm quyền, định danh, quy tắc match/merge và xử lý xung đột. Giữ khóa nguồn và lịch sử để hợp nhất không xóa provenance.

Quy trình master data tập trung có thể tăng tính nhất quán nhưng thêm độ trễ và overhead governance. Bắt đầu từ vấn đề liên hệ giữa các hệ thống và quyền sở hữu cần thiết, không mặc định phải cài công cụ MDM.

## Data Stewardship

Data stewardship giao cho những người cụ thể trách nhiệm hằng ngày về ý nghĩa, chất lượng và việc sử dụng đúng đắn dữ liệu trong một domain. **Owner** ra quyết định (một trường có nghĩa gì, ai được truy cập, khi nào breaking change được chấp nhận); **steward** giữ cho các quyết định đó chính xác và hiển thị rõ: duy trì thuật ngữ glossary và mô tả, rà soát phân loại, cùng producer phân loại xử lý sự cố chất lượng, và trả lời câu hỏi của consumer. Người giám hộ kỹ thuật (platform engineer hoặc data engineer) vận hành các hệ thống cưỡng chế những quyết định đó.

**Cách hoạt động.** Steward được giao theo domain hoặc data product, không theo công cụ. Trong data mesh, mỗi team domain có steward riêng, còn một nhóm governance trung tâm đặt tiêu chuẩn chung (mức phân loại, quy ước đặt tên, metadata bắt buộc) và audit chúng. Công việc stewardship chảy qua các hàng đợi: dataset mới cần mô tả và phân loại, sự cố chất lượng cần phân loại xử lý, yêu cầu truy cập cần rà soát, và định nghĩa cần đối chiếu.

**Ví dụ (minh họa bảng RACI stewardship cho domain khách hàng):**

| Hoạt động | Owner | Steward | Platform engineer | Consumer |
|---|---|---|---|---|
| Duyệt định nghĩa "khách hàng active" | A | R | I | C |
| Phân loại cột mới | A | R | C | I |
| Phân loại xử lý check chất lượng thất bại | I | A | R | I |
| Duyệt truy cập cột PII | A | R | I (triển khai) | I |
| Ngừng dùng một bảng | A | R | R | C |

R = thực hiện (responsible), A = chịu trách nhiệm cuối (accountable), C = được tham vấn (consulted), I = được thông báo (informed).

**Lỗi thường gặp.** Stewardship là việc phụ không có nguồn lực nên hàng đợi phình to; một steward trung tâm cho mọi domain; steward không có thẩm quyền chặn một định nghĩa sai; mục catalog bị bất kỳ ai sửa mà không có rà soát.

**Kiểm chứng.** Mọi tài sản certified có steward cụ thể vẫn còn làm trong domain đó; theo dõi tuổi hàng đợi và tỷ lệ tài sản có mô tả, phân loại còn cập nhật.

**Vị trí trong lakehouse / Text2SQL.** Steward duyệt mô tả, từ đồng nghĩa và ví dụ mà trợ lý sử dụng. Đối xử với thay đổi ngữ cảnh đó như thay đổi mã, có steward rà soát. Xem [Metadata Catalog, khám phá dữ liệu và lineage](metadata-catalogs-and-lineage.html) về công cụ.

## Data Classification

Phân loại dữ liệu là quá trình nhận diện dữ liệu và gắn nhãn theo mức nhạy cảm và yêu cầu xử lý để các biện pháp kiểm soát phù hợp được áp dụng tự động. Nhãn chỉ hữu ích khi mỗi mức ánh xạ tới quy tắc cụ thể.

**Ví dụ (minh họa lược đồ phân loại):**

| Mức | Ví dụ | Xử lý mặc định |
|---|---|---|
| Public | Danh mục sản phẩm đã công bố | Không hạn chế |
| Internal | Số đơn hàng, chỉ số vận hành không chứa dữ liệu cá nhân | Nhân viên có nhu cầu công việc |
| Confidential | Định danh khách hàng, doanh thu theo khách hàng, hợp đồng | Truy cập theo vai trò, masking ngoài vai trò được duyệt, mã hóa khi lưu trữ |
| Restricted | Số định danh quốc gia, dữ liệu thanh toán, dữ liệu sức khỏe, credential | Cột được tokenize hoặc mã hóa, người duyệt cụ thể, truy cập được ghi log và rà soát |

**Cách hoạt động.** Producer khai báo phân loại trong contract; bộ quét tự động đề xuất tag cho cột mới từ tên và mẫu giá trị; steward xác nhận hoặc sửa. Tag được lưu trong catalog và, nếu được hỗ trợ, lan truyền qua lineage tới cột phái sinh. Chính sách theo tag (masking, row filter, lưu giữ) sau đó gắn vào tag thay vì vào từng bảng.

```yaml
# Minh họa tag cột trong contract của model
columns:
  - name: email
    tags: [classification.confidential, pii.email]
  - name: national_id
    tags: [classification.restricted, pii.government_id]
  - name: country
    tags: [classification.internal]
```

**Lỗi thường gặp.** Cột chưa phân loại mặc định bị coi là public (hãy để "chưa phân loại" được xử lý như confidential); phân loại bảng nhưng bỏ qua cột văn bản tự do bên trong; tag không lan sang bảng phái sinh, extract hoặc vector index; tin bộ quét mà không rà soát.

**Kiểm chứng.** Báo cáo tỷ lệ cột đã phân loại theo từng lớp; cho CI fail khi cột mart mới thiếu phân loại; lấy mẫu bảng phái sinh để xác nhận tag đã được kế thừa.

**Vị trí trong lakehouse / Text2SQL.** Dùng phân loại để lọc ngữ cảnh schema và allow-list của trợ lý: mặc định chỉ cột `public` và `internal`, các cột khác chỉ khi vai trò của người dùng cuối cho phép. Kỹ thuật bảo vệ quyền riêng tư cho các mức cao hơn được trình bày trong [Quyền riêng tư và bảo vệ PII](privacy-and-pii-protection.html), còn việc cưỡng chế trong [Kiểm soát truy cập](access-control-rbac-rls-cls.html).

## Biến chính sách thành thực thi

Chuyển chính sách thành phân loại catalog, quyền warehouse, masking, retention job, schema check và quy tắc duyệt CI. Kiểm thử cả truy cập được phép lẫn bị từ chối. Với dữ liệu nhạy cảm, kiểm tra bản sao đi đâu, log nào chứa giá trị, AI provider nào nhận prompt và thao tác xóa lan tới bảng/index phát sinh ra sao.

## Bài liên quan

- [Metadata Catalog, khám phá dữ liệu và lineage](metadata-catalogs-and-lineage.html)
- [Công cụ chất lượng dữ liệu và observability](data-quality-tooling-and-observability.html)
- [Kiểm soát truy cập: RBAC, bảo mật cấp dòng và cấp cột](access-control-rbac-rls-cls.html)
- [Quyền riêng tư và bảo vệ PII](privacy-and-pii-protection.html)
- [Mã hóa và quản lý khóa](encryption-and-key-management.html)
- [Tư thế bảo mật và mô hình hóa mối đe dọa](security-posture-and-threat-modeling.html)

## Bài tập

Chọn dataset khách hàng dùng bởi dashboard và dịch vụ Text2SQL. Định nghĩa product owner, steward, grain, contract chất lượng/freshness, phân loại, vai trò truy cập, lineage, chính sách breaking change và đường deprecation. Thêm một ví dụ chính sách được cưỡng chế tự động và một ví dụ vẫn cần người duyệt.