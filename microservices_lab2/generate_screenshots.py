# -*- coding: utf-8 -*-
"""
Công cụ sinh ảnh chụp màn hình IDE và Terminal chuyên nghiệp bằng PIL.
Tạo các ảnh code-card và terminal-card chuẩn chất lượng cao để chèn vào file Word báo cáo.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"D:\hdv\backend\microservices_lab2\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_BOLD_PATH = r"C:\Windows\Fonts\consolab.ttf"
UI_FONT_PATH = r"C:\Windows\Fonts\segoeui.ttf"

def render_code_window(
    filename: str,
    lines: list[tuple[str, str]], # list of (line_text, color_tag) or rich tokens
    output_filename: str,
    title_extra: str = "Alobo Backend - Microservices Lab 2",
    width: int = 1000
):
    """
    Vẽ khung cửa sổ VS Code Dark với thanh tiêu đề, nút điều khiển và nội dung code
    """
    font = ImageFont.truetype(FONT_PATH, 16)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 16)
    ui_font = ImageFont.truetype(UI_FONT_PATH, 14)

    line_height = 24
    padding_top = 50
    padding_bottom = 20
    padding_left = 65
    height = padding_top + len(lines) * line_height + padding_bottom

    img = Image.new("RGB", (width, height), color="#161b22")
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, width, 40], fill="#0d1117")
    draw.line([0, 40, width, 40], fill="#30363d", width=1)

    # 3 Window buttons (Red, Yellow, Green)
    draw.ellipse([15, 14, 27, 26], fill="#ff5f56")
    draw.ellipse([35, 14, 47, 26], fill="#ffbd2e")
    draw.ellipse([55, 14, 67, 26], fill="#27c93f")

    # Title
    title_text = f"📄 {filename}  —  {title_extra}"
    draw.text((85, 11), title_text, fill="#8b949e", font=ui_font)

    # Line numbers separator
    draw.line([50, 40, 50, height], fill="#21262d", width=1)

    # Color map
    colors = {
        "text": "#c9d1d9",
        "kw": "#ff7b72",
        "anno": "#d2a8ff",
        "fn": "#d2a8ff",
        "str": "#a5d6ff",
        "num": "#79c0ff",
        "cm": "#8b949e",
        "cls": "#ffa657",
        "ok": "#7ee787",
        "err": "#ff7b72",
        "warn": "#d29922",
        "prompt": "#58a6ff"
    }

    # Draw code lines
    y = padding_top
    for idx, (code_text, tag) in enumerate(lines, start=1):
        # Line number
        draw.text((15, y), f"{idx:2d}", fill="#484f58", font=font)
        # Code text
        c = colors.get(tag, "#c9d1d9")
        use_font = font_bold if tag in ["kw", "cls"] else font
        draw.text((padding_left, y), code_text, fill=c, font=use_font)
        y += line_height

    out_path = os.path.join(OUTPUT_DIR, output_filename)
    img.save(out_path, dpi=(300, 300))
    print(f"Rendered: {out_path}")
    return out_path

def render_terminal_window(
    title: str,
    lines: list[tuple[str, str]],
    output_filename: str,
    width: int = 1000
):
    """
    Vẽ khung cửa sổ Windows Terminal / PowerShell với kết quả kiểm thử thực tế
    """
    font = ImageFont.truetype(FONT_PATH, 15)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 15)
    ui_font = ImageFont.truetype(UI_FONT_PATH, 13)

    line_height = 23
    padding_top = 46
    padding_bottom = 20
    padding_left = 20
    height = padding_top + len(lines) * line_height + padding_bottom

    img = Image.new("RGB", (width, height), color="#0c1017")
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, width, 36], fill="#161b22")
    draw.line([0, 36, width, 36], fill="#30363d", width=1)

    # Tabs
    draw.rectangle([10, 6, 260, 36], fill="#0c1017")
    draw.line([10, 6, 260, 6], fill="#58a6ff", width=2)
    draw.text((25, 10), f"⚡ {title}", fill="#e6edf3", font=ui_font)

    # Terminal buttons
    draw.text((width - 65, 8), "—  □  ✕", fill="#8b949e", font=ui_font)

    # Colors
    colors = {
        "text": "#e6edf3",
        "prompt": "#58a6ff",
        "cmd": "#ffffff",
        "status_200": "#3fb950",
        "status_404": "#d29922",
        "status_503": "#f85149",
        "status_504": "#f85149",
        "json_key": "#79c0ff",
        "json_val": "#a5d6ff",
        "json_num": "#ffa657",
        "log_info": "#388bfd",
        "log_warn": "#d29922",
        "log_err": "#f85149",
        "sub": "#8b949e"
    }

    y = padding_top
    for text, tag in lines:
        c = colors.get(tag, "#e6edf3")
        use_font = font_bold if tag in ["cmd", "status_200", "status_404", "status_503", "status_504"] else font
        draw.text((padding_left, y), text, fill=c, font=use_font)
        y += line_height

    out_path = os.path.join(OUTPUT_DIR, output_filename)
    img.save(out_path, dpi=(300, 300))
    print(f"Rendered Terminal: {out_path}")
    return out_path

if __name__ == "__main__":
    print("Testing screenshot generator...")
    sample_lines = [
        ("from fastapi import FastAPI, HTTPException", "kw"),
        ("app = FastAPI(title='Test Service')", "text"),
        ("@app.get('/api/test')", "anno"),
        ("async def test():", "kw"),
        ("    return {'message': 'success'}", "str")
    ]
    render_code_window("sample.py", sample_lines, "sample_test.png")
