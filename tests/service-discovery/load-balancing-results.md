# BÁO CÁO KẾT QUẢ KIỂM THỬ CÂN BẰNG TẢI (LOAD BALANCING)
## HỆ THỐNG ĐẶT SÂN THỂ THAO ANTA

- **Consumer**: `BOOKING-SERVICE` (Port 8083)
- **Provider**: `YARD-SERVICE` (chạy 2 Instance: Port 8081 và Port 8082)
- **Cơ chế Discovery**: Spring Cloud Netflix Eureka + Spring Cloud LoadBalancer (Round-Robin)
- **Thời gian thực hiện**: 16/11/2026

---

### 1. Bảng dữ liệu thực nghiệm 20 Request liên tiếp

Dưới đây là kết quả thực tế khi `BOOKING-SERVICE` nhận 20 request và khám phá `YARD-SERVICE` qua Eureka:

| Lần gửi | Consumer | Instance ID được chọn | Cổng xử lý | Trạng thái |
|:---:|:---:|:---:|:---:|:---:|
| 1 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 2 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 3 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 4 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 5 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 6 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 7 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 8 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 9 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 10 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 11 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 12 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 13 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 14 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 15 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 16 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 17 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 18 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |
| 19 | BOOKING-SERVICE:8083 | YARD-SERVICE:8082 | 8082 | Thành công (200 OK) |
| 20 | BOOKING-SERVICE:8083 | YARD-SERVICE:8081 | 8081 | Thành công (200 OK) |

---

### 2. Thống kê và Nhận xét

- **Tổng số request**: 20
- **Instance 8081 xử lý**: 10 requests (tỷ lệ 50%)
- **Instance 8082 xử lý**: 10 requests (tỷ lệ 50%)
- **Đánh giá**:
  - `BOOKING-SERVICE` hoàn toàn **không cấu hình cứng bất kỳ địa chỉ IP hay số cổng nào** của `YARD-SERVICE`.
  - Bộ cân bằng tải phía client (`Spring Cloud LoadBalancer`) đã tự động lấy danh sách instance khả dụng từ `Eureka Server` và phân phối luân phiên chính xác theo thuật toán **Round-Robin**.
