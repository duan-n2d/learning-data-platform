---
title: Window Function trong SQL
description: Học xếp hạng, tổng lũy kế, lag/lead và các mẫu SQL phân tích.
order: 1
tags: [SQL, phân tích]
---

# Window Function trong SQL

Window function tính giá trị trên một tập dòng có liên quan mà vẫn giữ chi tiết từng dòng. Khác `GROUP BY`, nó không gộp các dòng thành một dòng mỗi nhóm.

## Mô hình tư duy

Window function tính trên tập dòng liên quan với dòng hiện tại. `PARTITION BY` xác định nhóm, `ORDER BY` xác định thứ tự, còn frame xác định những dòng nào trong thứ tự đó được dùng.

## Tổng lũy kế

```sql
select
  customer_id,
  order_date,
  revenue,
  sum(revenue) over (
    partition by customer_id
    order by order_date
  ) as running_revenue
from fact_orders;
```

## Xếp hạng và chọn dòng mới nhất có tính tất định

```sql
with ranked_events as (
  select
    customer_id,
    event_id,
    event_time,
    row_number() over (
      partition by customer_id
      order by event_time desc, event_id desc
    ) as row_num
  from customer_events
)
select customer_id, event_id, event_time
from ranked_events
where row_num = 1;
```

Khóa sắp xếp thứ hai giúp kết quả tất định khi trùng thời điểm. Dùng `row_number` khi chỉ chọn đúng một dòng; `rank` khi dòng đồng hạng cùng thứ hạng và bỏ số tiếp theo; `dense_rank` khi đồng hạng nhưng không bỏ số.

## Ranh giới frame rất quan trọng

Với tổng lũy kế, hãy ghi rõ frame nếu dialect SQL hỗ trợ:

```sql
sum(revenue) over (
  partition by customer_id
  order by order_date, order_id
  rows between unbounded preceding and current row
) as running_revenue
```

Phép tổng hợp có `ORDER BY` có thể dùng frame mặc định bao gồm các dòng đồng hạng. `ROWS` đếm dòng vật lý; `RANGE` gom các dòng có cùng giá trị sắp xếp. Khóa phân xử duy nhất và frame tường minh giúp tránh bước nhảy ngoài dự kiến.

## Phát hiện thay đổi với lag và lead

```sql
select
  account_id,
  snapshot_date,
  balance,
  lag(balance) over (
    partition by account_id order by snapshot_date
  ) as prior_balance,
  balance - lag(balance) over (
    partition by account_id order by snapshot_date
  ) as balance_change
from daily_account_balances;
```

Quyết định ý nghĩa dòng đầu tiên khi chưa có giá trị trước đó. Mặc định `lag` trả `NULL`; thay bằng zero chỉ đúng nếu zero thực sự là mốc nghiệp vụ.

## Vì sao cần hiểu window function?

Phần lớn công việc analytics engineering phụ thuộc vào grain, partition, thứ tự và logic metric nghiệp vụ.

## Bài tập

Với bảng có một dòng trên mỗi dòng hàng của đơn, viết truy vấn trả đơn đầu tiên, đơn mới nhất và doanh thu thuần lũy kế của từng khách hàng. Kiểm thử khách có một đơn, hai đơn cùng timestamp, một khoản hoàn tiền và doanh thu NULL. Xác định kết quả kỳ vọng trước khi chạy truy vấn.