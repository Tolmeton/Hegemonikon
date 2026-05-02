/**
 * Icon Rail — 左端アイコンバー (U1)
 *
 * MECE 認知フロー型 (η→K→Δ→ε→Ω)
 * ホバーでサブルートがフライアウト表示
 */

import { ROUTES, ICON_GROUPS } from '../route-config';
import { getCurrentRoute } from '../utils';
import { activeGroup, isTabNavOpen } from './state';

// Re-export for consumers that used to import from here
export { ICON_GROUPS } from '../route-config';

export function buildIconRail(): void {
  const rail = document.getElementById('icon-rail');
  if (!rail) return;

  let html = '';
  for (const g of ICON_GROUPS) {
    const isActive = g.id === activeGroup;

    // Group wrapper for hover flyout
    html += `<div class="rail-group" data-group="${g.id}">`;

    // Group icon button
    html += `<button class="rail-btn ${isActive ? 'active' : ''}" data-group="${g.id}" title="${g.label}">
      <span class="rail-icon">${g.icon}</span>
    </button>`;

    // Flyout sub-routes (shown on hover)
    html += `<div class="rail-flyout">`;
    html += `<div class="rail-flyout-header">${g.icon} ${g.label}</div>`;
    for (const rKey of g.routes) {
      const route = ROUTES.find(r => r.key === rKey);
      if (!route) continue;
      const isCurrent = rKey === getCurrentRoute();
      html += `<button class="rail-flyout-item ${isCurrent ? 'active' : ''}" data-route="${route.key}">
        <span class="rail-flyout-icon">${route.icon}</span>
        <span class="rail-flyout-label">${route.label}</span>
      </button>`;
    }
    html += `</div>`; // .rail-flyout
    html += `</div>`; // .rail-group
  }

  // Tab nav toggle at bottom
  html += `<div class="rail-spacer"></div>`;
  html += `<button class="rail-btn rail-toggle" title="${isTabNavOpen ? 'タブを閉じる' : 'タブを開く'}">
    <span class="rail-icon">${isTabNavOpen ? '◀' : '▶'}</span>
  </button>`;

  rail.innerHTML = html;
}
