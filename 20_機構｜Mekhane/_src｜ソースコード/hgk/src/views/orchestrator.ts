/**
 * Orchestrator View — AI 指揮台 (Agent Manager 風)
 *
 * チャット中心の全画面レイアウト。
 * Agent Manager のようにメッセージストリームがメインで、
 * 下部に入力エリア + モデルセレクタ。
 */

import './orchestrator.css';

// ─── State ──────────────────────────────────────────────────
interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    model?: string;
    thinking?: string;
}

let chatHistory: ChatMessage[] = [];
let isLoading = false;
let currentModel = 'gemini-2.5-flash';
let currentMode: 'planning' | 'execution' | 'verification' = 'planning';
let showParamPanel = false;

// API Parameters
let paramTemperature = 1.0;   // AI Studio 推奨
let paramMaxTokens = 8192;
let paramThinkingBudget = 32768;
let paramThinkingEnabled = true;

// ─── Utilities ──────────────────────────────────────────────
function esc(s: string): string {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function timeStr(d: Date): string {
    return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

// ─── Markdown-lite renderer ─────────────────────────────────
function renderMarkdown(text: string): string {
    let html = esc(text);
    // Code blocks ```lang\ncode```
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) =>
        `<pre class="orch-code-block"><code class="language-${lang || 'text'}">${code}</code></pre>`
    );
    // Inline `code`
    html = html.replace(/`([^`]+)`/g, '<code class="orch-inline-code">$1</code>');
    // Bold **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="orch-link" target="_blank">$1</a>');
    // Bullet lists
    html = html.replace(/^[•\-]\s+(.+)/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    // Newlines
    html = html.replace(/\n/g, '<br>');
    return html;
}

// ─── Chat Message Renderer ──────────────────────────────────
function renderMessage(msg: ChatMessage): string {
    const isUser = msg.role === 'user';
    const align = isUser ? 'orch-msg--right' : 'orch-msg--left';
    const avatarIcon = isUser ? '👤' : (msg.model?.includes('claude') ? '✦' : '🤖');

    let thinkingHtml = '';
    if (msg.thinking && msg.thinking.trim()) {
        thinkingHtml = `
            <details class="orch-thinking">
                <summary>💭 思考過程</summary>
                <div class="orch-thinking-content">${esc(msg.thinking).replace(/\n/g, '<br>')}</div>
            </details>`;
    }

    const modelBadge = msg.model
        ? `<span class="orch-model-tag">${esc(msg.model)}</span>`
        : '';

    return `
        <div class="orch-msg ${align}">
            <div class="orch-msg-avatar">${avatarIcon}</div>
            <div class="orch-msg-content">
                <div class="orch-msg-header">
                    <span class="orch-msg-time">${timeStr(msg.timestamp)}</span>
                    ${modelBadge}
                </div>
                <div class="orch-msg-body">${renderMarkdown(msg.content)}</div>
                ${thinkingHtml}
            </div>
        </div>`;
}

// ─── Model Selector ─────────────────────────────────────────
const MODELS = [
    { id: 'claude-opus-4-6', label: 'Claude Opus 4.6', icon: '◆', tier: 'premium' },
    { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6', icon: '✦', tier: 'fast' },
    { id: 'gemini-3.1-pro-preview', label: 'Gemini 3.1 Pro Preview', icon: '💎', tier: 'fast' },
    { id: 'gemini-3-flash-preview', label: 'Gemini 3 Flash Preview', icon: '⚡', tier: 'speed' },
    { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', icon: '⚡', tier: 'speed' },
];

// ─── Mode System Prompts ─────────────────────────────────────
const MODE_PROMPTS: Record<string, string> = {
    planning: 'あなたは HGK の Planning モードで動作中です。設計・分析・調査に集中してください。コードを書く前に計画を提示してください。',
    execution: 'あなたは HGK の Execution モードで動作中です。具体的な実装・コード生成・ファイル操作に集中してください。',
    verification: 'あなたは HGK の Verification モードで動作中です。テスト・検証・品質チェックに集中してください。',
};

// ─── Chat Logic ─────────────────────────────────────────────
async function sendMessage(text: string): Promise<void> {
    if (!text.trim() || isLoading) return;

    chatHistory.push({
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
    });
    isLoading = true;
    updateChat();

    const systemPrompt = `あなたは Hegemonikón プロジェクトの AI アシスタントです。
ユーザーの指示に基づいてファイルの読み書き、コード修正、テスト実行などを行います。
作業ディレクトリは /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon です。
日本語で応答してください。簡潔かつ正確に。`;

    try {
        const modePrompt = MODE_PROMPTS[currentMode] || '';
        const fullSystemPrompt = [modePrompt, systemPrompt].filter(Boolean).join('\n');

        chatHistory.push({
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            model: currentModel,
        });
        const msgIndex = chatHistory.length - 1;
        updateChat();

        const request: Record<string, any> = {
            message: text.trim(),
            model: currentModel,
        };
        if (fullSystemPrompt) request.system_instruction = fullSystemPrompt;
        request.temperature = paramTemperature;
        request.max_tokens = paramMaxTokens;
        if (paramThinkingEnabled) request.thinking_budget = paramThinkingBudget;

        // Tauri IPC (invoke + Channel) — HTTP を完全に排除
        if (window.__TAURI_INTERNALS__) {
            const { invoke, Channel } = await import('@tauri-apps/api/core');
            const onChunk = new Channel<{ text: string; done: boolean; model?: string; error?: string }>();
            onChunk.onmessage = (chunk) => {
                if (chunk.error) {
                    chatHistory.push({ role: 'system', content: `エラー: ${chunk.error}`, timestamp: new Date() });
                    updateChat();
                    return;
                }
                const msg = chatHistory[msgIndex];
                if (msg) {
                    if (chunk.text) { msg.content += chunk.text; updateChat(); }
                    if (chunk.model) { msg.model = chunk.model; }
                    if (chunk.done) { isLoading = false; updateChat(); }
                }
            };
            await invoke('cortex_stream', { request, onChunk });
        } else {
            // Browser fallback — fetch SSE (dev mode without Tauri)
            const res = await fetch('/api/ask/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const reader = res.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    let boundary = buffer.indexOf('\n\n');
                    while (boundary !== -1) {
                        const block = buffer.slice(0, boundary).trim();
                        buffer = buffer.slice(boundary + 2);
                        if (block.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(block.slice(6));
                                if (data.error) throw new Error(data.error);
                                const msg = chatHistory[msgIndex];
                                if (msg) {
                                    if (data.text) { msg.content += data.text; updateChat(); }
                                    if (data.model) { msg.model = data.model; }
                                }
                            } catch (e) { console.error('SSE parse error:', e, block); }
                        }
                        boundary = buffer.indexOf('\n\n');
                    }
                }
            }
        }
    } catch (err) {
        chatHistory.push({
            role: 'system',
            content: `エラー: ${err}`,
            timestamp: new Date(),
        });
    } finally {
        isLoading = false;
        updateChat();
    }
}

// ─── Update Chat Area ───────────────────────────────────────
function updateChat(): void {
    const area = document.getElementById('orch-messages');
    if (!area) return;

    if (chatHistory.length === 0) {
        area.innerHTML = `
            <div class="orch-welcome">
                <div class="orch-welcome-logo">⬡</div>
                <h2 class="orch-welcome-title">Hegemonikón AI</h2>
                <p class="orch-welcome-sub">FEP-based Cognitive Hypervisor</p>
                <div class="orch-suggestions">
                    <button class="orch-suggestion" data-msg="プロジェクトの状態を教えて">📊 状態確認</button>
                    <button class="orch-suggestion" data-msg="最近の git diff を見せて">📋 Git Diff</button>
                    <button class="orch-suggestion" data-msg="テストを実行して">🧪 テスト実行</button>
                    <button class="orch-suggestion" data-msg="コードの品質を評価して">✅ 品質チェック</button>
                </div>
            </div>`;
    } else {
        area.innerHTML = chatHistory.map(renderMessage).join('');
    }

    if (isLoading) {
        area.innerHTML += `
            <div class="orch-msg orch-msg--left">
                <div class="orch-msg-avatar">⏳</div>
                <div class="orch-msg-content">
                    <div class="orch-typing">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>`;
    }

    area.scrollTop = area.scrollHeight;

    // Suggestion click handlers
    area.querySelectorAll('.orch-suggestion').forEach(btn => {
        btn.addEventListener('click', () => {
            const msg = btn.getAttribute('data-msg')!;
            const input = document.getElementById('orch-input') as HTMLTextAreaElement;
            if (input) {
                input.value = '';
                sendMessage(msg);
            }
        });
    });
}

// ─── Mode Button Renderer ────────────────────────────────────
function renderModeBtn(mode: string, label: string): string {
    const active = mode === currentMode ? 'active' : '';
    return `<button class="orch-mode-btn ${active}" data-mode="${mode}">${label}</button>`;
}

// ─── Param Panel ─────────────────────────────────────────────
function renderParamPanel(): string {
    if (!showParamPanel) return '';
    return `
    <div class="orch-param-panel">
      <div class="orch-param-row">
        <label>Temperature</label>
        <input type="range" id="param-temp" min="0" max="2" step="0.1" value="${paramTemperature}" />
        <span id="param-temp-val">${paramTemperature}</span>
      </div>
      <div class="orch-param-row">
        <label>Max Tokens</label>
        <select id="param-max-tokens">
          <option value="2048" ${paramMaxTokens === 2048 ? 'selected' : ''}>2K</option>
          <option value="4096" ${paramMaxTokens === 4096 ? 'selected' : ''}>4K</option>
          <option value="8192" ${paramMaxTokens === 8192 ? 'selected' : ''}>8K</option>
          <option value="16384" ${paramMaxTokens === 16384 ? 'selected' : ''}>16K</option>
          <option value="32768" ${paramMaxTokens === 32768 ? 'selected' : ''}>32K</option>
        </select>
      </div>
      <div class="orch-param-row">
        <label>Thinking</label>
        <input type="checkbox" id="param-thinking" ${paramThinkingEnabled ? 'checked' : ''} />
        <input type="range" id="param-think-budget" min="0" max="65536" step="1024" value="${paramThinkingBudget}" ${paramThinkingEnabled ? '' : 'disabled'} />
        <span id="param-think-val">${paramThinkingBudget}</span>
      </div>
    </div>`;
}

// ─── Main Renderer ──────────────────────────────────────────
export async function renderOrchestratorView(): Promise<void> {
    const app = document.getElementById('view-content')!;

    const modelOptions = MODELS.map(m =>
        `<option value="${m.id}" ${m.id === currentModel ? 'selected' : ''}>${m.icon} ${m.label}</option>`
    ).join('');

    app.innerHTML = `
        <div class="orch-layout">
            <div class="orch-main-chat">
                <!-- Message Stream -->
                <div id="orch-messages" class="orch-messages"></div>

                <!-- Parameter Panel (expandable) -->
                <div id="orch-param-mount">${renderParamPanel()}</div>

                <!-- Bottom Input Bar (スクショ1風) -->
                <div class="orch-input-bar">
                    <div class="orch-input-row">
                        <button id="orch-clear" class="orch-bar-icon" title="新規チャット">+</button>
                        <div class="orch-mode-group">
                            ${renderModeBtn('planning', '💡 計画')}
                            ${renderModeBtn('execution', '⚡ 実行')}
                            ${renderModeBtn('verification', '✅ 検証')}
                        </div>
                        <textarea id="orch-input" class="orch-input"
                                  placeholder="メッセージを入力... (Enter で送信、Shift+Enter で改行)"
                                  rows="1"></textarea>
                        <div class="orch-bar-right">
                            <select id="orch-model" class="orch-model-select">${modelOptions}</select>
                            <button id="orch-param-toggle" class="orch-bar-icon" title="パラメータ">⚙</button>
                            <button id="orch-send" class="orch-send-btn" title="送信">➤</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right: DevTools Sidebar -->
            <div id="orch-dt-sidebar" class="orch-dt-sidebar"></div>
        </div>`;

    // Initialize DevTools Sidebar
    const dtSidebar = document.getElementById('orch-dt-sidebar');
    if (dtSidebar) {
        await import('./devtools').then(m => m.mountDevTools(dtSidebar));
    }

    // ─── Event Handlers ─────────────────────────────────────
    const input = document.getElementById('orch-input') as HTMLTextAreaElement;
    const sendBtn = document.getElementById('orch-send')!;
    const modelSelect = document.getElementById('orch-model') as HTMLSelectElement;
    const clearBtn = document.getElementById('orch-clear')!;
    const paramToggle = document.getElementById('orch-param-toggle')!;

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    });

    // Send on Enter
    input.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            const text = input.value;
            input.value = '';
            input.style.height = 'auto';
            sendMessage(text);
        }
    });

    sendBtn.addEventListener('click', () => {
        const text = input.value;
        input.value = '';
        input.style.height = 'auto';
        sendMessage(text);
    });

    modelSelect.addEventListener('change', () => {
        currentModel = modelSelect.value;
    });

    clearBtn.addEventListener('click', () => {
        chatHistory = [];
        updateChat();
    });

    // Mode buttons
    document.querySelectorAll('.orch-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentMode = btn.getAttribute('data-mode') as typeof currentMode;
            document.querySelectorAll('.orch-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Param panel toggle
    paramToggle.addEventListener('click', () => {
        showParamPanel = !showParamPanel;
        const mount = document.getElementById('orch-param-mount');
        if (mount) mount.innerHTML = renderParamPanel();
        setupParamListeners();
    });

    // Initialize
    updateChat();
    input.focus();
}

// ─── Param Event Wiring ─────────────────────────────────────
function setupParamListeners(): void {
    const tempSlider = document.getElementById('param-temp') as HTMLInputElement;
    const tempVal = document.getElementById('param-temp-val');
    const maxTokensSelect = document.getElementById('param-max-tokens') as HTMLSelectElement;
    const thinkingCb = document.getElementById('param-thinking') as HTMLInputElement;
    const thinkBudget = document.getElementById('param-think-budget') as HTMLInputElement;
    const thinkVal = document.getElementById('param-think-val');

    tempSlider?.addEventListener('input', () => {
        paramTemperature = parseFloat(tempSlider.value);
        if (tempVal) tempVal.textContent = String(paramTemperature);
    });
    maxTokensSelect?.addEventListener('change', () => {
        paramMaxTokens = parseInt(maxTokensSelect.value);
    });
    thinkingCb?.addEventListener('change', () => {
        paramThinkingEnabled = thinkingCb.checked;
        if (thinkBudget) thinkBudget.disabled = !paramThinkingEnabled;
    });
    thinkBudget?.addEventListener('input', () => {
        paramThinkingBudget = parseInt(thinkBudget.value);
        if (thinkVal) thinkVal.textContent = String(paramThinkingBudget);
    });
}
