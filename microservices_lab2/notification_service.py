# -*- coding: utf-8 -*-
"""
Notification Service (Event Consumer)
Lắng nghe sự kiện từ hàng đợi RabbitMQ (queue: notification.booking.queue)
và in ra console thông báo nhận đơn đặt sân mới.
"""
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NotificationService")

def handle_booking_created_event(event_data: dict):
    """
    Xử lý sự kiện BookingCreated nhận được từ hàng đợi RabbitMQ
    """
    print("\n" + "=" * 65)
    print("📢 [NOTIFICATION SERVICE] NHẬN ĐƯỢC THÔNG BÁO ĐƠN ĐẶT SÂN MỚI!")
    print(f" ➔ Mã đơn (Booking ID) : {event_data.get('bookingId')}")
    print(f" ➔ Khách hàng          : {event_data.get('customerId')}")
    print(f" ➔ Tên sân thể thao    : {event_data.get('fieldName')}")
    print(f" ➔ Tổng tiền cọc       : {event_data.get('totalAmount'):,.0f} VNĐ")
    print(f" ➔ Thời gian sự kiện   : {event_data.get('timestamp')}")
    print(" ➔ Hành động tự động   : Đang gửi tin nhắn SMS / Email xác nhận...")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    print("[NOTIFICATION SERVICE] Đang lắng nghe trên queue 'notification.booking.queue'...")
    # Giả lập mẫu khi nhận được tin nhắn
    sample_event = {
        "event": "BookingCreated",
        "bookingId": "BK-202610-A91F",
        "fieldId": "f-101",
        "customerId": "cust-889",
        "fieldName": "Sân bóng đá cỏ nhân tạo 7 người - Sân A",
        "totalAmount": 700000.0,
        "timestamp": datetime.now().isoformat()
    }
    handle_booking_created_event(sample_event)
