# -*- coding: utf-8 -*-
"""
Booking Service (Consumer) sử dụng Service Discovery & Client-side Load Balancing
Thay vì gọi cứng địa chỉ IP/Port, Booking Service tra cứu Service ID 'FIELD-SERVICE'
từ Eureka Registry và phân phối tải xoay vòng (Round-Robin).
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import httpx
import os
import itertools
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BookingService")

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8761")
app = FastAPI(
    title="Booking Service (Consumer with Service Discovery)",
    description="Dịch vụ đặt sân thể thao tích hợp Service Discovery & Load Balancing",
    version="1.0.0"
)

class BookingRequest(BaseModel):
    customerId: str = Field(..., example="cust-889")
    fieldId: str = Field(..., example="f-101")
    bookingDate: str = Field(..., example="2026-10-10")
    startTime: str = Field(..., example="18:00:00")
    endTime: str = Field(..., example="20:00:00")

# Bộ đếm phục vụ thuật toán Round-Robin Load Balancing
_round_robin_counter = itertools.count()

async def discover_and_call_field_service(field_id: str) -> tuple[dict, str]:
    """
    1. Khám phá (Discovery) danh sách instances của 'FIELD-SERVICE' từ Eureka Server
    2. Cân bằng tải phía Client (Client-side Load Balancing) theo giải thuật Round-Robin
    3. Thực hiện gọi HTTP tới instance được chọn
    """
    # Bước 1: Tra cứu Registry
    discovery_url = f"{REGISTRY_URL}/eureka/apps/FIELD-SERVICE"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(discovery_url)
            if resp.status_code == 404 or resp.status_code == 503:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Không tìm thấy instance khả dụng nào của [FIELD-SERVICE] trong Service Registry!"
                )
            data = resp.json()
            instances = data.get("instances", [])
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối tới Service Registry (Eureka Server)! Hệ thống tạm dừng phục vụ."
        )

    if not instances:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tất cả các instance của [FIELD-SERVICE] đều đang ngoại tuyến!"
        )

    # Bước 2: Chọn instance theo Round-Robin
    idx = next(_round_robin_counter) % len(instances)
    selected_instance = instances[idx]
    target_host = selected_instance["host"]
    target_port = selected_instance["port"]
    instance_id = selected_instance["instanceId"]

    target_url = f"http://{target_host}:{target_port}/api/v1/fields/{field_id}"
    logger.info(f"[LOAD BALANCER] Yêu cầu được định tuyến tới instance: {instance_id} ({target_url})")

    # Bước 3: Gọi API tới instance được chọn
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            field_resp = await client.get(target_url)
            if field_resp.status_code == 200:
                return field_resp.json(), instance_id
            elif field_resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sân thể thao mã '{field_id}' không tồn tại!"
                )
            else:
                raise HTTPException(status_code=field_resp.status_code, detail="Lỗi từ Field Service")
    except httpx.ConnectError:
        # Nếu instance vừa chọn bị lỗi, ta có thể thử instance tiếp theo
        logger.warning(f"[FAILOVER] Instance {instance_id} không phản hồi! Đang thử lại...")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Instance {instance_id} vừa bị ngắt kết nối. Vui lòng gửi lại yêu cầu!"
        )

@app.post("/api/bookings", status_code=status.HTTP_201_CREATED, tags=["Bookings"])
async def create_booking(req: BookingRequest):
    """
    Tạo đơn đặt sân thông qua Service Discovery
    """
    field_data, handled_by_instance = await discover_and_call_field_service(req.fieldId)

    booking_id = f"BK-DISC-{os.urandom(4).hex().upper()}"
    return {
        "bookingId": booking_id,
        "customerId": req.customerId,
        "fieldId": req.fieldId,
        "fieldName": field_data["name"],
        "pricePerHour": field_data["pricePerHour"],
        "status": "CONFIRMED",
        "handledByInstance": handled_by_instance,
        "createdAt": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("booking_service_discovery:app", host="0.0.0.0", port=8080, reload=False)
