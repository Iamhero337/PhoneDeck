'use strict';

/* ------------------------------------------------------------------ *
 * Icons
 *
 * The Android app only renders the icon names listed in
 * TileGrid.kt#getIconForTile; anything else falls back to "apps".
 * ICONS lists the names offered in the picker, and ICON_GLYPH maps the
 * app's aliases to the Material Symbols glyph that looks the same.
 * ------------------------------------------------------------------ */
const ICONS = [
  // Apps & work
  'apps', 'code', 'terminal', 'public', 'search', 'folder', 'mail', 'calendar_month',
  'chat', 'forum', 'article', 'edit_note', 'menu_book', 'cloud', 'api', 'calculate',
  'desktop_windows', 'settings', 'home', 'help', 'sports_esports', 'shopping_cart',
  // Media
  'music_note', 'play_arrow', 'play_pause', 'stop', 'skip_previous', 'skip_next',
  'fast_rewind', 'fast_forward', 'shuffle', 'repeat', 'volume_up', 'volume_down',
  'volume_off', 'mic', 'mic_off', 'headphones', 'videocam', 'smart_display', 'photo_camera',
  // Creative & tools
  'screenshot', 'image', 'draw', 'brush', 'visibility', 'content_copy', 'content_paste',
  'download', 'upload', 'refresh', 'timer', 'notifications', 'keyboard',
  // System
  'brightness_high', 'brightness_low', 'dark_mode', 'light_mode', 'wifi', 'bluetooth',
  'lock', 'bedtime', 'logout', 'restart', 'shutdown',
  // Misc
  'star', 'favorite', 'bolt', 'rocket_launch',
];

const ICON_ALIASES = {
  chrome: 'public', next: 'skip_next', prev: 'skip_previous',
  brightness_up: 'brightness_high', brightness_down: 'brightness_low',
  hibernate: 'bedtime',
};

const ICON_GLYPH = {
  play_pause: 'pause', restart: 'restart_alt', shutdown: 'power_settings_new',
  logout: 'exit_to_app',
};

const SUPPORTED_ICONS = new Set([...ICONS, ...Object.keys(ICON_ALIASES)]);

function glyphFor(icon) {
  const name = ICON_ALIASES[icon] || icon;
  if (!SUPPORTED_ICONS.has(name)) return 'apps';
  return ICON_GLYPH[name] || name;
}

/* Default label/icon for built-in commands, used to prefill new tiles. */
const BUILTIN_ICON = {
  code: 'code', terminal: 'terminal', browser: 'public', spotify: 'music_note',
  figma: 'draw', photoshop: 'brush', illustrator: 'brush', preview: 'image',
  screenshot: 'screenshot', lock: 'lock', sleep: 'bedtime', restart: 'restart',
  shutdown: 'shutdown', logout: 'logout', hibernate: 'bedtime',
  volume_up: 'volume_up', volume_down: 'volume_down', mute: 'volume_off',
  play_pause: 'play_pause', next: 'skip_next', prev: 'skip_previous',
  brightness_up: 'brightness_high', brightness_down: 'brightness_low',
};

const TILE_SWATCHES = ['#1e1e2e', '#2a2a3e', '#16213e', '#1b2b1f', '#2e1a1a', '#2b2140', '#0f3460', '#3a2a12'];
const ICON_SWATCHES = ['#4a90d9', '#1db954', '#4caf50', '#ffc107', '#f57c00', '#e53935', '#ab47bc', '#ffffff'];

const DEFAULT_TILE_COLOR = '#1e1e2e';
const DEFAULT_ICON_COLOR = '#4a90d9';

/* ------------------------------------------------------------------ *
 * State
 * ------------------------------------------------------------------ */
const state = {
  pages: [],
  currentPageId: null,
  revision: null,
  dirty: false,
  connected: 0,
  meta: { commands: [], protectedPages: ['prod', 'media', 'system'] },
  installedApps: null,
  editing: null,        // { pageId, tileId|null }
  editingPageId: null,
  iconFilter: '',
  selectedIcon: 'apps',
  serverDown: false,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function currentPage() {
  return state.pages.find(p => p.id === state.currentPageId) || null;
}

function isProtected(pageId) {
  return state.meta.protectedPages.includes(pageId);
}

/* ------------------------------------------------------------------ *
 * API
 * ------------------------------------------------------------------ */
async function api(path, { method = 'GET', body } = {}) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, opts);
  } catch {
    throw new Error("Can't reach the PhoneDeck server. Is it running?");
  }
  let data = {};
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw new Error(data.error || data.message || `Request failed (${res.status})`);
  return data;
}

/* Run a mutation, then refresh pages so the UI reflects server state. */
async function mutate(fn, successMsg) {
  try {
    const result = await fn();
    await loadPages();
    if (successMsg) toast(successMsg, 'success');
    return result;
  } catch (e) {
    toast(e.message, 'error');
    return null;
  }
}

/* ------------------------------------------------------------------ *
 * Color helpers (tiles store Android ARGB ints, signed or unsigned)
 * ------------------------------------------------------------------ */
function argb(colorInt) {
  const u = colorInt < 0 ? colorInt + 0x100000000 : colorInt;
  return {
    a: Math.floor(u / 0x1000000) % 256,
    r: Math.floor(u / 0x10000) % 256,
    g: Math.floor(u / 0x100) % 256,
    b: u % 256,
  };
}

function cssColor(colorInt, fallback) {
  if (typeof colorInt !== 'number') return fallback;
  const { a, r, g, b } = argb(colorInt);
  return `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`;
}

function intToHex(colorInt, fallback) {
  if (typeof colorInt !== 'number') return fallback;
  const { r, g, b } = argb(colorInt);
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
}

function hexToInt(hex) {
  return 0xFF000000 + parseInt(hex.slice(1), 16);
}

/* WCAG relative luminance and contrast ratio, used to flag hard-to-read color choices. */
function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map(i => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(hexA, hexB) {
  const [hi, lo] = [luminance(hexA), luminance(hexB)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/* ------------------------------------------------------------------ *
 * DOM helpers
 * ------------------------------------------------------------------ */
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k === 'style') {
      for (const [prop, val] of Object.entries(v)) {
        if (prop.startsWith('--')) node.style.setProperty(prop, val);
        else node.style[prop] = val;
      }
    }
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, '');
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

const icon = (name, cls = '') => el('span', { class: `material-symbols-outlined ${cls}`.trim(), 'aria-hidden': 'true' }, name);

function describeCommand(cmd) {
  if (!cmd) return 'No action';
  if (cmd.startsWith('open_url:')) return cmd.slice(9);
  const builtin = state.meta.commands.find(c => c.command === cmd);
  return builtin ? builtin.label : cmd;
}

/* ------------------------------------------------------------------ *
 * Toasts
 * ------------------------------------------------------------------ */
function toast(message, type = 'info', { action, duration = 3500 } = {}) {
  const box = $('#toasts');
  const icons = { success: 'check_circle', error: 'error', info: 'info' };
  const node = el('div', { class: `toast ${type}`, role: type === 'error' ? 'alert' : 'status' },
    icon(icons[type] || 'info'),
    el('span', { class: 'toast-msg' }, message));
  const dismiss = () => {
    node.classList.add('leaving');
    setTimeout(() => node.remove(), 200);
  };
  if (action) {
    node.append(el('button', { class: 'toast-action', onclick: () => { dismiss(); action.run(); } }, action.label));
  }
  box.append(node);
  while (box.children.length > 4) box.firstElementChild.remove();
  setTimeout(dismiss, action ? Math.max(duration, 6000) : duration);
}

/* ------------------------------------------------------------------ *
 * Loading & status
 * ------------------------------------------------------------------ */
async function loadMeta() {
  try {
    state.meta = await api('/api/meta');
    $('#hostLabel').textContent = `${state.meta.hostname} · v${state.meta.version}`;
  } catch { /* defaults are fine */ }
  populateBuiltins();
}

async function loadPages() {
  try {
    const data = await api('/api/pages');
    state.pages = data.pages || [];
    state.revision = data.revision ?? state.revision;
  } catch (e) {
    toast(e.message, 'error');
    return;
  }
  if (!currentPage()) {
    const saved = safeStorage('get', 'phonedeck.page');
    state.currentPageId = (state.pages.find(p => p.id === saved) || state.pages[0] || {}).id || null;
  }
  render();
  refreshStatus();
}

async function refreshStatus() {
  let data;
  try {
    data = await api('/api/status');
  } catch {
    if (!state.serverDown) {
      state.serverDown = true;
      setBadge('offline', 'Server offline');
    }
    return;
  }
  if (state.serverDown) {
    state.serverDown = false;
    toast('Reconnected to PhoneDeck server', 'success');
  }
  state.connected = data.connected;
  state.dirty = data.dirty;
  if (data.connected > 0) setBadge('connected', data.connected > 1 ? `${data.connected} phones connected` : 'Phone connected');
  else setBadge('', 'No phone connected');
  $('#syncBtn').classList.toggle('is-dirty', !!data.dirty);
  $('#syncBtn').title = data.dirty
    ? 'You have changes that are not on your phone yet (Ctrl+S)'
    : 'Your phone is up to date (Ctrl+S)';

  // Something else (e.g. the phone) changed the config: refresh unless the user is mid-edit.
  if (state.revision !== null && data.revision !== state.revision && !document.querySelector('dialog[open]')) {
    loadPages();
  }
}

function setBadge(kind, text) {
  const badge = $('#connectionStatus');
  badge.className = `status-badge ${kind}`.trim();
  $('.status-text', badge).textContent = text;
}

/* ------------------------------------------------------------------ *
 * Rendering
 * ------------------------------------------------------------------ */
function render() {
  renderSidebar();
  renderContent();
  renderPhonePreview();
}

function renderSidebar() {
  const list = $('#pageList');
  list.replaceChildren(...state.pages.map((p, i) => {
    const active = p.id === state.currentPageId;
    return el('a', {
      href: '#', class: `page-item${active ? ' active' : ''}`, draggable: 'true',
      'aria-current': active ? 'page' : null,
      dataset: { pageId: p.id, index: i },
      onclick: (e) => { e.preventDefault(); selectPage(p.id); },
      ondblclick: () => openPageModal(p.id),
    },
    icon('drag_indicator', 'drag-handle'),
    el('span', { class: 'page-name' }, p.name),
    isProtected(p.id) ? icon('lock', 'page-lock') : null,
    el('span', { class: 'tile-count', title: `${(p.tiles || []).length} tiles` }, (p.tiles || []).length));
  }));
}

function renderContent() {
  const page = currentPage();
  const grid = $('#tileGrid');
  const header = $('#contentHeader');
  const empty = $('#emptyState');

  if (!page) {
    header.hidden = true;
    grid.replaceChildren();
    empty.hidden = false;
    $('#emptyText').textContent = state.pages.length
      ? 'Select a page from the sidebar.'
      : 'No pages yet. Create one to start adding tiles.';
    return;
  }

  header.hidden = false;
  empty.hidden = true;
  $('#pageName').textContent = page.name;
  const n = (page.tiles || []).length;
  $('#pageMeta').textContent = `${n} tile${n === 1 ? '' : 's'}`;
  $('#deletePageBtn').hidden = isProtected(page.id);

  const tiles = page.tiles || [];
  const cards = tiles.map((t, i) => tileCard(page, t, i));
  cards.push(el('button', { class: 'tile-card add-card', onclick: () => openTileModal(), title: 'Add tile (N)' },
    icon('add_circle'), el('span', {}, 'Add tile')));
  grid.replaceChildren(...cards);
}

function tileCard(page, t, index) {
  const bg = cssColor(t.color, DEFAULT_TILE_COLOR);
  const fg = cssColor(t.iconColor, DEFAULT_ICON_COLOR);
  const unsupported = t.icon && !SUPPORTED_ICONS.has(t.icon);
  const isUrl = (t.command || '').startsWith('open_url:');

  const action = (name, label, onclick, cls = '') =>
    el('button', { class: `tile-action ${cls}`.trim(), title: label, 'aria-label': label,
      onclick: (e) => { e.stopPropagation(); onclick(); } }, icon(name));

  return el('div', {
    class: 'tile-card', role: 'listitem', tabindex: '0', draggable: 'true',
    'aria-label': `${t.label}, ${describeCommand(t.command)}`,
    dataset: { tileId: t.id, index },
    style: { '--tile-bg': bg, '--tile-fg': fg, animationDelay: `${Math.min(index, 12) * 25}ms` },
    onclick: () => openTileModal(t.id),
  },
  el('div', { class: 'tile-actions' },
    action('play_arrow', 'Test on this computer', () => testCommand(t.command)),
    action('content_copy', 'Duplicate', () => duplicateTile(t.id)),
    action('delete', 'Delete', () => deleteTile(page.id, t.id), 'danger')),
  el('div', { class: 'tile-icon' }, icon(glyphFor(t.icon))),
  el('div', { class: 'tile-label' }, t.label || 'Untitled'),
  el('div', { class: 'tile-command' }, icon(isUrl ? 'link' : (BUILTIN_ICON[t.command] ? 'bolt' : 'terminal')), describeCommand(t.command)),
  unsupported ? el('span', { class: 'tile-warn', title: `"${t.icon}" isn't available on the phone and will show as the default icon` }, icon('warning')) : null);
}

function renderPhonePreview() {
  const page = currentPage();
  $('#phoneTabs').replaceChildren(...state.pages.map(p =>
    el('button', { class: `phone-tab${p.id === state.currentPageId ? ' active' : ''}`, onclick: () => selectPage(p.id) }, p.name)));
  const tabs = $('#phoneTabs');
  const active = $('.active', tabs);
  if (active) tabs.scrollLeft = active.offsetLeft - (tabs.clientWidth - active.offsetWidth) / 2;
  $('#phoneGrid').replaceChildren(...(page ? page.tiles || [] : []).map(t => phoneTile(t)));
}

function phoneTile(t) {
  return el('div', {
    class: 'phone-tile',
    style: { '--tile-bg': cssColor(t.color, DEFAULT_TILE_COLOR), '--tile-fg': cssColor(t.iconColor, DEFAULT_ICON_COLOR) },
    title: describeCommand(t.command),
  }, icon(glyphFor(t.icon), 'phone-tile-icon'), el('span', { class: 'phone-tile-label' }, t.label));
}

function selectPage(pageId) {
  if (!state.pages.some(p => p.id === pageId)) return;
  state.currentPageId = pageId;
  safeStorage('set', 'phonedeck.page', pageId);
  render();
}

function safeStorage(op, key, value) {
  try {
    if (op === 'get') return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch { /* storage unavailable */ }
  return null;
}

/* ------------------------------------------------------------------ *
 * Dialog helpers
 * ------------------------------------------------------------------ */
function openDialog(id) {
  const d = document.getElementById(id);
  if (!d.open) d.showModal();
  return d;
}

function closeDialog(id) {
  const d = document.getElementById(id);
  if (d.open) d.close();
}

function confirmAction({ title, message, confirmLabel = 'Delete' }) {
  return new Promise(resolve => {
    const d = $('#confirmModal');
    $('#confirmTitle').textContent = title;
    $('#confirmMessage').textContent = message;
    $('#confirmOk').textContent = confirmLabel;
    d.returnValue = 'cancel';
    d.addEventListener('close', () => resolve(d.returnValue === 'ok'), { once: true });
    d.showModal();
    $('#confirmOk').focus();
  });
}

/* ------------------------------------------------------------------ *
 * Pages
 * ------------------------------------------------------------------ */
function openPageModal(editId = null) {
  state.editingPageId = editId;
  const page = editId ? state.pages.find(p => p.id === editId) : null;
  $('#pageModalTitle').textContent = page ? 'Rename page' : 'New page';
  $('#savePageBtn span:last-child').textContent = page ? 'Save' : 'Create';
  $('#pageNameInput').value = page ? page.name : '';
  openDialog('pageModal');
  $('#pageNameInput').select();
}

async function savePage(e) {
  e.preventDefault();
  const name = $('#pageNameInput').value.trim();
  if (!name) {
    $('#pageNameInput').focus();
    return toast('Give the page a name', 'error');
  }
  const editId = state.editingPageId;
  const res = await mutate(
    () => editId
      ? api(`/api/pages/${encodeURIComponent(editId)}`, { method: 'PUT', body: { name } })
      : api('/api/pages', { method: 'POST', body: { name } }),
    editId ? 'Page renamed' : 'Page created');
  if (!res) return;
  closeDialog('pageModal');
  if (!editId && res.page) selectPage(res.page.id);
}

async function deletePage(pageId) {
  const page = state.pages.find(p => p.id === pageId);
  if (!page) return;
  const n = (page.tiles || []).length;
  const ok = await confirmAction({
    title: `Delete "${page.name}"?`,
    message: n ? `This page and its ${n} tile${n === 1 ? '' : 's'} will be removed.` : 'This empty page will be removed.',
  });
  if (!ok) return;
  const idx = state.pages.indexOf(page);
  const res = await mutate(() => api(`/api/pages/${encodeURIComponent(pageId)}`, { method: 'DELETE' }), 'Page deleted');
  if (res && state.currentPageId === pageId) {
    const next = state.pages[Math.min(idx, state.pages.length - 1)];
    if (next) selectPage(next.id);
  }
}

/* ------------------------------------------------------------------ *
 * Tile editor
 * ------------------------------------------------------------------ */
function populateBuiltins() {
  const sel = $('#builtinSelect');
  const groups = {
    Apps: ['code', 'terminal', 'browser', 'spotify', 'figma', 'photoshop', 'illustrator', 'preview'],
    Media: ['play_pause', 'next', 'prev', 'volume_up', 'volume_down', 'mute'],
    System: ['screenshot', 'lock', 'sleep', 'brightness_up', 'brightness_down'],
    Power: ['restart', 'shutdown', 'logout', 'hibernate'],
  };
  const labels = Object.fromEntries(state.meta.commands.map(c => [c.command, c.label]));
  const used = new Set();
  const opts = Object.entries(groups).map(([group, cmds]) =>
    el('optgroup', { label: group }, cmds.filter(c => labels[c]).map(c => {
      used.add(c);
      return el('option', { value: c }, labels[c]);
    })));
  const rest = state.meta.commands.filter(c => !used.has(c.command));
  if (rest.length) opts.push(el('optgroup', { label: 'Other' }, rest.map(c => el('option', { value: c.command }, c.label))));
  sel.replaceChildren(...opts);
}

function actionType() {
  return $('input[name="actionType"]:checked').value;
}

function setActionType(type) {
  $(`input[name="actionType"][value="${type}"]`).checked = true;
  $$('[data-action-panel]').forEach(p => { p.hidden = p.dataset.actionPanel !== type; });
}

function editorCommand() {
  const type = actionType();
  if (type === 'builtin') return $('#builtinSelect').value;
  if (type === 'url') {
    let url = $('#tileUrl').value.trim();
    if (url && !/^[a-z][a-z0-9+.-]*:/i.test(url)) url = 'https://' + url;
    return url ? 'open_url:' + url : '';
  }
  return $('#tileCommand').value.trim();
}

function openTileModal(tileId = null) {
  const page = currentPage();
  if (!page) return toast('Create a page first', 'error');

  let tile = null;
  let pageId = page.id;
  if (tileId) {
    for (const p of state.pages) {
      const t = (p.tiles || []).find(x => x.id === tileId);
      if (t) { tile = t; pageId = p.id; break; }
    }
    if (!tile) return;
  }
  state.editing = { pageId, tileId: tile ? tile.id : null };

  $('#tileModalTitle').textContent = tile ? 'Edit tile' : `Add tile to ${page.name}`;
  $('#tileLabel').value = tile ? tile.label : '';
  $('#tileColor').value = intToHex(tile?.color, DEFAULT_TILE_COLOR);
  $('#tileIconColor').value = intToHex(tile?.iconColor, DEFAULT_ICON_COLOR);
  state.selectedIcon = tile ? (tile.icon || 'apps') : 'apps';
  state.iconFilter = '';
  $('#iconSearch').value = '';

  const cmd = tile ? tile.command || '' : '';
  const builtin = state.meta.commands.find(c => c.command === cmd);
  // Remember which label/icon were auto-filled so switching actions only replaces those.
  $('#tileLabel').dataset.auto = builtin ? builtin.label : '';
  $('#tileLabel').dataset.autoIcon = BUILTIN_ICON[cmd] || '';
  $('#tileCommand').value = '';
  $('#tileUrl').value = '';
  if (!tile) {
    setActionType('builtin');
    $('#builtinSelect').selectedIndex = 0;
    prefillFromBuiltin(true);
  } else if (cmd.startsWith('open_url:')) {
    setActionType('url');
    $('#tileUrl').value = cmd.slice(9);
  } else if (state.meta.commands.some(c => c.command === cmd)) {
    setActionType('builtin');
    $('#builtinSelect').value = cmd;
  } else {
    setActionType('app');
    $('#tileCommand').value = cmd;
  }

  renderIconGrid();
  updatePreview();
  openDialog('tileModal');
  $('#tileLabel').focus();
}

/* When picking a built-in action, fill in a matching label and icon unless the user typed their own. */
function prefillFromBuiltin(force = false) {
  const sel = $('#builtinSelect');
  const cmd = sel.value;
  const label = sel.selectedOptions[0]?.textContent || '';
  const labelInput = $('#tileLabel');
  const prevAuto = labelInput.dataset.auto;
  if (force || !labelInput.value || labelInput.value === prevAuto) {
    labelInput.value = label;
    labelInput.dataset.auto = label;
  }
  if (BUILTIN_ICON[cmd] && (force || state.selectedIcon === 'apps' || state.selectedIcon === labelInput.dataset.autoIcon)) {
    state.selectedIcon = BUILTIN_ICON[cmd];
    labelInput.dataset.autoIcon = state.selectedIcon;
    renderIconGrid();
  }
}

/* Leaving "Built-in": drop the label/icon we filled in for the built-in action, keep anything the user chose. */
function clearAutofill(defaultIcon) {
  const labelInput = $('#tileLabel');
  if (labelInput.dataset.auto && labelInput.value === labelInput.dataset.auto) {
    labelInput.value = '';
    labelInput.dataset.auto = '';
  }
  const auto = labelInput.dataset.autoIcon;
  if (state.selectedIcon === 'apps' || state.selectedIcon === 'public' || (auto && state.selectedIcon === auto)) {
    state.selectedIcon = defaultIcon;
    labelInput.dataset.autoIcon = defaultIcon;
    renderIconGrid();
  }
}

function renderIconGrid() {
  const q = state.iconFilter.toLowerCase().replace(/\s+/g, '_');
  const list = ICONS.filter(n => !q || n.includes(q));
  const current = ICON_ALIASES[state.selectedIcon] || state.selectedIcon;
  $('#iconGrid').replaceChildren(...list.map(name =>
    el('button', {
      type: 'button', class: `icon-option${name === current ? ' selected' : ''}`,
      role: 'option', 'aria-selected': String(name === current), title: name.replace(/_/g, ' '),
      dataset: { icon: name },
      onclick: () => { state.selectedIcon = name; renderIconGrid(); updatePreview(); },
    }, icon(glyphFor(name)))));
  if (!list.length) $('#iconGrid').append(el('p', { class: 'help icon-empty' }, 'No matching icons'));
  $('#iconCurrent').textContent = state.selectedIcon.replace(/_/g, ' ');
}

function updatePreview() {
  const preview = $('#livePreview');
  const bg = $('#tileColor').value;
  preview.style.setProperty('--tile-bg', bg);
  preview.style.setProperty('--tile-fg', $('#tileIconColor').value);
  $('.phone-tile-icon', preview).textContent = glyphFor(state.selectedIcon);
  $('.phone-tile-label', preview).textContent = $('#tileLabel').value.trim() || 'Label';
  const cmd = editorCommand();
  $('#previewCommand').textContent = cmd || 'No action set';
  $('#iconWarning').hidden = SUPPORTED_ICONS.has(state.selectedIcon);
  // The phone always draws labels in white, so warn about light tiles and low-contrast icons.
  const fg = $('#tileIconColor').value;
  const issue = contrast(bg, '#ffffff') < 3 ? 'The phone shows labels in white, which will be hard to read on this tile color.'
    : contrast(bg, fg) < 2 ? 'The icon color is hard to see on this tile color.' : '';
  $('#contrastWarning').hidden = !issue;
  $('#contrastText').textContent = issue;
  $('#testTileBtn').disabled = !cmd;
  $$('.swatches').forEach(box => {
    const val = $('#' + box.dataset.target).value.toLowerCase();
    $$('.swatch', box).forEach(s => s.classList.toggle('selected', s.dataset.color === val));
  });
}

function renderSwatches() {
  $$('.swatches').forEach(box => {
    const colors = box.dataset.target === 'tileColor' ? TILE_SWATCHES : ICON_SWATCHES;
    box.replaceChildren(...colors.map(c => el('button', {
      type: 'button', class: 'swatch', title: c, 'aria-label': `Use ${c}`,
      dataset: { color: c }, style: { background: c },
      onclick: () => { $('#' + box.dataset.target).value = c; updatePreview(); },
    })));
  });
}

async function saveTile(e) {
  e?.preventDefault();
  const label = $('#tileLabel').value.trim();
  const command = editorCommand();
  if (!label) {
    $('#tileLabel').focus();
    return toast('Give the tile a label', 'error');
  }
  if (!command) return toast(actionType() === 'url' ? 'Enter a website URL' : 'Choose what the tile should do', 'error');
  if (actionType() === 'url') {
    try { new URL(command.slice(9)); } catch { return toast('That URL doesn\'t look right', 'error'); }
  }

  const body = {
    label, command,
    icon: state.selectedIcon || 'apps',
    color: hexToInt($('#tileColor').value),
    iconColor: hexToInt($('#tileIconColor').value),
  };
  const { pageId, tileId } = state.editing || {};
  const btn = $('#saveTileBtn');
  btn.disabled = true;
  const res = await mutate(
    () => tileId
      ? api(`/api/tiles/${encodeURIComponent(tileId)}`, { method: 'PUT', body })
      : api('/api/tiles', { method: 'POST', body: { ...body, pageId } }),
    tileId ? 'Tile updated' : 'Tile added');
  btn.disabled = false;
  if (res) closeDialog('tileModal');
}

async function deleteTile(pageId, tileId) {
  const page = state.pages.find(p => p.id === pageId);
  const index = page ? page.tiles.findIndex(t => t.id === tileId) : -1;
  const tile = index >= 0 ? page.tiles[index] : null;
  const res = await mutate(() => api(`/api/tiles/${encodeURIComponent(pageId)}/${encodeURIComponent(tileId)}`, { method: 'DELETE' }));
  if (!res || !tile) return;
  toast(`Deleted "${tile.label}"`, 'info', {
    action: {
      label: 'Undo',
      run: () => mutate(async () => {
        const { tile: restored } = await api('/api/tiles', { method: 'POST', body: { ...tile, pageId } });
        await api(`/api/tiles/${encodeURIComponent(restored.id)}/move`, { method: 'POST', body: { pageId, index } });
      }, 'Tile restored'),
    },
  });
}

function duplicateTile(tileId) {
  return mutate(() => api(`/api/tiles/${encodeURIComponent(tileId)}/duplicate`, { method: 'POST', body: {} }), 'Tile duplicated');
}

const POWER_COMMANDS = new Set(['restart', 'reboot', 'shutdown', 'logout', 'hibernate', 'sleep', 'lock']);

async function testCommand(command) {
  if (!command) return toast('This tile has no action', 'error');
  if (POWER_COMMANDS.has(command)) {
    const ok = await confirmAction({
      title: `Run "${describeCommand(command)}" now?`,
      message: 'Testing this tile runs it for real on the computer running PhoneDeck.',
      confirmLabel: "Run it",
    });
    if (!ok) return;
  }
  try {
    await api('/api/test', { method: 'POST', body: { command } });
    toast(`Ran: ${describeCommand(command)}`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ------------------------------------------------------------------ *
 * App picker
 * ------------------------------------------------------------------ */
async function openAppPicker() {
  openDialog('appPickerModal');
  $('#appSearch').value = '';
  $('#appSearch').focus();
  if (state.installedApps) return renderAppList();
  $('#appList').replaceChildren(el('div', { class: 'list-status' }, el('span', { class: 'spinner' }), 'Scanning installed apps…'));
  try {
    const data = await api('/api/apps');
    state.installedApps = data.apps || [];
  } catch (e) {
    $('#appList').replaceChildren(el('div', { class: 'list-status error' }, `Couldn't load apps: ${e.message}`));
    return;
  }
  renderAppList();
}

function renderAppList() {
  const q = $('#appSearch').value.trim().toLowerCase();
  const apps = (state.installedApps || []).filter(a =>
    !q || a.name.toLowerCase().includes(q) || a.command.toLowerCase().includes(q));
  const list = $('#appList');
  if (!apps.length) {
    list.replaceChildren(el('div', { class: 'list-status' }, q ? `No apps match "${q}"` : 'No apps found'));
    return;
  }
  list.replaceChildren(...apps.slice(0, 300).map(a => el('button', {
    type: 'button', class: 'app-item', role: 'option',
    onclick: () => selectApp(a),
  }, el('span', { class: 'app-avatar' }, a.name.trim().charAt(0).toUpperCase()),
     el('span', { class: 'app-text' },
       el('span', { class: 'app-name' }, a.name),
       el('span', { class: 'app-command' }, a.command)))));
}

function selectApp(app) {
  const labelInput = $('#tileLabel');
  if (!labelInput.value.trim() || labelInput.value === labelInput.dataset.auto) {
    labelInput.value = app.name;
    labelInput.dataset.auto = app.name;
  }
  setActionType('app');
  $('#tileCommand').value = app.command;
  closeDialog('appPickerModal');
  updatePreview();
  $('#tileLabel').focus();
}

/* ------------------------------------------------------------------ *
 * Sync, import/export, reset
 * ------------------------------------------------------------------ */
let syncing = false;
async function syncToPhone() {
  if (syncing) return;
  syncing = true;
  const btn = $('#syncBtn');
  btn.classList.add('is-syncing');
  btn.disabled = true;
  try {
    const data = await api('/api/sync', { method: 'POST', body: {} });
    if (data.connected > 0) toast(`Synced to ${data.connected > 1 ? data.connected + ' phones' : 'your phone'}`, 'success');
    else toast('No phone connected. Your changes are saved and will be sent when your phone connects.', 'info', { duration: 5000 });
  } catch (e) {
    toast(`Sync failed: ${e.message}`, 'error');
  }
  btn.classList.remove('is-syncing');
  btn.disabled = false;
  syncing = false;
  setTimeout(refreshStatus, 400);
}

function exportConfig() {
  const blob = new Blob([JSON.stringify({ version: '1', pages: state.pages }, null, 2)], { type: 'application/json' });
  const a = el('a', { href: URL.createObjectURL(blob), download: `phonedeck-config-${new Date().toISOString().slice(0, 10)}.json` });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast('Config exported', 'success');
}

async function importConfig(file) {
  let data;
  try {
    data = JSON.parse(await file.text());
  } catch {
    return toast('That file isn\'t valid JSON', 'error');
  }
  const pages = Array.isArray(data) ? data : data.pages;
  if (!Array.isArray(pages)) return toast('No pages found in that file', 'error');
  const ok = await confirmAction({
    title: 'Replace your layout?',
    message: `Import ${pages.length} page${pages.length === 1 ? '' : 's'} from "${file.name}". Your current pages will be replaced.`,
    confirmLabel: 'Import',
  });
  if (!ok) return;
  state.currentPageId = null;
  await mutate(() => api('/api/import', { method: 'POST', body: { pages } }), 'Config imported');
}

async function resetConfig() {
  const ok = await confirmAction({
    title: 'Reset to defaults?',
    message: 'All pages and tiles will be replaced with the default layout. Export first if you want a backup.',
    confirmLabel: 'Reset',
  });
  if (!ok) return;
  state.currentPageId = null;
  await mutate(() => api('/api/reset', { method: 'POST', body: {} }), 'Layout reset to defaults');
}

/* ------------------------------------------------------------------ *
 * Drag & drop and keyboard reordering
 * ------------------------------------------------------------------ */
let drag = null; // { kind: 'tile'|'page', id }

function setupDragAndDrop() {
  const grid = $('#tileGrid');
  const pageList = $('#pageList');

  document.addEventListener('dragstart', (e) => {
    const card = e.target.closest?.('.tile-card[data-tile-id]');
    const page = e.target.closest?.('.page-item');
    if (card) drag = { kind: 'tile', id: card.dataset.tileId, node: card, dropped: false };
    else if (page) drag = { kind: 'page', id: page.dataset.pageId, node: page, dropped: false };
    else return;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', drag.id);
    requestAnimationFrame(() => drag?.node.classList.add('dragging'));
  });

  document.addEventListener('dragend', () => {
    if (!drag) return;
    drag.node.classList.remove('dragging');
    $$('.drop-target').forEach(n => n.classList.remove('drop-target'));
    // Dropped somewhere else: undo the live DOM reordering.
    if (!drag.dropped) render();
    drag = null;
  });

  grid.addEventListener('dragover', (e) => {
    if (drag?.kind !== 'tile') return;
    e.preventDefault();
    const over = e.target.closest('.tile-card[data-tile-id]');
    if (!over || over === drag.node) return;
    const rect = over.getBoundingClientRect();
    const after = (e.clientX - rect.left) > rect.width / 2;
    over.parentNode.insertBefore(drag.node, after ? over.nextSibling : over);
  });

  grid.addEventListener('drop', (e) => {
    if (drag?.kind !== 'tile') return;
    e.preventDefault();
    drag.dropped = true;
    const order = $$('.tile-card[data-tile-id]', grid).map(n => n.dataset.tileId);
    saveTileOrder(order);
  });

  pageList.addEventListener('dragover', (e) => {
    const over = e.target.closest('.page-item');
    if (!drag || !over) return;
    e.preventDefault();
    if (drag.kind === 'page') {
      if (over === drag.node) return;
      const rect = over.getBoundingClientRect();
      const after = (e.clientY - rect.top) > rect.height / 2;
      pageList.insertBefore(drag.node, after ? over.nextSibling : over);
    } else if (over.dataset.pageId !== state.currentPageId) {
      $$('.drop-target').forEach(n => n.classList.remove('drop-target'));
      over.classList.add('drop-target');
    }
  });

  pageList.addEventListener('dragleave', (e) => {
    const over = e.target.closest('.page-item');
    if (over && !over.contains(e.relatedTarget)) over.classList.remove('drop-target');
  });

  pageList.addEventListener('drop', (e) => {
    if (!drag) return;
    e.preventDefault();
    drag.dropped = true;
    if (drag.kind === 'page') {
      const order = $$('.page-item', pageList).map(n => n.dataset.pageId);
      mutate(() => api('/api/pages/reorder', { method: 'POST', body: { order } }));
    } else {
      const target = e.target.closest('.page-item');
      if (target && target.dataset.pageId !== state.currentPageId) {
        const name = state.pages.find(p => p.id === target.dataset.pageId)?.name;
        mutate(() => api(`/api/tiles/${encodeURIComponent(drag.id)}/move`, { method: 'POST', body: { pageId: target.dataset.pageId } }),
          `Moved to ${name}`);
      }
    }
  });
}

function saveTileOrder(order) {
  const page = currentPage();
  if (!page) return;
  const same = order.join() === (page.tiles || []).map(t => t.id).join();
  if (same) return;
  mutate(() => api('/api/tiles/reorder', { method: 'POST', body: { pageId: page.id, order } }));
}

async function moveFocusedTile(card, delta) {
  const page = currentPage();
  const ids = (page.tiles || []).map(t => t.id);
  const from = ids.indexOf(card.dataset.tileId);
  const to = from + delta;
  if (from < 0 || to < 0 || to >= ids.length) return;
  ids.splice(to, 0, ids.splice(from, 1)[0]);
  const id = card.dataset.tileId;
  await mutate(() => api('/api/tiles/reorder', { method: 'POST', body: { pageId: page.id, order: ids } }));
  $(`.tile-card[data-tile-id="${CSS.escape(id)}"]`)?.focus();
}

/* ------------------------------------------------------------------ *
 * Wiring
 * ------------------------------------------------------------------ */
function closeMenu() {
  $('#moreMenu').hidden = true;
  $('#moreBtn').setAttribute('aria-expanded', 'false');
}

function bindEvents() {
  $('#syncBtn').addEventListener('click', syncToPhone);
  $('#addPageBtn').addEventListener('click', () => openPageModal());
  $('#addTileBtn').addEventListener('click', () => openTileModal());
  $('#renamePageBtn').addEventListener('click', () => state.currentPageId && openPageModal(state.currentPageId));
  $('#pageName').addEventListener('dblclick', () => state.currentPageId && openPageModal(state.currentPageId));
  $('#deletePageBtn').addEventListener('click', () => state.currentPageId && deletePage(state.currentPageId));
  $('#pageForm').addEventListener('submit', savePage);
  $('#tileForm').addEventListener('submit', saveTile);
  $('#browseAppsBtn').addEventListener('click', openAppPicker);
  $('#appSearch').addEventListener('input', renderAppList);
  $('#appSearch').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); $('#appList .app-item')?.click(); }
  });
  $('#testTileBtn').addEventListener('click', () => testCommand(editorCommand()));

  // Editor live updates
  $('#tileLabel').addEventListener('input', updatePreview);
  ['#tileCommand', '#tileUrl', '#tileColor', '#tileIconColor'].forEach(s => $(s).addEventListener('input', updatePreview));
  $('#builtinSelect').addEventListener('change', () => { prefillFromBuiltin(); updatePreview(); });
  $$('input[name="actionType"]').forEach(r => r.addEventListener('change', () => {
    setActionType(r.value);
    if (r.value === 'builtin') prefillFromBuiltin();
    else clearAutofill(r.value === 'url' ? 'public' : 'apps');
    updatePreview();
    $(`[data-action-panel="${r.value}"] input, [data-action-panel="${r.value}"] select`)?.focus();
  }));
  $('#iconSearch').addEventListener('input', (e) => { state.iconFilter = e.target.value; renderIconGrid(); });
  $('#iconSearch').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); $('#iconGrid .icon-option')?.click(); }
  });
  $('#tileForm').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) saveTile(e);
  });

  // Dialogs: [data-close] buttons and clicking the backdrop
  $$('dialog').forEach(d => {
    d.addEventListener('click', (e) => {
      if (e.target.closest('[data-close]')) d.close();
      else if (e.target === d) {
        const r = d.getBoundingClientRect();
        const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
        if (!inside) d.close();
      }
    });
  });

  // More menu
  $('#moreBtn').addEventListener('click', (e) => {
    e.stopPropagation();
    const menu = $('#moreMenu');
    menu.hidden = !menu.hidden;
    $('#moreBtn').setAttribute('aria-expanded', String(!menu.hidden));
    if (!menu.hidden) $('button', menu).focus();
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('.menu-wrap')) closeMenu(); });
  $('#moreMenu').addEventListener('click', (e) => {
    const action = e.target.closest('[data-action]')?.dataset.action;
    if (!action) return;
    closeMenu();
    if (action === 'export') exportConfig();
    else if (action === 'import') $('#importFile').click();
    else if (action === 'reset') resetConfig();
    else if (action === 'shortcuts') openDialog('shortcutsModal');
  });
  $('#importFile').addEventListener('change', (e) => {
    const file = e.target.files[0];
    e.target.value = '';
    if (file) importConfig(file);
  });

  // Tile card keyboard
  $('#tileGrid').addEventListener('keydown', (e) => {
    const card = e.target.closest('.tile-card[data-tile-id]');
    if (!card || e.target !== card) return;
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openTileModal(card.dataset.tileId); }
    else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteTile(state.currentPageId, card.dataset.tileId); }
    else if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowUp')) { e.preventDefault(); moveFocusedTile(card, -1); }
    else if (e.altKey && (e.key === 'ArrowRight' || e.key === 'ArrowDown')) { e.preventDefault(); moveFocusedTile(card, 1); }
  });

  // Global shortcuts
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      if (!document.querySelector('dialog[open]')) syncToPhone();
      return;
    }
    if (e.key === 'Escape') closeMenu();
    const typing = e.target.matches('input, textarea, select, [contenteditable]');
    if (typing || e.ctrlKey || e.metaKey || e.altKey || document.querySelector('dialog[open]')) return;
    if (e.key === 'n') { e.preventDefault(); openTileModal(); }
    else if (e.key === 'p') { e.preventDefault(); openPageModal(); }
    else if (e.key === '?') { e.preventDefault(); openDialog('shortcutsModal'); }
    else if (e.key === '[' || e.key === ']') {
      const i = state.pages.findIndex(p => p.id === state.currentPageId);
      const next = state.pages[i + (e.key === ']' ? 1 : -1)];
      if (next) selectPage(next.id);
    }
  });

  // Poll faster while visible, pause in background tabs.
  let timer = null;
  const schedule = () => {
    clearInterval(timer);
    timer = setInterval(refreshStatus, document.hidden ? 15000 : 3000);
  };
  document.addEventListener('visibilitychange', () => { schedule(); if (!document.hidden) refreshStatus(); });
  schedule();
}

async function init() {
  renderSwatches();
  bindEvents();
  setupDragAndDrop();
  $('#emptyState').hidden = false;
  await loadMeta();
  await loadPages();
}

document.addEventListener('DOMContentLoaded', init);
