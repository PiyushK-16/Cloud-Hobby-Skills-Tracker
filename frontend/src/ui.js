// utils: tiny DOM helper. Everything is inserted with textContent => user content can't inject HTML (XSS-safe).
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return el;
}
function toast(msg, err = false) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = err ? 'err' : ''; t.style.display = 'block';
  setTimeout(() => (t.style.display = 'none'), 3000);
}
const guard = fn => async (...a) => { try { return await fn(...a); } catch (e) { toast(e.message, true); } };
function barChart(rows, unit = 'h') {           // rows: [{label, value}]
  const max = Math.max(1, ...rows.map(r => r.value));
  return h('div', { class: 'chart' }, rows.length ? rows.map(r => h('div', { class: 'r' },
    h('span', {}, r.label), h('div', { class: 'bar' }, h('i', { style: `width:${(r.value / max) * 100}%` })), h('span', {}, r.value + unit)))
    : h('p', { class: 'muted' }, 'No data yet.'));
}
function field(label, input) { return h('label', {}, h('small', { class: 'muted' }, label), input); }
function ago(iso) { const s = (Date.now() - new Date(iso)) / 1000; return s < 60 ? 'just now' : s < 3600 ? Math.floor(s / 60) + ' min ago' : s < 86400 ? Math.floor(s / 3600) + ' h ago' : Math.floor(s / 86400) + ' d ago'; }
