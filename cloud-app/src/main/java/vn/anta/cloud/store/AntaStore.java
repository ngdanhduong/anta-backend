package vn.anta.cloud.store;

import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.text.Normalizer;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * In-memory catalog and state store loaded from catalog.json for fast startup and zero external DB dependency.
 */
@Component
public class AntaStore {

    public static final String DEMO_USER_ID = "user-customer-01";
    public static final List<String> DEFAULT_FAVORITES = List.of();

    public record UserRecord(String id, String identifier, String displayName, String password, boolean passwordLogin, String status, Instant createdAt) {}

    public record RoleEntry(String role, String branchId) {}

    public record OtpRecord(String challengeId, String identifier, String code, Instant expiresAt, String verificationToken) {}

    public record HoldRecord(String holdId, String userId, String yardId, String branchId, Instant startsAt, Instant endsAt, long total, Instant expiresAt) {}

    public record BookingStatusEvent(Instant createdAt, String fromStatus, String toStatus, String reason) {
        public Map<String, Object> toMap() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("created_at", createdAt.toString());
            m.put("from_status", fromStatus);
            m.put("to_status", toStatus);
            m.put("reason", reason);
            return m;
        }
    }

    public record BookingRecord(
            String id,
            String userId,
            String branchId,
            String yardId,
            String branchName,
            String branchAddress,
            String branchImage,
            String yardName,
            String sportName,
            String branchTimezone,
            Instant startsAt,
            Instant endsAt,
            long hourlyPrice,
            long amount,
            String status,
            String source,
            Instant createdAt,
            Instant paymentExpiresAt,
            Instant confirmDeadlineAt,
            List<BookingStatusEvent> statusHistory
    ) {
        public BookingRecord withStatus(String nextStatus, String reason) {
            List<BookingStatusEvent> history = new ArrayList<>(statusHistory != null ? statusHistory : List.of());
            history.add(new BookingStatusEvent(Instant.now(), status, nextStatus, reason));
            return new BookingRecord(id, userId, branchId, yardId, branchName, branchAddress, branchImage, yardName,
                    sportName, branchTimezone, startsAt, endsAt, hourlyPrice, amount, nextStatus, source, createdAt,
                    paymentExpiresAt, confirmDeadlineAt, List.copyOf(history));
        }

        public Map<String, Object> toApiMap() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", id);
            m.put("branch_id", branchId);
            m.put("branch_name", branchName);
            m.put("branch_address", branchAddress);
            m.put("branch_image", branchImage);
            m.put("yard_name", yardName);
            m.put("branch_timezone", branchTimezone);
            m.put("starts_at", startsAt.toString());
            m.put("ends_at", endsAt.toString());
            m.put("amount", amount);
            m.put("status", status);
            m.put("payment_expires_at", paymentExpiresAt != null ? paymentExpiresAt.toString() : null);
            m.put("confirm_deadline_at", confirmDeadlineAt != null ? confirmDeadlineAt.toString() : null);
            return m;
        }
    }

    public record PaymentIntentRecord(String id, String bookingId, String userId, long amount, String status, String refundStatus, Instant updatedAt) {
        public PaymentIntentRecord withRefund(String nextRefundStatus) {
            return new PaymentIntentRecord(id, bookingId, userId, amount, status, nextRefundStatus, Instant.now());
        }
    }

    public record BlockRecord(String id, String branchId, String yardId, Instant startsAt, Instant endsAt, String reason) {
        public Map<String, Object> toMap() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", id);
            m.put("branch_id", branchId);
            m.put("yard_id", yardId);
            m.put("starts_at", startsAt.toString());
            m.put("ends_at", endsAt.toString());
            m.put("reason", reason);
            return m;
        }
    }

    public record RefundRecord(String id, String orderCode, String provider, long amount, int percent, String reason, String status, String providerRef, Instant createdAt) {}

    public record AuditEventRecord(long id, Instant createdAt, String actorId, String action, String targetType, String targetId, Map<String, Object> details) {}

    private List<Map<String, Object>> sports = List.of();
    private List<Map<String, Object>> branches = List.of();
    private final Map<String, String> sportNameById = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> branchIndex = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> yardToBranch = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> yardIndex = new ConcurrentHashMap<>();

    private final Map<String, UserRecord> usersById = new ConcurrentHashMap<>();
    private final Map<String, String> userIdByIdentifier = new ConcurrentHashMap<>();
    private final Map<String, List<RoleEntry>> rolesByUser = new ConcurrentHashMap<>();
    private final Set<String> revokedTokens = ConcurrentHashMap.newKeySet();
    private final Map<String, OtpRecord> otpChallenges = new ConcurrentHashMap<>();
    private final Map<String, String> verificationTokens = new ConcurrentHashMap<>();
    private final Map<String, List<String>> favoritesByUser = new ConcurrentHashMap<>();
    private final Map<String, HoldRecord> holds = new ConcurrentHashMap<>();
    private final Map<String, BookingRecord> bookings = new ConcurrentHashMap<>();
    private final Map<String, PaymentIntentRecord> paymentIntents = new ConcurrentHashMap<>();
    private final Map<String, BlockRecord> blocks = new ConcurrentHashMap<>();
    private final Map<String, RefundRecord> refunds = new ConcurrentHashMap<>();
    private final List<AuditEventRecord> auditEvents = new CopyOnWriteArrayList<>();
    private final List<Map<String, Object>> deletionRequests = new CopyOnWriteArrayList<>();
    private final Map<String, Map<String, Object>> mediaStore = new ConcurrentHashMap<>();
    private final ObjectMapper mapper = new ObjectMapper();
    private final java.util.concurrent.atomic.AtomicLong auditSeq = new java.util.concurrent.atomic.AtomicLong(1);
    private final String tokenSecret = Optional.ofNullable(System.getenv("TOKEN_SECRET"))
            .filter(s -> !s.isBlank())
            .orElse("anta-cloud-demo-signing-secret-2026");

    @PostConstruct
    @SuppressWarnings("unchecked")
    public void init() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            ClassPathResource res = new ClassPathResource("data/catalog.json");
            if (res.exists()) {
                try (InputStream is = res.getInputStream()) {
                    Map<String, Object> root = mapper.readValue(is, new TypeReference<>() {});
                    if (root.get("sports") instanceof List<?> s) {
                        sports = (List<Map<String, Object>>) s;
                    }
                    if (root.get("branches") instanceof List<?> b) {
                        branches = (List<Map<String, Object>>) b;
                    }
                }
            }
            for (Map<String, Object> s : sports) {
                String sid = Objects.toString(s.get("id"), "");
                String sname = Objects.toString(s.get("name"), sid);
                if (!sid.isBlank()) sportNameById.put(sid, sname);
            }
            for (Map<String, Object> branch : branches) {
                putKey(branchIndex, branch.get("id"), branch);
                putKey(branchIndex, branch.get("slug"), branch);
                if (branch.get("yards") instanceof List<?> yards) {
                    for (Object yObj : yards) {
                        if (yObj instanceof Map<?, ?> rawYard) {
                            Map<String, Object> yard = (Map<String, Object>) rawYard;
                            String yId = Objects.toString(yard.get("id"), null);
                            if (yId != null) {
                                yardIndex.put(yId, yard);
                                yardToBranch.put(yId, branch);
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            throw new IllegalStateException("Failed to load catalog.json", e);
        }

        seedUser(DEMO_USER_ID, "customer@anta.vn", "Nguyễn Văn Khách", "anta123456", true);
        seedUser("user-owner-01", "owner@anta.vn", "Trần Minh Tâm (Chủ Sân)", "anta123456", true);
        seedUser("user-admin-01", "admin@anta.vn", "Quản Trị Viên Sàn", "anta123456", true);

        grantRole("user-admin-01", "admin", null);
        for (int i = 0; i < Math.min(5, branches.size()); i++) {
            grantRole("user-owner-01", "branch_owner", Objects.toString(branches.get(i).get("id"), null));
        }

        seedSampleBookings();
    }

    private void seedSampleBookings() {
        if (branches.isEmpty()) return;
        Map<String, Object> branch = branches.get(0);
        String branchId = Objects.toString(branch.get("id"), "branch-01");
        String branchName = Objects.toString(branch.get("name"), "Sân Anta");
        String branchAddress = Objects.toString(branch.get("address"), "");
        String branchTimezone = Objects.toString(branch.get("timezone"), "Asia/Ho_Chi_Minh");
        String branchImage = (branch.get("images") instanceof List<?> imgs && !imgs.isEmpty()) ? Objects.toString(imgs.get(0), null) : null;
        String yardId = "yard-demo-1";
        String yardName = "Sân 1";
        String sportName = "Pickleball";
        long price = 150000L;
        if (branch.get("yards") instanceof List<?> yards && !yards.isEmpty() && yards.get(0) instanceof Map<?, ?> y) {
            yardId = Objects.toString(y.get("id"), yardId);
            yardName = Objects.toString(y.get("name"), yardName);
            sportName = sportNameById.getOrDefault(Objects.toString(y.get("sport_id"), ""), "Thể thao");
            price = longVal(y.get("hourly_price"), 150000L);
        }
        Instant baseStart = java.time.LocalDate.now(java.time.ZoneId.of(branchTimezone))
                .atTime(18, 0).atZone(java.time.ZoneId.of(branchTimezone)).toInstant();
        BookingRecord b1 = new BookingRecord(
                "ANTA-BK-DEMO01", DEMO_USER_ID, branchId, yardId, branchName, branchAddress, branchImage,
                yardName, sportName, branchTimezone, baseStart, baseStart.plusSeconds(3600),
                price, price, "PENDING_OWNER_CONFIRMATION", "APP", Instant.now().minusSeconds(1800),
                null, Instant.now().plusSeconds(3600 * 6),
                List.of(new BookingStatusEvent(Instant.now().minusSeconds(1800), "PENDING_PAYMENT", "PENDING_OWNER_CONFIRMATION", "Khách đã thanh toán"))
        );
        bookings.put(b1.id(), b1);
        paymentIntents.put("pi-demo-01", new PaymentIntentRecord("pi-demo-01", b1.id(), DEMO_USER_ID, price, "SUCCEEDED", null, Instant.now().minusSeconds(1800)));
        recordAudit("user-admin-01", "system.bootstrap", "branch", branchId, Map.of("note", "Khởi tạo dữ liệu mẫu trên Cloud"));
    }

    private static void putKey(Map<String, Map<String, Object>> map, Object key, Map<String, Object> val) {
        if (key != null && !key.toString().isBlank()) {
            map.put(key.toString(), val);
        }
    }

    public UserRecord seedUser(String id, String identifier, String displayName, String password, boolean passwordLogin) {
        String normalized = identifier.trim().toLowerCase();
        UserRecord existing = usersById.get(id);
        Instant createdAt = existing != null ? existing.createdAt() : Instant.now();
        UserRecord user = new UserRecord(id, identifier.trim(), displayName, password, passwordLogin, "ACTIVE", createdAt);
        usersById.put(id, user);
        userIdByIdentifier.put(normalized, id);
        return user;
    }

    public List<RoleEntry> rolesFor(String userId) {
        return rolesByUser.computeIfAbsent(userId, k -> new CopyOnWriteArrayList<>());
    }

    public boolean hasRole(String userId, String role) {
        return rolesFor(userId).stream().anyMatch(r -> role.equalsIgnoreCase(r.role()));
    }

    public void grantRole(String userId, String role, String branchId) {
        List<RoleEntry> list = rolesFor(userId);
        RoleEntry entry = new RoleEntry(role, branchId != null && !branchId.isBlank() ? branchId : null);
        if (!list.contains(entry)) {
            list.add(entry);
        }
    }

    public void revokeRole(String userId, String role, String branchId) {
        String targetBranch = (branchId != null && !branchId.isBlank()) ? branchId : null;
        rolesFor(userId).removeIf(r -> role.equalsIgnoreCase(r.role()) && Objects.equals(targetBranch, r.branchId()));
    }

    public void recordAudit(String actorId, String action, String targetType, String targetId, Map<String, Object> details) {
        auditEvents.add(0, new AuditEventRecord(auditSeq.getAndIncrement(), Instant.now(), actorId, action, targetType, targetId, details != null ? details : Map.of()));
    }

    public String sportName(String sportId) {
        return sportNameById.getOrDefault(sportId, "Thể thao");
    }

    public List<Map<String, Object>> getSports() { return sports; }
    public List<Map<String, Object>> getBranches() { return branches; }
    public Map<String, Object> findBranch(String idOrSlug) { return branchIndex.get(idOrSlug); }
    public Map<String, Object> findYard(String yardId) { return yardIndex.get(yardId); }
    public Map<String, Object> findBranchByYard(String yardId) { return yardToBranch.get(yardId); }

    public Map<String, UserRecord> getUsersById() { return usersById; }
    public Map<String, String> getUserIdByIdentifier() { return userIdByIdentifier; }
    public Set<String> getRevokedTokens() { return revokedTokens; }
    public Map<String, OtpRecord> getOtpChallenges() { return otpChallenges; }
    public Map<String, String> getVerificationTokens() { return verificationTokens; }
    public Map<String, HoldRecord> getHolds() { return holds; }
    public Map<String, BookingRecord> getBookings() { return bookings; }
    public Map<String, PaymentIntentRecord> getPaymentIntents() { return paymentIntents; }
    public Map<String, BlockRecord> getBlocks() { return blocks; }
    public Map<String, RefundRecord> getRefunds() { return refunds; }
    public List<AuditEventRecord> getAuditEvents() { return auditEvents; }
    public List<Map<String, Object>> getDeletionRequests() { return deletionRequests; }
    public Map<String, Map<String, Object>> getMediaStore() { return mediaStore; }

    public List<String> favoriteIds(String userId) {
        return favoritesByUser.computeIfAbsent(userId, k -> new CopyOnWriteArrayList<>(DEFAULT_FAVORITES));
    }

    public UserRecord resolveUser(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            return null;
        }
        return parseSignedToken(authorizationHeader.substring(7).trim(), "access");
    }

    public UserRecord resolveRefreshToken(String token) {
        return parseSignedToken(token, "refresh");
    }

    public Map<String, Object> issueTokenBundle(UserRecord user) {
        String access = createSignedToken(user, "access", 86400L);
        String refresh = createSignedToken(user, "refresh", 2592000L);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("accessToken", access);
        data.put("refreshToken", refresh);
        data.put("expiresIn", 86400L);
        data.put("user", userMap(user));
        return data;
    }

    private String createSignedToken(UserRecord user, String kind, long ttlSeconds) {
        try {
            Map<String, Object> claims = new LinkedHashMap<>();
            claims.put("kind", kind);
            claims.put("id", user.id());
            claims.put("identifier", user.identifier());
            claims.put("displayName", user.displayName());
            claims.put("passwordLogin", user.passwordLogin());
            claims.put("exp", Instant.now().plusSeconds(ttlSeconds).getEpochSecond());
            claims.put("jti", UUID.randomUUID().toString());
            String payload = Base64.getUrlEncoder().withoutPadding().encodeToString(mapper.writeValueAsBytes(claims));
            String sig = hmacSha256(payload);
            return payload + "." + sig;
        } catch (Exception e) {
            throw new IllegalStateException("Token signing failed", e);
        }
    }

    private UserRecord parseSignedToken(String token, String expectedKind) {
        if (token == null || token.isBlank() || revokedTokens.contains(token)) {
            return null;
        }
        int dot = token.indexOf('.');
        if (dot <= 0) {
            return null;
        }
        String payload = token.substring(0, dot);
        String sig = token.substring(dot + 1);
        if (!hmacSha256(payload).equals(sig)) {
            return null;
        }
        try {
            byte[] decoded = Base64.getUrlDecoder().decode(payload);
            Map<String, Object> claims = mapper.readValue(decoded, new TypeReference<>() {});
            if (!expectedKind.equals(claims.get("kind"))) {
                return null;
            }
            long exp = longVal(claims.get("exp"), 0);
            if (Instant.now().getEpochSecond() > exp) {
                return null;
            }
            String id = Objects.toString(claims.get("id"), "");
            UserRecord existing = usersById.get(id);
            if (existing != null) {
                return existing;
            }
            String identifier = Objects.toString(claims.get("identifier"), "user@anta.vn");
            String displayName = Objects.toString(claims.get("displayName"), "Người Dùng Anta");
            boolean pwLogin = Boolean.TRUE.equals(claims.get("passwordLogin"));
            return seedUser(id, identifier, displayName, "", pwLogin);
        } catch (Exception e) {
            return null;
        }
    }

    private String hmacSha256(String data) {
        try {
            javax.crypto.Mac mac = javax.crypto.Mac.getInstance("HmacSHA256");
            mac.init(new javax.crypto.spec.SecretKeySpec(tokenSecret.getBytes(java.nio.charset.StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] raw = mac.doFinal(data.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(raw);
        } catch (Exception e) {
            throw new IllegalStateException("HMAC calculation failed", e);
        }
    }

    public static Map<String, Object> userMap(UserRecord user) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", user.id());
        m.put("identifier", user.identifier());
        m.put("displayName", user.displayName());
        m.put("passwordLogin", user.passwordLogin());
        return m;
    }

    public static ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("data", null);
        body.put("error", Map.of("code", code, "message", message));
        return ResponseEntity.status(status).body(body);
    }

    public static ResponseEntity<Map<String, Object>> unauthorized() {
        return error(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn");
    }

    /** Strips accents and normalizes 'đ' so Vietnamese accent-free search queries match cleanly. */
    public static String normalizeSearch(String input) {
        if (input == null) return "";
        String nfd = Normalizer.normalize(input.toLowerCase(Locale.ROOT), Normalizer.Form.NFD);
        return nfd.replaceAll("\\p{M}+", "").replace('đ', 'd').trim();
    }

    public static double haversineMeters(double lat1, double lon1, double lat2, double lon2) {
        final double r = 6371000.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return r * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    public Map<String, Object> branchWithDistance(Map<String, Object> branch, double userLat, double userLng) {
        Map<String, Object> copy = new LinkedHashMap<>(branch);
        double bLat = number(branch.get("lat"), userLat);
        double bLng = number(branch.get("lng"), userLng);
        double dist = haversineMeters(userLat, userLng, bLat, bLng);
        copy.put("distance_meters", Math.round(dist * 10.0) / 10.0);
        return copy;
    }

    public static double number(Object val, double fallback) {
        return (val instanceof Number n) ? n.doubleValue() : fallback;
    }

    public static long longVal(Object val, long fallback) {
        return (val instanceof Number n) ? n.longValue() : fallback;
    }
}
