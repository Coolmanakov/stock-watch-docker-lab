const $ = id => document.getElementById(id);
const form = $('product-form');
let editingId = null;
let currentItems = [];
const labels = {critical: 'Ниже порога', warning: 'На пороге', ok: 'Достаточно'};

async function api(path, method = 'GET', body) {
  const response = await fetch('/api/' + path, {
    method, headers: {'Content-Type': 'application/json'},
    ...(body !== undefined ? {body: JSON.stringify(body)} : {})
  });
  if (response.status === 204) return null;
  let data;
  try { data = await response.json(); }
  catch { throw new Error('Сервер недоступен. Проверь docker compose ps и логи.'); }
  if (!response.ok) throw new Error(data.error || 'Ошибка запроса');
  return data;
}

function message(text, error = false) {
  $('message').textContent = text;
  $('message').classList.toggle('error', error);
}
async function action(task) {
  const buttons = [...document.querySelectorAll('button')];
  buttons.forEach(button => button.disabled = true);
  try { await task(); } catch (error) { message(error.message, true); }
  finally { buttons.forEach(button => button.disabled = false); }
}

function resetMetrics() {
  ['total', 'critical', 'warning', 'ok'].forEach(id => $(id).textContent = '—');
}
function render(items, analyzed = false) {
  currentItems = items;
  const rows = $('rows'); rows.replaceChildren();
  if (!items.length) {
    const row = rows.insertRow(); const cell = row.insertCell();
    cell.colSpan = 9; cell.className = 'empty'; cell.textContent = 'Склад пуст. Добавь товар ниже.';
  }
  for (const item of items) {
    const row = rows.insertRow();
    for (const key of ['name', 'quantity', 'daily_usage', 'lead_days', 'safety_stock', 'threshold']) {
      row.insertCell().textContent = item[key] ?? '—';
    }
    const status = row.insertCell();
    if (analyzed) {
      const badge = document.createElement('span');
      badge.className = 'badge ' + item.status; badge.textContent = labels[item.status];
      status.append(badge);
    } else status.textContent = 'Не проверен';
    row.insertCell().textContent = analyzed ? item.recommended_order + ' шт.' : '—';
    const controls = row.insertCell();
    const edit = document.createElement('button'); edit.textContent = 'Изменить';
    edit.addEventListener('click', () => {
      editingId = item.id;
      for (const key of ['name', 'quantity', 'daily_usage', 'lead_days', 'safety_stock']) form.elements.namedItem(key).value = item[key];
      $('form-title').textContent = 'Изменить товар #' + item.id;
      $('cancel-edit').hidden = false; form.scrollIntoView({behavior: 'smooth', block: 'center'});
    });
    const remove = document.createElement('button'); remove.textContent = 'Удалить';
    remove.addEventListener('click', () => {
      if (!confirm('Удалить товар «' + item.name + '»?')) return;
      action(async () => {
        await api('products/' + item.id, 'DELETE');
        if (editingId === item.id) cancelEdit();
        await load(); message('Товар удалён. История прошлых проверок сохранена.');
      });
    });
    controls.append(edit, remove);
  }
  $('table-caption').textContent = analyzed ? 'Снимок склада на момент проверки. Результат сохранён в истории.' : 'Текущие данные из PostgreSQL. Для расчёта нажми «Проверить запасы».';
}

async function load() {
  const data = await api('products'); render(data.items); resetMetrics();
  message('Склад загружен из базы данных: ' + data.items.length + ' товаров.');
}
async function history() {
  const data = await api('analyses'); const list = $('history-list'); list.replaceChildren();
  if (!data.items.length) list.textContent = 'Проверок ещё нет. Нажми «Проверить запасы».';
  for (const item of data.items) {
    const summary = item.result.summary;
    const entry = document.createElement('div'); entry.className = 'history-entry';
    entry.textContent = '#' + item.id + ' · ' + new Date(item.created_at).toLocaleString('ru-RU') + ' · Товаров: ' + summary.total + ' · Ниже порога: ' + summary.critical + ' · На пороге: ' + summary.warning;
    const details = document.createElement('small');
    details.textContent = item.result.items.map(p => p.name + ': ' + p.quantity + ' шт., порог ' + p.threshold + ', заказать ' + p.recommended_order).join(' / ');
    entry.append(details); list.append(entry);
  }
}
function cancelEdit() {
  editingId = null; form.reset(); $('form-title').textContent = 'Добавить товар'; $('cancel-edit').hidden = true;
}
$('load').addEventListener('click', () => action(load));
$('analyze').addEventListener('click', () => action(async () => {
  const data = await api('analysis', 'POST'); render(data.items, true);
  for (const key of ['total', 'critical', 'warning', 'ok']) $(key).textContent = data.summary[key];
  message('Сервис расчёта проверил запасы. Проверка #' + data.id + ' сохранена в PostgreSQL.');
  await history();
}));
$('history').addEventListener('click', () => action(async () => { await history(); message('История загружена из базы данных.'); }));
$('cancel-edit').addEventListener('click', cancelEdit);
form.addEventListener('submit', event => {
  event.preventDefault();
  action(async () => {
    const data = {name: form.elements.namedItem('name').value.trim()};
    for (const key of ['quantity', 'daily_usage', 'lead_days', 'safety_stock']) data[key] = Number(form.elements.namedItem(key).value);
    await api(editingId === null ? 'products' : 'products/' + editingId, editingId === null ? 'POST' : 'PUT', data);
    cancelEdit(); await load(); message('Товар сохранён. Нажми «Проверить запасы», чтобы обновить расчёт.');
  });
});
