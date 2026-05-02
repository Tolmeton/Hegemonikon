/**
 * HGK Desktop — エントリポイント
 *
 * UI モジュール (ui/) を統合し、ルーティングとブートストラップを管理。
 */

import { ROUTES, ROUTE_MAP, DEFAULT_ROUTE } from './route-config';
import { api } from './api/client';
import { recordView } from './telemetry';
import { initCommandPalette, setNavigateCallback } from './command_palette';
import { clearPolling, setCurrentRoute, getCurrentRoute, skeletonHTML, esc } from './utils';
import './styles.css';

// WO-00: Chat ビュー遷移時に tab-nav を自動折り畳みする前の状態を保持
let tabNavStateBeforeChat: boolean | null = null;

// ─── UI Modules ──────────────────────────────────────────────
import { activeGroup, setActiveGroup } from './ui/state';
import { ICON_GROUPS, buildIconRail } from './ui/icon-rail';
import { buildTabNav } from './ui/tab-nav';
import { setupSlidePanel } from './ui/slide-panel';
import { initThemeToggle } from './ui/theme';

// ─── Bootstrap ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  buildIconRail();
  buildTabNav();
  setupNavigation();
  setupSlidePanel();
  localStorage.removeItem('hgk-route'); // アップデート後なので強制リセット
  navigate(DEFAULT_ROUTE);
  // Start global badge polling
  void updateNotifBadge();
  setInterval(() => { void updateNotifBadge(); }, 60_000);
  // PKS auto-push on startup (fire-and-forget)
  void api.pksTriggerPush().catch(() => { /* silent */ });
  // CCL Command Palette — Ctrl+K
  initCommandPalette();
  setNavigateCallback(navigate);
  initKeyboardNav();
  initThemeToggle();
});

// ─── Keyboard Navigation (Ctrl+1‑9,0) ───────────────────────

function initKeyboardNav(): void {
  const keyRouteMap: Record<string, string> = {
    '1': 'dashboard',
    '2': 'notifications',
    '3': 'digestor',
    '4': 'search',
    '5': 'gnosis',
    '6': 'sophia',
    '7': 'pks',
    '8': 'timeline',
    '9': 'fep',
    '0': 'graph',
  };
  document.addEventListener('keydown', (e: KeyboardEvent) => {
    const el = e.target as HTMLElement;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable) return;
    if (!e.ctrlKey || e.shiftKey || e.altKey || e.metaKey) return;
    const route = keyRouteMap[e.key];
    if (route) {
      e.preventDefault();
      navigate(route);
    }
  });
}

// ─── Navigation Setup ────────────────────────────────────────

import { isTabNavOpen, setTabNavOpen, expandedGroup, setExpandedGroup } from './ui/state';

function setupNavigation(): void {
  // Icon Rail: group switching + Obsidian-style expand
  document.getElementById('icon-rail')?.addEventListener('click', (e) => {
    const railBtn = (e.target as HTMLElement).closest('.rail-btn');
    const subBtn = (e.target as HTMLElement).closest('.rail-flyout-item');

    // Sub-item click → navigate directly
    if (subBtn) {
      const route = subBtn.getAttribute('data-route');
      if (route) navigate(route);
      return;
    }

    if (!railBtn) return;

    // Toggle button
    if (railBtn.classList.contains('rail-toggle')) {
      setTabNavOpen(!isTabNavOpen);
      buildIconRail();
      buildTabNav();
      setupTabClickHandlers();
      return;
    }

    const group = railBtn.getAttribute('data-group');
    if (!group) return;

    if (group === expandedGroup) {
      // Click same group → toggle collapse
      setExpandedGroup(null);
    } else {
      setExpandedGroup(group);
    }
    setActiveGroup(group);
    buildIconRail();
    buildTabNav();
    setupTabClickHandlers();

    // Navigate to first route in group if changing group
    const groupDef = ICON_GROUPS.find(g => g.id === group);
    if (groupDef && groupDef.routes.length > 0) {
      const currentRoute = getCurrentRoute();
      const firstRoute = groupDef.routes[0];
      if (firstRoute !== undefined && !groupDef.routes.includes(currentRoute)) {
        navigate(firstRoute);
      }
    }
  });

  setupTabClickHandlers();
}

function setupTabClickHandlers(): void {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const route = btn.getAttribute('data-route');
      if (route) navigate(route);
    });
  });
}

// ─── Nav Badge (CRITICAL count) ──────────────────────────────

async function updateNotifBadge(): Promise<void> {
  try {
    const criticals = await api.notifications(100, 'CRITICAL');
    const count = criticals.length;
    const notifBtn = document.querySelector('.tab-btn[data-route="notifications"]');
    if (!notifBtn) return;
    const existing = notifBtn.querySelector('.nav-badge');
    if (existing) existing.remove();
    if (count > 0) {
      const badge = document.createElement('span');
      badge.className = 'nav-badge';
      badge.textContent = String(count);
      notifBtn.appendChild(badge);
    }
  } catch { /* silent */ }
}

// ─── Navigation ──────────────────────────────────────────────

function navigate(route: string): void {
  if (route === getCurrentRoute()) return;

  const prevRoute = getCurrentRoute();
  setCurrentRoute(route);
  clearPolling();
  recordView(route);

  // WO-00 fix: Chat/Cowork ビューは独自の 3 カラム cw-layout を持つため、
  // tab-nav (アシスタントパネル 280px) を自動折り畳みして全幅を確保する。
  // Chat から離れるときは元の状態を復元する。
  const isChatRoute = route === 'chat' || route === 'cowork';
  const wasChatRoute = prevRoute === 'chat' || prevRoute === 'cowork';

  if (!isChatRoute && wasChatRoute && tabNavStateBeforeChat !== null) {
    // Chat から離れる: 保存していた tab-nav 状態を復元
    if (tabNavStateBeforeChat && !isTabNavOpen) {
      setTabNavOpen(true);
    }
    tabNavStateBeforeChat = null;
  } else if (isChatRoute && !wasChatRoute) {
    // Chat に入る: 現在の tab-nav 状態を保存
    tabNavStateBeforeChat = isTabNavOpen;
  }

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-route') === route);
  });

  // グループが変わった場合は icon rail を更新
  const group = ICON_GROUPS.find(g => g.routes.includes(route));
  if (group && group.id !== activeGroup) {
    setActiveGroup(group.id);
    buildIconRail();
  }

  // WO-00: buildTabNav() は常に呼ぶ (Chat 検出は buildTabNav() 内で行う)
  buildTabNav();
  setupTabClickHandlers();

  const app = document.getElementById('view-content');
  if (!app) return;

  app.classList.remove('view-enter');
  app.classList.add('view-exit');

  setTimeout(() => {
    app.classList.remove('view-exit');
    app.innerHTML = skeletonHTML();
    app.classList.add('view-enter');

    const renderer = ROUTE_MAP[route];
    if (renderer) {
      const timeout = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('応答がタイムアウトしました (10秒)')), 10000)
      );
      Promise.race([renderer(), timeout]).then(() => {
        app.classList.remove('view-enter');
        void app.offsetWidth;
        app.classList.add('view-enter');
      }).catch((err: Error) => {
        const routeLabel = ROUTES.find(r => r.key === route)?.label ?? route;
        app.innerHTML = `
          <div class="error-boundary">
            <div class="error-boundary-icon">⚠️</div>
            <h2>${esc(routeLabel)} を読み込めませんでした</h2>
            <p class="error-boundary-detail">${esc(err.message)}</p>
            <div class="error-boundary-actions">
              <button class="btn error-retry-btn" id="error-retry">再試行</button>
              <button class="btn btn-ghost" id="error-dashboard">Dashboard へ戻る</button>
            </div>
          </div>`;
        document.getElementById('error-retry')?.addEventListener('click', () => {
          setCurrentRoute('');  // force re-navigate
          navigate(route);
        });
        document.getElementById('error-dashboard')?.addEventListener('click', () => {
          setCurrentRoute('');
          navigate('dashboard');
        });
      });
    }
  }, 120);
}

// Expose for E2E testing & DevTools debugging
(window as any).__hgk_navigate = navigate;
