const state = {
  token: localStorage.getItem('access_token') || '',
  inventorySessionId: null,
};

function setStatus(message) {
  document.getElementById('login-status').textContent = message;
}

async function apiRequest(url, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  options.headers = headers;
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

async function apiDownload(url, filename) {
  const headers = {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const blob = await response.blob();
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function login(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const body = {
    username: formData.get('username'),
    password: formData.get('password'),
  };
  try {
    const response = await apiRequest('/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    state.token = response.access;
    localStorage.setItem('access_token', response.access);
    setStatus('Авторизовано');
    await loadEquipment();
    await loadNotifications();
  } catch (error) {
    setStatus('Ошибка авторизации');
  }
}

async function loadEquipment() {
  try {
    const data = await apiRequest('/api/equipment/');
    const tbody = document.getElementById('equipment-list');
    tbody.innerHTML = '';
    data.forEach((item) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="text-muted">${item.id}</td>
        <td>${item.name}</td>
        <td>${item.status}</td>
        <td>${item.location_detail ? item.location_detail.name : '-'}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (error) {
    setStatus('Нет доступа к списку оборудования');
  }
}

async function scanEquipment(value) {
  if (!value) return;
  try {
    const result = await apiRequest('/api/scan/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qr_data: value }),
    });
    document.getElementById('scan-result').textContent =
      `Найдено: ${result.name} (${result.status})`;
  } catch (error) {
    document.getElementById('scan-result').textContent = 'Оборудование не найдено';
  }
}

async function issueEquipment(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const dueValue = formData.get('due_at');
  const payload = {
    equipment_id: formData.get('equipment_id'),
    target_user_id: Number(formData.get('target_user_id')),
    notes: formData.get('notes') || '',
    due_at: dueValue ? new Date(dueValue).toISOString() : null,
  };
  try {
    await apiRequest('/api/operations/issue/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    document.getElementById('issue-result').textContent = 'Выдача зарегистрирована';
    await loadEquipment();
  } catch (error) {
    document.getElementById('issue-result').textContent = 'Ошибка выдачи';
  }
}

async function returnEquipment(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const payload = {
    equipment_id: formData.get('equipment_id'),
    condition: formData.get('condition'),
    notes: formData.get('notes') || '',
  };
  try {
    await apiRequest('/api/operations/return/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    document.getElementById('return-result').textContent = 'Возврат зарегистрирован';
    await loadEquipment();
    await loadNotifications();
  } catch (error) {
    document.getElementById('return-result').textContent = 'Ошибка возврата';
  }
}

async function startInventory(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const payload = {};
  const location = formData.get('location');
  if (location) payload.location = Number(location);
  try {
    const response = await apiRequest('/api/inventory/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    state.inventorySessionId = response.id;
    document.getElementById('inventory-result').textContent =
      `Сессия ${response.id} запущена`;
  } catch (error) {
    document.getElementById('inventory-result').textContent = 'Ошибка запуска инвентаризации';
  }
}

async function scanInventory() {
  const equipmentId = document.getElementById('inventory-scan-id').value.trim();
  if (!state.inventorySessionId || !equipmentId) return;
  try {
    const response = await apiRequest(`/api/inventory/${state.inventorySessionId}/scan/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ equipment_id: equipmentId }),
    });
    document.getElementById('inventory-result').textContent =
      `Отсканировано: ${response.scanned_count}`;
  } catch (error) {
    document.getElementById('inventory-result').textContent = 'Ошибка сканирования';
  }
}

async function finishInventory() {
  if (!state.inventorySessionId) return;
  try {
    const response = await apiRequest(`/api/inventory/${state.inventorySessionId}/finish/`, {
      method: 'POST',
    });
    document.getElementById('inventory-result').textContent =
      `Завершено. Отсутствует: ${response.missing.length}, лишнее: ${response.extra.length}`;
    state.inventorySessionId = null;
  } catch (error) {
    document.getElementById('inventory-result').textContent = 'Ошибка завершения';
  }
}

function initScanner() {
  const reader = new Html5Qrcode('qr-reader');
  const config = { fps: 10, qrbox: 200 };
  reader.start(
    { facingMode: 'environment' },
    config,
    (decodedText) => {
      scanEquipment(decodedText);
      reader.stop();
    },
    () => {}
  ).catch(() => {
    document.getElementById('qr-reader').textContent = 'Камера недоступна';
  });
}

let chart;
async function loadStats() {
  try {
    const stats = await apiRequest('/api/stats/');
    const labels = stats.by_action.map((item) => item.action_type);
    const values = stats.by_action.map((item) => item.count);
    const ctx = document.getElementById('stats-chart');
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Операции', data: values }],
      },
    });
  } catch (error) {
    setStatus('Не удалось загрузить статистику');
  }
}

async function loadNotifications() {
  try {
    const list = await apiRequest('/api/notifications/');
    const container = document.getElementById('notifications-list');
    container.innerHTML = '';
    list.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      li.innerHTML = `
        <div class="d-flex justify-content-between">
          <div>
            <strong>${item.title}</strong>
            <div class="text-muted small">${item.message || ''}</div>
          </div>
          <span class="badge text-bg-${item.is_read ? 'secondary' : 'primary'}">
            ${item.kind}
          </span>
        </div>
      `;
      container.appendChild(li);
    });
  } catch (error) {
    document.getElementById('notifications-list').innerHTML = '<li class="list-group-item">Нет данных</li>';
  }
}

async function markNotificationsRead() {
  try {
    await apiRequest('/api/notifications/mark_all_read/', { method: 'POST' });
    await loadNotifications();
  } catch (error) {
    setStatus('Не удалось обновить уведомления');
  }
}

async function loadOverdue() {
  try {
    const response = await apiRequest('/api/notifications/overdue/');
    const items = response.overdue || [];
    document.getElementById('overdue-result').textContent =
      items.length ? `Просрочено: ${items.length}` : 'Просрочек нет';
  } catch (error) {
    document.getElementById('overdue-result').textContent = 'Нет доступа к просрочкам';
  }
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js').catch(() => {});
  }
}

document.getElementById('login-form').addEventListener('submit', login);
document.getElementById('refresh-equipment').addEventListener('click', loadEquipment);
document.getElementById('scan-button').addEventListener('click', () => {
  const value = document.getElementById('manual-qr').value.trim();
  scanEquipment(value);
});
document.getElementById('load-stats').addEventListener('click', loadStats);
document.getElementById('issue-form').addEventListener('submit', issueEquipment);
document.getElementById('return-form').addEventListener('submit', returnEquipment);
document.getElementById('inventory-start-form').addEventListener('submit', startInventory);
document.getElementById('inventory-scan').addEventListener('click', scanInventory);
document.getElementById('inventory-finish').addEventListener('click', finishInventory);
document.getElementById('download-report-csv').addEventListener('click', () => {
  apiDownload('/api/reports/?format=csv', 'report.csv');
});
document.getElementById('download-report-xlsx').addEventListener('click', () => {
  apiDownload('/api/reports/?format=xlsx', 'report.xlsx');
});
document.getElementById('load-notifications').addEventListener('click', loadNotifications);
document.getElementById('mark-notifications-read').addEventListener('click', markNotificationsRead);
document.getElementById('load-overdue').addEventListener('click', loadOverdue);

if (state.token) {
  setStatus('Авторизовано');
  loadEquipment();
  loadNotifications();
}
initScanner();
registerServiceWorker();
