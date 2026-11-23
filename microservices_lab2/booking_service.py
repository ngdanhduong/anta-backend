# -*- coding: utf-8 -*-
"""
Booking Service (Consumer) - Port 8080
Tiếp nhận yêu cầu đặt sân, gọi sang Field Service xác thực bằng HTTP Client (httpx),
xử lý lỗi kết nối, timeout và đẩy sự kiện vào RabbitMQ.
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import httpx
import uuid
import asyncio
import json
import logging
from datetime import datetime
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BookingService")

app = FastAPI(
    title="Booking Service (Consumer)",
    description="Dịch vụ đặt sân thể thao (Alobo Court Booking)",
    version="1.0.0"
)

class BookingRequest(BaseModel):
    customerId: str = Field(..., example="cust-889")
    fieldId: str = Field(..., example="f-101")
    bookingDate: str = Field(..., example="2026-10-10")
    startTime: str = Field(..., example="18:00:00")
    endTime: str = Field(..., example="20:00:00")

class BookingResponse(BaseModel):
    bookingId: str
    customerId: str
    fieldId: str
    fieldName: str
    totalAmount: float
    status: str
    createdAt: str

# Giả lập Database lưu trữ đơn đặt sân
BOOKINGS_DB: dict[str, dict] = {}

def publish_to_rabbitmq(event_data: dict) -> bool:
    """
    Bắn sự kiện BookingCreated vào RabbitMQ Broker (hoặc giả lập log nếu chưa cài RabbitMQ)
    """
    try:
        # Nếu có thư viện pika hoặc kết nối RabbitMQ
        logger.info(f" [PRODUCER] Gửi sự kiện 'BookingCreated' đến RabbitMQ Exchange '{settings.RABBITMQ_EXCHANGE}'")
        logger.info(f" [PRODUCER] Payload: {json.dumps(event_data, ensure_ascii=False)}")
        return True
    except Exception as e:
        logger.warning(f"Không thể kết nối RabbitMQ ({e}), chuyển sang chế độ in-memory event log.")
        return False

async def fetch_field_with_retry(field_id: str, timeout: float = 3.0, simulate_delay: int = 0) -> dict:
    """
    Gọi sang Field Service với cơ chế tự động Retry tối đa 3 lần và Timeout 3s
    """
    target_url = f"{settings.FIELD_SERVICE_URL}/api/fields/{field_id}"
    if simulate_delay > 0:
        target_url += f"?delay={simulate_delay}"

    # Cấu hình Timeout: kết nối 2s, đọc 3s
    client_timeout = httpx.Timeout(timeout=timeout, connect=settings.CONNECT_TIMEOUT)
    
    last_exception = None
    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            logger.info(f"Đang gọi Field Service (lần {attempt}/{settings.MAX_RETRIES}): {target_url}")
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                response = await client.get(target_url)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Mã 404 là lỗi nghiệp vụ (không tồn tại sân), không retry
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Sân thể thao mã '{field_id}' không tồn tại. Hủy tạo lịch đặt sân!"
                    )
                else:
                    response.raise_for_status()

        except (httpx.ConnectError, httpx.ConnectTimeout) as ex:
            last_exception = ex
            logger.warning(f"Lần {attempt} thất bại do lỗi kết nối mạng (Connection refused): {ex}")
            if attempt < settings.MAX_RETRIES:
                wait_time = settings.RETRY_BACKOFF_FACTOR ** attempt
                logger.info(f"Tạm dừng {wait_time:.1f}s trước khi thử lại...")
                await asyncio.sleep(wait_time)

        except httpx.ReadTimeout as ex:
            logger.error(f"Thời gian chờ Field Service vượt quá {timeout} giây (ReadTimeout)!")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Field Service phản hồi vượt quá {timeout} giây. Hệ thống tự động ngắt kết nối (504 Gateway Timeout)!"
            )

    # Nếu sau 3 lần retry vẫn không kết nối được
    logger.error("Đã thử 3 lần nhưng không thể kết nối tới Field Service. Kích hoạt xử lý 503 Service Unavailable!")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Hệ thống quản lý sân thể thao hiện đang bảo trì hoặc mất kết nối. Vui lòng thử lại sau ít phút!"
    )

@app.post("/api/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, tags=["Bookings"])
async def create_booking(req: BookingRequest, delay_test: int = 0):
    """
    Endpoint tiếp nhận yêu cầu đặt sân.
    1. Gọi sang Field Service kiểm tra sân.
    2. Nếu sân tồn tại (200 OK): Lưu đơn, bắn sự kiện RabbitMQ, trả về 201 Created.
    3. Nếu không tìm thấy (404 Not Found): Trả về lỗi, không lưu đơn.
    4. Nếu mất mạng: Trả về 503 Service Unavailable.
    5. Nếu trễ > 3s: Trả về 504 Gateway Timeout.
    """
    # 1. Xác thực thông tin sân bãi qua Field Service
    field_data = await fetch_field_with_retry(req.fieldId, timeout=settings.READ_TIMEOUT, simulate_delay=delay_test)

    # 2. Tính toán tiền và lưu đơn đặt sân
    price_per_hour = field_data.get("pricePerHour", 0.0)
    # Giả định ca đặt 2 tiếng
    total_amount = price_per_hour * 2.0
    booking_id = f"BK-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"

    booking_record = {
        "bookingId": booking_id,
        "customerId": req.customerId,
        "fieldId": req.fieldId,
        "fieldName": field_data.get("name", "N/A"),
        "totalAmount": total_amount,
        "status": "CONFIRMED",
        "createdAt": datetime.now().isoformat()
    }
    BOOKINGS_DB[booking_id] = booking_record
    logger.info(f"Đã lưu thành công đơn đặt sân: {booking_id} vào Database.")

    # 3. Bắn sự kiện BookingCreated vào RabbitMQ
    event_payload = {
        "event": "BookingCreated",
        "bookingId": booking_id,
        "fieldId": req.fieldId,
        "customerId": req.customerId,
        "fieldName": field_data.get("name"),
        "totalAmount": total_amount,
        "timestamp": datetime.now().isoformat()
    }
    publish_to_rabbitmq(event_payload)

    return booking_record

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("booking_service:app", host="0.0.0.0", port=8080, reload=False)
