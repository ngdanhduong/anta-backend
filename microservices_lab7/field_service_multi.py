# -*- coding: utf-8 -*-
"""
Field Service Multi-Instance (Provider)
Hỗ trợ chạy đồng thời nhiều instance (ví dụ: port 8081 và 8082),
tự động đăng ký vào Service Registry (Eureka) và cung cấp endpoint /instance-info.
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import asyncio
import os
import sys
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FieldService")

# Cấu hình cổng và thông tin instance
PORT = int(os.getenv("PORT", "8081"))
SERVICE_NAME = "FIELD-SERVICE"
INSTANCE_ID = f"field-service:{PORT}"
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8761")

app = FastAPI(
    title=f"Field Service Instance ({PORT})",
    description="Dịch vụ quản lý sân thể thao có khả năng mở rộng ngang (Horizontal Scaling)",
    version="1.0.0"
)

class FieldResponse(BaseModel):
    id: str
    name: str
    sportType: str
    pricePerHour: float
    status: str

# Dữ liệu dùng chung giữa các instance (bảo đảm tính nhất quán)
FIELDS_DB = {
    "f-101": {
        "id": "f-101",
        "name": "Sân bóng đá cỏ nhân tạo 7 người - Sân A",
        "sportType": "FOOTBALL",
        "pricePerHour": 350000.0,
        "status": "AVAILABLE"
    },
    "f-102": {
        "id": "f-102",
        "name": "Sân Pickleball tiêu chuẩn quốc tế - Sân 1",
        "sportType": "PICKLEBALL",
        "pricePerHour": 180000.0,
        "status": "AVAILABLE"
    }
}

@app.get("/api/v1/instance-info", tags=["Instance Info"])
async def get_instance_info():
    """
    Endpoint trả về thông tin định danh instance phục vụ kiểm thử Load Balancing
    """
    return {
        "serviceName": SERVICE_NAME,
        "instanceId": INSTANCE_ID,
        "host": "localhost",
        "port": PORT,
        "status": "UP"
    }

@app.get("/api/v1/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
async def get_field_by_id(field_id: str):
    """
    Lấy thông tin chi tiết sân thể thao
    """
    logger.info(f"[{INSTANCE_ID}] Đang xử lý truy vấn sân: {field_id}")
    field = FIELDS_DB.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sân thể thao với mã '{field_id}' không tồn tại!"
        )
    return field

async def register_to_registry():
    """
    Tự động đăng ký instance vào Eureka Server khi khởi động
    """
    payload = {
        "instanceId": INSTANCE_ID,
        "serviceName": SERVICE_NAME,
        "host": "localhost",
        "port": PORT,
        "healthUrl": f"http://localhost:{PORT}/api/v1/instance-info",
        "status": "UP"
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{REGISTRY_URL}/eureka/apps/{SERVICE_NAME}", json=payload)
            if resp.status_code == 201:
                logger.info(f"[{INSTANCE_ID}] ĐĂNG KÝ THÀNH CÔNG VÀO SERVICE REGISTRY ({REGISTRY_URL})")
    except Exception as e:
        logger.warning(f"[{INSTANCE_ID}] Không thể kết nối Service Registry lúc này: {e}")

async def heartbeat_loop():
    """
    Gửi Heartbeat định kỳ 10 giây duy trì trạng thái 'UP'
    """
    while True:
        await asyncio.sleep(10)
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.put(f"{REGISTRY_URL}/eureka/apps/{SERVICE_NAME}/{INSTANCE_ID}")
        except Exception:
            pass

@app.on_event("startup")
async def on_startup():
    await register_to_registry()
    asyncio.create_task(heartbeat_loop())

@app.on_event("shutdown")
async def on_shutdown():
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.delete(f"{REGISTRY_URL}/eureka/apps/{SERVICE_NAME}/{INSTANCE_ID}")
            logger.info(f"[{INSTANCE_ID}] Đã hủy đăng ký khỏi Service Registry.")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    # Nhận cổng từ dòng lệnh nếu có (ví dụ: python field_service_multi.py 8082)
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
        INSTANCE_ID = f"field-service:{PORT}"
    uvicorn.run("field_service_multi:app", host="0.0.0.0", port=PORT, reload=False)
