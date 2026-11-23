package vn.anta.yard;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1")
public class YardController {

    @Value("${server.port:8081}")
    private int port;

    @Value("${spring.application.name:YARD-SERVICE}")
    private String serviceName;

    // Endpoint bắt buộc theo yêu cầu Bài thực hành số 7 để kiểm tra load balancing
    @GetMapping("/instance-info")
    public Map<String, Object> getInstanceInfo() {
        Map<String, Object> info = new LinkedHashMap<>();
        info.put("serviceName", serviceName);
        info.put("port", port);
        info.put("instanceId", serviceName + ":" + port);
        return info;
    }

    // Danh sách các sân thể thao mẫu của Anta
    @GetMapping("/yards")
    public List<Map<String, Object>> getYards() {
        return List.of(
            Map.of("id", "yard-01", "name", "Sân Cầu Lông Anta 1", "sport", "Badminton", "pricePerHour", 120000, "handledByPort", port),
            Map.of("id", "yard-02", "name", "Sân Bóng Đá Mini Anta 2", "sport", "Football", "pricePerHour", 300000, "handledByPort", port),
            Map.of("id", "yard-03", "name", "Sân Tennis Anta 3", "sport", "Tennis", "pricePerHour", 250000, "handledByPort", port)
        );
    }

    // Kiểm tra lịch trống của sân trước khi đặt
    @GetMapping("/yards/{id}/availability")
    public Map<String, Object> checkAvailability(@PathVariable String id) {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("yardId", id);
        res.put("status", "AVAILABLE");
        res.put("availableSlots", List.of("17:00-18:00", "18:00-19:00", "19:00-20:00", "20:00-21:00"));
        res.put("handledByPort", port);
        res.put("instanceId", serviceName + ":" + port);
        return res;
    }
}
