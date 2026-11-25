package vn.anta.cloud.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import vn.anta.cloud.service.AzureBlobStorageService;
import vn.anta.cloud.store.AntaStore;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
public class CatalogController {

    private final AntaStore store;
    private final AzureBlobStorageService blobService;

    public CatalogController(AntaStore store, AzureBlobStorageService blobService) {
        this.store = store;
        this.blobService = blobService;
    }

    @GetMapping({"/public/sports", "/sports"})
    public Map<String, Object> getSports() {
        return Map.of("data", store.getSports());
    }

    @GetMapping({"/public/branches", "/branches", "/yards"})
    public Map<String, Object> getBranches(
            @RequestParam(required = false) String sport,
            @RequestParam(required = false) String sportId,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String sort,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize
    ) {
        String filterSport = firstNonBlank(sport, sportId);
        String normalizedFilter = filterSport != null ? filterSport.trim().toLowerCase(Locale.ROOT) : null;
        String normalizedQuery = (q != null && !q.isBlank()) ? AntaStore.normalizeSearch(q) : null;

        boolean hasCoords = lat != null && lng != null;
        double userLat = hasCoords ? lat : 10.7721;
        double userLng = hasCoords ? lng : 106.6951;

        List<Map<String, Object>> filtered = store.getBranches().stream()
                .filter(b -> matchesSport(b, normalizedFilter))
                .filter(b -> matchesQuery(b, normalizedQuery))
                .map(b -> store.branchWithDistance(b, userLat, userLng))
                .toList();

        List<Map<String, Object>> sorted = new ArrayList<>(filtered);
        if ("rating".equalsIgnoreCase(sort)) {
            sorted.sort((a, b) -> Double.compare(AntaStore.number(b.get("rating"), 0.0), AntaStore.number(a.get("rating"), 0.0)));
        } else if ("price".equalsIgnoreCase(sort)) {
            sorted.sort((a, b) -> Long.compare(AntaStore.longVal(a.get("min_price"), 0L), AntaStore.longVal(b.get("min_price"), 0L)));
        } else if (!hasCoords && !"distance".equalsIgnoreCase(sort)) {
            sorted.sort(Comparator.comparing(a -> Objects.toString(a.get("name"), "")));
        } else {
            sorted.sort((a, b) -> Double.compare(AntaStore.number(a.get("distance_meters"), 0.0), AntaStore.number(b.get("distance_meters"), 0.0)));
        }

        int safePage = Math.max(1, page);
        int safeSize = Math.max(1, Math.min(pageSize, 100));
        int total = sorted.size();
        int fromIndex = Math.min(total, (safePage - 1) * safeSize);
        int toIndex = Math.min(total, fromIndex + safeSize);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("items", sorted.subList(fromIndex, toIndex));
        data.put("page", safePage);
        data.put("pageSize", safeSize);
        data.put("total", total);
        return Map.of("data", data);
    }

    @GetMapping({"/public/branches/{id}", "/branches/{id}"})
    public ResponseEntity<Map<String, Object>> getBranchDetail(@PathVariable String id) {
        Map<String, Object> branch = store.findBranch(id);
        if (branch == null) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy cơ sở: " + id);
        }
        return ResponseEntity.ok(Map.of("data", store.enrichBranchImages(branch)));
    }

    @GetMapping({"/public/branches/{id}/services", "/branches/{id}/services"})
    @SuppressWarnings("unchecked")
    public Map<String, Object> getBranchServices(@PathVariable String id) {
        Map<String, Object> branch = store.findBranch(id);
        List<Map<String, Object>> services = (branch != null && branch.get("services") instanceof List<?> list)
                ? (List<Map<String, Object>>) list
                : List.of();
        if (services.isEmpty()) {
            services = List.of(
                    Map.of("name", "Nước suối lạnh Lavie 500ml", "price", 10000L),
                    Map.of("name", "Nước giải khát Revive", "price", 15000L),
                    Map.of("name", "Thuê vợt / bóng tiêu chuẩn", "price", 30000L)
            );
        }
        return Map.of("data", services);
    }

    @GetMapping({"/public/branches/{venueId}/availability", "/yards/{venueId}/availability"})
    @SuppressWarnings("unchecked")
    public Map<String, Object> getAvailability(
            @PathVariable String venueId,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to
    ) {
        Map<String, Object> branch = store.findBranch(venueId);
        if (branch == null) {
            return Map.of("data", List.of());
        }

        ZoneId zone = ZoneId.of(Objects.toString(branch.get("timezone"), "Asia/Ho_Chi_Minh"));
        int openHour = (int) AntaStore.longVal(branch.get("opening_hour"), 6);
        int closeHour = (int) AntaStore.longVal(branch.get("closing_hour"), 22);
        if (closeHour <= openHour) {
            closeHour = 24;
        }

        Instant now = Instant.now();
        LocalDate targetDate = LocalDate.now(zone);
        if (from != null && !from.isBlank()) {
            try {
                targetDate = Instant.parse(from).atZone(zone).toLocalDate();
            } catch (Exception ignored) {
            }
        }

        List<Map<String, Object>> yards = (branch.get("yards") instanceof List<?> rawYards)
                ? (List<Map<String, Object>>) rawYards
                : List.of();
        if (yards.isEmpty()) {
            yards = List.of(Map.of("id", venueId + "-yard-1", "name", "Sân tiêu chuẩn 1", "hourly_price", 150000L));
        }

        List<Map<String, Object>> slots = new ArrayList<>();
        for (Map<String, Object> yard : yards) {
            String yardId = Objects.toString(yard.get("id"), venueId + "-yard-1");
            String yardName = Objects.toString(yard.get("name"), "Sân 1");
            long hourlyPrice = AntaStore.longVal(yard.get("hourly_price"), 150000L);

            for (int hour = openHour; hour < closeHour; hour++) {
                Instant start = targetDate.atTime(hour % 24, 0).atZone(zone).toInstant();
                Instant end = start.plus(1, ChronoUnit.HOURS);
                if (!end.isAfter(now)) {
                    continue;
                }
                boolean taken = isSlotTaken(yardId, start, end, now);
                slots.add(Map.of(
                        "yard_id", yardId,
                        "name", yardName,
                        "starts_at", start.toString(),
                        "ends_at", end.toString(),
                        "amount", hourlyPrice,
                        "available", !taken
                ));
            }
        }
        return Map.of("data", slots);
    }

    private boolean isSlotTaken(String yardId, Instant start, Instant end, Instant now) {
        return store.isSlotTaken(yardId, start, end, now);
    }

    @PostMapping("/media/presign")
    public Map<String, Object> presignGeneralUpload(@RequestBody(required = false) Map<String, Object> req) {
        return createPresignResponse("general", req);
    }

    @PostMapping("/branches/{branchId}/images/presign")
    public Map<String, Object> presignCourtUpload(@PathVariable String branchId, @RequestBody(required = false) Map<String, Object> req) {
        return createPresignResponse(branchId, req);
    }

    private Map<String, Object> createPresignResponse(String branchId, Map<String, Object> req) {
        String uploadId = UUID.randomUUID().toString();
        String mimeType = (req != null && req.get("mimeType") != null) ? req.get("mimeType").toString().trim() : "image/jpeg";
        String ext = switch (mimeType.toLowerCase(Locale.ROOT)) {
            case "image/png" -> ".png";
            case "image/webp" -> ".webp";
            default -> ".jpg";
        };
        String safeBranch = branchId.replaceAll("[^a-zA-Z0-9_-]", "_");
        String blobPath = "uploads/" + safeBranch + "/" + uploadId + ext;

        String uploadUrl;
        String publicUrl;
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", mimeType);

        if (blobService.isConfigured()) {
            uploadUrl = blobService.createUploadSasUrl(blobPath, Duration.ofMinutes(15));
            publicUrl = blobService.publicUrl(blobPath);
            headers.put("x-ms-blob-type", "BlockBlob");
            store.saveMediaAsset(uploadId, branchId, blobPath, mimeType, "PENDING", publicUrl);
        } else {
            publicUrl = "https://antamedia2026.blob.core.windows.net/media/catalog/branch/sport_pickleball_hoang_minh/main/cover-1753288232890-thumb.jpg";
            uploadUrl = publicUrl;
            store.saveMediaAsset(uploadId, branchId, blobPath, mimeType, "PENDING", publicUrl);
        }

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("uploadId", uploadId);
        data.put("method", "PUT");
        data.put("url", uploadUrl);
        data.put("publicUrl", publicUrl);
        data.put("headers", headers);
        data.put("expiresIn", 900);
        data.put("status", "PENDING");
        return Map.of("data", data);
    }

    @GetMapping("/media/{id}")
    public ResponseEntity<Map<String, Object>> getMedia(@PathVariable String id) {
        AntaStore.MediaAssetRecord media = store.findMediaAsset(id);
        if (media == null) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy tệp ảnh");
        }
        return ResponseEntity.ok(Map.of("data", media.toApiMap()));
    }

    @PostMapping("/media/{id}/complete")
    public ResponseEntity<Map<String, Object>> completeUpload(@PathVariable String id) {
        AntaStore.MediaAssetRecord media = store.findMediaAsset(id);
        if (media == null) {
            return AntaStore.error(HttpStatus.NOT_FOUND, "NOT_FOUND", "Không tìm thấy phiên tải ảnh");
        }
        if (blobService.isConfigured() && !blobService.blobExists(media.blobPath())) {
            return AntaStore.error(HttpStatus.BAD_REQUEST, "UPLOAD_NOT_FOUND", "Ảnh chưa được tải lên Azure Blob Storage");
        }
        store.markMediaClean(id);
        return ResponseEntity.ok(Map.of("data", Map.of("uploadId", id, "status", "CLEAN", "url", media.url())));
    }

    @DeleteMapping("/branches/{branchId}/images/{uploadId}")
    public ResponseEntity<Map<String, Object>> archiveImage(@PathVariable String branchId, @PathVariable String uploadId) {
        AntaStore.MediaAssetRecord media = store.findMediaAsset(uploadId);
        if (media != null && blobService.isConfigured()) {
            blobService.deleteBlob(media.blobPath());
        }
        store.deleteMediaAsset(uploadId);
        return ResponseEntity.ok(Map.of("data", Map.of("archived", true)));
    }

    @SuppressWarnings("unchecked")
    private static boolean matchesSport(Map<String, Object> branch, String filter) {
        if (filter == null) return true;
        if (!(branch.get("sports") instanceof List<?> sports)) return false;
        for (Object item : sports) {
            if (item instanceof Map<?, ?> s) {
                String slug = Objects.toString(s.get("slug"), "").toLowerCase(Locale.ROOT);
                String sid = Objects.toString(s.get("id"), "").toLowerCase(Locale.ROOT);
                if (slug.equals(filter) || sid.equals(filter) || filter.contains(slug)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static boolean matchesQuery(Map<String, Object> branch, String query) {
        if (query == null || query.isEmpty()) return true;
        String name = AntaStore.normalizeSearch(Objects.toString(branch.get("name"), ""));
        String addr = AntaStore.normalizeSearch(Objects.toString(branch.get("address"), ""));
        if (name.contains(query) || addr.contains(query)) return true;
        if (branch.get("sports") instanceof List<?> sports) {
            for (Object item : sports) {
                if (item instanceof Map<?, ?> s && AntaStore.normalizeSearch(Objects.toString(s.get("name"), "")).contains(query)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static String firstNonBlank(String a, String b) {
        if (a != null && !a.isBlank()) return a;
        return (b != null && !b.isBlank()) ? b : null;
    }
}
