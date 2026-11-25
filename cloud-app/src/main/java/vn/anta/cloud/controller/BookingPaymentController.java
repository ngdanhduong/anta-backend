package vn.anta.cloud.controller;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import vn.anta.cloud.store.AntaStore;

import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
public class BookingPaymentController {

    private final AntaStore store;

    public BookingPaymentController(AntaStore store) {
        this.store = store;
    }

    @PostMapping("/booking-holds")
    public ResponseEntity<Map<String, Object>> createHold(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        String yardId = Objects.toString(req.get("yardId"), "");
        Instant startsAt = Instant.parse(Objects.toString(req.get("startsAt")));
        Instant endsAt = Instant.parse(Objects.toString(req.get("endsAt")));

        if (store.isSlotTaken(yardId, startsAt, endsAt, Instant.now())) {
            return AntaStore.error(HttpStatus.CONFLICT, "SLOT_TAKEN", "Khung giờ này đã có người đặt hoặc giữ chỗ");
        }

        Map<String, Object> yard = store.findYard(yardId);
        String branchId = Optional.ofNullable(store.findBranchByYard(yardId))
                .map(b -> Objects.toString(b.get("id"), "branch-default"))
                .orElse("branch-default");
        long hourlyPrice = yard != null ? AntaStore.longVal(yard.get("hourly_price"), 150000L) : 150000L;
        long hours = Math.max(1, Duration.between(startsAt, endsAt).toHours());
        long total = hourlyPrice * hours;

        String holdId = "hold-" + UUID.randomUUID();
        Instant expiresAt = Instant.now().plus(10, ChronoUnit.MINUTES);
        store.saveHold(new AntaStore.HoldRecord(holdId, user.id(), yardId, branchId, startsAt, endsAt, total, expiresAt));

        return ResponseEntity.ok(Map.of("data", Map.of(
                "holdId", holdId,
                "expiresAt", expiresAt.toString(),
                "quote", Map.of("total", total)
        )));
    }

    @PostMapping("/bookings")
    public ResponseEntity<?> createBooking(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        if (req != null && req.containsKey("holdId")) {
            AntaStore.UserRecord user = store.resolveUser(auth);
            if (user == null) return AntaStore.unauthorized();
            String holdId = Objects.toString(req.get("holdId"), "");
            AntaStore.HoldRecord hold = store.consumeHold(holdId);
            if (hold == null) {
                return AntaStore.error(HttpStatus.NOT_FOUND, "HOLD_NOT_FOUND", "Phiên giữ sân không tồn tại hoặc đã hết hạn");
            }
            Map<String, Object> branch = store.findBranch(hold.branchId());
            Map<String, Object> yard = store.findYard(hold.yardId());
            String branchName = branch != null ? Objects.toString(branch.get("name"), "Sân thể thao Anta") : "Sân thể thao Anta";
            String branchAddress = branch != null ? Objects.toString(branch.get("address"), "") : "";
            String branchTimezone = branch != null ? Objects.toString(branch.get("timezone"), "Asia/Ho_Chi_Minh") : "Asia/Ho_Chi_Minh";
            String branchImage = null;
            if (branch != null && branch.get("images") instanceof List<?> imgs && !imgs.isEmpty()) {
                branchImage = Objects.toString(imgs.get(0), null);
            }
            String yardName = yard != null ? Objects.toString(yard.get("name"), "Sân 1") : "Sân 1";
            String sportName = yard != null ? store.sportName(Objects.toString(yard.get("sport_id"), "")) : "Thể thao";
            long hourlyPrice = yard != null ? AntaStore.longVal(yard.get("hourly_price"), 150000L) : 150000L;

            String bookingId = "ANTA-BK-" + UUID.randomUUID().toString().substring(0, 8);
            Instant now = Instant.now();
            Instant payExpires = now.plus(15, ChronoUnit.MINUTES);
            AntaStore.BookingRecord record = new AntaStore.BookingRecord(
                    bookingId, user.id(), hold.branchId(), hold.yardId(),
                    branchName, branchAddress, branchImage, yardName, sportName, branchTimezone,
                    hold.startsAt(), hold.endsAt(), hourlyPrice, hold.total(),
                    "PENDING_PAYMENT", "APP", now, payExpires, null,
                    List.of(new AntaStore.BookingStatusEvent(now, null, "PENDING_PAYMENT", "Tạo đơn từ app Anta"))
            );
            store.saveNewBooking(record);
            return ResponseEntity.ok(Map.of("data", record.toApiMap()));
        }

        String yardId = (req != null && req.containsKey("yardId")) ? Objects.toString(req.get("yardId")) : "yard-01";
        String slot = (req != null && req.containsKey("slot")) ? Objects.toString(req.get("slot")) : "18:00-19:00";
        long amount = (req != null && req.get("amount") instanceof Number n) ? n.longValue() : 120000L;
        return ResponseEntity.ok(Map.of(
                "bookingId", "ANTA-BK-" + System.currentTimeMillis(),
                "yardId", yardId, "slot", slot, "amount", amount, "status", "CONFIRMED"
        ));
    }

    @GetMapping({"/users/me/bookings", "/user/me/bookings"})
    public ResponseEntity<Map<String, Object>> myBookings(@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        List<Map<String, Object>> items = store.listBookingsByUser(user.id()).stream()
                .map(AntaStore.BookingRecord::toApiMap)
                .toList();
        return ResponseEntity.ok(Map.of("data", Map.of("items", items)));
    }

    @GetMapping("/bookings/{id}")
    public ResponseEntity<Map<String, Object>> getBooking(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BookingRecord b = store.findBooking(id);
        if (b == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn đặt sân");
        return ResponseEntity.ok(Map.of("data", b.toApiMap()));
    }

    @PostMapping("/bookings/{id}/cancel")
    public ResponseEntity<Map<String, Object>> cancelBooking(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String id
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.BookingRecord cancelled = store.updateBookingStatus(id, "CANCELLED", "Khách hủy đơn");
        if (cancelled == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn đặt sân");
        return ResponseEntity.ok(Map.of("data", cancelled.toApiMap()));
    }

    @PostMapping("/payment-intents")
    public ResponseEntity<Map<String, Object>> createPaymentIntent(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @RequestBody Map<String, Object> req
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        String bookingId = Objects.toString(req.get("bookingId"), "");
        AntaStore.BookingRecord booking = store.findBooking(bookingId);
        if (booking == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy đơn đặt sân");

        String intentId = "pi-" + UUID.randomUUID();
        store.savePaymentIntent(new AntaStore.PaymentIntentRecord(intentId, bookingId, user.id(), booking.amount(), "CREATED", null, Instant.now()));

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("id", intentId);
        data.put("status", "CREATED");
        data.put("amount", booking.amount());
        data.put("checkoutUrl", null);
        data.put("sandbox", true);
        return ResponseEntity.ok(Map.of("data", data));
    }

    @PostMapping("/dev/payment-intents/{intentId}/pay")
    public ResponseEntity<Map<String, Object>> settleSandboxPayment(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String auth,
            @PathVariable String intentId
    ) {
        AntaStore.UserRecord user = store.resolveUser(auth);
        if (user == null) return AntaStore.unauthorized();
        AntaStore.PaymentIntentRecord intent = store.findPaymentIntent(intentId);
        if (intent == null) return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy giao dịch thanh toán");

        store.savePaymentIntent(new AntaStore.PaymentIntentRecord(
                intent.id(), intent.bookingId(), intent.userId(), intent.amount(), "SUCCEEDED", intent.refundStatus(), Instant.now()
        ));
        store.updateBookingStatus(intent.bookingId(), "CONFIRMED", "Thanh toán sandbox thành công");
        return ResponseEntity.ok(Map.of("data", Map.of("outcome", "SUCCEEDED")));
    }

    @PostMapping("/payments/intents")
    public Map<String, Object> labCreatePaymentIntent(@RequestBody(required = false) Map<String, Object> req) {
        String bookingId = (req != null && req.containsKey("bookingId")) ? Objects.toString(req.get("bookingId")) : "BK-SAMPLE";
        long amount = (req != null && req.get("amount") instanceof Number n) ? n.longValue() : 120000L;
        return Map.of(
                "paymentIntentId", "PI-" + UUID.randomUUID(),
                "bookingId", bookingId, "amount", amount, "currency", "VND",
                "status", "SUCCEEDED", "provider", "Sandbox-AntaPay"
        );
    }
}
