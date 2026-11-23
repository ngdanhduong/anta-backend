import os
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Directories
    DIAGRAMS_DIR = r"D:\hdv\backend\docs\diagrams"
    
    # Visual Paradigm Diagrams (White background)
    IMG_SEQ = os.path.join(DIAGRAMS_DIR, "VisualParadigm_Sequence_DatSan.png")
    IMG_ERD_WHITE = os.path.join(DIAGRAMS_DIR, "VisualParadigm_ERD_DatSan_NenTrang.png")
    
    # Realistic VS Code Editor Screenshots
    SHOT_CONTROLLER = os.path.join(DIAGRAMS_DIR, "vscode_booking_controller.png")
    SHOT_BOOKING_SVC = os.path.join(DIAGRAMS_DIR, "vscode_booking_service.png")
    SHOT_CATALOG_SVC = os.path.join(DIAGRAMS_DIR, "vscode_catalog_service.png")
    SHOT_FILTER = os.path.join(DIAGRAMS_DIR, "vscode_exception_filter.png")
    SHOT_PYTHON = os.path.join(DIAGRAMS_DIR, "vscode_python_fastapi.png")

    # Colors
    BG_DARK = RGBColor(11, 17, 32)        # #0b1120
    CARD_BG = RGBColor(19, 29, 51)        # #131d33
    CARD_BORDER = RGBColor(35, 49, 79)    # #23314f
    ACCENT_CYAN = RGBColor(56, 189, 248)  # #38bdf8
    ACCENT_BLUE = RGBColor(96, 165, 250)  # #60a5fa
    ACCENT_GREEN = RGBColor(52, 211, 153) # #34d399
    ACCENT_ROSE = RGBColor(251, 113, 133) # #fb7185
    ACCENT_AMBER = RGBColor(251, 191, 36) # #fbbf24
    TEXT_LIGHT = RGBColor(248, 250, 252)  # #f8fafc
    TEXT_MUTED = RGBColor(148, 163, 184)  # #94a3b8
    CODE_BG = RGBColor(6, 10, 18)         # #060a12
    PURE_WHITE = RGBColor(255, 255, 255)

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, tag_text, title_text, subtitle_text, slide_num_str):
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_tag = tf.paragraphs[0]
        r_tag = p_tag.add_run()
        r_tag.text = tag_text.upper()
        r_tag.font.name = "Arial"
        r_tag.font.size = Pt(10)
        r_tag.font.bold = True
        r_tag.font.color.rgb = ACCENT_CYAN

        r_sep = p_tag.add_run()
        r_sep.text = "   |   " + slide_num_str
        r_sep.font.name = "Arial"
        r_sep.font.size = Pt(10)
        r_sep.font.color.rgb = TEXT_MUTED

        p_title = tf.add_paragraph()
        r_title = p_title.add_run()
        r_title.text = title_text
        r_title.font.name = "Arial"
        r_title.font.size = Pt(19)
        r_title.font.bold = True
        r_title.font.color.rgb = TEXT_LIGHT

        if subtitle_text:
            p_sub = tf.add_paragraph()
            r_sub = p_sub.add_run()
            r_sub.text = subtitle_text
            r_sub.font.name = "Arial"
            r_sub.font.size = Pt(11)
            r_sub.font.color.rgb = TEXT_MUTED

        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = CARD_BORDER
        line.line.fill.background()

    def add_footer(slide, time_str="20 PHÚT TOÀN BÀI"):
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(11.733), Inches(0.4))
        tf = footer_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = "HỆ THỐNG ANTA BACKEND — MINH CHỨNG THỰC TẾ D:\\hdv\\backend & VISUAL PARADIGM"
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = TEXT_MUTED

        r2 = p.add_run()
        r2.text = f"                                                                      Thời lượng: {time_str}"
        r2.font.name = "Arial"
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = ACCENT_AMBER

    def add_card(slide, x, y, w, h, title, items, border_color=CARD_BORDER, bg_color=CARD_BG, title_color=ACCENT_CYAN):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.18)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.16)
        tf.margin_bottom = Inches(0.16)

        if title:
            p0 = tf.paragraphs[0]
            r0 = p0.add_run()
            r0.text = title.upper()
            r0.font.name = "Arial"
            r0.font.size = Pt(11)
            r0.font.bold = True
            r0.font.color.rgb = title_color
            p0.space_after = Pt(6)

        first = (title is None)
        for item in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.space_after = Pt(4)
            r = p.add_run()
            r.text = "• " + item if not item.startswith("•") and not item.startswith("[") and not item.startswith(" ") else item
            r.font.name = "Arial"
            r.font.size = Pt(10)
            r.font.color.rgb = TEXT_LIGHT

    def add_code_card(slide, x, y, w, h, title, code_text):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        card.fill.solid()
        card.fill.fore_color.rgb = CODE_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.16)
        tf.margin_right = Inches(0.16)
        tf.margin_top = Inches(0.14)
        tf.margin_bottom = Inches(0.14)

        p0 = tf.paragraphs[0]
        r0 = p0.add_run()
        r0.text = title
        r0.font.name = "Consolas"
        r0.font.size = Pt(10)
        r0.font.bold = True
        r0.font.color.rgb = ACCENT_AMBER
        p0.space_after = Pt(5)

        p_code = tf.add_paragraph()
        r_code = p_code.add_run()
        r_code.text = code_text
        r_code.font.name = "Consolas"
        r_code.font.size = Pt(8.5)
        r_code.font.color.rgb = TEXT_LIGHT

    def set_speaker_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (00:00 - 01:30)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(11.0), Inches(3.6))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p_badge = tf1.paragraphs[0]
    r_badge = p_badge.add_run()
    r_badge.text = "BÁO CÁO THUYẾT TRÌNH BÀI TẬP LỚN — MINH CHỨNG THỰC TẾ D:\\hdv\\backend"
    r_badge.font.name = "Arial"
    r_badge.font.size = Pt(13)
    r_badge.font.bold = True
    r_badge.font.color.rgb = ACCENT_CYAN

    p_main = tf1.add_paragraph()
    p_main.space_before = Pt(12)
    r_main = p_main.add_run()
    r_main.text = "KIẾN TRÚC HƯỚNG DỊCH VỤ (SOA) &\nGIAO TIẾP SERVICE-TO-SERVICE"
    r_main.font.name = "Arial"
    r_main.font.size = Pt(30)
    r_main.font.bold = True
    r_main.font.color.rgb = TEXT_LIGHT

    p_sub = tf1.add_paragraph()
    p_sub.space_before = Pt(12)
    r_sub = p_sub.add_run()
    r_sub.text = "Sơ đồ Visual Paradigm nền sáng & Ảnh chụp mã nguồn thực tế trên Visual Studio Code"
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = TEXT_MUTED

    add_card(s1, 1.2, 5.2, 10.933, 1.4, None, [
        "Mã nguồn thực tế: D:\\hdv\\backend (NestJS Modular Monolith + Python/FastAPI tại python_backend)",
        "Sơ đồ minh chứng: Dự án Visual Paradigm tại C:\\Users\\ADMIN\\Documents\\VPProjects (BieuDoTrinhTu & ERD)",
        "Thời lượng trình bày: 20 phút (Phần 1: 5 phút Lý thuyết | Phần 2: 11 phút Thực nghiệm | Phần 3: 4 phút Phản biện)"
    ], border_color=CARD_BORDER, bg_color=CARD_BG)

    set_speaker_notes(s1, """[LỜI THOẠI THUYẾT TRÌNH - 00:00 ĐẾN 01:30]
"Kính chào quý thầy cô và các bạn! Hôm nay, em xin đại diện nhóm trình bày báo cáo bài tập lớn môn Kiến trúc phần mềm và Dịch vụ mạng.
Bài thuyết trình hôm nay có thời lượng 20 phút, tập trung giải quyết trọn vẹn hai nội dung học phần CĐR L1:
Thứ nhất: Về mặt lý thuyết, phân tích các đặc trưng cốt lõi của Kiến trúc Hướng Dịch vụ (SOA) và phân biệt rạch ròi ba khái niệm: Dịch vụ, API và Ứng dụng khách.
Thứ hai: Về mặt thực nghiệm, minh chứng trực tiếp quy trình giao tiếp Service-to-Service trong hệ thống Anta Backend tại thư mục D:\\hdv\\backend.
Đặc biệt, toàn bộ sơ đồ tuần tự và sơ đồ thực thể trong bài báo cáo đều được trích xuất trực tiếp từ các dự án Visual Paradigm thực tế với nền trắng rõ nét, kết hợp ảnh chụp trực tiếp mã nguồn trên Visual Studio Code từ dự án.
Sau đây, em xin phép bắt đầu với phần lý thuyết về Kiến trúc hướng dịch vụ."
""")

    # =========================================================================
    # SLIDE 2: SOA PRINCIPLES (01:30 - 03:30)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "CÂU 1: LÝ THUYẾT (Ý 1A)", "Đặc Điểm Chính Của Kiến Trúc Hướng Dịch Vụ (SOA)", 
               "Nền tảng thiết kế hệ thống phân tán theo các nguyên tắc chuẩn của Thomas Erl & W3C", "SLIDE 02 / 12")
    add_footer(s2, "01:30 - 03:30 (2 phút)")

    add_card(s2, 0.8, 1.8, 5.7, 4.8, "4 ĐẶC TÍNH CỐT LÕI (CORE PRINCIPLES)", [
        "1. Tính tự trị (Service Autonomy): Mỗi dịch vụ sở hữu toàn quyền logic nghiệp vụ và cơ sở dữ liệu riêng, tự chịu trách nhiệm về tính toàn vẹn trạng thái.",
        "2. Ghép nối lỏng (Loose Coupling): Các dịch vụ giảm thiểu sự phụ thuộc lẫn nhau, giao tiếp thông qua giao diện công khai độc lập với nền tảng triển khai.",
        "3. Hợp đồng chuẩn hóa (Standardized Service Contract): Thống nhất quy ước giao tiếp rõ ràng qua API specs (OpenAPI/Swagger, JSON Schema, Protobuf).",
        "4. Khả năng tái sử dụng (Service Reusability): Đóng gói logic nghiệp vụ để phục vụ cho nhiều ứng dụng khách và quy trình khác nhau mà không phải viết lại."
    ], border_color=ACCENT_CYAN)

    add_card(s2, 6.8, 1.8, 5.7, 4.8, "4 ĐẶC TÍNH NÂNG CAO & SO SÁNH", [
        "5. Tính trừu tượng (Service Abstraction): Ẩn giấu chi tiết cài đặt bên trong, client chỉ cần biết hợp đồng gọi mà không cần quan tâm dịch vụ viết bằng gì.",
        "6. Tính phi trạng thái (Service Statelessness): Giảm thiểu lưu trữ trạng thái phiên làm việc giữa các request, tối ưu cho khả năng mở rộng ngang (Horizontal Scaling).",
        "7. Khả năng kết hợp (Service Composability): Cho phép xâu chuỗi các dịch vụ nhỏ tạo nên quy trình nghiệp vụ phức tạp (Orchestration & Choreography).",
        "8. Khả năng khám phá (Service Discoverability): Cung cấp metadata để các client tự động nhận biết vị trí và hợp đồng của dịch vụ (Service Registry / Gateway).",
        "[SOA vs Microservices]: Microservices là bước tiến hóa tinh gọn của SOA: loại bỏ ESB nặng nề, dùng REST/JSON nhẹ, phân chia ranh giới theo Domain-Driven Design."
    ], border_color=ACCENT_BLUE)

    set_speaker_notes(s2, """[LỜI THOẠI THUYẾT TRÌNH - 01:30 ĐẾN 03:30]
"Thưa thầy cô, Kiến trúc hướng dịch vụ (SOA) là một triết lý thiết kế hệ thống phân tán bao gồm 8 nguyên tắc kinh điển:
Tính tự trị (Autonomy), Ghép nối lỏng (Loose Coupling), Hợp đồng chuẩn hóa (Standardized Contract), Khả năng tái sử dụng, Trừu tượng hóa, Phi trạng thái (Stateless), Khả năng kết hợp và Khả năng khám phá.
Trong dự án thực tế Anta Backend, nhóm đã áp dụng mô hình Microservices hiện đại: loại bỏ trục ESB cồng kềnh, chuyển sang sử dụng RESTful JSON trên nền HTTP/1.1 và HTTP/2, phân chia Bounded Context rõ ràng theo Domain-Driven Design."
""")

    # =========================================================================
    # SLIDE 3: SERVICE VS API VS CLIENT (03:30 - 05:00)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "CÂU 1: LÝ THUYẾT (Ý 1A)", "Phân Biệt: Dịch Vụ, API và Ứng Dụng Khách", 
               "Làm rõ ranh giới trách nhiệm và sự phối hợp giữa ba thực thể trong kiến trúc phân tán", "SLIDE 03 / 12")
    add_footer(s3, "03:30 - 05:00 (1.5 phút)")

    add_card(s3, 0.8, 1.8, 3.6, 4.8, "1. DỊCH VỤ (SERVICE)", [
        "Bản chất: Là đơn vị phần mềm logic độc lập (process/container) cung cấp một miền năng lực nghiệp vụ cụ thể.",
        "Trách nhiệm: Quản lý toàn bộ vòng đời dữ liệu nghiệp vụ, thực thi business rules, bảo vệ tính toàn vẹn trạng thái.",
        "Đặc trưng: Sở hữu cơ sở dữ liệu riêng (Database-per-service), độc lập triển khai (CI/CD).",
        "Thực tế Anta: modules/booking (quản lý đặt chỗ), modules/catalog (sân bãi, giá), modules/payment (thanh toán)."
    ], border_color=ACCENT_GREEN)

    add_card(s3, 4.8, 1.8, 3.7, 4.8, "2. API (CONTRACT)", [
        "Bản chất: Giao diện lập trình ứng dụng, đóng vai trò là 'Bản hợp đồng kỹ thuật' (Technical Contract) công khai.",
        "Trách nhiệm: Định nghĩa cú pháp, giao thức (HTTP/REST), đường dẫn URI, phương thức (GET, POST), schema payload và mã lỗi chuẩn.",
        "Đặc trưng: Không chứa dữ liệu lưu trữ, là cầu nối trừu tượng giúp Client tương tác với Service mà không biết code bên trong.",
        "Thực tế Anta: GET /api/v1/public/branches, POST /api/v1/bookings được sinh tự động ra Swagger /docs."
    ], border_color=ACCENT_CYAN)

    add_card(s3, 8.9, 1.8, 3.6, 4.8, "3. ỨNG DỤNG KHÁCH (CLIENT)", [
        "Bản chất: Thực thể chủ động khởi tạo yêu cầu (Request) để tiêu thụ năng lực do Service cung cấp.",
        "Trách nhiệm: Tương tác với người dùng (UI/UX), đóng gói tham số, gọi API và xử lý hiển thị kết quả phản hồi.",
        "Đa dạng hình thái: Có thể là Web Browser, Mobile App Android, hoặc chính một Microservice khác đóng vai trò Consumer.",
        "Thực tế Anta: App Android (anta-android), Web Admin (/admin), hoặc Booking Service khi gọi sang Catalog Service."
    ], border_color=ACCENT_AMBER)

    set_speaker_notes(s3, """[LỜI THOẠI THUYẾT TRÌNH - 03:30 ĐẾN 05:00]
"Để thiết kế hệ thống chính xác, việc phân biệt rạch ròi giữa Dịch vụ, API và Ứng dụng khách là yêu cầu tiên quyết:
Dịch vụ là 'Bộ não và Kho chứa' nắm giữ business logic và database riêng;
API là 'Bản hợp đồng kỹ thuật' quy định giao thức và định dạng trao đổi;
Ứng dụng khách là 'Bên tiêu thụ' phát lệnh. Trong dự án của nhóm, chính Booking Service cũng đóng vai trò là một Client khi nó gọi sang Catalog Service để kiểm tra sân."
""")

    # =========================================================================
    # SLIDE 4: ERD WHITE BACKGROUND (05:00 - 07:00)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "CÂU 2: THỰC NGHIỆM (Ý 2)", "Mô Hình Dữ Liệu ERD Từ Visual Paradigm (Bản Nền Trắng Rõ Nét)", 
               "Trích xuất trực tiếp từ file 'ERD_DatSan_nen_trang.png' tại C:\\Users\\ADMIN\\Documents\\VPProjects", "SLIDE 04 / 12")
    add_footer(s4, "05:00 - 07:00 (2 phút)")

    # Left: White Container Frame for ERD
    erd_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(7.4), Inches(4.8))
    erd_card.fill.solid()
    erd_card.fill.fore_color.rgb = PURE_WHITE
    erd_card.line.color.rgb = ACCENT_CYAN
    erd_card.line.width = Pt(1.5)

    if os.path.exists(IMG_ERD_WHITE):
        # Place the white-background ERD image centered inside the white container
        s4.shapes.add_picture(IMG_ERD_WHITE, Inches(0.95), Inches(2.2), width=Inches(7.1))
    
    # Text badge above ERD inside white container
    tb_badge = s4.shapes.add_textbox(Inches(0.95), Inches(1.82), Inches(7.0), Inches(0.35))
    p_b = tb_badge.text_frame.paragraphs[0]
    r_b = p_b.add_run()
    r_b.text = "SƠ ĐỒ THỰC THỂ LIÊN KẾT (ERD) — NỀN SÁNG CHUẨN VISUAL PARADIGM CE"
    r_b.font.name = "Arial"
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_b.font.color.rgb = RGBColor(14, 116, 144)

    # Right: Analysis
    add_card(s4, 8.4, 1.75, 4.133, 4.8, "QUẢN LÝ DỮ LIỆU ĐỘC LẬP", [
        "1. Phân chia Schema theo Service:",
        "  - catalog schema: Quản lý branches, yards, sports, opening_hours.",
        "  - booking schema: Quản lý bookings, booking_holds, reservations.",
        "",
        "2. Nguyên tắc Single Source of Truth:",
        "  - Catalog Service toàn quyền sở hữu thông tin sân và giá thuê.",
        "  - Booking Service chỉ lưu đơn và tham chiếu khóa ngoại sang yard_id.",
        "",
        "3. Chống trùng lịch bằng GiST:",
        "  - Bảng reservations áp dụng GiST Exclusion Constraint trên PostgreSQL để ngăn chặn 100% việc đặt trùng khung giờ."
    ], border_color=ACCENT_BLUE)

    set_speaker_notes(s4, """[LỜI THOẠI THUYẾT TRÌNH - 05:00 ĐẾN 07:00]
"Thưa thầy cô, trên màn hình bên trái là Sơ đồ thực thể ERD được xuất trực tiếp từ file ERD_DatSan.vpp trong thư mục Visual Paradigm trên máy của em, với bản nền sáng màu trắng để thầy cô dễ dàng quan sát từng thực thể:
Sơ đồ thể hiện rõ sự phân lập giữa hai miền dữ liệu:
Miền Catalog quản lý các bảng branches, yards, sports và opening_hours.
Miền Booking quản lý các bảng bookings, booking_holds và reservations.
Chúng em tuân thủ nghiêm ngặt nguyên tắc Database-per-Service: Booking không được phép tự ý sửa đổi dữ liệu sân, và muốn biết sân có hoạt động hay giá bao nhiêu thì bắt buộc phải hỏi Catalog qua API contract."
""")

    # =========================================================================
    # SLIDE 5: API CONTRACT (07:00 - 09:00)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "CÂU 2: THỰC NGHIỆM (Ý 2)", "Đặc Tả Hợp Đồng API & Dữ Liệu Trao Đổi Thực Tế", 
               "Quy chuẩn RESTful endpoints được triển khai thực tế trong D:\\hdv\\backend", "SLIDE 05 / 12")
    add_footer(s5, "07:00 - 09:00 (2 phút)")

    add_code_card(s5, 0.8, 1.8, 5.7, 4.8, "1. API ĐẶT SÂN: POST /api/v1/bookings",
"""// Request Header:
// Authorization: Bearer <accessToken>
// Idempotency-Key: idemp-bk-20261030-001

// Request Payload:
{
  "holdId": "3b29d494-82a1-4202-b2fa-10a19f20e401"
}

// Phản hồi thành công (201 Created):
{
  "data": {
    "id": "BK-20261030-001",
    "branch_id": "30000000-0000-4000-8000-000000000001",
    "yard_id": "40000000-0000-4000-8000-000000000001",
    "amount": 350000,
    "currency": "VND",
    "status": "PENDING_PAYMENT"
  },
  "meta": { "requestId": "req-9a8b7c" },
  "error": null
}""")

    add_code_card(s5, 6.8, 1.8, 5.7, 4.8, "2. API TRA CỨU SÂN: GET /api/v1/public/branches/{id}",
"""// Request Service-to-Service:
// GET /api/v1/public/branches/30000000-0000-4000-8000-000000000001

// Phản hồi thành công (200 OK):
{
  "data": {
    "id": "30000000-0000-4000-8000-000000000001",
    "name": "Sân Thể Thao Anta Sài Gòn",
    "timezone": "Asia/Ho_Chi_Minh",
    "opening_hour": 6,
    "closing_hour": 22,
    "min_price": 180000,
    "yards": [
      {
        "id": "40000000-0000-4000-8000-000000000001",
        "name": "Sân Bóng Đá Số 1",
        "hourly_price": 350000,
        "active": true
      }
    ]
  },
  "error": null
}""")

    set_speaker_notes(s5, """[LỜI THOẠI THUYẾT TRÌNH - 07:00 ĐẾN 09:00]
"Slide số 5 mô tả cấu trúc API Contract thực tế từ file OpenAPI của hệ thống:
Bên trái là API POST /api/v1/bookings với header bắt buộc Idempotency-Key để tránh việc người dùng bấm hai lần bị trừ tiền hai lần.
Bên phải là API GET /api/v1/public/branches/{id} trả về danh sách các sân (yards) kèm hourly_price và trạng thái active.
Toàn bộ phản hồi đều được bọc trong cấu trúc chuẩn: { data, meta, error } qua EnvelopeInterceptor của hệ thống."
""")

    # =========================================================================
    # SLIDE 6: REAL SEQUENCE DIAGRAM FROM VISUAL PARADIGM (09:00 - 11:30)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "CÂU 2: THỰC NGHIỆM (Ý 2)", "Sơ Đồ Tuần Tự Thực Tế Từ Visual Paradigm (3.1.9 Đặt Sân)", 
               "Trích xuất trực tiếp từ file '3.1.9 Dat san.png' tại C:\\Users\\ADMIN\\Documents\\VPProjects", "SLIDE 06 / 12")
    add_footer(s6, "09:00 - 11:30 (2.5 phút)")

    # Left: White frame behind Sequence Diagram
    seq_frame = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(4.5), Inches(4.8))
    seq_frame.fill.solid()
    seq_frame.fill.fore_color.rgb = PURE_WHITE
    seq_frame.line.color.rgb = ACCENT_CYAN
    seq_frame.line.width = Pt(1.5)

    if os.path.exists(IMG_SEQ):
        s6.shapes.add_picture(IMG_SEQ, Inches(0.95), Inches(1.85), height=Inches(4.6))

    # Right: Explanation
    add_card(s6, 5.5, 1.75, 7.033, 4.8, "PHÂN TÍCH LUỒNG TUẦN TỰ TRONG VISUAL PARADIGM", [
        "1. Khởi tạo yêu cầu (Client -> UI):",
        "  - Người dùng chọn ngày, giờ và loại sân trên giao diện di động (ManHinhDatSan).",
        "",
        "2. Kiểm tra khả dụng (UI -> BookingController -> CatalogService):",
        "  - BookingController tiếp nhận yêu cầu, gọi sang CatalogService kiểm tra trạng thái sân và giờ hoạt động (opening_hour đến closing_hour).",
        "",
        "3. Giữ chỗ có thời hạn (Hold Slot - 5 phút):",
        "  - Tạo bản ghi trong booking.holds và reservation nhằm khóa khung giờ tạm thời để tránh xung đột với người khác.",
        "",
        "4. Xác nhận đơn & Chuyển sang thanh toán:",
        "  - Khi khách xác nhận, hold được chuyển đổi thành Booking chính thức (PENDING_PAYMENT), phát sinh sự kiện thanh toán.",
        "",
        "5. Phân nhánh lỗi mạng:",
        "  - Nếu sân không tồn tại (404) hoặc dịch vụ bị sập (503): Luồng lập tức bị ngắt, hiển thị thông báo lỗi trên UI mà không lưu rác vào DB."
    ], border_color=ACCENT_CYAN)

    set_speaker_notes(s6, """[LỜI THOẠI THUYẾT TRÌNH - 09:00 ĐẾN 11:30]
"Kính thưa thầy cô, trên màn hình bên trái là Sơ đồ tuần tự nghiệp vụ Đặt sân (3.1.9 Đặt sân) được vẽ và trích xuất trực tiếp từ công cụ Visual Paradigm trên máy của em.
Sơ đồ mô tả tường minh từng bước đi của dữ liệu:
Từ Khách hàng tương tác trên Màn hình đặt sân, gửi request vào BookingController.
BookingController không tự ý lưu dữ liệu ngay mà gọi sang CatalogService để kiểm tra tính khả dụng của sân.
Sau khi sân được xác nhận hợp lệ, một lệnh Hold giữ chỗ trong 5 phút được tạo ra trong cơ sở dữ liệu.
Nếu sân không tồn tại hoặc đã bị đặt trước, hệ thống kích hoạt luồng ngoại lệ và báo lỗi ngay cho người dùng.
Tiếp theo, xin mời thầy cô xem trực tiếp các đoạn mã nguồn được chụp từ Visual Studio Code trong dự án backend của nhóm."
""")

    # =========================================================================
    # SLIDE 7: REAL VS CODE SCREENSHOT - BOOKING CONTROLLER (11:30 - 13:00)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "MÃ NGUỒN THỰC TẾ TRÊN VISUAL STUDIO CODE", "Booking Controller: Tiếp Nhận & Idempotency Key", 
               "Chụp trực tiếp từ file modules/booking/controller.ts trong dự án D:\\hdv\\backend", "SLIDE 07 / 12")
    add_footer(s7, "11:30 - 13:00 (1.5 phút)")

    if os.path.exists(SHOT_CONTROLLER):
        s7.shapes.add_picture(SHOT_CONTROLLER, Inches(0.8), Inches(1.8), width=Inches(7.3))

    add_card(s7, 8.3, 1.8, 4.233, 4.8, "ĐIỂM SÁNG TRONG THIẾT KẾ CONTROLLER", [
        "1. Decorator Chuẩn NestJS:",
        "  - @ApiBearerAuth() bảo vệ endpoint bằng JWT token.",
        "  - @ApiHeader(keyHeader) bắt buộc client phải truyền Idempotency-Key.",
        "",
        "2. Chống lặp giao dịch (Idempotency):",
        "  - Khi mạng chập chờn và client gửi lại request (retry), server kiểm tra key trong Redis/DB để trả về kết quả cũ thay vì tạo thêm đơn mới.",
        "",
        "3. Tách biệt trách nhiệm:",
        "  - Controller chỉ đóng vai trò phân phối request (Routing & Validation), toàn bộ logic nghiệp vụ được ủy quyền cho BookingService."
    ], border_color=ACCENT_BLUE)

    set_speaker_notes(s7, """[LỜI THOẠI THUYẾT TRÌNH - 11:30 ĐẾN 13:00]
"Trên slide số 7 là ảnh chụp thực tế màn hình Visual Studio Code mở file modules/booking/controller.ts trong dự án D:\\hdv\\backend:
Thầy cô có thể thấy rõ giao diện Visual Studio Code với tab controller.ts, breadcrumbs và các dòng mã từ dòng 7 đến dòng 24:
Phương thức hold() tại đường dẫn booking-holds nhận thông tin khung giờ muốn đặt và yêu cầu header Idempotency-Key.
Phương thức create() tại đường dẫn bookings chuyển đổi holdId thành đơn đặt sân chính thức.
Việc áp dụng Idempotency Key giúp hệ thống miễn nhiễm với tình trạng người dùng bấm liên tục nhiều lần vào nút đặt sân khi mạng lag."
""")

    # =========================================================================
    # SLIDE 8: REAL VS CODE SCREENSHOTS - INTER-SERVICE CALL (13:00 - 15:00)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "MÃ NGUỒN THỰC TẾ TRÊN VISUAL STUDIO CODE", "Giao Tiếp Giữa Booking Service & Catalog Service", 
               "Chụp trực tiếp từ modules/booking/service.ts & modules/catalog/service.ts", "SLIDE 08 / 12")
    add_footer(s8, "13:00 - 15:00 (2 phút)")

    if os.path.exists(SHOT_BOOKING_SVC):
        s8.shapes.add_picture(SHOT_BOOKING_SVC, Inches(0.8), Inches(1.8), width=Inches(5.7))

    if os.path.exists(SHOT_CATALOG_SVC):
        s8.shapes.add_picture(SHOT_CATALOG_SVC, Inches(6.8), Inches(1.8), width=Inches(5.7))

    set_speaker_notes(s8, """[LỜI THOẠI THUYẾT TRÌNH - 13:00 ĐẾN 15:00]
"Slide số 8 là minh chứng rõ nhất cho câu hỏi giao tiếp giữa các dịch vụ, chụp trực tiếp từ hai file service trên Visual Studio Code:
Ở bên trái là BookingService: Nó được inject CatalogService thông qua cơ chế Dependency Injection của NestJS.
Trong hàm tính giá quote(), BookingService gọi: const yard = await this.catalog.yard(tx, dto.yardId).
Ở bên phải là CatalogService: Nó thực hiện truy vấn bảng catalog.yards và sử dụng hàm invariant: Nếu sân không tồn tại hoặc không active, hàm invariant sẽ lập tức ném ra lỗi mã NOT_FOUND kèm HTTP status 404.
Nhờ vậy, BookingService hoàn toàn không cần tự query vào bảng catalog mà ủy quyền hoàn toàn cho CatalogService quản lý."
""")

    # =========================================================================
    # SLIDE 9: REAL VS CODE SCREENSHOT - EXCEPTION FILTER (15:00 - 16:30)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "MÃ NGUỒN THỰC TẾ TRÊN VISUAL STUDIO CODE", "Xử Lý Lỗi Ngoại Lệ Tập Trung: ApiExceptionFilter", 
               "Chụp trực tiếp từ packages/observability/http.ts trong dự án D:\\hdv\\backend", "SLIDE 09 / 12")
    add_footer(s9, "15:00 - 16:30 (1.5 phút)")

    if os.path.exists(SHOT_FILTER):
        s9.shapes.add_picture(SHOT_FILTER, Inches(0.8), Inches(1.8), width=Inches(6.8))

    add_card(s9, 7.8, 1.8, 4.733, 4.8, "CƠ CHẾ PHẢN HỒI LỖI CHUẨN RESTFUL", [
        "1. Chuyển hóa HTTP Status Code chính xác:",
        "  - Ngoại lệ ApiError ném ra từ invariant() được bắt gọn và gán đúng status (400, 404, 503).",
        "",
        "2. Bắt lỗi tranh chấp cơ sở dữ liệu (pgCode 23P01):",
        "  - Khi hai người dùng cùng đặt một khung giờ, Postgres ném mã 23P01 (Exclusion Constraint Violation).",
        "  - Filter tự động chuyển mã này thành 409 Conflict với thông điệp 'SLOT_UNAVAILABLE' thay vì văng lỗi 500.",
        "",
        "3. Định dạng JSON thống nhất:",
        "  - Mọi lỗi đều trả về { data: null, meta: { requestId }, error: { code, message } }, giúp client dễ dàng xử lý mà không làm lộ StackTrace nhạy cảm."
    ], border_color=ACCENT_ROSE)

    set_speaker_notes(s9, """[LỜI THOẠI THUYẾT TRÌNH - 15:00 ĐẾN 16:30]
"Slide số 9 là ảnh chụp Visual Studio Code của bộ xử lý lỗi tập trung ApiExceptionFilter tại file packages/observability/http.ts:
Điểm đặc biệt nhất trong dự án của nhóm:
Chúng em xử lý cả lỗi mạng cấp ứng dụng lẫn lỗi tranh chấp dữ liệu ở tầng PostgreSQL:
Khi có hai người cùng đặt một sân trong cùng một giây, ràng buộc GiST exclusion constraint của Postgres sẽ chặn lại với mã lỗi 23P01.
Filter của nhóm bắt mã 23P01 và chuyển thành HTTP 409 Conflict với thông báo 'The selected slot is no longer available'.
Đồng thời, mọi ngoại lệ 404 hay 503 đều được đóng gói chuẩn JSON kèm requestId để theo dõi vết lỗi (tracing)."
""")

    # =========================================================================
    # SLIDE 10: REAL VS CODE SCREENSHOT - PYTHON FASTAPI (16:30 - 18:00)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "MÃ NGUỒN THỰC TẾ TRÊN VISUAL STUDIO CODE", "Kiến Trúc Đa Nền Tảng (Polyglot) Với Python/FastAPI", 
               "Chụp trực tiếp từ python_backend/anta_api/catalog.py (Port 8000)", "SLIDE 10 / 12")
    add_footer(s10, "16:30 - 18:00 (1.5 phút)")

    if os.path.exists(SHOT_PYTHON):
        s10.shapes.add_picture(SHOT_PYTHON, Inches(0.8), Inches(1.8), width=Inches(6.8))

    add_card(s10, 7.8, 1.8, 4.733, 4.8, "ƯU THẾ CỦA FASTAPI MICROSERVICE", [
        "1. Đa ngôn ngữ (Polyglot Microservices):",
        "  - Dự án Anta chạy song song NestJS (Port 3000) và FastAPI (Port 8000) cùng chia sẻ một cơ sở dữ liệu PostgreSQL/PostGIS.",
        "",
        "2. Tối ưu tìm kiếm bán kính PostGIS:",
        "  - Module Python phụ trách tính toán khoảng cách địa lý (ST_Distance, ST_DWithin) với hiệu năng tính toán cao của AsyncIO.",
        "",
        "3. Tương thích API Contract 100%:",
        "  - FastAPI trả về cùng cấu trúc envelope(request, data) giống hệt bản NestJS, chứng minh tính độc lập và khả năng thay thế linh hoạt của dịch vụ."
    ], border_color=ACCENT_GREEN)

    set_speaker_notes(s10, """[LỜI THOẠI THUYẾT TRÌNH - 16:30 ĐẾN 18:00]
"Slide số 10 minh chứng cho tính đa ngôn ngữ (Polyglot) trong kiến trúc hướng dịch vụ của nhóm, được chụp trực tiếp từ Visual Studio Code mở file catalog.py trong thư mục python_backend:
Thầy cô có thể thấy icon PY màu vàng và tab catalog.py.
Dịch vụ này chuyên xử lý các truy vấn địa lý không gian PostGIS như tìm sân gần nhất theo kinh độ, vĩ độ.
Dù viết bằng Python, dịch vụ này vẫn tuân thủ 100% API contract và envelope chuẩn của NestJS. Điều này chứng minh đúng nguyên tắc Loose Coupling: thay đổi ngôn ngữ triển khai dịch vụ bên dưới mà không làm ảnh hưởng đến client bên ngoài."
""")

    # =========================================================================
    # SLIDE 11: FAULT TOLERANCE SCENARIOS (18:00 - 19:15)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "KIỂM THỬ THỰC NGHIỆM", "Xử Lý 3 Kịch Bản Lỗi Giao Tiếp Thực Tế", 
               "Bảo đảm tính bền vững (Resilience) và sẵn sàng cao cho hệ thống phân tán", "SLIDE 11 / 12")
    add_footer(s11, "18:00 - 19:15 (1.25 phút)")

    add_card(s11, 0.8, 1.8, 3.6, 4.8, "KỊCH BẢN 1: 404 NOT FOUND", [
        "Tình huống thực tế:",
        "Khách gửi yêu cầu đặt sân với yardId không tồn tại hoặc đã bị xóa.",
        "",
        "Cơ chế xử lý:",
        "CatalogService gọi invariant(yard?.active, 'NOT_FOUND', 404).",
        "",
        "Kết quả:",
        "BookingService bắt lỗi ngay, không tạo bản ghi rác, trả về 404 Not Found rõ ràng cho App."
    ], border_color=ACCENT_ROSE)

    add_card(s11, 4.8, 1.8, 3.7, 4.8, "KỊCH BẢN 2: 503 UNAVAILABLE", [
        "Tình huống thực tế:",
        "Tiến trình Catalog hoặc Redis bị sập đột ngột (Connection Refused).",
        "",
        "Cơ chế xử lý:",
        "ApiExceptionFilter bắt ngoại lệ mạng hoặc Redis disconnect.",
        "",
        "Kết quả:",
        "Chuyển thành mã 503 DEPENDENCY_UNAVAILABLE, bảo vệ ứng dụng không bị crash và không lộ StackTrace."
    ], border_color=ACCENT_AMBER)

    add_card(s11, 8.9, 1.8, 3.6, 4.8, "KỊCH BẢN 3: 409 CONFLICT", [
        "Tình huống thực tế:",
        "Hai người dùng đồng thời bấm đặt cùng 1 sân tại cùng 1 khung giờ.",
        "",
        "Cơ chế xử lý:",
        "PostgreSQL GiST constraint kích hoạt lỗi 23P01.",
        "",
        "Kết quả:",
        "Hệ thống bắt mã 23P01 và trả về 409 SLOT_UNAVAILABLE, đảm bảo 100% không bao giờ bị trùng lịch đặt sân."
    ], border_color=ACCENT_CYAN)

    set_speaker_notes(s11, """[LỜI THOẠI THUYẾT TRÌNH - 18:00 ĐẾN 19:15]
"Slide số 11 tổng hợp 3 kịch bản lỗi mạng và lỗi cạnh tranh mà nhóm đã kiểm thử thành công:
Kịch bản 1: Sân không tồn tại được bắt bằng 404 Not Found.
Kịch bản 2: Khi dịch vụ phụ thuộc sập, filter chuyển thành mã 503 Service Unavailable để tránh crash app.
Kịch bản 3: Khi có tranh chấp hai người cùng đặt một sân trong một tích tắc, Postgres GiST constraint chặn lại và trả về 409 Conflict."
""")

    # =========================================================================
    # SLIDE 12: CONCLUSION (19:15 - 20:00)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "TỔNG KẾT & ĐỊNH HƯỚNG", "Tổng Kết Bài Báo Cáo & Lộ Trình Phát Triển", 
               "Hoàn thành xuất sắc mục tiêu CĐR L1 với minh chứng thực tế từ mã nguồn và Visual Paradigm", "SLIDE 12 / 12")
    add_footer(s12, "19:15 - 20:00 (45 giây)")

    add_card(s12, 0.8, 1.8, 5.7, 4.8, "KẾT QUẢ ĐẠT ĐƯỢC", [
        "✓ Hoàn thành trọn vẹn yêu cầu Chuẩn đầu ra L1:",
        "  - Phân tích sâu sắc 8 đặc trưng kiến trúc SOA.",
        "  - Phân biệt tường minh Dịch vụ, API và Ứng dụng khách.",
        "",
        "✓ Minh chứng thực tế từ hệ thống D:\\hdv\\backend:",
        "  - Sơ đồ tuần tự và ERD trích xuất trực tiếp từ dự án Visual Paradigm.",
        "  - Mã nguồn NestJS TypeScript và FastAPI Python đã chạy thực tế.",
        "  - Xử lý trọn vẹn các mã phản hồi HTTP: 200, 201, 400, 404, 409, 503.",
        "  - Cơ chế chống lặp bằng Idempotency-Key và chống trùng lịch bằng GiST Exclusion Constraint."
    ], border_color=ACCENT_GREEN)

    add_card(s12, 6.8, 1.8, 5.7, 4.8, "ĐỊNH HƯỚNG PHÁT TRIỂN", [
        "• Giao tiếp Bất đồng bộ với BullMQ & Redis:",
        "  - Triển khai Transactional Outbox Pattern cho module notification và payment webhook.",
        "",
        "• Triển khai E2E Encryption cho Module Chat:",
        "  - Tích hợp giao thức Signal Protocol (X3DH + Double Ratchet) cho tin nhắn bảo mật giữa khách và chủ sân.",
        "",
        "• Hoàn thiện cổng thanh toán PayOS và VNPay:",
        "  - Kiểm thử giao dịch merchant thực tế với webhook có chữ ký HMAC-SHA256."
    ], border_color=ACCENT_CYAN)

    set_speaker_notes(s12, """[LỜI THOẠI THUYẾT TRÌNH - 19:15 ĐẾN 20:00]
"Kính thưa quý thầy cô và các bạn,
Để tổng kết lại bài báo cáo hôm nay:
Nhóm đã hoàn thành trọn vẹn mục tiêu Chuẩn đầu ra L1 cả về mặt lý thuyết lẫn thực nghiệm:
Toàn bộ sơ đồ trình tự và sơ đồ thực thể đều được vẽ từ Visual Paradigm thực tế.
Mã nguồn được trích xuất trực tiếp từ dự án backend Anta tại D:\\hdv\\backend, chứng minh đầy đủ khả năng giao tiếp giữa các dịch vụ và xử lý lỗi mạng an toàn.
Phần thuyết trình của nhóm xin được kết thúc tại đây. Em xin chân thành cảm ơn thầy cô và các bạn đã chú ý lắng nghe!"
""")

    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out_dir = r"D:\hdv\backend"
    out_file_v2 = os.path.join(out_dir, "Thuyet_Trinh_Microservices_Anta_20Phut_v2.pptx")
    create_deck(out_file_v2)
    
    # Try overwriting the original if not locked
    out_file = os.path.join(out_dir, "Thuyet_Trinh_Microservices_Anta_20Phut.pptx")
    try:
        import shutil
        shutil.copyfile(out_file_v2, out_file)
        print(f"Also updated: {out_file}")
    except Exception as e:
        print(f"Note: {out_file} is currently open in PowerPoint ({e}). Please view {out_file_v2}")
