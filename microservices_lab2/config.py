# -*- coding: utf-8 -*-
"""
Cấu hình động cho Booking Service - Tránh Hard-code theo chuẩn 12-Factor App
Nạp động từ biến môi trường hoặc file .env
"""
import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Địa chỉ Field Service (mặc định port 8081)
    FIELD_SERVICE_URL: str = os.getenv("FIELD_SERVICE_URL", "http://localhost:8081")
    
    # Cấu hình Timeout mạng (giây)
    CONNECT_TIMEOUT: float = float(os.getenv("CONNECT_TIMEOUT", "2.0"))
    READ_TIMEOUT: float = float(os.getenv("READ_TIMEOUT", "3.0"))
    
    # Cấu hình RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "notification.booking.queue")
    RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "booking.exchange")
    RABBITMQ_ROUTING_KEY: str = os.getenv("RABBITMQ_ROUTING_KEY", "booking.created")
    
    # Cơ chế Retry
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "1.5"))

settings = Settings()
