'use strict';
/* Motion primitives adapted from Lucian UX/UI Prompt · MIT License (c) 2026 Seokwoooo · https://lucianlabs.dev/uxui-prompt/ */
(function () {
  const reducedMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Global tactile press squish (.is-down) on pointer interactions
  document.addEventListener('pointerdown', e => {
    const btn = e.target && e.target.closest ? e.target.closest('button') : null;
    if (btn && !btn.disabled && e.button === 0) btn.classList.add('is-down');
  });
  const clearDown = () => document.querySelectorAll('button.is-down').forEach(b => b.classList.remove('is-down'));
  document.addEventListener('pointerup', clearDown);
  document.addEventListener('pointercancel', clearDown);

  // Stackable bottom-right toast region (adapted from 435-toast)
  let region = null;
  let toastQueue = [];
  let hovered = false;

  function ensureRegion() {
    if (region && region.isConnected) return region;
    region = document.createElement('section');
    region.className = 'ux-toast-region';
    region.setAttribute('aria-label', 'Thông báo');
    region.addEventListener('mouseenter', () => { hovered = true; region.classList.add('is-paused'); layoutToasts(); pauseTimers(true); });
    region.addEventListener('mouseleave', () => { hovered = false; region.classList.remove('is-paused'); layoutToasts(); pauseTimers(false); });
    document.body.appendChild(region);
    return region;
  }

  function layoutToasts() {
    const live = toastQueue.filter(t => !t.gone);
    let offsetY = 0;
    live.slice().reverse().forEach((t, idx) => {
      const h = t.el.offsetHeight || 54;
      const y = hovered ? -offsetY : -idx * 10;
      const s = hovered ? 1 : Math.max(0.86, 1 - idx * 0.05);
      t.el.style.setProperty('--ux-y', `${y}px`);
      t.el.style.setProperty('--ux-s', s.toFixed(3));
      t.el.style.setProperty('--ux-o', idx < 3 ? '1' : '0');
      t.el.style.zIndex = String(30 - idx);
      t.el.classList.toggle('is-back', !hovered && idx > 0);
      offsetY += h + 8;
    });
  }

  function pauseTimers(pause) {
    const now = Date.now();
    for (const t of toastQueue) {
      if (t.gone) continue;
      if (pause) {
        clearTimeout(t.timer);
        t.remaining = Math.max(400, t.endsAt - now);
      } else {
        t.endsAt = now + (t.remaining || 3000);
        t.timer = setTimeout(() => dismissToast(t), t.remaining || 3000);
      }
    }
  }

  function dismissToast(entry) {
    if (entry.gone) return;
    entry.gone = true;
    clearTimeout(entry.timer);
    entry.el.style.setProperty('--ux-y', '18px');
    entry.el.style.setProperty('--ux-o', '0');
    layoutToasts();
    setTimeout(() => {
      entry.el.remove();
      toastQueue = toastQueue.filter(t => t !== entry);
    }, reducedMotion() ? 10 : 280);
  }

  function makeIconSvg(isBad) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', isBad ? 'M7 7l10 10M17 7L7 17' : 'M5.5 12.5l4.5 4.5 8.5-9.5');
    svg.appendChild(path);
    return svg;
  }

  function toast(message, isBad = false) {
    if (!message) return;
    const host = ensureRegion();
    const card = document.createElement('div');
    card.className = 'ux-toast is-pre' + (isBad ? ' is-bad' : '');
    card.setAttribute('role', 'status');

    const ic = document.createElement('span');
    ic.className = 'ux-toast-ic';
    ic.appendChild(makeIconSvg(isBad));

    const msg = document.createElement('div');
    msg.className = 'ux-toast-msg';
    msg.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'ux-toast-close';
    closeBtn.setAttribute('aria-label', 'Đóng thông báo');
    closeBtn.textContent = '✕';

    const bar = document.createElement('div');
    bar.className = 'ux-toast-bar';
    bar.appendChild(document.createElement('i'));

    card.append(ic, msg, closeBtn, bar);
    host.appendChild(card);

    const entry = { el: card, gone: false, remaining: 4200, endsAt: Date.now() + 4200, timer: 0 };
    closeBtn.addEventListener('click', () => dismissToast(entry));
    toastQueue.push(entry);
    if (toastQueue.length > 4) dismissToast(toastQueue[0]);

    requestAnimationFrame(() => {
      card.classList.remove('is-pre');
      layoutToasts();
    });
    if (!hovered) {
      entry.timer = setTimeout(() => dismissToast(entry), entry.remaining);
    }
  }

  // Morph async action buttons: idle -> spinning -> mint checkmark -> idle (adapted from 438-loading-button)
  async function runButtonAction(button, work) {
    if (!button) return work();
    if (!button.querySelector('.ux-btn-label')) {
      const lbl = document.createElement('span');
      lbl.className = 'ux-btn-label';
      while (button.firstChild) lbl.appendChild(button.firstChild);
      const sp = document.createElement('i');
      sp.className = 'ux-btn-spin';
      sp.setAttribute('aria-hidden', 'true');
      const ck = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      ck.setAttribute('class', 'ux-btn-check');
      ck.setAttribute('viewBox', '0 0 24 24');
      ck.setAttribute('aria-hidden', 'true');
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', 'm5.5 12.5 4.5 4.5 8.5-9.5');
      ck.appendChild(path);
      button.append(lbl, sp, ck);
    }

    button.disabled = true;
    button.dataset.motion = 'busy';
    try {
      const result = await work();
      if (button.isConnected) {
        button.dataset.motion = 'ok';
        setTimeout(() => {
          if (button.isConnected) delete button.dataset.motion;
        }, reducedMotion() ? 60 : 850);
      }
      return result;
    } catch (err) {
      if (button.isConnected) delete button.dataset.motion;
      throw err;
    } finally {
      if (button.isConnected) button.disabled = false;
    }
  }

  // Shimmer skeleton placeholder (adapted from 439-skeleton-cards)
  function skeletonNode() {
    const wrap = document.createElement('div');
    wrap.className = 'ux-sk-wrap';

    const stats = document.createElement('div');
    stats.className = 'ux-sk-stats';
    for (let i = 0; i < 4; i++) {
      const c = document.createElement('div');
      c.className = 'ux-sk-card';
      const l1 = document.createElement('i'); l1.className = 'ux-sk-line sm';
      const l2 = document.createElement('i'); l2.className = 'ux-sk-line lg';
      c.append(l1, l2);
      stats.appendChild(c);
    }

    const tableSk = document.createElement('div');
    tableSk.className = 'ux-sk-card';
    for (let i = 0; i < 4; i++) {
      const row = document.createElement('i');
      row.className = 'ux-sk-line ' + (i === 0 ? 'sm' : 'md');
      tableSk.appendChild(row);
    }
    wrap.append(stats, tableSk);
    return wrap;
  }

  // Staggered entrance on newly rendered view content
  function animateIn(root) {
    if (!root || reducedMotion()) return;
    const targets = root.querySelectorAll('.card, .stat, .sub-card, .table-wrap, tbody tr');
    let idx = 0;
    targets.forEach(el => {
      if (idx > 14) return;
      el.style.setProperty('--ux-i', String(idx++));
      el.classList.add('ux-anim-in');
    });
  }

  // Smooth modal exit animation before DOM removal (adapted from 436-confirm-modal)
  function closeModal(backdrop) {
    if (!backdrop || !backdrop.isConnected) return;
    if (reducedMotion()) { backdrop.remove(); return; }
    backdrop.classList.add('is-leaving');
    setTimeout(() => backdrop.remove(), 220);
  }

  window.AntaMotion = { toast, runButtonAction, skeletonNode, animateIn, closeModal };
})();
