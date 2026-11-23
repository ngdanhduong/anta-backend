# THIẾT KẾ VÀ HOẠT ĐỘNG CỦA SERVICE REGISTRY (EUREKA)

### 1. Kiến trúc Service Registry
- **Công nghệ**: Spring Boot 4.1.2 / Spring Cloud 2025.1.4 với Netflix Eureka Server.
- **Cổng dịch vụ**: `8761`.
- **Dashboard**: `http://localhost:8761`.

### 2. Luồng đăng ký và khám phá dịch vụ (Service Discovery Flow)

```mermaid
sequenceDiagram
    autonumber
    participant Registry as Eureka Server (Port 8761)
    participant Yard1 as YARD-SERVICE :8081
    participant Yard2 as YARD-SERVICE :8082
    participant Booking as BOOKING-SERVICE :8083
    participant Client as Client (Postman / App)

    Note over Registry: Eureka Server khởi động tại cổng 8761
    Yard1->>Registry: Đăng ký YARD-SERVICE (IP:Port :8081) + Gửi Heartbeat định kỳ
    Yard2->>Registry: Đăng ký YARD-SERVICE (IP:Port :8082) + Gửi Heartbeat định kỳ
    Booking->>Registry: Đăng ký BOOKING-SERVICE (IP:Port :8083)

    Client->>Booking: POST /api/v1/bookings (Yêu cầu đặt sân)
    Booking->>Registry: Hỏi danh bạ: "Ai đang chạy YARD-SERVICE?"
    Registry-->>Booking: Trả về danh sách: [:8081, :8082]
    
    Note over Booking: Spring Cloud LoadBalancer chọn Instance :8082 (Round-Robin)
    Booking->>Yard2: GET /api/v1/yards/yard-01/availability
    Yard2-->>Booking: Trả về: { status: "AVAILABLE", handledByPort: 8082 }
    
    Booking-->>Client: Trả về kết quả: { bookingId: "ANTA-BK-...", status: "CONFIRMED" }
```

### 3. Cơ chế chịu lỗi (Fault Tolerance)
- Khi một instance của `YARD-SERVICE` bị tắt (ví dụ cổng 8081 gặp sự cố), các request tiếp theo tự động được định tuyến sang cổng 8082 còn lại mà không gây gián đoạn cho khách hàng.
- Eureka duy trì trạng thái các instance thông qua nhịp đập heartbeat (chu kỳ 30 giây). Nếu quá thời hạn không nhận được heartbeat, instance sẽ bị tự động loại bỏ (eviction).
