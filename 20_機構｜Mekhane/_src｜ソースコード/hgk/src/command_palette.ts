import './views/css/interactive.css';
/**
 * CCL Command Palette — Ctrl+K で起動するコマンドパレット
 *
 * kalon: ワークフローと CCL 式を「問い」のように手元に呼ぶ
 *
 * 機能:
 *   - Ctrl+K / Cmd+K でオーバーレイ表示
 *   - WF 名でフィルター打鍵 → 候補表示
 *   - CCL 式 (/ で始まる) を直接入力 → parse → 結果表示
 *   - Enter で WF 詳細 or CCL 実行
 */

import { api } from './api/client';
import type { WFSummary, CCLParseResponse, CCLExecuteResponse, SynteleiaAuditResponse } from './api/client';
import { esc } from './utils';
import { ROUTES } from './route-config';

// --- State ---

let paletteEl: HTMLElement | null = null;
let isOpen = false;
let navigateFn: ((route: string) => void) | null = null;
const recentViews: string[] = JSON.parse(localStorage.getItem('hgk-recent-views') || '[]');

/** Register navigate callback from main.ts */
export function setNavigateCallback(fn: (route: string) => void): void {
  navigateFn = fn;
}
let wfCache: WFSummary[] = [];

function trackRecentView(key: string): void {
  const idx = recentViews.indexOf(key);
  if (idx !== -1) recentViews.splice(idx, 1);
  recentViews.unshift(key);
  if (recentViews.length > 5) recentViews.length = 5;
  localStorage.setItem('hgk-recent-views', JSON.stringify(recentViews));
}

// --- HTML ---

function createPaletteHTML(): string {
  return `
    <div class="cp-overlay" id="cp-overlay">
      <div class="cp-dialog">
        <div class="cp-input-wrapper">
          <span class="cp-icon">⌘</span>
          <input type="text" id="cp-input" class="cp-input" placeholder="Type a workflow name or CCL expression..." autocomplete="off" />
          <kbd class="cp-kbd">ESC</kbd>
        </div>
        <div class="cp-results" id="cp-results"></div>
        <div class="cp-footer">
          <span>↑↓ Navigate</span>
          <span>↵ Execute</span>
          <span>ESC Close</span>
        </div>
      </div>
    </div>
  `;
}

// --- Rendering ---

function renderWFItems(items: WFSummary[]): string {
  if (items.length === 0) {
    return '<div class="cp-empty">No matching workflows</div>';
  }
  return items.map((wf, i) => `
    <div class="cp-item ${i === 0 ? 'cp-item-active' : ''}" data-idx="${i}" data-name="${esc(wf.name)}" data-ccl="${esc(wf.ccl)}">
      <div class="cp-item-header">
        <span class="cp-item-name">/${esc(wf.name)}</span>
        ${wf.ccl ? `<span class="cp-item-ccl">${esc(wf.ccl)}</span>` : ''}
      </div>
      <div class="cp-item-desc">${esc(wf.description)}</div>
      ${wf.modes.length > 0 ? `<div class="cp-item-modes">${wf.modes.map(m => `<span class="cp-mode-tag">${esc(m)}</span>`).join('')}</div>` : ''}
    </div>
  `).join('');
}

function renderParseResult(res: CCLParseResponse): string {
  if (!res.success) {
    return `<div class="cp-parse-error">❌ ${esc(res.error ?? 'Parse failed')}</div>`;
  }
  return `
    <div class="cp-parse-result">
      <div class="cp-parse-header">✅ Parsed: <code>${esc(res.ccl)}</code></div>
      ${res.tree ? `<pre class="cp-parse-tree">${esc(res.tree)}</pre>` : ''}
      ${res.workflows.length > 0 ? `
        <div class="cp-parse-wfs">
          <strong>Workflows:</strong> ${res.workflows.map(w => `<span class="cp-mode-tag">${esc(w)}</span>`).join(' ')}
        </div>
      ` : ''}
      ${res.plan_template ? `<pre class="cp-parse-plan">${esc(res.plan_template)}</pre>` : ''}
      <div class="cp-execute-bar">
        <button class="cp-execute-btn" data-ccl="${esc(res.ccl)}">▶ Synergeia 実行</button>
        <div class="cp-execute-result" id="cp-exec-result"></div>
      </div>
    </div>
  `;
}

/** Bind execute button's click event */
function initExecuteButton(resultsEl: HTMLElement): void {
  const btn = resultsEl.querySelector('.cp-execute-btn') as HTMLButtonElement | null;
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const ccl = btn.dataset.ccl ?? '';
    const resultDiv = resultsEl.querySelector('#cp-exec-result')!;
    btn.disabled = true;
    btn.textContent = '⏳ 実行中...';
    resultDiv.innerHTML = '';
    try {
      const res: CCLExecuteResponse = await api.cclExecute(ccl);
      if (res.success) {
        const detail = res.result ? JSON.stringify(res.result, null, 2) : 'OK';
        resultDiv.innerHTML = `<div class="cp-exec-ok">✅ 実行成功<pre>${esc(detail.substring(0, 500))}</pre></div>`;
      } else {
        resultDiv.innerHTML = `<div class="cp-parse-error">❌ ${esc(res.error ?? '実行失敗')}</div>`;
      }
    } catch (e) {
      resultDiv.innerHTML = `<div class="cp-parse-error">❌ ${esc((e as Error).message)}</div>`;
    }
    btn.disabled = false;
    btn.textContent = '▶ Synergeia 実行';
  });
}

// --- Kalon Judge ---

function renderAuditResult(res: SynteleiaAuditResponse): string {
  const badge = res.passed
    ? '<span class="syn-badge syn-pass">✅ PASS</span>'
    : '<span class="syn-badge syn-fail">❌ FAIL</span>';

  const issueRows = resnous_results.map(ar => {
    const icon = ar.passed ? '✅' : '⚠️';
    const issueList = ar.issues.length > 0
      ? ar.issues.map(i =>
        `<div class="syn-issue syn-sev-${esc(i.severity.toLowerCase())}">[${esc(i.severity)}] ${esc(i.message)}</div>`
      ).join('')
      : '';
    return `<div class="syn-agent">
            <div class="syn-agent-header">${icon} <strong>${esc(arnous_name)}</strong> <span class="syn-confidence">${(ar.confidence * 100).toFixed(0)}%</span></div>
            ${issueList}
        </div>`;
  }).join('');

  const wbcNote = res.wbc_alerted
    ? '<div class="syn-wbc-alert">🚨 WBC アラート送信済み</div>'
    : '';

  return `<div class="syn-result">
        <div class="syn-header">${badge} <span class="syn-summary">${esc(res.summary)}</span></div>
        <div class="syn-stats">
            問題: <strong>${res.total_issues}</strong>件
            (CRITICAL: ${res.critical_count} / HIGH: ${res.high_count})
        </div>
        ${wbcNote}
        <div class="syn-agents">${issueRows}</div>
    </div>`;
}

function renderKalonJudge(concept: string): string {
  const id = `kalon-${Date.now()}`;
  return `
    <div class="kalon-judge" id="${id}">
      <div class="kalon-header">
        <span class="kalon-icon">◆</span>
        <span class="kalon-title">Kalon 判定: <code>${esc(concept)}</code></span>
      </div>
      <div class="kalon-definition">Fix(G∘F) ∧ Presheaf ∧ Self-referential</div>

      <div class="kalon-step" data-step="g">
        <div class="kalon-step-label">Step 1: G テスト（蒸留）</div>
        <div class="kalon-step-question">これ以上蒸留しても変化しないか？</div>
        <div class="kalon-step-buttons">
          <button class="kalon-btn kalon-btn-yes" data-answer="yes" data-target="${id}">はい — 不変 ✅</button>
          <button class="kalon-btn kalon-btn-no" data-answer="no" data-target="${id}">いいえ — まだ圧縮可能</button>
        </div>
      </div>

      <div class="kalon-step" data-step="f">
        <div class="kalon-step-label">Step 2: F テスト（展開）</div>
        <div class="kalon-step-question">ここから3つ以上の新しい概念を導出できるか？</div>
        <div class="kalon-step-buttons">
          <button class="kalon-btn kalon-btn-yes" data-answer="yes" data-target="${id}">はい — 3+ 導出可 ✅</button>
          <button class="kalon-btn kalon-btn-no" data-answer="no" data-target="${id}">いいえ — 展開なし</button>
        </div>
      </div>

      <div class="kalon-result" id="${id}-result">
        <div class="kalon-result-pending">↑ G/F テストに回答してください</div>
      </div>

      <div class="kalon-attrs">
        <span class="kalon-attr" title="Fix(G∘F) — 不動点">Fix</span>
        <span class="kalon-attr" title="Presheaf — 多面性">Presheaf</span>
        <span class="kalon-attr" title="Self-referential — 自己参照">Self-ref</span>
      </div>
    </div>
  `;
}

function initKalonButtons(resultsEl: HTMLElement): void {
  const judge = resultsEl.querySelector('.kalon-judge') as HTMLElement;
  if (!judge) return;

  let gAnswer: boolean | null = null;
  let fAnswer: boolean | null = null;

  judge.querySelectorAll('.kalon-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const step = (btn.closest('.kalon-step') as HTMLElement)?.dataset.step;
      const answer = (btn as HTMLElement).dataset.answer === 'yes';

      // Highlight selected button
      const stepEl = btn.closest('.kalon-step')!;
      stepEl.querySelectorAll('.kalon-btn').forEach(b => b.classList.remove('kalon-btn-selected'));
      btn.classList.add('kalon-btn-selected');

      if (step === 'g') gAnswer = answer;
      if (step === 'f') fAnswer = answer;

      // Update result when both answered
      if (gAnswer !== null && fAnswer !== null) {
        const resultEl = judge.querySelector('.kalon-result')!;
        if (gAnswer && fAnswer) {
          resultEl.innerHTML = `
                      <div class="kalon-result-kalon">
                        <span class="kalon-verdict-icon">◎</span>
                        <span class="kalon-verdict-text">kalon — Fix(G∘F) に到達</span>
                      </div>`;
        } else if (gAnswer && !fAnswer) {
          resultEl.innerHTML = `
                      <div class="kalon-result-partial">
                        <span class="kalon-verdict-icon">✗</span>
                        <span class="kalon-verdict-text">自明 — lim だが colim なし (π パターン)</span>
                      </div>`;
        } else if (!gAnswer && fAnswer) {
          resultEl.innerHTML = `
                      <div class="kalon-result-partial">
                        <span class="kalon-verdict-icon">◯</span>
                        <span class="kalon-verdict-text">許容 — もう一回 G∘F を回すと改善</span>
                      </div>`;
        } else {
          resultEl.innerHTML = `
                      <div class="kalon-result-fail">
                        <span class="kalon-verdict-icon">✗</span>
                        <span class="kalon-verdict-text">要蒸留 — Fix から遠い</span>
                      </div>`;
        }
      }
    });
  });
}

// --- Quick Actions ---

interface QuickAction {
  label: string;
  icon: string;
  description: string;
  action: (arg: string) => void;
}

function renderRouteItems(filter: string): string {
  const q = filter.toLowerCase();
  const routes = q
    ? ROUTES.filter(r => r.key.includes(q) || r.label.toLowerCase().includes(q))
    : (recentViews.length > 0
      ? recentViews.map(k => ROUTES.find(r => r.key === k)).filter(Boolean) as typeof ROUTES
      : ROUTES.slice(0, 6));
  if (routes.length === 0) return '';
  const sectionLabel = !q && recentViews.length > 0 ? '最近のビュー' : 'ビュー';
  return `<div class="cp-section-label">${sectionLabel}</div>` +
    routes.map((r, i) => `
      <div class="cp-item cp-route-item ${i === 0 ? 'cp-item-active' : ''}" data-idx="${i}" data-route="${esc(r.key)}">
        <div class="cp-item-header">
          <span class="cp-item-icon">${r.icon}</span>
          <span class="cp-item-name">${esc(r.label)}</span>
        </div>
      </div>
    `).join('');
}

function getQuickActions(): QuickAction[] {
  return [
    {
      label: 'nav',
      icon: '🧭',
      description: 'ビュー遷移 (例: >nav dashboard)',
      action: (arg: string) => {
        if (!navigateFn) return;
        const match = ROUTES.find(r => r.key === arg || r.label.toLowerCase() === arg.toLowerCase());
        if (match) {
          navigateFn(match.key);
          closePalette();
        }
      },
    },
    {
      label: 'theme',
      icon: '🎨',
      description: 'テーマ切替 (dark/light)',
      action: (arg: string) => {
        const next = arg === 'light' ? 'light' : arg === 'dark' ? 'dark'
          : document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('hgk-theme', next);
        const btn = document.querySelector('.theme-toggle');
        if (btn) btn.textContent = next === 'dark' ? '☀️' : '🌙';
        closePalette();
      },
    },
    {
      label: 'pks',
      icon: '📡',
      description: 'PKS プッシュ実行',
      action: () => {
        void api.pksTriggerPush().then(() => {
          if (navigateFn) { navigateFn('pks'); closePalette(); }
        });
      },
    },
    {
      label: 'postcheck',
      icon: '🔄',
      description: 'ポストチェック実行 (例: >postcheck /noe)',
      action: (arg: string) => {
        if (arg && navigateFn) {
          navigateFn('postcheck');
          closePalette();
        }
      },
    },
  ];
}

function renderQuickActions(filter: string): string {
  const actions = getQuickActions().filter(a =>
    !filter || a.label.includes(filter) || a.description.includes(filter)
  );
  if (actions.length === 0) return '';
  return `<div class="cp-section-label">Quick Actions</div>` +
    actions.map((a, i) => `
      <div class="cp-item cp-quick-action ${i === 0 ? 'cp-item-active' : ''}" data-idx="${i}" data-action="${esc(a.label)}">
        <div class="cp-item-header">
          <span class="cp-item-name">${a.icon} >${esc(a.label)}</span>
        </div>
        <div class="cp-item-desc">${esc(a.description)}</div>
      </div>
    `).join('');
}

// --- Logic ---



async function loadWorkflows(): Promise<void> {
  if (wfCache.length > 0) return;
  try {
    const res = await api.wfList();
    wfCache = res.workflows;
  } catch {
    wfCache = [];
  }
}

function filterWorkflows(query: string): WFSummary[] {
  const q = query.toLowerCase().replace(/^\//, '');
  if (!q) return wfCache.slice(0, 15);
  return wfCache.filter(wf =>
    wf.name.toLowerCase().includes(q) ||
    wf.description.toLowerCase().includes(q) ||
    wf.ccl.toLowerCase().includes(q)
  ).slice(0, 15);
}

let activeIdx = 0;

function updateActive(resultsEl: HTMLElement, delta: number): void {
  const items = resultsEl.querySelectorAll('.cp-item');
  if (items.length === 0) return;
  items[activeIdx]?.classList.remove('cp-item-active');
  activeIdx = Math.max(0, Math.min(items.length - 1, activeIdx + delta));
  items[activeIdx]?.classList.add('cp-item-active');
  (items[activeIdx] as HTMLElement)?.scrollIntoView({ block: 'nearest' });
}

async function handleInput(input: HTMLInputElement, resultsEl: HTMLElement): Promise<void> {
  const val = input.value.trim();

  // Quick action commands (>nav, >theme, >pks, >postcheck)
  if (val.startsWith('>')) {
    const parts = val.slice(1).split(/\s+/);
    const cmd = parts[0]?.toLowerCase() ?? '';
    const arg = parts.slice(1).join(' ');
    const actions = getQuickActions();
    const match = actions.find(a => a.label === cmd);
    if (match) {
      // Show confirmation then execute on Enter
      resultsEl.innerHTML = `
        <div class="cp-parse-result">
          <div class="cp-parse-header">${match.icon} <strong>>${esc(match.label)}</strong> ${arg ? esc(arg) : ''}</div>
          <div class="cp-item-desc">${esc(match.description)}</div>
          <div class="cp-execute-bar">
            <button class="cp-execute-btn" id="cp-quick-exec">▶ 実行</button>
          </div>
        </div>`;
      const btn = resultsEl.querySelector('#cp-quick-exec');
      btn?.addEventListener('click', () => match.action(arg));
      return;
    }
    // Show filtered quick actions
    resultsEl.innerHTML = renderQuickActions(cmd);
    activeIdx = 0;
    // Click handlers for quick action items
    resultsEl.querySelectorAll('.cp-quick-action').forEach(item => {
      item.addEventListener('click', () => {
        const actionLabel = (item as HTMLElement).dataset.action ?? '';
        input.value = `>${actionLabel} `;
        void handleInput(input, resultsEl);
      });
    });
    return;
  }

  // Synteleia audit command
  if (val.toLowerCase().startsWith('audit ')) {
    const content = val.slice(6).trim();
    if (content) {
      resultsEl.innerHTML = '<div class="cp-loading">🔍 Synteleia 監査中...</div>';
      try {
        const res: SynteleiaAuditResponse = await api.synteleiaAudit(content);
        resultsEl.innerHTML = renderAuditResult(res);
      } catch (e) {
        resultsEl.innerHTML = `<div class="cp-parse-error">❌ 監査エラー: ${esc((e as Error).message)}</div>`;
      }
      return;
    }
  }

  // Kalon judge command
  if (val.toLowerCase().startsWith('kalon ')) {
    const concept = val.slice(6).trim();
    if (concept) {
      resultsEl.innerHTML = renderKalonJudge(concept);
      initKalonButtons(resultsEl);
      return;
    }
  }

  // CCL expression (contains operators like +, >>, ~, etc.)
  if (val && /[+>~{(\\]/.test(val)) {
    resultsEl.innerHTML = '<div class="cp-loading">Parsing CCL...</div>';
    try {
      const res: CCLParseResponse = await api.cclParse(val);
      resultsEl.innerHTML = renderParseResult(res);
      initExecuteButton(resultsEl);
    } catch (e) {
      resultsEl.innerHTML = `<div class="cp-parse-error">❌ ${esc((e as Error).message)}</div>`;
    }
    return;
  }

  // Workflow filter
  const filtered = filterWorkflows(val);
  activeIdx = 0;
  // Show route navigation + workflow list
  const routeSection = renderRouteItems(val);
  resultsEl.innerHTML = routeSection +
    (filtered.length > 0 ? `<div class="cp-section-label">ワークフロー</div>` : '') +
    renderWFItems(filtered);

  // Click handlers — routes
  resultsEl.querySelectorAll('.cp-route-item').forEach(item => {
    item.addEventListener('click', () => {
      const route = (item as HTMLElement).dataset.route ?? '';
      if (navigateFn && route) {
        trackRecentView(route);
        navigateFn(route);
        closePalette();
      }
    });
  });
  // Click handlers — workflows
  resultsEl.querySelectorAll('.cp-item:not(.cp-route-item):not(.cp-quick-action)').forEach(item => {
    item.addEventListener('click', () => {
      const name = (item as HTMLElement).dataset.name ?? '';
      selectWorkflow(name, resultsEl);
    });
  });
}

async function selectWorkflow(name: string, resultsEl: HTMLElement): Promise<void> {
  resultsEl.innerHTML = '<div class="cp-loading">Loading workflow...</div>';
  try {
    const detail = await api.wfDetail(name);
    resultsEl.innerHTML = `
      <div class="cp-wf-detail">
        <h3>/${esc(detail.name)}</h3>
        <p>${esc(detail.description)}</p>
        ${detail.ccl ? `<div class="cp-wf-ccl"><strong>CCL:</strong> <code>${esc(detail.ccl)}</code></div>` : ''}
        ${detail.modes.length > 0 ? `<div class="cp-wf-modes"><strong>Modes:</strong> ${detail.modes.map(m => `<span class="cp-mode-tag">${esc(m)}</span>`).join(' ')}</div>` : ''}
        ${detail.stages.length > 0 ? `
          <div class="cp-wf-stages">
            <strong>Stages:</strong>
            <ol>${detail.stages.map(s => `<li>${esc(s.name || s.description || '')}</li>`).join('')}</ol>
          </div>
        ` : ''}
      </div>
    `;
  } catch (e) {
    resultsEl.innerHTML = `<div class="cp-parse-error">❌ ${esc((e as Error).message)}</div>`;
  }
}

// --- Open / Close ---

export function openPalette(): void {
  if (isOpen) return;
  isOpen = true;

  // Inject HTML
  const container = document.createElement('div');
  container.innerHTML = createPaletteHTML();
  paletteEl = container.firstElementChild as HTMLElement;
  document.body.appendChild(paletteEl);

  const input = document.getElementById('cp-input') as HTMLInputElement;
  const resultsEl = document.getElementById('cp-results')!;
  const overlay = document.getElementById('cp-overlay')!;

  // Load WFs and show initial list
  void loadWorkflows().then(() => {
    void handleInput(input, resultsEl);
  });

  // Input handler (debounced)
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  input.addEventListener('input', () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => void handleInput(input, resultsEl), 150);
  });

  // Keyboard navigation
  input.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      closePalette();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      updateActive(resultsEl, 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      updateActive(resultsEl, -1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const activeItem = resultsEl.querySelector('.cp-item-active') as HTMLElement;
      if (activeItem) {
        const name = activeItem.dataset.name ?? '';
        void selectWorkflow(name, resultsEl);
      }
    }
  });

  // Click outside to close
  overlay.addEventListener('click', (e: MouseEvent) => {
    if (e.target === overlay) closePalette();
  });

  // Focus input
  requestAnimationFrame(() => input.focus());
}

export function closePalette(): void {
  if (!isOpen || !paletteEl) return;
  isOpen = false;
  paletteEl.remove();
  paletteEl = null;
  activeIdx = 0;
}

export function togglePalette(): void {
  isOpen ? closePalette() : openPalette();
}

// --- Global Keyboard Shortcut ---

export function initCommandPalette(): void {
  document.addEventListener('keydown', (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      togglePalette();
    }
  });
}

/**
 * Open the command palette with a pre-filled query.
 * Used by Graph → WF link integration.
 */
export function openPaletteWithQuery(query: string): void {
  openPalette();
  // Defer to ensure DOM is ready
  requestAnimationFrame(() => {
    const input = document.getElementById('cp-input') as HTMLInputElement | null;
    const resultsEl = document.getElementById('cp-results');
    if (input && resultsEl) {
      input.value = query;
      void handleInput(input, resultsEl);
    }
  });
}
