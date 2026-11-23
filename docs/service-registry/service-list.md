# DANH SÁCH CÁC MICROSERVICE TRÊN EUREKA REGISTRY
## DỰ ÁN ĐẶT SÂN THỂ THAO ANTA

Bảng thông tin các dịch vụ đăng ký trên Eureka Server (`http://localhost:8761`):

| STT | Service ID (Tên đăng ký) | Instance ID | Cổng (Port) | Vai trò | Endpoint chính |
|:---:|:---|:---|:---:|:---:|:---|
| 1 | `SERVICE-REGISTRY` | `service-registry:8761` | 8761 | Service Registry | `GET /` (Dashboard), `GET /eureka/apps` |
| 2 | `API-GATEWAY` | `API-GATEWAY:8080` | 8080 | Central Gateway / Reverse Proxy | `GET /api/v1/gateway/info`<br>Định tuyến tới toàn bộ Microservices |
| 3 | `YARD-SERVICE` | `YARD-SERVICE:8081` | 8081 | Provider (Instance 1) | `GET /api/v1/instance-info`<br>`GET /api/v1/yards`<br>`GET /api/v1/yards/{id}/availability` |
| 4 | `YARD-SERVICE` | `YARD-SERVICE:8082` | 8082 | Provider (Instance 2) | `GET /api/v1/instance-info`<br>`GET /api/v1/yards`<br>`GET /api/v1/yards/{id}/availability` |
| 5 | `BOOKING-SERVICE` | `BOOKING-SERVICE:8083` | 8083 | Consumer / Điều phối đặt sân | `GET /api/v1/bookings/test-load-balancing`<br>`GET /api/v1/bookings/yards`<br>`POST /api/v1/bookings` |
| 6 | `PAYMENT-SERVICE` | `PAYMENT-SERVICE:8084` | 8084 | Provider thanh toán | `GET /api/v1/payments/instance-info`<br>`POST /api/v1/payments/intents` |
| 7 | `AUTH-SERVICE` | `AUTH-SERVICE:8085` | 8085 | Provider xác thực & tài khoản | `GET /api/v1/auth/instance-info`<br>`POST /api/v1/public/auth/login`<br>`GET /api/v1/users/me` |
