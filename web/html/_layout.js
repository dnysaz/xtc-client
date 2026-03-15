/* _layout.js — session, API helpers, toast, sidebar toggle */

// ── Session ───────────────────────────────────────────────────────────────────
function getSession() {
  try { return JSON.parse(localStorage.getItem('xtc_session') || 'null'); }
  catch { return null; }
}
function requireSession() {
  const s = getSession();
  if (!s) { window.location.href = '/'; return null; }
  return s;
}
function getBase() {
  const s = getSession();
  return s ? `http://${s.ip}:${s.port}` : null;
}
function logout() {
  localStorage.removeItem('xtc_session');
  window.location.href = '/';
}

// ── API ───────────────────────────────────────────────────────────────────────
async function api(method, path, body = null) {
  const base = getBase();
  if (!base) { window.location.href = '/'; throw new Error('No session'); }
  const opts = { method, mode: 'cors', headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(`${base}${path}`, opts);
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}
const GET  = path        => api('GET',  path);
const POST = (path, body) => api('POST', path, body);

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const icons  = { info: 'ℹ️', success: '✅', error: '❌', warn: '⚠️' };
  const colors = { info: '#334155', success: '#15803d', error: '#b91c1c', warn: '#d97706' };
  const el     = Object.assign(document.createElement('div'), {
    innerHTML: `<span>${icons[type]}</span><span style="margin-left:8px">${msg}</span>`,
  });
  Object.assign(el.style, {
    position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
    display: 'flex', alignItems: 'center',
    background: colors[type], color: '#fff',
    padding: '12px 18px', borderRadius: '12px',
    fontSize: '13px', fontWeight: '600',
    boxShadow: '0 8px 24px rgba(0,0,0,.15)',
    transform: 'translateY(16px)', opacity: '0',
    transition: 'all .3s',
  });
  document.body.appendChild(el);
  requestAnimationFrame(() => {
    el.style.transform = 'translateY(0)';
    el.style.opacity   = '1';
  });
  setTimeout(() => {
    el.style.transform = 'translateY(16px)';
    el.style.opacity   = '0';
    setTimeout(() => el.remove(), 300);
  }, 3000);
}

// ── Sidebar toggle (mobile) ────────────────────────────────────────────────────
function openSidebar() {
  document.getElementById('sidebar').style.transform  = 'translateX(0)';
  document.getElementById('overlay').style.display    = 'block';
  document.body.style.overflow = 'hidden';
}
function closeSidebar() {
  if (window.innerWidth >= 1024) return;
  document.getElementById('sidebar').style.transform  = 'translateX(-100%)';
  document.getElementById('overlay').style.display    = 'none';
  document.body.style.overflow = '';
}
window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024) {
    document.getElementById('sidebar').style.transform = '';
    const ov = document.getElementById('overlay');
    if (ov) ov.style.display = 'none';
    document.body.style.overflow = '';
  }
});

// ── Init sidebar user info ────────────────────────────────────────────────────
function initSidebarUser() {
  const s = getSession();
  if (!s) return;
  const nameEl = document.getElementById('sb-user');
  const ipEl   = document.getElementById('sb-ip');
  const avEl   = document.getElementById('sb-avatar');
  if (nameEl) nameEl.textContent = s.user;
  if (ipEl)   ipEl.textContent   = `${s.ip}:${s.port}`;
  if (avEl)   avEl.textContent   = s.user.slice(0, 2).toUpperCase();
}
document.addEventListener('DOMContentLoaded', initSidebarUser);