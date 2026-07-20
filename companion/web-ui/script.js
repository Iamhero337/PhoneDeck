let pages = [];
let currentPageId = null;
let installedApps = [];
let selectedTilePageId = null;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + type;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3000);
}

async function loadPages() {
  try {
    const data = await api('/api/pages');
    pages = data.pages || [];
    renderSidebar();
    if (currentPageId) {
      const exists = pages.find(p => p.id === currentPageId);
      if (exists) selectPage(currentPageId);
      else if (pages.length > 0) selectPage(pages[0].id);
      else showEmptyState();
    } else if (pages.length > 0) {
      selectPage(pages[0].id);
    } else {
      showEmptyState();
    }
  } catch (e) {
    showToast('Failed to load pages: ' + e.message, 'error');
  }
}

function showEmptyState() {
  document.getElementById('pageName').textContent = 'No pages';
  document.getElementById('tileGrid').innerHTML = '';
  document.getElementById('emptyState').style.display = 'flex';
  document.getElementById('addTileBtn').style.display = 'none';
}

function renderSidebar() {
  const list = document.getElementById('pageList');
  list.innerHTML = pages.map(p => `
    <div class="page-item ${p.id === currentPageId ? 'active' : ''}" onclick="selectPage('${p.id}')">
      <div class="page-label">
        <span class="page-name">${escHtml(p.name)}</span>
        <span class="tile-count">${p.tiles ? p.tiles.length : 0}</span>
      </div>
      <div class="page-actions">
        <button class="edit-btn" onclick="event.stopPropagation();showAddPageModal('${p.id}')" title="Rename">
          <span class="material-symbols-outlined" style="font-size:16px">edit</span>
        </button>
        <button onclick="event.stopPropagation();confirmDeletePage('${p.id}')" title="Delete">
          <span class="material-symbols-outlined" style="font-size:16px">delete</span>
        </button>
      </div>
    </div>
  `).join('');
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function selectPage(pageId) {
  currentPageId = pageId;
  const page = pages.find(p => p.id === pageId);
  if (!page) return;
  renderSidebar();
  document.getElementById('pageName').textContent = page.name;
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('addTileBtn').style.display = 'inline-flex';
  renderTiles(page);
}

function renderTiles(page) {
  const grid = document.getElementById('tileGrid');
  if (!page.tiles || page.tiles.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;padding:40px">
      <span class="material-symbols-outlined empty-icon">widgets</span>
      <p>No tiles yet. Click "Add Tile" to get started.</p>
    </div>`;
    return;
  }
  grid.innerHTML = page.tiles.map(t => {
    const bgColor = t.color ? rgbaFromInt(t.color) : '#1E1E2E';
    const iconColor = t.iconColor ? rgbaFromInt(t.iconColor) : '#4A90D9';
    return `
    <div class="tile-card" style="background:${bgColor}">
      <div class="tile-actions">
        <button class="edit-tile-btn" onclick="event.stopPropagation();editTile('${t.id}')" title="Edit">
          <span class="material-symbols-outlined" style="font-size:14px">edit</span>
        </button>
        <button onclick="event.stopPropagation();confirmDeleteTile('${page.id}','${t.id}')" title="Delete">
          <span class="material-symbols-outlined" style="font-size:14px">delete</span>
        </button>
      </div>
      <div class="tile-icon" style="color:${iconColor}">
        <span class="material-symbols-outlined" style="font-size:32px">${t.icon || 'apps'}</span>
      </div>
      <div class="tile-label">${escHtml(t.label)}</div>
      <div class="tile-command">${escHtml(t.command || '')}</div>
    </div>`;
  }).join('');
}

function rgbaFromInt(colorInt) {
  const unsigned = colorInt < 0 ? colorInt + 4294967296 : colorInt;
  const r = Math.trunc(unsigned / 65536) % 256;
  const g = Math.trunc(unsigned / 256) % 256;
  const b = Math.trunc(unsigned) % 256;
  return `rgba(${r},${g},${b},${1.0})`;
}

function colorToHex(colorInt) {
  const unsigned = colorInt < 0 ? colorInt + 4294967296 : colorInt;
  const r = Math.trunc(unsigned / 65536) % 256;
  const g = Math.trunc(unsigned / 256) % 256;
  const b = Math.trunc(unsigned) % 256;
  return '#' + [r,g,b].map(x => x.toString(16).padStart(2,'0')).join('');
}

function hexToInt(hex) {
  const val = parseInt(hex.slice(1), 16);
  return (0xFF * 16777216) + val;
}

/* Page CRUD */
function showAddPageModal(editId) {
  if (editId) {
    const page = pages.find(p => p.id === editId);
    document.getElementById('pageNameInput').value = page ? page.name : '';
    document.getElementById('pageNameInput').dataset.editId = editId;
  } else {
    document.getElementById('pageNameInput').value = '';
    delete document.getElementById('pageNameInput').dataset.editId;
  }
  document.getElementById('pageModal').style.display = 'flex';
  document.getElementById('pageNameInput').focus();
}

async function savePage() {
  const name = document.getElementById('pageNameInput').value.trim();
  if (!name) return showToast('Page name is required', 'error');
  const editId = document.getElementById('pageNameInput').dataset.editId;
  try {
    if (editId) {
      await api('/api/pages/' + editId, { method: 'PUT', body: JSON.stringify({ name }) });
      showToast('Page renamed', 'success');
    } else {
      await api('/api/pages', { method: 'POST', body: JSON.stringify({ name }) });
      showToast('Page created', 'success');
    }
    closeModalById('pageModal');
    await loadPages();
  } catch (e) {
    showToast('Failed: ' + e.message, 'error');
  }
}

function confirmDeletePage(pageId) {
  const page = pages.find(p => p.id === pageId);
  showConfirm(
    `Delete page "${page ? page.name : ''}" and all its tiles?`,
    async () => {
      try {
        await api('/api/pages/' + pageId, { method: 'DELETE' });
        showToast('Page deleted', 'success');
        await loadPages();
      } catch (e) {
        showToast('Failed: ' + e.message, 'error');
      }
    }
  );
}

/* Tile CRUD */
function showAddTileModal() {
  if (!currentPageId) return;
  selectedTilePageId = currentPageId;
  document.getElementById('tileModalTitle').textContent = 'Add Tile';
  document.getElementById('editTileId').value = '';
  document.getElementById('editTilePageId').value = currentPageId;
  document.getElementById('tileLabel').value = '';
  document.getElementById('tileCommand').value = '';
  document.getElementById('tileIcon').value = 'apps';
  document.getElementById('tileColor').value = '#1e1e2e';
  document.getElementById('tileIconColor').value = '#4a90d9';
  document.getElementById('tileModal').style.display = 'flex';
  document.getElementById('tileLabel').focus();
}

function editTile(tileId) {
  for (const page of pages) {
    const tile = (page.tiles || []).find(t => t.id === tileId);
    if (tile) {
      selectedTilePageId = page.id;
      document.getElementById('tileModalTitle').textContent = 'Edit Tile';
      document.getElementById('editTileId').value = tile.id;
      document.getElementById('editTilePageId').value = page.id;
      document.getElementById('tileLabel').value = tile.label;
      document.getElementById('tileCommand').value = tile.command || '';
      document.getElementById('tileIcon').value = tile.icon || 'apps';
      document.getElementById('tileColor').value = tile.color ? colorToHex(tile.color) : '#1e1e2e';
      document.getElementById('tileIconColor').value = tile.iconColor ? colorToHex(tile.iconColor) : '#4a90d9';
      document.getElementById('tileModal').style.display = 'flex';
      return;
    }
  }
}

async function saveTile() {
  const label = document.getElementById('tileLabel').value.trim();
  const command = document.getElementById('tileCommand').value.trim();
  const icon = document.getElementById('tileIcon').value.trim() || 'apps';
  const color = hexToInt(document.getElementById('tileColor').value);
  const iconColor = hexToInt(document.getElementById('tileIconColor').value);
  const tileId = document.getElementById('editTileId').value;
  const pageId = document.getElementById('editTilePageId').value || selectedTilePageId;

  if (!label) return showToast('Label is required', 'error');
  if (!pageId) return showToast('No page selected', 'error');

  try {
    if (tileId) {
      await api('/api/tiles/' + tileId, {
        method: 'PUT',
        body: JSON.stringify({ label, command, icon, color, iconColor })
      });
      showToast('Tile updated', 'success');
    } else {
      await api('/api/tiles', {
        method: 'POST',
        body: JSON.stringify({ pageId, label, command, icon, color, iconColor })
      });
      showToast('Tile added', 'success');
    }
    closeModalById('tileModal');
    await loadPages();
  } catch (e) {
    showToast('Failed: ' + e.message, 'error');
  }
}

function confirmDeleteTile(pageId, tileId) {
  showConfirm('Delete this tile?', async () => {
    try {
      await api(`/api/tiles/${pageId}/${tileId}`, { method: 'DELETE' });
      showToast('Tile deleted', 'success');
      await loadPages();
    } catch (e) {
      showToast('Failed: ' + e.message, 'error');
    }
  });
}

/* App Picker */
async function showAppPicker() {
  document.getElementById('appPickerModal').style.display = 'flex';
  document.getElementById('appSearch').value = '';
  document.getElementById('appList').innerHTML = '<div style="text-align:center;padding:20px;color:#8888AA">Loading apps...</div>';
  try {
    const data = await api('/api/apps');
    installedApps = data.apps || [];
    renderAppList(installedApps);
  } catch (e) {
    document.getElementById('appList').innerHTML = '<div style="text-align:center;padding:20px;color:#E53935">Failed to load apps: ' + e.message + '</div>';
  }
}

function renderAppList(apps) {
  const list = document.getElementById('appList');
  if (apps.length === 0) {
    list.innerHTML = '<div style="text-align:center;padding:20px;color:#8888AA">No apps found</div>';
    return;
  }
  list.innerHTML = apps.map(a => `
    <div class="app-item" onclick="selectApp('${escHtml(a.name)}','${escHtml(a.command)}')">
      <span class="app-name">${escHtml(a.name)}</span>
      <span class="app-command">${escHtml(a.command)}</span>
    </div>
  `).join('');
}

function filterApps() {
  const q = document.getElementById('appSearch').value.toLowerCase();
  const filtered = installedApps.filter(a =>
    a.name.toLowerCase().includes(q) || a.command.toLowerCase().includes(q)
  );
  renderAppList(filtered);
}

function selectApp(name, command) {
  document.getElementById('tileLabel').value = name;
  document.getElementById('tileCommand').value = command;
  closeModalById('appPickerModal');
}

/* Sync */
async function syncToPhone() {
  const btn = document.getElementById('syncBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="material-symbols-outlined">sync</span> Syncing...';
  try {
    const data = await api('/api/sync', { method: 'POST' });
    if (data.connected > 0) {
      showToast('Config synced to ' + data.connected + ' phone(s)', 'success');
    } else {
      showToast('No phone connected. Config saved locally.', 'info');
    }
  } catch (e) {
    showToast('Sync failed: ' + e.message, 'error');
  }
  btn.disabled = false;
  btn.innerHTML = '<span class="material-symbols-outlined">sync</span> Sync to Phone';
}

/* Connection status */
async function checkConnection() {
  try {
    const data = await api('/api/status');
    const badge = document.getElementById('connectionStatus');
    if (data.connected > 0) {
      badge.textContent = 'Phone Connected';
      badge.className = 'status-badge connected';
    } else {
      badge.textContent = 'No Phone Connected';
      badge.className = 'status-badge';
    }
  } catch (e) {
    // server might be starting up
  }
}

/* Confirm dialog */
function showConfirm(message, onConfirm) {
  const overlay = document.createElement('div');
  overlay.className = 'confirm-overlay';
  overlay.innerHTML = `
    <div class="confirm-dialog">
      <p>${escHtml(message)}</p>
      <div class="confirm-actions">
        <button class="btn" onclick="this.closest('.confirm-overlay').remove()">Cancel</button>
        <button class="btn btn-danger" id="confirmBtn">Delete</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.querySelector('#confirmBtn').onclick = () => {
    overlay.remove();
    onConfirm();
  };
}

/* Modal helpers */
function closeModal(event, modalId) {
  if (event.target.id === modalId) {
    document.getElementById(modalId).style.display = 'none';
  }
}

function closeModalById(modalId) {
  document.getElementById(modalId).style.display = 'none';
}

/* Keyboard shortcuts */
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    document.querySelectorAll('.confirm-overlay').forEach(m => m.remove());
  }
});

/* Init */
document.addEventListener('DOMContentLoaded', () => {
  loadPages();
  checkConnection();
  setInterval(checkConnection, 5000);
});
