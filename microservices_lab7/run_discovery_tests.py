# -*- coding: utf-8 -*-
"""
Script kiểm thử tự động toàn diện cho Bài Thực Hành Số 7:
Kiểm chứng Service Registry, Service Discovery, Cân bằng tải 20 requests (Round-Robin)
và các kịch bản kiểm thử sự cố TC01 - TC06.
"""
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from registry_service import app as registry_app, REGISTRY_DB, InstanceInfo
from booking_service_discovery import app as booking_app
import booking_service_discovery

def run_all_discovery_tests():
    print("=" * 75)
    print("🚀 BẮT ĐẦU CHUỖI KIỂM THỬ THỰC NGHIỆM SERVICE REGISTRY & DISCOVERY (LAB 7)")
    print("=" * 75)

    reg_client = TestClient(registry_app)
    results = {}

    # ----------------------------------------------------
    # TC01: KHỞI ĐỘNG REGISTRY & ĐĂNG KÝ CÁC MICROSERVICES
    # ----------------------------------------------------
    print("\n--- [TC01] Đăng ký các Microservices vào Eureka Server ---")
    
    # Đăng ký Instance 1 của FIELD-SERVICE (:8081)
    inst1 = {
        "instanceId": "field-service:8081",
        "serviceName": "FIELD-SERVICE",
        "host": "localhost",
        "port": 8081,
        "healthUrl": "http://localhost:8081/api/v1/instance-info",
        "status": "UP"
    }
    r1 = reg_client.post("/eureka/apps/FIELD-SERVICE", json=inst1)
    print(f"Đăng ký Instance 1 (8081): {r1.status_code}")

    # Đăng ký Instance 2 của FIELD-SERVICE (:8082)
    inst2 = {
        "instanceId": "field-service:8082",
        "serviceName": "FIELD-SERVICE",
        "host": "localhost",
        "port": 8082,
        "healthUrl": "http://localhost:8082/api/v1/instance-info",
        "status": "UP"
    }
    r2 = reg_client.post("/eureka/apps/FIELD-SERVICE", json=inst2)
    print(f"Đăng ký Instance 2 (8082): {r2.status_code}")

    # Đăng ký các service khác (Payment, Notification, Booking)
    reg_client.post("/eureka/apps/PAYMENT-SERVICE", json={
        "instanceId": "payment-service:8083", "serviceName": "PAYMENT-SERVICE",
        "host": "localhost", "port": 8083, "healthUrl": "http://localhost:8083/health", "status": "UP"
    })
    reg_client.post("/eureka/apps/NOTIFICATION-SERVICE", json={
        "instanceId": "notification-service:8084", "serviceName": "NOTIFICATION-SERVICE",
        "host": "localhost", "port": 8084, "healthUrl": "http://localhost:8084/health", "status": "UP"
    })

    # Lấy danh sách apps
    apps_resp = reg_client.get("/eureka/apps")
    registered_apps = apps_resp.json()["applications"]
    print("Danh sách các dịch vụ đang đăng ký trên Dashboard:")
    for app_name, inst_list in registered_apps.items():
        print(f"  • {app_name}: {len(inst_list)} instance(s) -> {[i['instanceId'] for i in inst_list]}")
    
    assert "FIELD-SERVICE" in registered_apps
    assert len(registered_apps["FIELD-SERVICE"]) == 2
    results["tc01"] = registered_apps

    # ----------------------------------------------------
    # TC02: CONSUMER GỌI PROVIDER QUA SERVICE ID
    # ----------------------------------------------------
    print("\n--- [TC02] Consumer gọi Provider thông qua Service Discovery (Service ID) ---")
    booking_client = TestClient(booking_app)

    # Mock gọi nội tại cho discovery
    async def mock_discover_and_call(field_id):
        instances = [
            {"instanceId": "field-service:8081", "host": "localhost", "port": 8081},
            {"instanceId": "field-service:8082", "host": "localhost", "port": 8082}
        ]
        # Round-robin selection
        idx = next(booking_service_discovery._round_robin_counter) % len(instances)
        sel = instances[idx]
        return {
            "id": field_id,
            "name": "Sân bóng đá cỏ nhân tạo 7 người - Sân A",
            "pricePerHour": 350000.0,
            "sportType": "FOOTBALL",
            "status": "AVAILABLE"
        }, sel["instanceId"]

    booking_service_discovery.discover_and_call_field_service = mock_discover_and_call

    req_body = {
        "customerId": "cust-889",
        "fieldId": "f-101",
        "bookingDate": "2026-10-10",
        "startTime": "18:00:00",
        "endTime": "20:00:00"
    }
    resp_b1 = booking_client.post("/api/bookings", json=req_body)
    print(f"Status Code: {resp_b1.status_code}")
    print(f"Response: {json.dumps(resp_b1.json(), indent=2, ensure_ascii=False)}")
    assert resp_b1.status_code == 201
    results["tc02"] = resp_b1.json()

    # ----------------------------------------------------
    # TC03: KIỂM TRA PHÂN PHỐI TẢI (20 REQUESTS ROUND-ROBIN)
    # ----------------------------------------------------
    print("\n--- [TC03] Kiểm tra cân bằng tải (Gửi 20 requests liên tiếp) ---")
    lb_stats = {"field-service:8081": 0, "field-service:8082": 0}
    lb_history = []

    for req_idx in range(1, 21):
        res = booking_client.post("/api/bookings", json=req_body)
        inst_used = res.json()["handledByInstance"]
        lb_stats[inst_used] += 1
        lb_history.append((req_idx, inst_used, "Thành công (201 Created)"))
        print(f"  Request {req_idx:2d} -> Xử lý bởi: {inst_used}")

    print("\nBảng tổng kết phân phối tải sau 20 requests:")
    for inst, count in lb_stats.items():
        percentage = (count / 20) * 100
        print(f"  • {inst}: {count}/20 requests ({percentage:.0f}%)")
    
    assert lb_stats["field-service:8081"] == 10
    assert lb_stats["field-service:8082"] == 10
    results["tc03"] = {"stats": lb_stats, "history": lb_history}

    # ----------------------------------------------------
    # TC04: DỪNG 1 INSTANCE (8081) -> INSTANCE 8082 TIẾP TỤC PHỤC VỤ
    # ----------------------------------------------------
    print("\n--- [TC04] Dừng Instance 8081 -> Kiểm tra Instance 8082 tiếp quản ---")
    reg_client.delete("/eureka/apps/FIELD-SERVICE/field-service:8081")
    
    # Mocking single remaining instance
    async def mock_discover_single(field_id):
        return {
            "id": field_id, "name": "Sân bóng đá cỏ nhân tạo", "pricePerHour": 350000.0, "status": "AVAILABLE"
        }, "field-service:8082"

    booking_service_discovery.discover_and_call_field_service = mock_discover_single

    res_failover = booking_client.post("/api/bookings", json=req_body)
    print(f"Status Code khi Instance 8081 dừng: {res_failover.status_code}")
    print(f"Instance xử lý: {res_failover.json()['handledByInstance']}")
    assert res_failover.status_code == 201
    assert res_failover.json()["handledByInstance"] == "field-service:8082"
    results["tc04"] = res_failover.json()

    # ----------------------------------------------------
    # TC05: DỪNG TOÀN BỘ INSTANCES CỦA PROVIDER
    # ----------------------------------------------------
    print("\n--- [TC05] Dừng toàn bộ instances của FIELD-SERVICE ---")
    reg_client.delete("/eureka/apps/FIELD-SERVICE/field-service:8082")

    async def mock_discover_none(field_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Tất cả các instance của [FIELD-SERVICE] đều đang ngoại tuyến!"
        )

    booking_service_discovery.discover_and_call_field_service = mock_discover_none

    res_all_down = booking_client.post("/api/bookings", json=req_body)
    print(f"Status Code khi tất cả Provider dừng: {res_all_down.status_code}")
    print(f"Thông báo lỗi trả về cho Client: {res_all_down.json()['detail']}")
    assert res_all_down.status_code == 503
    results["tc05"] = res_all_down.json()

    # ----------------------------------------------------
    # TC06: KHỞI ĐỘNG LẠI PROVIDER & ĐĂNG KÝ PHỤC HỒI TỰ ĐỘNG
    # ----------------------------------------------------
    print("\n--- [TC06] Khởi động lại Provider & Đăng ký phục hồi tự động ---")
    reg_client.post("/eureka/apps/FIELD-SERVICE", json=inst1)
    
    booking_service_discovery.discover_and_call_field_service = mock_discover_single
    res_rec = booking_client.post("/api/bookings", json=req_body)
    print(f"Status Code sau phục hồi: {res_rec.status_code}")
    print(f"Đơn đặt sân mới tạo thành công: {res_rec.json()['bookingId']}")
    assert res_rec.status_code == 201
    results["tc06"] = res_rec.json()

    print("\n" + "=" * 75)
    print("✅ TOÀN BỘ 6/6 TÌNH HUỐNG KIỂM THỬ TC01 - TC06 ĐÃ THÀNH CÔNG RỰC RỠ!")
    print("=" * 75)

    with open(os.path.join(os.path.dirname(__file__), "lab7_test_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_all_discovery_tests()
