package vn.anta.cloud.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import vn.anta.cloud.store.AntaStore;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
public class HealthController {

    private final AntaStore store;

    public HealthController(AntaStore store) {
        this.store = store;
    }

    @GetMapping({"/", "/api/v1/gateway/info"})
    public Map<String, Object> info() {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("service", "anta-cloud-api");
        res.put("status", "UP");
        res.put("branches", store.getBranches().size());
        res.put("sports", store.getSports().size());
        res.put("endpoints", List.of(
                "/api/v1/health/ready",
                "/api/v1/public/sports",
                "/api/v1/public/branches",
                "/api/v1/public/config",
                "/api/v1/public/auth/login",
                "/api/v1/booking-holds",
                "/api/v1/bookings",
                "/api/v1/payment-intents"
        ));
        return res;
    }

    @GetMapping("/api/v1/health/ready")
    public Map<String, Object> ready() {
        return Map.of(
                "status", "UP",
                "data", Map.of(
                        "ready", true,
                        "branches", store.getBranches().size(),
                        "sports", store.getSports().size()
                )
        );
    }
}
