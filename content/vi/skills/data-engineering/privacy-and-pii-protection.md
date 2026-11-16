---
title: Quyền riêng tư và bảo vệ PII
description: Tìm và bảo vệ dữ liệu cá nhân, đáp ứng nghĩa vụ GDPR và CCPA kể cả xóa thật sự trong Iceberg, và chọn giữa tokenization, anonymization và differential privacy.
order: 23
tags: [quyền riêng tư, pii, gdpr, ccpa, tokenization, anonymization, differential privacy, iceberg]
---

# Quyền riêng tư và bảo vệ PII

Quyền riêng tư là việc sử dụng dữ liệu cá nhân hợp pháp, cho mục đích đã nêu, không thu thập nhiều hơn và không lưu lâu hơn mức cần thiết, đồng thời tôn trọng quyền của những người mà dữ liệu mô tả. Kiểm soát bảo mật (truy cập, mã hóa) là cần thiết cho quyền riêng tư nhưng chưa đủ: một bảng được bảo mật hoàn hảo vẫn có thể bị dùng cho mục đích mà không ai đồng ý.

Trang này là hướng dẫn kỹ thuật, **không phải tư vấn pháp lý**. Luật khác nhau theo khu vực pháp lý và thay đổi theo thời gian; hãy xác nhận nghĩa vụ với team quyền riêng tư hoặc pháp chế. Giả định cho các ví dụ: lakehouse Iceberg với các lớp raw, staging và mart, Spark cho các thủ tục bảo trì, và một trợ lý Text2SQL trên các mart đã tuyển chọn.

## PII

Thông tin nhận dạng cá nhân (PII) là mọi dữ liệu có thể nhận diện một người cụ thể, trực tiếp (tên, email, số định danh quốc gia, số điện thoại) hoặc gián tiếp khi kết hợp với dữ liệu khác (mã bưu chính + ngày sinh + giới tính, ID thiết bị, vị trí chính xác, ghi chú dạng văn bản tự do). GDPR dùng khái niệm rộng hơn là *dữ liệu cá nhân (personal data)*, bao gồm cả định danh trực tuyến và ID bí danh có thể liên kết ngược tới một người.

**Cách tìm.** Kết hợp (1) phân loại do producer khai báo trong contract, (2) quét tự động tên cột, mẫu giá trị và nội dung mẫu, và (3) rà soát trường văn bản tự do, payload JSON, log và file nơi PII hay ẩn nấp. Ghi kết quả thành tag trong catalog để chính sách có thể gắn vào (xem [Data Classification](governance-and-data-products.html#data-classification)).

**Ví dụ (minh họa câu quét giá trị giống email trong cột không ngờ tới):**

```sql
select 'support_tickets.body' as location, count(*) as hits
from staging.support_tickets
where regexp_like(body, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}');
```

**Cách xóa thật sự trong Iceberg.** Một lệnh `DELETE` trong Iceberg tạo snapshot mới; các snapshot cũ vẫn tham chiếu tới file dữ liệu chứa dòng đã xóa, nên time travel vẫn đọc được chúng. Với merge-on-read, các dòng còn nằm vật lý trong file dữ liệu cho tới khi compaction. Vì vậy một lần xóa hoàn chỉnh cần nhiều bước:

```sql
-- 1. Xóa logic (Spark SQL).
delete from lake.crm.customers where customer_id = 'C-1042';
delete from lake.analytics.fct_orders where customer_id = 'C-1042';

-- 2. Ghi lại file dữ liệu để áp dụng các delete file của merge-on-read.
call lake.system.rewrite_data_files(table => 'crm.customers', options => map('delete-file-threshold', '1'));

-- 3. Expire các snapshot còn tham chiếu tới file cũ (tuân theo chính sách lưu giữ của bạn).
call lake.system.expire_snapshots(table => 'crm.customers', older_than => timestamp '2026-11-17 00:00:00', retain_last => 1);

-- 4. Xóa các file không còn được metadata nào tham chiếu.
call lake.system.remove_orphan_files(table => 'crm.customers');
```

Sau đó xử lý các bản sao bên ngoài bảng: file landing raw, bản sao lưu, extract downstream, cache, search index và vector index, và log. Chỉ mang tính minh họa; hãy kiểm tra tùy chọn thủ tục cho phiên bản Iceberg của bạn và thử trên bản sao trước.

**Lỗi thường gặp.** PII trong văn bản tự do hoặc JSON mà công cụ quét tên cột bỏ sót; xóa ở mart nhưng không xóa ở file raw; lưu snapshot 90 ngày âm thầm giữ lại dữ liệu đã xóa; PII bị gửi tới LLM bên ngoài trong prompt hoặc lưu trong log của trợ lý.

**Kiểm chứng.** Sau một lần xóa, tìm định danh của chủ thể trong mọi lớp và index, bao gồm time travel về snapshot cũ nhất còn giữ, và lưu lại bằng chứng.

**Vị trí trong lakehouse / Text2SQL.** Giữ PII ngoài ngữ cảnh schema mặc định của trợ lý và ngoài log prompt; điều hướng câu hỏi cần dữ liệu cá nhân sang một đường đã được duyệt và có audit.

## Data Privacy

Quyền riêng tư dữ liệu là kỷ luật xử lý dữ liệu cá nhân theo quyền của cá nhân và nghĩa vụ pháp lý của tổ chức: có cơ sở pháp lý hoặc sự đồng ý để xử lý, giới hạn mục đích, tối thiểu hóa dữ liệu, chính xác, giới hạn lưu trữ, bảo mật và minh bạch.

**Cách vận hành theo góc nhìn kỹ thuật.**

| Nguyên tắc | Biện pháp kỹ thuật |
|---|---|
| Giới hạn mục đích | Ghi mục đích cho từng dataset; hạn chế truy cập theo mục đích, không chỉ theo team |
| Tối thiểu hóa | Không nạp cột mà không use case nào cần; bỏ hoặc hash định danh sớm |
| Giới hạn lưu trữ | Retention job cho từng bảng và lớp, gồm cả expire snapshot |
| Xử lý quyền | Chỉ mục chủ thể tìm kiếm được, workflow xóa và xuất dữ liệu, bằng chứng |
| Minh bạch | Catalog ghi lại dữ liệu cá nhân nào tồn tại và vì sao |

**Ví dụ (minh họa bản ghi quyền riêng tư của dataset):**

```yaml
dataset: crm.customers
personal_data: [name, email, phone, address]
purpose: [order fulfilment, customer support]
lawful_basis: contract
retention: 3 years after last order, then delete
subject_key: customer_id
processors: [email-service-vendor]
```

**Lỗi thường gặp.** Tái sử dụng cho phân tích với mục đích mới mà không rà soát; khóa chủ thể không nhất quán giữa các hệ thống nên không đáp ứng yêu cầu đầy đủ được; cấu hình lưu giữ trong warehouse nhưng không trên object storage.

**Kiểm chứng.** Với một chủ thể thử nghiệm, chạy yêu cầu truy cập và xóa từ đầu đến cuối, đo mức đầy đủ và thời gian.

## Data Privacy by Design

Privacy by design nghĩa là xây dựng biện pháp bảo vệ quyền riêng tư vào hệ thống ngay từ quyết định thiết kế đầu tiên thay vì bổ sung sau khi ra mắt. Khung của Ann Cavoukian mô tả bảy nguyên tắc, và Điều 25 GDPR biến "data protection by design and by default" thành nghĩa vụ pháp lý tại EU.

Bảy nguyên tắc, chuyển thành thực hành trên nền tảng dữ liệu:

1. **Chủ động, không bị động:** đưa bước rà soát quyền riêng tư vào tài liệu thiết kế cho pipeline mới.
2. **Quyền riêng tư là thiết lập mặc định:** cột mới bị hạn chế cho tới khi được phân loại; người dùng mới không có quyền vào dữ liệu cá nhân.
3. **Quyền riêng tư gắn vào thiết kế:** đặt bí danh (pseudonymise) ngay khi ingestion; xây đường xóa trước khi ra mắt.
4. **Đầy đủ chức năng (cùng có lợi):** cung cấp mart tổng hợp hoặc đã tokenize để phân tích vẫn hoạt động mà không cần định danh thô.
5. **Bảo mật đầu-cuối:** bảo vệ dữ liệu suốt vòng đời, từ thu thập tới xóa, gồm cả bản sao lưu.
6. **Hiển thị và minh bạch:** ghi lại việc xử lý trong catalog và giúp nó audit được.
7. **Tôn trọng quyền riêng tư của người dùng:** thực hiện đồng ý và lựa chọn của họ nhanh chóng và đầy đủ.

**Ví dụ (minh họa mục checklist thiết kế trong template PR của pipeline):**

```markdown
- [ ] New personal data fields listed and classified
- [ ] Purpose and lawful basis recorded in the dataset privacy record
- [ ] Default access: restricted; masking policy attached
- [ ] Deletion path tested for one subject across raw, staging, mart, index
```

**Lỗi thường gặp.** Checklist được tick mà không có bằng chứng; "mặc định hạn chế" bị phá vỡ bởi grant cấp schema; rà soát quyền riêng tư sau khi dữ liệu đã chảy.

**Kiểm chứng.** Audit một mẫu pipeline gần đây để tìm bằng chứng cho checklist.

## GDPR

Quy định chung về bảo vệ dữ liệu (GDPR) là luật của Liên minh châu Âu điều chỉnh việc xử lý dữ liệu cá nhân của người ở EU (và EEA). Luật áp dụng cho tổ chức thành lập tại EU và cho tổ chức bên ngoài cung cấp hàng hóa, dịch vụ cho, hoặc giám sát hành vi của, người ở EU.

**Yêu cầu đối với nền tảng dữ liệu, trên thực tế:**

- Cơ sở pháp lý cho từng mục đích xử lý (như đồng ý, hợp đồng, nghĩa vụ pháp lý hoặc lợi ích hợp pháp).
- Quyền của chủ thể dữ liệu: truy cập, sửa, xóa ("quyền được lãng quên"), hạn chế, chuyển dữ liệu và phản đối, thường phải đáp ứng trong vòng một tháng.
- Đánh giá tác động bảo vệ dữ liệu (DPIA) cho xử lý rủi ro cao, có thể gồm profiling quy mô lớn hoặc các use case AI.
- Hồ sơ hoạt động xử lý, hợp đồng với bên xử lý, và thông báo vi phạm cho cơ quan giám sát không chậm trễ quá mức và, nếu khả thi, trong vòng 72 giờ.
- Quy tắc chuyển dữ liệu cá nhân ra ngoài EEA, ảnh hưởng tới vị trí đặt bucket, bản sao và AI provider (data residency).
- Mức phạt có thể tới 20 triệu EUR hoặc 4% doanh thu toàn cầu hằng năm, tùy giá trị nào cao hơn, cho các vi phạm nghiêm trọng nhất.

**Ví dụ (minh họa log yêu cầu xóa):**

```json
{
  "request_id": "DSR-2026-0815",
  "type": "erasure",
  "subject_key": "C-1042",
  "received_at": "2026-11-02T09:14:00Z",
  "systems": {
    "crm.customers": "deleted+expired 2026-11-05",
    "analytics.fct_orders": "deleted+expired 2026-11-05",
    "raw/crm/": "files rewritten 2026-11-05",
    "vector_index.support_docs": "chunks removed 2026-11-06",
    "backups": "expire by 2026-12-05 per backup policy"
  },
  "verified_by": "privacy-ops",
  "completed_at": "2026-11-06T16:30:00Z"
}
```

**Lỗi thường gặp.** Coi dữ liệu đã đặt bí danh là ngoài phạm vi (nó vẫn là dữ liệu cá nhân); bản sao hoặc xử lý AI ở khu vực không có cơ chế bảo vệ cho việc chuyển dữ liệu; xóa nhưng bỏ sót snapshot hoặc bản sao lưu.

**Vị trí trong lakehouse / Text2SQL.** Dùng quy trình xóa trong phần [PII](#pii), partition hoặc bucket theo khu vực khi cần data residency, và xác nhận nơi nhà cung cấp mô hình của trợ lý xử lý prompt.

## CCPA

Đạo luật Quyền riêng tư Người tiêu dùng California (CCPA), được sửa đổi bởi Đạo luật Quyền Riêng tư California (CPRA), trao cho cư dân California các quyền đối với thông tin cá nhân mà doanh nghiệp nắm giữ, nếu doanh nghiệp vượt ngưỡng về doanh thu hoặc khối lượng dữ liệu. Luật được thực thi bởi Cơ quan Bảo vệ Quyền riêng tư California và Tổng chưởng lý bang.

**Các quyền chính của người tiêu dùng:** được biết thông tin cá nhân nào được thu thập và được dùng, chia sẻ ra sao; được xóa; được sửa; được từ chối (opt out) việc *bán* hoặc *chia sẻ* (cho quảng cáo hành vi xuyên ngữ cảnh) thông tin cá nhân; được giới hạn việc sử dụng thông tin cá nhân nhạy cảm; và không bị phân biệt đối xử khi thực hiện các quyền này.

**So sánh với GDPR.** CCPA chủ yếu là mô hình opt-out cho việc bán và chia sẻ, trong khi GDPR yêu cầu cơ sở pháp lý trước khi xử lý. Định nghĩa, thời hạn và ngoại lệ khác nhau, nên cần cùng các năng lực nền tảng (chỉ mục chủ thể, xóa, xuất, cờ opt-out) nhưng cấu hình theo từng luật.

**Ví dụ (minh họa cưỡng chế opt-out trong mart cấp dữ liệu cho đối tác quảng cáo):**

```sql
create or replace view exports.ad_partner_audience as
select c.hashed_email, c.segment
from analytics.dim_customer c
left join privacy.consumer_preferences p on c.customer_id = p.customer_id
where coalesce(p.opt_out_sale_share, false) = false;
-- Nhiều công ty áp dụng opt-out cho mọi khách hàng, không chỉ cư dân California,
-- vì dữ liệu nơi cư trú không đáng tin cậy. Hãy quyết định điều này cùng team quyền riêng tư.
```

**Lỗi thường gặp.** Cờ opt-out được lưu nhưng không được join vào mọi bản xuất; coi "email đã hash" là không phải dữ liệu cá nhân dù nó được chia sẻ để khớp người dùng; yêu cầu xóa không được chuyển tới nhà cung cấp dịch vụ.

**Kiểm chứng.** Cho một người tiêu dùng thử nghiệm opt-out và xác nhận họ biến mất khỏi mọi bản xuất bán hoặc chia sẻ ở lần chạy kế tiếp.

## Data Tokenization

Tokenization thay một giá trị nhạy cảm (số thẻ, số định danh, email) bằng một token thay thế không mang ý nghĩa khai thác được. Ánh xạ giữa token và bản gốc được giữ trong một **token vault** riêng, được kiểm soát chặt, hoặc được suy ra bằng khóa trong các phương án *vaultless* như mã hóa giữ định dạng (ví dụ NIST FF1).

**Cách hoạt động.** Khi ingestion, dịch vụ tokenization nhận giá trị và trả về token. Token tất định (cùng đầu vào, cùng token) cho phép join và đếm giữa các bảng mà không lộ giá trị; token ngẫu nhiên an toàn hơn nhưng làm mất khả năng join. Detokenization là một đặc quyền riêng, có audit, chỉ cấp cho rất ít danh tính.

**Ví dụ (minh họa):**

| Email gốc | Token lưu trong lakehouse |
|---|---|
| maria@example.com | `tok_em_7Q2XK9` |
| tuan@example.com | `tok_em_P4R1ZB` |

```sql
-- Analyst đếm được số khách hàng phân biệt và join theo token mà không thấy email.
select count(distinct email_token) from analytics.fct_orders where order_date >= date '2026-11-01';
```

**So sánh với mã hóa và masking.** Giá trị đã mã hóa có thể được giải mã bởi bất kỳ ai có khóa; token chỉ có thể đảo ngược qua dịch vụ vault. Masking thường tạo giá trị không thể đảo ngược và không nhằm mục đích join.

**Lỗi thường gặp.** Vault trở thành điểm lỗi duy nhất hoặc mục tiêu giá trị cao; token tất định cho phép liên kết giữa các dataset lẽ ra phải tách biệt (dùng miền token khác nhau cho từng mục đích); giá trị gốc lọt vào log trước khi được tokenize.

**Kiểm chứng.** Xác nhận giá trị thô không bao giờ xuất hiện trong storage landing hoặc log; kiểm thử rằng detokenization bị từ chối với vai trò analyst và được audit với vai trò được duyệt.

**Vị trí trong lakehouse / Text2SQL.** Định danh đã tokenize cho phép trợ lý trả lời "có bao nhiêu khách hàng phân biệt" mà mô hình không bao giờ thấy dữ liệu cá nhân.

## Data Anonymization

Data anonymization biến đổi dữ liệu sao cho không còn nhận diện được cá nhân bằng bất kỳ phương tiện nào có khả năng hợp lý được sử dụng, dù trực tiếp hay bằng cách liên kết với dữ liệu khác. Dữ liệu được ẩn danh đúng cách nằm ngoài phạm vi GDPR; dữ liệu **đặt bí danh (pseudonymised)** (token, hash, ID đã che) thì không.

**Kỹ thuật.**

- **Tổng quát hóa:** thay giá trị chính xác bằng khoảng (tuổi 34 -> 30-39; mã bưu chính -> vùng).
- **Loại bỏ:** bỏ bản ghi hoặc giá trị hiếm có thể làm lộ riêng một người.
- **Thêm nhiễu / xáo trộn:** thay đổi nhẹ giá trị nhưng giữ mẫu tổng hợp.
- **Tổng hợp:** chỉ công bố thống kê cấp nhóm trên một kích thước nhóm tối thiểu.
- **k-anonymity:** mọi tổ hợp quasi-identifier xuất hiện ở ít nhất *k* bản ghi; các mở rộng như l-diversity và t-closeness bảo vệ thêm thuộc tính nhạy cảm trong mỗi nhóm.

**Ví dụ (minh họa kiểm tra k-anonymity, k = 10):**

```sql
select age_band, region, gender, count(*) as group_size
from published.customer_profile_anon
group by age_band, region, gender
having count(*) < 10;     -- kỳ vọng 0 dòng trước khi phát hành
```

**Lỗi thường gặp.** Cho rằng bỏ tên là đã ẩn danh; phát hành nhiều bảng ẩn danh chồng lấn có thể kết hợp để tái nhận diện; nhóm nhỏ trong dashboard có bộ lọc (lọc một tổ hợp hiếm hiển thị đúng một người).

**Kiểm chứng.** Chạy kiểm tra k-anonymity ở mọi lần phát hành và thử tấn công liên kết bằng một dataset phụ trợ công khai trong một buổi rà soát có kiểm soát.

**Vị trí trong lakehouse / Text2SQL.** Cưỡng chế kích thước nhóm tối thiểu trong semantic layer: trợ lý nên từ chối hoặc ẩn kết quả khi bất kỳ nhóm nào dưới ngưỡng.

## Differential Privacy

Differential privacy (DP) là một đảm bảo toán học rằng kết quả phân tích thay đổi rất ít dù dữ liệu của một cá nhân bất kỳ có được đưa vào hay không. Điều này đạt được bằng cách thêm nhiễu ngẫu nhiên được hiệu chỉnh cẩn thận vào kết quả.

**Cách hoạt động.** Tham số quyền riêng tư **epsilon (ε)** giới hạn mức một người có thể ảnh hưởng tới kết quả; ε càng nhỏ thì quyền riêng tư càng mạnh và nhiễu càng nhiều. Với truy vấn đếm, thêm hoặc bớt một người làm kết quả thật thay đổi tối đa 1 (*độ nhạy - sensitivity*), nên cơ chế Laplace thêm nhiễu lấy từ Laplace(0, 1/ε). Mỗi truy vấn tiêu tốn một phần **ngân sách quyền riêng tư (privacy budget)**; theo nguyên lý kết hợp cơ bản, các epsilon cộng dồn, nên phải giới hạn số truy vấn lặp lại.

**Ví dụ (minh họa Python, chưa đạt mức production):**

```python
import numpy as np

def dp_count(true_count: int, epsilon: float, rng=np.random.default_rng()) -> float:
    sensitivity = 1.0
    return true_count + rng.laplace(loc=0.0, scale=sensitivity / epsilon)

budget = 1.0
for eps in (0.25, 0.25, 0.5):      # ba truy vấn tiêu hết ngân sách
    budget -= eps
    print(round(dp_count(1240, eps)), "remaining budget:", budget)
```

Trên thực tế, hãy dùng thư viện đã được kiểm chứng (ví dụ OpenDP hoặc các thư viện differential privacy của Google); bản tự cài đặt thường có lỗi về số thực dấu phẩy động và kết hợp ngân sách.

**Lỗi thường gặp.** Truy vấn lặp không giới hạn khiến nhiễu bị trung bình hóa mất; chọn ε không có lý do; trình bày kết quả có nhiễu như số chính xác; nhóm nhỏ nơi nhiễu lấn át tín hiệu.

**Kiểm chứng.** Theo dõi ngân sách theo dataset và consumer; kiểm thử rằng truy vấn bị từ chối khi hết ngân sách; báo cáo mức nhiễu kèm kết quả.

**Vị trí trong lakehouse / Text2SQL.** DP phù hợp cho thống kê công bố và chia sẻ dữ liệu ra bên ngoài hơn là báo cáo vận hành nội bộ. Nếu trợ lý phục vụ kết quả DP, nó phải nói rõ giá trị có nhiễu và là xấp xỉ.

## Bài tập

1. Quét lớp staging để tìm PII trong cột văn bản tự do và JSON; gắn tag mọi phát hiện trong catalog.
2. Viết bản ghi quyền riêng tư (mục đích, cơ sở pháp lý, lưu giữ, khóa chủ thể) cho hai dataset.
3. Thực hiện xóa hoàn toàn một chủ thể thử nghiệm trong bảng Iceberg, gồm compaction, expire snapshot và xóa file mồ côi, và chứng minh time travel không còn trả về các dòng đó.
4. Thay email bằng token tất định trong một mart; xác nhận số đếm phân biệt khớp với bản gốc.
5. Công bố một bảng tổng hợp vượt qua kiểm tra k = 10, và tính một DP count với ε = 0.5 để so sánh.

### Tiêu chí hoàn thành

- Mọi cột chứa dữ liệu cá nhân đều có tag, có mục đích và có quy tắc lưu giữ.
- Một yêu cầu xóa có thể được thực hiện và có bằng chứng trên raw, mart, snapshot và index trong thời gian mục tiêu.
- Trợ lý không thể trả về định danh hoặc nhóm dưới kích thước tối thiểu, và log của nó không chứa PII thô.
- Bạn giải thích được vì sao dữ liệu đã tokenize vẫn là dữ liệu cá nhân còn dữ liệu đã ẩn danh đúng cách thì không.
