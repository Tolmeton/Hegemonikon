import './css/dashboard.css';  // reuse dashboard card styles
import { esc } from '../utils';

/**
 * Settings View — HGK Desktop 設定画面
 *
 * 設定カテゴリ:
 *   1. テーマ (dark/light)
 *   2. ポーリング間隔 (Dashboard 自動更新)
 *   3. 通知フィルタ
 *   4. API エンドポイント表示
 */

interface SettingsState {
  theme: string;
  pollingInterval: number;
  notifFilter: string;
  apiBase: string;
}

function loadSettings(): SettingsState {
  return {
    theme: localStorage.getItem('hgk-theme') ?? 'dark',
    pollingInterval: parseInt(localStorage.getItem('hgk-polling') ?? '30', 10),
    notifFilter: localStorage.getItem('hgk-notif-filter') ?? 'ALL',
    apiBase: localStorage.getItem('hgk-api-base') ?? 'http://localhost:9696',
  };
}

function saveSettings(s: SettingsState): void {
  localStorage.setItem('hgk-theme', s.theme);
  localStorage.setItem('hgk-polling', String(s.pollingInterval));
  localStorage.setItem('hgk-notif-filter', s.notifFilter);
  localStorage.setItem('hgk-api-base', s.apiBase);
}

export async function renderSettingsView(): Promise<void> {
  const app = document.getElementById('view-content');
  if (!app) return;

  const s = loadSettings();

  app.innerHTML = `
    <div class="settings-view">
      <h1 class="view-title">⚙️ Settings</h1>

      <div class="settings-grid">
        <!-- Theme -->
        <div class="card settings-card">
          <h3>🎨 テーマ</h3>
          <div class="settings-row">
            <label>カラーモード</label>
            <select id="set-theme" class="settings-select">
              <option value="dark" ${s.theme === 'dark' ? 'selected' : ''}>🌙 Dark</option>
              <option value="light" ${s.theme === 'light' ? 'selected' : ''}>☀️ Light</option>
            </select>
          </div>
        </div>

        <!-- Polling -->
        <div class="card settings-card">
          <h3>🔄 ポーリング</h3>
          <div class="settings-row">
            <label>Dashboard 更新間隔</label>
            <div class="settings-range-wrap">
              <input type="range" id="set-polling" min="10" max="120" step="5" value="${s.pollingInterval}" class="settings-range">
              <span id="set-polling-val" class="settings-range-val">${s.pollingInterval}s</span>
            </div>
          </div>
        </div>

        <!-- Notifications -->
        <div class="card settings-card">
          <h3>🔔 通知フィルタ</h3>
          <div class="settings-row">
            <label>デフォルト表示</label>
            <select id="set-notif" class="settings-select">
              ${['ALL', 'CRITICAL', 'WARNING', 'INFO'].map(lv =>
    `<option value="${lv}" ${s.notifFilter === lv ? 'selected' : ''}>${esc(lv)}</option>`
  ).join('')}
            </select>
          </div>
        </div>

        <!-- API -->
        <div class="card settings-card">
          <h3>🌐 API エンドポイント</h3>
          <div class="settings-row">
            <label>ベース URL</label>
            <input type="text" id="set-api" value="${esc(s.apiBase)}" class="settings-input" spellcheck="false">
          </div>
        </div>
      </div>

      <div class="settings-actions">
        <button id="set-save" class="settings-btn primary">💾 保存</button>
        <button id="set-reset" class="settings-btn secondary">🔄 リセット</button>
      </div>

      <div id="set-toast" class="settings-toast hidden"></div>
    </div>
  `;

  // --- Event handlers ---

  const pollingSlider = document.getElementById('set-polling') as HTMLInputElement;
  const pollingVal = document.getElementById('set-polling-val')!;
  pollingSlider?.addEventListener('input', () => {
    pollingVal.textContent = `${pollingSlider.value}s`;
  });

  // Theme live preview
  const themeSelect = document.getElementById('set-theme') as HTMLSelectElement;
  themeSelect?.addEventListener('change', () => {
    document.documentElement.setAttribute('data-theme', themeSelect.value);
    const btn = document.querySelector('.theme-toggle');
    if (btn) btn.textContent = themeSelect.value === 'dark' ? '☀️' : '🌙';
  });

  // Save
  document.getElementById('set-save')?.addEventListener('click', () => {
    const newSettings: SettingsState = {
      theme: (document.getElementById('set-theme') as HTMLSelectElement).value,
      pollingInterval: parseInt((document.getElementById('set-polling') as HTMLInputElement).value, 10),
      notifFilter: (document.getElementById('set-notif') as HTMLSelectElement).value,
      apiBase: (document.getElementById('set-api') as HTMLInputElement).value.trim(),
    };
    saveSettings(newSettings);
    showToast('✅ 設定を保存しました');
  });

  // Reset
  document.getElementById('set-reset')?.addEventListener('click', () => {
    localStorage.removeItem('hgk-theme');
    localStorage.removeItem('hgk-polling');
    localStorage.removeItem('hgk-notif-filter');
    localStorage.removeItem('hgk-api-base');
    document.documentElement.setAttribute('data-theme', 'dark');
    showToast('🔄 設定をリセットしました');
    setTimeout(() => void renderSettingsView(), 500);
  });
}

function showToast(msg: string): void {
  const toast = document.getElementById('set-toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 2500);
}
