# -*- coding: utf-8 -*-
"""
Field Service (Provider) - Port 8081
Quản lý danh mục sân thể thao, giá thuê và trạng thái khả dụng.
"""
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel
import asyncio
import uvicorn

app = FastAPI(
    title="Field Service (Provider)",
    description="Dịch vụ quản lý thông tin sân thể thao (Alobo Court Catalog)",
    version="1.0.0"
)

class FieldResponse(BaseModel):
    id: str
    name: str
    sportType: str
    pricePerHour: float
    status: str

# Cơ sở dữ liệu mẫu trong bộ nhớ
FIELDS_DB: dict[str, dict] = {
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
    },
    "f-103": {
        "id": "f-103",
        "name": "Sân cầu lông thảm Taraflex - Sân B",
        "sportType": "BADMINTON",
        "pricePerHour": 120000.0,
        "status": "MAINTENANCE"
    }
}

@app.get("/api/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
async def get_field_by_id(field_id: str, delay: int = Query(0, description="Giả lập độ trễ mạng (giây)")):
    """
    Endpoint cung cấp thông tin sân bãi theo ID.
    - Trả về 200 OK kèm thông tin JSON nếu tìm thấy sân.
    - Trả về 404 Not Found nếu ID sân không tồn tại.
    - Hỗ trợ tham số ?delay=<giây> để giả lập phản hồi chậm nhằm kiểm thử Timeout.
    """
    if delay > 0:
        await asyncio.sleep(delay)

    field = FIELDS_DB.get(field_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sân thể thao với mã '{field_id}' không tồn tại trong hệ thống!"
        )
    return field

if __name__ == "__main__":
    uvicorn.run("field_service:app", host="0.0.0.0", port=8081, reload=False)
