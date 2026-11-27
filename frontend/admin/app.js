'use strict';
// Admin portal. All data is rendered with textContent/el(); nothing from the API is ever parsed as HTML.
const API = '/api/v1';
const $ = id => document.getElementById(id);
const store = { get: key => sessionStorage.getItem('admin_' + key), set: (key, value) => sessionStorage.setItem('admin_' + key, value), clear: () => ['access', 'refresh', 'tried'].forEach(k => sessionStorage.removeItem('admin_' + k)) };
let branches = [];

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'class') node.className = value;
    else if (key === 'on') for (const [name, fn] of Object.entries(value)) node.addEventListener(name, fn);
    else if (key === 'text') node.textContent = value;
    else if (value !== null && value !== undefined) node.setAttribute(key, value);
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

const TAB_META = {
  overview: { title: 'Tổng quan', sub: 'Số liệu vận hành, doanh thu và cảnh báo toàn hệ thống Anta', icon: ['M3 13h8V3H3z', 'M13 21h8V11h-8z', 'M13 3h8v6h-8z', 'M3 21h8v-6H3z'] },
  submissions: { title: 'Duyệt cơ sở', sub: 'Kiểm duyệt hồ sơ đăng ký cơ sở mới và thêm sân từ chủ sân', icon: ['M9 11l3 3L22 4', 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'] },
  users: { title: 'Người dùng', sub: 'Tìm kiếm tài khoản và cấp hoặc thu hồi quyền quản lý cơ sở', icon: ['M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2', 'M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M23 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'] },
  bookings: { title: 'Đặt sân', sub: 'Giám sát tất cả đơn đặt sân trên toàn hệ thống', icon: ['M8 2v4', 'M16 2v4', 'M3 10h18', 'M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z'] },
  payments: { title: 'Thanh toán', sub: 'Theo dõi giao dịch thanh toán và xử lý khoản tiền đến muộn', icon: ['M2 7h20v12H2z', 'M2 11h20', 'M6 15h4'] },
  refunds: { title: 'Hoàn tiền', sub: 'Xử lý yêu cầu hoàn tiền thủ công và ghi nhận mã giao dịch', icon: ['M3 7v6h6', 'M21 17a9 9 0 0 0-15-6.7L3 13'] },
  deletions: { title: 'Xóa tài khoản', sub: 'Theo dõi yêu cầu ẩn danh và xóa dữ liệu cá nhân người dùng', icon: ['M3 6h18', 'M8 6V4h8v2', 'M19 6l-1 14H6L5 6'] },
  audit: { title: 'Nhật ký', sub: 'Lịch sử thao tác hệ thống và phân quyền gần nhất', icon: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z', 'M14 2v6h6', 'M8 13h8', 'M8 17h6'] }
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
const money = value => Number(value || 0).toLocaleString('vi-VN') + ' ₫';
const time = value => value ? new Date(value).toLocaleString('vi-VN') : '—';
const short = value => value ? String(value).replace(/^ANTA-BK-/i, '').slice(0, 8).toUpperCase() : '—';

const STATUS_TEXT = {
  ACTIVE: 'Hoạt động',
  CONFIRMED: 'Đã xác nhận',
  SUCCEEDED: 'Thành công',
  PENDING_PAYMENT: 'Chờ thanh toán',
  PENDING_OWNER_CONFIRMATION: 'Chờ chủ sân duyệt',
  CREATED: 'Đang chờ',
  NEEDS_REVIEW: 'Tiền đến muộn',
  MANUAL_REVIEW: 'Cần chuyển tay',
  PENDING: 'Chờ duyệt',
  APPROVED: 'Đã duyệt',
  REJECTED: 'Từ chối',
  FAILED: 'Thất bại',
  CANCELLED: 'Đã hủy',
  DELETED: 'Đã xóa',
  DISABLED: 'Vô hiệu hóa',
  EXPIRED: 'Hết hạn'
};
function tag(status) {
  const ok = ['ACTIVE', 'CONFIRMED', 'SUCCEEDED', 'APPROVED'], bad = ['FAILED', 'CANCELLED', 'DELETED', 'DISABLED', 'EXPIRED', 'REJECTED'];
  const cls = ok.includes(status) ? 'ok' : bad.includes(status) ? 'bad' : 'warn';
  return el('span', { class: 'tag ' + cls, text: STATUS_TEXT[status] || status || '—' });
}
function table(columns, rows) {
  if (!rows.length) return el('div', { class: 'card' }, el('p', { class: 'muted', style: 'margin:0', text: 'Không có dữ liệu phù hợp.' }));
  const head = el('tr', {}, columns.map(column => el('th', { text: column.title })));
  const body = rows.map(row => el('tr', {}, columns.map(column => {
    const value = column.render(row);
    return el('td', column.wrap ? { class: 'wrap' } : {}, value instanceof Node ? value : document.createTextNode(value ?? '—'));
  })));
  return el('div', { class: 'table-wrap' }, el('table', {}, [el('thead', {}, head), el('tbody', {}, body)]));
}
function filter(label, options, onChange) {
  const select = el('select', { on: { change: () => onChange(select.value) } }, options.map(([value, text]) => el('option', { value, text })));
  return el('label', {}, [el('span', { text: label }), select]);
}
async function act(button, work, done) {
  const run = window.AntaMotion ? () => window.AntaMotion.runButtonAction(button, work) : async () => { button.disabled = true; try { return await work(); } finally { button.disabled = false; } };
  try { await run(); notify(done); await show(current); } catch (error) { notify(error.message, true); }
}
function modal(title, bodyNodes, { confirmText = 'Xác nhận', onConfirm, danger = false } = {}) {
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

const views = {
  async overview(view) {
    const s = await call('/admin/stats');
    updatePendingBadge(s.pendingBranchSubmissions || 0);
    const items = [
      { label: 'Hồ sơ sân chờ duyệt', value: s.pendingBranchSubmissions || 0, sub: 'Đăng ký cơ sở / sân mới', tone: (s.pendingBranchSubmissions || 0) > 0 ? 'warn' : 'ok', nav: ['submissions', { status: 'PENDING' }] },
      { label: 'Người dùng hoạt động', value: `${s.users.active} / ${s.users.total}`, sub: 'Tài khoản đang ACTIVE', tone: 'ok', nav: ['users', {}] },
      { label: 'Đặt sân đã xác nhận', value: s.bookings.confirmed, sub: 'Đơn hợp lệ trên hệ thống', tone: 'ok', nav: ['bookings', { status: 'CONFIRMED' }] },
      { label: 'Đơn chờ thanh toán / duyệt', value: s.bookings.pending, sub: 'Đang chờ hoàn tất', tone: s.bookings.pending > 0 ? 'warn' : '', nav: ['bookings', { status: 'PENDING_PAYMENT' }] },
      { label: 'Đặt sân đã hủy', value: s.bookings.cancelled, sub: 'Tổng đơn đã hủy', tone: '', nav: ['bookings', { status: 'CANCELLED' }] },
      { label: 'Giao dịch thành công', value: s.payments.count, sub: 'Lượt thanh toán thành công', tone: 'ok', nav: ['payments', { status: 'SUCCEEDED' }] },
      { label: 'Tổng tiền đã thu', value: money(s.payments.paid), sub: 'Tổng giá trị thanh toán', tone: 'ok', nav: ['payments', {}] },
      { label: 'Đã hoàn tiền', value: money(s.payments.refunded), sub: 'Tổng tiền đã hoàn trả', tone: '', nav: ['refunds', { status: 'SUCCEEDED' }] },
      { label: 'Hoàn tiền cần xử lý', value: s.openRefunds, sub: 'Yêu cầu đang mở', tone: s.openRefunds > 0 ? 'warn' : '', nav: ['refunds', {}] },
      { label: 'Tiền đến muộn cần duyệt', value: s.latePaymentsToReview, sub: 'Cần admin kiểm tra', tone: s.latePaymentsToReview > 0 ? 'warn' : '', nav: ['payments', { status: 'NEEDS_REVIEW' }] },
      { label: 'Yêu cầu xóa tài khoản', value: s.pendingDeletions, sub: 'Đang chờ xử lý', tone: s.pendingDeletions > 0 ? 'warn' : '', nav: ['deletions', {}] }
    ];
    view.append(el('div', { class: 'stats' }, items.map(item => {
      const card = el('div', { class: `card stat clickable${item.tone ? ' tone-' + item.tone : ''}` }, [
        el('div', { class: 'stat-top' }, [el('span', { text: item.label }), el('span', { text: '→' })]),
        el('b', { text: String(item.value) }),
        el('span', { text: item.sub })
      ]);
      card.addEventListener('click', () => show(item.nav[0], item.nav[1]));
      return card;
    })));
  },
  async submissions(view, toolbar, state) {
    const sel = filter('Trạng thái hồ sơ', [['', 'Tất cả'], ['PENDING', 'Chờ duyệt'], ['APPROVED', 'Đã duyệt'], ['REJECTED', 'Đã từ chối']],
      status => show('submissions', { status }));
    toolbar.append(el('div', { class: 'toolbar' }, sel));
    toolbar.querySelector('select').value = state.status || '';
    const rows = await call('/admin/submissions' + (state.status ? '?status=' + encodeURIComponent(state.status) : ''));
    const pendingCount = rows.filter(r => r.status === 'PENDING').length;
    if (!state.status || state.status === 'PENDING') updatePendingBadge(pendingCount);
    if (!rows.length) {
      view.append(el('div', { class: 'card' }, el('p', { class: 'muted', style: 'margin:0', text: 'Không có hồ sơ đăng ký sân nào.' })));
      return;
    }
    view.append(el('div', { class: 'sub-cards' }, rows.map(sub => {
      const approveBtn = el('button', { class: 'small', text: '✓ Duyệt & đưa lên server' });
      approveBtn.addEventListener('click', () => {
        const noteIn = el('input', { placeholder: 'Ghi chú cho chủ sân (không bắt buộc)', value: 'Hồ sơ đạt yêu cầu, đã kích hoạt lên hệ thống Anta.' });
        modal('Duyệt hồ sơ lên server', [
          el('p', { text: `Xác nhận duyệt "${sub.name}" (${sub.yards.length} sân con) của ${sub.owner_identifier}? Cơ sở/sân sẽ hiển thị công khai ngay lập tức và tự động cấp quyền Chủ sân.` }),
          el('label', {}, [el('span', { text: 'Ghi chú duyệt' }), noteIn])
        ], { confirmText: 'Duyệt ngay', onConfirm: async () => {
          await act(approveBtn, async () => {
            await call(`/admin/submissions/${sub.id}/approve`, 'POST', { note: noteIn.value.trim() });
            branches = await call('/admin/branches');
            const st = await call('/admin/stats').catch(() => null);
            if (st) updatePendingBadge(st.pendingBranchSubmissions || 0);
          }, `Đã duyệt "${sub.name}" lên server.`);
        } });
      });

      const rejectBtn = el('button', { class: 'small danger', text: 'Từ chối' });
      rejectBtn.addEventListener('click', () => {
        const reasonIn = el('textarea', { rows: 3, placeholder: 'Ví dụ: thiếu ảnh thực tế sân, địa chỉ chưa rõ ràng...' });
        modal('Từ chối hồ sơ đăng ký', [
          el('p', { text: `Từ chối hồ sơ "${sub.name}" của ${sub.owner_identifier}?` }),
          el('label', {}, [el('span', { text: 'Lý do từ chối (bắt buộc)' }), reasonIn])
        ], { confirmText: 'Xác nhận từ chối', danger: true, onConfirm: async () => {
          const reason = reasonIn.value.trim();
          if (!reason) throw new Error('Vui lòng nhập lý do từ chối.');
          await act(rejectBtn, async () => {
            await call(`/admin/submissions/${sub.id}/reject`, 'POST', { reason });
            const st = await call('/admin/stats').catch(() => null);
            if (st) updatePendingBadge(st.pendingBranchSubmissions || 0);
          }, 'Đã từ chối hồ sơ.');
        } });
      });

      const safeImgs = (sub.images || []).filter(u => typeof u === 'string' && (u.startsWith('https://') || u.startsWith('http://')));
      return el('div', { class: 'card sub-card' }, [
        el('div', { class: 'sub-head' }, [
          el('div', {}, [
            el('h3', { class: 'sub-title', text: sub.name }),
            el('div', { class: 'sub-meta' }, [
              el('span', { text: sub.submission_type === 'ADD_YARDS' ? `Thêm sân vào: ${sub.target_branch_name || sub.name}` : 'Đăng ký cơ sở mới' }),
              el('span', { text: `Chủ hồ sơ: ${sub.owner_name} (${sub.owner_identifier})` }),
              el('span', { text: `Gửi lúc ${time(sub.created_at)}` })
            ])
          ]),
          el('div', { class: 'actions' }, [tag(sub.status), ...(sub.status === 'PENDING' ? [approveBtn, rejectBtn] : [])])
        ]),
        el('div', { class: 'sub-grid' }, [
          el('div', { style: 'display:grid;gap:10px' }, [
            el('div', {}, [el('strong', { text: 'Địa chỉ & giờ mở cửa: ' }), el('span', { text: `${sub.address} · ${String(sub.opening_hour).padStart(2, '0')}:00–${String(sub.closing_hour).padStart(2, '0')}:00 (${sub.lat}, ${sub.lng})` })]),
            sub.description ? el('div', {}, [el('strong', { text: 'Mô tả: ' }), el('span', { class: 'muted', text: sub.description })]) : null,
            el('div', {}, [
              el('div', { style: 'font-weight:700;margin-bottom:6px', text: `Danh sách sân con (${sub.yards.length})` }),
              el('div', { class: 'yard-chips' }, sub.yards.map(y => el('span', { class: 'yard-chip', text: `${y.name} · ${y.sport_name} · ${money(y.hourly_price)}/h` })))
            ]),
            sub.rules?.length ? el('div', {}, [
              el('div', { style: 'font-weight:700;margin-bottom:4px', text: 'Nội quy' }),
              el('ul', { class: 'sub-rules' }, sub.rules.map(r => el('li', { text: r })))
            ]) : null,
            sub.review_note ? el('div', { class: 'muted', style: 'font-size:12.5px', text: `Ghi chú duyệt: ${sub.review_note}${sub.reviewed_at ? ' (' + time(sub.reviewed_at) + ')' : ''}` }) : null
          ]),
          safeImgs.length
            ? el('div', {}, [
                el('div', { style: 'font-weight:700;margin-bottom:8px', text: `Hình ảnh (${safeImgs.length})` }),
                el('div', { class: 'sub-photos' }, safeImgs.map(u => el('img', { src: u, alt: sub.name })))
              ])
            : el('p', { class: 'muted', style: 'margin:0', text: 'Chủ sân chưa đính kèm ảnh.' })
        ])
      ]);
    })));
  },
  async users(view, toolbar, state) {
    const input = el('input', { placeholder: 'Email, SĐT, tên hoặc ID', value: state.q || '' });
    toolbar.append(el('form', { class: 'toolbar', on: { submit: event => { event.preventDefault(); show('users', { q: input.value.trim() }); } } },
      [el('label', {}, [el('span', { text: 'Tìm kiếm người dùng' }), input]), el('button', { type: 'submit', text: 'Tìm kiếm' }),
        ...(state.q ? [el('button', { type: 'button', class: 'ghost', text: 'Xóa lọc', on: { click: () => show('users', {}) } })] : [])]));
    const rows = await call('/admin/users' + (state.q ? '?q=' + encodeURIComponent(state.q) : ''));
    view.append(table([
      { title: 'Tài khoản', render: r => el('strong', { text: r.identifier }) },
      { title: 'Tên hiển thị', render: r => r.display_name },
      { title: 'Trạng thái', render: r => tag(r.status) },
      { title: 'Quyền hiện tại', wrap: true, render: r => r.roles.length ? el('div', { class: 'actions' }, r.roles.map(role => {
        const branch = branches.find(b => b.id === role.branchId);
        const button = el('button', { class: 'small danger', title: 'Thu hồi quyền', text: `${role.role}${branch ? ' · ' + branch.name : ''} ✕` });
        button.addEventListener('click', () => modal('Thu hồi quyền', [
          el('p', { text: `Xác nhận thu hồi quyền "${role.role}"${branch ? ` tại ${branch.name}` : ''} của ${r.identifier}?` })
        ], { confirmText: 'Thu hồi', danger: true, onConfirm: () => act(button, () => call('/admin/roles', 'DELETE', { userId: r.id, role: role.role, ...(role.branchId ? { branchId: role.branchId } : {}) }), 'Đã thu hồi quyền.') }));
        return button;
      })) : el('span', { class: 'muted', text: 'Người dùng thường' }) },
      { title: 'Cấp quyền mới', render: r => {
        if (r.status !== 'ACTIVE') return '—';
        const role = el('select', {}, ['admin', 'support', 'branch_owner', 'branch_staff'].map(name => el('option', { value: name, text: name })));
        const branch = el('select', {}, [el('option', { value: '', text: '(toàn hệ thống)' }), ...branches.map(b => el('option', { value: b.id, text: b.name }))]);
        const button = el('button', { class: 'small', text: 'Cấp' });
        button.addEventListener('click', () => act(button, () => call('/admin/roles', 'POST',
          { userId: r.id, role: role.value, ...(branch.value ? { branchId: branch.value } : {}) }), 'Đã cấp quyền.'));
        return el('div', { class: 'grant-row' }, [role, branch, button]);
      } },
      { title: 'Tạo lúc', render: r => time(r.created_at) }], rows));
  },
  async bookings(view, toolbar, state) {
    const sel = filter('Trạng thái đơn', [['', 'Tất cả'], ['PENDING_PAYMENT', 'Chờ thanh toán'], ['PENDING_OWNER_CONFIRMATION', 'Chờ chủ sân duyệt'], ['CONFIRMED', 'Đã xác nhận'], ['CANCELLED', 'Đã hủy'], ['EXPIRED', 'Hết hạn']],
      status => show('bookings', { status }));
    toolbar.append(el('div', { class: 'toolbar' }, sel));
    toolbar.querySelector('select').value = state.status || '';
    const rows = await call('/admin/bookings' + (state.status ? '?status=' + state.status : ''));
    view.append(table([{ title: 'Mã đơn', render: r => el('code', { text: short(r.id) }) }, { title: 'Khách', render: r => r.identifier }, { title: 'Chi nhánh', render: r => r.branch },
      { title: 'Sân', render: r => r.yard }, { title: 'Bắt đầu', render: r => time(r.starts_at) }, { title: 'Kết thúc', render: r => time(r.ends_at) },
      { title: 'Số tiền', render: r => el('strong', { text: money(r.amount) }) }, { title: 'Trạng thái', render: r => tag(r.status) }, { title: 'Tạo lúc', render: r => time(r.created_at) }], rows));
  },
  async payments(view, toolbar, state) {
    const sel = filter('Trạng thái giao dịch', [['', 'Tất cả'], ['NEEDS_REVIEW', 'Tiền đến muộn'], ['SUCCEEDED', 'Thành công'], ['CREATED', 'Đang chờ'], ['EXPIRED', 'Hết hạn']],
      status => show('payments', { status }));
    toolbar.append(el('div', { class: 'toolbar' }, sel));
    toolbar.querySelector('select').value = state.status || '';
    const rows = await call('/admin/payment-intents' + (state.status ? '?status=' + state.status : ''));
    view.append(table([{ title: 'Mã đơn', render: r => el('code', { text: r.order_code || short(r.id) }) }, { title: 'Khách', render: r => r.identifier }, { title: 'Cổng', render: r => r.provider },
      { title: 'Loại', render: r => r.target }, { title: 'Số tiền', render: r => el('strong', { text: money(r.amount) }) }, { title: 'Trạng thái', render: r => tag(r.status) },
      { title: 'Hoàn tiền', render: r => {
        if (r.refund_status) return tag(r.refund_status);
        if (r.status !== 'NEEDS_REVIEW') return '—';
        const button = el('button', { class: 'small', text: 'Hoàn 100%' });
        button.addEventListener('click', () => modal('Xác nhận hoàn tiền 100%', [
          el('p', { text: `Tạo lệnh hoàn ${money(r.amount)} cho tài khoản ${r.identifier}?` })
        ], { confirmText: 'Hoàn 100%', onConfirm: () => act(button, () => call(`/admin/payment-intents/${r.id}/refund`, 'POST'), 'Đã tạo lệnh hoàn tiền.') }));
        return button;
      } }, { title: 'Cập nhật', render: r => time(r.updated_at) }], rows));
  },
  async refunds(view, toolbar, state) {
    const sel = filter('Trạng thái hoàn tiền', [['', 'Tất cả'], ['MANUAL_REVIEW', 'Cần chuyển tay'], ['PENDING', 'Đang gửi cổng'], ['FAILED', 'Thất bại'], ['SUCCEEDED', 'Đã hoàn']],
      status => show('refunds', { status }));
    toolbar.append(el('div', { class: 'toolbar' }, sel));
    toolbar.querySelector('select').value = state.status || '';
    const rows = await call('/admin/refunds' + (state.status ? '?status=' + state.status : ''));
    view.append(table([{ title: 'Mã', render: r => el('code', { text: short(r.id) }) }, { title: 'Mã đơn', render: r => r.order_code || '—' }, { title: 'Cổng', render: r => r.provider },
      { title: 'Số tiền', render: r => `${money(r.amount)} (${r.percent}%)` }, { title: 'Lý do', wrap: true, render: r => r.reason },
      { title: 'Trạng thái', render: r => tag(r.status) }, { title: 'Mã tham chiếu', render: r => r.provider_ref || '—' },
      { title: 'Xử lý', render: r => {
        if (r.status === 'SUCCEEDED') return '—';
        const done = el('button', { class: 'small', text: 'Đã chuyển tiền' }), fail = el('button', { class: 'small danger', text: 'Thất bại' });
        done.addEventListener('click', () => {
          const refInput = el('input', { placeholder: 'Ví dụ: FT26330123456' });
          modal('Ghi nhận đã chuyển tiền', [
            el('p', { text: `Khoản hoàn ${money(r.amount)} cho đơn ${r.order_code || short(r.id)}.` }),
            el('label', {}, [el('span', { text: 'Mã giao dịch chuyển khoản hoàn tiền' }), refInput])
          ], { confirmText: 'Xác nhận đã chuyển', onConfirm: async () => {
            const ref = refInput.value.trim();
            if (!ref) throw new Error('Vui lòng nhập mã giao dịch tham chiếu.');
            await act(done, () => call(`/admin/refunds/${r.id}/resolve`, 'POST', { outcome: 'SUCCEEDED', providerRef: ref }), 'Đã ghi nhận hoàn tiền.');
          } });
        });
        fail.addEventListener('click', () => modal('Đánh dấu thất bại', [
          el('p', { text: `Đánh dấu yêu cầu hoàn tiền ${short(r.id)} là thất bại?` })
        ], { confirmText: 'Đánh dấu thất bại', danger: true, onConfirm: () => act(fail, () => call(`/admin/refunds/${r.id}/resolve`, 'POST', { outcome: 'FAILED' }), 'Đã đánh dấu thất bại.') }));
        return el('div', { class: 'actions' }, r.status === 'FAILED' ? [done] : [done, fail]);
      } }, { title: 'Tạo lúc', render: r => time(r.created_at) }], rows));
  },
  async deletions(view) {
    const rows = await call('/admin/deletion-requests');
    view.append(table([{ title: 'Người dùng', render: r => el('code', { text: short(r.user_id) }) }, { title: 'Trạng thái', render: r => tag(r.status) },
      { title: 'Yêu cầu lúc', render: r => time(r.requested_at) }, { title: 'Xóa dữ liệu sau', render: r => time(r.purge_after) },
      { title: 'Đã xóa lúc', render: r => time(r.completed_at) },
      { title: 'Đã xóa', wrap: true, render: r => r.purge_summary ? Object.entries(r.purge_summary).filter(([, n]) => n).map(([k, n]) => `${k}: ${n}`).join(', ') || 'không có dữ liệu' : '—' }], rows));
  },
  async audit(view) {
    const rows = await call('/admin/audit-events');
    view.append(table([{ title: '#', render: r => String(r.id) }, { title: 'Thời gian', render: r => time(r.created_at) }, { title: 'Người thực hiện', render: r => el('code', { text: short(r.actor_id) }) },
      { title: 'Hành động', render: r => el('code', { text: r.action }) }, { title: 'Đối tượng', render: r => `${r.target_type} ${short(r.target_id)}` },
      { title: 'Chi tiết', wrap: true, render: r => JSON.stringify(r.details) }], rows));
  }
};

let current = 'overview', currentState = {};
function updatePendingBadge(count) {
  const btn = $('tabs').querySelector('[data-view="submissions"]');
  if (!btn) return;
  const old = btn.querySelector('.badge');
  if (old) old.remove();
  if (count > 0) btn.append(el('span', { class: 'badge', text: String(count) }));
}
function closeDrawer() {
  $('sidebar').classList.remove('open');
  $('backdrop').hidden = true;
}

async function show(name, state) {
  current = name; currentState = state || (name === current ? currentState : {});
  for (const button of $('tabs').children) {
    button.toggleAttribute('aria-current', false);
    if (button.dataset.view === name) button.setAttribute('aria-current', 'page');
  }
  const meta = TAB_META[name] || TAB_META.overview;
  $('page-title').textContent = meta.title;
  $('page-sub').textContent = meta.sub;
  const view = $('view'), toolbar = $('toolbar');
  view.replaceChildren(window.AntaMotion ? window.AntaMotion.skeletonNode() : el('div', { class: 'card' }, el('p', { class: 'muted', style: 'margin:0', text: 'Đang tải dữ liệu…' })));
  toolbar.replaceChildren();
  try {
    const fresh = document.createDocumentFragment();
    await views[name](fresh, toolbar, currentState);
    view.replaceChildren(fresh);
    if (window.AntaMotion) window.AntaMotion.animateIn(view);
  } catch (error) { view.replaceChildren(); notify(error.message, true); }
}

function signOut() { store.clear(); $('app').hidden = true; $('login').hidden = false; }
async function start() {
  try {
    const me = await call('/users/me');
    branches = await call('/admin/branches');
    $('who').textContent = me.identifier;
    $('who-avatar').textContent = (me.displayName || me.identifier || 'A').trim().charAt(0).toUpperCase();
    $('login').hidden = true; $('app').hidden = false; notify('');
    const stats = await call('/admin/stats').catch(() => null);
    if (stats) updatePendingBadge(stats.pendingBranchSubmissions || 0);
    await show('overview', {});
  } catch (error) { signOut(); $('login-error').textContent = store.get('tried') ? error.message : ''; }
}

$('tabs').append(...Object.entries(TAB_META).map(([name, meta]) => el('button', {
  'data-view': name,
  on: { click: () => { closeDrawer(); notify(''); show(name, {}); } }
}, [el('span', { class: 'nav-label' }, [svgIcon(meta.icon), el('span', { text: meta.title })])])));

$('refresh-btn').addEventListener('click', () => { notify(''); show(current, currentState); });
$('menu-toggle').addEventListener('click', () => { $('sidebar').classList.add('open'); $('backdrop').hidden = false; });
$('backdrop').addEventListener('click', closeDrawer);
$('toggle-pw').addEventListener('click', () => {
  const pw = $('pw-input');
  const visible = pw.type === 'password';
  pw.type = visible ? 'text' : 'password';
  $('toggle-pw').textContent = visible ? 'Ẩn' : 'Hiện';
});
$('fill-demo').addEventListener('click', () => {
  $('login-form').identifier.value = 'admin@anta.vn';
  $('login-form').password.value = 'anta123456';
});
$('logout').addEventListener('click', async () => { try { await call('/auth/logout', 'POST'); } catch { /* session already gone */ } signOut(); });
$('login-form').addEventListener('submit', async event => {
  event.preventDefault(); $('login-error').textContent = '';
  const form = new FormData(event.target);
  try {
    const tokens = await call('/public/auth/login', 'POST', { identifier: form.get('identifier'), password: form.get('password'), deviceId: 'admin-portal' });
    store.set('access', tokens.accessToken); store.set('refresh', tokens.refreshToken); store.set('tried', '1'); event.target.reset();
    await start();
    if ($('app').hidden) $('login-error').textContent = 'Tài khoản này không có quyền quản trị.';
  } catch (error) { $('login-error').textContent = error.message; }
});
if (store.get('access')) start(); else $('login').hidden = false;
