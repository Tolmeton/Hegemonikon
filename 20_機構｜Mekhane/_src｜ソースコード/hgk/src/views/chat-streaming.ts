/**
 * Chat Streaming — SSE Resilience + Reader 関数群
 * (ClawX adjoint: God Object 分割 + ToolStatus 構造化)
 *
 * chat.ts から SSE ストリーミングのロジックを分離。
 * UI 操作は StreamingDeps コールバック経由で行う。
 */

import { marked } from 'marked';
import { bumpEpoch } from '../api/client';
import { classifyLogMessage } from '../utils/log-classifier';
import { enhanceCodeBlocks, enhanceAlerts } from './enhance';
import type { ChatMessage, GeminiResponse, ToolStatus, StreamingDeps } from './chat-types';

// ─── SSE Resilience (from ClawX adjoint analysis) ────────────
// Safety Timeout: SSE イベントが一定時間来ない場合のタイムアウト
// Error Recovery Timer: エラー後に回復を待つ猶予期間

let _lastSSEEventAt = 0;
let _sseTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
let _errorRecoveryTimer: ReturnType<typeof setTimeout> | null = null;
const SSE_TIMEOUT_MS = 60_000;  // 60秒間イベントなしでタイムアウト
const ERROR_RECOVERY_MS = 3_000;  // エラー後3秒間は回復を待つ

export function recordSSEEvent(): void {
    _lastSSEEventAt = Date.now();
}

export function startSSETimeout(onTimeout: () => void): void {
    clearSSETimeout();
    _sseTimeoutTimer = setInterval(() => {
        if (_lastSSEEventAt > 0 && (Date.now() - _lastSSEEventAt) > SSE_TIMEOUT_MS) {
            console.warn(`[SSE] ${SSE_TIMEOUT_MS}ms 間イベントなし — タイムアウト`);
            clearSSETimeout();
            onTimeout();
        }
    }, 5_000);  // 5秒ごとにチェック
}

export function clearSSETimeout(): void {
    if (_sseTimeoutTimer) { clearInterval(_sseTimeoutTimer); _sseTimeoutTimer = null; }
}

export function clearErrorRecovery(): void {
    if (_errorRecoveryTimer) { clearTimeout(_errorRecoveryTimer); _errorRecoveryTimer = null; }
}

/** エラーを即座に表示せず、回復を待つ。回復しなければ onError を呼ぶ。 */
export function deferError(errorMsg: string, onError: (msg: string) => void): void {
    clearErrorRecovery();
    console.debug(`[SSE] Error deferred for ${ERROR_RECOVERY_MS}ms: ${errorMsg}`);
    _errorRecoveryTimer = setTimeout(() => {
        _errorRecoveryTimer = null;
        onError(errorMsg);
    }, ERROR_RECOVERY_MS);
}

/** エラーが回復した場合に呼ぶ (保留中のエラーをキャンセル) */
export function cancelDeferredError(): void {
    if (_errorRecoveryTimer) {
        console.debug('[SSE] Deferred error cancelled — stream recovered');
        clearErrorRecovery();
    }
}

// ─── DOM Update Helper ───────────────────────────────────────

export function updateLastMessage(content: string, thinking?: string, isThinkingActive?: boolean): void {
    const msgBodies = document.querySelectorAll('.cw-msg-bubble');
    const lastBody = msgBodies[msgBodies.length - 1];
    if (lastBody) {
        let html = '';
        if (thinking) {
            const openAttr = isThinkingActive ? ' open' : '';
            const thinkingLabel = isThinkingActive ? '💭 思考中...' : '💭 思考過程';
            const pulseClass = isThinkingActive ? ' cw-thinking-active' : '';
            html += `<details class="cw-thinking-block${pulseClass}"${openAttr}><summary>${thinkingLabel}</summary><div class="cw-thinking-content">${marked.parse(thinking) as string}</div></details>`;
        }
        html += marked.parse(content) as string;
        lastBody.innerHTML = html;
        enhanceCodeBlocks(lastBody as HTMLElement);
        enhanceAlerts(lastBody as HTMLElement);
        const container = document.getElementById('cw-messages');
        if (container) container.scrollTop = container.scrollHeight;
    }
}

// ─── SSE Readers ─────────────────────────────────────────────

/** 基本 SSE ストリーム (Gemini Direct API) */
export async function readSSEStream(response: Response, assistantMsg: ChatMessage, deps: StreamingDeps): Promise<string> {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    if (reader) {
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            recordSSEEvent();
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const raw = line.slice(6);
                if (raw === '[DONE]') continue;
                try {
                    const data: GeminiResponse = JSON.parse(raw);
                    const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
                    if (text) {
                        fullText += text;
                        assistantMsg.content = fullText;
                        updateLastMessage(fullText);
                    }
                } catch { /* skip */ }
            }
        }
    }
    if (!fullText) assistantMsg.content = '(応答なし)';
    deps.saveAllConversations();
    deps.renderMessages();
    return fullText;
}

/** Cortex SSE ストリーム (Backend API) */
export async function readCortexSSEStream(response: Response, assistantMsg: ChatMessage, deps: StreamingDeps): Promise<string> {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let thinkingText = '';
    let isThinking = false;

    if (reader) {
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            recordSSEEvent();
            let boundary = buffer.indexOf('\n\n');
            while (boundary !== -1) {
                const block = buffer.slice(0, boundary).trim();
                buffer = buffer.slice(boundary + 2);
                if (block.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(block.slice(6));
                        if (data.error) {
                            cancelDeferredError();
                            const errMsg = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                            fullText += `\n\n⚠️ ${errMsg}`;
                            assistantMsg.content = fullText;
                            updateLastMessage(fullText, thinkingText, false);
                            break;
                        }
                        if (data.thinking) {
                            if (!isThinking) isThinking = true;
                            thinkingText += data.thinking;
                            updateLastMessage(fullText, thinkingText, true);
                        }
                        if (data.text) {
                            if (isThinking) isThinking = false;
                            fullText += data.text;
                            assistantMsg.content = fullText;
                            updateLastMessage(fullText, thinkingText, false);
                        }
                    } catch (e) {
                        const classified = classifyLogMessage(String(e));
                        if (classified.level === 'drop') { /* ノイズ — 無視 */ }
                        else if (classified.level === 'error') {
                            assistantMsg.content += '\n\n⚠️ SSE error: ' + classified.normalized;
                        } else {
                            console.warn('[SSE] Parse error:', classified.normalized, block);
                            deferError(classified.normalized, (msg) => { assistantMsg.content += '\n\n⚠️ SSE parse error: ' + msg; });
                        }
                    }
                }
                boundary = buffer.indexOf('\n\n');
            }
        }
    }

    if (thinkingText) {
        assistantMsg.content = fullText;
    }
    if (!fullText && !thinkingText) assistantMsg.content = '(応答なし)';
    deps.saveAllConversations();
    deps.renderMessages();
    return fullText;
}

// ─── Agent SSE Reader (with ToolStatus tracking) ─────────────

/** ToolStatus[] から Markdown 表示を構築 */
function buildToolDisplay(statuses: ToolStatus[]): string {
    const lines: string[] = [];
    for (const ts of statuses) {
        if (ts.iteration !== undefined) {
            lines.push(`\n**🔄 ステップ ${ts.iteration}/${ts.maxIterations ?? '?'}**`);
        }
        switch (ts.state) {
            case 'running':
                lines.push(`- 🔧 \`${ts.name}\`(${formatArgs(ts.args)})`);
                break;
            case 'completed': {
                const dur = ts.duration != null ? ` (${ts.duration}ms)` : '';
                lines.push(`  - ✅ 完了${dur}`);
                if (ts.output) {
                    const preview = ts.output.slice(0, 100);
                    lines.push(`  > ${preview}${ts.output.length > 100 ? '...' : ''}`);
                }
                break;
            }
            case 'error': {
                const dur = ts.duration != null ? ` (${ts.duration}ms)` : '';
                lines.push(`  - ❌ エラー${dur}: ${ts.error || 'unknown'}`);
                break;
            }
            case 'approval_required':
                lines.push(`\n**⚠️ 承認待ち: \`${ts.name}\`**`);
                break;
        }
    }
    return lines.join('\n');
}

function formatArgs(args: Record<string, unknown>): string {
    const s = JSON.stringify(args || {});
    return s.length > 80 ? s.slice(0, 77) + '...' : s;
}

/** Agent モード SSE リーダー */
export async function readAgentSSEStream(response: Response, assistantMsg: ChatMessage, deps: StreamingDeps): Promise<string> {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let finalText = '';
    let thinkingText = '';
    let isThinkingActive = false;
    const toolStatuses: ToolStatus[] = [];

    if (!reader) { assistantMsg.content = '(ストリーム取得失敗)'; deps.renderMessages(); return ''; }

    function updateDisplay(content: string): void {
        assistantMsg.content = content;
        updateLastMessage(content, thinkingText || undefined, isThinkingActive);
    }

    let buffer = '';
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        recordSSEEvent();
        let boundary = buffer.indexOf('\n\n');
        while (boundary !== -1) {
            const block = buffer.slice(0, boundary).trim();
            buffer = buffer.slice(boundary + 2);

            if (block.startsWith('data: ')) {
                try {
                    const evt = JSON.parse(block.slice(6));
                    switch (evt.type) {
                        case 'iteration':
                            toolStatuses.push({
                                name: '__iteration__',
                                args: {},
                                state: 'running',
                                startedAt: Date.now(),
                                iteration: evt.iteration,
                                maxIterations: evt.max,
                            });
                            deps.terminalLog.push(`[Step ${evt.iteration}/${evt.max}]`);
                            updateDisplay(buildToolDisplay(toolStatuses));
                            break;
                        case 'tool_call':
                            toolStatuses.push({
                                name: evt.name,
                                args: evt.args || {},
                                state: 'running',
                                startedAt: Date.now(),
                            });
                            deps.terminalLog.push(`🔧 ${evt.name}(${formatArgs(evt.args || {})})`);
                            updateDisplay(buildToolDisplay(toolStatuses));
                            deps.updateTerminalTab();
                            break;
                        case 'tool_result': {
                            // 最後の running status を完了に更新
                            const lastRunning = [...toolStatuses].reverse().find(t => t.state === 'running' && t.name !== '__iteration__');
                            if (lastRunning) {
                                lastRunning.duration = evt.duration_ms;
                                if (evt.error) {
                                    lastRunning.state = 'error';
                                    lastRunning.error = evt.error;
                                    deps.terminalLog.push(`❌ ${evt.error}`);
                                } else {
                                    lastRunning.state = 'completed';
                                    lastRunning.output = evt.output || '';
                                    deps.terminalLog.push(`✅ done${evt.duration_ms != null ? ` (${evt.duration_ms}ms)` : ''}`);

                                    // F5: MCP App UI rendering
                                    if (deps.hasMcpAppUI(evt)) {
                                        const msgContainer = document.getElementById('cw-messages');
                                        if (msgContainer) {
                                            deps.renderMcpApp(msgContainer, evt.ui_html as string, {
                                                toolName: evt.name || 'tool',
                                                onOpenLink: (url) => window.open(url, '_blank', 'noopener'),
                                            });
                                        }
                                    }
                                }
                            }
                            updateDisplay(buildToolDisplay(toolStatuses));
                            deps.updateTerminalTab();
                            break;
                        }
                        case 'approval_required': {
                            const { request_id, name: toolName, args: toolArgs, diff: diffText } = evt;
                            toolStatuses.push({
                                name: toolName,
                                args: toolArgs || {},
                                state: 'approval_required',
                                startedAt: Date.now(),
                                requestId: request_id,
                            });
                            updateDisplay(buildToolDisplay(toolStatuses));
                            deps.showApprovalUI(request_id, toolName, toolArgs || {}, diffText || null);
                            break;
                        }
                        case 'chunk':
                            finalText = evt.text || '';
                            updateDisplay((buildToolDisplay(toolStatuses) ? buildToolDisplay(toolStatuses) + '\n\n' : '') + finalText);
                            break;
                        case 'thinking':
                            isThinkingActive = true;
                            thinkingText += evt.text || '';
                            updateDisplay((buildToolDisplay(toolStatuses) ? buildToolDisplay(toolStatuses) + '\n\n' : '') + finalText);
                            break;
                        case 'done': {
                            isThinkingActive = false;
                            const tokens = evt.token_usage?.total_tokens;
                            let content = finalText || '(応答なし)';
                            if (toolStatuses.length > 0) {
                                const logMd = buildToolDisplay(toolStatuses);
                                content += `\n\n<details><summary>🔧 ツール実行ログ${tokens ? ` | ${tokens} tokens` : ''}</summary>\n\n${logMd}\n\n</details>`;
                            } else if (tokens) {
                                content += `\n\n---\n*🔧 Agent mode | ${tokens} tokens*`;
                            }
                            updateDisplay(content);
                            break;
                        }
                        case 'error':
                            throw new Error(evt.error || 'Agent error');
                        default: break;
                    }
                } catch (e) {
                    if (e instanceof Error && e.message !== 'Agent error' && !e.message.startsWith('Agent')) { /* skip */ }
                    else throw e;
                }
            }
            boundary = buffer.indexOf('\n\n');
        }
    }

    deps.saveAllConversations();
    deps.renderMessages();
    return finalText;
}

// ─── Colony SSE Reader ───────────────────────────────────────

/** Colony モード SSE リーダー */
export async function readColonySSEStream(response: Response, assistantMsg: ChatMessage, deps: StreamingDeps): Promise<string> {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    const log: string[] = [];
    let synthesisText = '';

    if (!reader) { assistantMsg.content = '(ストリーム取得失敗)'; deps.renderMessages(); return ''; }

    function updateDisplay(content: string): void {
        assistantMsg.content = content;
        updateLastMessage(content);
    }

    let buffer = '';
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        recordSSEEvent();
        let boundary = buffer.indexOf('\n\n');
        while (boundary !== -1) {
            const block = buffer.slice(0, boundary).trim();
            buffer = buffer.slice(boundary + 2);

            if (block.startsWith('data: ')) {
                try {
                    const evt = JSON.parse(block.slice(6));
                    switch (evt.type) {
                        case 'phase':
                            log.push(`\n**📍 Phase: ${evt.phase}**`);
                            updateDisplay(log.join('\n'));
                            break;
                        case 'decompose': {
                            log.push('\n**🧠 COO タスク分解:**');
                            for (const st of evt.subtasks || []) {
                                const icon = st.worker_type === 'engineer' ? '⚙️'
                                    : st.worker_type === 'researcher' ? '🔬'
                                        : st.worker_type === 'jules' ? '💻'
                                            : '🧠';
                                log.push(`- ${icon} **${st.id}** (${st.worker_type}): ${st.description.slice(0, 80)}`);
                            }
                            updateDisplay(log.join('\n'));
                            break;
                        }
                        case 'worker_start':
                            log.push(`\n⏳ **${evt.task_id}** (${evt.worker_type}) 実行中...`);
                            updateDisplay(log.join('\n'));
                            break;
                        case 'worker_done': {
                            const status = evt.success ? '✅' : '❌';
                            log.push(`${status} **${evt.task_id}** 完了 (${evt.duration_ms}ms)`);
                            if (evt.output_preview) log.push(`  > ${evt.output_preview.slice(0, 120)}...`);
                            updateDisplay(log.join('\n'));
                            break;
                        }
                        case 'thinking':
                            log.push(`\n<details><summary>💭 COO 思考過程</summary>\n\n${evt.text}\n\n</details>`);
                            break;
                        case 'synthesis':
                            synthesisText = evt.text || '';
                            break;
                        case 'done': {
                            let content = synthesisText || '(統合回答なし)';
                            if (log.length > 0) {
                                const logMd = log.join('\n');
                                content += `\n\n<details><summary>🏛️ Colony 実行ログ | ${evt.total_duration_ms}ms | COO: ${evt.coo_model}</summary>\n\n${logMd}\n\n</details>`;
                            }
                            updateDisplay(content);
                            break;
                        }
                        case 'error':
                            throw new Error(evt.error || 'Colony error');
                        default: break;
                    }
                } catch (e) {
                    if (e instanceof Error && !e.message.startsWith('Colony')) { /* skip parse errors */ }
                    else throw e;
                }
            }
            boundary = buffer.indexOf('\n\n');
        }
    }

    deps.saveAllConversations();
    deps.renderMessages();
    return synthesisText;
}

// ─── SSE timeout wrapper ─────────────────────────────────────

/**
 * SSE ストリーミング実行のラッパー。
 * Safety Timeout の開始/停止を自動化する。
 */
export async function withSSETimeout<T>(
    assistantMsg: ChatMessage,
    reader: (deps: StreamingDeps) => Promise<T>,
    deps: StreamingDeps,
): Promise<T> {
    recordSSEEvent();
    startSSETimeout(() => {
        bumpEpoch("SSE timeout");
        assistantMsg.content += "\n\n⚠️ SSE タイムアウト (60秒)";
        deps.renderMessages();
    });
    try {
        return await reader(deps);
    } finally {
        clearSSETimeout();
        clearErrorRecovery();
    }
}
