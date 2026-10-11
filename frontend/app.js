const state = { month: null, summary: null, patterns: null, rows: [] };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const money = (value) => `¥${Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })}`;
const signedMoney = (value) => `${Number(value || 0) >= 0 ? '+' : '−'}${money(Math.abs(Number(value || 0)))}`;
const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[char]));

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `请求失败 (${response.status})`);
  return response.json();
}

function showToast(message, error = false) {
  const toast = $('#toast'); toast.textContent = message; toast.className = `toast show${error ? ' error' : ''}`;
  window.clearTimeout(showToast.timer); showToast.timer = window.setTimeout(() => { toast.className = 'toast'; }, 3000);
}

function renderMetrics(data) {
  const m = data.metrics;
  const change = m.expense_change == null ? '首个完整月份' : `${m.expense_change >= 0 ? '较上月增加' : '较上月减少'} ${Math.abs(m.expense_change).toFixed(1)}%`;
  const changeClass = m.expense_change > 0 ? 'up' : 'down';
  $('#metric-grid').innerHTML = [
    ['INCOME', money(m.income), '本月到账', 'neutral'],
    ['EXPENSE', money(m.expense), change, changeClass],
    ['BALANCE', signedMoney(m.balance), `储蓄率 ${m.saving_rate.toFixed(1)}%`, m.balance >= 0 ? 'down' : 'up'],
    ['RECORDS', `${m.records}`, '笔账单已整理', 'neutral'],
  ].map(([label, value, note, cls]) => `<article class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-note ${cls}">${note}</div></article>`).join('');
}

function renderTrend(rows) {
  const el = $('#trend-chart');
  if (!rows.length) { el.innerHTML = '<div class="empty">暂无趋势数据</div>'; return; }
  const width = 760, height = 286, pad = { left: 42, right: 14, top: 20, bottom: 30 };
  const max = Math.max(...rows.map((r) => Math.max(r.income, r.expense, Math.abs(r.running_balance))), 1);
  const x = (i) => pad.left + (rows.length === 1 ? (width - pad.left - pad.right) / 2 : i * (width - pad.left - pad.right) / (rows.length - 1));
  const y = (v) => pad.top + (1 - v / max) * (height - pad.top - pad.bottom);
  const line = rows.map((r, i) => `${x(i)},${y(r.running_balance)}`).join(' ');
  const area = `${x(0)},${height - pad.bottom} ${line} ${x(rows.length - 1)},${height - pad.bottom}`;
  const grid = [0, .5, 1].map((tick) => `<line class="gridline" x1="${pad.left}" x2="${width-pad.right}" y1="${y(max*tick)}" y2="${y(max*tick)}"/><text class="chart-label" x="3" y="${y(max*tick)+4}">${money(max*tick)}</text>`).join('');
  const bars = rows.map((r, i) => { const barW = Math.min(24, (width-pad.left-pad.right) / rows.length * .35); return `<rect class="expense-bar" x="${x(i)-barW/2}" y="${y(r.expense)}" width="${barW}" height="${height-pad.bottom-y(r.expense)}" rx="3"/><text class="chart-label" text-anchor="middle" x="${x(i)}" y="${height-5}">${r.month.slice(5)}</text>`; }).join('');
  const points = rows.map((r, i) => `<circle class="chart-point" cx="${x(i)}" cy="${y(r.running_balance)}" r="3.5"/>`).join('');
  el.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"><defs><linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#14786c" stop-opacity=".20"/><stop offset="1" stop-color="#14786c" stop-opacity="0"/></linearGradient></defs>${grid}<polygon class="trend-area" points="${area}"/><g>${bars}</g><polyline class="trend-line" points="${line}"/>${points}</svg>`;
}

function renderInsights(items, metrics) {
  $('#insight-stack').innerHTML = items.length ? items.map((item) => `<div class="insight ${item.tone}"><div class="insight-title">${escapeHtml(item.title)}</div><div class="insight-body">${escapeHtml(item.body)}</div></div>`).join('') : '<div class="empty">这个月还没有足够的信号。</div>';
  const score = Math.max(8, Math.min(100, Math.round(metrics.saving_rate + 55 - Math.max(0, metrics.expense_change || 0) * .35)));
  $('#health-index').textContent = `${score} / 100`; $('#health-bar').style.width = `${score}%`;
}

function renderCategories(categories, total) {
  const colors = ['#14786c','#c98d3d','#3b728b','#9da89a'];
  const stops = []; let cursor = 0;
  categories.forEach((cat, i) => { const end = cursor + cat.share; stops.push(`${colors[i % colors.length]} ${cursor}% ${end}%`); cursor = end; });
  $('#category-donut').style.background = `conic-gradient(${stops.join(',') || '#d7d5ca 0 100%'})`;
  $('#donut-total').textContent = money(total);
  $('#category-list').innerHTML = categories.slice(0, 5).map((cat) => `<div class="cat-row"><span class="cat-name">${escapeHtml(cat.name)}</span><span class="cat-bar"><i style="width:${Math.max(5, cat.share)}%"></i></span><span class="cat-amount">${money(cat.amount)}</span></div>`).join('') || '<div class="empty">暂无支出分类</div>';
}

function renderRecent(rows) {
  $('#recent-list').innerHTML = rows.map((row) => `<div class="recent-row"><div class="recent-mark">${row.type === '收入' ? '↗' : '•'}</div><div class="recent-main"><div class="recent-title">${escapeHtml(row.category)} / ${escapeHtml(row.subcategory)}</div><div class="recent-sub">${escapeHtml(row.date)} · ${escapeHtml(row.note)}</div></div><div class="recent-amount ${row.type === '收入' ? 'income' : ''}">${row.type === '收入' ? '+' : '−'}${money(row.amount)}</div></div>`).join('') || '<div class="empty">暂无记录</div>';
}

function renderOverview(data) {
  $('#period-label').textContent = data.month || '—';
  $('#hero-title').innerHTML = `${data.month ? data.month.replace('-', ' / ') : '你的消费'}，<em>有了上下文。</em>`;
  renderMetrics(data); renderTrend(data.trend); renderInsights(data.insights, data.metrics); renderCategories(data.categories, data.metrics.expense); renderRecent(data.recent);
}

function renderPatterns(data) {
  $('#pattern-month').textContent = data.month || '—';
  const max = Math.max(...data.categories.map((x) => x.amount), 1);
  $('#pattern-categories').innerHTML = data.categories.map((cat) => `<div class="bar-item"><span class="bar-name">${escapeHtml(cat.name)}</span><span class="bar-track"><i style="width:${cat.amount/max*100}%"></i></span><span class="bar-value">${money(cat.amount)}</span></div>`).join('') || '<div class="empty">暂无分类</div>';
  const maxWeek = Math.max(...data.weekday.map((x) => x.amount), 1);
  $('#weekday-chart').innerHTML = data.weekday.map((item) => `<div class="weekday-col"><b>${money(item.amount)}</b><i style="height:${Math.max(3, item.amount/maxWeek*175)}px"></i><span>${item.name.slice(1)}</span></div>`).join('');
  $('#subcategory-table').innerHTML = `<table class="ledger-table"><thead><tr><th>一级分类</th><th>二级分类</th><th>笔数</th><th>金额</th></tr></thead><tbody>${data.subcategories.map((row) => `<tr><td>${escapeHtml(row.category)}</td><td class="muted">${escapeHtml(row.subcategory)}</td><td class="muted">${row.records}</td><td>${money(row.amount)}</td></tr>`).join('') || '<tr><td colspan="4">暂无数据</td></tr>'}</tbody></table>`;
}

function renderLedger(rows) {
  state.rows = rows;
  $('#ledger-count').textContent = `${rows.length} 条记录`;
  const query = ($('#ledger-search').value || '').trim().toLowerCase();
  const filtered = rows.filter((row) => [row.date,row.category,row.subcategory,row.note].join(' ').toLowerCase().includes(query));
  $('#ledger-table').innerHTML = `<table class="ledger-table"><thead><tr><th>时间</th><th>分类</th><th>备注</th><th>类型</th><th>金额</th></tr></thead><tbody>${filtered.map((row) => `<tr><td class="muted">${escapeHtml(row.date)}</td><td>${escapeHtml(row.category)} <span class="muted">/ ${escapeHtml(row.subcategory)}</span></td><td class="muted">${escapeHtml(row.note)}</td><td class="${row.type === '收入' ? 'income' : ''}">${row.type}</td><td class="${row.type === '收入' ? 'income' : ''}">${row.type === '收入' ? '+' : '−'}${money(row.amount)}</td></tr>`).join('') || '<tr><td colspan="5">没有匹配的记录</td></tr>'}</tbody></table>`;
}

async function renderDataRoom() {
  const data = await api('/api/data-room'); const m = data.manifest || {};
  $('#data-status').textContent = data.duplicate_ids ? '需要复核' : '校验通过';
  $('#data-status').style.color = data.duplicate_ids ? 'var(--red)' : 'var(--teal)';
  $('#data-cards').innerHTML = [['主表记录', m.rows || 0],['来源文件', (m.source_files || []).length],['覆盖月份', (m.months || []).length],['重复 ID', data.duplicate_ids || 0]].map(([label,value]) => `<div class="data-card"><span>${label}</span><strong>${value}</strong></div>`).join('');
  $('#data-contract').innerHTML = (data.columns || []).map((col, i) => `<div class="contract-item"><strong>${escapeHtml(col)}</strong><span>${i < 3 ? '源字段 · 关键识别' : i < 6 ? '源字段 · 分类与收支' : '源字段 / 派生字段'}</span></div>`).join('');
}

async function loadMonth(month) {
  try { const query = encodeURIComponent(month || ''); const [data, pattern, transactions] = await Promise.all([api(`/api/summary?month=${query}`), api(`/api/patterns?month=${query}`), api(`/api/transactions?month=${query}`)]); state.summary = data; state.patterns = pattern; state.month = data.month; renderOverview(data); renderPatterns(pattern); renderLedger(transactions.rows); $('#month-select').value = data.month; $('#rail-status').textContent = `${data.month} 数据已同步`; } catch (error) { showToast(error.message, true); }
}

function switchView(view) {
  $$('.nav-item').forEach((el) => el.classList.toggle('active', el.dataset.view === view));
  $$('.view').forEach((el) => el.classList.toggle('active-view', el.id === `view-${view}`));
  $('#page-name').textContent = ({ overview:'总览', patterns:'消费模式', ledger:'账单明细', data:'数据室' })[view] || '总览';
  if (view === 'data') renderDataRoom().catch((error) => showToast(error.message, true));
}

async function boot() {
  try {
    const data = await api('/api/summary');
    $('#month-select').innerHTML = data.months.map((month) => `<option value="${month}">${month}</option>`).join('');
    await loadMonth(data.month);
  } catch (error) { $('#rail-status').textContent = '等待数据'; showToast(error.message, true); }
}

$$('.nav-item').forEach((item) => item.addEventListener('click', () => switchView(item.dataset.view)));
$$('[data-jump]').forEach((item) => item.addEventListener('click', () => switchView(item.dataset.jump)));
$('#month-select').addEventListener('change', (event) => loadMonth(event.target.value));
$('#ledger-search').addEventListener('input', () => renderLedger(state.rows));
$('#refresh-button').addEventListener('click', () => loadMonth(state.month).then(() => showToast('数据已刷新')));
$('#upload-button').addEventListener('click', () => $('#file-input').click());
$('#file-input').addEventListener('change', async (event) => {
  const file = event.target.files[0]; if (!file) return;
  const body = new FormData(); body.append('file', file);
  try { showToast('正在导入并重建数据…'); await api('/api/import', { method:'POST', body }); await boot(); showToast('导入完成，数据已重建'); } catch (error) { showToast(error.message, true); }
  event.target.value = '';
});
boot();

