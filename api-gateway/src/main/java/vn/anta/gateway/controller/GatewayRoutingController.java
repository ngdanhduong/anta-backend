package vn.anta.gateway.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalancerClient;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClient;

import java.io.InputStream;
import java.net.URI;
import java.util.*;

@RestController
@CrossOrigin(origins = "*")
public class GatewayRoutingController {

    @Value("${server.port:8080}")
    private int port;

    private final LoadBalancerClient loadBalancerClient;
    private final DiscoveryClient discoveryClient;
    private final RestClient restClient;

    public GatewayRoutingController(LoadBalancerClient loadBalancerClient, DiscoveryClient discoveryClient) {
        this.loadBalancerClient = loadBalancerClient;
        this.discoveryClient = discoveryClient;
        this.restClient = RestClient.create();
    }

    @GetMapping({"/", "/api/v1/gateway/info"})
    public Map<String, Object> getGatewayInfo() {
        Map<String, Object> info = new LinkedHashMap<>();
        info.put("gateway", "ANTA-API-GATEWAY");
        info.put("port", port);
        info.put("status", "UP");
        info.put("serviceRegistry", "Netflix Eureka (:8761)");

        Map<String, Object> services = new LinkedHashMap<>();
        for (String serviceId : discoveryClient.getServices()) {
            List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);
            List<String> uris = instances.stream().map(i -> i.getUri().toString()).toList();
            services.put(serviceId, uris);
        }
        info.put("registeredServices", services);

        info.put("routeTable", List.of(
            Map.of("prefix", "/api/v1/auth/**, /api/v1/users/**", "targetService", "AUTH-SERVICE"),
            Map.of("prefix", "/api/v1/yards/**, /api/v1/public/branches/**", "targetService", "YARD-SERVICE"),
            Map.of("prefix", "/api/v1/bookings/**", "targetService", "BOOKING-SERVICE"),
            Map.of("prefix", "/api/v1/payments/**", "targetService", "PAYMENT-SERVICE")
        ));
        return info;
    }

    // Dynamic reverse proxy router cho toàn bộ các endpoint /api/v1/**
    @RequestMapping(value = "/api/v1/**", method = {
        RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
        RequestMethod.DELETE, RequestMethod.PATCH
    })
    public ResponseEntity<?> routeRequest(
            HttpServletRequest request,
            @RequestBody(required = false) byte[] body,
            HttpMethod method
    ) {
        String path = request.getRequestURI();
        String query = request.getQueryString();
        String targetService = determineTargetService(path);

        if (targetService == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(Map.of("error", "NOT_FOUND", "message", "Không tìm thấy tuyến đường tương ứng tại API Gateway: " + path));
        }

        // Cân bằng tải phía Gateway (LoadBalancer chọn instance từ Eureka)
        ServiceInstance instance = loadBalancerClient.choose(targetService);
        if (instance == null) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(Map.of(
                    "error", "SERVICE_UNAVAILABLE",
                    "targetService", targetService,
                    "message", "Hiện không có instance khả dụng nào của dịch vụ " + targetService + " trên Eureka."
                ));
        }

        String targetUrl = instance.getUri().toString() + path + (query != null ? "?" + query : "");

        try {
            // Forward HTTP request
            RestClient.RequestBodySpec spec = restClient.method(method).uri(URI.create(targetUrl));

            // Copy relevant headers
            Enumeration<String> headerNames = request.getHeaderNames();
            while (headerNames.hasMoreElements()) {
                String name = headerNames.nextElement();
                if (!name.equalsIgnoreCase(HttpHeaders.HOST) && !name.equalsIgnoreCase(HttpHeaders.CONTENT_LENGTH)) {
                    spec.header(name, request.getHeader(name));
                }
            }

            if (body != null && body.length > 0) {
                spec.body(body);
                if (request.getContentType() != null) {
                    spec.contentType(MediaType.parseMediaType(request.getContentType()));
                }
            }

            return spec.retrieve().toEntity(byte[].class);
        } catch (HttpStatusCodeException ex) {
            return ResponseEntity.status(ex.getStatusCode())
                .contentType(MediaType.APPLICATION_JSON)
                .body(ex.getResponseBodyAsByteArray());
        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                .body(Map.of(
                    "error", "BAD_GATEWAY",
                    "targetInstance", instance.getUri().toString(),
                    "message", "Lỗi kết nối tới microservice: " + ex.getMessage()
                ));
        }
    }

    private String determineTargetService(String path) {
        if (path.startsWith("/api/v1/auth") || path.startsWith("/api/v1/public/auth") ||
            path.startsWith("/api/v1/users") || path.startsWith("/api/v1/public/config")) {
            return "AUTH-SERVICE";
        }
        if (path.startsWith("/api/v1/yards") || path.startsWith("/api/v1/public/branches") ||
            path.startsWith("/api/v1/public/sports")) {
            return "YARD-SERVICE";
        }
        if (path.startsWith("/api/v1/bookings")) {
            return "BOOKING-SERVICE";
        }
        if (path.startsWith("/api/v1/payments")) {
            return "PAYMENT-SERVICE";
        }
        return null;
    }
}
