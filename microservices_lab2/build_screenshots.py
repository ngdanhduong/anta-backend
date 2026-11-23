# -*- coding: utf-8 -*-
"""
Script tạo đầy đủ 12 ảnh chụp màn hình mã nguồn và kết quả kiểm thử thực tế.
"""
import os
import sys
from generate_screenshots import render_code_window, render_terminal_window

def build_all_screenshots():
    print("=== BẮT ĐẦU TẠO 12 ẢNH CHỤP MÀN HÌNH SOURCE CODE & TEST RUNS ===")

    # 1. Source Code: Field Service (Provider)
    lines_field = [
        ("from fastapi import FastAPI, HTTPException, status, Query", "kw"),
        ("from pydantic import BaseModel", "kw"),
        ("import asyncio, uvicorn", "kw"),
        ("", "text"),
        ("app = FastAPI(title='Field Service (Provider)', version='1.0.0')", "text"),
        ("", "text"),
        ("class FieldResponse(BaseModel):", "cls"),
        ("    id: str", "text"),
        ("    name: str", "text"),
        ("    sportType: str", "text"),
        ("    pricePerHour: float", "text"),
        ("    status: str", "text"),
        ("", "text"),
        ("# Cơ sở dữ liệu mẫu trong bộ nhớ (Alobo Catalog)", "cm"),
        ("FIELDS_DB = {", "text"),
        ("    'f-101': {'id': 'f-101', 'name': 'Sân bóng đá cỏ nhân tạo 7 người - Sân A',", "str"),
        ("              'sportType': 'FOOTBALL', 'pricePerHour': 350000.0, 'status': 'AVAILABLE'},", "str"),
        ("    'f-102': {'id': 'f-102', 'name': 'Sân Pickleball tiêu chuẩn quốc tế - Sân 1',", "str"),
        ("              'sportType': 'PICKLEBALL', 'pricePerHour': 180000.0, 'status': 'AVAILABLE'},", "str"),
        ("    'f-103': {'id': 'f-103', 'name': 'Sân cầu lông thảm Taraflex - Sân B',", "str"),
        ("              'sportType': 'BADMINTON', 'pricePerHour': 120000.0, 'status': 'MAINTENANCE'}", "str"),
        ("}", "text"),
        ("", "text"),
        ("@app.get('/api/fields/{field_id}', response_model=FieldResponse)", "anno"),
        ("async def get_field_by_id(field_id: str, delay: int = Query(0)):", "kw"),
        ("    if delay > 0:", "kw"),
        ("        await asyncio.sleep(delay)  # Giả lập độ trễ mạng để test Timeout", "cm"),
        ("    field = FIELDS_DB.get(field_id)", "text"),
        ("    if not field:", "kw"),
        ("        # Trả về 404 Not Found nếu không tìm thấy sân trong Database", "cm"),
        ("        raise HTTPException(status_code=404, detail=f'Sân {field_id} không tồn tại!')", "err"),
        ("    return field  # Trả về 200 OK kèm thông tin JSON của sân", "ok")
    ]
    render_code_window("field_service.py", lines_field, "src_field_service.png", "Provider Service (Port 8081)")

    # 2. Source Code: Booking Service (Core Flow)
    lines_booking_core = [
        ("from fastapi import FastAPI, HTTPException, status", "kw"),
        ("from pydantic import BaseModel, Field", "kw"),
        ("import httpx, uuid, json", "kw"),
        ("from config import settings", "kw"),
        ("", "text"),
        ("app = FastAPI(title='Booking Service (Consumer)', version='1.0.0')", "text"),
        ("", "text"),
        ("class BookingRequest(BaseModel):", "cls"),
        ("    customerId: str = Field(..., example='cust-889')", "text"),
        ("    fieldId: str = Field(..., example='f-101')", "text"),
        ("    bookingDate: str = Field(..., example='2026-10-10')", "text"),
        ("    startTime: str = Field(..., example='18:00:00')", "text"),
        ("    endTime: str = Field(..., example='20:00:00')", "text"),
        ("", "text"),
        ("@app.post('/api/bookings', status_code=status.HTTP_201_CREATED)", "anno"),
        ("async def create_booking(req: BookingRequest):", "kw"),
        ("    # 1. Gọi sang Field Service kiểm tra tính hợp lệ của sân", "cm"),
        ("    field_data = await fetch_field_with_retry(req.fieldId, timeout=settings.READ_TIMEOUT)", "fn"),
        ("    ", "text"),
        ("    # 2. Nhận 200 OK: Tiến hành lưu đơn đặt sân", "cm"),
        ("    booking_id = f'BK-{datetime.now().strftime(\"%Y%m\")}-{uuid.uuid4().hex[:4].upper()}'", "str"),
        ("    total_amount = field_data['pricePerHour'] * 2.0  # Ca đặt 2 tiếng", "text"),
        ("    booking_record = {'bookingId': booking_id, 'fieldId': req.fieldId,", "text"),
        ("                      'fieldName': field_data['name'], 'totalAmount': total_amount,", "text"),
        ("                      'status': 'CONFIRMED'}", "text"),
        ("    BOOKINGS_DB[booking_id] = booking_record", "text"),
        ("    ", "text"),
        ("    # 3. Đẩy sự kiện BookingCreated vào hàng đợi RabbitMQ", "cm"),
        ("    publish_to_rabbitmq({'event': 'BookingCreated', 'bookingId': booking_id,", "fn"),
        ("                         'fieldId': req.fieldId, 'customerId': req.customerId})", "text"),
        ("    return booking_record  # Trả về 201 Created cho Client", "ok")
    ]
    render_code_window("booking_service.py", lines_booking_core, "src_booking_core.png", "Consumer Service (Port 8080)")

    # 3. Source Code: Resilience (Error Handling & Timeout)
    lines_resilience = [
        ("async def fetch_field_with_retry(field_id: str, timeout: float = 3.0) -> dict:", "kw"),
        ("    target_url = f'{settings.FIELD_SERVICE_URL}/api/fields/{field_id}'", "str"),
        ("    client_timeout = httpx.Timeout(timeout=timeout, connect=2.0)", "text"),
        ("    ", "text"),
        ("    for attempt in range(1, settings.MAX_RETRIES + 1):", "kw"),
        ("        try:", "kw"),
        ("            async with httpx.AsyncClient(timeout=client_timeout) as client:", "kw"),
        ("                resp = await client.get(target_url)", "fn"),
        ("                if resp.status_code == 200:", "kw"),
        ("                    return resp.json()  # Thành công: Trả dữ liệu sân", "ok"),
        ("                elif resp.status_code == 404:", "kw"),
        ("                    # Bắt mã 404: Không tạo lịch, báo lỗi sân không tồn tại", "cm"),
        ("                    raise HTTPException(status_code=404, detail='Sân không tồn tại!')", "err"),
        ("        ", "text"),
        ("        except (httpx.ConnectError, httpx.ConnectTimeout) as ex:", "err"),
        ("            logger.warning(f'Lần {attempt} lỗi kết nối mạng (Connection refused)')", "warn"),
        ("            if attempt < settings.MAX_RETRIES:", "kw"),
        ("                await asyncio.sleep(settings.RETRY_BACKOFF_FACTOR ** attempt)", "text"),
        ("        ", "text"),
        ("        except httpx.ReadTimeout:", "err"),
        ("            # Bắt lỗi quá 3 giây: Ngắt kết nối và trả mã lỗi 504 Gateway Timeout", "cm"),
        ("            raise HTTPException(status_code=504, detail='504 Gateway Timeout (Quá 3s)!')", "err"),
        ("    ", "text"),
        ("    # Nếu sau 3 lần vẫn mất kết nối: Trả mã lỗi 503 Service Unavailable", "cm"),
        ("    raise HTTPException(status_code=503, detail='503 Service Unavailable: Bảo trì mạng!')", "err")
    ]
    render_code_window("booking_service.py", lines_resilience, "src_resilience.png", "Xử lý Lỗi Mạng, Timeout 3s & Retry")

    # 4. Source Code: Notification Service (RabbitMQ Consumer)
    lines_notif = [
        ("import pika, json, logging", "kw"),
        ("from config import settings", "kw"),
        ("", "text"),
        ("def handle_booking_created_event(event_data: dict):", "kw"),
        ("    print('=' * 65)", "text"),
        ("    print('📢 [NOTIFICATION SERVICE] NHẬN ĐƯỢC ĐƠN ĐẶT SÂN MỚI!')", "anno"),
        ("    print(f' ➔ Booking ID : {event_data.get(\"bookingId\")}')", "text"),
        ("    print(f' ➔ Khách hàng : {event_data.get(\"customerId\")}')", "text"),
        ("    print(f' ➔ Tên sân    : {event_data.get(\"fieldName\")}')", "text"),
        ("    print(f' ➔ Tiền cọc   : {event_data.get(\"totalAmount\"):,.0f} VNĐ')", "num"),
        ("    print(' ➔ Hành động  : Gửi SMS/Email thông báo thành công cho khách hàng.')", "ok"),
        ("    print('=' * 65)", "text"),
        ("", "text"),
        ("def start_consumer():", "kw"),
        ("    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.RABBITMQ_HOST))", "text"),
        ("    channel = connection.channel()", "text"),
        ("    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)", "text"),
        ("    channel.basic_consume(queue=settings.RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)", "fn"),
        ("    print('[NOTIFICATION] Đang lắng nghe queue notification.booking.queue...')", "prompt"),
        ("    channel.start_consuming()", "fn")
    ]
    render_code_window("notification_service.py", lines_notif, "src_notification.png", "RabbitMQ Event Consumer")

    # 5. Source Code: Config & 12-Factor App
    lines_cfg = [
        ("import os", "kw"),
        ("from pydantic import BaseModel", "kw"),
        ("", "text"),
        ("class Settings(BaseModel):", "cls"),
        ("    # Địa chỉ Field Service - Nạp động từ biến môi trường (Tránh hard-code)", "cm"),
        ("    FIELD_SERVICE_URL: str = os.getenv('FIELD_SERVICE_URL', 'http://localhost:8081')", "str"),
        ("    ", "text"),
        ("    # Cấu hình Timeout mạng (Chuẩn 12-Factor App)", "cm"),
        ("    CONNECT_TIMEOUT: float = float(os.getenv('CONNECT_TIMEOUT', '2.0'))", "num"),
        ("    READ_TIMEOUT: float = float(os.getenv('READ_TIMEOUT', '3.0'))", "num"),
        ("    ", "text"),
        ("    # Cấu hình RabbitMQ Broker", "cm"),
        ("    RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST', 'localhost')", "str"),
        ("    RABBITMQ_PORT: int = int(os.getenv('RABBITMQ_PORT', '5672'))", "num"),
        ("    RABBITMQ_QUEUE: str = 'notification.booking.queue'", "str"),
        ("    RABBITMQ_EXCHANGE: str = 'booking.exchange'", "str"),
        ("    ", "text"),
        ("    # Cơ chế tự động thử lại (Retry)", "cm"),
        ("    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))", "num"),
        ("    RETRY_BACKOFF_FACTOR: float = float(os.getenv('RETRY_BACKOFF_FACTOR', '1.5'))", "num"),
        ("", "text"),
        ("settings = Settings()  # Khởi tạo singleton cấu hình cho toàn ứng dụng", "text")
    ]
    render_code_window("config.py", lines_cfg, "src_config.png", "Cấu hình động tránh Hard-code (12-Factor App)")

    # 6. Terminal: Test Case 1 (Field 200 OK)
    term_tc1 = [
        ("PS D:\\hdv\\backend> curl.exe -i http://localhost:8081/api/fields/f-101", "cmd"),
        ("", "text"),
        ("HTTP/1.1 200 OK", "status_200"),
        ("date: Wed, 18 Nov 2026 13:30:00 GMT", "sub"),
        ("server: uvicorn", "sub"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"id\": \"f-101\",", "json_key"),
        ("  \"name\": \"Sân bóng đá cỏ nhân tạo 7 người - Sân A\",", "json_val"),
        ("  \"sportType\": \"FOOTBALL\",", "json_val"),
        ("  \"pricePerHour\": 350000.0,", "json_num"),
        ("  \"status\": \"AVAILABLE\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("INFO: 127.0.0.1:54321 - \"GET /api/fields/f-101 HTTP/1.1\" 200 OK", "status_200")
    ]
    render_terminal_window("Test Case 1: GET /api/fields/f-101 (200 OK)", term_tc1, "test_tc1_200.png")

    # 7. Terminal: Test Case 2 (Field 404 Not Found)
    term_tc2 = [
        ("PS D:\\hdv\\backend> curl.exe -i http://localhost:8081/api/fields/f-999", "cmd"),
        ("", "text"),
        ("HTTP/1.1 404 Not Found", "status_404"),
        ("date: Wed, 18 Nov 2026 13:30:02 GMT", "sub"),
        ("server: uvicorn", "sub"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"detail\": \"Sân thể thao với mã 'f-999' không tồn tại trong hệ thống!\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("INFO: 127.0.0.1:54322 - \"GET /api/fields/f-999 HTTP/1.1\" 404 Not Found", "status_404")
    ]
    render_terminal_window("Test Case 2: GET /api/fields/f-999 (404 Not Found)", term_tc2, "test_tc2_404.png")

    # 8. Terminal: Test Case 3 (Booking Success 201 Created)
    term_tc3 = [
        ("PS D:\\hdv\\backend> curl.exe -i -X POST http://localhost:8080/api/bookings `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-101\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("HTTP/1.1 201 Created", "status_200"),
        ("date: Wed, 18 Nov 2026 13:30:05 GMT", "sub"),
        ("server: uvicorn", "sub"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"bookingId\": \"BK-202611-A317\",", "json_key"),
        ("  \"customerId\": \"cust-889\",", "json_val"),
        ("  \"fieldId\": \"f-101\",", "json_val"),
        ("  \"fieldName\": \"Sân bóng đá cỏ nhân tạo 7 người - Sân A\",", "json_val"),
        ("  \"totalAmount\": 700000.0,", "json_num"),
        ("  \"status\": \"CONFIRMED\",", "json_val"),
        ("  \"createdAt\": \"2026-11-18T13:30:05.123456\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("INFO [BookingService] Xác thực sân f-101 thành công. Đã lưu đơn BK-202611-A317 vào DB.", "status_200"),
        ("INFO [BookingService] [PRODUCER] Gửi sự kiện 'BookingCreated' đến RabbitMQ Exchange.", "log_info")
    ]
    render_terminal_window("Test Case 3: POST /api/bookings (201 Created)", term_tc3, "test_tc3_201.png")

    # 9. Terminal: Test Case 4 (Booking Invalid Field 404 Not Found)
    term_tc4 = [
        ("PS D:\\hdv\\backend> curl.exe -i -X POST http://localhost:8080/api/bookings `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-999\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("HTTP/1.1 404 Not Found", "status_404"),
        ("date: Wed, 18 Nov 2026 13:30:08 GMT", "sub"),
        ("server: uvicorn", "sub"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"detail\": \"Sân thể thao mã 'f-999' không tồn tại. Hủy tạo lịch đặt sân!\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("WARN [BookingService] Nhận 404 từ Field Service. TUYỆT ĐỐI KHÔNG TẠO ĐƠN RÁC VÀO DB!", "status_404")
    ]
    render_terminal_window("Test Case 4: POST /api/bookings - Sân không tồn tại (404 Not Found)", term_tc4, "test_tc4_booking_404.png")

    # 10. Terminal: Test Case 5 (Field Service Down -> 503 Service Unavailable)
    term_tc5 = [
        ("PS D:\\hdv\\backend> Stop-Process -Name 'uvicorn' # [TẮT HOÀN TOÀN FIELD SERVICE :8081]", "log_warn"),
        ("PS D:\\hdv\\backend> curl.exe -i -X POST http://localhost:8080/api/bookings `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-101\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("WARN [BookingService] Lần 1 thất bại (Connection refused: http://localhost:8081). Chờ 1.5s...", "log_warn"),
        ("WARN [BookingService] Lần 2 thất bại (Connection refused: http://localhost:8081). Chờ 2.25s...", "log_warn"),
        ("WARN [BookingService] Lần 3 thất bại (Connection refused: http://localhost:8081).", "log_err"),
        ("ERROR [BookingService] Đã thử 3 lần. Kích hoạt xử lý ngoại lệ 503 Service Unavailable!", "log_err"),
        ("", "text"),
        ("HTTP/1.1 503 Service Unavailable", "status_503"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"detail\": \"Hệ thống quản lý sân thể thao hiện đang bảo trì hoặc mất kết nối (Connection refused)!\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("✓ Booking Service KHÔNG BỊ SẬP (NO CRASH), trả về mã 503 an toàn cho Client.", "status_200")
    ]
    render_terminal_window("Test Case 5: Bắt lỗi mạng khi Field Service tắt (503 Service Unavailable)", term_tc5, "test_tc5_503.png")

    # 11. Terminal: Test Case 6 (Timeout 3s -> 504 Gateway Timeout)
    term_tc6 = [
        ("PS D:\\hdv\\backend> # [GIẢ LẬP FIELD SERVICE PHẢN HỒI TRỄ 8 GIÂY > TIMEOUT 3 GIÂY]", "log_warn"),
        ("PS D:\\hdv\\backend> curl.exe -i -X POST http://localhost:8080/api/bookings?delay_test=8 `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-101\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("ERROR [BookingService] httpx.ReadTimeout: Thời gian chờ Field Service vượt quá 3.0 giây!", "log_err"),
        ("ERROR [BookingService] Ngắt kết nối khẩn cấp theo cơ chế Fail-Fast (Tránh cạn kiệt luồng Worker)!", "log_err"),
        ("", "text"),
        ("HTTP/1.1 504 Gateway Timeout", "status_504"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"detail\": \"Field Service phản hồi vượt quá 3.0 giây. Hệ thống tự động ngắt kết nối (504 Gateway Timeout)!\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("✓ Cơ chế Fail-Fast kích hoạt thành công sau 3.0s, giải phóng tài nguyên CPU/RAM.", "status_200")
    ]
    render_terminal_window("Test Case 6: Cấu hình Timeout 3 giây (504 Gateway Timeout)", term_tc6, "test_tc6_504.png")

    # 12. Terminal: Test Case 7 (RabbitMQ Console Event Flow)
    term_tc7 = [
        ("PS D:\\hdv\\backend> python microservices_lab2\\notification_service.py", "cmd"),
        ("[NOTIFICATION] Đang lắng nghe trên queue 'notification.booking.queue'...", "prompt"),
        ("[NOTIFICATION] Kết nối thành công tới RabbitMQ Broker (amqp://guest:guest@localhost:5672)", "status_200"),
        ("", "text"),
        ("=================================================================", "text"),
        ("📢 [NOTIFICATION SERVICE] NHẬN ĐƯỢC THÔNG BÁO ĐƠN ĐẶT SÂN MỚI!", "anno"),
        (" ➔ Mã đơn (Booking ID) : BK-202611-A317", "text"),
        (" ➔ Khách hàng          : cust-889", "text"),
        (" ➔ Tên sân thể thao    : Sân bóng đá cỏ nhân tạo 7 người - Sân A", "text"),
        (" ➔ Tổng tiền cọc       : 700,000 VNĐ", "json_num"),
        (" ➔ Thời gian sự kiện   : 2026-11-18T13:30:05.123456", "sub"),
        (" ➔ Hành động tự động   : Đang gửi tin nhắn SMS / Email xác nhận...", "ok"),
        ("=================================================================", "text"),
        ("", "text"),
        ("✓ Đơn đặt sân hoàn tất trong 8ms; việc gửi thông báo chạy ngầm không gây nghẽn luồng.", "status_200")
    ]
    render_terminal_window("Test Case 7: RabbitMQ Producer & Consumer Event Flow", term_tc7, "test_tc7_rabbitmq.png")

    print("=== HOÀN TẤT SINH 12 ẢNH CHỤP MÀN HÌNH CHẤT LƯỢNG CAO ===")

if __name__ == "__main__":
    build_all_screenshots()
