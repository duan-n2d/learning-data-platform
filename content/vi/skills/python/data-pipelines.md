---
title: Python cho pipeline dữ liệu
description: Dùng Python cho extraction, kiểm định, tiện ích điều phối và tự động hóa.
order: 1
tags: [Python, pipeline]
---

# Python cho pipeline dữ liệu

Python thường kết nối các hệ thống: API, file, kiểm định, batch job và orchestration.

## Cấu trúc pipeline

Tách rõ các giai đoạn: lấy đầu vào, kiểm định, biến đổi, ghi đầu ra và báo cáo tổng kết lượt chạy. Tách hàm biến đổi thuần khỏi mã gọi mạng/file để kiểm thử logic nghiệp vụ mà không cần dịch vụ ngoài.

## Mẫu khởi đầu

```python
from pathlib import Path
import json

def read_json_files(folder: str):
    for path in Path(folder).glob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            yield json.load(f)
```

Với API phân trang, chỉ lưu cursor hoặc watermark sau khi dữ liệu tương ứng đã được ghi bền vững. Tôn trọng rate limit, đặt timeout kết nối/đọc, retry lỗi tạm thời bằng exponential backoff có giới hạn và dừng retry lỗi client cố định.

## Checklist độ tin cậy

- **Idempotency:** dùng khóa nguồn ổn định hoặc content hash để retry không tạo bản sao.
- **Checkpoint:** chỉ ghi tiến độ sau khi batch đã commit.
- **Kiểm định:** kiểm tra trường bắt buộc, kiểu, tính duy nhất của khóa và quy tắc miền ở biên dữ liệu.
- **Logging:** có run ID, nguồn, batch, số dòng, thời lượng và nhóm lỗi; tránh log bí mật hoặc payload nhạy cảm đầy đủ.
- **Xử lý lỗi:** phân biệt lỗi mạng có thể retry với dữ liệu sai và lỗi lập trình.
- **Giới hạn tài nguyên:** stream dữ liệu lớn, giới hạn concurrency, đóng file/response đúng cách.
- **Kiểm thử:** bao phủ đầu vào rỗng, record lỗi, input trùng, lỗi một phần và chạy lại.

## Ví dụ kiểm định nhỏ

```python
def validate_order(record: dict) -> None:
    required = {"order_id", "created_at", "currency", "amount"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if record["amount"] < 0:
        raise ValueError("amount must be non-negative")
```

Trong production, dùng model có kiểu hoặc thư viện schema khi hợp đồng lớn hơn. Giữ lỗi dễ hành động và tránh ép kiểu âm thầm làm đổi ý nghĩa.

## Tư duy production

Mã pipeline Python tốt cần logging, kiểm định, retry có giới hạn, test và thông báo lỗi rõ. Đồng thời cần tổng kết lượt chạy hữu ích: số dòng vào, được nhận, bị từ chối, vị trí đầu ra và watermark nguồn.

## Bài tập

Mở rộng trình đọc mẫu để đếm file lỗi mà không dừng cả batch, xuất tổng kết có cấu trúc và cho kết quả giống nhau khi chạy hai lần trên cùng đầu vào. Ghi rõ file lỗi sẽ bị bỏ qua, cách ly hay làm pipeline thất bại và lý do.