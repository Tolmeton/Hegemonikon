/**
 * Tab Nav — 左サイドバー: COMET風 Assistant Pane のみ
 * ナビゲーションはアイコンレールのホバーフライアウトで行う
 */

import { ROUTES } from '../route-config';
import { getCurrentRoute, esc } from '../utils';
import { isTabNavOpen } from './state';

// ─── State ──────────────────────────────────────────────────

let currentMode: 'planning' | 'execution' | 'verification' = 'planning';
let currentModel = 'claude-opus-4-6';
let showParamPanel = false;
let isHistoryOpen = false;

// API Parameters
let paramTemperature = 1.0;
let paramMaxTokens = 8192;
let paramThinkingBudget = 32768;
let paramThinkingEnabled = true;

interface PaneMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ─── Session Management ─────────────────────────────────────
interface ChatSession {
  id: string;
  title: string;
  messages: PaneMessage[];
  createdAt: number;
}

const STORAGE_KEY = 'hgk-chat-sessions';
const ACTIVE_KEY = 'hgk-chat-active';

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveSessions(sessions: ChatSession[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function getActiveSessionId(): string {
  return localStorage.getItem(ACTIVE_KEY) || '';
}

function setActiveSessionId(id: string): void {
  localStorage.setItem(ACTIVE_KEY, id);
}

let sessions: ChatSession[] = loadSessions();
let activeSessionId = getActiveSessionId();

// Ensure at least one session exists
if (sessions.length === 0) {
  const first: ChatSession = { id: generateId(), title: '新規チャット', messages: [], createdAt: Date.now() };
  sessions.push(first);
  activeSessionId = first.id;
  saveSessions(sessions);
  setActiveSessionId(activeSessionId);
}

function getActiveSession(): ChatSession {
  const found = sessions.find(s => s.id === activeSessionId);
  if (found) return found;
  const fallback = sessions[0]!;
  activeSessionId = fallback.id;
  setActiveSessionId(fallback.id);
  return fallback;
}

let paneHistory: PaneMessage[] = getActiveSession().messages;

// ─── Models ─────────────────────────────────────────────────
const MODELS = [
  { id: 'claude-opus-4-6', label: 'Claude Opus 4.6', icon: '◆' },
  { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6', icon: '✦' },
  { id: 'gemini-3.1-pro-preview', label: 'Gemini 3.1 Pro', icon: '💎' },
];
// NOTE: 古いモデル (Gemini 3 Flash, Claude Sonnet 4.5 等) は選択不可。
// 最新モデルのみ使用する設計原則 (AMBITION.md L324)

// ─── Mode Prompts ───────────────────────────────────────────
const MODE_PROMPTS: Record<string, string> = {
  planning: 'Planning モード: 設計・分析・調査に集中。',
  execution: 'Execution モード: 実装・コード生成・操作に集中。',
  verification: 'Verification モード: テスト・検証・品質チェックに集中。',
};

function renderModeBtn(mode: string, label: string): string {
  const active = mode === currentMode ? 'active' : '';
  return `<button class="orch-mode-btn ${active}" data-mode="${mode}">${label}</button>`;
}

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

// ─── Main Render ────────────────────────────────────────────
export function buildTabNav(): void {
  const nav = document.getElementById('tab-nav');
  if (!nav) return;

  // WO-00 fix: Chat/Cowork ビューは独自の 3 カラム cw-layout を持つため、
  // tab-nav (アシスタントパネル 280px) を自動的に折り畳んで全幅を確保する。
  // この検出は buildTabNav() が呼ばれるたびに評価されるため、
  // どのコールパスからでも確実に Chat 時は折り畳まれる。
  const currentRoute = getCurrentRoute();
  const isChatView = currentRoute === 'chat' || currentRoute === 'cowork';
  const effectiveOpen = isChatView ? false : isTabNavOpen;

  nav.classList.toggle('collapsed', !effectiveOpen);
  const app = document.getElementById('app');
  if (app) {
    app.style.gridTemplateColumns = effectiveOpen ? '48px 280px 1fr' : '48px 0px 1fr';
  }

  if (!effectiveOpen) {
    nav.innerHTML = '';
    return;
  }

  // Messages
  const messagesHtml = paneHistory.length === 0
    ? `<div class="ap-empty">
        <div class="ap-empty-icon">◆</div>
        <div class="ap-empty-text">こんにちは</div>
        <div class="ap-empty-sub">何かお手伝いできることがあれば教えてください。</div>
      </div>`
    : paneHistory.map(m =>
      m.role === 'user'
        ? `<div class="ap-msg ap-msg-user">${esc(m.content)}</div>`
        : `<div class="ap-msg ap-msg-assistant">${esc(m.content)}</div>`
    ).join('');

  const modelOptions = MODELS.map(m =>
    `<option value="${m.id}" ${m.id === currentModel ? 'selected' : ''}>${m.icon} ${m.label}</option>`
  ).join('');

  // COMET風 — ヘッダー + ドロワー + メッセージ + パラメータ + 入力バー
  nav.innerHTML = `
    <div class="ap-container">
      <!-- Header -->
      <div class="ap-header">
        <button id="ap-history-toggle" class="ap-header-btn" title="履歴を開閉" style="margin-right: 4px;">☰</button>
        <span class="ap-header-icon">◆</span>
        <span class="ap-header-title">アシスタント</span>
        <div class="ap-header-actions">
          <button class="ap-header-btn ap-new-chat" title="新規チャット">+</button>
          <button id="ap-close-btn" class="ap-header-btn" title="閉じる">✕</button>
        </div>
      </div>

      <div class="ap-body-wrapper">
        <!-- History Drawer -->
        <div id="ap-history-drawer" class="ap-history-drawer ${isHistoryOpen ? 'open' : ''}">
          <div class="ap-history-list">
            ${sessions.map(s => `
              <div class="ap-history-item ${s.id === activeSessionId ? 'active' : ''}" data-sid="${s.id}" title="${esc(s.title)}">
                <span class="ap-history-title">${esc(s.title.length > 20 ? s.title.slice(0, 20) + '…' : s.title)}</span>
                ${sessions.length > 1 ? `<span class="ap-history-close" data-sid="${s.id}">✕</span>` : ''}
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Main Content (Messages + Input) -->
        <div class="ap-main-content">
          <!-- Messages -->
          <div id="assistant-pane-messages" class="ap-messages">${messagesHtml}</div>

          <!-- Parameter Panel -->
          <div id="ap-param-mount">${renderParamPanel()}</div>

          <!-- Bottom Input Bar (モード + 入力 + モデル + パラメータ + 送信) -->
          <div class="ap-input-bar">
            <div class="ap-input-top">
              <button class="ap-new-btn" title="新規">+</button>
              <div class="orch-mode-group">
                ${renderModeBtn('planning', 'P')}
                ${renderModeBtn('execution', 'E')}
                ${renderModeBtn('verification', 'V')}
              </div>
              <select id="ap-model-select" class="ap-model-select">${modelOptions}</select>
              <button id="ap-param-toggle" class="ap-bar-icon" title="パラメータ">⚙</button>
            </div>
            <div class="ap-input-bottom">
              <textarea id="assistant-pane-input" class="ap-input"
                        rows="1" placeholder="質問してみましょう... (Enter で送信、Shift+Enter で改行)"></textarea>
              <button id="assistant-pane-send" class="ap-send">↑</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // ─── Event Handlers ─────────────────────────────────────
  const paneInput = document.getElementById('assistant-pane-input') as HTMLTextAreaElement;
  const paneSend = document.getElementById('assistant-pane-send')!;
  const autoResizePaneInput = () => {
    if (!paneInput) return;
    paneInput.style.height = 'auto';
    paneInput.style.height = `${Math.min(paneInput.scrollHeight, 140)}px`;
  };

  const sendPaneMessage = async () => {
    const text = paneInput.value.trim();
    if (!text) return;
    paneInput.value = '';
    autoResizePaneInput();

    paneHistory.push({ role: 'user', content: text });
    const session = getActiveSession();
    session.messages = paneHistory;
    // Auto-set title from first message
    if (session.title === '新規チャット' && paneHistory.length === 1) {
      session.title = text.slice(0, 20) + (text.length > 20 ? '…' : '');
    }
    saveSessions(sessions);

    const paneMessages = document.getElementById('assistant-pane-messages')!;
    paneMessages.innerHTML += `<div class="ap-msg ap-msg-user">${esc(text)}</div>`;
    paneMessages.innerHTML += `<div class="ap-msg ap-msg-typing" id="ap-typing">...</div>`;
    paneMessages.scrollTop = paneMessages.scrollHeight;

    try {
      const currentRoute = getCurrentRoute();
      const routeInfo = ROUTES.find(r => r.key === currentRoute);
      const viewContext = routeInfo ? `現在のユーザーの表示画面: ${routeInfo.label}` : '表示画面: 不明';
      const modePrompt = MODE_PROMPTS[currentMode] || '';
      const systemPrompt = `あなたは HGK アシスタントです。${modePrompt}\n簡潔かつ正確に日本語で応答してください。\n[Context]\n${viewContext}`;

      // SSE ストリーミングで応答を取得
      const resp = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          model: currentModel,
          system_instruction: systemPrompt,
          thinking_budget: 8192,
        }),
      });

      if (!resp.ok) {
        throw new Error(`API Error ${resp.status}`);
      }

      // SSE パース — 逐次表示
      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let buffer = '';

      document.getElementById('ap-typing')?.remove();

      // thinking/text 分離表示用の DOM 要素
      let thinkingDiv: HTMLElement | null = null;
      const assistantDiv = document.createElement('div');
      assistantDiv.className = 'ap-msg ap-msg-assistant';
      paneMessages.appendChild(assistantDiv);

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
                if (data.error) {
                  throw new Error(data.error);
                }
                if (data.thinking) {
                  // Thinking chunk — 折りたたみ表示
                  if (!thinkingDiv) {
                    thinkingDiv = document.createElement('details');
                    thinkingDiv.className = 'ap-thinking';
                    const summary = document.createElement('summary');
                    summary.textContent = '思考中...';
                    thinkingDiv.appendChild(summary);
                    const content = document.createElement('div');
                    content.className = 'ap-thinking-content';
                    thinkingDiv.appendChild(content);
                    assistantDiv.prepend(thinkingDiv);
                  }
                  const content = thinkingDiv.querySelector('.ap-thinking-content');
                  if (content) {
                    content.textContent += data.thinking;
                  }
                  paneMessages.scrollTop = paneMessages.scrollHeight;
                }
                if (data.text) {
                  fullText += data.text;
                  // テキスト部分は thinking の後に表示
                  let textEl = assistantDiv.querySelector('.ap-text-content') as HTMLElement;
                  if (!textEl) {
                    textEl = document.createElement('div');
                    textEl.className = 'ap-text-content';
                    assistantDiv.appendChild(textEl);
                  }
                  textEl.textContent = fullText;
                  paneMessages.scrollTop = paneMessages.scrollHeight;
                }
                if (data.done && thinkingDiv) {
                  // 思考完了 — summary を更新
                  const summary = thinkingDiv.querySelector('summary');
                  if (summary) summary.textContent = '💭 思考過程';
                }
              } catch (parseErr) {
                if ((parseErr as Error).message !== 'Unexpected end of JSON input') {
                  throw parseErr;
                }
              }
            }
            boundary = buffer.indexOf('\n\n');
          }
        }
      }

      // SSE パーサーで .ap-text-content が構築されていない場合のみフォールバック
      if (!assistantDiv.querySelector('.ap-text-content')) {
        if (!fullText) fullText = '(応答なし)';
        assistantDiv.textContent = fullText;
      }

      paneHistory.push({ role: 'assistant', content: fullText });
      session.messages = paneHistory;
      saveSessions(sessions);
    } catch (err) {
      document.getElementById('ap-typing')?.remove();
      const errMsg = (err as Error).message || String(err);
      // ユーザーフレンドリーなエラーメッセージ
      let displayErr = errMsg;
      if (errMsg.includes('RESOURCE_EXHAUSTED') || errMsg.includes('429')) {
        displayErr = 'API の処理枠が一時的に満杯です。数分後に再試行してください。';
      } else if (errMsg.includes('500') || errMsg.includes('INTERNAL')) {
        displayErr = 'API サーバーで一時エラーが発生しました。';
      }
      paneMessages.innerHTML += `<div class="ap-msg ap-msg-error">⚠️ ${esc(displayErr)}</div>`;
    }
    paneMessages.scrollTop = paneMessages.scrollHeight;
    // Refresh session tabs to show updated title
    buildTabNav();
  };

  autoResizePaneInput();
  paneInput?.addEventListener('input', autoResizePaneInput);
  paneInput?.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendPaneMessage();
    }
  });
  paneSend?.addEventListener('click', sendPaneMessage);

  // Close button — アシスタントペインを閉じる
  document.getElementById('ap-close-btn')?.addEventListener('click', () => {
    import('./state').then(({ toggleTabNav }) => {
      toggleTabNav();
      buildTabNav();
    });
  });

  // New chat — 新規セッション作成
  nav.querySelectorAll('.ap-new-chat, .ap-new-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const newSession: ChatSession = {
        id: generateId(),
        title: '新規チャット',
        messages: [],
        createdAt: Date.now(),
      };
      sessions.push(newSession);
      activeSessionId = newSession.id;
      setActiveSessionId(activeSessionId);
      paneHistory = newSession.messages;
      saveSessions(sessions);
      buildTabNav();
    });
  });

  // History drawer toggle
  document.getElementById('ap-history-toggle')?.addEventListener('click', () => {
    isHistoryOpen = !isHistoryOpen;
    buildTabNav();
  });

  // Session history switching
  document.querySelectorAll('.ap-history-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      // Don't switch if clicking close button
      if (target.classList.contains('ap-history-close')) return;
      const sid = (item as HTMLElement).getAttribute('data-sid');
      if (sid && sid !== activeSessionId) {
        activeSessionId = sid;
        setActiveSessionId(sid);
        paneHistory = getActiveSession().messages;
        buildTabNav();
      }
    });
  });

  // Session history close
  document.querySelectorAll('.ap-history-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const sid = (btn as HTMLElement).getAttribute('data-sid');
      if (!sid || sessions.length <= 1) return;
      sessions = sessions.filter(s => s.id !== sid);
      if (activeSessionId === sid) {
        activeSessionId = sessions[0]!.id;
        setActiveSessionId(activeSessionId);
        paneHistory = getActiveSession().messages;
      }
      saveSessions(sessions);
      buildTabNav();
    });
  });

  // Mode buttons
  document.querySelectorAll('.orch-mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentMode = btn.getAttribute('data-mode') as typeof currentMode;
      document.querySelectorAll('.orch-mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Model select
  document.getElementById('ap-model-select')?.addEventListener('change', (e) => {
    currentModel = (e.target as HTMLSelectElement).value;
  });

  // Param panel toggle
  document.getElementById('ap-param-toggle')?.addEventListener('click', () => {
    showParamPanel = !showParamPanel;
    const mount = document.getElementById('ap-param-mount');
    if (mount) mount.innerHTML = renderParamPanel();
    setupParamListeners();
  });


}

// ─── Param Listeners ────────────────────────────────────────
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
