const state = {
  token: localStorage.getItem('access_token') || '',
  refreshToken: localStorage.getItem('refresh_token') || '',
  inventorySessionId: null,
  role: null,
};
const publicPaths = new Set(['/login/', '/403/', '/404/', '/500/', '/501/', '/503/']);
let refreshPromise = null;
const themeKey = 'ui_theme';
const colorThemeKey = 'ui_color_theme';

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function getEl(id) {
  return document.getElementById(id);
}

const labelMap = {
  actionType: {
    issue: 'Выдача',
    return: 'Возврат',
    move: 'Перемещение',
    repair: 'Ремонт',
    write_off: 'Списание',
  },
  status: {
    in_stock: 'На складе',
    issued: 'Выдано',
    in_repair: 'В ремонте',
    written_off: 'Списано',
  },
  notificationKind: {
    overdue: 'Просрочка',
    repair: 'Нужен ремонт',
    info: 'Информация',
  },
};

function mapLabel(map, value) {
  if (!value) return '';
  return map[value] || value;
}

function setStatus(message) {
  const statusEl = getEl('login-status');
  if (statusEl) statusEl.textContent = message;
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const toggle = getEl('theme-toggle');
  if (toggle) {
    toggle.innerHTML = theme === 'dark'
      ? '<i class="fa-regular fa-sun"></i>'
      : '<i class="fa-regular fa-moon"></i>';
  }
}

function applyColorTheme(colorTheme) {
  const link = document.getElementById('theme-stylesheet');
  if (!link) return;
  const href = colorTheme === 'purple'
    ? '/static/rt-purple-theme.css?v=18'
    : '/static/rt-theme.css?v=18';
  link.setAttribute('href', href);
  const toggle = getEl('color-toggle');
  if (toggle) {
    toggle.setAttribute(
      'title',
      colorTheme === 'purple' ? 'Фиолетовая тема' : 'Оранжевая тема'
    );
  }
}

function initThemeToggle() {
  const saved = localStorage.getItem(themeKey);
  const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initial = saved || (systemPrefersDark ? 'dark' : 'light');
  applyTheme(initial);
  const toggle = getEl('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      localStorage.setItem(themeKey, next);
      applyTheme(next);
    });
  }
  if (!saved && window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (event) => {
      const next = event.matches ? 'dark' : 'light';
      applyTheme(next);
    });
  }
}

function initColorToggle() {
  const saved = localStorage.getItem(colorThemeKey) || 'orange';
  applyColorTheme(saved);
  const toggle = getEl('color-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = localStorage.getItem(colorThemeKey) || 'orange';
      const next = current === 'purple' ? 'orange' : 'purple';
      localStorage.setItem(colorThemeKey, next);
      applyColorTheme(next);
    });
  }
}

function initPasswordToggles() {
  const buttons = document.querySelectorAll('[data-toggle="password"]');
  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.closest('.input-group')?.querySelector('input[type="password"], input[type="text"]');
      const icon = button.querySelector('.password-icon');
      if (!input) return;
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      if (icon) {
        icon.innerHTML = showing
          ? '<i class="fa-regular fa-eye-slash"></i>'
          : '<i class="fa-regular fa-eye"></i>';
      }
      button.classList.toggle('btn-outline-secondary', showing);
      button.classList.toggle('btn-outline-primary', !showing);
    });
  });
}

async function apiRequest(url, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  options.headers = headers;
  let response = await fetch(url, options);
  if (response.status === 401 && !options._retry && state.refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      options._retry = true;
      return apiRequest(url, options);
    }
  }
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
  let response = await fetch(url, { headers });
  if (response.status === 401 && state.refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetch(url, { headers: { Authorization: `Bearer ${state.token}` } });
    }
  }
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
    if (!getCookie('csrftoken')) {
      await fetch('/login/', { credentials: 'include' });
    }
    const sessionResponse = await fetch('/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(body),
    });
    if (!sessionResponse.ok) {
      const errorText = await sessionResponse.text();
      throw new Error(errorText || 'Session login failed');
    }
    const response = await apiRequest('/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    state.token = response.access;
    state.refreshToken = response.refresh;
    localStorage.setItem('access_token', response.access);
    localStorage.setItem('refresh_token', response.refresh);
    setStatus('Авторизовано');
    await loadCurrentUser();
    await applyRoleGuard();
    applyAuthGuard();
    await loadEquipment();
    await loadNotifications();
    hideLoginModal();
    if (window.location.pathname === '/login/') {
      window.location.href = '/profile/';
    }
  } catch (error) {
    setStatus(`Ошибка авторизации: ${error.message}`);
  }
}

async function refreshAccessToken() {
  if (!state.refreshToken) return false;
  if (refreshPromise) return refreshPromise;
  refreshPromise = fetch('/api/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: state.refreshToken }),
  })
    .then(async (response) => {
      if (!response.ok) return false;
      const data = await response.json();
      state.token = data.access;
      localStorage.setItem('access_token', data.access);
      return true;
    })
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

async function loadEquipment() {
  try {
    const data = await apiRequest('/api/equipment/');
    const tbody = getEl('equipment-list');
    if (!tbody) return;
    tbody.innerHTML = '';
    data.forEach((item) => {
      const row = document.createElement('tr');
      const statusLabel = mapLabel(labelMap.status, item.status);
      row.innerHTML = `
        <td class="text-muted">${item.id}</td>
        <td>${item.name}</td>
        <td>${statusLabel}</td>
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
    const resultEl = getEl('scan-result');
    if (resultEl) {
      const statusLabel = mapLabel(labelMap.status, result.status);
      resultEl.textContent = `Найдено: ${result.name} (${statusLabel})`;
    }
  } catch (error) {
    const resultEl = getEl('scan-result');
    if (resultEl) resultEl.textContent = 'Оборудование не найдено';
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
    const resultEl = getEl('issue-result');
    if (resultEl) resultEl.textContent = 'Выдача зарегистрирована';
    await loadEquipment();
  } catch (error) {
    const resultEl = getEl('issue-result');
    if (resultEl) resultEl.textContent = 'Ошибка выдачи';
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
    const resultEl = getEl('return-result');
    if (resultEl) resultEl.textContent = 'Возврат зарегистрирован';
    await loadEquipment();
    await loadNotifications();
  } catch (error) {
    const resultEl = getEl('return-result');
    if (resultEl) resultEl.textContent = 'Ошибка возврата';
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
    const resultEl = getEl('inventory-result');
    if (resultEl) {
      resultEl.textContent = `Сессия ${response.id} запущена`;
    }
  } catch (error) {
    const resultEl = getEl('inventory-result');
    if (resultEl) resultEl.textContent = 'Ошибка запуска инвентаризации';
  }
}

async function scanInventory() {
  const scanInput = getEl('inventory-scan-id');
  if (!scanInput) return;
  const equipmentId = scanInput.value.trim();
  if (!state.inventorySessionId || !equipmentId) return;
  try {
    const response = await apiRequest(`/api/inventory/${state.inventorySessionId}/scan/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ equipment_id: equipmentId }),
    });
    const resultEl = getEl('inventory-result');
    if (resultEl) {
      resultEl.textContent = `Отсканировано: ${response.scanned_count}`;
    }
  } catch (error) {
    const resultEl = getEl('inventory-result');
    if (resultEl) resultEl.textContent = 'Ошибка сканирования';
  }
}

async function finishInventory() {
  if (!state.inventorySessionId) return;
  try {
    const response = await apiRequest(`/api/inventory/${state.inventorySessionId}/finish/`, {
      method: 'POST',
    });
    const resultEl = getEl('inventory-result');
    if (resultEl) {
      resultEl.textContent =
        `Завершено. Отсутствует: ${response.missing.length}, лишнее: ${response.extra.length}`;
    }
    state.inventorySessionId = null;
  } catch (error) {
    const resultEl = getEl('inventory-result');
    if (resultEl) resultEl.textContent = 'Ошибка завершения';
  }
}

function initScanner() {
  const container = getEl('qr-reader');
  if (!container) return;
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
    container.textContent = 'Камера недоступна';
  });
}

let chart;
async function loadStats() {
  try {
    const stats = await apiRequest('/api/stats/');
    const labels = stats.by_action.map((item) => mapLabel(labelMap.actionType, item.action_type));
    const values = stats.by_action.map((item) => item.count);
    const ctx = getEl('stats-chart');
    if (!ctx) return;
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
    const container = getEl('notifications-list');
    if (!container) return;
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
            ${mapLabel(labelMap.notificationKind, item.kind)}
          </span>
        </div>
      `;
      container.appendChild(li);
    });
  } catch (error) {
    const container = getEl('notifications-list');
    if (container) {
      container.innerHTML = '<li class="list-group-item">Нет данных</li>';
    }
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
    const overdueEl = getEl('overdue-result');
    if (overdueEl) {
      overdueEl.textContent =
        items.length ? `Просрочено: ${items.length}` : 'Просрочек нет';
    }
  } catch (error) {
    const overdueEl = getEl('overdue-result');
    if (overdueEl) overdueEl.textContent = 'Нет доступа к просрочкам';
  }
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js').catch(() => {});
  }
}

function showLoginModal() {
  const modalEl = getEl('loginModal');
  if (!modalEl) return;
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl, { backdrop: 'static', keyboard: false });
  modal.show();
}

function hideLoginModal() {
  const modalEl = getEl('loginModal');
  if (!modalEl) return;
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.hide();
}

function isManagerRole() {
  return ['admin', 'storekeeper'].includes(state.role);
}

async function loadCurrentUser() {
  try {
    const data = await apiRequest('/api/users/me/');
    state.role = data.role;
    const info = getEl('profile-info');
    const roleEl = getEl('profile-role');
    const usernameEl = getEl('profile-username');
    const emailEl = getEl('profile-email');
    if (info) {
      info.textContent = `${data.first_name || ''} ${data.last_name || ''}`.trim() || data.username;
    }
    if (roleEl) roleEl.textContent = data.role;
    if (usernameEl) usernameEl.textContent = data.username;
    if (emailEl) emailEl.textContent = data.email || '—';
    return data;
  } catch (error) {
    state.token = '';
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    applyAuthGuard();
    return null;
  }
}

async function applyRoleGuard() {
  const required = document.body.dataset.requiredRole;
  const isManager = isManagerRole();
  const inventoryNav = getEl('nav-inventory');
  const reportsNav = getEl('nav-reports');
  const homeInventory = getEl('home-inventory');
  const homeReports = getEl('home-reports');
  if (inventoryNav) inventoryNav.classList.toggle('d-none', !isManager);
  if (reportsNav) reportsNav.classList.toggle('d-none', !isManager);
  if (homeInventory) homeInventory.classList.toggle('d-none', !isManager);
  if (homeReports) homeReports.classList.toggle('d-none', !isManager);
  if (required === 'manager' && !isManager) {
    window.location.href = '/';
  }
}

function applyAuthGuard() {
  const path = window.location.pathname;
  const isPublic = publicPaths.has(path);
  const content = getEl('protected-content');
  const navbar = getEl('main-navbar');
  const loginLink = getEl('login-link');
  const logoutButton = getEl('logout-button');
  if (!state.token) {
    if (navbar) navbar.classList.add('d-none');
    if (loginLink) loginLink.classList.remove('d-none');
    if (logoutButton) logoutButton.classList.add('d-none');
    if (!isPublic) {
      window.location.href = '/login/';
      return;
    }
    if (content) content.classList.add('d-none');
    showLoginModal();
    return;
  }
  if (navbar) navbar.classList.remove('d-none');
  if (loginLink) loginLink.classList.add('d-none');
  if (logoutButton) logoutButton.classList.remove('d-none');
  if (content) content.classList.remove('d-none');
}

function logout() {
  fetch('/auth/logout/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
  }).finally(() => {
    state.token = '';
    state.role = null;
    state.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login/';
  });
}

document.querySelectorAll('form[data-login-form]').forEach((form) => {
  form.addEventListener('submit', login);
});
const refreshBtn = getEl('refresh-equipment');
if (refreshBtn) refreshBtn.addEventListener('click', loadEquipment);
const scanBtn = getEl('scan-button');
if (scanBtn) {
  scanBtn.addEventListener('click', () => {
    const manualInput = getEl('manual-qr');
    const value = manualInput ? manualInput.value.trim() : '';
    scanEquipment(value);
  });
}
const statsBtn = getEl('load-stats');
if (statsBtn) statsBtn.addEventListener('click', loadStats);
const issueForm = getEl('issue-form');
if (issueForm) issueForm.addEventListener('submit', issueEquipment);
const returnForm = getEl('return-form');
if (returnForm) returnForm.addEventListener('submit', returnEquipment);
const inventoryStart = getEl('inventory-start-form');
if (inventoryStart) inventoryStart.addEventListener('submit', startInventory);
const inventoryScan = getEl('inventory-scan');
if (inventoryScan) inventoryScan.addEventListener('click', scanInventory);
const inventoryFinish = getEl('inventory-finish');
if (inventoryFinish) inventoryFinish.addEventListener('click', finishInventory);
const reportCsv = getEl('download-report-csv');
if (reportCsv) {
  reportCsv.addEventListener('click', () => {
    apiDownload('/api/reports/?format=csv', 'report.csv');
  });
}
const reportXlsx = getEl('download-report-xlsx');
if (reportXlsx) {
  reportXlsx.addEventListener('click', () => {
    apiDownload('/api/reports/?format=xlsx', 'report.xlsx');
  });
}
const notificationsBtn = getEl('load-notifications');
if (notificationsBtn) notificationsBtn.addEventListener('click', loadNotifications);
const notificationsRead = getEl('mark-notifications-read');
if (notificationsRead) notificationsRead.addEventListener('click', markNotificationsRead);
const overdueBtn = getEl('load-overdue');
if (overdueBtn) overdueBtn.addEventListener('click', loadOverdue);
const logoutButton = getEl('logout-button');
if (logoutButton) logoutButton.addEventListener('click', logout);

if (state.token) {
  setStatus('Авторизовано');
  loadCurrentUser().then(() => {
    applyRoleGuard();
    loadEquipment();
    loadNotifications();
    applyAuthGuard();
    if (window.location.pathname === '/login/') {
      window.location.href = '/profile/';
    }
  });
} else {
  applyAuthGuard();
}
initScanner();
registerServiceWorker();
initPasswordToggles();
initThemeToggle();
initColorToggle();

if (state.refreshToken) {
  setInterval(() => {
    refreshAccessToken();
  }, 9 * 60 * 1000);
}
