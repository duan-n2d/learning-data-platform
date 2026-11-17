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

## Notebook: từ khám phá đến một bước pipeline

Notebook là nơi hợp lý để khám phá dữ liệu, nhưng nếu không quản lý sẽ sinh ra **notebook sprawl**: mỗi analyst hay engineer giữ một bản sao logic khám phá tương tự trong notebook riêng, trùng lặp và dần trôi lệch khỏi nhau, không có một nguồn sự thật chung cho phiên bản "đúng" của một phép biến đổi. Triệu chứng thường thấy là nhiều notebook gần giống nhau cùng giải một bài toán theo cách hơi khác nhau, không ai sở hữu hay test, và không thể biết notebook nào đã tạo ra một kết quả cụ thể.

**Papermill** là cơ chế cụ thể để biến một notebook thành một bước pipeline production có thể tái sử dụng, thay vì để nó là một artifact thủ công dùng một lần. Nó tham số hóa notebook bằng cách tiêm giá trị vào một cell được gắn tag `parameters`, thực thi notebook theo chương trình từ dòng lệnh hoặc từ mã, rồi lưu một notebook đầu ra mới chứa kết quả của lượt chạy cùng với các cell gốc. Notebook đầu ra đó chính là bản ghi của lượt chạy: đầu vào, mã và kết quả hiển thị cùng nhau, có thể kiểm tra lại sau.

```bash
papermill analysis.ipynb runs/analysis_2026-11-17.ipynb -p run_date 2026-11-17 -p min_amount 0
```

Vì một notebook đã tham số hóa và thực thi theo chương trình chỉ là một lệnh khác có đầu vào/đầu ra, một orchestrator như Dagster hay Airflow có thể chạy nó như một bước trong pipeline theo lịch — với cùng cơ chế retry, logging và theo dõi phụ thuộc như bất kỳ task nào khác — thay vì trông chờ ai đó mở và chạy lại nó bằng tay.

**Kiểu lỗi.** Coi notebook phát triển tương tác là sẵn sàng production mà không dọn trạng thái ẩn (biến còn sót từ lúc khám phá thủ công, không tồn tại khi chạy mới); bỏ qua kiểm định bên trong notebook vì "chạy không lỗi" không đồng nghĩa kết quả đúng; để notebook đầu ra chất đống không quản lý, tái tạo lại notebook sprawl ở một lớp khác.

**Kiểm định.** Thực thi notebook từ trạng thái sạch (không còn kernel state cũ) như một phần của việc kiểm tra trước khi lập lịch; assert trên giá trị đầu ra của chính notebook, không chỉ exit code; giữ notebook đã tham số hóa và test của nó trong version control như mọi mã pipeline khác, và xem notebook đầu ra là artifact của lượt chạy, không phải nguồn sự thật.

## Bài tập

Mở rộng trình đọc mẫu để đếm file lỗi mà không dừng cả batch, xuất tổng kết có cấu trúc và cho kết quả giống nhau khi chạy hai lần trên cùng đầu vào. Ghi rõ file lỗi sẽ bị bỏ qua, cách ly hay làm pipeline thất bại và lý do.