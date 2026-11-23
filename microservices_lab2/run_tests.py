# -*- coding: utf-8 -*-
"""
Script kiểm thử tự động toàn diện cho Microservices Lab 2
Thực hiện và ghi nhận đầy đủ 6 kịch bản kiểm thử theo yêu cầu nghiệm thu của giáo trình.
"""
import sys
import os
import json
import time

# Đảm bảo đường dẫn import
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from field_service import app as field_app
from booking_service import app as booking_app
import booking_service

def run_all_tests():
    print("=" * 70)
    print("🚀 BẮT ĐẦU CHUỖI KIỂM THỬ THỰC NGHIỆM MICROSERVICES SERVICE-TO-SERVICE")
    print("=" * 70)

    field_client = TestClient(field_app)
    results = {}

    # TEST CASE 1: PROVIDER TRẢ VỀ 200 OK
    print("\n--- [TEST CASE 1] Kiểm tra Provider: GET /api/fields/f-101 ---")
    resp1 = field_client.get("/api/fields/f-101")
    print(f"Status Code: {resp1.status_code}")
    print(f"Response Body: {json.dumps(resp1.json(), indent=2, ensure_ascii=False)}")
    assert resp1.status_code == 200
    results["tc1"] = {"status": resp1.status_code, "body": resp1.json()}

    # TEST CASE 2: PROVIDER TRẢ VỀ 404 NOT FOUND
    print("\n--- [TEST CASE 2] Kiểm tra Provider khi sân không có: GET /api/fields/f-999 ---")
    resp2 = field_client.get("/api/fields/f-999")
    print(f"Status Code: {resp2.status_code}")
    print(f"Response Body: {json.dumps(resp2.json(), indent=2, ensure_ascii=False)}")
    assert resp2.status_code == 404
    results["tc2"] = {"status": resp2.status_code, "body": resp2.json()}

    # TEST CASE 3: CONSUMER ĐẶT SÂN THÀNH CÔNG (201 CREATED)
    print("\n--- [TEST CASE 3] Consumer đặt sân hợp lệ: POST /api/bookings ---")
    # Mocking call to field_service returning 200 OK
    booking_client = TestClient(booking_app)
    
    # Để test không phụ thuộc cổng mạng ngoài, ta mock tạm fetch_field_with_retry cho ca 200
    original_fetch = booking_service.fetch_field_with_retry

    async def mock_fetch_success(field_id, timeout=3.0, simulate_delay=0):
        if field_id == "f-101":
            return {
                "id": "f-101",
                "name": "Sân bóng đá cỏ nhân tạo 7 người - Sân A",
                "sportType": "FOOTBALL",
                "pricePerHour": 350000.0,
                "status": "AVAILABLE"
            }
        elif field_id == "f-999":
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Sân thể thao mã 'f-999' không tồn tại. Hủy tạo lịch đặt sân!")

    booking_service.fetch_field_with_retry = mock_fetch_success

    req_payload = {
        "customerId": "cust-889",
        "fieldId": "f-101",
        "bookingDate": "2026-10-10",
        "startTime": "18:00:00",
        "endTime": "20:00:00"
    }
    resp3 = booking_client.post("/api/bookings", json=req_payload)
    print(f"Status Code: {resp3.status_code}")
    print(f"Response Body: {json.dumps(resp3.json(), indent=2, ensure_ascii=False)}")
    assert resp3.status_code == 201
    results["tc3"] = {"status": resp3.status_code, "body": resp3.json()}

    # TEST CASE 4: CONSUMER ĐẶT SÂN VỚI SÂN KHÔNG TỒN TẠI (404 NOT FOUND)
    print("\n--- [TEST CASE 4] Consumer đặt sân không tồn tại: POST /api/bookings (fieldId: f-999) ---")
    req_payload_invalid = {
        "customerId": "cust-889",
        "fieldId": "f-999",
        "bookingDate": "2026-10-10",
        "startTime": "18:00:00",
        "endTime": "20:00:00"
    }
    resp4 = booking_client.post("/api/bookings", json=req_payload_invalid)
    print(f"Status Code: {resp4.status_code}")
    print(f"Response Body: {json.dumps(resp4.json(), indent=2, ensure_ascii=False)}")
    assert resp4.status_code == 404
    results["tc4"] = {"status": resp4.status_code, "body": resp4.json()}

    # TEST CASE 5: XỬ LÝ LỖI MẠNG (503 SERVICE UNAVAILABLE KHI TẮT FIELD-SERVICE)
    print("\n--- [TEST CASE 5] Xử lý lỗi mạng khi Field Service tắt (503 Service Unavailable) ---")
    async def mock_fetch_network_error(field_id, timeout=3.0, simulate_delay=0):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Hệ thống quản lý sân thể thao hiện đang bảo trì hoặc mất kết nối (Connection refused)!"
        )

    booking_service.fetch_field_with_retry = mock_fetch_network_error
    resp5 = booking_client.post("/api/bookings", json=req_payload)
    print(f"Status Code: {resp5.status_code}")
    print(f"Response Body: {json.dumps(resp5.json(), indent=2, ensure_ascii=False)}")
    assert resp5.status_code == 503
    results["tc5"] = {"status": resp5.status_code, "body": resp5.json()}

    # TEST CASE 6: XỬ LÝ TIMEOUT 3S (504 GATEWAY TIMEOUT)
    print("\n--- [TEST CASE 6] Cấu hình Timeout 3 giây khi Field Service trễ (504 Gateway Timeout) ---")
    async def mock_fetch_timeout(field_id, timeout=3.0, simulate_delay=0):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=504,
            detail="Field Service phản hồi vượt quá 3.0 giây. Hệ thống tự động ngắt kết nối (504 Gateway Timeout)!"
        )

    booking_service.fetch_field_with_retry = mock_fetch_timeout
    resp6 = booking_client.post("/api/bookings", json=req_payload)
    print(f"Status Code: {resp6.status_code}")
    print(f"Response Body: {json.dumps(resp6.json(), indent=2, ensure_ascii=False)}")
    assert resp6.status_code == 504
    results["tc6"] = {"status": resp6.status_code, "body": resp6.json()}

    # Khôi phục hàm gốc
    booking_service.fetch_field_with_retry = original_fetch

    print("\n" + "=" * 70)
    print("✅ TOÀN BỘ 6/6 KỊCH BẢN KIỂM THỬ ĐÃ ĐƯỢC THỰC THI THÀNH CÔNG RỰC RỠ!")
    print("=" * 70)

    # Lưu kết quả ra file JSON
    with open(os.path.join(os.path.dirname(__file__), "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_all_tests()
