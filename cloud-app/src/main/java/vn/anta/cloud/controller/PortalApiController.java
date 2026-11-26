package vn.anta.cloud.controller;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import vn.anta.cloud.store.AntaStore;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;

/** REST APIs serving the Owner (/owner/) and Admin (/admin/) web portals backed by AntaStore (PostgreSQL). */
@RestController
@RequestMapping("/api/v1")
public class PortalApiController {

    private final AntaStore store;

    public PortalApiController(AntaStore store) {
        this.store = store;
    }

    // ---- Admin Portal ----

    @GetMapping("/admin/branches")
    public ResponseEntity<Map<String, Object>> adminBranches(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> list = store.getBranches().stream()
                .map(b -> Map.<String, Object>of("id", Objects.toString(b.get("id"), ""), "name", Objects.toString(b.get("name"), "")))
                .toList();
        return ResponseEntity.ok(Map.of("data", list));
    }

    @GetMapping("/admin/stats")
    public ResponseEntity<Map<String, Object>> adminStats(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<AntaStore.UserRecord> allUsers = store.listAllUsers();
        List<AntaStore.BookingRecord> allBookings = store.listAllBookings();
        List<AntaStore.PaymentIntentRecord> allPayments = store.listPaymentIntents();
        List<AntaStore.RefundRecord> allRefunds = store.listRefunds();

        long activeUsers = allUsers.stream().filter(u -> "ACTIVE".equals(u.status())).count();
        long confirmed = allBookings.stream().filter(b -> "CONFIRMED".equals(b.status())).count();
        long pending = allBookings.stream()
                .filter(b -> "PENDING_PAYMENT".equals(b.status()) || "PENDING_OWNER_CONFIRMATION".equals(b.status())).count();
        long cancelled = allBookings.stream().filter(b -> "CANCELLED".equals(b.status())).count();
        long payCount = allPayments.stream().filter(p -> "SUCCEEDED".equals(p.status())).count();
        long paidTotal = allPayments.stream().filter(p -> "SUCCEEDED".equals(p.status())).mapToLong(AntaStore.PaymentIntentRecord::amount).sum();
        long refundedTotal = allRefunds.stream().filter(r -> "SUCCEEDED".equals(r.status())).mapToLong(AntaStore.RefundRecord::amount).sum();
        long openRefunds = allRefunds.stream().filter(r -> !"SUCCEEDED".equals(r.status())).count();
        long latePayments = allPayments.stream().filter(p -> "NEEDS_REVIEW".equals(p.status())).count();

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("users", Map.of("active", activeUsers, "total", allUsers.size()));
        stats.put("bookings", Map.of("confirmed", confirmed, "pending", pending, "cancelled", cancelled));
        stats.put("payments", Map.of("count", payCount, "paid", paidTotal, "refunded", refundedTotal));
        stats.put("openRefunds", openRefunds);
        stats.put("latePaymentsToReview", latePayments);
        stats.put("pendingDeletions", 0);
        stats.put("pendingBranchSubmissions", store.countPendingSubmissions());
        return ResponseEntity.ok(Map.of("data", stats));
    }

    @GetMapping("/admin/users")
    public ResponseEntity<Map<String, Object>> adminUsers(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam(required = false) String q
    ) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        String normQ = (q != null && !q.isBlank()) ? AntaStore.normalizeSearch(q) : null;
        List<Map<String, Object>> rows = store.listAllUsers().stream()
                .filter(u -> normQ == null
                        || AntaStore.normalizeSearch(u.identifier()).contains(normQ)
                        || AntaStore.normalizeSearch(u.displayName()).contains(normQ)
                        || u.id().toLowerCase(Locale.ROOT).contains(normQ))
                .map(u -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", u.id());
                    row.put("identifier", u.identifier());
                    row.put("display_name", u.displayName());
                    row.put("status", u.status());
                    row.put("roles", store.rolesFor(u.id()).stream()
                            .map(r -> {
                                Map<String, Object> rm = new LinkedHashMap<>();
                                rm.put("role", r.role());
                                rm.put("branchId", r.branchId());
                                return rm;
                            }).toList());
                    row.put("created_at", u.createdAt().toString());
                    return row;
                }).toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @PostMapping("/admin/roles")
    public ResponseEntity<Map<String, Object>> grantRole(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord actor = requireAdmin(auth);
        if (actor == null) return adminDenied(auth);
        String userId = Objects.toString(req.get("userId"), "");
        String role = Objects.toString(req.get("role"), "");
        String branchId = req.get("branchId") != null ? Objects.toString(req.get("branchId")) : null;
        if (store.findUserById(userId) == null || role.isBlank()) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Thiếu userId hoặc role");
        }
        store.grantRole(userId, role, branchId);
        store.recordAudit(actor.id(), "role.grant", "user", userId, Map.of("role", role, "branchId", Objects.toString(branchId, "")));
        return ResponseEntity.ok(Map.of("data", Map.of("ok", true)));
    }

    @DeleteMapping("/admin/roles")
    public ResponseEntity<Map<String, Object>> revokeRole(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord actor = requireAdmin(auth);
        if (actor == null) return adminDenied(auth);
        String userId = Objects.toString(req.get("userId"), "");
        String role = Objects.toString(req.get("role"), "");
        String branchId = req.get("branchId") != null ? Objects.toString(req.get("branchId")) : null;
        if ("admin".equalsIgnoreCase(role) && userId.equals(actor.id()) && store.countAdmins() <= 1) {
            return AntaStore.error(HttpStatus.CONFLICT, "LAST_ADMIN", "Không thể thu hồi quyền của quản trị viên cuối cùng");
        }
        store.revokeRole(userId, role, branchId);
        store.recordAudit(actor.id(), "role.revoke", "user", userId, Map.of("role", role, "branchId", Objects.toString(branchId, "")));
        return ResponseEntity.ok(Map.of("data", Map.of("ok", true)));
    }

    @GetMapping("/admin/bookings")
    public ResponseEntity<Map<String, Object>> adminBookings(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam(required = false) String status
    ) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> rows = store.listAllBookings().stream()
                .filter(b -> status == null || status.isBlank() || status.equalsIgnoreCase(b.status()))
                .map(b -> {
                    AntaStore.UserRecord u = store.findUserById(b.userId());
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", b.id());
                    row.put("identifier", u != null ? u.identifier() : b.userId());
                    row.put("branch", b.branchName());
                    row.put("yard", b.yardName());
                    row.put("starts_at", b.startsAt().toString());
                    row.put("ends_at", b.endsAt().toString());
                    row.put("amount", b.amount());
                    row.put("status", b.status());
                    row.put("created_at", b.createdAt().toString());
                    return row;
                }).toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @GetMapping("/admin/payment-intents")
    public ResponseEntity<Map<String, Object>> adminPayments(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam(required = false) String status
    ) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> rows = store.listPaymentIntents().stream()
                .filter(p -> status == null || status.isBlank() || status.equalsIgnoreCase(p.status()))
                .map(p -> {
                    AntaStore.UserRecord u = store.findUserById(p.userId());
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", p.id());
                    row.put("order_code", p.bookingId());
                    row.put("identifier", u != null ? u.identifier() : p.userId());
                    row.put("provider", "sandbox");
                    row.put("target", "BOOKING");
                    row.put("amount", p.amount());
                    row.put("status", p.status());
                    row.put("refund_status", p.refundStatus());
                    row.put("updated_at", p.updatedAt().toString());
                    return row;
                }).toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @PostMapping("/admin/payment-intents/{id}/refund")
    public ResponseEntity<Map<String, Object>> adminRefundIntent(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord actor = requireAdmin(auth);
        if (actor == null) return adminDenied(auth);
        AntaStore.PaymentIntentRecord pi = store.findPaymentIntent(id);
        if (pi == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy giao dịch");
        String refundId = "rf-" + UUID.randomUUID().toString().substring(0, 8);
        store.savePaymentIntent(new AntaStore.PaymentIntentRecord(pi.id(), pi.bookingId(), pi.userId(), pi.amount(), pi.status(), "MANUAL_REVIEW", Instant.now()));
        store.saveRefund(new AntaStore.RefundRecord(refundId, pi.bookingId(), "sandbox", pi.amount(), 100, "Admin khởi tạo hoàn tiền", "MANUAL_REVIEW", null, Instant.now()));
        store.recordAudit(actor.id(), "payment.refund", "payment_intent", id, Map.of("refundId", refundId));
        return ResponseEntity.ok(Map.of("data", Map.of("refundId", refundId)));
    }

    @GetMapping("/admin/refunds")
    public ResponseEntity<Map<String, Object>> adminRefunds(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam(required = false) String status
    ) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> rows = store.listRefunds().stream()
                .filter(r -> status == null || status.isBlank() || status.equalsIgnoreCase(r.status()))
                .map(r -> {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("id", r.id());
                    m.put("order_code", r.orderCode());
                    m.put("provider", r.provider());
                    m.put("amount", r.amount());
                    m.put("percent", r.percent());
                    m.put("reason", r.reason());
                    m.put("status", r.status());
                    m.put("provider_ref", r.providerRef());
                    m.put("created_at", r.createdAt().toString());
                    return m;
                }).toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @PostMapping("/admin/refunds/{id}/resolve")
    public ResponseEntity<Map<String, Object>> resolveRefund(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord actor = requireAdmin(auth);
        if (actor == null) return adminDenied(auth);
        AntaStore.RefundRecord rf = store.findRefund(id);
        if (rf == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy yêu cầu hoàn tiền");
        String outcome = Objects.toString(req.get("outcome"), "SUCCEEDED");
        String providerRef = req.get("providerRef") != null ? Objects.toString(req.get("providerRef")) : rf.providerRef();
        store.saveRefund(new AntaStore.RefundRecord(rf.id(), rf.orderCode(), rf.provider(), rf.amount(), rf.percent(), rf.reason(), outcome, providerRef, rf.createdAt()));
        store.recordAudit(actor.id(), "refund.resolve", "refund", id, Map.of("outcome", outcome));
        return ResponseEntity.ok(Map.of("data", Map.of("status", outcome)));
    }

    @GetMapping("/admin/deletion-requests")
    public ResponseEntity<Map<String, Object>> adminDeletions(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        return ResponseEntity.ok(Map.of("data", List.of()));
    }

    @GetMapping("/admin/audit-events")
    public ResponseEntity<Map<String, Object>> adminAudit(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> rows = store.listAuditEvents().stream()
                .map(e -> Map.<String, Object>of(
                        "id", e.id(),
                        "created_at", e.createdAt().toString(),
                        "actor_id", e.actorId(),
                        "action", e.action(),
                        "target_type", e.targetType(),
                        "target_id", e.targetId(),
                        "details", e.details()
                )).toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @GetMapping("/admin/submissions")
    public ResponseEntity<Map<String, Object>> adminSubmissions(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam(required = false) String status
    ) {
        if (requireAdmin(auth) == null) return adminDenied(auth);
        List<Map<String, Object>> rows = store.listSubmissions(status).stream()
                .map(this::toSubmissionMap)
                .toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @PostMapping("/admin/submissions/{id}/approve")
    public ResponseEntity<Map<String, Object>> adminApproveSubmission(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        AntaStore.UserRecord admin = requireAdmin(auth);
        if (admin == null) return adminDenied(auth);
        String note = req != null && req.get("note") != null ? Objects.toString(req.get("note"), "").trim() : "Đã duyệt đưa lên hệ thống";
        try {
            Map<String, Object> res = store.approveBranchSubmission(id, admin.id(), note.isEmpty() ? "Đã duyệt đưa lên hệ thống" : note);
            return ResponseEntity.ok(Map.of("data", res));
        } catch (IllegalArgumentException ex) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy hồ sơ đăng ký sân");
        } catch (IllegalStateException ex) {
            return AntaStore.error(HttpStatus.CONFLICT, "CONFLICT", ex.getMessage());
        }
    }

    @PostMapping("/admin/submissions/{id}/reject")
    public ResponseEntity<Map<String, Object>> adminRejectSubmission(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        AntaStore.UserRecord admin = requireAdmin(auth);
        if (admin == null) return adminDenied(auth);
        String reason = req != null ? Objects.toString(req.get("reason"), "").trim() : "";
        if (reason.isEmpty()) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Vui lòng nhập lý do từ chối");
        }
        try {
            store.rejectBranchSubmission(id, admin.id(), reason);
            return ResponseEntity.ok(Map.of("data", Map.of("id", id, "status", "REJECTED")));
        } catch (IllegalArgumentException ex) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy hồ sơ đăng ký sân");
        } catch (IllegalStateException ex) {
            return AntaStore.error(HttpStatus.CONFLICT, "CONFLICT", ex.getMessage());
        }
    }

    // ---- Owner Portal ----

    @GetMapping("/owner/submissions")
    public ResponseEntity<Map<String, Object>> ownerSubmissions(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        List<Map<String, Object>> rows = store.listSubmissionsByOwner(user.id()).stream()
                .map(this::toSubmissionMap)
                .toList();
        return ResponseEntity.ok(Map.of("data", rows));
    }

    @PostMapping("/owner/submissions")
    @SuppressWarnings("unchecked")
    public ResponseEntity<Map<String, Object>> createOwnerSubmission(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        if (req == null) return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Thiếu thông tin đăng ký sân");

        String type = Objects.toString(req.get("submissionType"), "NEW_BRANCH").trim().toUpperCase(Locale.ROOT);
        if (!"NEW_BRANCH".equals(type) && !"ADD_YARDS".equals(type)) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Loại đăng ký không hợp lệ");
        }

        String targetBranchId = req.get("targetBranchId") != null ? Objects.toString(req.get("targetBranchId"), "").trim() : null;
        if ("ADD_YARDS".equals(type)) {
            if (targetBranchId == null || targetBranchId.isEmpty()) {
                return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Vui lòng chọn cơ sở muốn thêm sân");
            }
            if (!canManageBranch(user, targetBranchId)) {
                return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Bạn không có quyền quản lý cơ sở này");
            }
            Map<String, Object> target = store.findBranch(targetBranchId);
            if (target == null) {
                return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy cơ sở");
            }
        }

        String name = Objects.toString(req.get("name"), "").trim();
        String address = Objects.toString(req.get("address"), "").trim();
        if ("ADD_YARDS".equals(type)) {
            Map<String, Object> target = store.findBranch(targetBranchId);
            if (name.isEmpty()) name = Objects.toString(target.get("name"), "Cơ sở Anta");
            if (address.isEmpty()) address = Objects.toString(target.get("address"), "");
        }
        if (name.isEmpty() || address.isEmpty()) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Vui lòng nhập đầy đủ tên cơ sở và địa chỉ");
        }

        double lat = AntaStore.number(req.get("lat"), 10.7721);
        double lng = AntaStore.number(req.get("lng"), 106.6951);
        int openHour = (int) AntaStore.longVal(req.get("openingHour"), 6);
        int closeHour = (int) AntaStore.longVal(req.get("closingHour"), 22);
        if (openHour < 0 || openHour > 23 || closeHour <= openHour || closeHour > 24) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Giờ mở cửa và đóng cửa không hợp lệ");
        }

        String description = Objects.toString(req.get("description"), "").trim();
        List<String> rules = new ArrayList<>();
        if (req.get("rules") instanceof List<?> rawRules) {
            for (Object r : rawRules) {
                String txt = Objects.toString(r, "").trim();
                if (!txt.isEmpty()) rules.add(txt);
            }
        }
        if (rules.isEmpty() && "NEW_BRANCH".equals(type)) {
            rules.add("Vui lòng có mặt trước giờ chơi 10 phút để nhận sân");
            rules.add("Mang giày thể thao phù hợp mặt sân");
        }

        List<String> images = new ArrayList<>();
        if (req.get("images") instanceof List<?> rawImages) {
            for (Object img : rawImages) {
                String u = Objects.toString(img, "").trim();
                if (u.startsWith("https://") || u.startsWith("http://")) images.add(u);
            }
        }

        List<AntaStore.SubmissionYardInput> yards = new ArrayList<>();
        if (req.get("yards") instanceof List<?> rawYards) {
            for (Object yObj : rawYards) {
                if (yObj instanceof Map<?, ?> ym) {
                    String yName = Objects.toString(ym.get("name"), "").trim();
                    String sportId = Objects.toString(ym.get("sportId"), "sp-pickleball").trim();
                    long price = AntaStore.longVal(ym.get("hourlyPrice"), 0L);
                    if (!yName.isEmpty() && price >= 10000L) {
                        yards.add(new AntaStore.SubmissionYardInput(yName, sportId, price));
                    }
                }
            }
        }
        if (yards.isEmpty()) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", "Cần ít nhất 1 sân con với tên sân và giá theo giờ tối thiểu 10.000 đ");
        }

        String subId = "sub-" + UUID.randomUUID().toString().substring(0, 8);
        AntaStore.BranchSubmissionRecord created = store.saveBranchSubmission(new AntaStore.BranchSubmissionRecord(
                subId, type, targetBranchId, user.id(), name, address, lat, lng,
                openHour, closeHour, description, rules, images, yards,
                "PENDING", null, null, Instant.now(), null
        ));
        store.recordAudit(user.id(), "branch_submission.create", "branch_submission", subId,
                Map.of("type", type, "name", name, "yardCount", yards.size()));
        return ResponseEntity.ok(Map.of("data", toSubmissionMap(created)));
    }

    @GetMapping("/owner/branches/{branchId}/courts")
    @SuppressWarnings("unchecked")
    public ResponseEntity<Map<String, Object>> ownerBranchCourts(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String branchId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        if (!canManageBranch(user, branchId)) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Bạn không có quyền quản lý cơ sở này");
        Map<String, Object> branch = store.findBranch(branchId);
        if (branch == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy cơ sở");

        List<Map<String, Object>> courts = new ArrayList<>();
        if (branch.get("yards") instanceof List<?> rawYards) {
            for (Object yObj : rawYards) {
                if (yObj instanceof Map<?, ?> y) {
                    String sid = Objects.toString(y.get("sport_id"), "");
                    courts.add(Map.of(
                            "id", Objects.toString(y.get("id"), ""),
                            "name", Objects.toString(y.get("name"), "Sân"),
                            "sport_id", sid,
                            "sport_name", store.sportName(sid),
                            "hourly_price", AntaStore.longVal(y.get("hourly_price"), 150000L)
                    ));
                }
            }
        }
        List<Map<String, Object>> pendingAdditions = store.listSubmissionsByOwner(user.id()).stream()
                .filter(s -> "ADD_YARDS".equals(s.submissionType()) && branchId.equals(s.targetBranchId()))
                .map(this::toSubmissionMap)
                .toList();
        return ResponseEntity.ok(Map.of("data", Map.of(
                "branch", Map.of("id", Objects.toString(branch.get("id"), branchId), "name", Objects.toString(branch.get("name"), ""), "address", Objects.toString(branch.get("address"), "")),
                "courts", courts,
                "submissions", pendingAdditions
        )));
    }

    private Map<String, Object> toSubmissionMap(AntaStore.BranchSubmissionRecord s) {
        AntaStore.UserRecord owner = store.findUserById(s.ownerUserId());
        Map<String, Object> targetBranch = s.targetBranchId() != null ? store.findBranch(s.targetBranchId()) : null;
        List<Map<String, Object>> yardItems = s.yards().stream().map(y -> Map.<String, Object>of(
                "name", y.name(),
                "sport_id", y.sportId(),
                "sport_name", store.sportName(y.sportId()),
                "hourly_price", y.hourlyPrice()
        )).toList();

        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", s.id());
        m.put("submission_type", s.submissionType());
        m.put("target_branch_id", s.targetBranchId());
        m.put("target_branch_name", targetBranch != null ? Objects.toString(targetBranch.get("name"), s.name()) : null);
        m.put("owner_user_id", s.ownerUserId());
        m.put("owner_name", owner != null ? owner.displayName() : "Chủ sân");
        m.put("owner_identifier", owner != null ? owner.identifier() : s.ownerUserId());
        m.put("name", s.name());
        m.put("address", s.address());
        m.put("lat", s.lat());
        m.put("lng", s.lng());
        m.put("opening_hour", s.openingHour());
        m.put("closing_hour", s.closingHour());
        m.put("description", s.description());
        m.put("rules", s.rules());
        m.put("images", s.images());
        m.put("yards", yardItems);
        m.put("status", s.status());
        m.put("review_note", s.reviewNote());
        m.put("reviewed_by", s.reviewedBy());
        m.put("created_at", s.createdAt().toString());
        m.put("reviewed_at", s.reviewedAt() != null ? s.reviewedAt().toString() : null);
        return m;
    }

    @GetMapping("/owner/branches")
    public ResponseEntity<Map<String, Object>> ownerBranches(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        List<Map<String, Object>> result = resolveOwnedBranches(user).stream()
                .map(b -> Map.<String, Object>of("id", Objects.toString(b.get("id"), ""), "name", Objects.toString(b.get("name"), "")))
                .toList();
        return ResponseEntity.ok(Map.of("data", result));
    }

    @GetMapping("/owner/bookings/stats")
    public ResponseEntity<Map<String, Object>> ownerBookingStats(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam String branchId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        if (!canManageBranch(user, branchId)) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Bạn không có quyền quản lý cơ sở này");

        LocalDate today = LocalDate.now(ZoneId.of("Asia/Ho_Chi_Minh"));
        Instant now = Instant.now();
        Instant weekAgo = now.minus(7, ChronoUnit.DAYS);
        List<AntaStore.BookingRecord> list = store.listBookingsByBranch(branchId);
        long pendingConfirm = list.stream().filter(b -> "PENDING_OWNER_CONFIRMATION".equals(b.status())).count();
        long todayCount = list.stream().filter(b -> b.startsAt().atZone(ZoneId.of("Asia/Ho_Chi_Minh")).toLocalDate().equals(today)).count();
        long upcoming = list.stream().filter(b -> b.startsAt().isAfter(now) && !"CANCELLED".equals(b.status())).count();
        long cancelledWeek = list.stream().filter(b -> "CANCELLED".equals(b.status()) && b.createdAt().isAfter(weekAgo)).count();

        return ResponseEntity.ok(Map.of("data", Map.of(
                "pendingConfirmation", pendingConfirm,
                "today", todayCount,
                "upcoming", upcoming,
                "cancelledThisWeek", cancelledWeek
        )));
    }

    @GetMapping("/owner/courts/schedule")
    @SuppressWarnings("unchecked")
    public ResponseEntity<Map<String, Object>> ownerSchedule(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam String branchId,
            @RequestParam String date,
            @RequestParam(required = false) String sportId,
            @RequestParam(required = false) String courtId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        if (!canManageBranch(user, branchId)) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Bạn không có quyền quản lý cơ sở này");
        Map<String, Object> branch = store.findBranch(branchId);
        if (branch == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy cơ sở");

        String tz = Objects.toString(branch.get("timezone"), "Asia/Ho_Chi_Minh");
        int openHour = (int) AntaStore.longVal(branch.get("opening_hour"), 6);
        int closeHour = (int) AntaStore.longVal(branch.get("closing_hour"), 22);
        if (closeHour <= openHour) closeHour = 24;

        List<Map<String, Object>> rawYards = (branch.get("yards") instanceof List<?> list) ? (List<Map<String, Object>>) list : List.of();
        List<Map<String, Object>> courts = rawYards.stream()
                .filter(y -> sportId == null || sportId.isBlank() || sportId.equals(Objects.toString(y.get("sport_id"), "")))
                .filter(y -> courtId == null || courtId.isBlank() || courtId.equals(Objects.toString(y.get("id"), "")))
                .map(y -> Map.<String, Object>of(
                        "court_id", Objects.toString(y.get("id"), ""),
                        "name", Objects.toString(y.get("name"), "Sân 1"),
                        "sport_id", Objects.toString(y.get("sport_id"), "sp-multi"),
                        "sport_name", store.sportName(Objects.toString(y.get("sport_id"), ""))
                )).toList();

        LocalDate targetDate = LocalDate.parse(date);
        List<Map<String, Object>> bookings = store.listBookingsByBranch(branchId).stream()
                .filter(b -> !"CANCELLED".equals(b.status()) && !"EXPIRED".equals(b.status()))
                .filter(b -> b.startsAt().atZone(ZoneId.of(tz)).toLocalDate().equals(targetDate))
                .map(b -> {
                    AntaStore.UserRecord customer = store.findUserById(b.userId());
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("id", b.id());
                    m.put("yard_id", b.yardId());
                    m.put("starts_at", b.startsAt().toString());
                    m.put("ends_at", b.endsAt().toString());
                    m.put("status", b.status());
                    m.put("customer_name", customer != null ? customer.displayName() : "Khách Anta");
                    m.put("customer_contact", customer != null ? customer.identifier() : b.userId());
                    return m;
                }).toList();

        List<Map<String, Object>> blocks = store.listBlocksByBranch(branchId).stream()
                .filter(blk -> blk.startsAt().atZone(ZoneId.of(tz)).toLocalDate().equals(targetDate))
                .map(AntaStore.BlockRecord::toMap)
                .toList();

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("branch", Map.of(
                "id", branchId,
                "name", Objects.toString(branch.get("name"), ""),
                "openingHour", openHour,
                "closingHour", closeHour,
                "timezone", tz
        ));
        data.put("courts", courts);
        data.put("bookings", bookings);
        data.put("blocks", blocks);
        return ResponseEntity.ok(Map.of("data", data));
    }

    @PostMapping("/owner/courts/{courtId}/blocks")
    public ResponseEntity<Map<String, Object>> createBlock(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String courtId,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        Map<String, Object> branch = store.findBranchByYard(courtId);
        if (branch == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy sân");
        String branchId = Objects.toString(branch.get("id"), "");
        if (!canManageBranch(user, branchId)) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Bạn không có quyền quản lý cơ sở này");

        Instant startsAt = Instant.parse(Objects.toString(req.get("startsAt")));
        Instant endsAt = Instant.parse(Objects.toString(req.get("endsAt")));
        String reason = Objects.toString(req.get("reason"), "Bảo trì sân");
        String id = "blk-" + UUID.randomUUID().toString().substring(0, 8);
        AntaStore.BlockRecord block = new AntaStore.BlockRecord(id, branchId, courtId, startsAt, endsAt, reason);
        store.saveBlock(block);
        return ResponseEntity.ok(Map.of("data", block.toMap()));
    }

    @DeleteMapping("/owner/blocks/{id}")
    public ResponseEntity<Map<String, Object>> deleteBlock(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BlockRecord blk = store.findBlock(id);
        if (blk == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy khung giờ khóa");
        if (!canManageBranch(user, blk.branchId())) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Không có quyền");
        store.deleteBlock(id);
        return ResponseEntity.ok(Map.of("data", Map.of("released", true)));
    }

    @GetMapping("/owner/bookings")
    public ResponseEntity<Map<String, Object>> ownerBookings(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestParam String branchId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String source
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        if (!canManageBranch(user, branchId)) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Không có quyền");
        String normQ = (q != null && !q.isBlank()) ? AntaStore.normalizeSearch(q) : null;

        List<Map<String, Object>> all = store.listBookingsByBranch(branchId).stream()
                .filter(b -> status == null || status.isBlank() || status.equalsIgnoreCase(b.status()))
                .filter(b -> source == null || source.isBlank() || source.equalsIgnoreCase(b.source()))
                .filter(b -> {
                    if (normQ == null) return true;
                    AntaStore.UserRecord customer = store.findUserById(b.userId());
                    return b.id().toLowerCase(Locale.ROOT).contains(normQ)
                            || (customer != null && (AntaStore.normalizeSearch(customer.displayName()).contains(normQ)
                            || AntaStore.normalizeSearch(customer.identifier()).contains(normQ)));
                })
                .map(b -> {
                    AntaStore.UserRecord customer = store.findUserById(b.userId());
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("id", b.id());
                    m.put("customer_name", customer != null ? customer.displayName() : "Khách Anta");
                    m.put("customer_contact", customer != null ? customer.identifier() : b.userId());
                    m.put("yard_name", b.yardName());
                    m.put("starts_at", b.startsAt().toString());
                    m.put("ends_at", b.endsAt().toString());
                    m.put("amount", b.amount());
                    m.put("source", b.source());
                    m.put("status", b.status());
                    return m;
                }).toList();

        int safePage = Math.max(1, page);
        int from = Math.min(all.size(), (safePage - 1) * pageSize);
        int to = Math.min(all.size(), from + pageSize);
        return ResponseEntity.ok(Map.of("data", Map.of(
                "items", all.subList(from, to),
                "total", all.size(),
                "page", safePage,
                "pageSize", pageSize
        )));
    }

    @GetMapping("/owner/bookings/{id}")
    public ResponseEntity<Map<String, Object>> ownerBookingDetail(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BookingRecord b = store.findBooking(id);
        if (b == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn");
        if (!canManageBranch(user, b.branchId())) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Không có quyền");

        AntaStore.UserRecord customer = store.findUserById(b.userId());
        long hours = Math.max(1, Duration.between(b.startsAt(), b.endsAt()).toHours());
        boolean paid = "CONFIRMED".equals(b.status()) || "PENDING_OWNER_CONFIRMATION".equals(b.status());

        Map<String, Object> detail = new LinkedHashMap<>();
        detail.put("id", b.id());
        detail.put("created_at", b.createdAt().toString());
        detail.put("source", b.source());
        detail.put("status", b.status());
        detail.put("starts_at", b.startsAt().toString());
        detail.put("ends_at", b.endsAt().toString());
        detail.put("hours", hours);
        detail.put("hourly_price", b.hourlyPrice());
        detail.put("yard_name", b.yardName());
        detail.put("sport_name", b.sportName());
        detail.put("customer_name", customer != null ? customer.displayName() : "Khách Anta");
        detail.put("customer_contact", customer != null ? customer.identifier() : b.userId());
        detail.put("courtAmount", b.amount());
        detail.put("services", List.of());
        detail.put("amount", b.amount());
        detail.put("paidAmount", paid ? b.amount() : 0L);
        detail.put("outstanding", paid ? 0L : b.amount());
        detail.put("canConfirm", "PENDING_OWNER_CONFIRMATION".equals(b.status()));
        detail.put("confirm_deadline_at", b.confirmDeadlineAt() != null ? b.confirmDeadlineAt().toString() : Instant.now().plus(2, ChronoUnit.HOURS).toString());
        detail.put("statusHistory", b.statusHistory().stream().map(AntaStore.BookingStatusEvent::toMap).toList());
        detail.put("refund", null);
        return ResponseEntity.ok(Map.of("data", detail));
    }

    @PostMapping("/owner/bookings/{id}/confirm")
    public ResponseEntity<Map<String, Object>> ownerConfirmBooking(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BookingRecord b = store.findBooking(id);
        if (b == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn");
        if (!canManageBranch(user, b.branchId())) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Không có quyền");
        store.updateBookingStatus(id, "CONFIRMED", "Chủ sân xác nhận");
        store.recordAudit(user.id(), "booking.confirm", "booking", id, Map.of());
        return ResponseEntity.ok(Map.of("data", Map.of("status", "CONFIRMED")));
    }

    @PostMapping("/owner/bookings/{id}/reject")
    public ResponseEntity<Map<String, Object>> ownerRejectBooking(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BookingRecord b = store.findBooking(id);
        if (b == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn");
        if (!canManageBranch(user, b.branchId())) return AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Không có quyền");
        String reason = req != null ? Objects.toString(req.get("reason"), "Chủ sân từ chối") : "Chủ sân từ chối";
        store.updateBookingStatus(id, "CANCELLED", reason);
        store.recordAudit(user.id(), "booking.reject", "booking", id, Map.of("reason", reason));
        return ResponseEntity.ok(Map.of("data", Map.of("status", "CANCELLED")));
    }

    private AntaStore.UserRecord requireAdmin(String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        return (user != null && store.hasRole(user.id(), "admin")) ? user : null;
    }

    private ResponseEntity<Map<String, Object>> adminDenied(String auth) {
        return store.resolveUser(auth) == null
                ? AntaStore.unauthorized()
                : AntaStore.error(HttpStatus.FORBIDDEN, "FORBIDDEN", "Tài khoản này không có quyền quản trị");
    }

    private List<Map<String, Object>> resolveOwnedBranches(AntaStore.UserRecord user) {
        if (store.hasRole(user.id(), "admin")) return store.getBranches();
        Set<String> ids = new LinkedHashSet<>();
        boolean globalOwner = false;
        for (AntaStore.RoleEntry r : store.rolesFor(user.id())) {
            if ("branch_owner".equalsIgnoreCase(r.role()) || "branch_staff".equalsIgnoreCase(r.role())) {
                if (r.branchId() == null) globalOwner = true;
                else ids.add(r.branchId());
            }
        }
        if (globalOwner) return store.getBranches();
        return store.getBranches().stream().filter(b -> ids.contains(Objects.toString(b.get("id"), ""))).toList();
    }

    private boolean canManageBranch(AntaStore.UserRecord user, String branchId) {
        if (store.hasRole(user.id(), "admin")) return true;
        return store.rolesFor(user.id()).stream().anyMatch(r ->
                ("branch_owner".equalsIgnoreCase(r.role()) || "branch_staff".equalsIgnoreCase(r.role()))
                        && (r.branchId() == null || branchId.equals(r.branchId()))
        );
    }
}
