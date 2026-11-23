# PHÂN HỆ GIAO DIỆN WEB (FRONTEND) - ANTA SPORTS PLATFORM

Thư mục `frontend/` chứa toàn bộ các giao diện người dùng trên nền tảng Web chính thức của dự án **Anta**:

---

## 📂 Cấu trúc thư mục

```
frontend/
├── index.html                   # Trang điều hướng tập trung vào 2 cổng Web Anta
├── admin/                       # Cổng Quản Trị Hệ Thống (Anta Admin Portal)
│   ├── index.html               # Giao diện đăng nhập & quản trị tài khoản, cơ sở
│   ├── app.js                   # Logic xử lý gọi API Quản trị (/api/v1)
│   └── style.css                # Style giao diện Quản trị
│
└── owner/                       # Cổng Dành Cho Chủ Sân (Anta Venue Owner Portal)
    ├── index.html               # Giao diện vận hành lịch sân, duyệt đơn, check-in
    ├── app.js                   # Logic xử lý gọi API Kênh chủ sân (/api/v1/owner/*)
    └── style.css                # Style giao diện Kênh chủ sân
```

---

## 🚀 Hướng dẫn mở và sử dụng

* Mở file `frontend/index.html` trong trình duyệt.
* Hoặc truy cập trực tiếp:
  - **Quản trị Anta:** [frontend/admin/index.html](admin/index.html)
  - **Kênh Chủ sân Anta:** [frontend/owner/index.html](owner/index.html)

---

## 🌐 Kết nối API Microservices

Tất cả các trang Web khi gửi nhận dữ liệu động đều kết nối qua **API Gateway** tại:
* **API Gateway URL**: `http://localhost:8080/api/v1`
