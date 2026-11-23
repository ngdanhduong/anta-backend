# THIẾT KẾ KIẾN TRÚC MICROSERVICES HỆ THỐNG ANTA
## BÀI THỰC HÀNH SỐ 7 & 8 – PTPM HƯỚNG DỊCH VỤ

---

### 1. Kiến trúc hệ thống chuyển đổi hoàn chỉnh sang Microservices

Hệ thống đã được chuyển đổi hoàn toàn từ kiến trúc Monolith sang **Hệ sinh thái Microservices hoàn chỉnh** gồm 6 dịch vụ thành phần:

1. **`SERVICE-REGISTRY`** (Port 8761): Netflix Eureka Server quản lý danh bạ dịch vụ tập trung, heartbeat và tự động loại bỏ instance gặp sự cố.
2. **`API-GATEWAY`** (Port 8080): Điểm đón tiếp duy nhất (Single Entry Point) cho toàn bộ Client (Mobile App, Web Admin, Web Chủ Sân). Tự động tra cứu Eureka và cân bằng tải tới các dịch vụ phía sau.
3. **`YARD-SERVICE`** (Port 8081, 8082): Quản lý danh mục sân bãi, chi nhánh, môn thể thao, khung giờ trống (`availability`). Thiết lập 2 instance chạy song song phục vụ kiểm thử Cân bằng tải (Round-Robin).
4. **`BOOKING-SERVICE`** (Port 8083): Điều phối quy trình đặt sân (`bookings`). Tự động gọi sang `YARD-SERVICE` (kiểm tra sân trống) và `PAYMENT-SERVICE` (tạo thanh toán) thông qua Spring Cloud OpenFeign.
5. **`PAYMENT-SERVICE`** (Port 8084): Xử lý khởi tạo giao dịch thanh toán mô phỏng (Sandbox).
6. **`AUTH-SERVICE`** (Port 8085): Quản lý phiên đăng nhập, cấp phát JWT, xác minh mã OTP và thông tin người dùng.

---

### 2. Bảng phân định trách nhiệm và Quyền sở hữu dữ liệu

| Dịch vụ | Trách nhiệm chính | CSDL / Schema sở hữu | Consumer sử dụng | Provider cần gọi |
|:---|:---|:---|:---|:---|
| **`API-GATEWAY`** | Cổng đón tiếp duy nhất, xác thực CORS, định tuyến thông minh theo Service ID. | Không sở hữu dữ liệu nghiệp vụ | Client (Android / Web) | Mọi Microservices |
| **`AUTH-SERVICE`** | Đăng ký, đăng nhập OTP / Mật khẩu / Google, cấp phát token JWT, thông tin cá nhân. | `auth_db` (`users`, `roles`, `otp_challenges`) | `API-GATEWAY`, Client | Không |
| **`YARD-SERVICE`** | Quản lý thông tin chi nhánh, sân bãi, môn thể thao, khung giờ trống (`availability`), bảng giá. | `yard_db` (`branches`, `yards`, `sports`, `opening_hours`, `slots`) | `BOOKING-SERVICE`, Client | Không |
| **`BOOKING-SERVICE`** | Quản lý quy trình giữ chỗ (`hold`), xác nhận đặt sân (`booking`), hủy đơn và điều phối. | `booking_db` (`booking_holds`, `bookings`, `booking_status_history`) | `API-GATEWAY`, Client | `YARD-SERVICE`, `PAYMENT-SERVICE` |
| **`PAYMENT-SERVICE`** | Khởi tạo giao dịch thanh toán (`payment-intents`), xử lý thanh toán mô phỏng (Sandbox). | `payment_db` (`payment_intents`, `payment_transactions`, `refunds`) | `BOOKING-SERVICE` | Không |
| **`SERVICE-REGISTRY`** | Quản lý danh bạ, heartbeat, vòng đời đăng ký và hủy đăng ký của các Microservice. | Bộ nhớ Registry (In-Memory) | Mọi Microservice | Không |

> **Nguyên tắc bất biến**: Các Microservices giao tiếp phi tập trung qua Service Discovery (Eureka) và OpenFeign. Client chỉ cần kết nối qua cổng Gateway duy nhất (`8080`).
