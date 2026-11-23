import os
import subprocess
from PIL import Image

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0b1120;
    padding: 16px;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    display: inline-block;
  }
  .vscode-window {
    width: 920px;
    background: #1e1e1e;
    border-radius: 9px;
    overflow: hidden;
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.12);
    border: 1px solid #333333;
  }
  /* Titlebar */
  .titlebar {
    height: 36px;
    background: #181818;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    border-bottom: 1px solid #252525;
    user-select: none;
  }
  .titlebar-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .window-dots {
    display: flex;
    gap: 7px;
  }
  .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  .dot-close { background: #ff5f56; }
  .dot-min { background: #ffbd2e; }
  .dot-max { background: #27c93f; }
  .title-text {
    color: #cccccc;
    font-size: 12.5px;
    font-weight: 500;
    margin-left: 10px;
    letter-spacing: 0.2px;
  }
  /* Tabs */
  .tabs-bar {
    height: 36px;
    background: #141414;
    display: flex;
    align-items: flex-end;
    border-bottom: 1px solid #1e1e1e;
  }
  .tab {
    height: 36px;
    background: #1e1e1e;
    color: #ffffff;
    font-size: 12.5px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 8px;
    border-top: 2px solid #007acc;
    border-right: 1px solid #252525;
  }
  .tab-icon {
    font-weight: 800;
    font-size: 10px;
    color: #3178c6;
    background: rgba(49, 120, 198, 0.18);
    padding: 2px 4px;
    border-radius: 3px;
  }
  .tab-py {
    color: #ffd43b;
    background: rgba(255, 212, 59, 0.18);
  }
  .tab-inactive {
    height: 33px;
    background: #181818;
    color: #888888;
    border-top: 2px solid transparent;
  }
  /* Breadcrumbs */
  .breadcrumbs {
    height: 25px;
    background: #1e1e1e;
    color: #8c8c8c;
    font-size: 11.5px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid #252525;
    gap: 6px;
  }
  .crumb-sep { color: #555555; }
  .crumb-active { color: #cccccc; font-weight: 500; }
  /* Editor */
  .editor {
    display: flex;
    background: #1e1e1e;
    padding: 14px 0;
    font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
    font-size: 12.8px;
    line-height: 1.55;
  }
  .gutter {
    width: 48px;
    text-align: right;
    padding-right: 14px;
    color: #6e7681;
    user-select: none;
    border-right: 1px solid #2d2d2d;
  }
  .gutter div { height: 20px; }
  .code {
    padding-left: 16px;
    padding-right: 20px;
    flex: 1;
    overflow: hidden;
    color: #d4d4d4;
  }
  .code div { height: 20px; white-space: pre; }
  /* Statusbar */
  .statusbar {
    height: 24px;
    background: #007acc;
    color: #ffffff;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    font-weight: 500;
  }
  .status-left, .status-right {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  /* Syntax Highlighting */
  .kw { color: #569cd6; font-weight: 600; }
  .kw-ctrl { color: #c586c0; font-weight: 600; }
  .dec { color: #dcdcaa; }
  .type { color: #4ec9b0; }
  .fn { color: #dcdcaa; }
  .str { color: #ce9178; }
  .num { color: #b5cea8; }
  .cm { color: #6a9955; font-style: italic; }
  .prop { color: #9cdcfe; }
</style>
</head>
<body>
<div class="vscode-window">
  <div class="titlebar">
    <div class="titlebar-left">
      <div class="window-dots">
        <div class="dot dot-close"></div>
        <div class="dot dot-min"></div>
        <div class="dot dot-max"></div>
      </div>
      <div class="title-text">__TITLE_TEXT__</div>
    </div>
    <div style="color: #888888; font-size: 11px;">Visual Studio Code — Anta Backend Project</div>
  </div>
  <div class="tabs-bar">
    <div class="tab">
      <span class="tab-icon __ICON_CLASS__">__ICON_TEXT__</span>
      <span>__TAB_NAME__</span>
    </div>
    <div class="tab tab-inactive">
      <span style="font-size: 11px; color: #666;">service.ts</span>
    </div>
    <div class="tab tab-inactive">
      <span style="font-size: 11px; color: #666;">dto.ts</span>
    </div>
  </div>
  <div class="breadcrumbs">
    <span>anta-backend</span>
    <span class="crumb-sep">&gt;</span>
    <span>__FOLDER_PATH__</span>
    <span class="crumb-sep">&gt;</span>
    <span class="crumb-active">__TAB_NAME__</span>
    <span class="crumb-sep">&gt;</span>
    <span class="crumb-active">__ACTIVE_SYMBOL__</span>
  </div>
  <div class="editor">
    <div class="gutter">
      __LINE_NUMBERS__
    </div>
    <div class="code">
      __CODE_HTML__
    </div>
  </div>
  <div class="statusbar">
    <div class="status-left">
      <span>&#x2942; main*</span>
      <span>&#x2713; 0 &#x26A0; 0</span>
    </div>
    <div class="status-right">
      <span>Ln __CURRENT_LINE__, Col 1</span>
      <span>Spaces: 2</span>
      <span>UTF-8</span>
      <span>__LANG_NAME__</span>
    </div>
  </div>
</div>
</body>
</html>
"""

def generate_vscode_shot(html_path, output_png_path, title_text, tab_name, folder_path, symbol, lang_name, icon_text, icon_class, start_line, lines_code):
    line_nums = "\n".join([f"<div>{i}</div>" for i in range(start_line, start_line + len(lines_code))])
    code_html = "\n".join([f"<div>{line}</div>" for line in lines_code])
    
    content = HTML_TEMPLATE.replace("__TITLE_TEXT__", title_text)
    content = content.replace("__TAB_NAME__", tab_name)
    content = content.replace("__FOLDER_PATH__", folder_path)
    content = content.replace("__ACTIVE_SYMBOL__", symbol)
    content = content.replace("__LANG_NAME__", lang_name)
    content = content.replace("__ICON_TEXT__", icon_text)
    content = content.replace("__ICON_CLASS__", icon_class)
    content = content.replace("__LINE_NUMBERS__", line_nums)
    content = content.replace("__CODE_HTML__", code_html)
    content = content.replace("__CURRENT_LINE__", str(start_line + 4))

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    temp_shot = output_png_path + ".temp.png"
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_exe,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--screenshot={temp_shot}",
        "--window-size=960,720",
        f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    ]
    subprocess.run(cmd, check=True)
    
    # Crop with Pillow to exact window
    im = Image.open(temp_shot)
    # The vscode window starts at x=16, y=16 and width=920
    # Let's crop tight
    # We find bbox where pixels are not the dark background #0b1120
    # Or simply crop (16, 16, 936, content_height + 16)
    content_height = 36 + 36 + 25 + 28 + (len(lines_code) * 20) + 24
    crop_box = (16, 16, 936, 16 + content_height)
    cropped = im.crop(crop_box)
    cropped.save(output_png_path)
    if os.path.exists(temp_shot):
        os.remove(temp_shot)
    print(f"Generated: {output_png_path} (size: {cropped.size})")

def main():
    out_dir = r"D:\hdv\backend\docs\diagrams"
    os.makedirs(out_dir, exist_ok=True)

    # 1. Booking Controller
    lines_controller = [
        '<span class="kw">const</span> <span class="prop">keyHeader</span> = { <span class="prop">name</span>: <span class="str">\'Idempotency-Key\'</span>, <span class="prop">required</span>: <span class="kw">true</span>, <span class="prop">description</span>: <span class="str">\'8-128 chars\'</span> };',
        '',
        '<span class="dec">@ApiTags</span>(<span class="str">\'booking\'</span>) <span class="dec">@Controller</span>()',
        '<span class="kw">export class</span> <span class="type">BookingController</span> {',
        '  <span class="kw">constructor</span>(<span class="kw">private readonly</span> <span class="prop">booking</span>: <span class="type">BookingService</span>) {}',
        '',
        '  <span class="cm">// 1. Client gửi yêu cầu giữ chỗ có TTL 5 phút</span>',
        '  <span class="dec">@ApiBearerAuth</span>() <span class="dec">@Post</span>(<span class="str">\'booking-holds\'</span>) <span class="dec">@ApiHeader</span>(<span class="prop">keyHeader</span>)',
        '  <span class="fn">hold</span>(<span class="dec">@CurrentUser</span>() <span class="prop">user</span>: <span class="type">Principal</span>, <span class="dec">@Body</span>() <span class="prop">dto</span>: <span class="type">SlotDto</span>, <span class="dec">@Headers</span>(<span class="str">\'idempotency-key\'</span>) <span class="prop">key</span>?: <span class="type">string</span>) {',
        '    <span class="kw-ctrl">return</span> <span class="kw">this</span>.<span class="prop">booking</span>.<span class="fn">hold</span>(<span class="prop">user</span>.<span class="prop">userId</span>, <span class="prop">dto</span>, <span class="prop">key</span>);',
        '  }',
        '',
        '  <span class="cm">// 2. Chuyển đổi HoldId thành Đơn đặt sân chính thức</span>',
        '  <span class="dec">@ApiBearerAuth</span>() <span class="dec">@Post</span>(<span class="str">\'bookings\'</span>) <span class="dec">@ApiHeader</span>(<span class="prop">keyHeader</span>)',
        '  <span class="fn">create</span>(<span class="dec">@CurrentUser</span>() <span class="prop">user</span>: <span class="type">Principal</span>, <span class="dec">@Body</span>() <span class="prop">dto</span>: <span class="type">BookingDto</span>,',
        '         <span class="dec">@Req</span>() <span class="prop">req</span>: <span class="type">AuthRequest</span>, <span class="dec">@Headers</span>(<span class="str">\'idempotency-key\'</span>) <span class="prop">key</span>?: <span class="type">string</span>) {',
        '    <span class="kw-ctrl">return</span> <span class="kw">this</span>.<span class="prop">booking</span>.<span class="fn">create</span>(<span class="prop">user</span>.<span class="prop">userId</span>, <span class="prop">dto</span>.<span class="prop">holdId</span>, <span class="prop">key</span>, <span class="prop">req</span>.<span class="prop">requestId</span>);',
        '  }',
        '}'
    ]
    generate_vscode_shot(
        os.path.join(out_dir, "shot_controller.html"),
        os.path.join(out_dir, "vscode_booking_controller.png"),
        "controller.ts - modules/booking - Anta Backend",
        "controller.ts",
        "modules > booking",
        "BookingController > create",
        "TypeScript",
        "TS",
        "",
        7,
        lines_controller
    )

    # 2. Booking Service (Inter-service call)
    lines_booking_service = [
        '<span class="dec">@Injectable</span>()',
        '<span class="kw">export class</span> <span class="type">BookingService</span> {',
        '  <span class="kw">constructor</span>(',
        '    <span class="kw">private readonly</span> <span class="prop">db</span>: <span class="type">Database</span>,',
        '    <span class="kw">private readonly</span> <span class="prop">catalog</span>: <span class="type">CatalogService</span>, <span class="cm">// Inject CatalogService (Provider)</span>',
        '    <span class="kw">private readonly</span> <span class="prop">idem</span>: <span class="type">Idempotency</span>,',
        '    <span class="kw">private readonly</span> <span class="prop">refunds</span>: <span class="type">RefundService</span>',
        '  ) {}',
        '',
        '  <span class="kw">async</span> <span class="fn">quote</span>(<span class="prop">dto</span>: <span class="type">SlotDto</span>, <span class="prop">tx</span>: <span class="type">DbClient</span> = <span class="kw">this</span>.<span class="prop">db</span>.<span class="prop">pool</span>) {',
        '    <span class="kw">const</span> <span class="prop">slot</span> = <span class="fn">validateSlot</span>(<span class="prop">dto</span>.<span class="prop">startsAt</span>, <span class="prop">dto</span>.<span class="prop">endsAt</span>);',
        '    <span class="cm">// GỌI SANG CATALOG SERVICE XÁC THỰC SÂN & LẤY GIÁ THỜI GIAN THỰC</span>',
        '    <span class="kw">const</span> <span class="prop">yard</span> = <span class="kw">await</span> <span class="kw">this</span>.<span class="prop">catalog</span>.<span class="fn">yard</span>(<span class="prop">tx</span>, <span class="prop">dto</span>.<span class="prop">yardId</span>);',
        '',
        '    <span class="cm">// Kiểm tra giờ mở cửa của chi nhánh theo múi giờ</span>',
        '    <span class="kw">const</span> <span class="prop">open</span> = (<span class="kw">await</span> <span class="prop">tx</span>.<span class="fn">query</span>(<span class="str">`SELECT ...`</span>, [<span class="prop">slot</span>.<span class="prop">start</span>, <span class="prop">slot</span>.<span class="prop">end</span>, <span class="prop">yard</span>.<span class="prop">timezone</span>])).<span class="prop">rows</span>[<span class="num">0</span>].<span class="prop">valid</span>;',
        '    <span class="fn">invariant</span>(<span class="prop">open</span>, <span class="str">\'OUTSIDE_OPENING_HOURS\'</span>, <span class="str">\'Slot is outside branch opening hours\'</span>, <span class="num">400</span>);',
        '    <span class="kw-ctrl">return</span> { <span class="prop">subtotal</span>: <span class="prop">yard</span>.<span class="prop">hourly_price</span> * <span class="prop">slot</span>.<span class="prop">hours</span>, <span class="prop">total</span>: <span class="prop">yard</span>.<span class="prop">hourly_price</span> * <span class="prop">slot</span>.<span class="prop">hours</span>, <span class="prop">currency</span>: <span class="prop">yard</span>.<span class="prop">currency</span> };',
        '  }',
        '}'
    ]
    generate_vscode_shot(
        os.path.join(out_dir, "shot_booking_service.html"),
        os.path.join(out_dir, "vscode_booking_service.png"),
        "service.ts - modules/booking - Anta Backend",
        "service.ts",
        "modules > booking",
        "BookingService > quote",
        "TypeScript",
        "TS",
        "",
        13,
        lines_booking_service
    )

    # 3. Catalog Service (Provider + 404 Invariant)
    lines_catalog_service = [
        '<span class="dec">@Injectable</span>()',
        '<span class="kw">export class</span> <span class="type">CatalogService</span> {',
        '  <span class="kw">constructor</span>(<span class="kw">private readonly</span> <span class="prop">db</span>: <span class="type">Database</span>, <span class="kw">private readonly</span> <span class="prop">media</span>: <span class="type">MediaService</span>) {}',
        '',
        '  <span class="cm">// Cung cấp dữ liệu sân bãi & bảo vệ bằng 404 NOT_FOUND</span>',
        '  <span class="kw">async</span> <span class="fn">yard</span>(<span class="prop">tx</span>: <span class="type">DbClient</span>, <span class="prop">id</span>: <span class="type">string</span>, <span class="prop">lock</span> = <span class="kw">false</span>) {',
        '    <span class="kw">const</span> <span class="prop">yard</span> = (<span class="kw">await</span> <span class="prop">tx</span>.<span class="fn">query</span>(<span class="str">`SELECT y.*, b.timezone, b.opening_hour, b.closing_hour',
        '      FROM catalog.yards y JOIN catalog.branches b ON b.id=y.branch_id',
        '      WHERE y.id=$1 ${lock ? \'FOR UPDATE OF y\' : \'\'}`</span>, [<span class="prop">id</span>])).<span class="prop">rows</span>[<span class="num">0</span>];',
        '',
        '    <span class="cm">// NẾU SÂN KHÔNG TỒN TẠI HOẶC KHÔNG ACTIVE -> 404 NOT FOUND</span>',
        '    <span class="fn">invariant</span>(<span class="prop">yard</span>?.<span class="prop">active</span>, <span class="str">\'NOT_FOUND\'</span>, <span class="str">\'Active yard not found\'</span>, <span class="num">404</span>);',
        '    <span class="kw-ctrl">return</span> <span class="prop">yard</span>;',
        '  }',
        '}'
    ]
    generate_vscode_shot(
        os.path.join(out_dir, "shot_catalog_service.html"),
        os.path.join(out_dir, "vscode_catalog_service.png"),
        "service.ts - modules/catalog - Anta Backend",
        "service.ts",
        "modules > catalog",
        "CatalogService > yard",
        "TypeScript",
        "TS",
        "",
        65,
        lines_catalog_service
    )

    # 4. Exception Filter (PostgreSQL GiST 409 & 503)
    lines_filter = [
        '<span class="dec">@Catch</span>()',
        '<span class="kw">export class</span> <span class="type">ApiExceptionFilter</span> <span class="kw">implements</span> <span class="type">ExceptionFilter</span> {',
        '  <span class="fn">catch</span>(<span class="prop">exception</span>: <span class="type">unknown</span>, <span class="prop">host</span>: <span class="type">ArgumentsHost</span>) {',
        '    <span class="kw">const</span> <span class="prop">req</span> = <span class="prop">host</span>.<span class="fn">switchToHttp</span>().<span class="fn">getRequest</span>&lt;<span class="type">AuthRequest</span>&gt;();',
        '    <span class="kw">const</span> <span class="prop">res</span> = <span class="prop">host</span>.<span class="fn">switchToHttp</span>().<span class="fn">getResponse</span>&lt;<span class="type">Response</span>&gt;();',
        '    <span class="kw">const</span> <span class="prop">pgCode</span> = (<span class="prop">exception</span> <span class="kw">as</span> { <span class="prop">code</span>?: <span class="type">string</span> })?.<span class="prop">code</span>;',
        '',
        '    <span class="kw">let</span> <span class="prop">status</span> = <span class="prop">exception</span> <span class="kw">instanceof</span> <span class="type">HttpException</span> ? <span class="prop">exception</span>.<span class="fn">getStatus</span>() : <span class="num">500</span>;',
        '    <span class="kw">let</span> <span class="prop">code</span> = <span class="prop">exception</span> <span class="kw">instanceof</span> <span class="type">ApiError</span> ? <span class="prop">exception</span>.<span class="prop">code</span> : <span class="prop">status</span> === <span class="num">404</span> ? <span class="str">\'NOT_FOUND\'</span> : <span class="str">\'INTERNAL_ERROR\'</span>;',
        '',
        '    <span class="cm">// BẮT LỖI XUNG ĐỘT KHUNG GIỜ POSTGRES GIST CONSTRAINT (23P01) -> 409 CONFLICT</span>',
        '    <span class="kw-ctrl">if</span> (<span class="prop">pgCode</span> === <span class="str">\'23P01\'</span>) {',
        '      <span class="prop">status</span> = <span class="num">409</span>; <span class="prop">code</span> = <span class="str">\'SLOT_UNAVAILABLE\'</span>; <span class="prop">message</span> = <span class="str">\'The selected slot is no longer available\'</span>;',
        '    }',
        '    <span class="prop">res</span>.<span class="fn">status</span>(<span class="prop">status</span>).<span class="fn">json</span>({ <span class="prop">data</span>: <span class="kw">null</span>, <span class="prop">meta</span>: { <span class="prop">requestId</span>: <span class="prop">req</span>.<span class="prop">requestId</span> }, <span class="prop">error</span>: { <span class="prop">code</span>, <span class="prop">message</span> } });',
        '  }',
        '}'
    ]
    generate_vscode_shot(
        os.path.join(out_dir, "shot_filter.html"),
        os.path.join(out_dir, "vscode_exception_filter.png"),
        "http.ts - packages/observability - Anta Backend",
        "http.ts",
        "packages > observability",
        "ApiExceptionFilter > catch",
        "TypeScript",
        "TS",
        "",
        26,
        lines_filter
    )

    # 5. Python FastAPI
    lines_python = [
        '<span class="prop">router</span> = <span class="fn">APIRouter</span>(<span class="prop">prefix</span>=<span class="str">"/api/v1"</span>, <span class="prop">tags</span>=[<span class="str">"catalog"</span>])',
        '',
        '<span class="dec">@router.get</span>(<span class="str">"/public/branches"</span>)',
        '<span class="kw">async def</span> <span class="fn">branches</span>(',
        '    <span class="prop">request</span>: <span class="type">Request</span>,',
        '    <span class="prop">lat</span>: <span class="type">Annotated</span>[<span class="type">float</span> | <span class="kw">None</span>, <span class="fn">Query</span>(<span class="prop">ge</span>=-<span class="num">90</span>, <span class="prop">le</span>=<span class="num">90</span>)] = <span class="kw">None</span>,',
        '    <span class="prop">lng</span>: <span class="type">Annotated</span>[<span class="type">float</span> | <span class="kw">None</span>, <span class="fn">Query</span>(<span class="prop">ge</span>=-<span class="num">180</span>, <span class="prop">le</span>=<span class="num">180</span>)] = <span class="kw">None</span>,',
        '    <span class="prop">radius</span>: <span class="type">Annotated</span>[<span class="type">int</span> | <span class="kw">None</span>, <span class="fn">Query</span>(<span class="prop">ge</span>=<span class="num">100</span>)] = <span class="kw">None</span>,',
        '    <span class="prop">conn</span>: <span class="type">AsyncConnection</span> = <span class="fn">Depends</span>(<span class="prop">connection</span>)',
        '):',
        '    <span class="fn">require</span>((<span class="prop">lat</span> <span class="kw">is None</span>) == (<span class="prop">lng</span> <span class="kw">is None</span>), <span class="str">"VALIDATION_FAILED"</span>, <span class="str">"lat and lng required together"</span>, <span class="num">400</span>)',
        '    <span class="cm"># TÍNH TOÁN KHOẢNG CÁCH POSTGIS KHÔNG GIAN BẤT ĐỒNG BỘ</span>',
        '    <span class="prop">point</span> = <span class="str">"ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography"</span>',
        '    <span class="prop">cur</span> = <span class="kw">await</span> <span class="prop">conn</span>.<span class="fn">execute</span>(<span class="str">f"""SELECT {CARD}, ST_Distance(b.location,{point}) AS distance_meters</span>',
        '        <span class="str">FROM catalog.branches b WHERE ST_DWithin(b.location,{point},%s)"""</span>, (<span class="prop">lng</span>, <span class="prop">lat</span>, <span class="prop">lng</span>, <span class="prop">lat</span>, <span class="prop">radius</span>))',
        '    <span class="kw-ctrl">return</span> <span class="fn">envelope</span>(<span class="prop">request</span>, <span class="kw">await</span> <span class="prop">cur</span>.<span class="fn">fetchall</span>())'
    ]
    generate_vscode_shot(
        os.path.join(out_dir, "shot_python.html"),
        os.path.join(out_dir, "vscode_python_fastapi.png"),
        "catalog.py - python_backend/anta_api - Anta Backend",
        "catalog.py",
        "python_backend > anta_api",
        "branches()",
        "Python",
        "PY",
        "tab-py",
        62,
        lines_python
    )

if __name__ == "__main__":
    main()
