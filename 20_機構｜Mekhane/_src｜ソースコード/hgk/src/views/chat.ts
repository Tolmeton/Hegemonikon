import './css/cowork.css';
/**
 * Chat View — Cowork Style (claude.ai clone)
 * 3-column layout: Conversations | Chat | Files/Terminal/AI
 * God Object 分割済み: 型は chat-types.ts、ストリーミングは chat-streaming.ts
 */

import { marked } from 'marked';
import { renderMcpApp, hasMcpAppUI, createDemoAppHtml } from '../ui/mcp-app-renderer';
import { enhanceCodeBlocks, enhanceAlerts } from './enhance';

// ─── エラーメッセージ変換 ──────────────────────────────────────────
// 生の API エラーをユーザーフレンドリーな日本語メッセージに変換する
function friendlyError(raw: string): string {
    if (raw.includes('RESOURCE_EXHAUSTED') || raw.includes('429') || raw.includes('rate') || raw.includes('quota')) {
        return 'API の処理枠が一時的に満杯です。数分後に再試行してください。';
    }
    if (raw.includes('500') || raw.includes('INTERNAL') || raw.includes('internal_error')) {
        return 'API サーバーで一時エラーが発生しました。';
    }
    if (raw.includes('401') || raw.includes('UNAUTHENTICATED') || raw.includes('API キー')) {
        return 'API キーが無効です。設定を確認してください。';
    }
    if (raw.includes('403') || raw.includes('PERMISSION_DENIED')) {
        return 'API へのアクセスが拒否されました。権限を確認してください。';
    }
    // 長すぎるエラーは切り詰める
    if (raw.length > 200) return raw.slice(0, 200) + '…';
    return raw;
}

// ─── Types (from chat-types.ts) ──────────────────────────────
import type { ChatMessage, Attachment, BranchPoint, GeminiContent, Conversation, StreamingDeps } from './chat-types';

// ─── Streaming (from chat-streaming.ts) ──────────────────────
import {
    readSSEStream, readCortexSSEStream, readAgentSSEStream, readColonySSEStream,
    withSSETimeout
} from './chat-streaming';

// ─── Types: see chat-types.ts ────────────────────────────────

// ─── State ───────────────────────────────────────────────────

let conversations: Conversation[] = [];
let activeConvId = '';
let currentModel = 'gemini-3.1-pro-preview';
let isStreaming = false;
let currentAbortController: AbortController | null = null;
let apiKey = '';
let systemInstruction = 'あなたは Hegemonikón の認知支援AIです。日本語で応答してください。簡潔かつ正確に。';
let agentMode = false;
let colonyMode = false;
let pendingAttachments: Attachment[] = [];
let activeRightTab: 'files' | 'terminal' | 'ai' = 'files';
let currentFilePath = '';
let terminalLog: string[] = [];
let sidebarVisible = true;
let mdViewMode: 'raw' | 'rendered' = 'rendered';
let currentFileContent = '';

function getStreamingDeps(): StreamingDeps {
    return { renderMessages, saveAllConversations, updateTerminalTab, showApprovalUI, terminalLog, renderMcpApp, hasMcpAppUI };
}

const MODELS: Record<string, string> = {
    'gemini-3.1-pro-preview': '💎 Gemini 3.1 Pro',
    'claude-opus-4-6': '◆ Claude Opus 4.6',
    'claude-sonnet-4-6': '✦ Claude Sonnet 4.6',
};

const API_BACKEND = '/api';
const API_GEMINI_DIRECT = 'https://generativelanguage.googleapis.com/v1beta/models';
let useBackend = true;

// ─── Helpers ─────────────────────────────────────────────────

function esc(s: string): string {
    return s.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatTime(d: Date): string {
    return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function genId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function getMessages(): ChatMessage[] {
    const conv = conversations.find(c => c.id === activeConvId);
    return conv ? conv.messages : [];
}

function setMessages(msgs: ChatMessage[]): void {
    const conv = conversations.find(c => c.id === activeConvId);
    if (conv) conv.messages = msgs;
}

// ─── API Key ─────────────────────────────────────────────────

async function loadApiKey(): Promise<void> {
    const stored = localStorage.getItem('hgk-gemini-api-key');
    if (stored) { apiKey = stored; return; }
    try {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 3000);
        const resp = await fetch('/api/hgk/gateway/health', { signal: ctrl.signal });
        clearTimeout(timer);
        if (resp.ok) { apiKey = '__backend__'; return; }
    } catch { /* no backend or timeout */ }
}

function buildContents(msgs: ChatMessage[]): GeminiContent[] {
    return msgs.filter(m => m.content.trim()).map(m => ({
        role: m.role === 'model' ? 'model' : 'user',
        parts: [{ text: m.content }],
    }));
}

// ─── SSE Streaming ───────────────────────────────────────────

async function sendDirectFallback(
    assistantMsg: ChatMessage,
    contents: GeminiContent[],
    generationConfig: Record<string, unknown>,
    sysInstr: { parts: { text: string }[] } | undefined,
): Promise<string> {
    const key = apiKey === '__backend__' ? '' : apiKey;
    if (!key) throw new Error('API キーが設定されていません');

    const url = `${API_GEMINI_DIRECT}/${currentModel}:streamGenerateContent?alt=sse&key=${key}`;
    const body: Record<string, unknown> = { contents, generationConfig };
    if (sysInstr) body.systemInstruction = sysInstr;

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errText = await response.text();
        let errMsg = `API Error ${response.status}`;
        try { errMsg = JSON.parse(errText).error?.message || errMsg; } catch { /* */ }
        const msgs = getMessages();
        msgs.splice(-2, 2);
        setMessages(msgs);
        throw new Error(errMsg);
    }

    return await withSSETimeout(assistantMsg, deps => readSSEStream(response, assistantMsg, deps), getStreamingDeps());
}

async function sendToGemini(userMessage: string): Promise<string> {
    const msgs = getMessages();
    msgs.push({ role: 'user', content: userMessage, timestamp: new Date(), attachments: pendingAttachments.length ? [...pendingAttachments] : undefined });

    const assistantMsg: ChatMessage = { role: 'model', content: '', timestamp: new Date(), model: currentModel };
    msgs.push(assistantMsg);
    setMessages(msgs);
    pendingAttachments = [];
    renderMessages();
    renderAttachments();

    const contents = buildContents(msgs.slice(0, -1));
    const generationConfig = { temperature: 0.7, maxOutputTokens: 8192 };
    const sysInstr = systemInstruction ? { parts: [{ text: systemInstruction }] } : undefined;

    let response: Response;
    currentAbortController = new AbortController();

    if (useBackend) {
        try {
            const userText = contents[contents.length - 1]?.parts?.[0]?.text ?? userMessage;
            response = await fetch(`${API_BACKEND}/ask/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: currentAbortController.signal,
                body: JSON.stringify({
                    message: userText, model: currentModel,
                    system_instruction: sysInstr?.parts?.[0]?.text,
                    temperature: generationConfig.temperature,
                    max_tokens: generationConfig.maxOutputTokens,
                    thinking_budget: 8192,
                }),
            });
        } catch {
            console.warn('[Chat] Backend unreachable, falling back to direct API');
            useBackend = false;
            return sendDirectFallback(assistantMsg, contents, generationConfig, sysInstr);
        }
    } else {
        return sendDirectFallback(assistantMsg, contents, generationConfig, sysInstr);
    }

    if (!response.ok) {
        const errText = await response.text();
        let errMsg = `API Error ${response.status}`;
        try { errMsg = JSON.parse(errText).error?.message || errMsg; } catch { /* */ }
        // Show error as assistant message instead of removing
        assistantMsg.content = `⚠️ ${friendlyError(errMsg)}`;
        setMessages(msgs);
        renderMessages();
        return errMsg;
    }

    return await withSSETimeout(assistantMsg, deps => readCortexSSEStream(response, assistantMsg, deps), getStreamingDeps());
}

// ─── Agent Mode ──────────────────────────────────────────────

async function sendToAgent(userMessage: string): Promise<string> {
    const msgs = getMessages();
    msgs.push({ role: 'user', content: userMessage, timestamp: new Date(), attachments: pendingAttachments.length ? [...pendingAttachments] : undefined });
    const assistantMsg: ChatMessage = { role: 'model', content: '🔧 Agent 起動中...', timestamp: new Date(), model: `agent:${currentModel}` };
    msgs.push(assistantMsg);
    setMessages(msgs);
    pendingAttachments = [];
    renderMessages();
    renderAttachments();

    try {
        currentAbortController = new AbortController();
        const response = await fetch('/api/ask/agent/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: currentAbortController.signal,
            body: JSON.stringify({
                message: userMessage, model: currentModel,
                system_instruction: systemInstruction, max_iterations: 10,
                thinking_budget: 8192,
            }),
        });

        if (!response.ok) {
            const errText = await response.text();
            let errMsg = `Agent Error ${response.status}`;
            try { errMsg = JSON.parse(errText).error || errMsg; } catch { /* */ }
            msgs.splice(-2, 2);
            setMessages(msgs);
            throw new Error(errMsg);
        }
        return await withSSETimeout(assistantMsg, deps => readAgentSSEStream(response, assistantMsg, deps), getStreamingDeps());
    } catch (err) {
        msgs.splice(-2, 2);
        setMessages(msgs);
        throw err;
    }
}

// ─── Safety Gate ─────────────────────────────────────────────

function renderDiffHtml(diffText: string): string {
    const MAX_LINES = 120;
    const lines = diffText.split('\n');
    const visible = lines.slice(0, MAX_LINES);
    const truncated = lines.length > MAX_LINES;

    const html = visible.map(line => {
        const escaped = esc(line);
        if (line.startsWith('+++') || line.startsWith('---')) return `<span class="diff-meta">${escaped}</span>`;
        else if (line.startsWith('@@')) return `<span class="diff-hunk">${escaped}</span>`;
        else if (line.startsWith('+')) return `<span class="diff-add">${escaped}</span>`;
        else if (line.startsWith('-')) return `<span class="diff-del">${escaped}</span>`;
        return `<span class="diff-ctx">${escaped}</span>`;
    }).join('\n');

    return html + (truncated ? `\n<span class="diff-meta">... (${lines.length - MAX_LINES} lines omitted)</span>` : '');
}

function showApprovalUI(requestId: string, toolName: string, args: Record<string, unknown>, diffText: string | null): void {
    const container = document.getElementById('cw-messages');
    if (!container) return;

    let previewHtml = '';
    let headerExtra = '';

    if (toolName === 'write_file' && diffText) {
        const path = String(args.path || '?');
        const addCount = (diffText.match(/^\+[^+]/gm) || []).length;
        const delCount = (diffText.match(/^-[^-]/gm) || []).length;
        headerExtra = `<span class="diff-stat"><span class="diff-stat-add">+${addCount}</span> <span class="diff-stat-del">-${delCount}</span></span>`;
        previewHtml = `<div style="font-size:0.75rem;color:var(--cw-text-secondary);margin-bottom:4px;">📄 ${esc(path)}</div><pre class="cw-approval-preview">${renderDiffHtml(diffText)}</pre>`;
    } else if (toolName === 'write_file') {
        const path = String(args.path || '');
        const content = String(args.content || '');
        const lines = content.split('\n');
        const previewLines = lines.slice(0, 50).join('\n');
        const truncatedText = lines.length > 50 ? `\n... (${lines.length - 50} lines omitted)` : '';
        previewHtml = `<pre class="cw-approval-preview">📄 ${esc(path)}\n\n${esc(previewLines)}${truncatedText}</pre>`;
    } else if (toolName === 'run_command') {
        previewHtml = `<pre class="cw-approval-preview">$ ${esc(String(args.command || ''))}</pre>`;
    } else {
        previewHtml = `<pre class="cw-approval-preview">${esc(JSON.stringify(args, null, 2).slice(0, 500))}</pre>`;
    }

    const panel = document.createElement('div');
    panel.className = 'cw-approval';
    panel.innerHTML = `
        <div class="cw-approval-header">⚠️ <strong>${esc(toolName)}</strong> の実行を承認しますか？ ${headerExtra}</div>
        ${previewHtml}
        <div class="cw-approval-actions">
            <button class="cw-btn-approve" data-rid="${requestId}">✅ 承認</button>
            <button class="cw-btn-reject" data-rid="${requestId}">❌ 却下</button>
        </div>
    `;
    container.appendChild(panel);
    container.scrollTop = container.scrollHeight;

    panel.querySelector('.cw-btn-approve')?.addEventListener('click', () => void respondToApproval(requestId, true, panel));
    panel.querySelector('.cw-btn-reject')?.addEventListener('click', () => void respondToApproval(requestId, false, panel));
}

async function respondToApproval(requestId: string, approved: boolean, panel: HTMLElement): Promise<void> {
    panel.querySelectorAll('button').forEach(b => { (b as HTMLButtonElement).disabled = true; });
    panel.querySelector('.cw-approval-header')!.textContent = approved ? '✅ 承認しました — 実行中...' : '❌ 却下しました';
    try {
        await fetch('/api/ask/agent/approve', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId, approved }),
        });
    } catch (err) { console.error('[Safety Gate] Approval request failed:', err); }
    setTimeout(() => panel.remove(), 1500);
}

// ─── Colony Mode ─────────────────────────────────────────────

async function sendToColony(userMessage: string): Promise<string> {
    const msgs = getMessages();
    msgs.push({ role: 'user', content: userMessage, timestamp: new Date(), attachments: pendingAttachments.length ? [...pendingAttachments] : undefined });
    const assistantMsg: ChatMessage = { role: 'model', content: '🏛️ Colony 起動中...\nCOO (Opus 4.6) がタスクを分析中...', timestamp: new Date(), model: 'colony:opus-4.6' };
    msgs.push(assistantMsg);
    setMessages(msgs);
    pendingAttachments = [];
    renderMessages();
    renderAttachments();

    try {
        const response = await fetch('/api/ask/colony/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage }),
        });

        if (!response.ok) {
            const errText = await response.text();
            let errMsg = `Colony Error ${response.status}`;
            try { errMsg = JSON.parse(errText).error || errMsg; } catch { /* */ }
            msgs.splice(-2, 2);
            setMessages(msgs);
            throw new Error(errMsg);
        }
        return await withSSETimeout(assistantMsg, deps => readColonySSEStream(response, assistantMsg, deps), getStreamingDeps());
    } catch (err) {
        msgs.splice(-2, 2);
        setMessages(msgs);
        throw err;
    }
}

// ─── Persistence ─────────────────────────────────────────────

function saveAllConversations(): void {
    try {
        // Sync active branch before saving
        for (const conv of conversations) {
            if (conv.branchPoints) {
                for (const bp of conv.branchPoints) {
                    if (conv.id === activeConvId) {
                        bp.branches[bp.activeBranch] = conv.messages.slice(bp.atIndex);
                    }
                }
            }
        }

        const serializeMsg = (m: ChatMessage) => ({ ...m, timestamp: m.timestamp.toISOString() });
        const data = conversations.map(c => ({
            ...c,
            messages: c.messages.map(serializeMsg),
            branchPoints: c.branchPoints?.map(bp => ({
                ...bp,
                branches: bp.branches.map(branch => branch.map(serializeMsg)),
            })),
            createdAt: c.createdAt.toISOString(),
        }));
        localStorage.setItem('hgk-conversations', JSON.stringify(data));
    } catch { /* quota exceeded */ }
}

function loadAllConversations(): void {
    try {
        const raw = localStorage.getItem('hgk-conversations');
        if (!raw) {
            // Migrate from old single-history format
            const oldRaw = localStorage.getItem('hgk-chat-history');
            if (oldRaw) {
                const oldMsgs = JSON.parse(oldRaw) as Array<ChatMessage & { timestamp: string }>;
                const conv: Conversation = {
                    id: genId(),
                    title: oldMsgs[0]?.content?.slice(0, 40) || 'Chat',
                    messages: oldMsgs.map(m => ({ ...m, timestamp: new Date(m.timestamp) })),
                    createdAt: new Date(oldMsgs[0]?.timestamp || Date.now()),
                };
                conversations = [conv];
                activeConvId = conv.id;
            }
            return;
        }
        const data = JSON.parse(raw);
        const deserializeMsg = (m: ChatMessage & { timestamp: string }) => ({
            ...m, timestamp: new Date(m.timestamp),
        });
        conversations = data.map((c: Record<string, unknown>) => ({
            ...c,
            messages: (c.messages as Array<ChatMessage & { timestamp: string }>).map(deserializeMsg),
            branchPoints: (c.branchPoints as BranchPoint[] | undefined)?.map((bp: BranchPoint) => ({
                ...bp,
                branches: bp.branches.map((branch: ChatMessage[]) =>
                    (branch as unknown as Array<ChatMessage & { timestamp: string }>).map(deserializeMsg)
                ),
            })),
            createdAt: new Date(c.createdAt as string),
        }));
        if (conversations.length > 0 && !activeConvId) {
            activeConvId = conversations[0]!.id;
        }
    } catch { /* corrupt */ }
}

// NOTE: enhanceCodeBlocks & enhanceAlerts are imported from './enhance'

/**
 * CCL expression highlighter for user messages.
 * Visually distinguishes operators to prevent _ vs - confusion.
 */
function highlightCCL(html: string): string {
    // Pattern: / followed by lowercase letters, then optional operators (+, -, ^, !, ~, *, _, ', \\)
    // followed by more WFs connected by _ or other operators
    return html.replace(
        /(\/[a-z]+)([+\-^!~*_'\\]*)/g,
        (_match, wf: string, ops: string) => {
            let result = `<span class="ccl-wf">${wf}</span>`;
            if (ops) {
                result += ops.split('').map(op => {
                    const cls = op === '_' ? 'ccl-seq'
                        : op === '-' ? 'ccl-condense'
                            : op === '+' ? 'ccl-deepen'
                                : op === '~' ? 'ccl-oscillate'
                                    : op === '*' ? 'ccl-fuse'
                                        : 'ccl-op';
                    return `<span class="${cls}">${esc(op)}</span>`;
                }).join('');
            }
            return result;
        }
    );
}

// ─── Rendering ───────────────────────────────────────────────

function renderMessage(msg: ChatMessage, index: number): string {
    const isUser = msg.role === 'user';
    const rendered = isUser ? highlightCCL(esc(msg.content)) : (marked.parse(msg.content) as string);
    const modelTag = msg.model ? `<span class="cw-msg-model-tag">${esc(MODELS[msg.model] || msg.model)}</span>` : '';

    let attachmentHtml = '';
    if (msg.attachments?.length) {
        attachmentHtml = msg.attachments.map(a => {
            if (a.mime?.startsWith('image/') && a.dataUrl) {
                return `<img class="cw-msg-image" src="${a.dataUrl}" alt="${esc(a.name)}" />`;
            }
            return `<div class="cw-attachment" style="margin-top:6px;">📎 ${esc(a.name)} (${formatSize(a.size)})</div>`;
        }).join('');
    }

    // Branch navigator (← 1/3 →)
    let branchNav = '';
    if (isUser) {
        const bp = getBranchPointAt(index);
        if (bp && bp.branches.length > 1) {
            branchNav = `<span class="cw-branch-nav" data-idx="${index}">
                <button class="cw-branch-prev" data-idx="${index}" title="前の分岐">◀</button>
                <span class="cw-branch-label">${bp.activeBranch + 1} / ${bp.branches.length}</span>
                <button class="cw-branch-next" data-idx="${index}" title="次の分岐">▶</button>
            </span>`;
        }
    }

    const retryBtn = !isUser ? `<button class="cw-msg-retry" title="再生成" data-idx="${index}">🔄</button>` : '';
    const copyMsgBtn = `<button class="cw-msg-copy" title="コピー" data-idx="${index}">📋</button>`;
    const editBtn = isUser ? `<button class="cw-msg-edit" title="編集" data-idx="${index}">✏️</button>` : '';

    return `
    <div class="cw-msg ${isUser ? 'cw-msg-user' : 'cw-msg-assistant'}" data-idx="${index}">
      <div class="cw-msg-avatar">${isUser ? '👤' : '✦'}</div>
      <div class="cw-msg-content">
        <div class="cw-msg-bubble">${rendered}${attachmentHtml}</div>
        <div class="cw-msg-meta">
          <span>${formatTime(msg.timestamp)}</span>
          ${modelTag}
          ${branchNav}
          ${editBtn}${copyMsgBtn}${retryBtn}
          <button class="cw-msg-delete" title="削除" data-idx="${index}">✕</button>
        </div>
      </div>
    </div>
  `;
}

function renderMessages(): void {
    const container = document.getElementById('cw-messages');
    if (!container) return;
    const msgs = getMessages();

    if (msgs.length === 0) {
        container.innerHTML = `
      <div class="cw-empty">
        <div class="cw-empty-icon">✦</div>
        <div class="cw-empty-title">何をお手伝いしましょう？</div>
        <div class="cw-empty-subtitle">HGK と対話を始めましょう</div>
        <div class="cw-empty-hints">
          <span class="cw-hint">HGK の現在の方向性は？</span>
          <span class="cw-hint">FEP を簡単に説明して</span>
          <span class="cw-hint">CCL の @helm を解説</span>
        </div>
      </div>
    `;
        container.querySelectorAll('.cw-hint').forEach(chip => {
            chip.addEventListener('click', () => {
                const input = document.getElementById('cw-input') as HTMLTextAreaElement | null;
                if (input && !isStreaming) { input.value = chip.textContent ?? ''; void handleSend(); }
            });
        });
        return;
    }

    container.innerHTML = msgs.map((m, i) => renderMessage(m, i)).join('');
    container.scrollTop = container.scrollHeight;

    container.querySelectorAll('.cw-msg-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            const msgs = getMessages();
            if (idx >= 0 && idx < msgs.length) {
                msgs.splice(idx, 1);
                setMessages(msgs);
                saveAllConversations();
                renderMessages();
            }
        });
    });

    // Retry (regenerate) button
    container.querySelectorAll('.cw-msg-retry').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (isStreaming) return;
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            const msgs = getMessages();
            // Find the last user message before this assistant message
            let userText = '';
            for (let i = idx - 1; i >= 0; i--) {
                if (msgs[i]?.role === 'user') { userText = msgs[i]?.content ?? ''; break; }
            }
            if (!userText) return;
            // Remove the assistant message being regenerated
            msgs.splice(idx, 1);
            setMessages(msgs);
            saveAllConversations();
            renderMessages();
            void handleSend(userText);
        });
    });

    // Copy message button
    container.querySelectorAll('.cw-msg-copy').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            const msgs = getMessages();
            if (idx >= 0 && idx < msgs.length) {
                void navigator.clipboard.writeText(msgs[idx]?.content ?? '').then(() => {
                    (btn as HTMLElement).textContent = '✓';
                    setTimeout(() => { (btn as HTMLElement).textContent = '📋'; }, 1500);
                });
            }
        });
    });

    enhanceCodeBlocks(container);
    enhanceAlerts(container);

    // Edit message button
    container.querySelectorAll('.cw-msg-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (isStreaming) return;
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            startEditMessage(idx);
        });
    });

    // Branch navigation buttons (◀ ▶)
    container.querySelectorAll('.cw-branch-prev').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            switchBranch(idx, -1);
        });
    });
    container.querySelectorAll('.cw-branch-next').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt((btn as HTMLElement).dataset.idx ?? '-1', 10);
            switchBranch(idx, 1);
        });
    });
}

// ─── Message Edit (Non-destructive Branching) ───────────────

function getBranchPoints(): BranchPoint[] {
    const conv = conversations.find(c => c.id === activeConvId);
    if (!conv) return [];
    if (!conv.branchPoints) conv.branchPoints = [];
    return conv.branchPoints;
}

function getBranchPointAt(idx: number): BranchPoint | undefined {
    return getBranchPoints().find(bp => bp.atIndex === idx);
}

function switchBranch(idx: number, direction: 1 | -1): void {
    const bp = getBranchPointAt(idx);
    if (!bp || bp.branches.length <= 1) return;

    // Save current active branch's messages before switching
    const msgs = getMessages();
    bp.branches[bp.activeBranch] = msgs.slice(bp.atIndex);

    // Switch to the next/previous branch
    bp.activeBranch = (bp.activeBranch + direction + bp.branches.length) % bp.branches.length;

    // Replace messages from branch point onwards
    const prefix = msgs.slice(0, bp.atIndex);
    const branchMsgs = bp.branches[bp.activeBranch] || [];
    setMessages([...prefix, ...branchMsgs]);
    saveAllConversations();
    renderMessages();
}

function startEditMessage(idx: number): void {
    const msgs = getMessages();
    if (idx < 0 || idx >= msgs.length || msgs[idx]?.role !== 'user') return;
    const msgEl = document.querySelector(`.cw-msg[data-idx="${idx}"]`);
    if (!msgEl) return;
    const bubble = msgEl.querySelector('.cw-msg-bubble') as HTMLElement | null;
    if (!bubble) return;

    const originalText = msgs[idx]?.content ?? '';
    bubble.innerHTML = `
        <textarea class="cw-msg-edit-area">${esc(originalText)}</textarea>
        <div class="cw-msg-edit-actions">
            <button class="cw-msg-edit-save">保存して送信</button>
            <button class="cw-msg-edit-cancel">キャンセル</button>
        </div>
    `;

    const textarea = bubble.querySelector('.cw-msg-edit-area') as HTMLTextAreaElement;
    if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        textarea.style.height = Math.max(60, textarea.scrollHeight) + 'px';
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });
    }

    bubble.querySelector('.cw-msg-edit-save')?.addEventListener('click', () => {
        const newText = textarea?.value?.trim();
        if (!newText) return;

        const conv = conversations.find(c => c.id === activeConvId);
        if (!conv) return;
        if (!conv.branchPoints) conv.branchPoints = [];

        // Find or create BranchPoint at this index
        let bp = conv.branchPoints.find(b => b.atIndex === idx);
        if (!bp) {
            // First edit at this position — create BranchPoint with original as branch 0
            bp = { atIndex: idx, branches: [msgs.slice(idx)], activeBranch: 0 };
            conv.branchPoints.push(bp);
        } else {
            // Save current active branch before creating new one
            bp.branches[bp.activeBranch] = msgs.slice(idx);
        }

        // Create new branch: edited msg + (will receive AI response via handleSend)
        const editedMsg: ChatMessage = {
            ...msgs[idx]!,
            content: newText,
            timestamp: new Date(),
        };
        const newBranch: ChatMessage[] = [editedMsg];
        bp.branches.push(newBranch);
        bp.activeBranch = bp.branches.length - 1;

        // Update visible messages: keep prefix + new branch
        const prefix = msgs.slice(0, idx);
        setMessages([...prefix, ...newBranch]);
        saveAllConversations();
        renderMessages();
        void handleSend(newText);
    });

    bubble.querySelector('.cw-msg-edit-cancel')?.addEventListener('click', () => {
        renderMessages();
    });
}

// ─── Chat Search ─────────────────────────────────────────────

let searchVisible = false;
let searchMatches: HTMLElement[] = [];
let searchCurrentIdx = -1;

function toggleSearchBar(): void {
    searchVisible = !searchVisible;
    const bar = document.getElementById('cw-search-bar');
    if (bar) {
        bar.style.display = searchVisible ? 'flex' : 'none';
        if (searchVisible) {
            const input = bar.querySelector('.cw-search-input') as HTMLInputElement | null;
            input?.focus();
        } else {
            clearSearchHighlights();
        }
    }
}

function performSearch(query: string): void {
    clearSearchHighlights();
    if (!query.trim()) { updateSearchStatus(''); return; }

    const container = document.getElementById('cw-messages');
    if (!container) return;
    const bubbles = container.querySelectorAll('.cw-msg-bubble');

    searchMatches = [];
    bubbles.forEach(bubble => {
        const walker = document.createTreeWalker(bubble, NodeFilter.SHOW_TEXT);
        let node: Text | null;
        while ((node = walker.nextNode() as Text | null)) {
            const text = node.nodeValue || '';
            const lowerText = text.toLowerCase();
            const lowerQuery = query.toLowerCase();
            let startIdx = 0;
            let pos: number;
            while ((pos = lowerText.indexOf(lowerQuery, startIdx)) !== -1) {
                const range = document.createRange();
                range.setStart(node, pos);
                range.setEnd(node, pos + query.length);
                const mark = document.createElement('mark');
                mark.className = 'cw-search-highlight';
                range.surroundContents(mark);
                searchMatches.push(mark);
                // After surroundContents, walker position is invalid — restart
                startIdx = pos + query.length;
                break; // re-walk from here on next iteration
            }
        }
    });

    searchCurrentIdx = searchMatches.length > 0 ? 0 : -1;
    if (searchCurrentIdx >= 0) {
        searchMatches[0]!.classList.add('cw-search-active');
        searchMatches[0]!.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    updateSearchStatus(query);
}

function navigateSearch(direction: 1 | -1): void {
    if (searchMatches.length === 0) return;
    searchMatches[searchCurrentIdx]?.classList.remove('cw-search-active');
    searchCurrentIdx = (searchCurrentIdx + direction + searchMatches.length) % searchMatches.length;
    searchMatches[searchCurrentIdx]!.classList.add('cw-search-active');
    searchMatches[searchCurrentIdx]!.scrollIntoView({ behavior: 'smooth', block: 'center' });
    updateSearchStatus('');
}

function clearSearchHighlights(): void {
    document.querySelectorAll('.cw-search-highlight').forEach(mark => {
        const parent = mark.parentNode;
        if (parent) {
            parent.replaceChild(document.createTextNode(mark.textContent || ''), mark);
            parent.normalize();
        }
    });
    searchMatches = [];
    searchCurrentIdx = -1;
}

function updateSearchStatus(query: string): void {
    const status = document.getElementById('cw-search-status');
    if (!status) return;
    if (searchMatches.length === 0 && query) {
        status.textContent = '一致なし';
    } else if (searchMatches.length > 0) {
        status.textContent = `${searchCurrentIdx + 1} / ${searchMatches.length}`;
    } else {
        status.textContent = '';
    }
}


function renderConvList(): void {
    const list = document.getElementById('cw-conv-list');
    if (!list) return;
    list.innerHTML = conversations.map(c => `
    <div class="cw-conv-item ${c.id === activeConvId ? 'active' : ''}" data-cid="${c.id}">
      <div class="cw-conv-title">${esc(c.title || 'New Chat')}</div>
      <div class="cw-conv-meta">${c.messages.length} messages</div>
    </div>
  `).join('');

    list.querySelectorAll('.cw-conv-item').forEach(item => {
        item.addEventListener('click', () => {
            activeConvId = (item as HTMLElement).dataset.cid || '';
            renderConvList();
            renderMessages();
        });
    });
}

// ─── Loading State ───────────────────────────────────────────

function setLoading(loading: boolean): void {
    isStreaming = loading;
    const btn = document.getElementById('cw-send-btn') as HTMLButtonElement | null;
    const input = document.getElementById('cw-input') as HTMLTextAreaElement | null;
    if (btn) {
        if (loading) {
            btn.disabled = false;
            btn.innerHTML = '■';
            btn.title = 'ストリーミング停止';
            btn.onclick = () => {
                if (currentAbortController) {
                    currentAbortController.abort();
                    currentAbortController = null;
                    setLoading(false);
                }
            };
        } else {
            btn.disabled = false;
            btn.innerHTML = '↑';
            btn.title = '送信';
            btn.onclick = null;
        }
    }
    if (input) input.disabled = loading;
    const indicator = document.getElementById('cw-typing');
    if (indicator) indicator.style.display = loading ? 'flex' : 'none';
}

// ─── Event Handlers ──────────────────────────────────────────

async function handleSend(retryText?: string): Promise<void> {
    const input = document.getElementById('cw-input') as HTMLTextAreaElement | null;
    const text = retryText ?? input?.value.trim() ?? '';
    if (!text || isStreaming) return;

    // Ensure we have an active conversation
    if (!activeConvId || !conversations.find(c => c.id === activeConvId)) {
        createNewConversation();
    }

    if (input && !retryText) { input.value = ''; input.style.height = 'auto'; }
    setLoading(true);

    // Update conversation title from first message
    const conv = conversations.find(c => c.id === activeConvId);
    if (conv && conv.messages.length === 0) {
        conv.title = text.slice(0, 50);
        renderConvList();
    }

    try {
        if (colonyMode) await sendToColony(text);
        else if (agentMode) await sendToAgent(text);
        else await sendToGemini(text);
    } catch (err) {
        const container = document.getElementById('cw-messages');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'cw-error-msg';
        errorDiv.innerHTML = `⚠️ ${esc(friendlyError((err as Error).message))} <button class="cw-retry-btn">🔄 再送</button>`;
        container?.appendChild(errorDiv);
        errorDiv.querySelector('.cw-retry-btn')?.addEventListener('click', () => {
            errorDiv.remove();
            void handleSend(text);
        });
        if (container) container.scrollTop = container.scrollHeight;
    } finally {
        setLoading(false);
    }
}

function handleKeyDown(e: KeyboardEvent): void {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        void handleSend();
    }
}

function autoResize(textarea: HTMLTextAreaElement): void {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// ─── Conversations ───────────────────────────────────────────

function createNewConversation(): void {
    const conv: Conversation = {
        id: genId(), title: 'New Chat', messages: [], createdAt: new Date(),
    };
    conversations.unshift(conv);
    activeConvId = conv.id;
    saveAllConversations();
    renderConvList();
    renderMessages();
}

// ─── Attachments & Paste ─────────────────────────────────────

function renderAttachments(): void {
    const area = document.getElementById('cw-attachments');
    if (!area) return;
    if (pendingAttachments.length === 0) { area.innerHTML = ''; return; }
    area.innerHTML = pendingAttachments.map((a, i) => {
        const preview = a.mime?.startsWith('image/') && a.dataUrl
            ? `<img src="${a.dataUrl}" alt="" />`
            : '📎';
        return `<div class="cw-attachment">${preview} ${esc(a.name)} (${formatSize(a.size)})
            <button class="cw-attachment-remove" data-aidx="${i}">✕</button></div>`;
    }).join('');
    area.querySelectorAll('.cw-attachment-remove').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt((btn as HTMLElement).dataset.aidx ?? '-1', 10);
            if (idx >= 0) { pendingAttachments.splice(idx, 1); renderAttachments(); }
        });
    });
}

async function handleFileUpload(file: File): Promise<void> {
    const dataUrl = file.type.startsWith('image/') ? await readFileAsDataUrl(file) : undefined;

    // Upload to API
    const formData = new FormData();
    formData.append('file', file);
    try {
        const resp = await fetch('/api/files/upload', { method: 'POST', body: formData });
        const result = await resp.json();
        pendingAttachments.push({
            name: file.name, path: result.path || '', mime: file.type,
            size: file.size, dataUrl,
        });
    } catch {
        pendingAttachments.push({
            name: file.name, path: '', mime: file.type,
            size: file.size, dataUrl,
        });
    }
    renderAttachments();
}

function readFileAsDataUrl(file: File): Promise<string> {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
    });
}

function handlePaste(e: ClipboardEvent): void {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item && item.type.startsWith('image/')) {
            e.preventDefault();
            const file = item.getAsFile();
            if (file) {
                const name = `screenshot_${new Date().toISOString().slice(11, 19).replace(/:/g, '')}.png`;
                const renamed = new File([file], name, { type: file.type });
                void handleFileUpload(renamed);
            }
            return;
        }
    }
}

function handleDrop(e: DragEvent): void {
    e.preventDefault();
    const dt = e.dataTransfer;
    if (!dt?.files.length) return;
    for (let i = 0; i < dt.files.length; i++) {
        const f = dt.files[i];
        if (f) void handleFileUpload(f);
    }
}

// ─── Right Panel: Files ──────────────────────────────────────

async function loadFileTree(path: string = '~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon'): Promise<void> {
    currentFilePath = path;
    const content = document.getElementById('cw-panel-content');
    if (!content || activeRightTab !== 'files') return;
    content.innerHTML = '<div style="color:var(--cw-text-tertiary);padding:8px;">読込中...</div>';

    try {
        const resp = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`);
        const data = await resp.json();
        if (data.error || data.detail || !data.path) {
            content.innerHTML = `<div style="color:var(--cw-error);padding:8px;">${esc(data.error || data.detail || 'ファイル一覧の取得に失敗しました')}</div>`;
            return;
        }

        // Breadcrumb
        const parts = data.path.split('/').filter(Boolean);
        const breadcrumb = parts.map((p: string, i: number) => {
            const fullPath = '/' + parts.slice(0, i + 1).join('/');
            return `<button class="cw-breadcrumb-item" data-path="${fullPath}">${esc(p)}</button>`;
        }).join(' / ');

        // File list
        const items = data.entries.map((e: Record<string, unknown>) => {
            const icon = e.is_dir ? '📁' : getFileIcon(String(e.name));
            const size = e.is_dir ? '' : `<span class="cw-file-size">${formatSize(Number(e.size || 0))}</span>`;
            return `<div class="cw-file-item ${e.is_dir ? 'dir' : ''}" data-path="${esc(String(e.path))}" data-isdir="${e.is_dir}">
        <span class="cw-file-icon">${icon}</span>
        <span class="cw-file-name">${esc(String(e.name))}</span>
        ${size}
      </div>`;
        }).join('');

        content.innerHTML = `<div class="cw-breadcrumb">${breadcrumb}</div><div class="cw-file-tree">${items}</div>`;

        // Click handlers
        content.querySelectorAll('.cw-breadcrumb-item').forEach(btn => {
            btn.addEventListener('click', () => void loadFileTree((btn as HTMLElement).dataset.path || ''));
        });
        content.querySelectorAll('.cw-file-item').forEach(item => {
            item.addEventListener('click', () => {
                const el = item as HTMLElement;
                if (el.dataset.isdir === 'true') void loadFileTree(el.dataset.path || '');
                else void loadFileContent(el.dataset.path || '');
            });
        });
    } catch (err) {
        content.innerHTML = `<div style="color:var(--cw-error);padding:8px;">ファイル読込失敗: ${esc((err as Error).message)}</div>`;
    }
}

async function loadFileContent(path: string): Promise<void> {
    const content = document.getElementById('cw-panel-content');
    if (!content) return;
    content.innerHTML = '<div style="color:var(--cw-text-tertiary);padding:8px;">読込中...</div>';

    try {
        const resp = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
        const data = await resp.json();
        if (data.error) { content.innerHTML = `<div style="color:var(--cw-error);padding:8px;">${esc(data.error)}</div>`; return; }

        const fileName = path.split('/').pop() || '';
        const backPath = path.split('/').slice(0, -1).join('/');
        const isMd = fileName.endsWith('.md') || fileName.endsWith('.markdown');

        currentFileContent = data.content || '';

        if (data.encoding === 'text') {
            const preview = data.content.length > 50000 ? data.content.slice(0, 50000) + '\n\n... (truncated)' : data.content;

            // File header with action buttons
            const mdToggle = isMd
                ? `<button class="cw-file-action-btn" id="cw-md-toggle" title="表示切替">${mdViewMode === 'rendered' ? '📝 Raw' : '👁️ View'}</button>`
                : '';

            content.innerHTML = `
        <div class="cw-file-header">
          <div class="cw-file-header-left">
            <button class="cw-breadcrumb-item" data-back="${backPath}">← 戻る</button>
            <span class="cw-file-header-name">${esc(fileName)}</span>
            <span class="cw-file-header-size">${formatSize(data.size)}</span>
          </div>
          <div class="cw-file-header-actions">
            ${mdToggle}
            <button class="cw-file-action-btn" id="cw-file-copy" title="コピー">📋 Copy</button>
            <button class="cw-file-action-btn" id="cw-file-folder" title="フォルダで表示">📂</button>
          </div>
        </div>
        <div id="cw-file-body">
          ${isMd && mdViewMode === 'rendered'
                    ? `<div class="cw-md-rendered">${marked.parse(preview) as string}</div>`
                    : `<pre class="cw-file-viewer">${esc(preview)}</pre>`}
        </div>
      `;

            // MD toggle handler
            content.querySelector('#cw-md-toggle')?.addEventListener('click', () => {
                mdViewMode = mdViewMode === 'rendered' ? 'raw' : 'rendered';
                void loadFileContent(path); // re-render
            });

            // Copy handler
            content.querySelector('#cw-file-copy')?.addEventListener('click', () => {
                void navigator.clipboard.writeText(currentFileContent).then(() => {
                    const btn = content.querySelector('#cw-file-copy');
                    if (btn) { btn.textContent = '✓ Copied'; setTimeout(() => { btn.textContent = '📋 Copy'; }, 1500); }
                });
            });

            // Folder handler — navigate back to parent dir
            content.querySelector('#cw-file-folder')?.addEventListener('click', () => void loadFileTree(backPath));

        } else if (data.mime?.startsWith('image/')) {
            content.innerHTML = `
        <div class="cw-file-header">
          <div class="cw-file-header-left">
            <button class="cw-breadcrumb-item" data-back="${backPath}">← 戻る</button>
            <span class="cw-file-header-name">${esc(fileName)}</span>
          </div>
          <div class="cw-file-header-actions">
            <button class="cw-file-action-btn" id="cw-file-folder" title="フォルダで表示">📂</button>
          </div>
        </div>
        <img src="data:${data.mime};base64,${data.content}" style="max-width:100%;border-radius:var(--cw-radius-sm);" />
      `;
            content.querySelector('#cw-file-folder')?.addEventListener('click', () => void loadFileTree(backPath));
        } else {
            content.innerHTML = `
        <div class="cw-file-header">
          <div class="cw-file-header-left">
            <button class="cw-breadcrumb-item" data-back="${backPath}">← 戻る</button>
            <span class="cw-file-header-name">${esc(fileName)}</span>
          </div>
        </div>
        <div style="color:var(--cw-text-tertiary);padding:16px;">バイナリファイル (${esc(data.mime || 'unknown')})</div>
      `;
        }

        content.querySelector('[data-back]')?.addEventListener('click', () => void loadFileTree(backPath));
    } catch (err) {
        content.innerHTML = `<div style="color:var(--cw-error);padding:8px;">読込失敗: ${esc((err as Error).message)}</div>`;
    }
}

function getFileIcon(name: string): string {
    const ext = name.split('.').pop()?.toLowerCase() || '';
    const icons: Record<string, string> = {
        py: '🐍', ts: '📘', js: '📒', rs: '🦀', md: '📝', json: '📋',
        yaml: '⚙️', yml: '⚙️', css: '🎨', html: '🌐', sh: '🖥️',
        toml: '⚙️', txt: '📄', png: '🖼️', jpg: '🖼️', svg: '🎨',
    };
    return icons[ext] || '📄';
}

// ─── Right Panel: Terminal Tab ──────────────────────────────

function updateTerminalTab(): void {
    if (activeRightTab !== 'terminal') return;
    const content = document.getElementById('cw-panel-content');
    if (!content) return;
    const entries = terminalLog.slice(-100).map(l => {
        const cls = l.startsWith('❌') ? 'cw-terminal-err' : l.startsWith('✅') ? 'cw-terminal-out' : 'cw-terminal-cmd';
        return `<div class="cw-terminal-entry ${cls}">${esc(l)}</div>`;
    }).join('');
    content.innerHTML = `<div class="cw-terminal">${entries || '<div style="color:var(--cw-text-tertiary);">Agent モードでツールを実行するとここに表示されます</div>'}</div>`;
    content.scrollTop = content.scrollHeight;
}

// ─── Right Panel Tab Switching ──────────────────────────────

function switchRightTab(tab: 'files' | 'terminal' | 'ai'): void {
    activeRightTab = tab;
    document.querySelectorAll('.cw-panel-tab').forEach(t => t.classList.toggle('active', (t as HTMLElement).dataset.tab === tab));
    if (tab === 'files') void loadFileTree(currentFilePath || '~/oikos/01_ヘゲモニコン｜Hegemonikon');
    else if (tab === 'terminal') updateTerminalTab();
    else {
        const content = document.getElementById('cw-panel-content');
        if (content) content.innerHTML = '<div style="color:var(--cw-text-tertiary);padding:16px;text-align:center;">AI thinking ログ<br/><small>Agent モード実行時に表示</small></div>';
    }
}

// ─── Sidebar Toggle ──────────────────────────────────────────

function toggleSidebar(): void {
    sidebarVisible = !sidebarVisible;
    const sidebar = document.getElementById('cw-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('cw-sidebar-hidden', !sidebarVisible);
    }
}

// ─── Settings ────────────────────────────────────────────────

function showSettingsDialog(): void {
    const existing = document.getElementById('cw-settings-dialog');
    if (existing) existing.remove();

    const dialog = document.createElement('div');
    dialog.id = 'cw-settings-dialog';
    dialog.className = 'cw-dialog-overlay';
    dialog.innerHTML = `
    <div class="cw-dialog">
      <h3>⚙️ 設定</h3>
      <label style="color:var(--cw-text-secondary);font-size:var(--cw-font-size-sm);display:block;margin-bottom:4px;">🔑 Gemini API キー</label>
      <input type="password" id="cw-apikey-input" class="cw-input" placeholder="AIzaSy..." value="${esc(apiKey)}" />
      <label style="color:var(--cw-text-secondary);font-size:var(--cw-font-size-sm);display:block;margin-bottom:4px;">📝 システムプロンプト</label>
      <textarea id="cw-sysprompt-input" class="cw-input" rows="4" style="resize:vertical;font-family:inherit;">${esc(systemInstruction)}</textarea>
      <div class="cw-dialog-actions">
        <button id="cw-cancel" class="cw-btn">キャンセル</button>
        <button id="cw-save" class="cw-btn cw-btn-primary">保存</button>
      </div>
    </div>
  `;
    document.body.appendChild(dialog);

    document.getElementById('cw-cancel')?.addEventListener('click', () => dialog.remove());
    document.getElementById('cw-save')?.addEventListener('click', () => {
        const keyInput = document.getElementById('cw-apikey-input') as HTMLInputElement;
        const sysInput = document.getElementById('cw-sysprompt-input') as HTMLTextAreaElement;
        const key = keyInput.value.trim();
        if (key) { apiKey = key; localStorage.setItem('hgk-gemini-api-key', key); }
        systemInstruction = sysInput.value;
        localStorage.setItem('hgk-chat-sysprompt', systemInstruction);
        dialog.remove();
        updateConnectionStatus(!!apiKey);
    });
}

function updateConnectionStatus(connected: boolean): void {
    const statusEl = document.getElementById('cw-status');
    if (!statusEl) return;
    // When using backend proxy, always show connected (serve.py handles auth)
    const isConnected = connected || useBackend;
    statusEl.innerHTML = isConnected
        ? `<span class="cw-connector-dot online" style="display:inline-block;margin-right:4px;"></span>${esc(MODELS[currentModel] || currentModel)}`
        : '<span class="cw-connector-dot offline" style="display:inline-block;margin-right:4px;"></span>未接続';
}

// ─── Main View ───────────────────────────────────────────────

export async function renderChatView(): Promise<void> {
    const app = document.getElementById('view-content');
    if (!app) return;

    await loadApiKey();
    loadAllConversations();
    const savedSysPrompt = localStorage.getItem('hgk-chat-sysprompt');
    if (savedSysPrompt !== null) systemInstruction = savedSysPrompt;

    if (conversations.length === 0) createNewConversation();

    const modelOptions = Object.entries(MODELS).map(([id, name]) =>
        `<option value="${id}" ${id === currentModel ? 'selected' : ''}>${esc(name)}</option>`
    ).join('');

    app.innerHTML = `
    <div class="cw-layout">
      <!-- Left: Conversations -->
      <div class="cw-sidebar ${sidebarVisible ? '' : 'cw-sidebar-hidden'}" id="cw-sidebar">
        <div class="cw-sidebar-header">
          <span class="cw-sidebar-title">Chats</span>
          <button id="cw-new-chat" class="cw-new-chat-btn" title="新規チャット">+</button>
        </div>
        <div id="cw-conv-list" class="cw-conv-list"></div>
      </div>

      <!-- Center: Chat -->
      <div class="cw-main">
        <div class="cw-main-header">
          <div class="cw-main-header-left">
            <button id="cw-sidebar-toggle" class="cw-icon-btn" title="サイドバー切替 (Ctrl+B)">☰</button>
            <span id="cw-status" style="font-size:var(--cw-font-size-sm);color:var(--cw-text-secondary);">
              ${(apiKey || useBackend)
            ? `<span class="cw-connector-dot online" style="display:inline-block;margin-right:4px;"></span>${esc(MODELS[currentModel] || currentModel)}`
            : '<span class="cw-connector-dot offline" style="display:inline-block;margin-right:4px;"></span>未接続'}
            </span>
          </div>
          <div class="cw-main-header-right">
            <button id="cw-search-toggle" class="cw-icon-btn" title="検索 (Ctrl+F)">🔍</button>
            <button id="cw-colony-toggle" class="cw-icon-btn ${colonyMode ? 'active' : ''}" title="Colony モード (F6 多AI組織)">🏛️</button>
            <button id="cw-agent-toggle" class="cw-icon-btn ${agentMode ? 'active' : ''}" title="Agent モード">🔧</button>
            <select id="cw-model-select" class="cw-model-select">${modelOptions}</select>
            <button id="cw-settings-btn" class="cw-icon-btn" title="設定">⚙️</button>
            <button id="cw-clear-btn" class="cw-icon-btn" title="会話クリア">🗑️</button>
          </div>
        </div>

        <div id="cw-search-bar" class="cw-search-bar" style="display:none; padding:8px 16px; background:var(--cw-surface-raised); border-bottom:1px solid var(--cw-border); align-items:center; gap:8px;">
            <input type="text" class="cw-input cw-search-input" placeholder="チャット内を検索..." style="flex:1;" />
            <span id="cw-search-status" style="color:var(--cw-text-secondary); font-size:var(--cw-font-size-sm); min-width:60px; text-align:right;"></span>
            <button class="cw-icon-btn cw-search-up" title="前へ">↑</button>
            <button class="cw-icon-btn cw-search-down" title="次へ">↓</button>
            <button class="cw-icon-btn cw-search-close" style="margin-left:8px;" title="閉じる">✕</button>
        </div>

        <div id="cw-messages" class="cw-messages"></div>

        <div id="cw-typing" class="cw-typing" style="display:none;">
          <div class="cw-typing-dots"><span></span><span></span><span></span></div>
          <span>${colonyMode ? '🏛️ Colony 実行中...' : agentMode ? '🔧 ツール実行中...' : '応答を生成中...'}</span>
        </div>

        <div id="cw-attachments" class="cw-attachments"></div>

        <div class="cw-input-area"
          id="cw-input-area"
          ondragover="event.preventDefault()">
          <div class="cw-input-container">
            <button id="cw-attach-btn" class="cw-attach-btn" title="ファイル添付">📎</button>
            <textarea id="cw-input" class="cw-textarea"
              placeholder="メッセージを入力... (Enter で送信)"
              rows="1"></textarea>
            <button id="cw-mcp-demo" class="mcp-demo-btn" title="MCP App デモ">⚡F5</button>
            <button id="cw-send-btn" class="cw-send-btn">↑</button>
          </div>
        </div>
      </div>

      <!-- Right: Files / Terminal / AI -->
      <div class="cw-panel">
        <div class="cw-panel-tabs">
          <button class="cw-panel-tab active" data-tab="files">Files</button>
          <button class="cw-panel-tab" data-tab="terminal">Terminal</button>
          <button class="cw-panel-tab" data-tab="ai">AI</button>
        </div>
        <div id="cw-panel-content" class="cw-panel-content"></div>
        <div class="cw-context">
          <div class="cw-context-title">コネクタ</div>
          <div class="cw-connector">
            <span class="cw-connector-icon">⚡</span>
            HGK Gateway
            <span class="cw-connector-dot online"></span>
          </div>
          <div class="cw-connector">
            <span class="cw-connector-icon">🧠</span>
            Ochēma
            <span class="cw-connector-dot online"></span>
          </div>
        </div>
      </div>
    </div>
  `;

    // Initial renders
    renderConvList();
    renderMessages();
    void loadFileTree();

    // Event bindings
    const input = document.getElementById('cw-input') as HTMLTextAreaElement;
    const sendBtn = document.getElementById('cw-send-btn')!;
    const modelSelect = document.getElementById('cw-model-select') as HTMLSelectElement;
    const settingsBtn = document.getElementById('cw-settings-btn')!;
    const clearBtn = document.getElementById('cw-clear-btn')!;
    const newChatBtn = document.getElementById('cw-new-chat')!;
    const agentToggle = document.getElementById('cw-agent-toggle')!;
    const attachBtn = document.getElementById('cw-attach-btn')!;
    const inputArea = document.getElementById('cw-input-area')!;

    input.addEventListener('keydown', handleKeyDown);
    input.addEventListener('input', () => autoResize(input));
    input.addEventListener('paste', handlePaste);
    sendBtn.addEventListener('click', () => void handleSend());
    settingsBtn.addEventListener('click', showSettingsDialog);
    newChatBtn.addEventListener('click', createNewConversation);

    // F5: MCP App Demo button
    const mcpDemoBtn = document.getElementById('cw-mcp-demo');
    mcpDemoBtn?.addEventListener('click', () => {
        const container = document.getElementById('cw-messages');
        if (!container) return;
        const demoData = [
            { title: 'Free Energy Principle and Active Inference', url: 'https://arxiv.org/abs/2012.01714', source: 'Semantic Scholar', score: 0.95 },
            { title: 'The Markov blankets of life', url: 'https://doi.org/10.1098/rsif.2017.0792', source: 'Gnōsis', score: 0.89 },
            { title: 'Variational inference with normalizing flows', url: 'https://arxiv.org/abs/1505.05770', source: 'arXiv', score: 0.82 },
            { title: 'Planning as inference in active learning', url: '#', source: 'Sophia', score: 0.78 },
            { title: 'Bayesian brain hypothesis', url: '#', source: 'Wikipedia', score: 0.71 },
        ];
        renderMcpApp(container, createDemoAppHtml('periskope_search', demoData), {
            toolName: 'periskope_search',
            onOpenLink: (url) => window.open(url, '_blank', 'noopener'),
            onMessage: (msg) => console.log('[MCP App]', msg),
        });
        container.scrollTop = container.scrollHeight;
    });

    // Sidebar toggle & Search shortcut
    const sidebarToggle = document.getElementById('cw-sidebar-toggle')!;
    sidebarToggle.addEventListener('click', toggleSidebar);

    document.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.ctrlKey && e.key === 'b' && !e.shiftKey && !e.altKey) {
            const el = e.target as HTMLElement;
            if (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') {
                e.preventDefault();
                toggleSidebar();
            }
        }
        if (e.ctrlKey && e.key === 'f' && !e.shiftKey && !e.altKey) {
            e.preventDefault();
            toggleSearchBar();
        }
    });

    // Search events
    const searchToggleBtn = document.getElementById('cw-search-toggle')!;
    const searchInput = document.querySelector('.cw-search-input') as HTMLInputElement | null;
    searchToggleBtn.addEventListener('click', toggleSearchBar);
    document.querySelector('.cw-search-close')?.addEventListener('click', toggleSearchBar);
    searchInput?.addEventListener('input', (e) => performSearch((e.target as HTMLInputElement).value));
    searchInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') navigateSearch(e.shiftKey ? -1 : 1);
        if (e.key === 'Escape') {
            e.preventDefault();
            toggleSearchBar();
        }
    });
    document.querySelector('.cw-search-down')?.addEventListener('click', () => navigateSearch(1));
    document.querySelector('.cw-search-up')?.addEventListener('click', () => navigateSearch(-1));

    clearBtn.addEventListener('click', () => {
        const conv = conversations.find(c => c.id === activeConvId);
        if (conv) { conv.messages = []; saveAllConversations(); renderMessages(); }
    });

    modelSelect.addEventListener('change', () => {
        currentModel = modelSelect.value;
        updateConnectionStatus(!!apiKey);
    });

    agentToggle.addEventListener('click', () => {
        if (!agentMode && currentModel.startsWith('claude-')) {
            const warn = document.createElement('div');
            warn.className = 'cw-error-msg';
            warn.innerHTML = '⚠️ Agent モードは Gemini モデル専用です';
            document.getElementById('cw-messages')?.appendChild(warn);
            setTimeout(() => warn.remove(), 3000);
        }
        agentMode = !agentMode;
        if (agentMode) colonyMode = false; // Mutual exclusion
        agentToggle.classList.toggle('active', agentMode);
        const colonyToggle2 = document.getElementById('cw-colony-toggle');
        if (colonyToggle2) colonyToggle2.classList.toggle('active', colonyMode);
        const typingLabel = document.querySelector('#cw-typing span:last-child');
        if (typingLabel) typingLabel.textContent = colonyMode ? '🏛️ Colony 実行中...' : agentMode ? '🔧 ツール実行中...' : '応答を生成中...';
    });

    const colonyToggle = document.getElementById('cw-colony-toggle')!;
    colonyToggle.addEventListener('click', () => {
        colonyMode = !colonyMode;
        if (colonyMode) agentMode = false; // Mutual exclusion
        colonyToggle.classList.toggle('active', colonyMode);
        agentToggle.classList.toggle('active', agentMode);
        const typingLabel = document.querySelector('#cw-typing span:last-child');
        if (typingLabel) typingLabel.textContent = colonyMode ? '🏛️ Colony 実行中...' : agentMode ? '🔧 ツール実行中...' : '応答を生成中...';
    });

    // File attachment
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);
    attachBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files) {
            for (let i = 0; i < fileInput.files.length; i++) {
                const f = fileInput.files[i];
                if (f) void handleFileUpload(f);
            }
        }
        fileInput.value = '';
    });

    // Drag & drop
    inputArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        inputArea.style.borderColor = 'var(--cw-accent)';
    });
    inputArea.addEventListener('dragleave', () => {
        inputArea.style.borderColor = '';
    });
    inputArea.addEventListener('drop', (e) => {
        inputArea.style.borderColor = '';
        handleDrop(e);
    });

    // Right panel tabs
    document.querySelectorAll('.cw-panel-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchRightTab((tab as HTMLElement).dataset.tab as 'files' | 'terminal' | 'ai');
        });
    });

    input.focus();
}
