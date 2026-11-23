# BẢNG KIỂM THỬ KHẢ NĂNG PHỤC HỒI VÀ XỬ LÝ LỖI (FAULT TOLERANCE)
## HỆ THỐNG MICROSERVICES ANTA

Tuân thủ danh mục kiểm thử từ **TC01 đến TC06** theo yêu cầu Barem Bài thực hành số 7:

| Mã | Tình huống kiểm thử | Hành động thực hiện | Kết quả mong đợi | Kết quả thực tế quan sát | Đánh giá |
|:---:|:---|:---|:---|:---|:---:|
| **TC01** | Khởi động Registry và các Microservice | Chạy `service-registry`, 2 instance `yard-service` (8081, 8082), `booking-service` (8083), `payment-service` (8084). | Các dịch vụ tự đăng ký và hiển thị `UP` trên Eureka Dashboard `http://localhost:8761`. | Dashboard hiển thị đầy đủ `YARD-SERVICE` (2 instances), `BOOKING-SERVICE` (1 instance), `PAYMENT-SERVICE` (1 instance). | **ĐẠT** |
| **TC02** | Consumer gọi Provider theo Service ID | Gửi request `POST /api/v1/bookings` hoặc `GET /test-load-balancing` tới `BOOKING-SERVICE`. | `BOOKING-SERVICE` tra cứu `YARD-SERVICE` qua Eureka và nhận kết quả kiểm tra sân thành công. | Trả về HTTP 200 OK kèm thông tin xác nhận từ `YARD-SERVICE`. | **ĐẠT** |
| **TC03** | Một Provider có hai instance | Gửi 20 request liên tiếp đến `BOOKING-SERVICE`. | Request được phân phối luân phiên cho cả hai cổng 8081 và 8082. | Kết quả 50% request vào 8081 và 50% request vào 8082 (Round-Robin). | **ĐẠT** |
| **TC04** | Dừng một instance đột ngột | Tắt tiến trình `YARD-SERVICE` tại cổng 8081, giữ nguyên cổng 8082. Tiếp tục gửi request tới `BOOKING-SERVICE`. | Toàn bộ các request mới vẫn được Instance 8082 tiếp nhận và phục vụ bình thường, không làm gián đoạn hệ thống. | `BOOKING-SERVICE` chuyển hướng 100% request vào `YARD-SERVICE:8082`, người dùng không gặp lỗi. | **ĐẠT** |
| **TC05** | Dừng toàn bộ instance Provider | Tắt nốt Instance 8082 (không còn instance `YARD-SERVICE` nào khả dụng). Gửi request tới `BOOKING-SERVICE`. | `BOOKING-SERVICE` trả về thông báo lỗi rõ ràng (503 Service Unavailable / Feign Exception), không bị treo vô hạn. | Trả về lỗi `503 No instances available for YARD-SERVICE`, request hoàn thành nhanh chóng không bị timeout. | **ĐẠT** |
| **TC06** | Khởi động lại Provider | Khởi động lại `YARD-SERVICE` cổng 8081. | Dịch vụ gửi heartbeat đăng ký lại vào Eureka Server và `BOOKING-SERVICE` tự động phục hồi luồng gọi. | Sau khi instance gửi heartbeat, Eureka Dashboard cập nhật trạng thái `UP` và `BOOKING-SERVICE` gọi lại thành công 100%. | **ĐẠT** |
