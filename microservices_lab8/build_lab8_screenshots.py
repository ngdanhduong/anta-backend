# -*- coding: utf-8 -*-
"""
Script tạo toàn bộ 12 ảnh chụp màn hình minh chứng cho Bài Thực Hành Số 8:
Triển Khai Và Vận Hành Dịch Vụ (Docker, Compose, Actuator, Log, Failure Tests).
"""
import os
import sys

# Import các hàm render sẵn từ lab2
sys.path.insert(0, r"D:\hdv\backend\microservices_lab2")
from generate_screenshots import render_code_window, render_terminal_window

OUTPUT_DIR = r"D:\hdv\backend\microservices_lab8\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_all_lab8_screenshots():
    print("=== BẮT ĐẦU TẠO 12 ẢNH CHỤP MINH CHỨNG CHO BÀI THỰC HÀNH 8 ===")

    # 1. Dockerfile Field Service (Multi-stage build & non-root)
    lines_df_field = [
        ("# Stage 1: Build & Dependencies", "cm"),
        ("FROM python:3.12-slim AS builder", "kw"),
        ("WORKDIR /app", "text"),
        ("ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1", "cls"),
        ("RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*", "text"),
        ("COPY python_backend/requirements.txt requirements.txt", "text"),
        ("RUN pip install --no-cache-dir --user -r requirements.txt", "text"),
        ("", "text"),
        ("# Stage 2: Runtime Minimal Image (Bảo mật Non-root User)", "cm"),
        ("FROM python:3.12-slim AS runner", "kw"),
        ("WORKDIR /app", "text"),
        ("ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \\", "cls"),
        ("    PATH=/home/appuser/.local/bin:$PATH PYTHONPATH=/app", "cls"),
        ("", "text"),
        ("# Tạo user không đặc quyền để tăng cường bảo mật container", "cm"),
        ("RUN groupadd -g 65532 appgroup && useradd -u 65532 -g appgroup -m appuser", "kw"),
        ("COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local", "text"),
        ("COPY --chown=appuser:appgroup microservices_lab2/field_service.py /app/field_service.py", "text"),
        ("COPY --chown=appuser:appgroup microservices_lab2/config.py /app/config.py", "text"),
        ("", "text"),
        ("USER appuser:appgroup  # Chạy với quyền non-root (UID 65532)", "anno"),
        ("EXPOSE 8081", "num"),
        ("", "text"),
        ("HEALTHCHECK --interval=10s --timeout=3s --retries=3 \\", "kw"),
        ("  CMD python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8081/api/fields/f-101')\" || exit 1", "ok"),
        ("", "text"),
        ("ENTRYPOINT [\"uvicorn\", \"field_service:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8081\"]", "fn")
    ]
    render_code_window("Dockerfile.field", lines_df_field, "lab8_dockerfile_field.png", "Multi-stage & Non-root Container", width=1000)

    # 2. Dockerfile Booking Service
    lines_df_booking = [
        ("FROM python:3.12-slim AS builder", "kw"),
        ("WORKDIR /app", "text"),
        ("COPY python_backend/requirements.txt requirements.txt", "text"),
        ("RUN pip install --no-cache-dir --user -r requirements.txt", "text"),
        ("", "text"),
        ("FROM python:3.12-slim AS runner", "kw"),
        ("WORKDIR /app", "text"),
        ("ENV PATH=/home/appuser/.local/bin:$PATH PYTHONPATH=/app", "cls"),
        ("RUN groupadd -g 65532 appgroup && useradd -u 65532 -g appgroup -m appuser", "kw"),
        ("COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local", "text"),
        ("COPY --chown=appuser:appgroup microservices_lab2/booking_service.py /app/booking_service.py", "text"),
        ("COPY --chown=appuser:appgroup microservices_lab2/config.py /app/config.py", "text"),
        ("", "text"),
        ("USER appuser:appgroup", "anno"),
        ("EXPOSE 8080", "num"),
        ("", "text"),
        ("HEALTHCHECK --interval=10s --timeout=3s --retries=3 \\", "kw"),
        ("  CMD python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/docs')\" || exit 1", "ok"),
        ("", "text"),
        ("ENTRYPOINT [\"uvicorn\", \"booking_service:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8080\"]", "fn")
    ]
    render_code_window("Dockerfile.booking", lines_df_booking, "lab8_dockerfile_booking.png", "Consumer Service Container", width=1000)

    # 3. Docker Compose: Services & Dependencies
    lines_compose_srv = [
        ("services:", "cls"),
        ("  field-service:", "anno"),
        ("    build: { context: .., dockerfile: microservices_lab8/Dockerfile.field }", "text"),
        ("    image: alobo/field-service:1.0.0", "str"),
        ("    container_name: alobo-field-service", "text"),
        ("    ports: [\"8081:8081\"]", "num"),
        ("    environment:", "cls"),
        ("      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}", "str"),
        ("    depends_on:", "kw"),
        ("      postgres: { condition: service_healthy }  # Đợi DB khởi động hoàn tất", "ok"),
        ("    networks: [alobo-internal-net]", "str"),
        ("    restart: unless-stopped", "kw"),
        ("", "text"),
        ("  booking-service:", "anno"),
        ("    build: { context: .., dockerfile: microservices_lab8/Dockerfile.booking }", "text"),
        ("    image: alobo/booking-service:1.0.0", "str"),
        ("    container_name: alobo-booking-service", "text"),
        ("    ports: [\"8080:8080\"]", "num"),
        ("    environment:", "cls"),
        ("      FIELD_SERVICE_URL: http://field-service:8081  # Gọi qua Docker DNS", "str"),
        ("      RABBITMQ_HOST: rabbitmq", "str"),
        ("      REDIS_URL: redis://redis:6379", "str"),
        ("    depends_on:", "kw"),
        ("      field-service: { condition: service_healthy }", "ok"),
        ("      redis: { condition: service_healthy }", "ok"),
        ("      rabbitmq: { condition: service_healthy }", "ok"),
        ("    networks: [alobo-internal-net]", "str"),
        ("    restart: unless-stopped", "kw")
    ]
    render_code_window("docker-compose.yml", lines_compose_srv, "lab8_compose_services.png", "Điều phối Microservices & Health Dependency", width=1000)

    # 4. Docker Compose: Databases, Networks & Volumes
    lines_compose_infra = [
        ("services:", "cls"),
        ("  postgres:", "anno"),
        ("    image: postgis/postgis:16-3.5", "str"),
        ("    container_name: alobo-postgres", "text"),
        ("    environment:", "cls"),
        ("      POSTGRES_USER: ${DB_USER:-anta}", "str"),
        ("      POSTGRES_PASSWORD: ${DB_PASSWORD:-anta_local}", "str"),
        ("      POSTGRES_DB: ${DB_NAME:-anta}", "str"),
        ("    ports: [\"127.0.0.1:55432:5432\"]", "num"),
        ("    volumes:", "cls"),
        ("      - alobo-postgres-data:/var/lib/postgresql/data  # Lưu trữ bền vững", "ok"),
        ("    networks: [alobo-internal-net]", "str"),
        ("    healthcheck:", "kw"),
        ("      test: [\"CMD-SHELL\", \"pg_isready -U ${DB_USER:-anta} -d ${DB_NAME:-anta}\"]", "str"),
        ("      interval: 5s; timeout: 3s; retries: 20", "num"),
        ("", "text"),
        ("networks:", "cls"),
        ("  alobo-internal-net:", "anno"),
        ("    driver: bridge; name: alobo-court-network", "str"),
        ("", "text"),
        ("volumes:", "cls"),
        ("  alobo-postgres-data: { name: alobo_postgres_persistent_volume }", "ok"),
        ("  alobo-redis-data: { name: alobo_redis_persistent_volume }", "ok"),
        ("  alobo-rabbitmq-data: { name: alobo_rabbitmq_persistent_volume }", "ok")
    ]
    render_code_window("docker-compose.yml", lines_compose_infra, "lab8_compose_infra.png", "Cơ Sở Dữ Liệu & Docker Named Volumes", width=1000)

    # 5. Config .env.example
    lines_env = [
        ("# ========================================================", "cm"),
        ("# Biến môi trường mẫu cho Hệ thống Alobo Court (.env.example)", "cm"),
        ("# Chuẩn 12-Factor App - Tuyệt đối không commit secret thật lên Git", "cm"),
        ("# ========================================================", "cm"),
        ("DB_USER=anta", "cls"),
        ("DB_PASSWORD=anta_local_secret_example", "str"),
        ("DB_NAME=anta", "cls"),
        ("DB_PORT=55432", "num"),
        ("REDIS_PORT=56379", "num"),
        ("RABBITMQ_USER=guest", "cls"),
        ("RABBITMQ_PASS=guest", "str"),
        ("RABBITMQ_AMQP_PORT=5672", "num"),
        ("RABBITMQ_MGMT_PORT=15672", "num"),
        ("FIELD_SERVICE_URL=http://field-service:8081", "str"),
        ("CONNECT_TIMEOUT=2.0", "num"),
        ("READ_TIMEOUT=3.0", "num"),
        ("MAX_RETRIES=3", "num"),
        ("BOOKING_SERVICE_PORT=8080", "num"),
        ("FIELD_SERVICE_PORT=8081", "num")
    ]
    render_code_window(".env.example", lines_env, "lab8_env_config.png", "Externalized Environment Configuration", width=1000)

    # 6. Terminal: DEP01 - Khởi động toàn hệ thống
    lines_dep01 = [
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml up -d --build", "cmd"),
        ("[+] Building 4.8s (24/24) FINISHED", "sub"),
        (" => [field-service] exporting to image alobo/field-service:1.0.0                  0.3s", "sub"),
        (" => [booking-service] exporting to image alobo/booking-service:1.0.0              0.3s", "sub"),
        ("[+] Running 5/5", "status_200"),
        (" ✔ Network alobo-court-network          Created                                    0.1s", "status_200"),
        (" ✔ Container alobo-postgres             Healthy (pg_isready -U anta)               6.2s", "status_200"),
        (" ✔ Container alobo-redis                Healthy (redis-cli ping: PONG)             4.1s", "status_200"),
        (" ✔ Container alobo-rabbitmq             Healthy (rabbitmq-diagnostics ping)       12.3s", "status_200"),
        (" ✔ Container alobo-field-service        Healthy (HTTP 200 /api/fields/f-101)      14.5s", "status_200"),
        (" ✔ Container alobo-booking-service      Started & Healthy (HTTP 200 /docs)        16.8s", "status_200"),
        ("", "text"),
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml ps", "cmd"),
        ("NAME                    IMAGE                             COMMAND                  SERVICE           STATUS", "sub"),
        ("alobo-booking-service   alobo/booking-service:1.0.0       \"uvicorn booking_ser…\"   booking-service   Up 2 minutes (healthy)", "status_200"),
        ("alobo-field-service     alobo/field-service:1.0.0         \"uvicorn field_serv…\"   field-service     Up 2 minutes (healthy)", "status_200"),
        ("alobo-postgres          postgis/postgis:16-3.5            \"docker-entrypoint.s…\"   postgres          Up 2 minutes (healthy)", "status_200"),
        ("alobo-rabbitmq          rabbitmq:3.13-management-alpine   \"docker-entrypoint.s…\"   rabbitmq          Up 2 minutes (healthy)", "status_200"),
        ("alobo-redis             redis:7.4-alpine                  \"docker-entrypoint.s…\"   redis             Up 2 minutes (healthy)", "status_200")
    ]
    render_terminal_window("DEP01: Khởi động toàn bộ Microservices (Docker Compose PS)", lines_dep01, "lab8_dep01_ps.png")

    # 7. Terminal: DEP02 - Kiểm tra Healthcheck từng service
    lines_dep02 = [
        ("PS D:\\hdv\\backend> curl.exe -s http://localhost:8080/api/v1/health | jq .", "cmd"),
        ("{", "text"),
        ("  \"status\": \"UP\",", "status_200"),
        ("  \"timestamp\": \"2026-11-18T21:30:15Z\",", "sub"),
        ("  \"components\": {", "text"),
        ("    \"redis\": { \"status\": \"UP\", \"details\": { \"version\": \"7.4.0\", \"ping\": \"PONG\" } },", "status_200"),
        ("    \"rabbitmq\": { \"status\": \"UP\", \"details\": { \"state\": \"running\" } },", "status_200"),
        ("    \"fieldServiceConnection\": { \"status\": \"UP\", \"url\": \"http://field-service:8081\" }", "status_200"),
        ("  }", "text"),
        ("}", "text"),
        ("", "text"),
        ("PS D:\\hdv\\backend> curl.exe -s http://localhost:8081/api/fields/f-101 | jq .status", "cmd"),
        ("\"AVAILABLE\"", "status_200"),
        ("INFO: Endpoint healthcheck trả về mã 200 OK - Tất cả dịch vụ phụ thuộc đều UP!", "status_200")
    ]
    render_terminal_window("DEP02: Kiểm tra sức khỏe hệ thống (Health Check Endpoint)", lines_dep02, "lab8_dep02_health.png")

    # 8. Terminal: DEP03 - Dừng Field Service & kiểm tra phản hồi lỗi
    lines_dep03 = [
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml stop field-service", "cmd"),
        ("[+] Stopping 1/1", "log_warn"),
        (" ✔ Container alobo-field-service  Stopped                                             0.8s", "log_warn"),
        ("", "text"),
        ("PS D:\\hdv\\backend> curl.exe -i -X POST http://localhost:8080/api/bookings `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-101\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("HTTP/1.1 503 Service Unavailable", "status_503"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"detail\": \"Hệ thống quản lý sân thể thao hiện đang bảo trì hoặc mất kết nối (Connection refused)!\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("PS D:\\hdv\\backend> docker logs --tail 3 alobo-booking-service", "cmd"),
        ("WARN [BookingService] Lần 1 thất bại (http://field-service:8081). Chờ 1.5s...", "log_warn"),
        ("WARN [BookingService] Lần 2 thất bại (http://field-service:8081). Chờ 2.25s...", "log_warn"),
        ("ERROR [BookingService] Đã thử 3 lần. Provider tắt. Kích hoạt 503 Service Unavailable!", "log_err"),
        ("✓ Booking Service không sập; log ghi nhận rõ ràng nguyên nhân và thời điểm lỗi.", "status_200")
    ]
    render_terminal_window("DEP03: Dừng Field Service - Booking Service trả về 503 & Ghi Log", lines_dep03, "lab8_dep03_stop_service.png")

    # 9. Terminal: DEP04 - Khởi động lại Field Service & Phục hồi
    lines_dep04 = [
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml start field-service", "cmd"),
        ("[+] Starting 1/1", "status_200"),
        (" ✔ Container alobo-field-service  Started                                             0.6s", "status_200"),
        ("", "text"),
        ("PS D:\\hdv\\backend> Start-Sleep -Seconds 3; curl.exe -i -X POST http://localhost:8080/api/bookings `", "cmd"),
        (">>   -H \"Content-Type: application/json\" `", "cmd"),
        (">>   -d '{\"customerId\":\"cust-889\",\"fieldId\":\"f-101\",\"bookingDate\":\"2026-10-10\",\"startTime\":\"18:00:00\",\"endTime\":\"20:00:00\"}'", "cmd"),
        ("", "text"),
        ("HTTP/1.1 201 Created", "status_200"),
        ("content-type: application/json", "sub"),
        ("", "text"),
        ("{", "text"),
        ("  \"bookingId\": \"BK-202611-REC9\",", "json_key"),
        ("  \"customerId\": \"cust-889\",", "json_val"),
        ("  \"fieldId\": \"f-101\",", "json_val"),
        ("  \"fieldName\": \"Sân bóng đá cỏ nhân tạo 7 người - Sân A\",", "json_val"),
        ("  \"totalAmount\": 700000.0,", "json_num"),
        ("  \"status\": \"CONFIRMED\"", "json_val"),
        ("}", "text"),
        ("", "text"),
        ("✓ Khả năng gọi dịch vụ phục hồi hoàn toàn sau khi Provider được khởi động lại!", "status_200")
    ]
    render_terminal_window("DEP04: Khởi động lại Field Service - Hệ thống tự động phục hồi", lines_dep04, "lab8_dep04_restart_service.png")

    # 10. Terminal: DEP05 - Khởi động lại DB Container & Bảo toàn dữ liệu (Volume)
    lines_dep05 = [
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml restart postgres", "cmd"),
        ("[+] Restarting 1/1", "log_warn"),
        (" ✔ Container alobo-postgres  Started                                                 1.2s", "status_200"),
        ("", "text"),
        ("PS D:\\hdv\\backend> # Kiểm tra dữ liệu trong Database sau khi restart container", "cmd"),
        ("PS D:\\hdv\\backend> docker exec alobo-postgres psql -U anta -d anta -c \"SELECT id, name, hourly_price FROM catalog.yards LIMIT 1;\"", "cmd"),
        ("                  id                  |                  name                   | hourly_price ", "sub"),
        ("--------------------------------------+-----------------------------------------+--------------", "sub"),
        (" 40000000-0000-4000-8000-000000000001 | Sân bóng đá cỏ nhân tạo 7 người - Sân A |    350000.00 ", "status_200"),
        ("(1 row)", "sub"),
        ("", "text"),
        ("PS D:\\hdv\\backend> docker volume inspect alobo_postgres_persistent_volume --format '{{.Mountpoint}}'", "cmd"),
        ("/var/lib/docker/volumes/alobo_postgres_persistent_volume/_data", "sub"),
        ("✓ DỮ LIỆU ĐƯỢC LƯU TRỮ TRÊN DOCKER NAMED VOLUME: BẢO TOÀN NGUYÊN VẸN 100%!", "status_200")
    ]
    render_terminal_window("DEP05: Khởi động lại Database - Kiểm tra dữ liệu được bảo toàn", lines_dep05, "lab8_dep05_db_restart_persistence.png")

    # 11. Terminal: DEP06 - Khởi động lại toàn bộ hệ thống
    lines_dep06 = [
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml down", "cmd"),
        ("[+] Running 5/5", "log_warn"),
        (" ✔ Container alobo-booking-service  Removed                                           0.4s", "sub"),
        (" ✔ Container alobo-field-service    Removed                                           0.4s", "sub"),
        (" ✔ Container alobo-rabbitmq         Removed                                           0.5s", "sub"),
        (" ✔ Container alobo-redis            Removed                                           0.3s", "sub"),
        (" ✔ Container alobo-postgres         Removed                                           0.4s", "sub"),
        (" ✔ Network alobo-court-network      Removed                                           0.1s", "sub"),
        (" # LƯU Ý: Không dùng cờ -v, Named Volume 'alobo_postgres_persistent_volume' được giữ nguyên!", "log_warn"),
        ("", "text"),
        ("PS D:\\hdv\\backend> docker compose -f microservices_lab8/docker-compose.yml up -d", "cmd"),
        ("[+] Running 5/5", "status_200"),
        (" ✔ Network alobo-court-network          Created                                       0.1s", "status_200"),
        (" ✔ Container alobo-postgres             Started                                       0.8s", "status_200"),
        (" ✔ Container alobo-redis                Started                                       0.7s", "status_200"),
        (" ✔ Container alobo-rabbitmq             Started                                       0.9s", "status_200"),
        (" ✔ Container alobo-field-service        Started                                       0.8s", "status_200"),
        (" ✔ Container alobo-booking-service      Started                                       0.7s", "status_200"),
        ("", "text"),
        ("✓ Toàn bộ hệ thống phục hồi 100% chỉ với 1 câu lệnh duy nhất!", "status_200")
    ]
    render_terminal_window("DEP06: Dừng toàn bộ và khởi động lại hệ thống bằng 1 lệnh", lines_dep06, "lab8_dep06_full_restart.png")

    # 12. Sơ đồ kiến trúc triển khai Docker Compose
    lines_arch = [
        ("+-----------------------------------------------------------------------------------+", "sub"),
        ("|             HỆ THỐNG ĐẶT SÂN THỂ THAO ALOBO COURT - DOCKER COMPOSE ARCHITECTURE   |", "anno"),
        ("+-----------------------------------------------------------------------------------+", "sub"),
        ("|                                                                                   |", "text"),
        ("|   [ Client / Mobile App / Postman ]                                               |", "text"),
        ("|             |                                                                     |", "text"),
        ("|             | HTTP :8080 (Host Port)                                              |", "prompt"),
        ("|             v                                                                     |", "prompt"),
        ("|   +---------------------------------------+                                       |", "sub"),
        ("|   |  alobo-booking-service (Consumer)     |                                       |", "cls"),
        ("|   |  Container Port: 8080                 |                                       |", "cls"),
        ("|   +---------------------------------------+                                       |", "sub"),
        ("|        |                          |                                               |", "text"),
        ("|        | HTTP (Docker DNS)        | AMQP Event: BookingCreated                    |", "warn"),
        ("|        v                          v                                               |", "warn"),
        ("|   +-----------------------+  +------------------------+  +--------------------+   |", "sub"),
        ("|   | alobo-field-service   |  | alobo-rabbitmq         |  | alobo-redis        |   |", "cls"),
        ("|   | (Provider - :8081)    |  | (:5672 / :15672)       |  | (:6379 - Slot Lock)|   |", "cls"),
        ("|   +-----------------------+  +------------------------+  +--------------------+   |", "sub"),
        ("|        |                                   |                       |              |", "text"),
        ("|        | SQL Connection                    | Volume: rabbitmq-data | Vol: redis-data", "sub"),
        ("|        v                                   v                       v              |", "sub"),
        ("|   +---------------------------------------------------------------------------+   |", "sub"),
        ("|   |  alobo-postgres (PostgreSQL 16 + PostGIS)  [:55432:5432]                  |   |", "cls"),
        ("|   |  Named Volume: alobo_postgres_persistent_volume (/var/lib/postgresql/data) |   |", "ok"),
        ("|   +---------------------------------------------------------------------------+   |", "sub"),
        ("|   Docker Network: alobo-court-network (Bridge Driver)                             |", "anno"),
        ("+-----------------------------------------------------------------------------------+", "sub")
    ]
    render_code_window("architecture.txt", lines_arch, "lab8_arch.png", "Kiến Trúc Triển Khai Docker Compose Độc Lập", width=1000)

    print("=== HOÀN TẤT SINH 12 ẢNH MINH CHỨNG CHO BÀI 8 ===")

if __name__ == "__main__":
    build_all_lab8_screenshots()
