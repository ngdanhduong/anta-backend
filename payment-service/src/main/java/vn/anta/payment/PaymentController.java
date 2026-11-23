package vn.anta.payment;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    @Value("${server.port:8084}")
    private int port;

    @Value("${spring.application.name:PAYMENT-SERVICE}")
    private String serviceName;

    @GetMapping("/instance-info")
    public Map<String, Object> getInstanceInfo() {
        return Map.of(
            "serviceName", serviceName,
            "port", port,
            "instanceId", serviceName + ":" + port
        );
    }

    @PostMapping("/intents")
    public Map<String, Object> createPaymentIntent(@RequestBody(required = false) Map<String, Object> request) {
        String bookingId = (request != null && request.containsKey("bookingId")) ? request.get("bookingId").toString() : "BK-SAMPLE";
        int amount = (request != null && request.containsKey("amount")) ? Integer.parseInt(request.get("amount").toString()) : 120000;

        Map<String, Object> res = new LinkedHashMap<>();
        res.put("paymentIntentId", "PI-" + UUID.randomUUID());
        res.put("bookingId", bookingId);
        res.put("amount", amount);
        res.put("currency", "VND");
        res.put("status", "SUCCEEDED");
        res.put("provider", "Sandbox-AntaPay");
        res.put("processedByPort", port);
        return res;
    }
}
