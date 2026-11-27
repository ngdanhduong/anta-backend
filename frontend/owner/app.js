'use strict';
// Venue-owner portal (Chủ sân). All data is rendered with textContent/el(); nothing from the API is ever
// parsed as HTML. Every write goes through /api/v1/owner/* — the server re-checks branch ownership on every call.
const API = '/api/v1';
const $ = id => document.getElementById(id);
const store = { get: k => sessionStorage.getItem('owner_' + k), set: (k, v) => sessionStorage.setItem('owner_' + k, v), clear: () => ['access', 'refresh', 'tried', 'branch'].forEach(k => sessionStorage.removeItem('owner_' + k)) };

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') node.className = v;
    else if (k === 'on') for (const [name, fn] of Object.entries(v)) node.addEventListener(name, fn);
    else if (k === 'text') node.textContent = v;
    else if (v !== null && v !== undefined) node.setAttribute(k, v);
  }
  const flat = Array.isArray(children) ? children.flat(Infinity) : [children];
  for (const child of flat) if (child !== null && child !== undefined) node.append(child);
  return node;
}

function svgIcon(paths) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '16');
  svg.setAttribute('height', '16');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '2');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  for (const d of paths) {
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', d);
    svg.appendChild(p);
  }
  return svg;
}

const NAV_ICONS = {
  stats: ['M3 3v18h18', 'M18 17V9', 'M13 17V5', 'M8 17v-3'],
  schedule: ['M8 2v4', 'M16 2v4', 'M3 10h18', 'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z'],
  bookings: ['M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2', 'M9 3h6v4H9z', 'M9 12h6', 'M9 16h4'],
  cancellations: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z', 'M15 9l-6 6', 'M9 9l6 6'],
  courts: ['M3 5h18v14H3z', 'M12 5v14', 'M3 12h18'],
  'submit-branch': ['M12 5v14', 'M5 12h14', 'M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z'],
  services: ['M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z', 'M3 6h18', 'M16 10a4 4 0 0 1-8 0'],
  cashflow: ['M12 1v22', 'M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6']
};

async function call(path, method = 'GET', body, retried = false) {
  const response = await fetch(API + path, { method, body: body === undefined ? undefined : JSON.stringify(body),
    headers: { 'Content-Type': 'application/json', ...(store.get('access') ? { Authorization: 'Bearer ' + store.get('access') } : {}) } });
  if (response.status === 401 && !retried && store.get('refresh') && !path.startsWith('/public/')) {
    const refreshed = await fetch(API + '/public/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: store.get('refresh') }) });
    if (refreshed.ok) { const tokens = (await refreshed.json()).data; store.set('access', tokens.accessToken); store.set('refresh', tokens.refreshToken); return call(path, method, body, true); }
    signOut(); throw new Error('Phiên đăng nhập đã hết hạn');
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error ? `${payload.error.code}: ${payload.error.message}` : `HTTP ${response.status}`);
  return payload.data;
}
function notify(message, bad = false) {
  const box = $('notice');
  if (message && window.AntaMotion) window.AntaMotion.toast(message, bad);
  if (!message || !bad) { box.textContent = ''; box.hidden = true; return; }
  box.textContent = message; box.className = 'notice bad'; box.hidden = false;
}
const money = v => v === null || v === undefined ? '—' : Number(v).toLocaleString('vi-VN') + ' đ';
const time = v => v ? new Date(v).toLocaleString('vi-VN') : '—';
const hhmm = v => v ? new Date(v).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—';
const short = v => v ? String(v).replace(/^ANTA-BK-/i, '').slice(0, 8).toUpperCase() : '—';
const dateInput = d => d.toISOString().slice(0, 10);

const STATUS_LABEL = { PENDING_PAYMENT: 'Chờ thanh toán', PENDING_OWNER_CONFIRMATION: 'Chờ xác nhận',
  CONFIRMED: 'Đã xác nhận', CANCELLED: 'Đã hủy', EXPIRED: 'Hết hạn thanh toán' };
function displayStatus(row) {
  if (row.status === 'CONFIRMED') {
    const now = Date.now(), start = Date.parse(row.starts_at), end = Date.parse(row.ends_at);
    if (now >= start && now < end) return { text: 'Đang chơi', cls: 'playing' };
    if (now >= end) return { text: 'Hoàn thành', cls: 'ok' };
  }
  const cls = { PENDING_PAYMENT: 'pending', PENDING_OWNER_CONFIRMATION: 'wait', CONFIRMED: 'ok', CANCELLED: 'bad', EXPIRED: 'bad' }[row.status] || 'pending';
  return { text: STATUS_LABEL[row.status] || row.status, cls };
}
function tag(row) { const s = displayStatus(row); return el('span', { class: 'tag ' + s.cls, text: s.text }); }
function table(columns, rows) {
  if (!rows.length) return el('div', { class: 'card' }, el('p', { class: 'muted', style: 'margin:0', text: 'Không có dữ liệu phù hợp.' }));
  const head = el('tr', {}, columns.map(c => el('th', { text: c.title })));
  const body = rows.map(row => el('tr', {}, columns.map(c => {
    const value = c.render(row);
    return el('td', c.wrap ? { class: 'wrap' } : {}, value instanceof Node ? value : document.createTextNode(value ?? '—'));
  })));
  return el('div', { class: 'table-wrap' }, el('table', {}, [el('thead', {}, head), el('tbody', {}, body)]));
}
async function act(button, work, done) {
  const run = window.AntaMotion ? () => window.AntaMotion.runButtonAction(button, work) : async () => { button.disabled = true; try { return await work(); } finally { button.disabled = false; } };
  try { const result = await run(); notify(done); return result; }
  catch (error) { notify(error.message, true); throw error; }
}
function modal(title, bodyNodes, { confirmText = 'Lưu', onConfirm, danger = false } = {}) {
  const backdrop = el('div', { class: 'modal-backdrop' });
  const close = () => {
    document.removeEventListener('keydown', onKey);
    if (window.AntaMotion) window.AntaMotion.closeModal(backdrop); else backdrop.remove();
  };
  const onKey = e => { if (e.key === 'Escape') close(); };
  const error = el('p', { class: 'error' });
  const confirmBtn = el('button', { class: danger ? 'danger' : '', text: confirmText });
  confirmBtn.addEventListener('click', async () => {
    error.textContent = '';
    try {
      const work = window.AntaMotion ? () => window.AntaMotion.runButtonAction(confirmBtn, onConfirm) : async () => { confirmBtn.disabled = true; try { await onConfirm(); } finally { confirmBtn.disabled = false; } };
      await work();
      close();
    } catch (e) { error.textContent = e.message; }
  });
  backdrop.append(el('div', { class: 'modal' }, [el('h3', { text: title }), ...bodyNodes, error,
    el('div', { class: 'actions' }, [el('button', { class: 'ghost', text: 'Hủy', on: { click: close } }), confirmBtn])]));
  backdrop.addEventListener('click', e => { if (e.target === backdrop) close(); });
  document.addEventListener('keydown', onKey);
  document.body.append(backdrop);
  return { close };
}
function notAvailableYet(what) {
  modal(what, [el('p', { text: `Tính năng "${what}" cần thêm xác nhận nghiệp vụ (mô hình khách vãng lai/thanh toán tại sân) trước khi triển khai. Màn hình đã sẵn sàng về giao diện, API sẽ bổ sung sau.` })],
    { confirmText: 'Đã hiểu', onConfirm: () => {} });
}

// ---- state ----
let branches = [], sportsList = [], currentBranch = null, stats = null;
let scheduleState = { date: dateInput(new Date()), sportId: '', courtId: '' };
let bookingState = { page: 1 };

const NAV = { operations: [['stats', 'Thống kê'], ['schedule', 'Lịch sân'], ['bookings', 'Đơn đặt'], ['cancellations', 'Yêu cầu huỷ']],
  facility: [['courts', 'Sân và giá'], ['submit-branch', 'Đăng ký sân mới'], ['services', 'Dịch vụ'], ['cashflow', 'Thu chi']] };
const IMPLEMENTED = new Set(['schedule', 'bookings', 'courts', 'submit-branch']);
let current = 'schedule';

function closeDrawer() {
  $('sidebar').classList.remove('open');
  $('backdrop').hidden = true;
}

function renderNav() {
  const build = (items, target) => $(target).replaceChildren(...items.map(([key, label]) => {
    const icon = svgIcon(NAV_ICONS[key] || NAV_ICONS.schedule);
    const btn = el('button', {}, [el('span', { class: 'nav-label' }, [icon, el('span', { text: label })])]);
    if (key === 'bookings' && stats?.pendingConfirmation) btn.append(el('span', { class: 'badge', text: String(stats.pendingConfirmation) }));
    btn.toggleAttribute('aria-current', key === current); if (key === current) btn.setAttribute('aria-current', 'page');
    btn.addEventListener('click', () => { closeDrawer(); go(key); });
    return btn;
  }));
  build(NAV.operations, 'nav-ops'); build(NAV.facility, 'nav-facility');
}
async function go(view, extra) {
  current = view; renderNav();
  const container = $('view');
  container.replaceChildren(window.AntaMotion ? window.AntaMotion.skeletonNode() : el('div', { class: 'card' }, el('p', { class: 'muted', style: 'margin:0', text: 'Đang tải dữ liệu…' })));
  if (!IMPLEMENTED.has(view) && view !== 'detail') {
    container.replaceChildren(el('div', { class: 'card' }, [
      el('h3', { text: 'Phân hệ đang phát triển' }),
      el('p', { class: 'muted', style: 'margin:0',
        text: 'Màn hình này chưa thuộc phạm vi triển khai giai đoạn đầu (hiện hỗ trợ Lịch sân, Đơn đặt, Sân và giá, và Đăng ký cơ sở mới chờ Admin duyệt).' })
    ]));
    if (window.AntaMotion) window.AntaMotion.animateIn(container);
    return;
  }
  if ((view === 'schedule' || view === 'bookings' || view === 'courts' || view === 'detail') && !currentBranch) {
    container.replaceChildren(el('div', { class: 'card' }, [
      el('h3', { text: 'Tài khoản chưa có cơ sở được duyệt' }),
      el('p', { class: 'muted', text: 'Bạn có thể gửi hồ sơ đăng ký cơ sở mới ngay bây giờ. Sau khi Admin phê duyệt, cơ sở sẽ xuất hiện ở thanh chọn bên trái.' }),
      el('button', { text: '＋ Đăng ký cơ sở mới ngay', on: { click: () => go('submit-branch') } })
    ]));
    if (window.AntaMotion) window.AntaMotion.animateIn(container);
    return;
  }
  try {
    if (view === 'schedule') await renderSchedule(container);
    else if (view === 'bookings') await renderBookings(container);
    else if (view === 'detail') await renderDetail(container, extra);
    else if (view === 'courts') await renderCourts(container);
    else if (view === 'submit-branch') await renderSubmitBranch(container);
    if (window.AntaMotion) window.AntaMotion.animateIn(container);
  } catch (error) { container.replaceChildren(); notify(error.message, true); }
}
async function refreshStats() {
  if (!currentBranch) return;
  try { stats = await call(`/owner/bookings/stats?branchId=${currentBranch}`); renderNav(); } catch { /* badge is best-effort */ }
}

// ---- Lịch sân ----
async function renderSchedule(container) {
  const data = await call(`/owner/courts/schedule?${new URLSearchParams({ branchId: currentBranch, date: scheduleState.date,
    ...(scheduleState.sportId ? { sportId: scheduleState.sportId } : {}), ...(scheduleState.courtId ? { courtId: scheduleState.courtId } : {}) })}`);
  const wrap = el('div');
  wrap.append(el('div', { class: 'page-head' }, [
    el('div', {}, [el('h2', { text: 'Lịch sân' }),
      el('div', { class: 'sub', text: `${data.branch.name} · Mở cửa ${String(data.branch.openingHour).padStart(2, '0')}:00 – ${String(data.branch.closingHour).padStart(2, '0')}:00` })]),
    el('div', { class: 'actions' }, [
      el('button', { class: 'ghost', text: '🔒 Khóa khung giờ', on: { click: () => openBlockModal(data) } }),
      el('button', { text: '＋ Tạo đơn tại quầy', on: { click: () => notAvailableYet('Tạo đơn tại quầy') } })])
  ]));

  const dateNav = el('div', { class: 'date-nav' });
  const shift = n => { const d = new Date(scheduleState.date + 'T00:00:00'); d.setDate(d.getDate() + n); scheduleState.date = dateInput(d); go('schedule'); };
  const dateLabel = new Date(scheduleState.date + 'T00:00:00').toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' });
  const dateField = el('input', { type: 'date', value: scheduleState.date });
  dateField.addEventListener('change', () => { scheduleState.date = dateField.value; go('schedule'); });
  dateNav.append(
    el('button', { class: 'ghost small', text: '‹ Hôm trước', on: { click: () => shift(-1) } }),
    el('button', { class: 'ghost small', text: 'Hôm nay', on: { click: () => { scheduleState.date = dateInput(new Date()); go('schedule'); } } }),
    el('button', { class: 'ghost small', text: 'Hôm sau ›', on: { click: () => shift(1) } }),
    el('span', { class: 'current-date', text: dateLabel.charAt(0).toUpperCase() + dateLabel.slice(1) }),
    dateField);

  const sports = [...new Map(data.courts.map(c => [c.sport_id, c.sport_name])).entries()];
  const sportTabs = el('div', { class: 'sport-tabs' }, [
    tabButton(`Tất cả (${data.courts.length})`, !scheduleState.sportId, () => { scheduleState.sportId = ''; go('schedule'); }),
    ...sports.map(([id, name]) => tabButton(`${name} (${data.courts.filter(c => c.sport_id === id).length})`,
      scheduleState.sportId === id, () => { scheduleState.sportId = id; go('schedule'); }))]);

  wrap.append(el('div', { class: 'schedule-toolbar' }, [dateNav, sportTabs]));
  wrap.append(renderGrid(data));
  container.replaceChildren(wrap);
}
function tabButton(text, activeNow, onClick) {
  const b = el('button', { text, on: { click: onClick } }); if (activeNow) b.setAttribute('aria-current', 'page'); return b;
}
function renderGrid(data) {
  const opening = data.branch.openingHour, closing = data.branch.closingHour, hourPx = 48;
  const minutesFromOpening = iso => {
    const d = new Date(iso); const local = new Date(d.toLocaleString('en-US', { timeZone: data.branch.timezone }));
    return (local.getHours() - opening) * 60 + local.getMinutes();
  };
  const timeCol = el('div', { style: 'width:64px;flex:none' }, [el('div', { class: 'corner', style: `height:50px` }),
    ...Array.from({ length: closing - opening }, (_, i) => el('div', { class: 'time-label', style: `height:${hourPx}px;line-height:${hourPx}px`, text: `${String(opening + i).padStart(2, '0')}:00` }))]);
  const columns = [timeCol];
  for (const court of data.courts) {
    const body = el('div', { style: `position:relative;height:${(closing - opening) * hourPx}px` });
    for (let i = 0; i < closing - opening; i++) {
      body.append(el('div', { style: `position:absolute;left:0;right:0;top:${i * hourPx}px;height:${hourPx}px;border-top:1px solid var(--line);pointer-events:none` }));
    }
    const items = [...data.bookings.filter(b => b.yard_id === court.court_id).map(b => ({ ...b, kind: 'booking' })),
      ...data.blocks.filter(b => b.yard_id === court.court_id).map(b => ({ ...b, kind: 'block' }))];
    for (const item of items) {
      const top = Math.max(0, minutesFromOpening(item.starts_at)) / 60 * hourPx;
      const height = Math.max(24, (minutesFromOpening(item.ends_at) - minutesFromOpening(item.starts_at)) / 60 * hourPx - 4);
      const cls = item.kind === 'block' ? 'locked' : { PENDING_PAYMENT: 'pending', PENDING_OWNER_CONFIRMATION: 'wait', CONFIRMED: 'confirmed' }[item.status] || 'pending';
      const card = el('div', { class: 'booking-card ' + cls, style: `top:${top + 2}px;height:${height}px` }, [
        el('b', { text: item.kind === 'block' ? '🔒 Đã khóa' : (item.customer_name || item.customer_contact) }),
        el('span', { text: `${hhmm(item.starts_at)}–${hhmm(item.ends_at)}` })]);
      card.addEventListener('click', () => item.kind === 'block' ? confirmReleaseBlock(item) : go('detail', { id: item.id }));
      body.append(card);
    }
    columns.push(el('div', { style: 'flex:1;min-width:160px;border-left:1px solid var(--line)' },
      [el('div', { class: 'court-head', style: 'height:50px', text: court.name }, [el('span', { class: 'sport', text: court.sport_name })]), body]));
  }
  const grid = el('div', { class: 'schedule-grid', style: 'display:flex' }, columns);
  const legend = el('div', { class: 'legend' }, [
    legendItem('var(--orange)', 'Chờ xác nhận / Chờ thanh toán'), legendItem('var(--green)', 'Đã xác nhận'), legendItem('var(--muted)', 'Đã khóa')]);
  return el('div', { class: 'schedule-grid-wrap' }, [grid, legend]);
}
function legendItem(color, text) { return el('span', {}, [el('i', { style: `background:${color}` }), text]); }

function openBlockModal(data) {
  const courtSel = el('select', {}, data.courts.map(c => el('option', { value: c.court_id, text: c.name })));
  if (scheduleState.courtId) courtSel.value = scheduleState.courtId;
  const dateF = el('input', { type: 'date', value: scheduleState.date });
  const startF = el('input', { type: 'time', value: '10:00' }), endF = el('input', { type: 'time', value: '12:00' });
  const reasonF = el('textarea', { rows: 3, placeholder: 'Ví dụ: bảo trì đèn, thay thảm sân' });
  modal('Khóa khung giờ', [
    el('label', {}, [el('span', { text: 'Sân cần khóa' }), courtSel]), el('label', {}, [el('span', { text: 'Ngày' }), dateF]),
    el('div', { style: 'display:flex;gap:10px' }, [el('label', { style: 'flex:1' }, [el('span', { text: 'Giờ bắt đầu' }), startF]), el('label', { style: 'flex:1' }, [el('span', { text: 'Giờ kết thúc' }), endF])]),
    el('label', {}, [el('span', { text: 'Lý do khóa' }), reasonF])
  ], { confirmText: 'Khóa khung giờ', onConfirm: async () => {
    const startsAt = toOffsetIso(dateF.value, startF.value), endsAt = toOffsetIso(dateF.value, endF.value);
    await call(`/owner/courts/${courtSel.value}/blocks`, 'POST', { startsAt, endsAt, reason: reasonF.value.trim() || 'Bảo trì sân' });
    notify('Đã khóa khung giờ.'); await go('schedule');
  } });
}
function toOffsetIso(date, hhmmValue) { return `${date}T${hhmmValue}:00+07:00`; }
function confirmReleaseBlock(block) {
  modal('Mở khóa khung giờ', [el('p', {}, [`Mở lại khung giờ ${hhmm(block.starts_at)}–${hhmm(block.ends_at)}?`]),
    el('p', { class: 'muted', text: block.reason })], { confirmText: 'Mở khóa', danger: true, onConfirm: async () => {
    await call(`/owner/blocks/${block.id}`, 'DELETE'); notify('Đã mở khóa khung giờ.'); await go('schedule');
  } });
}

// ---- Đơn đặt ----
async function renderBookings(container) {
  const [s, list] = await Promise.all([
    call(`/owner/bookings/stats?branchId=${currentBranch}`),
    call(`/owner/bookings?${new URLSearchParams({ branchId: currentBranch, page: String(bookingState.page || 1),
      ...(bookingState.q ? { q: bookingState.q } : {}), ...(bookingState.fromDate ? { fromDate: bookingState.fromDate } : {}),
      ...(bookingState.toDate ? { toDate: bookingState.toDate } : {}), ...(bookingState.status ? { status: bookingState.status } : {}),
      ...(bookingState.source ? { source: bookingState.source } : {}) })}`)]);
  stats = s; renderNav();
  const wrap = el('div');
  wrap.append(el('div', { class: 'page-head' }, [
    el('div', {}, [el('h2', { text: 'Đơn đặt' }), el('div', { class: 'sub', text: 'Mọi đơn của cơ sở, từ app Anta và tại quầy' })]),
    el('button', { text: '＋ Tạo đơn tại quầy', on: { click: () => notAvailableYet('Tạo đơn tại quầy') } })]));
  wrap.append(el('div', { class: 'stats' }, [
    statCard(s.pendingConfirmation, 'Chờ xác nhận'), statCard(s.today, 'Hôm nay'), statCard(s.upcoming, 'Sắp tới'), statCard(s.cancelledThisWeek, 'Đã hủy tuần này')]));

  const q = el('input', { placeholder: 'Tìm tên, SĐT hoặc mã đơn', value: bookingState.q || '' });
  const from = el('input', { type: 'date', value: bookingState.fromDate || '' }), to = el('input', { type: 'date', value: bookingState.toDate || '' });
  const status = selectEl({ '': 'Mọi trạng thái', PENDING_PAYMENT: 'Chờ thanh toán', PENDING_OWNER_CONFIRMATION: 'Chờ xác nhận',
    CONFIRMED: 'Đã xác nhận', CANCELLED: 'Đã hủy', EXPIRED: 'Hết hạn' }, bookingState.status || '');
  const source = selectEl({ '': 'Mọi nguồn', APP: 'App Anta', COUNTER: 'Tại quầy' }, bookingState.source || '');
  const apply = () => { Object.assign(bookingState, { q: q.value.trim(), fromDate: from.value, toDate: to.value, status: status.value, source: source.value, page: 1 }); go('bookings'); };
  const form = el('form', { class: 'toolbar', on: { submit: e => { e.preventDefault(); apply(); } } },
    [el('label', {}, [el('span', { text: 'Tìm kiếm' }), q]), el('label', {}, [el('span', { text: 'Từ ngày' }), from]), el('label', {}, [el('span', { text: 'Đến ngày' }), to]),
      el('label', {}, [el('span', { text: 'Trạng thái' }), status]), el('label', {}, [el('span', { text: 'Nguồn đặt' }), source]), el('button', { type: 'submit', text: 'Lọc' }),
      el('button', { type: 'button', class: 'ghost', text: 'Xóa lọc', on: { click: () => { bookingState = { page: 1 }; go('bookings'); } } })]);
  wrap.append(form);

  wrap.append(table([
    { title: 'Mã đơn', render: r => el('code', { text: short(r.id) }) },
    { title: 'Khách hàng', wrap: true, render: r => el('div', {}, [el('div', { style: 'font-weight:600', text: r.customer_name }), el('div', { class: 'muted', style: 'font-size:12px', text: r.customer_contact })]) },
    { title: 'Sân', render: r => r.yard_name }, { title: 'Ngày chơi', render: r => new Date(r.starts_at).toLocaleDateString('vi-VN') },
    { title: 'Giờ chơi', render: r => `${hhmm(r.starts_at)}–${hhmm(r.ends_at)}` }, { title: 'Tổng tiền', render: r => el('strong', { text: money(r.amount) }) },
    { title: 'Nguồn', render: r => r.source === 'COUNTER' ? 'Tại quầy' : 'App Anta' }, { title: 'Trạng thái', render: r => tag(r) },
    { title: '', render: r => { const b = el('button', { class: 'small ghost', text: 'Chi tiết →' }); b.addEventListener('click', () => go('detail', { id: r.id })); return b; } }
  ], list.items));

  const pages = Math.max(1, Math.ceil(list.total / list.pageSize));
  if (pages > 1) wrap.append(el('div', { class: 'actions', style: 'margin-top:14px;justify-content:flex-end;align-items:center' }, [
    el('button', { class: 'ghost small', text: '‹ Trước', disabled: list.page <= 1 ? 'disabled' : null, on: { click: () => { bookingState.page = list.page - 1; go('bookings'); } } }),
    el('span', { class: 'muted', text: `Trang ${list.page}/${pages}` }),
    el('button', { class: 'ghost small', text: 'Sau ›', disabled: list.page >= pages ? 'disabled' : null, on: { click: () => { bookingState.page = list.page + 1; go('bookings'); } } })]));
  container.replaceChildren(wrap);
}
function statCard(value, label) { return el('div', { class: 'card stat' }, [el('b', { text: String(value) }), el('span', { text: label })]); }
function selectEl(options, value) { const s = el('select', {}, Object.entries(options).map(([v, t]) => el('option', { value: v, text: t }))); s.value = value; return s; }

// ---- Chi tiết đơn ----
async function renderDetail(container, extra) {
  const row = await call(`/owner/bookings/${extra.id}`);
  const wrap = el('div');
  wrap.append(el('div', { class: 'page-head' }, [
    el('div', {}, [el('h2', { text: `Đơn ${short(row.id)}` }), el('div', { class: 'sub', text: `Khách đặt lúc ${time(row.created_at)} từ ${row.source === 'COUNTER' ? 'tại quầy' : 'app Anta'}` })]),
    el('button', { class: 'ghost', text: '← Danh sách đơn', on: { click: () => go('bookings') } })]));

  const grid = el('div', { class: 'detail-grid' });
  const left = el('div');
  left.append(el('div', { class: 'card' }, [el('h3', { text: 'Thông tin đặt sân' }),
    el('dl', { class: 'rows' }, [
      dRow('Sân', `${row.yard_name}, ${row.sport_name}`), dRow('Ngày chơi', new Date(row.starts_at).toLocaleDateString('vi-VN')),
      dRow('Giờ chơi', `${hhmm(row.starts_at)} – ${hhmm(row.ends_at)} (${row.hours} giờ)`), dRow('Giá sân theo giờ', money(row.hourly_price)),
      dRow('Nguồn đặt', row.source === 'COUNTER' ? 'Tại quầy' : 'App Anta')])]));
  left.append(el('div', { class: 'card' }, [el('h3', { text: 'Khách hàng' }),
    el('dl', { class: 'rows' }, [dRow('Tên khách', row.customer_name), dRow('Liên hệ', row.customer_contact)])]));
  left.append(costCard(row));
  if (row.statusHistory?.length) left.append(el('div', { class: 'card' }, [el('h3', { text: 'Lịch sử thao tác' }),
    el('ul', { style: 'margin:0;padding-left:18px;display:grid;gap:6px' }, row.statusHistory.map(h => el('li', { text: `${time(h.created_at)}: ${h.from_status || '—'} → ${h.to_status}${h.reason ? ' (' + h.reason + ')' : ''}` })))]));

  const right = el('div');
  right.append(statusCard(row));
  grid.append(left, right);
  wrap.append(grid);
  container.replaceChildren(wrap);
}
function dRow(label, value) { return [el('dt', { text: label }), el('dd', { text: value ?? '—' })]; }
function costCard(row) {
  const rows = [['Tiền sân', `${row.yard_name}, ${row.hours} giờ`, money(row.hourly_price), money(row.courtAmount)],
    ...row.services.map(s => ['Dịch vụ: ' + s.name, `${s.quantity} x`, money(s.unit_price), money(s.subtotal)])];
  const t = el('table', { class: 'cost-table' }, [
    el('thead', {}, el('tr', {}, ['Khoản mục', 'Số lượng', 'Đơn giá', 'Thành tiền'].map(h => el('th', { text: h })))),
    el('tbody', {}, rows.map(r => el('tr', {}, r.map(v => el('td', { text: v })))))]);
  return el('div', { class: 'card' }, [el('h3', { text: 'Dịch vụ kèm theo và thanh toán' }), el('div', { class: 'table-wrap', style: 'box-shadow:none' }, t),
    el('dl', { class: 'rows', style: 'margin-top:14px' }, [
      dRow('Tổng cộng', money(row.amount)), dRow('Đã thanh toán', money(row.paidAmount)), dRow('Còn phải thu tại sân', money(row.outstanding))])]);
}
function statusCard(row) {
  const card = el('div', { class: 'card' }, [el('h3', { text: 'Trạng thái đơn' }), el('div', { style: 'margin-bottom:12px' }, tag(row))]);
  if (row.status === 'PENDING_OWNER_CONFIRMATION') {
    const note = el('p', {}, ['Khách đã thanh toán. ', row.canConfirm
      ? el('span', { class: 'countdown', text: `Còn ${remaining(row.confirm_deadline_at)} để xác nhận.` })
      : el('span', { class: 'tag bad', text: 'Đã quá hạn xác nhận' })]);
    card.append(note);
    const confirmBtn = el('button', { text: '✓ Xác nhận đơn', disabled: row.canConfirm ? null : 'disabled' });
    confirmBtn.addEventListener('click', () => act(confirmBtn, () => call(`/owner/bookings/${row.id}/confirm`, 'POST'), 'Đã xác nhận đơn.').then(() => go('detail', { id: row.id })).catch(() => {}));
    const rejectBtn = el('button', { class: 'danger', text: 'Từ chối đơn' });
    rejectBtn.addEventListener('click', () => openRejectModal(row));
    card.append(el('div', { class: 'actions' }, [confirmBtn, rejectBtn]),
      el('p', { class: 'muted', style: 'margin-top:10px;font-size:12.5px', text: 'Từ chối thì phải ghi lý do. Khách nhận lại toàn bộ số tiền đã trả.' }));
  } else if (row.refund) {
    card.append(el('p', {}, [`Hoàn tiền: ${money(row.refund.amount)} (${row.refund.percent}%) — `, el('span', { class: 'tag ' + (row.refund.status === 'SUCCEEDED' ? 'ok' : 'pending'), text: row.refund.status }),
      row.refund.reason ? el('div', { class: 'muted', text: row.refund.reason }) : null]));
  } else {
    card.append(el('p', { class: 'muted', style: 'margin:0', text: 'Không còn thao tác nào khả dụng cho trạng thái này.' }));
  }
  return card;
}
function remaining(deadline) {
  const ms = Date.parse(deadline) - Date.now(); if (ms <= 0) return '0 phút';
  const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000);
  return h > 0 ? `${h} giờ ${m} phút` : `${m} phút`;
}
function openRejectModal(row) {
  const reasonF = el('textarea', { rows: 3, placeholder: 'Ví dụ: sân đang bảo trì đột xuất, trùng lịch do lỗi hệ thống…' });
  modal('Từ chối đơn', [el('p', {}, [`Đơn ${short(row.id)} của ${row.customer_name}. Khách sẽ được hoàn lại toàn bộ ${money(row.amount)}.`]),
    el('label', {}, [el('span', { text: 'Lý do từ chối (bắt buộc)' }), reasonF])], { confirmText: 'Từ chối đơn và hoàn tiền', danger: true, onConfirm: async () => {
    const reason = reasonF.value.trim();
    if (!reason) throw new Error('Vui lòng nhập lý do từ chối.');
    await call(`/owner/bookings/${row.id}/reject`, 'POST', { reason });
    notify('Đã từ chối đơn và hoàn tiền cho khách.'); await go('detail', { id: row.id });
  } });
}

// ---- Đăng ký cơ sở mới & Sân và giá ----
function submissionBadge(status) {
  if (status === 'APPROVED') return el('span', { class: 'tag ok', text: 'Đã duyệt · Đã lên server' });
  if (status === 'REJECTED') return el('span', { class: 'tag bad', text: 'Từ chối' });
  return el('span', { class: 'tag wait', text: 'Chờ Admin duyệt' });
}

async function uploadPhotoToAzure(file, branchId) {
  const mimeType = file.type || 'image/jpeg';
  const presign = await call(branchId ? `/branches/${branchId}/images/presign` : '/media/presign', 'POST', { mimeType });
  const putResp = await fetch(presign.url, { method: presign.method || 'PUT', headers: presign.headers || { 'Content-Type': mimeType }, body: file });
  if (!putResp.ok) throw new Error(`Tải ảnh lên Azure thất bại (HTTP ${putResp.status})`);
  const done = await call(`/media/${presign.uploadId}/complete`, 'POST');
  return done.url || presign.publicUrl;
}

function makeYardRowEditor(initial = {}) {
  const nameIn = el('input', { placeholder: 'Ví dụ: Sân 1 (Ngoài trời)', value: initial.name || '' });
  const opts = sportsList.length ? sportsList : [{ id: 'sp-pickleball', name: 'Pickleball' }, { id: 'sp-badminton', name: 'Cầu lông' }, { id: 'sp-football', name: 'Bóng đá mini' }, { id: 'sp-tennis', name: 'Tennis' }];
  const sportSel = el('select', {}, opts.map(s => el('option', { value: s.id, text: s.name })));
  if (initial.sportId) sportSel.value = initial.sportId;
  const priceIn = el('input', { type: 'number', min: '10000', step: '10000', value: String(initial.hourlyPrice || 200000) });
  const removeBtn = el('button', { type: 'button', class: 'danger small', text: '✕', title: 'Xóa sân này' });
  const row = el('div', { class: 'yard-row' }, [
    el('label', {}, [el('span', { text: 'Tên sân con' }), nameIn]),
    el('label', {}, [el('span', { text: 'Môn thể thao' }), sportSel]),
    el('label', {}, [el('span', { text: 'Giá / giờ (đ)' }), priceIn]),
    removeBtn
  ]);
  return {
    el: row,
    removeBtn,
    read: () => ({ name: nameIn.value.trim(), sportId: sportSel.value, hourlyPrice: Number(priceIn.value || 0) })
  };
}

async function renderSubmitBranch(container) {
  const [subs] = await Promise.all([call('/owner/submissions'), loadBranchesAndSyncSelector()]);
  const wrap = el('div');
  wrap.append(el('div', { class: 'page-head' }, [
    el('div', {}, [
      el('h2', { text: 'Đăng ký sân & cơ sở mới' }),
      el('div', { class: 'sub', text: 'Hồ sơ gửi lên sẽ được Admin kiểm duyệt trước khi hiển thị công khai trên app và server.' })
    ]),
    el('button', { class: 'ghost small', text: '↻ Cập nhật trạng thái duyệt', on: { click: () => go('submit-branch') } })
  ]));

  const nameIn = el('input', { placeholder: 'Ví dụ: Pickleball Cầu Giấy Arena', required: 'required' });
  const addrIn = el('input', { placeholder: 'Số nhà, đường, quận/huyện, thành phố', required: 'required' });
  const latIn = el('input', { type: 'number', step: 'any', value: '21.0285' });
  const lngIn = el('input', { type: 'number', step: 'any', value: '105.8542' });
  const citySel = el('select', {}, [
    el('option', { value: '21.0285,105.8542', text: 'Hà Nội (mặc định)' }),
    el('option', { value: '10.7721,106.6951', text: 'TP. Hồ Chí Minh (Q.1)' }),
    el('option', { value: '16.0544,108.2022', text: 'Đà Nẵng' }),
    el('option', { value: '', text: 'Giữ tọa độ tự nhập' })
  ]);
  citySel.addEventListener('change', () => {
    if (!citySel.value) return;
    const [la, ln] = citySel.value.split(',');
    latIn.value = la; lngIn.value = ln;
  });

  const openIn = el('input', { type: 'number', min: '0', max: '23', value: '6' });
  const closeIn = el('input', { type: 'number', min: '1', max: '24', value: '22' });
  const descIn = el('textarea', { rows: 3, placeholder: 'Ví dụ: Sân tiêu chuẩn thi đấu, có mái che, bãi đỗ xe miễn phí. T2-CN: 6h-22h: 200.000 ₫.' });
  const rulesIn = el('textarea', { rows: 3, placeholder: 'Mỗi dòng là một nội quy (ví dụ: Mang giày đế bằng không bám bẩn)' });

  const uploadedImages = [];
  const thumbsWrap = el('div', { class: 'photo-thumbs' });
  function renderThumbs() {
    thumbsWrap.replaceChildren(...uploadedImages.map((url, idx) => el('div', { class: 'photo-thumb' }, [
      el('img', { src: url, alt: 'Ảnh cơ sở' }),
      el('button', { type: 'button', text: '✕', on: { click: () => { uploadedImages.splice(idx, 1); renderThumbs(); } } })
    ])));
  }

  const fileIn = el('input', { type: 'file', accept: 'image/jpeg,image/png,image/webp' });
  const uploadStatus = el('span', { class: 'muted', style: 'font-size:12px', text: 'Hỗ trợ JPG/PNG/WebP — lưu trực tiếp lên Azure Blob Storage.' });
  const uploadBtn = el('button', { type: 'button', class: 'ghost small', text: '⬆ Tải ảnh lên Azure' });
  uploadBtn.addEventListener('click', async () => {
    const file = fileIn.files?.[0];
    if (!file) { notify('Vui lòng chọn tệp ảnh trước khi tải lên.', true); return; }
    await act(uploadBtn, async () => {
      uploadStatus.textContent = 'Đang tải ảnh lên Azure Blob…';
      const url = await uploadPhotoToAzure(file, null);
      uploadedImages.push(url);
      renderThumbs();
      fileIn.value = '';
      uploadStatus.textContent = `Đã tải lên (${uploadedImages.length} ảnh).`;
    }, 'Đã tải ảnh lên Azure Blob Storage.');
  });

  const urlIn = el('input', { placeholder: 'Hoặc dán link ảnh https://...' });
  const addUrlBtn = el('button', { type: 'button', class: 'ghost small', text: 'Thêm link' });
  addUrlBtn.addEventListener('click', () => {
    const u = urlIn.value.trim();
    if (!u.startsWith('http://') && !u.startsWith('https://')) { notify('Link ảnh phải bắt đầu bằng https:// hoặc http://', true); return; }
    uploadedImages.push(u); renderThumbs(); urlIn.value = '';
  });

  const yardEditors = [];
  const yardHost = el('div', { class: 'yard-rows' });
  function addYardRow(init) {
    const editor = makeYardRowEditor(init);
    editor.removeBtn.addEventListener('click', () => {
      if (yardEditors.length <= 1) { notify('Cần tối thiểu 1 sân con trong hồ sơ.', true); return; }
      const i = yardEditors.indexOf(editor);
      if (i >= 0) yardEditors.splice(i, 1);
      editor.el.remove();
    });
    yardEditors.push(editor);
    yardHost.append(editor.el);
  }
  addYardRow({ name: 'Sân 1', hourlyPrice: 200000 });

  const submitBtn = el('button', { type: 'submit', text: 'Gửi hồ sơ chờ Admin duyệt' });
  const form = el('form', { class: 'form-stack' }, [
    el('label', {}, [el('span', { text: 'Tên cơ sở / cụm sân *' }), nameIn]),
    el('label', {}, [el('span', { text: 'Địa chỉ đầy đủ *' }), addrIn]),
    el('div', { class: 'form-grid' }, [
      el('label', {}, [el('span', { text: 'Khu vực gợi ý' }), citySel]),
      el('div', { class: 'form-grid' }, [
        el('label', {}, [el('span', { text: 'Giờ mở cửa' }), openIn]),
        el('label', {}, [el('span', { text: 'Giờ đóng cửa' }), closeIn])
      ])
    ]),
    el('div', { class: 'form-grid' }, [
      el('label', {}, [el('span', { text: 'Vĩ độ (Lat)' }), latIn]),
      el('label', {}, [el('span', { text: 'Kinh độ (Lng)' }), lngIn])
    ]),
    el('div', {}, [
      el('label', {}, [el('span', { text: 'Hình ảnh cơ sở' })]),
      el('div', { class: 'photo-box' }, [
        el('div', { class: 'actions' }, [fileIn, uploadBtn]),
        el('div', { class: 'actions' }, [urlIn, addUrlBtn]),
        uploadStatus,
        thumbsWrap
      ])
    ]),
    el('div', {}, [
      el('div', { style: 'display:flex;justify-content:space-between;align-items:center' }, [
        el('label', { style: 'margin:0' }, [el('span', { style: 'margin:0', text: 'Danh sách sân con (tối thiểu 1 sân) *' })]),
        el('button', { type: 'button', class: 'ghost small', text: '＋ Thêm sân con', on: { click: () => addYardRow({ name: `Sân ${yardEditors.length + 1}`, hourlyPrice: 200000 }) } })
      ]),
      yardHost
    ]),
    el('label', {}, [el('span', { text: 'Mô tả & bảng giá' }), descIn]),
    el('label', {}, [el('span', { text: 'Nội quy sân (mỗi dòng 1 quy định)' }), rulesIn]),
    el('div', { class: 'actions' }, [submitBtn])
  ]);
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const yards = yardEditors.map(x => x.read()).filter(y => y.name && y.hourlyPrice >= 10000);
    if (!nameIn.value.trim() || !addrIn.value.trim()) { notify('Vui lòng nhập tên cơ sở và địa chỉ.', true); return; }
    if (!yards.length) { notify('Cần tối thiểu 1 sân con hợp lệ (giá tối thiểu 10.000 đ).', true); return; }
    const rules = rulesIn.value.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    await act(submitBtn, () => call('/owner/submissions', 'POST', {
      submissionType: 'NEW_BRANCH',
      name: nameIn.value.trim(),
      address: addrIn.value.trim(),
      lat: Number(latIn.value || 10.7721),
      lng: Number(lngIn.value || 106.6951),
      openingHour: Number(openIn.value || 6),
      closingHour: Number(closeIn.value || 22),
      description: descIn.value.trim(),
      rules,
      images: uploadedImages,
      yards
    }), 'Đã gửi hồ sơ đăng ký cơ sở mới! Chờ Admin duyệt để lên sàn.');
    await go('submit-branch');
  });

  const historyCard = el('div', { class: 'card' }, [
    el('h3', { text: `Hồ sơ đã gửi (${subs.length})` }),
    subs.length
      ? el('div', { class: 'sub-list' }, subs.map(s => el('div', { class: 'sub-item' }, [
          el('div', { class: 'sub-item-head' }, [
            el('strong', { text: `${s.submission_type === 'ADD_YARDS' ? '[Thêm sân] ' : ''}${s.name}` }),
            submissionBadge(s.status)
          ]),
          el('div', { class: 'muted', style: 'font-size:12.5px', text: `${s.address} · ${s.yards.length} sân con · Gửi lúc ${time(s.created_at)}` }),
          el('div', { class: 'muted', style: 'font-size:12.5px', text: s.yards.map(y => `${y.name} (${y.sport_name} - ${money(y.hourly_price)}/h)`).join(', ') }),
          s.review_note ? el('div', { class: 'sub-note', text: `Ghi chú Admin: ${s.review_note}` }) : null
        ])))
      : el('p', { class: 'muted', style: 'margin:0', text: 'Bạn chưa gửi hồ sơ đăng ký cơ sở hay sân nào.' })
  ]);

  wrap.append(el('div', { class: 'two-col' }, [
    el('div', { class: 'card' }, [el('h3', { text: 'Thông tin cơ sở mới' }), form]),
    historyCard
  ]));
  container.replaceChildren(wrap);
}

async function renderCourts(container) {
  const data = await call(`/owner/branches/${currentBranch}/courts`);
  const wrap = el('div');
  wrap.append(el('div', { class: 'page-head' }, [
    el('div', {}, [
      el('h2', { text: 'Sân và giá' }),
      el('div', { class: 'sub', text: `${data.branch.name} · Hiện có ${data.courts.length} sân đang hoạt động trên sàn` })
    ]),
    el('button', { class: 'ghost small', text: '＋ Đăng ký cơ sở mới khác', on: { click: () => go('submit-branch') } })
  ]));

  const currentCard = el('div', { class: 'card' }, [
    el('h3', { text: 'Danh sách sân đang hoạt động' }),
    table([
      { title: 'Tên sân', render: r => el('strong', { text: r.name }) },
      { title: 'Môn thể thao', render: r => r.sport_name },
      { title: 'Giá / giờ', render: r => el('strong', { text: money(r.hourly_price) }) }
    ], data.courts)
  ]);

  const yardEditor = makeYardRowEditor({ name: `Sân ${data.courts.length + 1}`, hourlyPrice: 200000 });
  yardEditor.removeBtn.hidden = true;
  const addBtn = el('button', { type: 'submit', text: 'Gửi yêu cầu thêm sân chờ Admin duyệt' });
  const addForm = el('form', { class: 'form-stack' }, [
    yardEditor.el,
    el('div', { class: 'actions' }, [addBtn])
  ]);
  addForm.addEventListener('submit', async e => {
    e.preventDefault();
    const y = yardEditor.read();
    if (!y.name || y.hourlyPrice < 10000) { notify('Nhập tên sân và giá hợp lệ (tối thiểu 10.000 đ).', true); return; }
    await act(addBtn, () => call('/owner/submissions', 'POST', {
      submissionType: 'ADD_YARDS',
      targetBranchId: currentBranch,
      name: data.branch.name,
      address: data.branch.address,
      yards: [y]
    }), 'Đã gửi yêu cầu thêm sân con chờ Admin duyệt.');
    await go('courts');
  });

  const addCard = el('div', { class: 'card' }, [
    el('h3', { text: 'Đăng ký thêm sân con mới' }),
    el('p', { class: 'muted', style: 'margin:0 0 12px;font-size:13px', text: 'Sân mới thêm sẽ ở trạng thái chờ duyệt và chỉ hiển thị cho khách đặt sau khi Admin phê duyệt.' }),
    addForm
  ]);

  const pendingCard = el('div', { class: 'card', style: 'margin-top:16px' }, [
    el('h3', { text: `Yêu cầu thêm sân đã gửi (${data.submissions.length})` }),
    data.submissions.length
      ? el('div', { class: 'sub-list' }, data.submissions.map(s => el('div', { class: 'sub-item' }, [
          el('div', { class: 'sub-item-head' }, [
            el('strong', { text: s.yards.map(y => `${y.name} (${y.sport_name} · ${money(y.hourly_price)}/h)`).join(', ') }),
            submissionBadge(s.status)
          ]),
          el('div', { class: 'muted', style: 'font-size:12px', text: `Gửi lúc ${time(s.created_at)}` }),
          s.review_note ? el('div', { class: 'sub-note', text: `Ghi chú Admin: ${s.review_note}` }) : null
        ])))
      : el('p', { class: 'muted', style: 'margin:0', text: 'Chưa có yêu cầu thêm sân nào cho cơ sở này.' })
  ]);

  wrap.append(el('div', { class: 'two-col' }, [currentCard, el('div', {}, [addCard, pendingCard])]));
  container.replaceChildren(wrap);
}

// ---- shell ----
$('menu-toggle').addEventListener('click', () => { $('sidebar').classList.add('open'); $('backdrop').hidden = false; });
$('backdrop').addEventListener('click', closeDrawer);
$('toggle-pw').addEventListener('click', () => {
  const pw = $('pw-input');
  const show = pw.type === 'password';
  pw.type = show ? 'text' : 'password';
  $('toggle-pw').textContent = show ? 'Ẩn' : 'Hiện';
});
$('fill-demo').addEventListener('click', () => {
  $('login-form').identifier.value = 'owner@anta.vn';
  $('login-form').password.value = 'anta123456';
});
$('branch-select').addEventListener('change', () => {
  currentBranch = $('branch-select').value || null;
  if (currentBranch) store.set('branch', currentBranch);
  go(current);
  refreshStats();
});

async function loadBranchesAndSyncSelector() {
  branches = await call('/owner/branches');
  if (!branches.length) {
    currentBranch = null;
    $('branch-select').replaceChildren(el('option', { value: '', text: 'Chưa có cơ sở được duyệt' }));
    $('branch-select').disabled = true;
    return;
  }
  $('branch-select').disabled = false;
  currentBranch = store.get('branch') && branches.some(b => b.id === store.get('branch')) ? store.get('branch') : branches[0].id;
  $('branch-select').replaceChildren(...branches.map(b => el('option', { value: b.id, text: b.name })));
  $('branch-select').value = currentBranch;
}

function signOut() { store.clear(); $('app').hidden = true; $('login').hidden = false; }
async function start() {
  try {
    const [me, sports] = await Promise.all([call('/users/me'), call('/public/sports').catch(() => [])]);
    sportsList = Array.isArray(sports) ? sports : [];
    await loadBranchesAndSyncSelector();
    $('who-name').textContent = me.identifier;
    $('who-avatar').textContent = (me.displayName || me.identifier || 'O').trim().charAt(0).toUpperCase();
    $('login').hidden = true; $('app').hidden = false; notify('');
    await refreshStats();
    await go(currentBranch ? 'schedule' : 'submit-branch');
  } catch (error) { signOut(); $('login-error').textContent = store.get('tried') ? error.message : ''; }
}
$('logout').addEventListener('click', async () => { try { await call('/auth/logout', 'POST'); } catch { /* session already gone */ } signOut(); });
$('login-form').addEventListener('submit', async event => {
  event.preventDefault(); $('login-error').textContent = '';
  const form = new FormData(event.target);
  try {
    const tokens = await call('/public/auth/login', 'POST', { identifier: form.get('identifier'), password: form.get('password'), deviceId: 'owner-portal' });
    store.set('access', tokens.accessToken); store.set('refresh', tokens.refreshToken); store.set('tried', '1'); event.target.reset();
    await start();
  } catch (error) { $('login-error').textContent = error.message; }
});
if (store.get('access')) start(); else $('login').hidden = false;
