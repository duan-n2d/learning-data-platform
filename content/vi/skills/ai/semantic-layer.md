---
title: Lớp ngữ nghĩa
description: Kiểm soát logic nghiệp vụ để người và LLM truy vấn metric nhất quán.
order: 1
tags: [lớp ngữ nghĩa, metric, Text2SQL]
---

# Lớp ngữ nghĩa

Lớp ngữ nghĩa định nghĩa entity, dimension, metric và quan hệ nghiệp vụ đáng tin cậy.

## Mô hình hóa hợp đồng nghiệp vụ

Bắt đầu từ câu hỏi mọi người thực sự đặt. Với mỗi measure, ghi ý nghĩa nghiệp vụ, chủ sở hữu, model nguồn, grain, bộ lọc, cơ sở thời gian, đơn vị, cách xử lý tiền tệ và tính cộng gộp. Với mỗi dimension, định nghĩa giá trị hợp lệ và quan hệ với entity. Khai báo đường join rõ ràng; từ chối đường mơ hồ thay vì để người dùng tự đoán.

## Vì sao quan trọng với LLM?

LLM có thể sinh SQL nhưng cần ngữ cảnh được kiểm soát. Không có lớp ngữ nghĩa, model có thể chọn sai bảng, sai đường join hoặc sai định nghĩa metric.

## Ví dụ định nghĩa metric

```yaml
metrics:
  total_revenue:
    type: sum
    expression: revenue_amount
    entity: order
    filters:
      - payment_status = 'paid'
```

Ví dụ này cố ý chưa đủ cho production. Định nghĩa hữu ích còn cần chính sách quy đổi tiền tệ, ngày báo cáo, cách xử lý hoàn tiền, chủ sở hữu nguồn và ví dụ đã kiểm thử. Ưu tiên định nghĩa thực thi trong framework ngữ nghĩa được duyệt thay cho glossary chỉ nằm trong prompt.

## Grain và tính cộng gộp

Giả sử `fct_order_lines` có một dòng trên mỗi dòng hàng. `net_revenue` có thể cộng theo dòng nếu tiền tệ và quy tắc hoàn tiền nhất quán. `distinct_customers` không cộng được giữa các ngày vì khách quay lại sẽ bị đếm lặp. Gắn nhãn metric không cộng được hoặc bán cộng được và định nghĩa cách tổng hợp hợp lệ.

## Quản lý thay đổi

- Gán chủ sở hữu cho từng metric và quy trình duyệt thay đổi định nghĩa.
- Quản lý định nghĩa trong version control, liên kết thay đổi với báo cáo/câu hỏi bị ảnh hưởng.
- Thêm câu hỏi chuẩn cùng kết quả kỳ vọng làm regression fixture.
- Truyền thông thay đổi phá vỡ tương thích; khi cần thì version hoặc ngừng metric theo lộ trình.
- Kiểm tra SQL sinh ra khớp grain và bộ lọc mong muốn.

## Bài tập

Định nghĩa “khách hàng hoạt động hàng tháng” cho một sản phẩm. Ghi loại hoạt động, timezone, ranh giới tháng, quy tắc định danh, loại trừ và cách xử lý event đến muộn. Viết hai câu hỏi phải cho cùng kết quả và một câu không thể trả lời từ metric này.