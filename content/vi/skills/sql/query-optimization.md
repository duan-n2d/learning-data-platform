---
title: Tối ưu truy vấn SQL
description: Các mẫu thực tế để cải thiện hiệu năng truy vấn phân tích.
order: 2
tags: [SQL, hiệu năng]
---

# Tối ưu truy vấn SQL

Bắt đầu tối ưu bằng cách hiểu dung lượng dữ liệu, lực lượng kết hợp (cardinality), chỉ mục, phân vùng và query plan.

## Quy trình tinh chỉnh có thể lặp lại

1. Xác định kết quả đúng, lưu truy vấn baseline và đo thời gian trên dữ liệu đại diện.
2. Xem plan để tìm scan, join, sort, spill và ước tính lệch xa số dòng thực tế.
3. Kiểm tra grain và lực lượng join trước khi sửa cú pháp.
4. Mỗi lần chỉ thay đổi một yếu tố và xác minh kết quả không đổi.
5. So thời gian và tài nguyên trong cùng điều kiện; chỉ giữ thay đổi nếu nó giúp workload mục tiêu.

Mỗi SQL engine khác nhau, nên dùng tài liệu và định dạng plan của kho dữ liệu đang dùng, không mặc định một mẫu áp dụng giống nhau ở mọi nơi.

## Checklist

- Lọc sớm khi phù hợp.
- Tránh join nhiều-nhiều ngoài ý muốn.
- Xác định grain bảng trước khi join.
- Dùng partition hoặc clustering cho fact table lớn.
- Materialize phép biến đổi được lặp lại thường xuyên.
- Chỉ chọn cột cần thiết cho các bước sau.
- So sánh số dòng ước tính và thực tế quanh join/filter.
- Dùng partition filter khớp khóa phân vùng và khoảng thời gian cần truy vấn.
- Kiểm tra correlated subquery có thể viết rõ hơn bằng join/window không.
- Đo trước khi thêm index, clustering hoặc materialization; mỗi thứ đều tốn chi phí ghi, lưu trữ và bảo trì.

## Ví dụ fanout khi join

Nếu một đơn có 3 dòng hàng và 2 bản ghi lịch sử trạng thái, join cả hai bảng con trước khi tổng hợp có thể tạo 6 dòng cho đơn đó. Tổng doanh thu cấp đơn bị nhân lên. Hãy tổng hợp từng bảng con về grain join dự kiến trước, hoặc chỉ join quan hệ thực sự cần cho câu hỏi.

## Vì sao optimizer chọn full table scan

Full scan đọc toàn bộ dòng trong bảng thay vì dùng index hoặc partition pruning để bỏ qua dòng không cần. Cost-based optimizer chọn full scan khi nó ước tính scan rẻ hơn phương án khác:

- Không có index dùng được trên cột đang filter hoặc join.
- Bảng đủ nhỏ nên chi phí I/O thêm của index lookup không đáng; scan vài nghìn dòng có thể rẻ hơn duyệt cấu trúc index.
- Truy vấn không chọn lọc: trả về phần lớn số dòng của bảng, ví dụ `WHERE status != 'cancelled'` trên bảng mà phần lớn đơn đang active. Index chỉ giúp khi truy vấn loại bỏ phần lớn dòng, không phải khi giữ lại phần lớn dòng.
- Truy vấn count/aggregate trên toàn bảng (`SELECT count(*)`, `SELECT sum(amount)` không filter) phải chạm mọi dòng dù có index hay không.
- Table statistics cũ khiến cost-based optimizer đánh giá sai độ chọn lọc, dẫn tới chọn full scan (hoặc index) sai phương án. Refresh statistics thường là cách sửa đúng, không phải viết lại truy vấn.

B-tree index và bitmap index tránh scan trong các tình huống khác nhau. B-tree index phù hợp với range query, equality lookup và truy cập theo thứ tự trên cột có nhiều giá trị khác nhau. Bitmap index phù hợp với cột cardinality thấp (ít giá trị khác nhau, ví dụ `status` hoặc `region`) kết hợp filter `AND`/`OR`, thường gặp ở fact table trong warehouse; bitmap index thường không hợp với cột bị update từng dòng thường xuyên.

## Common table expression (CTE)

CTE không đệ quy là một subquery được đặt tên, dễ đọc, có thể tham chiếu lại trong cùng câu lệnh; engine có thể inline nó vào plan hoặc materialize, nên tự nó không đảm bảo thay đổi hiệu năng (xem "Không nên tối ưu một cách máy móc" bên dưới).

CTE đệ quy (recursive) duyệt một hierarchy hoặc graph tới bất kỳ độ sâu nào. Nó gồm hai phần nối bằng `UNION ALL`: **anchor member** chọn các dòng khởi đầu, và **recursive member** join CTE với chính nó, được tính lại cho tới khi không còn trả dòng nào (điều kiện dừng). Nếu không có điều kiện dừng rồi hết khớp, engine sẽ lặp tới khi chạm giới hạn đệ quy nội bộ.

Ví dụ minh họa: duyệt chuỗi nhân viên → quản lý để tìm mọi nhân viên dưới quyền một quản lý, ở bất kỳ cấp nào.

```sql
with recursive org_chart as (
    -- anchor member: nhân viên khởi đầu
    select employee_id, manager_id, full_name, 1 as depth
    from employees
    where employee_id = 100

    union all

    -- recursive member: mỗi nhân viên có quản lý đã có trong kết quả
    select e.employee_id, e.manager_id, e.full_name, oc.depth + 1
    from employees e
    join org_chart oc on e.manager_id = oc.employee_id
)
select * from org_chart order by depth;
```

Mẫu tương tự áp dụng cho bill-of-materials: tự tham chiếu `part_id -> parent_part_id` được duyệt theo cùng cách để triển khai một sản phẩm thành mọi sub-part ở mọi cấp.

## Không nên tối ưu một cách máy móc

- Truy vấn ngắn hơn chưa chắc chạy nhanh hơn.
- CTE có thể được inline hoặc materialize tùy engine.
- Lọc sớm chỉ hữu ích nếu giảm khối lượng xử lý và có thể đẩy xuống scan.
- Aggregate xấp xỉ đánh đổi độ chính xác lấy hiệu năng, cần được sản phẩm phê duyệt rõ.

## Bài tập

Chọn truy vấn chậm gồm một fact table và hai dimension. Ghi grain từng bảng, cardinality join dự kiến và số dòng sau lọc. So sánh plan trước/sau một thay đổi, rồi đối soát kết quả trên fixture nhỏ có đáp án chính xác.