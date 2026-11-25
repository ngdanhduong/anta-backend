package vn.anta.auth.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
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
            "identifier", "customer@anta.vn",
            "displayName", "Nguyễn Văn Khách",
            "passwordLogin", true
        ));
        USERS_STORE.put("owner@anta.vn", Map.of(
            "id", "user-owner-01",
            "identifier", "owner@anta.vn",
            "displayName", "Trần Minh Tâm (Chủ Sân)",
            "passwordLogin", true
        ));
        USERS_STORE.put("admin@anta.vn", Map.of(
            "id", "user-admin-01",
            "identifier", "admin@anta.vn",
            "displayName", "Quản Trị Viên Sàn",
            "passwordLogin", true
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

    // Public config cho Android App: GET /public/config
    @GetMapping({"/public/config", "/config"})
    public Map<String, Object> getConfig() {
        Map<String, Object> cfg = new LinkedHashMap<>();
        cfg.put("googleClientId", null);
        cfg.put("feedbackEmail", "hotro@anta.vn");
        cfg.put("features", Map.of("sandboxPayment", true));

        return Map.of("data", cfg);
    }

    // Tài liệu điều khoản / nội dung công khai: GET /public/content/{slug}
    @GetMapping("/public/content/{slug}")
    public Map<String, Object> getContent(@PathVariable String slug) {
        Map<String, Object> doc = Map.of(
            "title", "Điều khoản dịch vụ Anta Sports",
            "body", "Chào mừng bạn đến với Anta - Nền tảng đặt sân thể thao thông minh hàng đầu Việt Nam.\nQuy định: Vui lòng check-in đúng giờ và giữ gìn cơ sở vật chất sân bãi."
        );
        return Map.of("data", doc);
    }

    // Gửi mã OTP (POST /public/auth/code, POST /public/auth/otp/send)
    @PostMapping(value = {"/public/auth/code", "/public/auth/otp/send", "/auth/code"})
    public Map<String, Object> sendCode(@RequestBody(required = false) Map<String, Object> req) {
        Instant expires = Instant.now().plus(15, ChronoUnit.MINUTES);
        Map<String, Object> challenge = Map.of(
            "challengeId", "challenge-" + UUID.randomUUID(),
            "expiresAt", expires.toString(),
            "delivery", "development-only"
        );
        return Map.of("data", challenge);
    }

    // Xác minh mã OTP (POST /public/auth/verify, POST /public/auth/otp/verify)
    @PostMapping(value = {"/public/auth/verify", "/public/auth/otp/verify", "/auth/verify"})
    public Map<String, Object> verifyCode(@RequestBody(required = false) Map<String, Object> req) {
        return Map.of("data", Map.of("verificationToken", "verify-token-" + UUID.randomUUID().toString().substring(0, 12)));
    }

    // Đăng nhập mật khẩu / OTP (POST /public/auth/login)
    @PostMapping(value = {"/public/auth/login", "/auth/login"})
    public Map<String, Object> login(@RequestBody(required = false) Map<String, Object> req) {
        String email = (req != null && req.containsKey("identifier")) ? req.get("identifier").toString() : "customer@anta.vn";
        Map<String, Object> user = USERS_STORE.getOrDefault(email, Map.of(
            "id", "user-" + UUID.randomUUID().toString().substring(0, 8),
            "identifier", email,
            "displayName", "Người Dùng Anta",
            "passwordLogin", true
        ));

        Map<String, Object> tokens = new LinkedHashMap<>();
        tokens.put("accessToken", "anta-jwt-access-" + UUID.randomUUID());
        tokens.put("refreshToken", "anta-jwt-refresh-" + UUID.randomUUID());
        tokens.put("expiresIn", 86400L);
        tokens.put("user", user);

        return Map.of("data", tokens);
    }

    // Đăng nhập qua mạng xã hội (POST /public/auth/social)
    @PostMapping(value = {"/public/auth/social", "/auth/social"})
    public Map<String, Object> socialLogin(@RequestBody(required = false) Map<String, Object> req) {
        Map<String, Object> user = Map.of(
            "id", "user-google-01",
            "identifier", "google_user@anta.vn",
            "displayName", "VĐV Anta Sports",
            "passwordLogin", false
        );

        Map<String, Object> tokens = Map.of(
            "accessToken", "anta-google-access-" + UUID.randomUUID(),
            "refreshToken", "anta-google-refresh-" + UUID.randomUUID(),
            "expiresIn", 86400L,
            "user", user
        );

        return Map.of("data", tokens);
    }

    // Đăng ký tài khoản (POST /public/auth/register)
    @PostMapping(value = {"/public/auth/register", "/auth/register"})
    public Map<String, Object> register(@RequestBody(required = false) Map<String, Object> req) {
        String email = (req != null && req.containsKey("identifier")) ? req.get("identifier").toString() : "newuser@anta.vn";
        Map<String, Object> user = Map.of(
            "id", "user-" + UUID.randomUUID().toString().substring(0, 8),
            "identifier", email,
            "displayName", "Thành Viên Mới",
            "passwordLogin", true
        );

        Map<String, Object> tokens = Map.of(
            "accessToken", "anta-new-access-" + UUID.randomUUID(),
            "refreshToken", "anta-new-refresh-" + UUID.randomUUID(),
            "expiresIn", 86400L,
            "user", user
        );

        return Map.of("data", tokens);
    }

    // Thông tin người dùng hiện tại (GET /api/v1/users/me)
    @GetMapping({"/users/me", "/user/me"})
    public Map<String, Object> getCurrentUser() {
        Map<String, Object> user = Map.of(
            "id", "user-customer-01",
            "identifier", "customer@anta.vn",
            "displayName", "Nguyễn Văn Khách",
            "passwordLogin", true
        );
        return Map.of("data", user);
    }

    // Danh sách sân yêu thích (GET /api/v1/users/me/favorites)
    @GetMapping({"/users/me/favorites", "/user/me/favorites"})
    public Map<String, Object> getFavorites() {
        return Map.of("data", List.of());
    }

    // Danh sách đơn đặt của tôi (GET /api/v1/users/me/bookings)
    @GetMapping({"/users/me/bookings", "/user/me/bookings"})
    public Map<String, Object> getMyBookings() {
        Map<String, Object> items = Map.of("items", List.of());
        return Map.of("data", items);
    }
}
