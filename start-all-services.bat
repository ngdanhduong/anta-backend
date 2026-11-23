@echo off
title Khoi dong Cum Microservices ANTA
chcp 65001 >nul
echo =====================================================================
echo       HE THONG MICROSERVICES DAT SAN THE THAO ANTA
echo =====================================================================
echo.

set "BASE_DIR=%~dp0"
set "FRONTEND_DIR=%~dp0frontend\"
if exist "%~dp0service-registry" (
    set "BASE_DIR=%~dp0"
    set "FRONTEND_DIR=%~dp0frontend\"
) else (
    set "BASE_DIR=%~dp0backend\"
    set "FRONTEND_DIR=%~dp0frontend\"
)

echo [1/7] Dang khoi dong Service Registry (Eureka Server - Port 8761)...
start "Eureka-Registry:8761" java -jar "%BASE_DIR%service-registry\target\service-registry-0.0.1-SNAPSHOT.jar"
timeout /t 6 /nobreak >nul

echo [2/7] Dang khoi dong Yard-Service Instance 1 (Port 8081)...
start "Yard-Service-1:8081" java -jar "%BASE_DIR%yard-service\target\yard-service-0.0.1-SNAPSHOT.jar" --server.port=8081

echo [3/7] Dang khoi dong Yard-Service Instance 2 (Port 8082)...
start "Yard-Service-2:8082" java -jar "%BASE_DIR%yard-service\target\yard-service-0.0.1-SNAPSHOT.jar" --server.port=8082

echo [4/7] Dang khoi dong Booking-Service (Port 8083)...
start "Booking-Service:8083" java -jar "%BASE_DIR%booking-service\target\booking-service-0.0.1-SNAPSHOT.jar" --server.port=8083

echo [5/7] Dang khoi dong Payment-Service (Port 8084)...
start "Payment-Service:8084" java -jar "%BASE_DIR%payment-service\target\payment-service-0.0.1-SNAPSHOT.jar" --server.port=8084

echo [6/7] Dang khoi dong Auth-Service (Port 8085)...
start "Auth-Service:8085" java -jar "%BASE_DIR%auth-service\target\auth-service-0.0.1-SNAPSHOT.jar" --server.port=8085
timeout /t 4 /nobreak >nul

echo [7/7] Dang khoi dong API Gateway (Port 8080)...
start "API-Gateway:8080" java -jar "%BASE_DIR%api-gateway\target\api-gateway-0.0.1-SNAPSHOT.jar" --server.port=8080

echo.
echo =====================================================================
echo  KHOI DONG HOAN TAT CUM MICROSERVICES!
echo  - API Gateway (Diem truy cap tap trung): http://localhost:8080
echo  - Eureka Server Dashboard:             http://localhost:8761
echo  - Booking API qua Gateway:              http://localhost:8080/api/v1/bookings
echo  - Yard Catalog qua Gateway:             http://localhost:8080/api/v1/yards
echo  - Auth API qua Gateway:                 http://localhost:8080/api/v1/auth/instance-info
echo  - Web Admin & Chu san Anta:            %FRONTEND_DIR%index.html
echo =====================================================================
echo.
pause
