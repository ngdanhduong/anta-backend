@echo off
title Dung Cum Microservices ANTA
chcp 65001 >nul
echo Dang dung cac tien trinh Microservices tren cong 8761, 8080, 8081, 8082, 8083, 8084, 8085...
powershell -Command "Get-NetTCPConnection -LocalPort 8761, 8080, 8081, 8082, 8083, 8084, 8085 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
echo Da dung toan bo cac Microservices!
pause
