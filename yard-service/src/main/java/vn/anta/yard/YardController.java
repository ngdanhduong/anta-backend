package vn.anta.yard;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.web.bind.annotation.*;

import java.io.InputStream;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class YardController {

    @Value("${server.port:8081}")
    private int port;

    @Value("${spring.application.name:YARD-SERVICE}")
    private String serviceName;

    private List<Map<String, Object>> allSports = new ArrayList<>();
    private List<Map<String, Object>> allBranches = new ArrayList<>();
    private final Map<String, Map<String, Object>> branchIndex = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> mediaStore = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            ClassPathResource res = new ClassPathResource("data/catalog.json");
            if (res.exists()) {
                try (InputStream is = res.getInputStream()) {
                    Map<String, Object> root = mapper.readValue(is, new TypeReference<>() {});
                    if (root.containsKey("sports")) {
                        allSports = (List<Map<String, Object>>) root.get("sports");
                    }
                    if (root.containsKey("branches")) {
                        allBranches = (List<Map<String, Object>>) root.get("branches");
                    }
                }
            }

            for (Map<String, Object> b : allBranches) {
                if (b.containsKey("id")) {
                    branchIndex.put(b.get("id").toString(), b);
                }
                if (b.containsKey("slug")) {
                    branchIndex.put(b.get("slug").toString(), b);
                }
            }
            System.out.println("[YardController] Loaded " + allBranches.size() + " branches and " + allSports.size() + " sports from catalog.json");
        } catch (Exception e) {
            System.err.println("[YardController] Error loading catalog.json: " + e.getMessage());
            e.printStackTrace();
        }
    }

    // Instance info phục vụ kiểm thử Load balancing
    @GetMapping("/instance-info")
    public Map<String, Object> getInstanceInfo() {
        return Map.of(
            "serviceName", serviceName,
            "port", port,
            "instanceId", serviceName + ":" + port,
            "status", "UP",
            "venuesCount", allBranches.size(),
            "sportsCount", allSports.size()
        );
    }

    // Danh sách môn thể thao (Android app: GET /public/sports)
    @GetMapping({"/public/sports", "/sports"})
    public Map<String, Object> getSports() {
        return Map.of("data", allSports);
    }

    // Danh sách cơ sở / cụm sân thể thao (Android app: GET /public/branches)
    @GetMapping({"/public/branches", "/branches"})
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
        String filterSport = (sport != null && !sport.isBlank()) ? sport.trim().toLowerCase() :
                             (sportId != null && !sportId.isBlank()) ? sportId.trim().toLowerCase() : null;
        String queryTerm = (q != null && !q.isBlank()) ? q.trim().toLowerCase() : null;

        double userLat = (lat != null) ? lat : 10.7721;
        double userLng = (lng != null) ? lng : 106.6951;

        List<Map<String, Object>> filtered = allBranches.stream().filter(b -> {
            // Lọc theo sport
            if (filterSport != null) {
                List<Map<String, Object>> sports = (List<Map<String, Object>>) b.get("sports");
                boolean matchSport = false;
                if (sports != null) {
                    for (Map<String, Object> s : sports) {
                        String slug = String.valueOf(s.get("slug")).toLowerCase();
                        String sid = String.valueOf(s.get("id")).toLowerCase();
                        if (slug.equals(filterSport) || sid.equals(filterSport) || filterSport.contains(slug)) {
                            matchSport = true;
                            break;
                        }
                    }
                }
                if (!matchSport) return false;
            }

            // Lọc theo từ khóa tìm kiếm q
            if (queryTerm != null) {
                String name = String.valueOf(b.get("name")).toLowerCase();
                String addr = String.valueOf(b.get("address")).toLowerCase();
                boolean matchQuery = name.contains(queryTerm) || addr.contains(queryTerm);
                if (!matchQuery) {
                    List<Map<String, Object>> sports = (List<Map<String, Object>>) b.get("sports");
                    if (sports != null) {
                        for (Map<String, Object> s : sports) {
                            if (String.valueOf(s.get("name")).toLowerCase().contains(queryTerm)) {
                                matchQuery = true;
                                break;
                            }
                        }
                    }
                }
                if (!matchQuery) return false;
            }

            return true;
        }).map(b -> {
            Map<String, Object> copy = new LinkedHashMap<>(b);
            double bLat = (b.get("lat") instanceof Number) ? ((Number) b.get("lat")).doubleValue() : userLat;
            double bLng = (b.get("lng") instanceof Number) ? ((Number) b.get("lng")).doubleValue() : userLng;
            double dist = haversineDistanceMeters(userLat, userLng, bLat, bLng);
            copy.put("distance_meters", Math.round(dist * 10.0) / 10.0);
            return copy;
        }).collect(Collectors.toList());

        // Sắp xếp
        if ("rating".equalsIgnoreCase(sort)) {
            filtered.sort((a, b) -> Double.compare(
                (b.get("rating") instanceof Number) ? ((Number) b.get("rating")).doubleValue() : 0.0,
                (a.get("rating") instanceof Number) ? ((Number) a.get("rating")).doubleValue() : 0.0
            ));
        } else if ("price".equalsIgnoreCase(sort)) {
            filtered.sort((a, b) -> Long.compare(
                (a.get("min_price") instanceof Number) ? ((Number) a.get("min_price")).longValue() : 0L,
                (b.get("min_price") instanceof Number) ? ((Number) b.get("min_price")).longValue() : 0L
            ));
        } else {
            // distance mặc định
            filtered.sort((a, b) -> Double.compare(
                (a.get("distance_meters") instanceof Number) ? ((Number) a.get("distance_meters")).doubleValue() : 0.0,
                (b.get("distance_meters") instanceof Number) ? ((Number) b.get("distance_meters")).doubleValue() : 0.0
            ));
        }

        int total = filtered.size();
        int fromIndex = Math.max(0, (page - 1) * pageSize);
        int toIndex = Math.min(total, fromIndex + pageSize);
        List<Map<String, Object>> pagedItems = (fromIndex < total) ? filtered.subList(fromIndex, toIndex) : Collections.emptyList();

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("items", pagedItems);
        data.put("page", page);
        data.put("pageSize", pageSize);
        data.put("total", total);
        data.put("handledByPort", port);

        return Map.of("data", data);
    }

    // Chi tiết cơ sở (Android app: GET /public/branches/{id})
    @GetMapping({"/public/branches/{id}", "/branches/{id}"})
    public Map<String, Object> getBranchDetail(@PathVariable String id) {
        Map<String, Object> branch = branchIndex.get(id);
        if (branch == null) {
            // Tìm theo substring hoặc fallback sang cơ sở đầu tiên nếu không tìm thấy
            branch = allBranches.stream()
                .filter(b -> String.valueOf(b.get("id")).equalsIgnoreCase(id) || String.valueOf(b.get("slug")).equalsIgnoreCase(id))
                .findFirst()
                .orElse(allBranches.isEmpty() ? null : allBranches.get(0));
        }

        if (branch == null) {
            return Map.of("error", Map.of("code", "NOT_FOUND", "message", "Branch not found: " + id));
        }

        return Map.of("data", branch);
    }

    // Dịch vụ kèm theo của cơ sở (Android app: GET /public/branches/{id}/services)
    @GetMapping({"/public/branches/{id}/services", "/branches/{id}/services"})
    public Map<String, Object> getBranchServices(@PathVariable String id) {
        Map<String, Object> branch = branchIndex.get(id);
        List<Map<String, Object>> services = null;
        if (branch != null && branch.containsKey("services")) {
            services = (List<Map<String, Object>>) branch.get("services");
        }
        if (services == null || services.isEmpty()) {
            services = List.of(
                Map.of("name", "Nước suối lạnh Lavie 500ml", "price", 10000L),
                Map.of("name", "Nước giải khát Revive chanh muối", "price", 15000L),
                Map.of("name", "Thuê dụng cụ thi đấu tiêu chuẩn", "price", 30000L)
            );
        }
        return Map.of("data", services);
    }

    // Khung giờ trống đặt sân (Android app: GET /public/branches/{venueId}/availability)
    @GetMapping({"/public/branches/{venueId}/availability", "/yards/{venueId}/availability"})
    public Map<String, Object> getAvailability(
            @PathVariable String venueId,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to
    ) {
        Map<String, Object> branch = branchIndex.get(venueId);
        List<Map<String, Object>> yards = (branch != null && branch.containsKey("yards")) ?
                (List<Map<String, Object>>) branch.get("yards") : Collections.emptyList();

        Instant now = Instant.now().truncatedTo(ChronoUnit.HOURS);
        List<Map<String, Object>> slots = new ArrayList<>();

        String yardId = yards.isEmpty() ? "yard-01" : String.valueOf(yards.get(0).get("id"));
        String yardName = yards.isEmpty() ? "Sân thi đấu 1" : String.valueOf(yards.get(0).get("name"));
        long hourlyPrice = yards.isEmpty() ? 150000L :
                (yards.get(0).get("hourly_price") instanceof Number) ? ((Number) yards.get(0).get("hourly_price")).longValue() : 150000L;

        for (int i = 1; i <= 8; i++) {
            Instant start = now.plus(i, ChronoUnit.HOURS);
            Instant end = start.plus(1, ChronoUnit.HOURS);
            boolean available = (i % 3 != 0); // slot 3, 6 bận

            slots.add(Map.of(
                "yard_id", yardId,
                "name", yardName,
                "starts_at", start.toString(),
                "ends_at", end.toString(),
                "amount", hourlyPrice,
                "available", available
            ));
        }

        return Map.of("data", slots);
    }

    // ---- MEDIA ENDPOINTS ----

    // Presign upload ảnh chung (POST /api/v1/media/presign)
    @PostMapping("/media/presign")
    public Map<String, Object> presignGeneralUpload(@RequestBody(required = false) Map<String, Object> req) {
        return createPresignResponse("general", req);
    }

    // Presign upload ảnh sân (POST /api/v1/branches/{branchId}/images/presign)
    @PostMapping("/branches/{branchId}/images/presign")
    public Map<String, Object> presignCourtUpload(
            @PathVariable String branchId,
            @RequestBody(required = false) Map<String, Object> req
    ) {
        return createPresignResponse(branchId, req);
    }

    private Map<String, Object> createPresignResponse(String branchId, Map<String, Object> req) {
        String uploadId = UUID.randomUUID().toString();
        String mimeType = (req != null && req.containsKey("mimeType")) ? req.get("mimeType").toString() : "image/jpeg";

        Map<String, Object> upload = new LinkedHashMap<>();
        upload.put("id", uploadId);
        upload.put("branch_id", branchId);
        upload.put("mime_type", mimeType);
        upload.put("status", "CLEAN");
        upload.put("url", "https://m-files.alobo.vn/branch/sport_pickleball_hoang_minh/main/cover-1753288232890-thumb.jpg");
        mediaStore.put(uploadId, upload);

        Map<String, Object> res = new LinkedHashMap<>();
        res.put("uploadId", uploadId);
        res.put("method", "PUT");
        res.put("url", "https://m-files.alobo.vn/upload/" + uploadId);
        res.put("headers", Map.of("Content-Type", mimeType));
        res.put("expiresIn", 120);
        res.put("status", "PENDING");

        return Map.of("data", res);
    }

    // Thông tin file upload (GET /api/v1/media/{id})
    @GetMapping("/media/{id}")
    public Map<String, Object> getMedia(@PathVariable String id) {
        Map<String, Object> media = mediaStore.get(id);
        if (media == null) {
            media = Map.of(
                "id", id,
                "status", "CLEAN",
                "mime_type", "image/jpeg",
                "url", "https://m-files.alobo.vn/branch/sport_pickleball_hoang_minh/main/cover-1753288232890-thumb.jpg"
            );
        }
        return Map.of("data", media);
    }

    // Hoàn thành upload (POST /api/v1/media/{id}/complete)
    @PostMapping("/media/{id}/complete")
    public Map<String, Object> completeUpload(@PathVariable String id) {
        Map<String, Object> media = mediaStore.get(id);
        if (media != null) {
            media.put("status", "CLEAN");
        }
        return Map.of("data", Map.of("uploadId", id, "status", "CLEAN"));
    }

    // Xóa/ẩn ảnh cơ sở (DELETE /api/v1/branches/{branchId}/images/{uploadId})
    @DeleteMapping("/branches/{branchId}/images/{uploadId}")
    public Map<String, Object> archiveImage(@PathVariable String branchId, @PathVariable String uploadId) {
        mediaStore.remove(uploadId);
        return Map.of("data", Map.of("archived", true));
    }

    // Công thức tính khoảng cách haversine (mét) giữa 2 tọa độ GPS
    private double haversineDistanceMeters(double lat1, double lon1, double lat2, double lon2) {
        final double R = 6371000.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }
}
