package vn.anta.yard;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class YardController {

    @Value("${server.port:8081}")
    private int port;

    @Value("${spring.application.name:YARD-SERVICE}")
    private String serviceName;

    // Instance info phục vụ kiểm thử Load balancing
    @GetMapping("/instance-info")
    public Map<String, Object> getInstanceInfo() {
        return Map.of(
            "serviceName", serviceName,
            "port", port,
            "instanceId", serviceName + ":" + port,
            "status", "UP"
        );
    }

    // Danh sách môn thể thao (Android app: GET /public/sports)
    @GetMapping({"/public/sports", "/sports"})
    public Map<String, Object> getSports() {
        List<Map<String, Object>> sports = List.of(
            Map.of("id", "sp-badminton", "name", "Cầu lông", "slug", "badminton", "venue_count", 8),
            Map.of("id", "sp-pickleball", "name", "Pickleball", "slug", "pickleball", "venue_count", 6),
            Map.of("id", "sp-football", "name", "Bóng đá mini", "slug", "football", "venue_count", 5),
            Map.of("id", "sp-tennis", "name", "Tennis", "slug", "tennis", "venue_count", 4),
            Map.of("id", "sp-basketball", "name", "Bóng rổ", "slug", "basketball", "venue_count", 3)
        );
        return Map.of("data", sports);
    }

    private Map<String, Object> createVenueItem(
            String id, String name, String address, double lat, double lng,
            double distanceMeters, int openingHour, int closingHour, String image,
            double rating, int reviewCount, long minPrice, List<Map<String, String>> sports
    ) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", id);
        item.put("name", name);
        item.put("address", address);
        item.put("lat", lat);
        item.put("lng", lng);
        item.put("distance_meters", distanceMeters);
        item.put("opening_hour", openingHour);
        item.put("closing_hour", closingHour);
        item.put("images", List.of(image));
        item.put("rating", rating);
        item.put("review_count", reviewCount);
        item.put("min_price", minPrice);
        item.put("sports", sports);
        return item;
    }

    // Danh sách cơ sở / sân thể thao (Android app: GET /public/branches)
    @GetMapping({"/public/branches", "/branches", "/yards"})
    public Map<String, Object> getBranches(
            @RequestParam(required = false) String sport,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "1") int page
    ) {
        List<Map<String, Object>> items = List.of(
            createVenueItem(
                "branch-01", "CLB Thể Thao Anta Sài Gòn",
                "123 Điện Biên Phủ, Phường 15, Bình Thạnh, TP.HCM",
                10.7932, 106.7021, 850.0, 6, 23,
                "https://images.unsplash.com/photo-1544717305-2782549b5136",
                4.9, 86, 120000L,
                List.of(Map.of("slug", "badminton", "name", "Cầu lông"), Map.of("slug", "pickleball", "name", "Pickleball"))
            ),
            createVenueItem(
                "branch-02", "Anta Pickleball & Tennis Complex",
                "456 Nguyễn Thị Thập, Tân Phong, Quận 7, TP.HCM",
                10.7381, 106.7054, 2400.0, 5, 22,
                "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0",
                4.8, 64, 150000L,
                List.of(Map.of("slug", "pickleball", "name", "Pickleball"), Map.of("slug", "tennis", "name", "Tennis"))
            ),
            createVenueItem(
                "branch-03", "Trung Tâm Thể Thao Anta Cầu Giấy",
                "78 Duy Tân, Cầu Giấy, Hà Nội",
                21.0313, 105.7836, 4500.0, 6, 22,
                "https://images.unsplash.com/photo-1574629810360-7efbbe195018",
                4.9, 112, 100000L,
                List.of(Map.of("slug", "football", "name", "Bóng đá mini"), Map.of("slug", "badminton", "name", "Cầu lông"))
            )
        );

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("items", items);
        data.put("page", page);
        data.put("total", items.size());
        data.put("handledByPort", port);

        return Map.of("data", data);
    }

    // Chi tiết cơ sở (Android app: GET /public/branches/{id})
    @GetMapping({"/public/branches/{id}", "/branches/{id}"})
    public Map<String, Object> getBranchDetail(@PathVariable String id) {
        Map<String, Object> branch = new LinkedHashMap<>();
        branch.put("id", id);
        branch.put("name", "CLB Thể Thao Anta Sài Gòn");
        branch.put("address", "123 Điện Biên Phủ, Phường 15, Bình Thạnh, TP.HCM");
        branch.put("lat", 10.7932);
        branch.put("lng", 106.7021);
        branch.put("opening_hour", 6);
        branch.put("closing_hour", 23);
        branch.put("timezone", "Asia/Ho_Chi_Minh");
        branch.put("images", List.of("https://images.unsplash.com/photo-1544717305-2782549b5136"));
        branch.put("rating", 4.9);
        branch.put("review_count", 86);
        branch.put("min_price", 120000L);
        branch.put("rules", List.of(
            "Vui lòng mang giày thể thao đế mềm (non-marking)",
            "Có mặt và check-in trước giờ chơi 10 phút",
            "Giữ gìn vệ sinh chung sân bãi"
        ));
        branch.put("description", "Bảng giá ngày thường: 06:00-17:00: 120.000 ₫; 17:00-22:00: 180.000 ₫.\nBảng giá cuối tuần: 06:00-22:00: 200.000 ₫.");
        branch.put("sports", List.of(
            Map.of("slug", "badminton", "name", "Cầu lông"),
            Map.of("slug", "pickleball", "name", "Pickleball")
        ));
        branch.put("yards", List.of(
            Map.of("id", "yard-01", "sport_id", "sp-badminton", "name", "Sân Cầu Lông VIP 1", "hourly_price", 150000L),
            Map.of("id", "yard-02", "sport_id", "sp-badminton", "name", "Sân Cầu Lông Tiêu Chuẩn 2", "hourly_price", 120000L),
            Map.of("id", "yard-03", "sport_id", "sp-pickleball", "name", "Sân Pickleball Sân 1", "hourly_price", 180000L)
        ));

        return Map.of("data", branch);
    }

    // Dịch vụ kèm theo của cơ sở (Android app: GET /public/branches/{id}/services)
    @GetMapping({"/public/branches/{id}/services", "/branches/{id}/services"})
    public Map<String, Object> getBranchServices(@PathVariable String id) {
        List<Map<String, Object>> services = List.of(
            Map.of("name", "Nước suối lạnh Lavie 500ml", "price", 10000L),
            Map.of("name", "Nước tăng lực Revive chanh muối", "price", 15000L),
            Map.of("name", "Thuê vợt cầu lông Yonex", "price", 30000L),
            Map.of("name", "Quả cầu lông thi đấu Thành Công", "price", 25000L)
        );
        return Map.of("data", services);
    }

    // Khung giờ trống đặt sân (Android app: GET /public/branches/{venueId}/availability)
    @GetMapping({"/public/branches/{venueId}/availability", "/yards/{venueId}/availability"})
    public Map<String, Object> getAvailability(
            @PathVariable String venueId,
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to
    ) {
        Instant now = Instant.now().truncatedTo(ChronoUnit.HOURS);
        List<Map<String, Object>> slots = new ArrayList<>();

        for (int i = 1; i <= 6; i++) {
            Instant start = now.plus(i, ChronoUnit.HOURS);
            Instant end = start.plus(1, ChronoUnit.HOURS);
            boolean available = (i % 3 != 0); // slot 3, 6 bận, còn lại trống

            slots.add(Map.of(
                "yard_id", "yard-01",
                "name", "Sân Cầu Lông VIP 1",
                "starts_at", start.toString(),
                "ends_at", end.toString(),
                "amount", 150000L,
                "available", available
            ));
        }

        return Map.of("data", slots);
    }
}
