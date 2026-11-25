package vn.anta.cloud.service;

import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Base64;

/**
 * Lightweight Azure Blob Storage helper using pure JDK HTTP + HMAC-SHA256 SAS signing (sv=2022-11-02).
 * Activated when AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables are configured.
 */
@Service
public class AzureBlobStorageService {

    private static final String API_VERSION = "2022-11-02";
    private static final DateTimeFormatter ISO_UTC = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'").withZone(ZoneOffset.UTC);

    private final HttpClient httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    public boolean isConfigured() {
        return accountName() != null && accountKey() != null;
    }

    public String accountName() {
        return nonBlank("AZURE_STORAGE_ACCOUNT");
    }

    public String containerName() {
        String c = nonBlank("AZURE_STORAGE_CONTAINER");
        return c != null ? c : "media";
    }

    private String accountKey() {
        return nonBlank("AZURE_STORAGE_KEY");
    }

    public String publicUrl(String blobPath) {
        String acct = accountName();
        if (acct == null) return null;
        return "https://" + acct + ".blob.core.windows.net/" + containerName() + "/" + normalizePath(blobPath);
    }

    public String createUploadSasUrl(String blobPath, Duration ttl) {
        return createBlobSasUrl(blobPath, "cw", ttl);
    }

    public String createBlobSasUrl(String blobPath, String permissions, Duration ttl) {
        String acct = accountName();
        String key = accountKey();
        if (acct == null || key == null) return null;

        String container = containerName();
        String cleanPath = normalizePath(blobPath);
        Instant now = Instant.now();
        String start = ISO_UTC.format(now.minusSeconds(300));
        String expiry = ISO_UTC.format(now.plus(ttl));

        String canonicalizedResource = "/blob/" + acct + "/" + container + "/" + cleanPath;
        String stringToSign = String.join("\n",
                permissions,
                start,
                expiry,
                canonicalizedResource,
                "",
                "",
                "https",
                API_VERSION,
                "b",
                "",
                "",
                "",
                "",
                "",
                "",
                ""
        );
        String signature = signHmacSha256(key, stringToSign);

        String query = "sv=" + encode(API_VERSION)
                + "&st=" + encode(start)
                + "&se=" + encode(expiry)
                + "&sr=b"
                + "&sp=" + encode(permissions)
                + "&spr=https"
                + "&sig=" + encode(signature);
        return publicUrl(cleanPath) + "?" + query;
    }

    public boolean blobExists(String blobPath) {
        String url = createBlobSasUrl(blobPath, "r", Duration.ofMinutes(5));
        if (url == null) return false;
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                    .timeout(Duration.ofSeconds(10))
                    .method("HEAD", HttpRequest.BodyPublishers.noBody())
                    .build();
            HttpResponse<Void> resp = httpClient.send(req, HttpResponse.BodyHandlers.discarding());
            return resp.statusCode() == 200;
        } catch (Exception ex) {
            return false;
        }
    }

    public boolean deleteBlob(String blobPath) {
        String url = createBlobSasUrl(blobPath, "d", Duration.ofMinutes(5));
        if (url == null) return false;
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                    .timeout(Duration.ofSeconds(10))
                    .DELETE()
                    .build();
            HttpResponse<Void> resp = httpClient.send(req, HttpResponse.BodyHandlers.discarding());
            return resp.statusCode() == 202 || resp.statusCode() == 200 || resp.statusCode() == 404;
        } catch (Exception ex) {
            return false;
        }
    }

    private static String signHmacSha256(String base64Key, String data) {
        try {
            byte[] decodedKey = Base64.getDecoder().decode(base64Key);
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(decodedKey, "HmacSHA256"));
            return Base64.getEncoder().encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception ex) {
            throw new IllegalStateException("Unable to sign Azure Blob SAS", ex);
        }
    }

    private static String normalizePath(String path) {
        return path == null ? "" : path.replaceAll("^/+", "");
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    private static String nonBlank(String key) {
        String val = System.getenv(key);
        return (val != null && !val.isBlank()) ? val.trim() : null;
    }
}
