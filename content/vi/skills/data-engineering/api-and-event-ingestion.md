---
title: Ingestion từ API và sự kiện
description: Kéo dữ liệu từ REST và GraphQL API, nhận webhook an toàn, và hiểu event sourcing như một nguồn lịch sử phân tích.
order: 34
tags: [ingestion, API, REST, GraphQL, webhook, event sourcing, pagination, rate limits]
---

# Ingestion từ API và sự kiện

Nhiều nguồn không phải database mà bạn đọc trực tiếp được: chúng là sản phẩm SaaS và service nội bộ cung cấp API hoặc đẩy event. Bài này bao gồm việc kéo (REST, GraphQL), được đẩy tới (webhook), và một mẫu thiết kế phía nguồn, event sourcing, làm thay đổi ý nghĩa của "lịch sử".

Giả định: một CRM SaaS có REST API và webhook, một service GraphQL nội bộ, và vùng nạp raw trên Iceberg hoặc warehouse. Endpoint, header và payload chỉ mang tính **minh họa**.

## REST API

**Là gì.** REST API là giao diện web cung cấp các *tài nguyên* (khách hàng, đơn hàng) tại các URL và thao tác với chúng bằng phương thức HTTP tiêu chuẩn. REST là phong cách kiến trúc với các ràng buộc như tách client-server, không trạng thái (mỗi request mang đủ thông tin cần thiết, kể cả xác thực), có thể cache và giao diện đồng nhất.

**Cách hoạt động khi ingestion.** Bạn chủ yếu dùng `GET` trên endpoint tập hợp và theo quy ước của API về:

- **Xác thực:** API key, token OAuth 2.0 hết hạn và cần làm mới.
- **Phân trang:** offset/limit (đơn giản nhưng không ổn định khi dữ liệu thay đổi trong lúc phân trang), số trang, hoặc cursor (token mờ cho trang kế tiếp; ổn định và được ưu tiên).
- **Lọc:** tham số kiểu `updated_since` cho tải incremental.
- **Mã trạng thái:** `200` thành công, `4xx` lỗi phía client (`401` xác thực, `404` không tồn tại, `429` bị giới hạn tốc độ), `5xx` lỗi phía server.

```http
GET /v1/contacts?updated_since=2026-11-16T00:00:00Z&limit=100&cursor=eyJpZCI6MTIzfQ HTTP/1.1
Authorization: Bearer <token>
Accept: application/json

HTTP/1.1 200 OK
X-RateLimit-Remaining: 42
{"data": [...], "next_cursor": "eyJpZCI6MjIzfQ"}
```

**Điểm yếu với dữ liệu khối lớn.** Mỗi request một tập record, giới hạn kích thước trang và giới hạn tốc độ khiến tải toàn bộ lịch sử rất chậm. Nhiều API có endpoint bulk export (job bất đồng bộ sinh ra file); ưu tiên dùng chúng cho backfill.

**Kiểu lỗi.** Phân trang offset bỏ sót hoặc nhân đôi dòng khi có record mới được chèn trong lúc tải; bộ lọc `updated_since` với độ chính xác theo giây bỏ sót record cập nhật trong cùng giây ở ranh giới; record đã xóa không bao giờ xuất hiện trong endpoint danh sách; đổi phiên bản API làm thay đổi kiểu dữ liệu của trường.

## GraphQL

**Là gì.** GraphQL là ngôn ngữ truy vấn và runtime mã nguồn mở cho API. Client gửi truy vấn tới một endpoint duy nhất và nhận đúng những trường đã yêu cầu, có hình dạng giống truy vấn, được kiểm tra theo schema có kiểu.

**Cách hoạt động khi ingestion.**

```graphql
query Orders($after: String, $since: DateTime!) {
  orders(first: 100, after: $after, filter: {updatedAt: {gte: $since}}) {
    pageInfo { hasNextPage endCursor }
    edges { node { id status totalCents updatedAt customer { id } } }
  }
}
```

Lặp khi `pageInfo.hasNextPage` còn true, truyền `endCursor` vào `after`. Nhiều GraphQL API theo quy ước "connections" dựa trên cursor này.

**Đánh đổi.** Chỉ lấy trường cần thiết và đối tượng liên quan trong một request giúp giảm over-fetching. Nhưng giới hạn tốc độ thường dựa trên *chi phí truy vấn* (điểm theo trường và kích thước trang) thay vì số request, truy vấn lồng sâu có thể đắt hoặc bị từ chối, và lỗi thường được trả về với HTTP `200` trong mảng `errors` cùng `data` không đầy đủ.

**Kiểu lỗi.** Xem HTTP 200 là thành công và nạp dữ liệu thiếu; trường bị deprecate rồi bị xóa; danh sách lồng trong một node bị cắt âm thầm ở giới hạn trang riêng của nó (ví dụ chỉ 10 line item đầu tiên).

## API Integration

**Là gì.** API integration là việc kết nối các hệ thống qua API của chúng. Với đội dữ liệu, đó là xây và vận hành việc trích xuất đáng tin cậy từ API vào lakehouse, bao gồm xác thực, phân trang, giới hạn, trạng thái incremental và xử lý schema.

**Cách xây (checklist).**

1. **Thông tin xác thực:** lưu secret trong secret manager; dùng phạm vi quyền tối thiểu; lên kế hoạch làm mới và xoay vòng token.
2. **Trạng thái incremental:** lưu cursor hoặc high-water mark *sau khi* dữ liệu đã được ghi bền vững, không bao giờ trước đó.
3. **Giới hạn tốc độ:** tôn trọng `429` và `Retry-After`; dùng exponential backoff có jitter; giới hạn mức song song.
4. **Idempotency:** nạp phản hồi raw cùng khóa record ổn định và metadata request (endpoint, tham số, thời điểm lấy), rồi khử trùng phía sau.
5. **Delete:** dùng endpoint record đã xóa, webhook, hoặc đối soát định kỳ toàn bộ khóa.
6. **Giữ raw:** giữ JSON raw (hoặc bảng raw có kiểu) để thay đổi logic parse có thể replay mà không gọi lại API.

```python
# Minh họa vòng retry tôn trọng giới hạn tốc độ.
import random, time, requests

def get_with_backoff(session, url, params, max_attempts=6):
    for attempt in range(max_attempts):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = float(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait + random.uniform(0, 1))
            continue
        resp.raise_for_status()  # 4xx khác 429 phải lỗi rõ ràng, không retry
        return resp.json()
    raise RuntimeError(f"gave up after {max_attempts} attempts: {url}")
```

Các thư viện và công cụ như dlt, Airbyte và Fivetran hiện thực phần lớn những điều này (xem [công cụ ingestion managed và mã nguồn mở](managed-and-open-ingestion-tools.html)); checklist vẫn là cách bạn đánh giá chúng.

**Kiểm định.** So sánh số lượng cho một khoảng đã đóng với UI hoặc API báo cáo của nhà cung cấp; kiểm tra khóa trùng; cảnh báo khi một nguồn vốn thay đổi hằng ngày lại nạp 0 dòng.

## Webhook

**Là gì.** Webhook là HTTP callback: khi có sự kiện ở hệ thống nguồn, nó gửi HTTP `POST` kèm payload event tới URL bạn đã đăng ký. Webhook đảo chiều API từ kéo sang đẩy.

**Cách hoạt động.**

1. Bạn đăng ký một endpoint và các loại event muốn nhận.
2. Nhà cung cấp gửi event, thường được ký bằng secret chung (ví dụ header chữ ký HMAC-SHA256) và kèm event ID và timestamp.
3. Endpoint của bạn xác minh chữ ký, lưu event raw bền vững (queue hoặc object storage) và trả `2xx` nhanh. Việc xử lý diễn ra bất đồng bộ.
4. Nếu bạn không trả `2xx` kịp, nhà cung cấp retry với backoff trong một khoảng giới hạn, sau đó có thể vô hiệu hóa endpoint.

```python
# Minh họa receiver: xác minh, lưu, xác nhận. Không xử lý trực tiếp tại đây.
import hashlib, hmac

def handle(request, secret: bytes, queue):
    body = request.body  # byte raw, trước khi parse JSON
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get("X-Signature", "")):
        return 401
    queue.send(body, dedupe_id=request.headers["X-Event-Id"])
    return 200
```

**Kiểu lỗi.** Webhook thường là *at-least-once* và *không có thứ tự*: cùng một event có thể đến hai lần, và `updated` có thể đến trước `created`. Endpoint ngừng hoạt động lâu hơn khoảng retry sẽ mất event. Xử lý đồng bộ chậm gây timeout và bão retry. Thiếu kiểm tra chữ ký hoặc dung sai timestamp cho phép request giả mạo hoặc phát lại.

**Kiểm định và khôi phục.** Khử trùng theo event ID; áp dụng cập nhật theo version hoặc timestamp nguồn, không theo thứ tự đến; chạy đối soát API (kéo) định kỳ để bắt event bị lỡ; dùng API replay hoặc danh sách event của nhà cung cấp sau sự cố.

## Event Sourcing

**Là gì.** Event sourcing là mẫu thiết kế ứng dụng trong đó hệ thống ghi nhận chuẩn là một log append-only của các domain event (`OrderPlaced`, `ItemAdded`, `OrderPaid`) thay vì các dòng có thể sửa. Trạng thái hiện tại được suy ra bằng cách replay (fold) các event của một thực thể.

**Cách hoạt động.** Command được kiểm tra với trạng thái hiện tại và, nếu được chấp nhận, sinh event mới ghi nối vào stream của thực thể với số version tăng dần. Read model (*projection*) được xây bằng cách tiêu thụ event, thường đi cùng CQRS (tách model ghi và model đọc). Snapshot lưu trạng thái tại một version để tránh replay stream dài.

```python
# Minh họa fold: trạng thái là hàm của các event có thứ tự.
def apply(state, event):
    match event["type"]:
        case "OrderPlaced": return {"status": "placed", "total": 0}
        case "ItemAdded":   return {**state, "total": state["total"] + event["price_cents"]}
        case "OrderPaid":   return {**state, "status": "paid"}
    return state
```

**Event sourcing so với CDC.** CDC capture tác động mức dòng của transaction lên bảng (`status` đổi từ `pending` sang `paid`). Event sourcing ghi lại *ý định và ý nghĩa* (`OrderPaid` kèm phương thức thanh toán). Với phân tích, hệ thống event-sourced là nguồn lịch sử tuyệt vời, nhưng event của nó là model nội bộ: hãy công bố integration event đã chọn lọc hoặc một hợp đồng thay vì lộ mọi loại event nội bộ.

**Kiểu lỗi.** Schema event tiến hóa qua nhiều năm, nên event cũ cần upcasting hoặc handler theo version; projection dựng lại bằng mã đã đổi cho ra số khác trước; xóa dữ liệu cá nhân khỏi log bất biến cần có kế hoạch (crypto-shredding hoặc lưu PII riêng); replay một stream lớn có thể mất hàng giờ.

**Kiểm định.** Dựng lại projection từ đầu trong môi trường thử và so sánh với projection đang chạy; kiểm tra chuỗi version của từng stream không bị đứt quãng.

## Bài tập

1. Viết extractor incremental cho một REST API phân trang (hoặc mock cục bộ) dùng phân trang cursor, tôn trọng `429` với `Retry-After`, và chỉ lưu cursor sau khi ghi thành công. Kill giữa chừng và chứng minh nó tiếp tục mà không thiếu hay trùng.
2. Viết cùng phần trích xuất đó với một GraphQL endpoint dùng truy vấn kiểu connections. Làm loader thất bại khi phản hồi chứa `errors`, kể cả khi HTTP 200.
3. Xây webhook receiver xác minh chữ ký HMAC, lưu event raw và khử trùng theo event ID. Gửi cùng một event hai lần và một event `updated` trước `created`; chứng minh trạng thái cuối cùng đúng.
4. Mô hình hóa một stream đơn hàng event-sourced nhỏ, xây projection, đổi logic projection, dựng lại và giải thích sự khác biệt.

## Tiêu chí hoàn thành

- Extractor API của bạn xử lý xác thực, phân trang, giới hạn tốc độ, trạng thái incremental và delete, và bạn giải thích được từng lựa chọn.
- Loader xem phản hồi thiếu hoặc có lỗi là thất bại và giữ payload raw để replay.
- Đường webhook được xác minh, idempotent, chịu được sai thứ tự và có đối soát bằng kéo dữ liệu.
- Bạn giải thích được khi nào event từ event sourcing, event CDC và snapshot API cho đúng loại lịch sử cần thiết.
