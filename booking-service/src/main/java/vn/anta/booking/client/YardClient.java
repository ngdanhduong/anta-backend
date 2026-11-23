package vn.anta.booking.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.List;
import java.util.Map;

/**
 * Service Discovery Client gọi Provider theo Service ID: 'YARD-SERVICE'.
 * Tự động tích hợp Spring Cloud LoadBalancer để phân phối request giữa các instance (8081, 8082).
 */
@FeignClient(name = "YARD-SERVICE")
public interface YardClient {

    @GetMapping("/api/v1/instance-info")
    Map<String, Object> getInstanceInfo();

    @GetMapping("/api/v1/yards")
    List<Map<String, Object>> getYards();

    @GetMapping("/api/v1/yards/{id}/availability")
    Map<String, Object> checkAvailability(@PathVariable("id") String id);
}
