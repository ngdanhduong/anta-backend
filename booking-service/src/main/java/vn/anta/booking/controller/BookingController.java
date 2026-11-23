package vn.anta.booking.controller;

import org.springframework.web.bind.annotation.*;
import vn.anta.booking.client.PaymentClient;
import vn.anta.booking.client.YardClient;

import java.util.*;

@RestController
@RequestMapping("/api/v1/bookings")
public class BookingController {

    private final YardClient yardClient;
    private final PaymentClient paymentClient;

    public BookingController(YardClient yardClient, PaymentClient paymentClient) {
        this.yardClient = yardClient;
        this.paymentClient = paymentClient;
    }

    // Endpoint 1: Bắt buộc theo Bài thực hành số 7 để test phân phối request & cân bằng tải
    @GetMapping("/test-load-balancing")
    public Map<String, Object> testLoadBalancing() {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("consumer", "BOOKING-SERVICE:8083");
        res.put("providerInfo", yardClient.getInstanceInfo());
        res.put("timestamp", System.currentTimeMillis());
        return res;
    }

    // Endpoint 2: Khám phá danh sách sân từ Provider YARD-SERVICE
    @GetMapping("/yards")
    public List<Map<String, Object>> getAvailableYards() {
        return yardClient.getYards();
    }

    // Endpoint 3: Nghiệp vụ đặt sân hoàn chỉnh sử dụng Service Discovery điều phối cả YARD-SERVICE và PAYMENT-SERVICE
    @PostMapping
    public Map<String, Object> createBooking(@RequestBody(required = false) Map<String, Object> request) {
        String yardId = (request != null && request.containsKey("yardId")) ? request.get("yardId").toString() : "yard-01";
        String slot = (request != null && request.containsKey("slot")) ? request.get("slot").toString() : "18:00-19:00";
        String userId = (request != null && request.containsKey("userId")) ? request.get("userId").toString() : "customer-anta-01";
        int amount = (request != null && request.containsKey("amount")) ? Integer.parseInt(request.get("amount").toString()) : 120000;

        // 1. Service Discovery: Khám phá YARD-SERVICE qua Eureka và gọi kiểm tra sân trống
        Map<String, Object> availability = yardClient.checkAvailability(yardId);

        // 2. Tạo mã đơn đặt sân
        String bookingId = "ANTA-BK-" + System.currentTimeMillis();

        // 3. Service Discovery: Gọi PAYMENT-SERVICE qua OpenFeign để tạo giao dịch thanh toán
        Map<String, Object> paymentPayload = new HashMap<>();
        paymentPayload.put("bookingId", bookingId);
        paymentPayload.put("amount", amount);
        Map<String, Object> paymentIntent = paymentClient.createPaymentIntent(paymentPayload);

        // 4. Tổng hợp đơn đặt hoàn tất
        Map<String, Object> booking = new LinkedHashMap<>();
        booking.put("bookingId", bookingId);
        booking.put("userId", userId);
        booking.put("yardId", yardId);
        booking.put("slot", slot);
        booking.put("amount", amount);
        booking.put("status", "CONFIRMED");
        booking.put("yardVerification", availability);
        booking.put("paymentDetails", paymentIntent);
        booking.put("orchestration", "Orchestrated via Spring Cloud OpenFeign + Netflix Eureka (YARD-SERVICE + PAYMENT-SERVICE)");
        booking.put("message", "Đặt sân và thanh toán thành công qua chuỗi Microservices!");

        return booking;
    }
}
