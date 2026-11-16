---
title: Mã hóa và quản lý khóa
description: Bảo vệ dữ liệu lakehouse khi lưu trữ và khi truyền, hiểu envelope encryption với KMS và xoay vòng khóa, và biết khi nào homomorphic encryption đáng với chi phí của nó.
order: 24
tags: [bảo mật, mã hóa, tls, kms, quản lý khóa, homomorphic encryption, parquet]
---

# Mã hóa và quản lý khóa

Mã hóa biến dữ liệu đọc được thành ciphertext mà chỉ người giữ đúng khóa mới đọc được. Nó giới hạn thiệt hại khi phương tiện lưu trữ, bản sao lưu hoặc lưu lượng mạng bị lộ, nhưng **không** quyết định ai được xem dữ liệu sau khi đã giải mã cho một truy vấn hợp lệ; đó là việc của [kiểm soát truy cập](access-control-rbac-rls-cls.html). Phần lớn sự cố thực tế liên quan tới khóa, chứng chỉ và quyền, chứ không phải thuật toán bị phá.

Giả định cho các ví dụ: object storage (Amazon S3 hoặc tương đương), một Iceberg REST catalog, engine Spark và Trino, một dịch vụ quản lý khóa trên cloud, và các client BI cùng Text2SQL kết nối qua mạng.

## Encryption at Rest

Mã hóa khi lưu trữ bảo vệ dữ liệu đã lưu (object storage, ổ đĩa, file database, bản sao lưu, snapshot) bằng cách giữ chúng ở dạng ciphertext trên phương tiện. Hệ thống hiện đại thường dùng AES-256, hay ở chế độ GCM, vốn còn phát hiện được giả mạo.

**Có thể áp dụng ở đâu.**

| Cấp | Ví dụ | Ai giữ khóa | Bảo vệ trước |
|---|---|---|---|
| Ổ đĩa / volume | Mã hóa block storage trên cloud | Nhà cung cấp hoặc KMS | Phương tiện bị đánh cắp hoặc thải bỏ |
| Object storage, phía server | SSE-S3, SSE-KMS | Khóa do nhà cung cấp quản lý hoặc khóa KMS của bạn | Lộ phương tiện; với khóa KMS, còn có thêm một key policy riêng chặn truy cập |
| Object storage, khóa do khách hàng cấp | SSE-C | Bạn cung cấp khóa theo từng request | Lo ngại về việc nhà cung cấp giữ khóa |
| Phía client / ứng dụng | Mã hóa trước khi upload; Parquet modular encryption | Ứng dụng của bạn và KMS | Quản trị viên storage và bất kỳ ai chỉ có quyền vào bucket |

*Modular encryption* của Parquet có thể mã hóa footer và từng cột bằng các khóa khác nhau, nên người đọc không có khóa của cột `email` vẫn đọc được các cột khác. Iceberg đang bổ sung tích hợp mã hóa cấp bảng với KMS; hãy kiểm tra mức hỗ trợ trong phiên bản engine của bạn trước khi dựa vào nó.

**Ví dụ (minh họa bucket policy bắt buộc mã hóa phía server bằng KMS):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyUnencryptedUploads",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::lake-prod/*",
    "Condition": {
      "StringNotEquals": { "s3:x-amz-server-side-encryption": "aws:kms" }
    }
  }]
}
```

S3 hiện mặc định mã hóa object mới bằng SSE-S3; policy như trên cưỡng chế lựa chọn mạnh hơn là khóa KMS do khách hàng quản lý, mà key policy của khóa đó tạo thêm một lớp chặn thứ hai.

**Lỗi thường gặp.** Tin rằng "mã hóa khi lưu trữ" chặn được người dùng có quyền đọc (dịch vụ storage giải mã cho mọi bên gọi được phép); file spill tạm, cache cục bộ và bản xuất notebook không được mã hóa; bản sao lưu được mã hóa bằng một khóa đã bị xóa, khiến không thể khôi phục.

**Kiểm chứng.** Kiểm kê bucket và volume cùng thiết lập mã hóa; liệt kê object thiếu khóa mong đợi; khôi phục một bản sao lưu trong môi trường thử để chứng minh khóa vẫn dùng được.

**Vị trí trong lakehouse / Text2SQL.** Mã hóa phía client cấp cột hữu ích cho các trường nhạy cảm nhất mà trợ lý không bao giờ được đọc; đảm bảo danh tính thực thi của trợ lý không được cấp quyền decrypt trên các khóa đó.

## Encryption in Transit

Mã hóa khi truyền bảo vệ dữ liệu khi di chuyển qua mạng, hầu như luôn dùng TLS (1.2 hoặc 1.3). TLS cung cấp tính bí mật, tính toàn vẹn, và thông qua việc xác minh chứng chỉ, đảm bảo client đang nói chuyện với đúng server. Mutual TLS (mTLS) còn xác thực client bằng chứng chỉ.

**TLS áp dụng ở đâu trong lakehouse.**

- Client (công cụ BI, notebook, trợ lý) tới query engine qua JDBC/ODBC/HTTPS.
- Engine tới catalog (Iceberg REST qua HTTPS) và tới object storage (endpoint HTTPS).
- Bên trong engine: lưu lượng coordinator tới worker và worker tới worker (ví dụ internal communication của Trino và thiết lập mã hóa RPC/shuffle của Spark), thường không được mã hóa mặc định.
- Pipeline tới nguồn (kết nối database, SFTP, API) và tới nhà cung cấp LLM hoặc embedding.

**Ví dụ (minh họa đoạn cấu hình):**

```json
{
  "Sid": "DenyInsecureTransport",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::lake-prod", "arn:aws:s3:::lake-prod/*"],
  "Condition": { "Bool": { "aws:SecureTransport": "false" } }
}
```

```text
# Kết nối nguồn PostgreSQL: mã hóa VÀ xác minh chứng chỉ server cùng hostname.
postgresql://ingest@orders-db.internal:5432/orders?sslmode=verify-full&sslrootcert=/etc/ssl/internal-ca.pem
```

**Lỗi thường gặp.** Bật TLS nhưng tắt xác minh chứng chỉ (`sslmode=require`, `verify=False`, "trust all certificates"), mở đường cho tấn công man-in-the-middle; chứng chỉ hết hạn gây sự cố và dẫn tới giải pháp tạm bợ thiếu an toàn; lưu lượng nội bộ cluster để ở dạng rõ vì cho rằng mạng đáng tin (xem [Zero Trust Architecture](security-posture-and-threat-modeling.html#zero-trust-architecture)).

**Kiểm chứng.** Quét endpoint để kiểm tra phiên bản TLS và hiệu lực chứng chỉ; tìm trong cấu hình các chỗ tắt xác minh; cảnh báo chứng chỉ sắp hết hạn trong 30 ngày; thử truy cập HTTP thường và xác nhận bị từ chối.

**Vị trí trong lakehouse / Text2SQL.** Trợ lý gửi câu hỏi, ngữ cảnh schema và đôi khi cả dòng kết quả tới endpoint mô hình; chặng đó phải dùng TLS có xác minh và nằm trong thỏa thuận với nhà cung cấp, giống như kết nối engine.

## Key Management Service (KMS)

Dịch vụ quản lý khóa tạo, lưu trữ và kiểm soát khóa mật mã, đồng thời thực hiện các thao tác mật mã để khóa chủ không bao giờ rời khỏi dịch vụ, thường được hỗ trợ bởi hardware security module (HSM). Ví dụ trên cloud gồm AWS KMS, Azure Key Vault và Google Cloud KMS; HashiCorp Vault là lựa chọn tự vận hành phổ biến.

**Envelope encryption hoạt động thế nào.**

1. **Key encryption key (KEK)**, còn gọi là khóa KMS hay khóa chủ, nằm yên trong KMS.
2. Để mã hóa một object hoặc file, dịch vụ yêu cầu KMS tạo một **data encryption key (DEK)** mới. KMS trả về DEK ở dạng rõ và cả dạng đã mã hóa bằng KEK.
3. Dữ liệu được mã hóa cục bộ bằng DEK dạng rõ, sau đó DEK dạng rõ bị hủy; DEK đã mã hóa được lưu cạnh dữ liệu (ví dụ trong metadata của object hoặc footer Parquet).
4. Để giải mã, bên đọc gửi DEK đã mã hóa tới KMS; KMS kiểm tra quyền của bên gọi, giải mã và trả về DEK.

Cách này giữ cho việc mã hóa khối lượng lớn nhanh và cục bộ, trong khi mọi lần giải mã vẫn được KMS phân quyền và ghi log.

**Ví dụ (minh họa đoạn key policy chỉ cấp decrypt cho vai trò pipeline và engine):**

```json
{
  "Sid": "AllowLakehouseUse",
  "Effect": "Allow",
  "Principal": { "AWS": [
    "arn:aws:iam::111122223333:role/pipeline-prod-writer",
    "arn:aws:iam::111122223333:role/trino-prod-workers"
  ]},
  "Action": ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*"
}
```

**Xoay vòng khóa và crypto-shredding.** Xoay vòng tự động tạo key material mới cho KEK nhưng vẫn giữ các phiên bản cũ để giải mã dữ liệu hiện có. Cố ý xóa một khóa chỉ dùng để mã hóa dữ liệu của một chủ thể hoặc một tenant sẽ khiến dữ liệu đó không thể đọc được (crypto-shredding), có thể hỗ trợ yêu cầu xóa, nhưng chỉ khi khóa được phân phạm vi hẹp như vậy và không còn bản sao dạng rõ ở nơi khác.

**Lỗi thường gặp.** Key policy cấp `kms:*` cho vai trò rộng; lên lịch xóa khóa do nhầm lẫn (dùng thời gian chờ xóa và cảnh báo); một khóa cho mọi môi trường, nên lộ ở dev là lộ cả prod; hạn mức request của KMS làm nghẽn job lớn; không giám sát lệnh decrypt.

**Kiểm chứng.** Rà soát key policy theo ma trận truy cập; cảnh báo sự kiện vô hiệu hóa hoặc xóa khóa; kiểm thử decrypt bị từ chối với vai trò không được phép; xem audit log của KMS để tìm khối lượng decrypt bất thường.

**Vị trí trong lakehouse / Text2SQL.** Tách khóa theo domain dữ liệu hoặc mức nhạy cảm cho phép chỉ cấp quyền decrypt cho đường thực thi của trợ lý trên những domain mà nó phục vụ.

## Homomorphic Encryption

Homomorphic encryption (HE) cho phép tính toán trên dữ liệu đã mã hóa: một bên không có khóa vẫn có thể cộng hoặc nhân các ciphertext, và kết quả sau khi giải mã bằng kết quả của cùng phép toán trên dữ liệu gốc.

**Các loại lược đồ.**

- **Đồng cấu một phần (partially homomorphic):** hỗ trợ không giới hạn một phép toán, ví dụ Paillier (cộng) hoặc RSA không padding (nhân).
- **Đồng cấu hạn chế / theo tầng (somewhat / levelled):** hỗ trợ cả hai phép toán tới một độ sâu giới hạn.
- **Đồng cấu hoàn toàn (FHE):** hỗ trợ tính toán tùy ý, lần đầu được Craig Gentry chứng minh năm 2009; các lược đồ hiện đại gồm BFV, BGV (số học số nguyên chính xác) và CKKS (số học xấp xỉ trên số thực). Thư viện gồm Microsoft SEAL và OpenFHE.

**Ví dụ (minh họa phép cộng tổng hợp với thư viện Python `phe` dùng Paillier):**

```python
from phe import paillier

public_key, private_key = paillier.generate_paillier_keypair()
# Mỗi chi nhánh mã hóa doanh thu trước khi gửi tới bộ tổng hợp chung.
encrypted = [public_key.encrypt(x) for x in (120_500, 98_200, 143_900)]
encrypted_total = sum(encrypted[1:], encrypted[0])   # bộ tổng hợp cộng ciphertext, không thấy giá trị
print(private_key.decrypt(encrypted_total))          # 362600, chỉ người giữ khóa đọc được
```

**Chi phí và sự phù hợp.** Phép toán FHE chậm hơn phép toán trên dữ liệu rõ nhiều bậc độ lớn, ciphertext lớn hơn nhiều, và chỉ một số phép tính là khả thi. Trong phân tích dữ liệu, đây là công cụ ngách cho một số phép tổng hợp liên bên hoặc suy luận riêng tư, không phải cách chạy một SQL warehouse tổng quát trên dữ liệu mã hóa. Các phương án nên đánh giá trước gồm môi trường thực thi tin cậy (confidential computing), tính toán đa bên an toàn, clean room và differential privacy.

**Lỗi thường gặp.** Rò rỉ thông tin qua việc truy vấn nào được chạy hoặc kích thước kết quả; chọn tham số không an toàn hoặc gây tràn số; cho rằng HE cũng xác thực được ai đã gửi dữ liệu.

**Kiểm chứng.** Dùng thư viện đã được rà soát với tham số khuyến nghị, đo hiệu năng trên khối lượng dữ liệu thực tế, và nhờ người có kinh nghiệm mật mã ứng dụng rà soát thiết kế.

**Vị trí trong lakehouse / Text2SQL.** Thường không nằm trên đường chính. Một trợ lý trên workflow HE chỉ có thể gọi các phép tính mã hóa đã định nghĩa trước, không thể sinh SQL tùy ý.

## Bài tập

1. Kiểm kê storage trong lab và ghi lại chế độ mã hóa khi lưu trữ cùng khóa cho từng bucket hoặc volume.
2. Thêm policy chặn truyền không an toàn và xác nhận request HTTP thất bại còn HTTPS thành công.
3. Đổi một kết nối nguồn từ `sslmode=require` sang `verify-full` và ghi lại CA bundle.
4. Vẽ luồng envelope encryption cho một file Parquet và chỉ ra nơi lưu DEK đã mã hóa.
5. Chạy ví dụ Paillier và đo thời gian 10.000 phép cộng mã hóa so với dữ liệu rõ.

### Tiêu chí hoàn thành

- Mọi vị trí lưu trữ có chế độ mã hóa và chủ sở hữu khóa được ghi rõ, và upload không mã hóa bị từ chối.
- Không client, engine hay kết nối pipeline nào tắt xác minh chứng chỉ.
- Key policy của KMS khớp ma trận truy cập, và các lệnh decrypt được ghi log và rà soát.
- Bạn giải thích được khi nào homomorphic encryption là hợp lý và những phương án đơn giản hơn nào bạn sẽ thử trước.
