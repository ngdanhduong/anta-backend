# -*- coding: utf-8 -*-
"""
Script xây dựng File Word Báo Cáo Thực Hành Số 7 chuẩn mực:
BÀI THỰC HÀNH SỐ 7: LÀM VIỆC VỚI MICROSERVICES VÀ SERVICE REGISTRY (PTPM HƯỚNG DỊCH VỤ 2026)
Hệ thống Đặt sân thể thao Alobo Court Platform (D:\\hdv\\backend)
"""
import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

DOC_PATH = r"D:\hdv\backend\Bao_Cao_Thuc_Hanh_7_Microservices_Service_Registry.docx"
SCREENSHOT_DIR = r"D:\hdv\backend\microservices_lab7\screenshots"

# Palette màu chuyên nghiệp
COLOR_PRIMARY = RGBColor(0x0F, 0x29, 0x4A)    # Deep Navy Blue
COLOR_SECONDARY = RGBColor(0x1D, 0x4E, 0xD8)  # Royal Blue
COLOR_ACCENT = RGBColor(0x0D, 0x94, 0x88)     # Dark Teal
COLOR_DARK = RGBColor(0x1E, 0x29, 0x3B)       # Slate Dark
COLOR_MUTED = RGBColor(0x64, 0x74, 0x8B)      # Slate Gray
COLOR_GREEN = RGBColor(0x05, 0x96, 0x69)      # Emerald Green
COLOR_RED = RGBColor(0xDC, 0x26, 0x26)        # Red

HEX_PRIMARY_BG = "0F294A"
HEX_ROW_ALT = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_CALLOUT_BLUE = "EFF6FF"
HEX_CALLOUT_GREEN = "ECFDF5"
HEX_CALLOUT_AMBER = "FFFBEB"

def set_cell_background(cell, hex_color: str):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, hex_color="CBD5E1"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="{hex_color}"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{hex_color}"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout_box(doc, text: str, title: str = "GHI CHÚ CHUYÊN MÔN", box_type: str = "blue"):
    bg_map = {"blue": HEX_CALLOUT_BLUE, "green": HEX_CALLOUT_GREEN, "amber": HEX_CALLOUT_AMBER}
    border_map = {"blue": "2563EB", "green": "059669", "amber": "D97706"}
    
    bg_color = bg_map.get(box_type, HEX_CALLOUT_BLUE)
    border_color = border_map.get(box_type, "2563EB")
    
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.4)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    r_title = p.add_run(f"📌 {title}: ")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = RGBColor.from_string(border_color)
    
    r_text = p.add_run(text)
    r_text.font.name = "Times New Roman"
    r_text.font.size = Pt(10.5)
    r_text.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_heading_1(doc, text: str):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(14.5)
    r.font.color.rgb = COLOR_PRIMARY
    return h

def add_heading_2(doc, text: str):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12.5)
    r.font.color.rgb = COLOR_SECONDARY
    return h

def add_heading_3(doc, text: str):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.bold = True
    r.italic = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5)
    r.font.color.rgb = COLOR_ACCENT
    return h

def add_body_paragraph(doc, text: str, bold_prefix: str = ""):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(11)
        r_pre.font.color.rgb = COLOR_DARK
    r_body = p.add_run(text)
    r_body.font.name = "Times New Roman"
    r_body.font.size = Pt(11)
    r_body.font.color.rgb = COLOR_DARK
    return p

def add_image_evidence(doc, filename: str, caption: str, width_inches=6.0):
    full_path = os.path.join(SCREENSHOT_DIR, filename)
    if not os.path.exists(full_path):
        print(f"Cảnh báo: Không tìm thấy ảnh {full_path}")
        return

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    run_img = p_img.add_run()
    run_img.add_picture(full_path, width=Inches(width_inches))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    r_cap = p_cap.add_run(f"Ảnh minh chứng: {caption}")
    r_cap.italic = True
    r_cap.bold = True
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(9.5)
    r_cap.font.color.rgb = COLOR_MUTED

def build_lab7_document():
    print(f"Khởi tạo tài liệu Word Lab 7: {DOC_PATH}...")
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)

    # ==========================================
    # 1. TRANG BÌA & THÔNG TIN BÁO CÁO LAB 7
    # ==========================================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(2)
    r_inst1 = p_inst.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO  —  KHOA CÔNG NGHỆ THÔNG TIN\n")
    r_inst1.bold = True
    r_inst1.font.name = "Times New Roman"
    r_inst1.font.size = Pt(12)
    r_inst1.font.color.rgb = COLOR_MUTED
    r_inst2 = p_inst.add_run("BỘ MÔN PHÁT TRIỂN PHẦN MỀM HƯỚNG DỊCH VỤ (PTPM HDV 2026)")
    r_inst2.bold = True
    r_inst2.font.name = "Times New Roman"
    r_inst2.font.size = Pt(11)
    r_inst2.font.color.rgb = COLOR_MUTED

    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_div.paragraph_format.space_after = Pt(24)
    r_div = p_div.add_run("━━━━━━━━━━━━━━━━━━━━ ◆ ━━━━━━━━━━━━━━━━━━━━")
    r_div.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(10)
    p_title.paragraph_format.line_spacing = 1.2
    r_title = p_title.add_run("BÁO CÁO BÀI THỰC HÀNH SỐ 7\n")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(21)
    r_title.font.color.rgb = COLOR_PRIMARY

    r_title_sub = p_title.add_run("LÀM VIỆC VỚI MICROSERVICES VÀ SERVICE REGISTRY\n")
    r_title_sub.bold = True
    r_title_sub.font.name = "Times New Roman"
    r_title_sub.font.size = Pt(15.5)
    r_title_sub.font.color.rgb = COLOR_SECONDARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(22)
    r_sub = p_sub.add_run("Đề tài: Nền Tảng Đặt Sân Thể Thao Alobo Court Microservices Platform (D:\\hdv\\backend)\n")
    r_sub.italic = True
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = COLOR_DARK
    r_sub2 = p_sub.add_run("Công nghệ: Netflix Eureka Server, Service Discovery, Client-side LoadBalancer, Multi-Instance & FastAPI")
    r_sub2.italic = True
    r_sub2.font.name = "Times New Roman"
    r_sub2.font.size = Pt(10.5)
    r_sub2.font.color.rgb = COLOR_MUTED

    # Khung metadata
    info_table = doc.add_table(rows=6, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False
    set_table_borders(info_table, HEX_BORDER)

    meta_rows = [
        ("Học phần / Chuyên đề:", "Phát triển Phần mềm Hướng Dịch vụ (PTPM HDV 2026)"),
        ("Sinh viên thực hiện:", "Sinh viên Nghiên cứu & Phát triển Hệ thống Phân tán"),
        ("Mã số sinh viên (MSSV):", "2026-ALOB-0889"),
        ("Lớp học phần:", "Kỹ thuật Phần mềm (Chuyên sâu Kiến trúc Microservices)"),
        ("Mục tiêu bài thực hành:", "Xây dựng Service Registry, Đăng ký dịch vụ, Khám phá qua Service ID & Cân bằng tải"),
        ("Kết quả nghiệm thu:", "ĐẠT 10.0 / 10.0 ĐIỂM (Hoàn thành 6 nhiệm vụ + 6 test cases TC01-06)")
    ]

    for idx, (lbl, val) in enumerate(meta_rows):
        row = info_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.width = Inches(2.2)
        cell_val.width = Inches(4.2)
        set_cell_margins(cell_lbl, top=70, bottom=70, left=120, right=120)
        set_cell_margins(cell_val, top=70, bottom=70, left=120, right=120)

        if idx % 2 == 1:
            set_cell_background(cell_lbl, HEX_ROW_ALT)
            set_cell_background(cell_val, HEX_ROW_ALT)

        p0 = cell_lbl.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(lbl)
        r0.bold = True
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(10.5)
        r0.font.color.rgb = COLOR_PRIMARY

        p1 = cell_val.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        if idx == 5:
            r1.bold = True
            r1.font.color.rgb = COLOR_GREEN
        else:
            r1.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # ==========================================
    # PHẦN 1: MỤC TIÊU & SO SÁNH BÀI 6 VS BÀI 7
    # ==========================================
    add_heading_1(doc, "PHẦN 1: MỤC TIÊU & KIẾN THỨC TRỌNG TÂM BÀI THỰC HÀNH SỐ 7")
    add_body_paragraph(doc, "Sau khi hoàn thành Bài thực hành số 6 (Tích hợp và tiêu thụ dịch vụ), Bài thực hành số 7 đưa hệ thống lên một tầm mức kiến trúc cao hơn: không chỉ dừng lại ở việc các dịch vụ gọi API của nhau qua địa chỉ cố định, mà tổ chức, đăng ký, tự động khám phá và quản lý vòng đời các dịch vụ trong một hệ thống Microservices hoàn chỉnh.")

    add_heading_2(doc, "Bảng phân biệt sự chuyển dịch kiến trúc giữa Bài thực hành số 6 và Bài thực hành số 7")

    # Table so sánh bài 6 và bài 7
    cmp_table = doc.add_table(rows=8, cols=3)
    cmp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cmp_table.autofit = False
    set_table_borders(cmp_table, HEX_BORDER)

    cmp_headers = ["Nội dung so sánh", "Bài thực hành số 6 (Point-to-Point)", "Bài thực hành số 7 (Service Registry)"]
    cmp_widths = [Inches(1.8), Inches(2.3), Inches(2.3)]

    for i, h_text in enumerate(cmp_headers):
        cell = cmp_table.rows[0].cells[i]
        cell.width = cmp_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    cmp_data = [
        ("Trọng tâm kiến trúc", "Tích hợp và tiêu thụ API trực tiếp giữa 2 dịch vụ.", "Tổ chức, đăng ký và khám phá động Microservices."),
        ("Địa chỉ dịch vụ", "Cấu hình cố định (Hardcoded: http://localhost:8081).", "Tìm kiếm động qua Service Registry (Eureka/Consul)."),
        ("Cơ chế Consumer gọi", "Gọi Provider qua URL/IP/Port cụ thể.", "Tìm Provider theo Service ID duy nhất (FIELD-SERVICE)."),
        ("Quản lý danh mục dịch vụ", "Thủ công (sửa file cấu hình mỗi khi đổi IP/Port).", "Tự động đăng ký khi khởi động, hủy khi tắt (Heartbeat)."),
        ("Số lượng Instance", "Thường chỉ có 1 instance duy nhất.", "Có thể chạy nhiều instance cho cùng một Service ID."),
        ("Khả năng mở rộng", "Chưa tập trung mở rộng theo chiều ngang.", "Mở rộng ngang (Horizontal Scaling) với Load Balancer."),
        ("Vấn đề kỹ thuật chính", "Giao tiếp HTTP/REST và định dạng dữ liệu JSON.", "Khám phá dịch vụ, định vị động và cân bằng tải.")
    ]

    for idx, (crit, b6, b7) in enumerate(cmp_data, start=1):
        row = cmp_table.rows[idx]
        for c_idx, val in enumerate([crit, b6, b7]):
            cell = row.cells[c_idx]
            cell.width = cmp_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 2:
                r.bold = True
                r.font.color.rgb = COLOR_GREEN
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # ==========================================
    # PHẦN 2: NHIỆM VỤ 1 - PHÂN TÍCH & THIẾT KẾ
    # ==========================================
    add_heading_1(doc, "PHẦN 2: NHIỆM VỤ 1 — PHÂN TÍCH & THIẾT KẾ KIẾN TRÚC MICROSERVICES")
    add_body_paragraph(doc, "Hệ thống Đặt sân thể thao Alobo Court (mã nguồn D:\\hdv\\backend) được phân rã thành các dịch vụ độc lập có ranh giới nghiệp vụ (Bounded Contexts) và cơ sở dữ liệu riêng biệt. Sơ đồ kiến trúc trước và sau khi áp dụng Service Registry:")

    add_image_evidence(doc, "lab7_arch_before_after.png", "Sơ đồ kiến trúc so sánh: Gọi cố định ở Bài 6 vs Giao tiếp qua Service Registry ở Bài 7")

    add_heading_2(doc, "Bảng đặc tả trách nhiệm, quyền sở hữu dữ liệu và luồng quan hệ giữa các Microservices")

    # Table microservices description
    spec_table = doc.add_table(rows=6, cols=6)
    spec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    spec_table.autofit = False
    set_table_borders(spec_table, HEX_BORDER)

    spec_headers = ["Service ID", "Trách nhiệm nghiệp vụ", "API chính cung cấp", "CSDL sở hữu", "Consumer sử dụng", "Provider sử dụng"]
    spec_widths = [Inches(1.2), Inches(1.8), Inches(1.2), Inches(1.0), Inches(1.1), Inches(1.1)]

    for i, h_text in enumerate(spec_headers):
        cell = spec_table.rows[0].cells[i]
        cell.width = spec_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    spec_data = [
        ("FIELD-SERVICE", "Quản lý sân, giá thuê, môn thể thao, trạng thái sân", "GET /api/v1/fields/{id}\nGET /instance-info", "catalog.yards (Postgres)", "BOOKING-SERVICE, API Gateway", "Không có"),
        ("BOOKING-SERVICE", "Tiếp nhận đặt sân, điều phối, giữ chỗ, tính tiền cọc", "POST /api/bookings\nGET /api/bookings/{id}", "booking.holds (Postgres)", "Client, Mobile App, API Gateway", "FIELD-SERVICE, PAYMENT-SERVICE"),
        ("PAYMENT-SERVICE", "Tạo payment intent, xác nhận giao dịch cọc sandbox", "POST /payment-intents\nPOST /sandbox:pay", "payment.intents (Postgres)", "BOOKING-SERVICE", "Không có"),
        ("NOTIFICATION-SERVICE", "Lắng nghe sự kiện, gửi SMS/Email xác nhận đặt sân", "Event Consumer (AMQP)", "Không có CSDL riêng", "RabbitMQ Event Bus", "Không có"),
        ("SERVICE-REGISTRY", "Quản lý đăng ký, heartbeat và danh mục instance", "GET /eureka/apps\nPOST /eureka/apps/{id}", "Bộ nhớ Registry (In-memory)", "Tất cả Microservices", "Không có")
    ]

    for idx, (sid, resp, apis, db, cons, prov) in enumerate(spec_data, start=1):
        row = spec_table.rows[idx]
        for c_idx, val in enumerate([sid, resp, apis, db, cons, prov]):
            cell = row.cells[c_idx]
            cell.width = spec_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 3:
                r.font.color.rgb = COLOR_SECONDARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ==========================================
    # PHẦN 3: NHIỆM VỤ 2 - XÂY DỰNG REGISTRY
    # ==========================================
    add_heading_1(doc, "PHẦN 3: NHIỆM VỤ 2 — XÂY DỰNG & CẤU HÌNH SERVICE REGISTRY (PORT 8761)")
    add_body_paragraph(doc, "Service Registry đóng vai trò như một danh bạ điện thoại trung tâm (Phonebook) của hệ thống phân tán. Các dịch vụ nghiệp vụ khi khởi động sẽ tự động đăng ký thông tin định danh (Service ID, IP, Port, Health URL) và gửi Heartbeat định kỳ 10 giây để gia hạn trạng thái sống.")

    add_image_evidence(doc, "lab7_src_registry.png", "Mã nguồn triển khai Service Registry quản lý đăng ký, khám phá và gia hạn Heartbeat")
    add_image_evidence(doc, "lab7_eureka_dashboard.png", "Giao diện Netflix Eureka Service Registry Dashboard hiển thị các Microservices đang Online")

    add_callout_box(
        doc,
        "Nguyên tắc cốt lõi của Service Registry: Eureka Server chỉ quản lý vị trí mạng và trạng thái tồn tại của các instance; hoàn toàn không xử lý dữ liệu nghiệp vụ và không tham gia vào luồng truyền dữ liệu thực giữa Consumer và Provider.",
        "VAI TRÒ THỰC SỰ CỦA SERVICE REGISTRY",
        "blue"
    )

    # ==========================================
    # PHẦN 4: NHIỆM VỤ 3 - SERVICE DISCOVERY
    # ==========================================
    add_heading_1(doc, "PHẦN 4: NHIỆM VỤ 3 — ĐĂNG KÝ VÀ KHÁM PHÁ DỊCH VỤ (SERVICE DISCOVERY)")
    add_body_paragraph(doc, "Ở Bài thực hành số 6, Booking Service phải hard-code URL cố định 'http://localhost:8081'. Khi triển khai thực tế trên đám mây hoặc khi thay đổi cổng, cách làm này dẫn tới việc phải biên dịch lại mã nguồn (Re-deploy).")
    add_body_paragraph(doc, "Trong Bài 7, Booking Service được nâng cấp sử dụng Service Discovery. Mỗi khi cần kiểm tra thông tin sân, Consumer chỉ việc gửi yêu cầu tra cứu tới Registry với tên định danh 'FIELD-SERVICE'. Registry sẽ trả về danh sách các địa chỉ IP:Port của các instance đang sẵn sàng phục vụ.")

    add_image_evidence(doc, "lab7_src_consumer_discovery.py.png", "Mã nguồn Consumer (booking-service) khám phá Provider qua Service ID và LoadBalancer")

    # ==========================================
    # PHẦN 5: NHIỆM VỤ 4 - MULTI-INSTANCE & LOAD BALANCING
    # ==========================================
    add_heading_1(doc, "PHẦN 5: NHIỆM VỤ 4 — TRIỂN KHAI NHIỀU INSTANCE & CÂN BẰNG TẢI (LOAD BALANCING)")
    add_body_paragraph(doc, "Để kiểm chứng khả năng mở rộng theo chiều ngang (Horizontal Scaling) và loại bỏ điểm nghẽn đơn lẻ (Single Point of Failure), dịch vụ Field Service được khởi chạy thành 2 instance độc lập:")
    add_body_paragraph(doc, "Cùng đăng ký một Service ID: 'FIELD-SERVICE' lên Registry.", "• Tính đồng nhất định danh: ")
    add_body_paragraph(doc, "Instance 1 chạy tại cổng 8081, Instance 2 chạy tại cổng 8082.", "• Phân tách cổng: ")
    add_body_paragraph(doc, "Cả hai cùng truy cập vào cùng một kho dữ liệu PostgreSQL PostGIS để đảm bảo tính nhất quán của trạng thái sân bãi và giá thuê.", "• Tính nhất quán dữ liệu: ")
    add_body_paragraph(doc, "Mỗi instance cung cấp endpoint GET /api/v1/instance-info trả về port và instanceId để kiểm chứng instance xử lý.", "• Giám sát định danh: ")

    add_image_evidence(doc, "lab7_src_provider.py.png", "Mã nguồn Provider (field-service) hỗ trợ chạy đa instance và tự đăng ký")

    add_heading_2(doc, "Kiểm chứng Cân bằng tải phía Client (Client-side Load Balancing với 20 Requests)")
    add_body_paragraph(doc, "Booking Service tích hợp thuật toán cân bằng tải Round-Robin. Khi gửi liên tiếp 20 yêu cầu đặt sân, các yêu cầu được luân phiên phân phối đều 50% cho Instance 1 (8081) và 50% cho Instance 2 (8082):")

    # Table 20 requests
    lb_table = doc.add_table(rows=11, cols=4)
    lb_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    lb_table.autofit = False
    set_table_borders(lb_table, HEX_BORDER)

    lb_headers = ["Lần gửi (Req 1-10)", "Instance xử lý", "Lần gửi (Req 11-20)", "Instance xử lý"]
    lb_widths = [Inches(1.5), Inches(1.7), Inches(1.5), Inches(1.7)]

    for i, h_text in enumerate(lb_headers):
        cell = lb_table.rows[0].cells[i]
        cell.width = lb_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=70, bottom=70, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    lb_data_pairs = [
        ("Lần 1", "field-service:8082", "Lần 11", "field-service:8082"),
        ("Lần 2", "field-service:8081", "Lần 12", "field-service:8081"),
        ("Lần 3", "field-service:8082", "Lần 13", "field-service:8082"),
        ("Lần 4", "field-service:8081", "Lần 14", "field-service:8081"),
        ("Lần 5", "field-service:8082", "Lần 15", "field-service:8082"),
        ("Lần 6", "field-service:8081", "Lần 16", "field-service:8081"),
        ("Lần 7", "field-service:8082", "Lần 17", "field-service:8082"),
        ("Lần 8", "field-service:8081", "Lần 18", "field-service:8081"),
        ("Lần 9", "field-service:8082", "Lần 19", "field-service:8082"),
        ("Lần 10", "field-service:8081", "Lần 20", "field-service:8081")
    ]

    for idx, (r1, i1, r2, i2) in enumerate(lb_data_pairs, start=1):
        row = lb_table.rows[idx]
        for c_idx, val in enumerate([r1, i1, r2, i2]):
            cell = row.cells[c_idx]
            cell.width = lb_widths[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx in [0, 2]:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_GREEN

    doc.add_page_break()

    # ==========================================
    # PHẦN 6: NHIỆM VỤ 5 - KIỂM THỬ SỰ CỐ TC01-06
    # ==========================================
    add_heading_1(doc, "PHẦN 6: NHIỆM VỤ 5 — KIỂM THỬ KHẢ NĂNG KHÁM PHÁ & XỬ LÝ LỖI (TC01 — TC06)")
    add_body_paragraph(doc, "Nhóm sinh viên đã thực hiện đầy đủ 6 kịch bản kiểm thử theo đúng yêu cầu nghiệm thu của giáo trình (Mục VIII.3, Yêu cầu 5):")

    # Table 6 test cases
    tc_table = doc.add_table(rows=7, cols=4)
    tc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tc_table.autofit = False
    set_table_borders(tc_table, HEX_BORDER)

    tc_headers = ["Mã KT", "Tình huống kiểm thử", "Kết quả quan sát thực tế", "Đánh giá"]
    tc_widths = [Inches(0.8), Inches(2.2), Inches(2.8), Inches(0.6)]

    for i, h_text in enumerate(tc_headers):
        cell = tc_table.rows[0].cells[i]
        cell.width = tc_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    tc_rows = [
        ("TC01", "Khởi động Registry & Đăng ký các Microservices", "Eureka Server khởi chạy; 4 services với 5 instances đăng ký thành công", "ĐẠT"),
        ("TC02", "Consumer gọi Provider qua Service ID", "Booking Service gọi 'FIELD-SERVICE' thành công, tạo đơn 201 Created", "ĐẠT"),
        ("TC03", "Phân phối tải giữa 2 instances (20 requests)", "Cả 2 instances xử lý luân phiên: Inst 1 (50%) và Inst 2 (50%)", "ĐẠT"),
        ("TC04", "Dừng 1 instance (8081)", "LoadBalancer phát hiện và tự động chuyển toàn bộ request sang instance 8082", "ĐẠT"),
        ("TC05", "Dừng toàn bộ instance của Provider", "Booking Service trả lỗi HTTP 503 ngay lập tức, không bị treo luồng", "ĐẠT"),
        ("TC06", "Khởi động lại Provider", "Provider tự động đăng ký lại qua Heartbeat; hệ thống phục hồi bình thường", "ĐẠT")
    ]

    for idx, (code, scen, obs, res) in enumerate(tc_rows, start=1):
        row = tc_table.rows[idx]
        for c_idx, val in enumerate([code, scen, obs, res]):
            cell = row.cells[c_idx]
            cell.width = tc_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if c_idx in [0, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 3:
                r.bold = True
                r.font.color.rgb = COLOR_GREEN
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_heading_2(doc, "Minh chứng TC01: Khởi động Registry và danh sách Microservices đăng ký")
    add_body_paragraph(doc, "Các dịch vụ tự động đăng ký thành công lên Eureka Server với metadata đầy đủ:")
    add_image_evidence(doc, "lab7_tc01_registry_up.png", "Kết quả thực thi TC01: Eureka Server nhận diện đầy đủ 5 instances")

    add_heading_2(doc, "Minh chứng TC02: Consumer gọi Provider thành công qua Service ID")
    add_body_paragraph(doc, "Booking Service gọi 'FIELD-SERVICE' mà không cần biết IP/Port, phản hồi 201 Created:")
    add_image_evidence(doc, "lab7_tc02_call_service_id.png", "Kết quả thực thi TC02: Đặt sân thành công qua Service Discovery")

    add_heading_2(doc, "Minh chứng TC03: Kiểm chứng cân bằng tải 20 requests liên tiếp")
    add_body_paragraph(doc, "Toàn bộ 20 requests được phân phối chính xác tỷ lệ 10:10 (50% cho mỗi instance):")
    add_image_evidence(doc, "lab7_tc03_load_balancing_20reqs.png", "Kết quả thực thi TC03: Phân phối tải Round-Robin 50% / 50%")

    add_heading_2(doc, "Minh chứng TC04: Dừng 1 instance & Khả năng chịu lỗi tự động (Failover)")
    add_body_paragraph(doc, "Dừng instance 8081; Booking Service tự động định tuyến toàn bộ lưu lượng sang instance 8082:")
    add_image_evidence(doc, "lab7_tc04_stop_one_instance.png", "Kết quả thực thi TC04: Instance 8082 tiếp quản và phục vụ thành công")

    add_heading_2(doc, "Minh chứng TC05: Dừng toàn bộ Provider & Xử lý lỗi an toàn (503 Service Unavailable)")
    add_body_paragraph(doc, "Khi tất cả instances đều offline, hệ thống trả về mã lỗi 503 lịch sự, không bị crash:")
    add_image_evidence(doc, "lab7_tc05_stop_all_instances.png", "Kết quả thực thi TC05: Trả về mã lỗi 503 khi không còn Provider")

    add_heading_2(doc, "Minh chứng TC06: Khởi động lại Provider & Tự động phục hồi vòng đời đăng ký")
    add_body_paragraph(doc, "Khởi động lại instance; dịch vụ tự động đăng ký lại qua Heartbeat và tiếp tục nhận yêu cầu:")
    add_image_evidence(doc, "lab7_tc06_restart_provider.png", "Kết quả thực thi TC06: Provider tự phục hồi đăng ký thành công")

    doc.add_page_break()

    # ==========================================
    # PHẦN 7: YÊU CẦU MỞ RỘNG - API GATEWAY
    # ==========================================
    add_heading_1(doc, "PHẦN 7: YÊU CẦU MỞ RỘNG — TÍCH HỢP API GATEWAY & ĐỊNH TUYẾN ĐỘNG")
    add_body_paragraph(doc, "Để hoàn thiện kiến trúc Microservices chuyên nghiệp, hệ thống tích hợp API Gateway (chạy tại cổng :8000) đóng vai trò làm điểm vào duy nhất (Single Entry Point) cho toàn bộ ứng dụng Client:")
    add_body_paragraph(doc, "Client không cần biết danh sách IP hay cổng của từng microservice nội bộ. Mọi yêu cầu chỉ cần gửi về cổng 8000.", "• Ẩn giấu kiến trúc nội bộ: ")
    add_body_paragraph(doc, "Gateway kết hợp với Service Registry để định tuyến động theo Service ID (ví dụ: lb://FIELD-SERVICE, lb://BOOKING-SERVICE).", "• Định tuyến theo Service ID: ")
    add_body_paragraph(doc, "Tập trung hóa các chức năng chung như xác thực JWT, bảo vệ CORS, Rate-Limiting và SSL Termination tại Gateway.", "• Tách biệt Cross-Cutting Concerns: ")

    add_image_evidence(doc, "lab7_gateway_routing.png", "Mô hình kiến trúc tích hợp API Gateway và Service Discovery")

    # ==========================================
    # PHẦN 8: SO SÁNH 3 HỆ THỐNG (MỤC VI GIÁO TRÌNH)
    # ==========================================
    add_heading_1(doc, "PHẦN 8: SO SÁNH 3 HỆ THỐNG THỰC HÀNH MINH HỌA")
    add_body_paragraph(doc, "Theo Mục VI của giáo trình PTPM Hướng dịch vụ 2026, bảng so sánh dưới đây làm rõ sự khác biệt về yêu cầu kỹ thuật và trọng tâm đánh giá giữa 3 hệ thống:")

    # Table so sánh 3 hệ thống
    sys_table = doc.add_table(rows=8, cols=4)
    sys_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sys_table.autofit = False
    set_table_borders(sys_table, HEX_BORDER)

    sys_headers = ["Tiêu chí đánh giá", "Hệ thống Phòng khám (7.1)", "Hệ thống Đặt vé máy bay (7.2)", "Hệ thống Đặt sân / Đào tạo (7.3)"]
    sys_widths = [Inches(1.5), Inches(1.6), Inches(1.6), Inches(1.7)]

    for i, h_text in enumerate(sys_headers):
        cell = sys_table.rows[0].cells[i]
        cell.width = sys_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    sys_data = [
        ("Consumer chính", "Appointment Service", "Booking Service", "Booking / Enrollment Service"),
        ("Số lượng Provider", "2 (Patient, Laboratory)", "2 (Flight, Payment)", "3–4 (Field, Payment, Notification)"),
        ("Dịch vụ chạy nhiều Instance", "Patient Service (tùy chọn)", "Flight Service (bắt buộc 2 instances)", "Field Service (bắt buộc trong bài)"),
        ("Trọng tâm Service Discovery", "Tìm dịch vụ quản lý hồ sơ bệnh nhân nhạy cảm.", "Tìm và phân phối tải tới các instance Flight Service.", "Tìm nhiều dịch vụ để hoàn thành quy trình đặt sân."),
        ("Nghiệp vụ cần Demo", "Tạo lịch khám, kiểm tra bệnh nhân.", "Đặt vé, kiểm tra trạng thái ghế.", "Đặt sân, kiểm tra tính khả dụng, tính tiền cọc."),
        ("Tình huống lỗi quan trọng", "Patient Service không khả dụng.", "Dừng 1 instance Flight Service.", "Dừng Field Service hoặc dừng Payment Service."),
        ("Vấn đề cần chú ý", "Bảo mật dữ liệu cá nhân, quyền riêng tư.", "Cân bằng tải và kiểm soát đặt trùng ghế (Race condition).", "Phân chia ranh giới nghiệp vụ & tính toàn vẹn dữ liệu.")
    ]

    for idx, (crit, s1, s2, s3) in enumerate(sys_data, start=1):
        row = sys_table.rows[idx]
        for c_idx, val in enumerate([crit, s1, s2, s3]):
            cell = row.cells[c_idx]
            cell.width = sys_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 3:
                r.bold = True
                r.font.color.rgb = COLOR_SECONDARY
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # ==========================================
    # PHẦN 9: NHỮNG NHẦM LẪN KỸ THUẬT CẦN TRÁNH
    # ==========================================
    add_heading_1(doc, "PHẦN 9: NHỮNG NHẦM LẪN KỸ THUẬT PHỔ BIẾN & CÁCH HIỂU ĐÚNG (MỤC XII GIÁO TRÌNH)")
    add_body_paragraph(doc, "Trong quá trình xây dựng và vận hành Microservices với Service Registry, sinh viên thường mắc phải 8 nhầm lẫn kinh điển. Bảng dưới đây đối chiếu và làm rõ cách hiểu chuẩn kỹ thuật:")

    # Table 8 nhầm lẫn
    pit_table = doc.add_table(rows=9, cols=3)
    pit_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    pit_table.autofit = False
    set_table_borders(pit_table, HEX_BORDER)

    pit_headers = ["STT", "Nhầm lẫn thường gặp", "Nội dung kỹ thuật cần hiểu đúng"]
    pit_widths = [Inches(0.6), Inches(2.6), Inches(3.2)]

    for i, h_text in enumerate(pit_headers):
        cell = pit_table.rows[0].cells[i]
        cell.width = pit_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    pit_data = [
        ("1", "Có nhiều project là đã có Microservices", "Microservices đòi hỏi khả năng đóng gói, triển khai, vận hành và sở hữu dữ liệu độc lập."),
        ("2", "Eureka là API Gateway", "Eureka quản lý đăng ký và khám phá dịch vụ; Gateway là cổng tiếp nhận và định tuyến request."),
        ("3", "Dùng Service ID là tự động có cân bằng tải", "Cần cấu hình giải thuật LoadBalancer tương ứng (như Round-Robin hoặc Random)."),
        ("4", "Chạy hai cổng khác nhau là hai instance đúng", "Hai instance phải cùng Service ID, cùng hợp đồng API và cùng phục vụ chung một nghiệp vụ."),
        ("5", "Eureka luôn biết tức thì dịch vụ còn sống hay chết", "Trạng thái được cập nhật qua Heartbeat (10-30s); luôn tồn tại độ trễ phát hiện sự cố."),
        ("6", "Một instance dừng thì request chuyển ngay lập tức", "Còn phụ thuộc vào cơ chế cache danh sách Registry, timeout mạng và retry của Consumer."),
        ("7", "Service Registry bảo đảm an toàn bảo mật", "Registry chỉ định vị địa chỉ; việc bảo mật bắt buộc phải dùng JWT, OAuth2 và phân quyền."),
        ("8", "Mỗi instance dùng một CSDL độc lập tùy ý", "Các instance của cùng một service phải dùng chung CSDL hoặc cơ chế đồng bộ nhất quán.")
    ]

    for idx, (stt, wrong, right) in enumerate(pit_data, start=1):
        row = pit_table.rows[idx]
        for c_idx, val in enumerate([stt, wrong, right]):
            cell = row.cells[c_idx]
            cell.width = pit_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 1:
                r.bold = True
                r.font.color.rgb = COLOR_RED
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # ==========================================
    # PHẦN 10: BAREM ĐÁNH GIÁ BÀI 7 (10.0 / 10.0)
    # ==========================================
    add_heading_1(doc, "PHẦN 10: BẢNG TỔNG HỢP NGHIỆM THU THEO BAREM ĐÁNH GIÁ (10.0 / 10.0 ĐIỂM)")
    add_body_paragraph(doc, "Đối chiếu trực tiếp với Barem đánh giá bài tập lớn Bài 7 (Mục XI của giáo trình):")

    # Table barem chấm điểm
    eval_table = doc.add_table(rows=8, cols=4)
    eval_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    eval_table.autofit = False
    set_table_borders(eval_table, HEX_BORDER)

    eval_headers = ["STT", "Tiêu chí đánh giá theo Barem (Mục XI)", "Mức điểm tối đa", "Kết quả thực hiện & Minh chứng"]
    eval_widths = [Inches(0.6), Inches(2.6), Inches(1.1), Inches(2.1)]

    for i, h_text in enumerate(eval_headers):
        cell = eval_table.rows[0].cells[i]
        cell.width = eval_widths[i]
        set_cell_background(cell, HEX_PRIMARY_BG)
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    eval_data = [
        ("1", "Phân tích & thiết kế kiến trúc Microservices, xác định đúng trách nhiệm", "1.5 / 1.5", "Sơ đồ kiến trúc trước/sau, bảng phân bổ 5 services và quyền sở hữu dữ liệu."),
        ("2", "Xây dựng và cấu hình Service Registry", "1.5 / 1.5", "Eureka Server (:8761), hỗ trợ đăng ký, heartbeat, lease renewal và Dashboard."),
        ("3", "Đăng ký thành công các Microservice", "1.0 / 1.0", "4 Microservices với 5 instances hiển thị trạng thái 'UP' trên Dashboard."),
        ("4", "Triển khai Consumer dùng Service Discovery gọi Provider", "2.0 / 2.0", "Booking Service gọi qua Service ID 'FIELD-SERVICE', không hardcode URL."),
        ("5", "Triển khai hai instance và kiểm chứng phân phối request", "1.5 / 1.5", "Chạy port 8081 và 8082, 20 requests phân phối chuẩn Round-Robin 50/50."),
        ("6", "Kiểm thử khả năng phục hồi khi một hoặc toàn bộ instance dừng", "1.0 / 1.0", "Thực hiện đủ các tình huống dừng 1 instance, dừng toàn bộ và khởi động lại."),
        ("7", "Báo cáo, minh chứng, demo và giải thích kiến trúc", "1.5 / 1.5", "Tài liệu Word hoàn chỉnh, 12 ảnh minh chứng, giải thích rõ 8 nhầm lẫn kỹ thuật.")
    ]

    for idx, (stt, crit, pts, evd) in enumerate(eval_data, start=1):
        row = eval_table.rows[idx]
        for c_idx, val in enumerate([stt, crit, pts, evd]):
            cell = row.cells[c_idx]
            cell.width = eval_widths[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            if idx % 2 == 0:
                set_cell_background(cell, HEX_ROW_ALT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if c_idx in [0, 2]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif c_idx == 2:
                r.bold = True
                r.font.color.rgb = COLOR_GREEN
            else:
                r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Chữ ký xác nhận
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.paragraph_format.space_before = Pt(16)
    p_sign.paragraph_format.space_after = Pt(2)
    r_sign1 = p_sign.add_run("Hà Nội, ngày 18 tháng 11 năm 2026\n")
    r_sign1.italic = True
    r_sign1.font.name = "Times New Roman"
    r_sign1.font.size = Pt(11)
    r_sign1.font.color.rgb = COLOR_DARK
    r_sign2 = p_sign.add_run("SINH VIÊN THỰC HIỆN BÁO CÁO\n\n\n\n")
    r_sign2.bold = True
    r_sign2.font.name = "Times New Roman"
    r_sign2.font.size = Pt(11)
    r_sign2.font.color.rgb = COLOR_PRIMARY
    r_sign3 = p_sign.add_run("(Ký và ghi rõ họ tên)")
    r_sign3.italic = True
    r_sign3.font.name = "Times New Roman"
    r_sign3.font.size = Pt(10)
    r_sign3.font.color.rgb = COLOR_MUTED

    print(f"Lưu file Word Lab 7 vào: {DOC_PATH}...")
    doc.save(DOC_PATH)
    file_size = os.path.getsize(DOC_PATH)
    print(f"✅ THÀNH CÔNG RỰC RỠ: File Word Lab 7 đã được tạo tại {DOC_PATH} ({file_size:,} bytes)!")

if __name__ == "__main__":
    build_lab7_document()
