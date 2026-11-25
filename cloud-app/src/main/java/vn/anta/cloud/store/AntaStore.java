package vn.anta.cloud.store;

import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.Normalizer;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Persistent store backed by PostgreSQL (or H2 in PostgreSQL mode for local dev) via JdbcTemplate,
 * with BCrypt password hashing and in-memory read-only catalog loaded from catalog.json.
 */
@Component
public class AntaStore {

    public static final String DEMO_USER_ID = "user-customer-01";

    public record UserRecord(String id, String identifier, String displayName, String passwordHash, boolean passwordLogin, String status, Instant createdAt) {}
    public record RoleEntry(String role, String branchId) {}
    public record OtpRecord(String challengeId, String identifier, String code, Instant expiresAt) {}
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
            String id, String userId, String branchId, String yardId,
            String branchName, String branchAddress, String branchImage,
            String yardName, String sportName, String branchTimezone,
            Instant startsAt, Instant endsAt, long hourlyPrice, long amount,
            String status, String source, Instant createdAt,
            Instant paymentExpiresAt, Instant confirmDeadlineAt,
            List<BookingStatusEvent> statusHistory
    ) {
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

    public record PaymentIntentRecord(String id, String bookingId, String userId, long amount, String status, String refundStatus, Instant updatedAt) {}

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

    private final JdbcTemplate jdbc;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();
    private final ObjectMapper mapper = new ObjectMapper();
    private final String tokenSecret = Optional.ofNullable(System.getenv("TOKEN_SECRET"))
            .filter(s -> !s.isBlank())
            .orElse("anta-cloud-demo-signing-secret-2026");

    private List<Map<String, Object>> sports = List.of();
    private List<Map<String, Object>> branches = List.of();
    private final Map<String, String> sportNameById = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> branchIndex = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> yardToBranch = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> yardIndex = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> mediaStore = new ConcurrentHashMap<>();

    private final RowMapper<UserRecord> userRowMapper = (rs, i) -> new UserRecord(
            rs.getString("id"), rs.getString("identifier"), rs.getString("display_name"),
            rs.getString("password_hash"), rs.getBoolean("password_login"),
            rs.getString("status"), Instant.ofEpochMilli(rs.getLong("created_at_ms"))
    );

    public AntaStore(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @PostConstruct
    @SuppressWarnings("unchecked")
    public void init() {
        loadCatalog();
        Long userCount = jdbc.queryForObject("SELECT COUNT(*) FROM app_users", Long.class);
        if (userCount == null || userCount == 0L) {
            createUser(DEMO_USER_ID, "customer@anta.vn", "Nguyễn Văn Khách", "anta123456", true);
            createUser("user-owner-01", "owner@anta.vn", "Trần Minh Tâm (Chủ Sân)", "anta123456", true);
            createUser("user-admin-01", "admin@anta.vn", "Quản Trị Viên Sàn", "anta123456", true);
            grantRole("user-admin-01", "admin", null);
            for (int i = 0; i < Math.min(5, branches.size()); i++) {
                grantRole("user-owner-01", "branch_owner", Objects.toString(branches.get(i).get("id"), null));
            }
            seedSampleBooking();
        }
    }

    @SuppressWarnings("unchecked")
    private void loadCatalog() {
        try {
            ClassPathResource res = new ClassPathResource("data/catalog.json");
            if (res.exists()) {
                try (InputStream is = res.getInputStream()) {
                    Map<String, Object> root = mapper.readValue(is, new TypeReference<>() {});
                    if (root.get("sports") instanceof List<?> s) sports = (List<Map<String, Object>>) s;
                    if (root.get("branches") instanceof List<?> b) branches = (List<Map<String, Object>>) b;
                }
            }
            for (Map<String, Object> s : sports) {
                String sid = Objects.toString(s.get("id"), "");
                if (!sid.isBlank()) sportNameById.put(sid, Objects.toString(s.get("name"), sid));
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
    }

    private void seedSampleBooking() {
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
        Instant baseStart = LocalDate.now(ZoneId.of(branchTimezone)).atTime(18, 0).atZone(ZoneId.of(branchTimezone)).toInstant();
        Instant created = Instant.now().minusSeconds(1800);
        saveNewBooking(new BookingRecord(
                "ANTA-BK-DEMO01", DEMO_USER_ID, branchId, yardId, branchName, branchAddress, branchImage,
                yardName, sportName, branchTimezone, baseStart, baseStart.plusSeconds(3600),
                price, price, "PENDING_OWNER_CONFIRMATION", "APP", created,
                null, Instant.now().plusSeconds(3600 * 6),
                List.of(new BookingStatusEvent(created, "PENDING_PAYMENT", "PENDING_OWNER_CONFIRMATION", "Khách đã thanh toán"))
        ));
        savePaymentIntent(new PaymentIntentRecord("pi-demo-01", "ANTA-BK-DEMO01", DEMO_USER_ID, price, "SUCCEEDED", null, created));
        recordAudit("user-admin-01", "system.bootstrap", "branch", branchId, Map.of("note", "Khởi tạo dữ liệu PostgreSQL"));
    }

    // ---- Catalog helpers ----

    public List<Map<String, Object>> getSports() { return sports; }
    public List<Map<String, Object>> getBranches() { return branches; }
    public Map<String, Object> findBranch(String idOrSlug) { return branchIndex.get(idOrSlug); }
    public Map<String, Object> findYard(String yardId) { return yardIndex.get(yardId); }
    public Map<String, Object> findBranchByYard(String yardId) { return yardToBranch.get(yardId); }
    public String sportName(String sportId) { return sportNameById.getOrDefault(sportId, "Thể thao"); }
    public Map<String, Map<String, Object>> getMediaStore() { return mediaStore; }

    // ---- Users & Password Hashing ----

    public boolean verifyPassword(String rawPassword, UserRecord user) {
        if (!user.passwordLogin()) return false;
        if (user.passwordHash() == null || user.passwordHash().isEmpty()) return false;
        return passwordEncoder.matches(rawPassword, user.passwordHash());
    }

    public UserRecord createUser(String id, String identifier, String displayName, String rawPassword, boolean passwordLogin) {
        String trimmed = identifier.trim();
        String norm = trimmed.toLowerCase(Locale.ROOT);
        String hash = (rawPassword != null && !rawPassword.isEmpty()) ? passwordEncoder.encode(rawPassword) : "";
        long now = Instant.now().toEpochMilli();
        jdbc.update(
                "INSERT INTO app_users(id, identifier, identifier_norm, display_name, password_hash, password_login, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                id, trimmed, norm, displayName.trim(), hash, passwordLogin, "ACTIVE", now
        );
        return new UserRecord(id, trimmed, displayName.trim(), hash, passwordLogin, "ACTIVE", Instant.ofEpochMilli(now));
    }

    public UserRecord updateUserDisplayName(String userId, String displayName) {
        jdbc.update("UPDATE app_users SET display_name = ? WHERE id = ?", displayName.trim(), userId);
        return findUserById(userId);
    }

    public void updateUserPassword(String userId, String rawPassword) {
        String hash = passwordEncoder.encode(rawPassword);
        jdbc.update("UPDATE app_users SET password_hash = ?, password_login = true WHERE id = ?", hash, userId);
    }

    @Transactional
    public void deleteUser(String userId) {
        jdbc.update("DELETE FROM user_roles WHERE user_id = ?", userId);
        jdbc.update("DELETE FROM user_favorites WHERE user_id = ?", userId);
        jdbc.update("DELETE FROM app_users WHERE id = ?", userId);
    }

    public UserRecord findUserById(String id) {
        List<UserRecord> rows = jdbc.query("SELECT * FROM app_users WHERE id = ?", userRowMapper, id);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public UserRecord findUserByIdentifier(String identifier) {
        if (identifier == null) return null;
        List<UserRecord> rows = jdbc.query("SELECT * FROM app_users WHERE identifier_norm = ?", userRowMapper, identifier.trim().toLowerCase(Locale.ROOT));
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<UserRecord> listAllUsers() {
        return jdbc.query("SELECT * FROM app_users ORDER BY created_at_ms DESC", userRowMapper);
    }

    // ---- Roles ----

    public List<RoleEntry> rolesFor(String userId) {
        return jdbc.query(
                "SELECT role, branch_id FROM user_roles WHERE user_id = ?",
                (rs, i) -> {
                    String bid = rs.getString("branch_id");
                    return new RoleEntry(rs.getString("role"), (bid == null || bid.isEmpty()) ? null : bid);
                },
                userId
        );
    }

    public boolean hasRole(String userId, String role) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM user_roles WHERE user_id = ? AND LOWER(role) = LOWER(?)",
                Integer.class, userId, role
        );
        return count != null && count > 0;
    }

    @Transactional
    public void grantRole(String userId, String role, String branchId) {
        String bid = (branchId != null && !branchId.isBlank()) ? branchId : "";
        jdbc.update("DELETE FROM user_roles WHERE user_id = ? AND role = ? AND branch_id = ?", userId, role, bid);
        jdbc.update("INSERT INTO user_roles(user_id, role, branch_id) VALUES (?, ?, ?)", userId, role, bid);
    }

    public void revokeRole(String userId, String role, String branchId) {
        String bid = (branchId != null && !branchId.isBlank()) ? branchId : "";
        jdbc.update("DELETE FROM user_roles WHERE user_id = ? AND LOWER(role) = LOWER(?) AND branch_id = ?", userId, role, bid);
    }

    public long countAdmins() {
        Long count = jdbc.queryForObject("SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE LOWER(role) = 'admin'", Long.class);
        return count != null ? count : 0L;
    }

    // ---- Favorites ----

    public List<String> favoriteIds(String userId) {
        return jdbc.queryForList("SELECT branch_id FROM user_favorites WHERE user_id = ? ORDER BY sort_order DESC", String.class, userId);
    }

    @Transactional
    public void addFavorite(String userId, String branchId) {
        jdbc.update("DELETE FROM user_favorites WHERE user_id = ? AND branch_id = ?", userId, branchId);
        jdbc.update("INSERT INTO user_favorites(user_id, branch_id, sort_order) VALUES (?, ?, ?)", userId, branchId, Instant.now().toEpochMilli());
    }

    public void removeFavorite(String userId, String branchId) {
        jdbc.update("DELETE FROM user_favorites WHERE user_id = ? AND branch_id = ?", userId, branchId);
    }

    // ---- OTP & Verification Tokens ----

    @Transactional
    public void saveOtpChallenge(String challengeId, String identifier, String code, Instant expiresAt) {
        jdbc.update("DELETE FROM otp_challenges WHERE challenge_id = ?", challengeId);
        jdbc.update("INSERT INTO otp_challenges(challenge_id, identifier, code, expires_at_ms) VALUES (?, ?, ?, ?)",
                challengeId, identifier, code, expiresAt.toEpochMilli());
    }

    public OtpRecord findOtpChallenge(String challengeId) {
        List<OtpRecord> rows = jdbc.query(
                "SELECT * FROM otp_challenges WHERE challenge_id = ? AND expires_at_ms > ?",
                (rs, i) -> new OtpRecord(rs.getString("challenge_id"), rs.getString("identifier"),
                        rs.getString("code"), Instant.ofEpochMilli(rs.getLong("expires_at_ms"))),
                challengeId, Instant.now().toEpochMilli()
        );
        return rows.isEmpty() ? null : rows.get(0);
    }

    @Transactional
    public void saveVerificationToken(String token, String identifier) {
        long exp = Instant.now().plusSeconds(1800).toEpochMilli();
        jdbc.update("INSERT INTO verification_tokens(token, identifier, expires_at_ms) VALUES (?, ?, ?)", token, identifier, exp);
    }

    @Transactional
    public boolean consumeVerificationToken(String token) {
        if (token == null || token.isBlank()) return false;
        int deleted = jdbc.update("DELETE FROM verification_tokens WHERE token = ? AND expires_at_ms > ?", token, Instant.now().toEpochMilli());
        return deleted > 0;
    }

    // ---- Holds, Bookings, Blocks & Payment Intents ----

    public boolean isSlotTaken(String yardId, Instant start, Instant end, Instant now) {
        long s = start.toEpochMilli();
        long e = end.toEpochMilli();
        Integer bookingHits = jdbc.queryForObject(
                "SELECT COUNT(*) FROM bookings WHERE yard_id = ? AND status NOT IN ('CANCELLED', 'EXPIRED') AND starts_at_ms < ? AND ends_at_ms > ?",
                Integer.class, yardId, e, s
        );
        if (bookingHits != null && bookingHits > 0) return true;

        Integer blockHits = jdbc.queryForObject(
                "SELECT COUNT(*) FROM court_blocks WHERE yard_id = ? AND starts_at_ms < ? AND ends_at_ms > ?",
                Integer.class, yardId, e, s
        );
        if (blockHits != null && blockHits > 0) return true;

        Integer holdHits = jdbc.queryForObject(
                "SELECT COUNT(*) FROM booking_holds WHERE yard_id = ? AND expires_at_ms > ? AND starts_at_ms < ? AND ends_at_ms > ?",
                Integer.class, yardId, now.toEpochMilli(), e, s
        );
        return holdHits != null && holdHits > 0;
    }

    public void saveHold(HoldRecord hold) {
        jdbc.update(
                "INSERT INTO booking_holds(hold_id, user_id, yard_id, branch_id, starts_at_ms, ends_at_ms, total, expires_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                hold.holdId(), hold.userId(), hold.yardId(), hold.branchId(),
                hold.startsAt().toEpochMilli(), hold.endsAt().toEpochMilli(), hold.total(), hold.expiresAt().toEpochMilli()
        );
    }

    @Transactional
    public HoldRecord consumeHold(String holdId) {
        List<HoldRecord> rows = jdbc.query(
                "SELECT * FROM booking_holds WHERE hold_id = ? AND expires_at_ms > ?",
                (rs, i) -> new HoldRecord(
                        rs.getString("hold_id"), rs.getString("user_id"), rs.getString("yard_id"), rs.getString("branch_id"),
                        Instant.ofEpochMilli(rs.getLong("starts_at_ms")), Instant.ofEpochMilli(rs.getLong("ends_at_ms")),
                        rs.getLong("total"), Instant.ofEpochMilli(rs.getLong("expires_at_ms"))
                ),
                holdId, Instant.now().toEpochMilli()
        );
        if (rows.isEmpty()) return null;
        jdbc.update("DELETE FROM booking_holds WHERE hold_id = ?", holdId);
        return rows.get(0);
    }

    @Transactional
    public void saveNewBooking(BookingRecord b) {
        jdbc.update(
                """
                INSERT INTO bookings(id, user_id, branch_id, yard_id, branch_name, branch_address, branch_image,
                  yard_name, sport_name, branch_timezone, starts_at_ms, ends_at_ms, hourly_price, amount,
                  status, source, created_at_ms, payment_expires_at_ms, confirm_deadline_at_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                b.id(), b.userId(), b.branchId(), b.yardId(), b.branchName(), b.branchAddress(), b.branchImage(),
                b.yardName(), b.sportName(), b.branchTimezone(), b.startsAt().toEpochMilli(), b.endsAt().toEpochMilli(),
                b.hourlyPrice(), b.amount(), b.status(), b.source(), b.createdAt().toEpochMilli(),
                b.paymentExpiresAt() != null ? b.paymentExpiresAt().toEpochMilli() : null,
                b.confirmDeadlineAt() != null ? b.confirmDeadlineAt().toEpochMilli() : null
        );
        for (BookingStatusEvent ev : b.statusHistory()) {
            jdbc.update(
                    "INSERT INTO booking_status_events(booking_id, created_at_ms, from_status, to_status, reason) VALUES (?, ?, ?, ?, ?)",
                    b.id(), ev.createdAt().toEpochMilli(), ev.fromStatus(), ev.toStatus(), ev.reason()
            );
        }
    }

    @Transactional
    public BookingRecord updateBookingStatus(String bookingId, String nextStatus, String reason) {
        BookingRecord existing = findBooking(bookingId);
        if (existing == null) return null;
        jdbc.update("UPDATE bookings SET status = ? WHERE id = ?", nextStatus, bookingId);
        jdbc.update(
                "INSERT INTO booking_status_events(booking_id, created_at_ms, from_status, to_status, reason) VALUES (?, ?, ?, ?, ?)",
                bookingId, Instant.now().toEpochMilli(), existing.status(), nextStatus, reason
        );
        return findBooking(bookingId);
    }

    public BookingRecord findBooking(String id) {
        List<BookingRecord> rows = jdbc.query("SELECT * FROM bookings WHERE id = ?", bookingRowMapper(true), id);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<BookingRecord> listBookingsByUser(String userId) {
        return jdbc.query("SELECT * FROM bookings WHERE user_id = ? ORDER BY starts_at_ms DESC", bookingRowMapper(false), userId);
    }

    public List<BookingRecord> listBookingsByBranch(String branchId) {
        return jdbc.query("SELECT * FROM bookings WHERE branch_id = ? ORDER BY created_at_ms DESC", bookingRowMapper(false), branchId);
    }

    public List<BookingRecord> listAllBookings() {
        return jdbc.query("SELECT * FROM bookings ORDER BY created_at_ms DESC", bookingRowMapper(false));
    }

    private RowMapper<BookingRecord> bookingRowMapper(boolean includeHistory) {
        return (rs, i) -> {
            String id = rs.getString("id");
            Long payExp = rs.getObject("payment_expires_at_ms", Long.class);
            Long confExp = rs.getObject("confirm_deadline_at_ms", Long.class);
            List<BookingStatusEvent> history = includeHistory
                    ? jdbc.query(
                            "SELECT * FROM booking_status_events WHERE booking_id = ? ORDER BY id ASC",
                            (hrs, hi) -> new BookingStatusEvent(
                                    Instant.ofEpochMilli(hrs.getLong("created_at_ms")),
                                    hrs.getString("from_status"), hrs.getString("to_status"), hrs.getString("reason")
                            ),
                            id
                    )
                    : List.of();
            return new BookingRecord(
                    id, rs.getString("user_id"), rs.getString("branch_id"), rs.getString("yard_id"),
                    rs.getString("branch_name"), rs.getString("branch_address"), rs.getString("branch_image"),
                    rs.getString("yard_name"), rs.getString("sport_name"), rs.getString("branch_timezone"),
                    Instant.ofEpochMilli(rs.getLong("starts_at_ms")), Instant.ofEpochMilli(rs.getLong("ends_at_ms")),
                    rs.getLong("hourly_price"), rs.getLong("amount"), rs.getString("status"), rs.getString("source"),
                    Instant.ofEpochMilli(rs.getLong("created_at_ms")),
                    payExp != null ? Instant.ofEpochMilli(payExp) : null,
                    confExp != null ? Instant.ofEpochMilli(confExp) : null,
                    history
            );
        };
    }

    @Transactional
    public void savePaymentIntent(PaymentIntentRecord pi) {
        jdbc.update("DELETE FROM payment_intents WHERE id = ?", pi.id());
        jdbc.update(
                "INSERT INTO payment_intents(id, booking_id, user_id, amount, status, refund_status, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                pi.id(), pi.bookingId(), pi.userId(), pi.amount(), pi.status(), pi.refundStatus(), pi.updatedAt().toEpochMilli()
        );
    }

    public PaymentIntentRecord findPaymentIntent(String id) {
        List<PaymentIntentRecord> rows = jdbc.query(
                "SELECT * FROM payment_intents WHERE id = ?",
                (rs, i) -> new PaymentIntentRecord(
                        rs.getString("id"), rs.getString("booking_id"), rs.getString("user_id"),
                        rs.getLong("amount"), rs.getString("status"), rs.getString("refund_status"),
                        Instant.ofEpochMilli(rs.getLong("updated_at_ms"))
                ),
                id
        );
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<PaymentIntentRecord> listPaymentIntents() {
        return jdbc.query(
                "SELECT * FROM payment_intents ORDER BY updated_at_ms DESC",
                (rs, i) -> new PaymentIntentRecord(
                        rs.getString("id"), rs.getString("booking_id"), rs.getString("user_id"),
                        rs.getLong("amount"), rs.getString("status"), rs.getString("refund_status"),
                        Instant.ofEpochMilli(rs.getLong("updated_at_ms"))
                )
        );
    }

    public void saveBlock(BlockRecord blk) {
        jdbc.update(
                "INSERT INTO court_blocks(id, branch_id, yard_id, starts_at_ms, ends_at_ms, reason) VALUES (?, ?, ?, ?, ?, ?)",
                blk.id(), blk.branchId(), blk.yardId(), blk.startsAt().toEpochMilli(), blk.endsAt().toEpochMilli(), blk.reason()
        );
    }

    public BlockRecord findBlock(String id) {
        List<BlockRecord> rows = jdbc.query(
                "SELECT * FROM court_blocks WHERE id = ?",
                (rs, i) -> new BlockRecord(
                        rs.getString("id"), rs.getString("branch_id"), rs.getString("yard_id"),
                        Instant.ofEpochMilli(rs.getLong("starts_at_ms")), Instant.ofEpochMilli(rs.getLong("ends_at_ms")),
                        rs.getString("reason")
                ),
                id
        );
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<BlockRecord> listBlocksByBranch(String branchId) {
        return jdbc.query(
                "SELECT * FROM court_blocks WHERE branch_id = ?",
                (rs, i) -> new BlockRecord(
                        rs.getString("id"), rs.getString("branch_id"), rs.getString("yard_id"),
                        Instant.ofEpochMilli(rs.getLong("starts_at_ms")), Instant.ofEpochMilli(rs.getLong("ends_at_ms")),
                        rs.getString("reason")
                ),
                branchId
        );
    }

    public void deleteBlock(String id) {
        jdbc.update("DELETE FROM court_blocks WHERE id = ?", id);
    }

    @Transactional
    public void saveRefund(RefundRecord rf) {
        jdbc.update("DELETE FROM refunds WHERE id = ?", rf.id());
        jdbc.update(
                "INSERT INTO refunds(id, order_code, provider, amount, percent, reason, status, provider_ref, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rf.id(), rf.orderCode(), rf.provider(), rf.amount(), rf.percent(), rf.reason(), rf.status(), rf.providerRef(), rf.createdAt().toEpochMilli()
        );
    }

    public RefundRecord findRefund(String id) {
        List<RefundRecord> rows = jdbc.query(
                "SELECT * FROM refunds WHERE id = ?",
                (rs, i) -> new RefundRecord(
                        rs.getString("id"), rs.getString("order_code"), rs.getString("provider"),
                        rs.getLong("amount"), rs.getInt("percent"), rs.getString("reason"),
                        rs.getString("status"), rs.getString("provider_ref"), Instant.ofEpochMilli(rs.getLong("created_at_ms"))
                ),
                id
        );
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<RefundRecord> listRefunds() {
        return jdbc.query(
                "SELECT * FROM refunds ORDER BY created_at_ms DESC",
                (rs, i) -> new RefundRecord(
                        rs.getString("id"), rs.getString("order_code"), rs.getString("provider"),
                        rs.getLong("amount"), rs.getInt("percent"), rs.getString("reason"),
                        rs.getString("status"), rs.getString("provider_ref"), Instant.ofEpochMilli(rs.getLong("created_at_ms"))
                )
        );
    }

    public void recordAudit(String actorId, String action, String targetType, String targetId, Map<String, Object> details) {
        String json;
        try {
            json = mapper.writeValueAsString(details != null ? details : Map.of());
        } catch (Exception e) {
            json = "{}";
        }
        jdbc.update(
                "INSERT INTO audit_events(created_at_ms, actor_id, action, target_type, target_id, details_json) VALUES (?, ?, ?, ?, ?, ?)",
                Instant.now().toEpochMilli(), actorId, action, targetType, targetId, json
        );
    }

    public List<AuditEventRecord> listAuditEvents() {
        return jdbc.query(
                "SELECT * FROM audit_events ORDER BY id DESC LIMIT 200",
                (rs, i) -> {
                    Map<String, Object> details;
                    try {
                        details = mapper.readValue(rs.getString("details_json"), new TypeReference<>() {});
                    } catch (Exception e) {
                        details = Map.of();
                    }
                    return new AuditEventRecord(
                            rs.getLong("id"), Instant.ofEpochMilli(rs.getLong("created_at_ms")),
                            rs.getString("actor_id"), rs.getString("action"),
                            rs.getString("target_type"), rs.getString("target_id"), details
                    );
                }
        );
    }

    // ---- Tokens & Revocation ----

    public void revokeToken(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) return;
        String hash = sha256Hex(rawToken);
        jdbc.update("DELETE FROM revoked_tokens WHERE token_hash = ?", hash);
        jdbc.update("INSERT INTO revoked_tokens(token_hash, revoked_at_ms) VALUES (?, ?)", hash, Instant.now().toEpochMilli());
    }

    public boolean isTokenRevoked(String rawToken) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM revoked_tokens WHERE token_hash = ?", Integer.class, sha256Hex(rawToken));
        return count != null && count > 0;
    }

    public UserRecord resolveUser(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) return null;
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
            return payload + "." + hmacSha256(payload);
        } catch (Exception e) {
            throw new IllegalStateException("Token signing failed", e);
        }
    }

    private UserRecord parseSignedToken(String token, String expectedKind) {
        if (token == null || token.isBlank() || isTokenRevoked(token)) return null;
        int dot = token.indexOf('.');
        if (dot <= 0) return null;
        String payload = token.substring(0, dot);
        String sig = token.substring(dot + 1);
        if (!hmacSha256(payload).equals(sig)) return null;
        try {
            byte[] decoded = Base64.getUrlDecoder().decode(payload);
            Map<String, Object> claims = mapper.readValue(decoded, new TypeReference<>() {});
            if (!expectedKind.equals(claims.get("kind"))) return null;
            if (Instant.now().getEpochSecond() > longVal(claims.get("exp"), 0)) return null;
            return findUserById(Objects.toString(claims.get("id"), ""));
        } catch (Exception e) {
            return null;
        }
    }

    private String hmacSha256(String data) {
        try {
            javax.crypto.Mac mac = javax.crypto.Mac.getInstance("HmacSHA256");
            mac.init(new javax.crypto.spec.SecretKeySpec(tokenSecret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("HMAC calculation failed", e);
        }
    }

    private static String sha256Hex(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(digest.length * 2);
            for (byte b : digest) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 failed", e);
        }
    }

    private static void putKey(Map<String, Map<String, Object>> map, Object key, Map<String, Object> val) {
        if (key != null && !key.toString().isBlank()) map.put(key.toString(), val);
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
