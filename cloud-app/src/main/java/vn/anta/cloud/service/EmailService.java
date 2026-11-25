package vn.anta.cloud.service;

import jakarta.mail.internet.MimeMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.util.Properties;

/**
 * Optional SMTP email sender. Activated automatically when SMTP_USER and SMTP_PASS environment variables are set.
 */
@Service
public class EmailService {

    public boolean isConfigured() {
        return nonBlank("SMTP_USER") != null && nonBlank("SMTP_PASS") != null;
    }

    public boolean sendOtpEmail(String toEmail, String code, String purpose) {
        String user = nonBlank("SMTP_USER");
        String pass = nonBlank("SMTP_PASS");
        if (user == null || pass == null || toEmail == null || !toEmail.contains("@")) {
            return false;
        }
        String host = OptionalEnv("SMTP_HOST", "smtp.gmail.com");
        int port = Integer.parseInt(OptionalEnv("SMTP_PORT", "465"));
        String from = OptionalEnv("SMTP_FROM", user);

        try {
            JavaMailSenderImpl sender = new JavaMailSenderImpl();
            sender.setHost(host);
            sender.setPort(port);
            sender.setUsername(user);
            sender.setPassword(pass);

            Properties props = sender.getJavaMailProperties();
            props.put("mail.transport.protocol", "smtp");
            props.put("mail.smtp.auth", "true");
            if (port == 465) {
                props.put("mail.smtp.ssl.enable", "true");
            } else {
                props.put("mail.smtp.starttls.enable", "true");
            }
            props.put("mail.smtp.connectiontimeout", "10000");
            props.put("mail.smtp.timeout", "10000");

            MimeMessage message = sender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, "UTF-8");
            helper.setFrom(from);
            helper.setTo(toEmail);
            String action = "reset-password".equalsIgnoreCase(purpose) ? "đặt lại mật khẩu" : "đăng ký tài khoản";
            helper.setSubject("[Anta Sports] Mã xác thực " + code);
            helper.setText("""
                    Xin chào,

                    Mã xác thực (OTP) để %s tài khoản Anta Sports của bạn là: %s

                    Mã có hiệu lực trong 15 phút. Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.
                    """.formatted(action, code), false);

            sender.send(message);
            return true;
        } catch (Exception ex) {
            System.err.println("[EmailService] Failed to send OTP email to " + toEmail + ": " + ex.getMessage());
            return false;
        }
    }

    private static String nonBlank(String key) {
        String val = System.getenv(key);
        return (val != null && !val.isBlank()) ? val.trim() : null;
    }

    private static String OptionalEnv(String key, String fallback) {
        String val = nonBlank(key);
        return val != null ? val : fallback;
    }
}
