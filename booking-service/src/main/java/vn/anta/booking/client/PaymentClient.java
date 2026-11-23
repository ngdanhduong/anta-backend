package vn.anta.booking.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.Map;

/**
 * Service Discovery Client gọi Provider theo Service ID: 'PAYMENT-SERVICE'.
 * Tự động khám phá IP/Port qua Eureka và thực hiện thanh toán cho đơn đặt sân.
 */
@FeignClient(name = "PAYMENT-SERVICE")
public interface PaymentClient {

    @GetMapping("/api/v1/payments/instance-info")
    Map<String, Object> getInstanceInfo();

    @PostMapping("/api/v1/payments/intents")
    Map<String, Object> createPaymentIntent(@RequestBody Map<String, Object> request);
}
