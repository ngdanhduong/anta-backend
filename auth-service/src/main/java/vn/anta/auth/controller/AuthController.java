package vn.anta.auth.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1")
public class AuthController {

    @Value("${server.port:8085}")
    private int port;

    @Value("${spring.application.name:AUTH-SERVICE}")
    private String serviceName;

    // In-memory demo store for registered users
    private static final Map<String, Map<String, Object>> USERS_STORE = new HashMap<>();

    static {
        USERS_STORE.put("customer@anta.vn", Map.of(
            "id", "user-customer-01",
            "email", "customer@anta.vn",
            "displayName", "Nguyễn Văn Khách",
            "role", "CUSTOMER"
        ));
        USERS_STORE.put("owner@anta.vn", Map.of(
            "id", "user-owner-01",
            "email", "owner@anta.vn",
            "displayName", "Trần Minh Tâm (Chủ Sân)",
            "role", "OWNER"
        ));
        USERS_STORE.put("admin@anta.vn", Map.of(
            "id", "user-admin-01",
            "email", "admin@anta.vn",
            "displayName", "Quản Trị Viên Sàn",
            "role", "SUPER_ADMIN"
        ));
    }

    @GetMapping("/auth/instance-info")
    public Map<String, Object> getInstanceInfo() {
        return Map.of(
            "serviceName", serviceName,
            "port", port,
            "instanceId", serviceName + ":" + port,
            "status", "UP"
        );
    }

    // Public auth config for mobile app (Google Client ID, etc.)
    @GetMapping("/public/config")
    public Map<String, Object> getConfig() {
        return Map.of(
            "googleClientId", "demo-anta-google-client-id.apps.googleusercontent.com",
            "environment", "microservices-docker",
            "handledByPort", port
        );
    }

    // Yêu cầu mã xác thực OTP
    @PostMapping(value = {"/public/auth/code", "/auth/code"})
    public Map<String, Object> sendCode(@RequestBody(required = false) Map<String, Object> req) {
        String target = (req != null && req.containsKey("target")) ? req.get("target").toString() : "user@example.com";
        return Map.of(
            "challengeId", "challenge-" + UUID.randomUUID(),
            "target", target,
            "status", "SENT",
            "developmentCode", "123456",
            "message", "Mã xác thực đã được gửi (Mã thử nghiệm: 123456)"
        );
    }

    // Xác minh mã OTP
    @PostMapping(value = {"/public/auth/verify", "/auth/verify"})
    public Map<String, Object> verifyCode(@RequestBody(required = false) Map<String, Object> req) {
        return Map.of(
            "verificationProof", "proof-" + UUID.randomUUID(),
            "verified", true
        );
    }

    // Đăng nhập
    @PostMapping(value = {"/public/auth/login", "/auth/login"})
    public Map<String, Object> login(@RequestBody(required = false) Map<String, Object> req) {
        String email = (req != null && req.containsKey("identifier")) ? req.get("identifier").toString() : "customer@anta.vn";
        Map<String, Object> user = USERS_STORE.getOrDefault(email, Map.of(
            "id", "user-" + UUID.randomUUID().toString().substring(0, 8),
            "email", email,
            "displayName", "Người Dùng Anta",
            "role", "CUSTOMER"
        ));

        Map<String, Object> res = new LinkedHashMap<>();
        res.put("accessToken", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.anta-access-" + UUID.randomUUID());
        res.put("refreshToken", "anta-refresh-" + UUID.randomUUID());
        res.put("tokenType", "Bearer");
        res.put("expiresIn", 86400);
        res.put("user", user);
        res.put("handledByPort", port);
        return res;
    }

    // Đăng ký tài khoản
    @PostMapping(value = {"/public/auth/register", "/auth/register"})
    public Map<String, Object> register(@RequestBody(required = false) Map<String, Object> req) {
        String email = (req != null && req.containsKey("identifier")) ? req.get("identifier").toString() : "newuser@anta.vn";
        String name = (req != null && req.containsKey("displayName")) ? req.get("displayName").toString() : "Khách hàng mới";

        Map<String, Object> newUser = Map.of(
            "id", "user-" + UUID.randomUUID().toString().substring(0, 8),
            "email", email,
            "displayName", name,
            "role", "CUSTOMER"
        );
        USERS_STORE.put(email, newUser);

        return Map.of(
            "accessToken", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.anta-access-" + UUID.randomUUID(),
            "refreshToken", "anta-refresh-" + UUID.randomUUID(),
            "user", newUser,
            "message", "Đăng ký tài khoản thành công!"
        );
    }

    // Đăng nhập mạng xã hội (Google Social Sign-in)
    @PostMapping(value = {"/public/auth/social", "/auth/social"})
    public Map<String, Object> socialLogin(@RequestBody(required = false) Map<String, Object> req) {
        return Map.of(
            "accessToken", "anta-google-jwt-" + UUID.randomUUID(),
            "refreshToken", "anta-refresh-" + UUID.randomUUID(),
            "user", Map.of(
                "id", "user-google-01",
                "email", "google.user@anta.vn",
                "displayName", "Khách Hàng Google",
                "role", "CUSTOMER"
            )
        );
    }

    // Thông tin người dùng hiện tại
    @GetMapping("/users/me")
    public Map<String, Object> getCurrentUser(@RequestHeader(value = "Authorization", required = false) String authHeader) {
        return Map.of(
            "id", "user-customer-01",
            "email", "customer@anta.vn",
            "displayName", "Khách Hàng Thử Nghiệm",
            "role", "CUSTOMER",
            "phone", "0901234567",
            "handledByPort", port
        );
    }
}
