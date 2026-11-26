package vn.anta.cloud.controller;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;
import vn.anta.cloud.service.EmailService;
import vn.anta.cloud.store.AntaStore;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
public class AuthUsersController {

    private final AntaStore store;
    private final EmailService emailService;
    private final ObjectMapper mapper = new ObjectMapper();
    private final HttpClient httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    public AuthUsersController(AntaStore store, EmailService emailService) {
        this.store = store;
        this.emailService = emailService;
    }

    @GetMapping({"/public/config", "/config"})
    public Map<String, Object> getConfig() {
        String googleClientId = Optional.ofNullable(System.getenv("GOOGLE_CLIENT_ID"))
                .filter(s -> !s.isBlank())
                .map(String::trim)
                .orElse(null);
        Map<String, Object> cfg = new LinkedHashMap<>();
        cfg.put("googleClientId", googleClientId);
        cfg.put("feedbackEmail", "hotro@anta.vn");
        cfg.put("features", Map.of("sandboxPayment", true));
        return Map.of("data", cfg);
    }

    @GetMapping("/public/content/{slug}")
    public Map<String, Object> getContent(@PathVariable String slug) {
        String title = "terms".equalsIgnoreCase(slug) ? "Điều khoản dịch vụ Anta Sports" : "Thông tin Anta Sports";
        String body = """
                Chào mừng bạn đến với Anta - Nền tảng đặt sân thể thao trực tuyến.
                1. Vui lòng có mặt trước giờ chơi 10 phút để làm thủ tục nhận sân.
                2. Hủy lịch trước giờ chơi tối thiểu 2 giờ qua ứng dụng.
                3. Hỗ trợ kỹ thuật: hotro@anta.vn
                """;
        return Map.of("data", Map.of("title", title, "body", body));
    }

    @PostMapping({"/public/auth/otp/send", "/public/auth/code", "/auth/code"})
    public Map<String, Object> sendOtp(@RequestBody(required = false) Map<String, Object> req) {
        String identifier = req != null ? Objects.toString(req.get("identifier"), "").trim() : "";
        String purpose = req != null ? Objects.toString(req.get("purpose"), "register") : "register";
        String challengeId = "challenge-" + UUID.randomUUID();
        String code = String.format("%06d", new Random().nextInt(1_000_000));
        Instant expiresAt = Instant.now().plus(15, ChronoUnit.MINUTES);
        store.saveOtpChallenge(challengeId, identifier, code, expiresAt);

        boolean emailed = identifier.contains("@") && emailService.sendOtpEmail(identifier, code, purpose);
        String delivery = emailed ? "provider" : "development-only";

        return Map.of("data", Map.of(
                "challengeId", challengeId,
                "expiresAt", expiresAt.toString(),
                "delivery", delivery
        ));
    }

    @GetMapping("/dev/otp/{challengeId}")
    public ResponseEntity<Map<String, Object>> getDevOtp(@PathVariable String challengeId) {
        AntaStore.OtpRecord otp = store.findOtpChallenge(challengeId);
        if (otp == null) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Mã thử nghiệm không tồn tại hoặc đã hết hạn");
        }
        return ResponseEntity.ok(Map.of("data", Map.of("code", otp.code())));
    }

    @PostMapping({"/public/auth/otp/verify", "/public/auth/verify", "/auth/verify"})
    public ResponseEntity<Map<String, Object>> verifyOtp(@RequestBody(required = false) Map<String, Object> req) {
        String challengeId = req != null ? Objects.toString(req.get("challengeId"), "") : "";
        String code = req != null ? Objects.toString(req.get("code"), "").trim() : "";
        AntaStore.OtpRecord otp = store.findOtpChallenge(challengeId);
        if (otp == null) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "OTP_EXPIRED", "Phiên xác thực đã hết hạn");
        }
        if (!otp.code().equals(code)) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "OTP_INVALID", "Mã xác thực không chính xác");
        }
        String token = "verify-token-" + UUID.randomUUID();
        store.saveVerificationToken(token, otp.identifier());
        return ResponseEntity.ok(Map.of("data", Map.of("verificationToken", token)));
    }

    @PostMapping({"/public/auth/register", "/auth/register"})
    public ResponseEntity<Map<String, Object>> register(@RequestBody(required = false) Map<String, Object> req) {
        return AntaStore.error(HttpStatus.FORBIDDEN, "REGISTRATION_DISABLED", "Ứng dụng hiện chỉ hỗ trợ đăng nhập bằng Google");
    }

    @PostMapping({"/public/auth/login", "/auth/login"})
    public ResponseEntity<Map<String, Object>> login(@RequestBody(required = false) Map<String, Object> req) {
        String identifier = req != null ? Objects.toString(req.get("identifier"), "").trim() : "";
        String password = req != null ? Objects.toString(req.get("password"), "") : "";
        if (identifier.isEmpty()) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Vui lòng nhập email hoặc số điện thoại");
        }
        AntaStore.UserRecord user = store.findUserByIdentifier(identifier);
        if (user == null || !store.verifyPassword(password, user)) {
            return AntaStore.error(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", "Sai tài khoản hoặc mật khẩu");
        }
        return ResponseEntity.ok(Map.of("data", store.issueTokenBundle(user)));
    }

    @PostMapping({"/public/auth/refresh", "/auth/refresh"})
    public ResponseEntity<Map<String, Object>> refresh(@RequestBody(required = false) Map<String, Object> req) {
        String refreshToken = req != null ? Objects.toString(req.get("refreshToken"), "") : "";
        AntaStore.UserRecord user = store.resolveRefreshToken(refreshToken);
        if (user == null) {
            return AntaStore.unauthorized();
        }
        store.revokeToken(refreshToken);
        return ResponseEntity.ok(Map.of("data", store.issueTokenBundle(user)));
    }

    @PostMapping({"/public/auth/social", "/auth/social"})
    public ResponseEntity<Map<String, Object>> socialLogin(@RequestBody(required = false) Map<String, Object> req) {
        String idToken = req != null ? Objects.toString(req.get("idToken"), "").trim() : "";
        String expectedAud = System.getenv("GOOGLE_CLIENT_ID");
        String email = "google_user@anta.vn";
        String name = "VĐV Anta Sports";

        if (idToken.isEmpty()) {
            if (expectedAud != null && !expectedAud.isBlank()) {
                return AntaStore.error(HttpStatus.UNAUTHORIZED, "INVALID_SOCIAL_TOKEN", "Thiếu mã xác thực Google");
            }
        } else {
            try {
                String url = "https://oauth2.googleapis.com/tokeninfo?id_token=" + URLEncoder.encode(idToken, StandardCharsets.UTF_8);
                HttpRequest request = HttpRequest.newBuilder(URI.create(url)).timeout(Duration.ofSeconds(10)).GET().build();
                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() != 200) {
                    return AntaStore.error(HttpStatus.UNAUTHORIZED, "INVALID_SOCIAL_TOKEN", "Google chưa xác nhận được tài khoản");
                }
                Map<String, Object> claims = mapper.readValue(response.body(), new TypeReference<>() {});
                if (expectedAud != null && !expectedAud.isBlank()) {
                    String aud = Objects.toString(claims.get("aud"), "").trim();
                    boolean audMatched = Arrays.stream(expectedAud.split(","))
                            .map(String::trim)
                            .filter(s -> !s.isEmpty())
                            .anyMatch(s -> s.equals(aud));
                    if (!audMatched) {
                        return AntaStore.error(HttpStatus.UNAUTHORIZED, "INVALID_SOCIAL_TOKEN", "Token Google không khớp ứng dụng");
                    }
                }
                if ("false".equalsIgnoreCase(Objects.toString(claims.get("email_verified"), "true"))) {
                    return AntaStore.error(HttpStatus.UNAUTHORIZED, "UNSUPPORTED_SOCIAL_IDENTITY", "Tài khoản Google này chưa xác minh email");
                }
                email = Objects.toString(claims.get("email"), email).trim();
                name = Objects.toString(claims.get("name"), email).trim();
            } catch (Exception ex) {
                return AntaStore.error(HttpStatus.UNAUTHORIZED, "INVALID_SOCIAL_TOKEN", "Không xác minh được tài khoản Google");
            }
        }

        AntaStore.UserRecord user = store.findUserByIdentifier(email);
        if (user == null) {
            user = store.createUser("user-gg-" + UUID.randomUUID().toString().substring(0, 8), email, name, "", false);
        }
        return ResponseEntity.ok(Map.of("data", store.issueTokenBundle(user)));
    }

    @PostMapping("/public/auth/reset-password")
    public ResponseEntity<Map<String, Object>> resetPassword(@RequestBody(required = false) Map<String, Object> req) {
        String identifier = req != null ? Objects.toString(req.get("identifier"), "").trim() : "";
        String password = req != null ? Objects.toString(req.get("password"), "") : "";
        String vToken = req != null ? Objects.toString(req.get("verificationToken"), "") : "";
        if (!store.consumeVerificationToken(vToken)) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "INVALID_VERIFICATION_TOKEN", "Mã xác thực không hợp lệ");
        }
        AntaStore.UserRecord old = store.findUserByIdentifier(identifier);
        if (old == null) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "USER_NOT_FOUND", "Không tìm thấy tài khoản");
        }
        store.updateUserPassword(old.id(), password);
        return ResponseEntity.ok(Map.of("data", Map.of("ok", true)));
    }

    @PostMapping("/auth/logout")
    public Map<String, Object> logout(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        if (auth != null && auth.startsWith("Bearer ")) {
            store.revokeToken(auth.substring(7).trim());
        }
        return Map.of("data", Map.of("ok", true));
    }

    @GetMapping({"/users/me", "/user/me"})
    public ResponseEntity<Map<String, Object>> me(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        return ResponseEntity.ok(Map.of("data", AntaStore.userMap(user)));
    }

    @PatchMapping({"/users/me", "/user/me"})
    public ResponseEntity<Map<String, Object>> rename(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        String displayName = req != null ? Objects.toString(req.get("displayName"), user.displayName()).trim() : user.displayName();
        AntaStore.UserRecord updated = store.updateUserDisplayName(user.id(), displayName);
        return ResponseEntity.ok(Map.of("data", AntaStore.userMap(updated)));
    }

    @DeleteMapping({"/users/me", "/user/me"})
    public ResponseEntity<Map<String, Object>> deleteAccount(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        store.deleteUser(user.id());
        if (auth != null && auth.startsWith("Bearer ")) {
            store.revokeToken(auth.substring(7).trim());
        }
        return ResponseEntity.ok(Map.of("data", Map.of("deleted", true)));
    }

    @GetMapping({"/users/me/favorites", "/user/me/favorites"})
    public ResponseEntity<Map<String, Object>> favorites(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        List<Map<String, Object>> items = new ArrayList<>();
        for (String branchId : store.favoriteIds(user.id())) {
            Map<String, Object> branch = store.findBranch(branchId);
            if (branch != null) items.add(store.branchWithDistance(branch, 10.7721, 106.6951));
        }
        return ResponseEntity.ok(Map.of("data", items));
    }

    @PostMapping("/users/me/favorites/{venueId}")
    public ResponseEntity<Map<String, Object>> addFavorite(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String venueId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        store.addFavorite(user.id(), venueId);
        return ResponseEntity.ok(Map.of("data", Map.of("favorite", true)));
    }

    @DeleteMapping("/users/me/favorites/{venueId}")
    public ResponseEntity<Map<String, Object>> removeFavorite(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String venueId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        store.removeFavorite(user.id(), venueId);
        return ResponseEntity.ok(Map.of("data", Map.of("favorite", false)));
    }
}
