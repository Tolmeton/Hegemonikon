/**
 * Cowork View — Claude.AI × HGK Gateway 統合ダッシュボード
 *
 * Claude.AI の Cowork セッションが Gateway 経由で実行した
 * Jules タスク・Cortex 呼び出し・Research を可視化する。
 */

import { api } from '../api/client';

// ─── Types ───────────────────────────────────────────────────

interface TraceEntry {
    timestamp: string;
    tool_name: string;
    input_size: number;
    duration_ms: number;
    success: boolean;
}

interface CoworkState {
    traces: TraceEntry[];
    gatewayHealth: { result: string } | null;
    lastRefresh: Date | null;
    autoRefresh: boolean;
    refreshTimer: number | null;
}

const state: CoworkState = {
    traces: [],
    gatewayHealth: null,
    lastRefresh: null,
    autoRefresh: false,
    refreshTimer: null,
};

// ─── Utilities ───────────────────────────────────────────────

function esc(s: string): string {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function toolIcon(name: string): string {
    if (name.startsWith('hgk_jules')) return '⚡';
    if (name.startsWith('hgk_research')) return '🔬';
    if (name.startsWith('hgk_ask')) return '🤖';
    if (name.startsWith('hgk_chat')) return '💬';
    if (name.startsWith('hgk_search') || name.startsWith('hgk_pks')) return '🔍';
    if (name.startsWith('hgk_digest')) return '🧬';
    if (name.startsWith('hgk_ccl')) return '🔗';
    return '🔧';
}

function toolCategory(name: string): string {
    if (name.startsWith('hgk_jules')) return 'Jules';
    if (name.startsWith('hgk_research')) return 'Research';
    if (name.startsWith('hgk_ask') || name.startsWith('hgk_chat')) return 'Cortex';
    if (name.startsWith('hgk_search') || name.startsWith('hgk_pks')) return 'Search';
    if (name.startsWith('hgk_digest')) return 'Digest';
    return 'Other';
}

function formatDuration(ms: number): string {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
}

function timeAgo(dateStr: string): string {
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now.getTime() - then.getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return '今';
    if (mins < 60) return `${mins}分前`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}時間前`;
    return `${Math.floor(hours / 24)}日前`;
}

// ─── Data Loading ────────────────────────────────────────────

async function loadTraces(): Promise<TraceEntry[]> {
    try {
        const resp = await fetch('/api/hgk/gateway/trace');
        if (!resp.ok) return [];
        const data = await resp.json();
        return data.traces || [];
    } catch {
        return [];
    }
}

async function refreshData(): Promise<void> {
    const [traces, health] = await Promise.all([
        loadTraces(),
        api.hgkGatewayHealth().catch(() => null),
    ]);
    state.traces = traces;
    state.gatewayHealth = health;
    state.lastRefresh = new Date();
    render();
}

// ─── Render Components ───────────────────────────────────────

function renderSummaryCards(): string {
    const traces = state.traces;
    const total = traces.length;
    const success = traces.filter(t => t.success).length;
    const rate = total > 0 ? ((success / total) * 100).toFixed(0) : '—';

    // Category breakdown
    const cats: Record<string, number> = {};
    traces.forEach(t => {
        const cat = toolCategory(t.tool_name);
        cats[cat] = (cats[cat] || 0) + 1;
    });

    // Total duration
    const totalMs = traces.reduce((s, t) => s + t.duration_ms, 0);

    return `
        <div class="cowork-summary">
            <div class="summary-card">
                <div class="summary-number">${total}</div>
                <div class="summary-label">Total Calls</div>
            </div>
            <div class="summary-card ${parseInt(rate) >= 90 ? 'success' : parseInt(rate) >= 70 ? 'warning' : 'error'}">
                <div class="summary-number">${rate}%</div>
                <div class="summary-label">Success Rate</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">${formatDuration(totalMs)}</div>
                <div class="summary-label">Total Time</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">${Object.keys(cats).length}</div>
                <div class="summary-label">Categories</div>
            </div>
        </div>
        <div class="cowork-categories">
            ${Object.entries(cats)
            .sort((a, b) => b[1] - a[1])
            .map(([cat, count]) => `<span class="cat-badge">${cat}: ${count}</span>`)
            .join('')}
        </div>
    `;
}

function renderToolTable(): string {
    const traces = state.traces.slice(-50).reverse(); // Latest 50

    if (traces.length === 0) {
        return `
            <div class="cowork-empty">
                <div class="empty-icon">📡</div>
                <div class="empty-text">Gateway トレースなし</div>
                <div class="empty-sub">Claude.AI が Gateway ツールを使うとここに表示されます</div>
            </div>
        `;
    }

    const rows = traces.map(t => `
        <tr class="${t.success ? '' : 'error-row'}">
            <td class="tool-icon">${toolIcon(t.tool_name)}</td>
            <td class="tool-name">${esc(t.tool_name.replace('hgk_', ''))}</td>
            <td class="tool-status">${t.success ? '✅' : '❌'}</td>
            <td class="tool-input">${t.input_size > 0 ? t.input_size + ' chars' : '—'}</td>
            <td class="tool-duration">${formatDuration(t.duration_ms)}</td>
            <td class="tool-time">${timeAgo(t.timestamp)}</td>
        </tr>
    `).join('');

    return `
        <table class="cowork-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Tool</th>
                    <th>Status</th>
                    <th>Input</th>
                    <th>Duration</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function renderGatewayStatus(): string {
    const h = state.gatewayHealth;
    if (!h) return '<div class="gateway-status offline">Gateway: 未接続</div>';
    return `<div class="gateway-status online">Gateway: ✅</div>`;
}

// ─── Main Render ─────────────────────────────────────────────

function render(): void {
    const el = document.getElementById('main-content');
    if (!el) return;

    const refreshLabel = state.lastRefresh
        ? `最終更新: ${state.lastRefresh.toLocaleTimeString('ja-JP')}`
        : '';

    el.innerHTML = `
        <div class="cowork-view">
            <div class="cowork-header">
                <div class="cowork-title">
                    <h2>🤝 Cowork Dashboard</h2>
                    <span class="cowork-subtitle">Claude.AI × HGK Gateway</span>
                </div>
                <div class="cowork-controls">
                    ${renderGatewayStatus()}
                    <button id="cowork-refresh" class="btn-refresh">🔄 更新</button>
                    <label class="auto-refresh-label">
                        <input type="checkbox" id="cowork-auto" ${state.autoRefresh ? 'checked' : ''}>
                        Auto (30s)
                    </label>
                    <span class="refresh-time">${refreshLabel}</span>
                </div>
            </div>

            ${renderSummaryCards()}

            <div class="cowork-section">
                <h3>📋 ツール実行ログ</h3>
                ${renderToolTable()}
            </div>
        </div>

        <style>
            .cowork-view {
                padding: 24px;
                max-width: 1200px;
                margin: 0 auto;
                color: var(--text-primary, #e8e6e3);
            }
            .cowork-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
                flex-wrap: wrap;
                gap: 12px;
            }
            .cowork-title h2 {
                margin: 0;
                font-size: 1.5rem;
            }
            .cowork-subtitle {
                opacity: 0.6;
                font-size: 0.85rem;
            }
            .cowork-controls {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .gateway-status {
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8rem;
            }
            .gateway-status.online {
                background: rgba(76, 175, 80, 0.2);
                color: #81c784;
            }
            .gateway-status.offline {
                background: rgba(244, 67, 54, 0.2);
                color: #e57373;
            }
            .btn-refresh {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                color: inherit;
                padding: 6px 14px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.85rem;
            }
            .btn-refresh:hover {
                background: rgba(255,255,255,0.15);
            }
            .auto-refresh-label {
                font-size: 0.8rem;
                opacity: 0.7;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .refresh-time {
                font-size: 0.75rem;
                opacity: 0.5;
            }
            .cowork-summary {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 16px;
            }
            .summary-card {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            }
            .summary-card.success { border-color: rgba(76,175,80,0.4); }
            .summary-card.warning { border-color: rgba(255,193,7,0.4); }
            .summary-card.error { border-color: rgba(244,67,54,0.4); }
            .summary-number {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1;
            }
            .summary-label {
                font-size: 0.75rem;
                opacity: 0.6;
                margin-top: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .cowork-categories {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 24px;
            }
            .cat-badge {
                background: rgba(255,255,255,0.08);
                padding: 4px 10px;
                border-radius: 16px;
                font-size: 0.75rem;
            }
            .cowork-section h3 {
                margin-bottom: 12px;
                font-size: 1.1rem;
            }
            .cowork-table {
                width: 100%;
                border-collapse: collapse;
            }
            .cowork-table th {
                text-align: left;
                padding: 8px 12px;
                border-bottom: 2px solid rgba(255,255,255,0.15);
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.6;
            }
            .cowork-table td {
                padding: 10px 12px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
                font-size: 0.85rem;
            }
            .cowork-table tr:hover {
                background: rgba(255,255,255,0.03);
            }
            .error-row { background: rgba(244,67,54,0.05); }
            .tool-icon { width: 30px; text-align: center; font-size: 1.1rem; }
            .tool-name { font-family: monospace; }
            .tool-duration { font-family: monospace; opacity: 0.7; }
            .tool-time { opacity: 0.5; font-size: 0.75rem; }
            .cowork-empty {
                text-align: center;
                padding: 60px 20px;
                opacity: 0.5;
            }
            .empty-icon { font-size: 3rem; margin-bottom: 16px; }
            .empty-text { font-size: 1.2rem; margin-bottom: 8px; }
            .empty-sub { font-size: 0.85rem; }
        </style>
    `;

    // Wire up events
    document.getElementById('cowork-refresh')?.addEventListener('click', () => refreshData());
    document.getElementById('cowork-auto')?.addEventListener('change', (e) => {
        state.autoRefresh = (e.target as HTMLInputElement).checked;
        if (state.autoRefresh) {
            state.refreshTimer = window.setInterval(() => refreshData(), 30000);
        } else if (state.refreshTimer) {
            clearInterval(state.refreshTimer);
            state.refreshTimer = null;
        }
    });
}

// ─── Export ──────────────────────────────────────────────────

export async function renderCoworkView(): Promise<void> {
    await refreshData();
}
