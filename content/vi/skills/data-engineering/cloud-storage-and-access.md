---
title: Cơ bản về lưu trữ Cloud và quyền truy cập
description: Chọn nơi lưu dữ liệu bền vững và áp dụng quyền tối thiểu.
order: 4
tags: [cloud, object storage, IAM, bảo mật]
---

# Cơ bản về lưu trữ Cloud và quyền truy cập

Hệ thống dữ liệu cloud kết hợp object storage, compute, database và kiểm soát danh tính. Chi tiết từng nhà cung cấp khác nhau nhưng câu hỏi thiết kế tương tự: lưu gì, trong bao lâu, ai được truy cập và khôi phục thế nào?

## Các tầng lưu trữ

Object storage phù hợp lưu file raw bền vững và snapshot bất biến. Warehouse hoặc lakehouse cung cấp cấu trúc tối ưu cho đọc và biến đổi phân tích. Tách nguồn raw khỏi đầu ra curated để có thể sửa lỗi biến đổi mà không mất nguồn.

Chọn định dạng và partition theo mẫu truy cập. Định dạng cột có thể giảm chi phí scan cho workload phân tích. Partition theo trường thường được lọc và có cardinality phù hợp; quá nhiều partition nhỏ gây overhead. Lưu schema và metadata ingestion để file vẫn đọc hiểu được về sau.

## Danh tính và quyền tối thiểu

Dùng danh tính riêng cho ingestion, biến đổi, analytics tương tác và ứng dụng truy vấn. Chỉ cấp bucket path, schema và thao tác cần thiết. Dịch vụ Text2SQL không dùng lại credential admin hay developer. Rà cả quyền kế thừa và đường impersonate service account, không chỉ grant trực tiếp.

Không để bí mật trong source control, notebook, prompt hay log. Ưu tiên secret store được quản lý hoặc workload identity. Xoay vòng credential và audit truy cập theo độ nhạy và chính sách lưu giữ dữ liệu.

## Độ bền và khôi phục

Định nghĩa thời hạn lưu, chuyển tầng lifecycle, mã hóa, backup và mục tiêu khôi phục. Hãy thử restore; cấu hình backup không chứng minh rằng dữ liệu khôi phục được. Với dữ liệu nguồn quan trọng, giữ bản bất biến/có phiên bản và bảo đảm chính sách xóa không xóa bản khôi phục cuối cùng.

## Chi phí và vận hành

Theo dõi tăng trưởng lưu trữ, byte scan, thời gian compute, egress và tài nguyên nhàn rỗi. Dùng lifecycle cho dữ liệu tạm hết hạn nhưng không xóa dữ liệu cần tái tạo hoặc tuân thủ. Mỗi kiểm soát chi phí cần chủ sở hữu và ngưỡng dựa trên workload dự kiến.

## Bài tập

Thiết kế lưu trữ cho pipeline event hằng ngày gồm raw, staged, curated. Liệt kê danh tính và thao tác chính xác cần cấp, xác định trường nhạy cảm, mô tả cách khôi phục partition bị ghi đè nhầm mà không cấp quyền bucket rộng cho tất cả người dùng.