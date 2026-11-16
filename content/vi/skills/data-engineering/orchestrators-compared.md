---
title: So sánh cron và các orchestrator
description: Biết khi nào cron là đủ, và so sánh Airflow, Dagster, Prefect, Mage trong việc lập lịch pipeline lakehouse và warehouse.
order: 43
tags: [điều phối, cron, Airflow, Dagster, Prefect, Mage, lập lịch]
---

# So sánh cron và các orchestrator

[Điều phối pipeline](orchestration.html) trình bày nguyên tắc: phụ thuộc, idempotency, retry, backfill. Trang này nói về công cụ. Nó bắt đầu với bộ lập lịch đơn giản nhất, giải thích chính xác nó thiếu gì, rồi so sánh bốn orchestrator trên cùng một pipeline nhỏ:

```text
extract_orders(day) -> validate_orders(day) -> build_marts(day) -> refresh_semantic_cache
```

Mỗi bước xử lý một ngày nghiệp vụ UTC và ghi theo kiểu idempotent (ghi đè partition), nên có thể retry hoặc backfill an toàn.

## Cron

**Là gì.** Cron là daemon Unix chạy lệnh theo lịch thời gian. Mỗi dòng trong crontab có năm trường thời gian, theo sau là lệnh:

```text
┌ phút (0-59)
│ ┌ giờ (0-23)
│ │ ┌ ngày trong tháng (1-31)
│ │ │ ┌ tháng (1-12)
│ │ │ │ ┌ thứ trong tuần (0-6, Chủ nhật = 0)
│ │ │ │ │
15 2 * * *  command
```

Cú pháp năm trường này được dùng lại ở nhiều hệ thống — Kubernetes CronJob, `schedule` của GitHub Actions, bộ lập lịch trên cloud và mọi orchestrator trong trang này — nên rất đáng học cho chính xác.

**Cách hoạt động.** Daemon cron thức dậy mỗi phút, kiểm tra mục nào khớp thời điểm hiện tại và khởi chạy lệnh tương ứng. Chỉ vậy thôi. Nó không biết lượt trước đã xong, thành công hay vẫn đang chạy; nó không retry; nó không biết `build_marts` phụ thuộc vào `extract_orders`.

**Ví dụ cụ thể (crontab minh họa).**

```bash
# Chạy theo UTC bất kể múi giờ cục bộ của máy chủ (cronie và một số bản khác hỗ trợ;
# nếu không, hãy đặt múi giờ hệ thống hoặc tính ngày bên trong script)
CRON_TZ=UTC
# 02:15 UTC hằng ngày; flock ngăn các lượt chạy chồng nhau; output ghi vào log theo ngày
15 2 * * * flock -n /tmp/orders.lock /opt/pipelines/run_orders.sh "$(date -u -d yesterday +\%F)" >> /var/log/orders/$(date -u +\%F).log 2>&1
```

Lưu ý ký tự `%` đã được escape: trong crontab, `%` không escape sẽ bị đổi thành ký tự xuống dòng.

**Kiểu lỗi.**

- *Chồng lượt*: một lượt chậm vẫn đang chạy khi lượt kế tiếp bắt đầu; không có khóa thì cả hai cùng ghi một partition.
- *Lỗi âm thầm*: exit code khác 0 nằm trong log không ai đọc, hoặc trong mail cục bộ.
- *Bỏ lỡ lượt chạy*: nếu máy tắt lúc 02:15, lượt đó đơn giản là không xảy ra (không chạy bù).
- *Múi giờ và DST*: lịch theo giờ địa phương chạy hai lần hoặc không chạy quanh thời điểm đổi giờ mùa hè.
- *Ngày trong tháng và thứ trong tuần*: khi cả hai đều bị giới hạn, đa số bản cron chạy khi *một trong hai* khớp, điều khiến nhiều người bất ngờ.
- *Phụ thuộc ẩn*: nối job theo giờ ("extract lúc 2:00, transform lúc 3:00") sẽ hỏng ngay lần đầu extract mất 61 phút.

**Kiểm định.** Kiểm tra biểu thức bằng công cụ in ra các thời điểm chạy kế tiếp; cho script trả exit code khác 0 khi lỗi và gửi tới cảnh báo; ghi heartbeat (ngày thành công gần nhất) để một bộ giám sát kiểm tra độ mới.

**Khi nào cron là đủ, khi nào orchestrator thắng.**

| Cron là ổn | Dùng orchestrator |
|---|---|
| Một job độc lập (ví dụ vacuum hoặc compaction hằng đêm) | Nhiều bước có phụ thuộc |
| Thỉnh thoảng lỡ một lượt là chấp nhận được | Lượt bị lỡ phải được phát hiện và chạy bù |
| Log trên một máy là đủ | Nhiều người cần lịch sử chạy, lineage và giao diện |
| Không có backfill | Backfill theo khoảng ngày với concurrency được kiểm soát |
| Không cần phản ứng khi dữ liệu đến | Kích hoạt theo sự kiện hoặc theo dữ liệu |

Lộ trình thực dụng: bắt đầu với cron cộng các chốt chặn ở trên cho một job, và chuyển sang orchestrator khi thêm bước phụ thuộc thứ hai.

## Bức tranh các orchestrator

**Airflow** (Apache) là orchestrator được triển khai rộng rãi nhất. Bạn định nghĩa DAG gồm các task bằng Python; scheduler kích hoạt lượt chạy theo data interval; executor chạy task trên worker, Celery hoặc pod Kubernetes. Nó có hệ sinh thái provider package rất lớn. Airflow 3 (phát hành 2025) làm lại nhiều phần, gồm đánh phiên bản DAG và đổi tên "dataset" thành "asset" cho lập lịch theo dữ liệu — hãy xác nhận nền tảng của bạn chạy phiên bản chính nào trước khi chép ví dụ.

**Dagster** hướng asset: bạn khai báo các dataset (asset) mà mã tạo ra, phụ thuộc, partition và check của chúng. Lịch sử chạy được tổ chức quanh asset, nên độ mới và lineage hiển thị sẵn.

Cả hai được trình bày ở mức khái niệm trong [Điều phối pipeline](orchestration.html). Hai công cụ dưới đây là lựa chọn mới hơn với trải nghiệm sử dụng khác.

## Prefect

**Là gì.** Prefect là orchestrator workflow Python mã nguồn mở (có dịch vụ cloud thương mại). Mục tiêu thiết kế là làm cho hàm Python thông thường có thể quan sát, retry và lập lịch với ít thủ tục nhất.

**Cách hoạt động.** Bạn gắn decorator `@flow` và `@task` cho hàm. Flow có thể gọi task và flow khác bằng luồng điều khiển Python bình thường — vòng lặp, điều kiện, fan-out động — thay vì khai báo trước một đồ thị tĩnh. Retry, timeout, cache và lưu kết quả được cấu hình trên decorator. Một **deployment** gắn lịch (cron, khoảng thời gian) hoặc trigger theo sự kiện cho flow; **work pool** và **worker** quyết định lượt chạy thực thi ở đâu (tiến trình cục bộ, Docker, Kubernetes, container serverless). Prefect cũng có hệ thống sự kiện và automation (ví dụ "nếu flow này lỗi hai lần, thông báo và tạm dừng").

**Ví dụ cụ thể (minh họa, kiểu Prefect 3).**

```python
from datetime import date, timedelta
from prefect import flow, task, get_run_logger

@task(retries=3, retry_delay_seconds=[10, 60, 300], timeout_seconds=900)
def extract_orders(day: date) -> str:
    # ghi s3://lake/raw/orders/dt=<day>/ theo kiểu ghi đè
    return f"s3://lake/raw/orders/dt={day}"

@task
def validate_orders(path: str) -> None:
    ...  # raise ValueError khi vi phạm hợp đồng: lỗi tất định nên không retry

@task(retries=1)
def build_marts(day: date) -> None:
    ...  # ví dụ dbt build --select marts --vars '{day: ...}'

@flow(log_prints=True)
def daily_orders(day: date | None = None) -> None:
    day = day or date.today() - timedelta(days=1)
    path = extract_orders(day)
    validate_orders(path)
    build_marts(day)
    get_run_logger().info("published %s", day)

if __name__ == "__main__":
    daily_orders.serve(name="daily-orders", cron="15 2 * * *")  # mặc định lập lịch theo UTC
```

**Kiểu lỗi.** Logic Python động khiến đồ thị khó suy luận; dựa vào kết quả trong bộ nhớ vốn mất khi worker khởi động lại (hãy lưu kết quả hoặc truyền tham chiếu tới lưu trữ bền vững); retry lỗi kiểm định vốn không bao giờ thành công; deployment trôi lệch khỏi mã trong Git.

**Kiểm định.** Unit test các hàm task như Python thuần; chạy flow cục bộ với một ngày fixture; kiểm tra rằng lỗi cưỡng bức trong `validate_orders` dừng flow mà không retry; giữ định nghĩa deployment (ví dụ `prefect.yaml`) trong version control.

## Mage

**Là gì.** Mage là công cụ pipeline dữ liệu mã nguồn mở (có bản Pro thương mại) kết hợp trình soạn thảo kiểu notebook trên trình duyệt với bộ lập lịch. Pipeline được dựng từ các **block** — data loader, transformer, data exporter, sensor và block SQL hoặc dbt — chạy tuần tự và truyền data frame cho nhau.

**Cách hoạt động.** Mỗi block là một file Python, SQL hoặc R trong thư mục dự án, được gắn decorator để khai báo vai trò, kèm các hàm `@test` tùy chọn chạy sau block. Bạn có thể chạy từng block tương tác và xem output, phù hợp cho khám phá. **Trigger** chạy pipeline theo lịch, theo sự kiện hoặc qua lời gọi API. Vì mặc định block truyền dữ liệu trong bộ nhớ, nó phù hợp nhất với dữ liệu nhỏ đến trung bình hoặc khi block đẩy việc tính toán xuống một engine.

**Ví dụ cụ thể (block transformer của Mage, minh họa).**

```python
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def keep_paid_orders(df, *args, **kwargs):
    paid = df[df["payment_status"] == "paid"].drop_duplicates("order_id")
    return paid

@test
def test_unique_and_non_negative(output, *args) -> None:
    assert output["order_id"].is_unique, "duplicate order_id"
    assert (output["amount_usd"] >= 0).all(), "negative amount"
```

**Kiểu lỗi.** Trạng thái tương tác kiểu notebook khác với một lượt chạy theo lịch sạch sẽ; data frame lớn truyền giữa các block làm cạn bộ nhớ; logic nghiệp vụ nằm trong giao diện công cụ thay vì trong mã đã review; ít tích hợp và cộng đồng nhỏ hơn Airflow.

**Kiểm định.** Chạy mọi pipeline từ đầu đến cuối từ trạng thái sạch trong CI; giữ test của block có ý nghĩa (tính duy nhất, khoảng giá trị, số dòng); kiểm tra rằng thư mục dự án, không phải giao diện, là nguồn sự thật trong Git.

## Đặt cạnh nhau

| | Airflow | Dagster | Prefect | Mage |
|---|---|---|---|---|
| Abstraction cốt lõi | DAG task theo data interval | Software-defined asset | Flow và task Python | Block trong pipeline |
| Định nghĩa đồ thị | Tĩnh (có dynamic mapping) | Phụ thuộc giữa asset | Động, Python lúc chạy | Block có thứ tự, kiểu notebook |
| Backfill | Có sẵn, theo data interval | Nhận biết partition | Qua lượt chạy có tham số | Có hỗ trợ, ít trọng tâm hơn |
| Nhận biết dữ liệu | Asset (Airflow 3), sensor | Gốc (độ mới, check, lineage) | Sự kiện và automation | Test của block, sensor |
| Thế mạnh điển hình | Hệ sinh thái, độ chín, dễ tuyển người | Lineage asset và chất lượng | Python ít thủ tục | Dựng nhanh, tương tác |
| Rủi ro điển hình | Phức tạp vận hành, task mọc tràn lan | Phải học mô hình asset | Đồ thị khó rõ khi quá động | Quy mô và kỷ luật production |

**Cách chọn.** Liệt kê điều bắt buộc — kiểu backfill, nhận biết dữ liệu, đích triển khai (Kubernetes, dịch vụ managed), kỹ năng đội, hệ sinh thái sẵn có — và dựng cùng pipeline ba bước ở hai ứng viên hàng đầu. Đo thời gian để thêm một check thất bại, chạy backfill bảy ngày và tìm ra vì sao một lượt chạy lỗi. Năng lực sản phẩm thay đổi nhanh; hãy kiểm tra tài liệu hiện hành thay vì dựa vào bảng so sánh, kể cả bảng này.

## Liên hệ với trợ lý phân tích có quản trị

Trợ lý chỉ đáng tin bằng dữ liệu được chứng nhận mới nhất của nó. Dù chọn orchestrator nào, hãy cho nó công bố trạng thái máy đọc được — "`fct_orders` đầy đủ đến 2026-11-16, các check đạt" — để trợ lý đọc trước khi trả lời. Nếu lượt chạy gần nhất lỗi hoặc trễ, trợ lý nên nói rõ ("dữ liệu cập nhật đến 2026-11-15") thay vì âm thầm trả lời từ bảng cũ. Làm mới cache của semantic layer nên là bước cuối của pipeline, không phải một job riêng chạy theo giờ.

## Bài tập

1. Lập lịch `run_orders.sh` bằng cron, có khóa, xử lý UTC, exit code khi lỗi và file heartbeat. Cho nó lỗi một lần và xác nhận bạn sẽ phát hiện được.
2. Hiện thực cùng pipeline bốn bước bằng hai trong số Airflow, Dagster, Prefect hoặc Mage (đều chạy được cục bộ hoặc trong Docker).
3. Ở mỗi công cụ, mô phỏng lỗi tạm thời trong `extract_orders` (retry thành công) và lỗi hợp đồng trong `validate_orders` (không retry, thông báo lỗi rõ).
4. Backfill từ 2026-11-01 đến 2026-11-07 với tối đa hai ngày chạy đồng thời và xác nhận partition không bị nhân đôi.
5. Xuất một file hoặc bảng trạng thái độ mới ở cuối mỗi lượt chạy.

**Tiêu chí hoàn thành.**

- Thiết lập cron có cơ chế phát hiện lỗi được tài liệu hóa, và lý do bằng văn bản cho việc vượt ra ngoài cron.
- Hai hiện thực chạy được với retry, một lỗi kiểm định không retry và một backfill thành công.
- Số dòng mỗi partition giống hệt nhau sau khi chạy backfill hai lần.
- Quyết định chọn công cụ một trang kèm thời gian đo được cho ba việc ở trên.
