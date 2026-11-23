# -*- coding: utf-8 -*-
"""
Service Registry (Eureka-compatible Server) - Port 8761
Quản lý đăng ký, heartbeat và khám phá dịch vụ (Service Discovery)
cho hệ thống Microservices Alobo Court.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ServiceRegistry")

app = FastAPI(
    title="Service Registry (Eureka Server)",
    description="Trung tâm đăng ký và khám phá dịch vụ cho hệ thống Microservices",
    version="1.0.0"
)

class InstanceInfo(BaseModel):
    instanceId: str
    serviceName: str
    host: str
    port: int
    healthUrl: str
    status: str = "UP"
    lastHeartbeat: float = 0.0

# Lưu trữ danh sách dịch vụ: { service_name: { instance_id: InstanceInfo } }
REGISTRY_DB: Dict[str, Dict[str, InstanceInfo]] = {}

@app.post("/eureka/apps/{app_name}", status_code=status.HTTP_201_CREATED)
async def register_instance(app_name: str, instance: InstanceInfo):
    """
    Đăng ký một instance microservice vào Registry
    """
    app_key = app_name.upper()
    if app_key not in REGISTRY_DB:
        REGISTRY_DB[app_key] = {}
    
    instance.serviceName = app_key
    instance.lastHeartbeat = time.time()
    REGISTRY_DB[app_key][instance.instanceId] = instance
    logger.info(f"Đã đăng ký instance mới: {instance.instanceId} ({instance.host}:{instance.port}) cho dịch vụ [{app_key}]")
    return {"message": "Registered successfully", "instance": instance}

@app.get("/eureka/apps")
async def get_all_services():
    """
    Lấy danh sách tất cả các dịch vụ và instance đang hoạt động
    """
    # Lọc bỏ các instance hết hạn heartbeat (> 30s)
    current_time = time.time()
    result = {}
    for service_name, instances in REGISTRY_DB.items():
        active = {
            iid: inst for iid, inst in instances.items()
            if (current_time - inst.lastHeartbeat) < 45.0
        }
        if active:
            result[service_name] = list(active.values())
    return {"applications": result}

@app.get("/eureka/apps/{app_name}")
async def get_service_instances(app_name: str):
    """
    Lấy danh sách các instance khả dụng của một Service ID cụ thể (Service Discovery)
    """
    app_key = app_name.upper()
    if app_key not in REGISTRY_DB or not REGISTRY_DB[app_key]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dịch vụ [{app_key}] không tìm thấy trong Service Registry!"
        )
    
    current_time = time.time()
    active_instances = [
        inst for inst in REGISTRY_DB[app_key].values()
        if (current_time - inst.lastHeartbeat) < 45.0 and inst.status == "UP"
    ]
    
    if not active_instances:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không có instance nào khả dụng cho dịch vụ [{app_key}]!"
        )
    return {"serviceName": app_key, "instances": active_instances}

@app.put("/eureka/apps/{app_name}/{instance_id}")
async def send_heartbeat(app_name: str, instance_id: str):
    """
    Tiếp nhận Heartbeat duy trì trạng thái 'UP' của instance
    """
    app_key = app_name.upper()
    if app_key in REGISTRY_DB and instance_id in REGISTRY_DB[app_key]:
        REGISTRY_DB[app_key][instance_id].lastHeartbeat = time.time()
        return {"status": "RENEWED", "instanceId": instance_id}
    raise HTTPException(status_code=404, detail="Instance not found")

@app.delete("/eureka/apps/{app_name}/{instance_id}")
async def deregister_instance(app_name: str, instance_id: str):
    """
    Hủy đăng ký instance khi tắt service
    """
    app_key = app_name.upper()
    if app_key in REGISTRY_DB and instance_id in REGISTRY_DB[app_key]:
        del REGISTRY_DB[app_key][instance_id]
        logger.info(f"Đã hủy đăng ký instance {instance_id} khỏi dịch vụ [{app_key}]")
        return {"message": "Deregistered successfully"}
    raise HTTPException(status_code=404, detail="Instance not found")

@app.get("/dashboard", response_class=HTMLResponse)
async def registry_dashboard():
    """
    Giao diện Web trực quan hiển thị danh sách các Microservices (tương tự Eureka Dashboard)
    """
    rows_html = ""
    for service_name, instances in REGISTRY_DB.items():
        for inst in instances.values():
            status_badge = "<span style='color:green;font-weight:bold;'>UP (Online)</span>" if inst.status == "UP" else "<span style='color:red;'>DOWN</span>"
            rows_html += f"""
            <tr>
                <td style='padding:8px;border:1px solid #ddd;'><b>{service_name}</b></td>
                <td style='padding:8px;border:1px solid #ddd;'>{inst.instanceId}</td>
                <td style='padding:8px;border:1px solid #ddd;'>{inst.host}:{inst.port}</td>
                <td style='padding:8px;border:1px solid #ddd;'>{status_badge}</td>
                <td style='padding:8px;border:1px solid #ddd;'><a href='{inst.healthUrl}' target='_blank'>Check Health</a></td>
            </tr>
            """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Eureka Server Dashboard - Alobo Microservices</title>
        <style>
            body {{ font-family: sans-serif; margin: 30px; background: #f8fafc; }}
            h1 {{ color: #0f294a; }}
            table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 15px; }}
            th {{ background: #0f294a; color: white; padding: 10px; text-align: left; }}
        </style>
    </head>
    <body>
        <h1>🍀 Netflix Eureka Service Registry Dashboard</h1>
        <p><b>Hệ thống:</b> Alobo Court Platform Microservices | <b>Port:</b> 8761</p>
        <table>
            <thead>
                <tr>
                    <th>Application (Service ID)</th>
                    <th>Instance ID</th>
                    <th>Address:Port</th>
                    <th>Status</th>
                    <th>Health URL</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else "<tr><td colspan='5' style='padding:15px;text-align:center;'>Chưa có dịch vụ nào đăng ký</td></tr>"}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("registry_service:app", host="0.0.0.0", port=8761, reload=False)
