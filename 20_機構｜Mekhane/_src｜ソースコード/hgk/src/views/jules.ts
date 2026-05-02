/**
 * Jules View — Async Coding Agent Dashboard
 *
 * Jules API (v1alpha) 経由で GitHub リポジトリ上の非同期コーディングタスクを管理。
 * タスク作成・ステータス監視・PR確認を HGK から一元管理。
 */
import './css/interactive.css';

// ─── Types ───────────────────────────────────────────────────

interface JulesSource {
    name: string;
    [key: string]: unknown;
}

interface JulesSession {
    name?: string;
    id?: string;
    title?: string;
    prompt?: string;
    state?: string;
    outputs?: { pullRequest?: { url: string; title: string; description: string } }[];
    createTime?: string;
    [key: string]: unknown;
}

// ─── State ───────────────────────────────────────────────────

let sources: JulesSource[] = [];
let sessions: JulesSession[] = [];
let selectedSource = '';
let isLoading = false;
// let pollingSessions: Set<string> = new Set(); // TODO: use for auto-poll

const API = '/api/jules';

// ─── API ─────────────────────────────────────────────────────

function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

async function fetchSources(): Promise<JulesSource[]> {
    const res = await fetch(`${API}/sources`);
    if (!res.ok) throw new Error(`${res.status}`);
    const data = await res.json();
    return data.sources || [];
}

async function fetchSessions(): Promise<JulesSession[]> {
    const res = await fetch(`${API}/sessions?page_size=30`);
    if (!res.ok) throw new Error(`${res.status}`);
    const data = await res.json();
    return data.sessions || [];
}

async function createSession(prompt: string, source: string, title: string, branch: string, requireApproval: boolean): Promise<JulesSession> {
    const res = await fetch(`${API}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, source, title, branch, require_plan_approval: requireApproval }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
        throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
}

async function fetchSessionDetail(id: string): Promise<JulesSession> {
    const res = await fetch(`${API}/sessions/${id}`);
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json();
}

async function approvePlan(id: string): Promise<void> {
    await fetch(`${API}/sessions/${id}/approve`, { method: 'POST' });
}

async function sendMessage(id: string, message: string): Promise<void> {
    await fetch(`${API}/sessions/${id}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
    });
}

// ─── Render ──────────────────────────────────────────────────

function stateEmoji(state?: string): string {
    switch (state) {
        case 'COMPLETED': return '✅';
        case 'FAILED': return '❌';
        case 'CANCELLED': return '🚫';
        case 'RUNNING': return '⚡';
        case 'PLANNING': return '📋';
        case 'WAITING_FOR_APPROVAL': return '⏳';
        default: return '🔄';
    }
}

function stateClass(state?: string): string {
    switch (state) {
        case 'COMPLETED': return 'jules-state-done';
        case 'FAILED': case 'CANCELLED': return 'jules-state-fail';
        case 'RUNNING': case 'PLANNING': return 'jules-state-active';
        default: return 'jules-state-pending';
    }
}

function renderSessionCard(s: JulesSession): string {
    const pr = s.outputs?.[0]?.pullRequest;
    const prLink = pr ? `<a href="${esc(pr.url)}" target="_blank" class="jules-pr-link">🔗 ${esc(pr.title || 'PR')}</a>` : '';
    const time = s.createTime ? new Date(s.createTime).toLocaleString('ja-JP') : '';

    return `
    <div class="jules-session-card ${stateClass(s.state)}" data-session-id="${esc(s.id || '')}">
        <div class="jules-session-header">
            <span class="jules-state-badge">${stateEmoji(s.state)} ${esc(s.state || 'UNKNOWN')}</span>
            <span class="jules-session-time">${time}</span>
        </div>
        <div class="jules-session-title">${esc(s.title || s.prompt?.slice(0, 80) || '(no title)')}</div>
        <div class="jules-session-prompt">${esc(s.prompt?.slice(0, 200) || '')}</div>
        ${prLink}
        <div class="jules-session-actions">
            ${s.state === 'WAITING_FOR_APPROVAL' ? `<button class="btn btn-sm jules-approve-btn" data-id="${esc(s.id || '')}">✅ Plan 承認</button>` : ''}
            <button class="btn btn-sm btn-outline jules-detail-btn" data-id="${esc(s.id || '')}">詳細</button>
            ${s.state === 'RUNNING' || s.state === 'PLANNING' ? `<button class="btn btn-sm btn-outline jules-msg-btn" data-id="${esc(s.id || '')}">💬 メッセージ</button>` : ''}
        </div>
    </div>`;
}

function render(): void {
    const app = document.getElementById('view-content');
    if (!app) return;

    const sourceOptions = sources.map(s =>
        `<option value="${esc(s.name)}" ${s.name === selectedSource ? 'selected' : ''}>${esc(s.name.replace('sources/github/', ''))}</option>`
    ).join('');

    app.innerHTML = `
    <div class="jules-container">
        <div class="jules-header">
            <h2 class="view-title">⚡ Jules — Async Coding Agent</h2>
            <div class="jules-header-actions">
                <button id="jules-refresh" class="btn btn-sm btn-outline" ${isLoading ? 'disabled' : ''}>🔄 更新</button>
            </div>
        </div>

        <div class="jules-create-panel">
            <div class="jules-create-row">
                <select id="jules-source" class="jules-select">
                    <option value="">リポジトリを選択...</option>
                    ${sourceOptions}
                </select>
                <input id="jules-branch" class="jules-input" type="text" value="main" placeholder="ブランチ" style="width:120px" />
                <label class="jules-checkbox"><input type="checkbox" id="jules-plan-approval" /> Plan承認必須</label>
            </div>
            <div class="jules-create-row">
                <input id="jules-title" class="jules-input" type="text" placeholder="タスクタイトル（任意）" style="flex:1" />
            </div>
            <div class="jules-create-row">
                <textarea id="jules-prompt" class="jules-textarea" placeholder="タスク指示を入力...\n例: Fix the authentication bug in src/auth.py — the JWT token expiration is not being checked." rows="3"></textarea>
            </div>
            <div class="jules-create-row" style="justify-content:flex-end">
                <button id="jules-create" class="btn jules-create-btn" ${isLoading ? 'disabled' : ''}>⚡ タスク作成</button>
            </div>
        </div>

        <div class="jules-sessions-header">
            <h3>セッション一覧</h3>
            <span class="jules-session-count">${sessions.length} 件</span>
        </div>

        <div id="jules-sessions-list" class="jules-sessions-list">
            ${isLoading ? '<div class="jules-loading">⏳ 読み込み中...</div>' : ''}
            ${!isLoading && sessions.length === 0 ? '<div class="jules-empty">セッションなし。タスクを作成してください。</div>' : ''}
            ${sessions.map(renderSessionCard).join('')}
        </div>
    </div>`;

    bindEvents();
}

function bindEvents(): void {
    document.getElementById('jules-refresh')?.addEventListener('click', () => void loadData());
    document.getElementById('jules-source')?.addEventListener('change', (e) => {
        selectedSource = (e.target as HTMLSelectElement).value;
    });
    document.getElementById('jules-create')?.addEventListener('click', () => void handleCreate());

    document.querySelectorAll('.jules-approve-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = (btn as HTMLElement).dataset.id || '';
            try {
                await approvePlan(id);
                await loadData();
            } catch (e) { alert(`承認失敗: ${(e as Error).message}`); }
        });
    });

    document.querySelectorAll('.jules-detail-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = (btn as HTMLElement).dataset.id || '';
            try {
                const detail = await fetchSessionDetail(id);
                alert(JSON.stringify(detail, null, 2));
            } catch (e) { alert(`詳細取得失敗: ${(e as Error).message}`); }
        });
    });

    document.querySelectorAll('.jules-msg-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = (btn as HTMLElement).dataset.id || '';
            const msg = prompt('Jules にメッセージを送信:');
            if (!msg) return;
            try {
                await sendMessage(id, msg);
                alert('メッセージ送信完了');
            } catch (e) { alert(`送信失敗: ${(e as Error).message}`); }
        });
    });
}

async function handleCreate(): Promise<void> {
    const promptEl = document.getElementById('jules-prompt') as HTMLTextAreaElement;
    const titleEl = document.getElementById('jules-title') as HTMLInputElement;
    const branchEl = document.getElementById('jules-branch') as HTMLInputElement;
    const approvalEl = document.getElementById('jules-plan-approval') as HTMLInputElement;

    const promptText = promptEl?.value.trim();
    if (!promptText) { alert('タスク指示を入力してください'); return; }
    if (!selectedSource) { alert('リポジトリを選択してください'); return; }

    try {
        isLoading = true;
        render();
        const session = await createSession(
            promptText,
            selectedSource,
            titleEl?.value.trim() || '',
            branchEl?.value.trim() || 'main',
            approvalEl?.checked || false,
        );
        sessions.unshift(session);
        isLoading = false;
        render();
    } catch (e) {
        isLoading = false;
        render();
        alert(`タスク作成失敗: ${(e as Error).message}`);
    }
}

async function loadData(): Promise<void> {
    isLoading = true;
    render();
    try {
        [sources, sessions] = await Promise.all([fetchSources(), fetchSessions()]);
        if (sources.length > 0 && !selectedSource) {
            selectedSource = sources[0]?.name ?? '';
        }
    } catch (e) {
        console.error('[Jules] Load error:', e);
    }
    isLoading = false;
    render();
}

// ─── Entry Point ─────────────────────────────────────────────

export async function renderJulesView(): Promise<void> {
    await loadData();
}
