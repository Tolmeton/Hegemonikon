import './css/devtools.css';
import { marked } from 'marked';
import { enhanceMarkdown } from './enhance';
import { api } from '../api/client';

// ─── Types ───────────────────────────────────────────────────

interface FileEntry {
    name: string;
    path: string;
    is_dir: boolean;
    size?: number;
    children?: number;
}

interface TerminalLine {
    type: 'input' | 'output' | 'error';
    text: string;
    timestamp: Date;
}

// ─── State ───────────────────────────────────────────────────

let currentPath = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon';
let pathHistory: string[] = [currentPath];
let openFilePath = '';
let openFileContent = '';
let terminalHistory: TerminalLine[] = [];
let cmdHistory: string[] = [];
let cmdHistoryIdx = -1;
let aiConversation: { role: 'user' | 'ai'; text: string }[] = [];
let searchQuery = '';
let searchResults: { file: string; line: number; content: string }[] | null = null;
let searchInProgress = false;
let aiModel = 'gemini-3.1-pro-preview';  // DevTools AI default model

const DEV_MODELS: { id: string; label: string }[] = [
    { id: 'gemini-3.1-pro-preview', label: '💎 Gemini 3.1 Pro' },
    { id: 'claude-opus-4-6', label: '◆ Claude Opus 4.6' },
    { id: 'claude-sonnet-4-6', label: '✦ Claude Sonnet 4.6' },
];
// Active tab tracked by DOM state (dt-tab-active class)

// ─── API Calls (client.ts 経由 — Tauri IPC 統一) ─────────────

async function apiListDir(path: string): Promise<FileEntry[]> {
    try {
        const data = await api.filesList(path);
        return (data as any).entries || [];
    } catch {
        return [];
    }
}

async function apiReadFile(path: string): Promise<string> {
    try {
        const data = await api.filesRead(path);
        return (data as any).content || '';
    } catch {
        return '(ファイル読み込み失敗)';
    }
}

async function apiRunCommand(cmd: string, cwd: string): Promise<string> {
    try {
        const data = await api.terminalExecute(cmd, cwd);
        return (data as any).output || (data as any).stdout || '';
    } catch {
        return '(コマンド実行失敗)';
    }
}

// ─── SSE Streaming via /api/ask/stream (Cortex API 直通) ────

async function streamAskSSE(
    message: string,
    model: string,
    onChunk: (text: string) => void,
): Promise<string> {
    const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message,
            model,
            system_instruction: 'あなたは Hegemonikón の開発アシスタントです。日本語で応答。ツールを使ってファイル読み書き・コマンド実行が可能です。',
            temperature: 0.7,
            max_tokens: 8192,
        }),
    });
    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`API Error ${response.status}: ${errText}`);
    }
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    if (reader) {
        let buffer = '';
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
                        if (data.text) {
                            fullText += data.text;
                            onChunk(fullText);
                        }
                    } catch { /* skip malformed */ }
                }
                boundary = buffer.indexOf('\n\n');
            }
        }
    }
    return fullText || '(応答なし)';
}

// ─── Helpers ─────────────────────────────────────────────────

function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function fileIcon(entry: FileEntry): string {
    if (entry.is_dir) return '📁';
    const ext = entry.name.split('.').pop()?.toLowerCase() || '';
    const icons: Record<string, string> = {
        py: '🐍', ts: '📘', js: '📒', json: '📋', md: '📝',
        yaml: '⚙️', yml: '⚙️', css: '🎨', html: '🌐',
        sh: '💻', toml: '📦', txt: '📄', rs: '🦀',
    };
    return icons[ext] || '📄';
}

function formatSize(bytes?: number): string {
    if (bytes === undefined || bytes === null) return '';
    if (bytes === 0) return '0B';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}M`;
}

function basename(path: string): string {
    return path.split('/').filter(Boolean).pop() || '/';
}

function normalizePath(p: string): string {
    const parts = p.split('/').filter(Boolean);
    const out: string[] = [];
    for (const seg of parts) {
        if (seg === '..') out.pop();
        else if (seg !== '.') out.push(seg);
    }
    return '/' + out.join('/');
}

const HOME_DIR = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon';
let prevCwd = HOME_DIR;

const BINARY_EXTS = new Set([
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'webp', 'svg',
    'woff', 'woff2', 'ttf', 'eot', 'otf',
    'zip', 'gz', 'tar', 'bz2', 'xz', '7z',
    'pdf', 'doc', 'docx', 'xls', 'xlsx',
    'mp3', 'mp4', 'wav', 'avi', 'mov',
    'pyc', 'pyo', 'so', 'dll', 'exe', 'bin',
]);

function isBinary(name: string): boolean {
    const ext = name.split('.').pop()?.toLowerCase() || '';
    return BINARY_EXTS.has(ext);
}

const MAX_DISPLAY_LINES = 5000;

// ─── Render: File Explorer ───────────────────────────────────

async function renderFileTree(): Promise<void> {
    const panel = document.getElementById('dt-file-panel');
    if (!panel) return;

    panel.innerHTML = '<div class="dt-loading">📂 読み込み中...</div>';
    const entries = await apiListDir(currentPath);

    // Sort: dirs first, then by name
    entries.sort((a, b) => {
        if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
        return a.name.localeCompare(b.name);
    });

    // Breadcrumb
    const parts = currentPath.split('/').filter(Boolean);
    const breadcrumb = parts.map((p, i) => {
        const fullPath = '/' + parts.slice(0, i + 1).join('/');
        return `<span class="dt-breadcrumb-item" data-path="${fullPath}">${esc(p)}</span>`;
    }).join('<span class="dt-breadcrumb-sep">/</span>');

    // Build search results HTML or file list
    let listHTML: string;
    if (searchResults !== null) {
        if (searchResults.length === 0) {
            listHTML = '<div class="dt-empty">検索結果なし</div>';
        } else {
            listHTML = searchResults.map(r => {
                const fname = r.file.split('/').pop() || r.file;
                const linePreview = r.content.trim().slice(0, 80);
                return `
                    <div class="dt-file-entry dt-search-result" data-path="${esc(r.file)}" data-line="${r.line}">
                        <span class="dt-file-icon">🔍</span>
                        <span class="dt-file-name">${esc(fname)}:${r.line}</span>
                        <span class="dt-file-meta dt-search-preview">${esc(linePreview)}</span>
                    </div>`;
            }).join('');
        }
    } else {
        listHTML = entries.length === 0 ? '<div class="dt-empty">空のディレクトリ</div>' :
            entries.map(e => `
                <div class="dt-file-entry ${e.is_dir ? 'dt-dir' : 'dt-file'} ${currentPath + '/' + e.name === openFilePath ? 'dt-file-active' : ''}"
                     data-path="${esc(currentPath + '/' + e.name)}" data-is-dir="${e.is_dir}">
                    <span class="dt-file-icon">${fileIcon(e)}</span>
                    <span class="dt-file-name">${esc(e.name)}</span>
                    <span class="dt-file-meta">${e.is_dir ? '' : formatSize(e.size)}</span>
                </div>
            `).join('');
    }

    panel.innerHTML = `
        <div class="dt-breadcrumb">
            <span class="dt-breadcrumb-item" data-path="/">🏠</span>
            <span class="dt-breadcrumb-sep">/</span>
            ${breadcrumb}
        </div>
        <div class="dt-search-bar">
            <input type="text" id="dt-search-input" placeholder="🔍 ファイル内検索 (Enter で実行)" value="${esc(searchQuery)}" />
            ${searchResults !== null ? '<button id="dt-search-clear" title="検索クリア">✕</button>' : ''}
        </div>
        <div class="dt-file-list">
            ${searchInProgress ? '<div class="dt-loading">🔍 検索中...</div>' : listHTML}
        </div>
    `;

    // Bind events
    panel.querySelectorAll('.dt-file-entry').forEach(el => {
        el.addEventListener('click', () => {
            const path = (el as HTMLElement).dataset.path || '';
            const isDir = (el as HTMLElement).dataset.isDir === 'true';
            if (isDir) {
                currentPath = path;
                pathHistory.push(path);
                void renderFileTree();
            } else {
                void openFile(path);
            }
        });
    });

    panel.querySelectorAll('.dt-breadcrumb-item').forEach(el => {
        el.addEventListener('click', () => {
            const path = (el as HTMLElement).dataset.path || '/';
            currentPath = path;
            pathHistory.push(path);
            searchResults = null;
            searchQuery = '';
            void renderFileTree();
        });
    });

    // Search bar events
    const searchInput = document.getElementById('dt-search-input') as HTMLInputElement;
    if (searchInput) {
        searchInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter' && searchInput.value.trim()) {
                searchQuery = searchInput.value.trim();
                searchInProgress = true;
                searchResults = [];
                void renderFileTree();
                try {
                    const data = await api.filesSearch(searchQuery, currentPath);
                    searchResults = (data as any).matches || [];
                } catch {
                    searchResults = [];
                }
                searchInProgress = false;
                void renderFileTree();
            }
            if (e.key === 'Escape') {
                searchResults = null;
                searchQuery = '';
                void renderFileTree();
            }
        });
    }

    document.getElementById('dt-search-clear')?.addEventListener('click', () => {
        searchResults = null;
        searchQuery = '';
        void renderFileTree();
    });

    // Search result click
    panel.querySelectorAll('.dt-search-result').forEach(el => {
        el.addEventListener('click', () => {
            const path = (el as HTMLElement).dataset.path || '';
            void openFile(path);
        });
    });
}

// ─── Render: Code Viewer ─────────────────────────────────────

async function openFile(path: string): Promise<void> {
    openFilePath = path;
    const viewer = document.getElementById('dt-code-viewer');
    if (!viewer) return;

    const name = basename(path);

    // Binary file check
    if (isBinary(name)) {
        const ext = name.split('.').pop()?.toLowerCase() || '';
        const isImage = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico'].includes(ext);
        viewer.innerHTML = `
            <div class="dt-viewer-header">
                <span class="dt-viewer-filename">${fileIcon({ name, path, is_dir: false })} ${esc(name)}</span>
                <span class="dt-viewer-path">${esc(path)}</span>
                <span class="dt-viewer-info">${isImage ? '画像ファイル' : 'バイナリファイル'}</span>
            </div>
            <div class="dt-viewer-empty">
                <div style="font-size:3rem">${isImage ? '🖼️' : '📦'}</div>
                <div style="font-weight:600;margin-top:0.5rem">${isImage ? '画像プレビュー未対応' : 'バイナリファイル'}</div>
                <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem">
                    このファイルはテキストとして表示できません
                </div>
            </div>
        `;
        document.querySelectorAll('.dt-file-entry').forEach(el => {
            el.classList.toggle('dt-file-active', (el as HTMLElement).dataset.path === path);
        });
        return;
    }

    viewer.innerHTML = `<div class="dt-loading">📖 ${esc(name)} を読み込み中...</div>`;
    openFileContent = await apiReadFile(path);

    let isEditing = false;

    const renderViewer = () => {
        const allLines = openFileContent.split('\n');
        const truncated = allLines.length > MAX_DISPLAY_LINES;
        const lines = truncated && !isEditing ? allLines.slice(0, MAX_DISPLAY_LINES) : allLines;
        const lineNums = lines.map((_, i) => `<span>${i + 1}</span>`).join('\n');
        const code = lines.map(l => esc(l)).join('\n');

        const truncMsg = truncated && !isEditing
            ? `<div class="dt-truncation-notice">⚠️ ${allLines.length} 行中 ${MAX_DISPLAY_LINES} 行を表示</div>`
            : '';

        const headerBtns = isEditing
            ? `<button class="btn btn-sm btn-success dt-save-btn">保存</button>
               <button class="btn btn-sm btn-outline dt-cancel-btn">キャンセル</button>`
            : `<button class="btn btn-sm btn-outline dt-edit-btn" title="編集">✏️</button>
               <button class="btn btn-sm btn-outline dt-copy-btn" title="コピー">📋</button>`;

        const contentArea = isEditing
            ? `<textarea class="dt-code-edit" spellcheck="false" style="width:100%;height:100%;box-sizing:border-box;background:var(--bg-secondary);color:var(--text-color);font-family:monospace;border:none;padding:1rem;resize:none;">${esc(openFileContent)}</textarea>`
            : `<div class="dt-code-container">
                   <pre class="dt-line-numbers">${lineNums}</pre>
                   <pre class="dt-code"><code>${code}</code></pre>
               </div>`;

        viewer.innerHTML = `
            <div class="dt-viewer-header">
                <span class="dt-viewer-filename">${fileIcon({ name, path, is_dir: false })} ${esc(name)}</span>
                <span class="dt-viewer-path">${esc(path)}</span>
                <span class="dt-viewer-info" id="dt-file-info-span">${allLines.length} 行 | ${formatSize(openFileContent.length)}</span>
                <div style="display:flex;gap:0.5rem">
                    ${headerBtns}
                </div>
            </div>
            ${truncMsg}
            <!-- Use flex-grow so textarea fills available space nicely -->
            <div style="flex:1; overflow:hidden; display:flex; flex-direction:column;">
                ${contentArea}
            </div>
        `;

        if (isEditing) {
            const textarea = viewer.querySelector('.dt-code-edit') as HTMLTextAreaElement;
            textarea?.focus();

            viewer.querySelector('.dt-cancel-btn')?.addEventListener('click', () => {
                isEditing = false;
                renderViewer();
            });

            viewer.querySelector('.dt-save-btn')?.addEventListener('click', async () => {
                const btn = viewer.querySelector('.dt-save-btn') as HTMLButtonElement;
                if (!btn) return;
                btn.disabled = true;
                btn.textContent = '保存中...';
                try {
                    const newContent = textarea.value;
                    await api.filesWrite(path, newContent);
                    openFileContent = newContent;
                    btn.textContent = '保存完了';
                    setTimeout(() => {
                        isEditing = false;
                        void openFile(path); // fully reload
                    }, 1000);
                } catch (e: any) {
                    btn.disabled = false;
                    btn.textContent = '❌ 失敗';
                    const infoSpan = document.getElementById('dt-file-info-span');
                    if (infoSpan) {
                        infoSpan.textContent = `保存エラー: ${e.message}`;
                        infoSpan.style.color = 'var(--text-error)';
                    }
                    setTimeout(() => { btn.textContent = '保存'; }, 2000);
                }
            });
        } else {
            viewer.querySelector('.dt-copy-btn')?.addEventListener('click', () => {
                void navigator.clipboard.writeText(openFileContent).then(() => {
                    const btn = viewer.querySelector('.dt-copy-btn')!;
                    btn.textContent = '✓';
                    setTimeout(() => { btn.textContent = '📋'; }, 1500);
                });
            });

            viewer.querySelector('.dt-edit-btn')?.addEventListener('click', () => {
                if (truncated) {
                    alert('ファイルが大きすぎるため、DevTools での編集はサポートされていません。');
                    return;
                }
                isEditing = true;
                renderViewer();
            });

            // Sync scroll between line numbers and code
            const codeEl = viewer.querySelector('.dt-code');
            const numsEl = viewer.querySelector('.dt-line-numbers');
            if (codeEl && numsEl) {
                codeEl.addEventListener('scroll', () => {
                    numsEl.scrollTop = codeEl.scrollTop;
                });
            }
        }
    };

    renderViewer();

    // Highlight active file in list
    document.querySelectorAll('.dt-file-entry').forEach(el => {
        el.classList.toggle('dt-file-active', (el as HTMLElement).dataset.path === path);
    });
}

// ─── Render: Terminal ────────────────────────────────────────

function renderTerminal(): void {
    const panel = document.getElementById('dt-terminal-panel');
    if (!panel) return;

    panel.innerHTML = `
        <div class="dt-term-output" id="dt-term-output">
            ${terminalHistory.length === 0
            ? '<div class="dt-term-welcome">💻 ターミナル — コマンドを入力して Enter<br><span style="color:var(--text-secondary)">cwd: ${esc(currentPath)}</span></div>'
            : terminalHistory.map(l => `<div class="dt-term-line dt-term-${l.type}">${l.type === 'input' ? '<span class="dt-term-prompt">$ </span>' : ''}${esc(l.text)}</div>`).join('')
        }
        </div>
        <div class="dt-term-input-area">
            <span class="dt-term-prompt-icon">$</span>
            <textarea id="dt-term-input" class="dt-term-input" placeholder="コマンドを入力... (Enter で送信、Shift+Enter で改行)" rows="1"></textarea>
        </div>
    `;

    const input = document.getElementById('dt-term-input') as HTMLTextAreaElement;
    const output = document.getElementById('dt-term-output')!;
    output.scrollTop = output.scrollHeight;
    const autoResizeTermInput = () => {
        input.style.height = 'auto';
        input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
    };
    autoResizeTermInput();
    input?.addEventListener('input', autoResizeTermInput);

    input?.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            const cmd = input.value.trim();
            if (!cmd) return;
            input.value = '';
            autoResizeTermInput();
            cmdHistory.unshift(cmd);
            cmdHistoryIdx = -1;

            // Handle cd
            if (cmd === 'cd' || cmd.startsWith('cd ')) {
                const target = cmd === 'cd' ? '~' : cmd.slice(3).trim();
                let newCwd: string;
                if (target === '~' || target === '') {
                    newCwd = HOME_DIR;
                } else if (target === '-') {
                    newCwd = prevCwd;
                } else if (target.startsWith('/')) {
                    newCwd = target;
                } else if (target.startsWith('~')) {
                    newCwd = HOME_DIR + target.slice(1);
                } else {
                    newCwd = currentPath + '/' + target;
                }
                newCwd = normalizePath(newCwd);
                prevCwd = currentPath;
                currentPath = newCwd;
                terminalHistory.push({ type: 'input', text: cmd, timestamp: new Date() });
                terminalHistory.push({ type: 'output', text: `cd → ${currentPath}`, timestamp: new Date() });
                renderTerminal();
                void renderFileTree();
                return;
            }

            // Handle clear
            if (cmd === 'clear') {
                terminalHistory = [];
                renderTerminal();
                return;
            }

            terminalHistory.push({ type: 'input', text: cmd, timestamp: new Date() });
            renderTerminal();

            const result = await apiRunCommand(cmd, currentPath);
            if (result.trim()) {
                terminalHistory.push({ type: 'output', text: result, timestamp: new Date() });
            } else {
                terminalHistory.push({ type: 'output', text: '(完了 — 出力なし)', timestamp: new Date() });
            }
            renderTerminal();
            document.getElementById('dt-term-input')?.focus();
        } else if (e.key === 'ArrowUp') {
            if (input.value.includes('\n') || input.selectionStart !== 0 || input.selectionEnd !== 0) return;
            e.preventDefault();
            if (cmdHistoryIdx < cmdHistory.length - 1) {
                cmdHistoryIdx++;
                input.value = cmdHistory[cmdHistoryIdx] ?? '';
                autoResizeTermInput();
            }
        } else if (e.key === 'ArrowDown') {
            if (input.value.includes('\n') || input.selectionStart !== input.value.length || input.selectionEnd !== input.value.length) return;
            e.preventDefault();
            if (cmdHistoryIdx > 0) {
                cmdHistoryIdx--;
                input.value = cmdHistory[cmdHistoryIdx] ?? '';
            } else {
                cmdHistoryIdx = -1;
                input.value = '';
            }
            autoResizeTermInput();
        }
    });

    input?.focus();
}

// ─── Render: AI Assistant ────────────────────────────────────

function renderAI(): void {
    const panel = document.getElementById('dt-ai-panel');
    if (!panel) return;

    const modelOptions = DEV_MODELS.map(m =>
        `<option value="${m.id}" ${m.id === aiModel ? 'selected' : ''}>${esc(m.label)}</option>`
    ).join('');

    panel.innerHTML = `
        <div class="dt-ai-header">
            <select id="dt-ai-model" class="dt-ai-model-select">${modelOptions}</select>
        </div>
        <div class="dt-ai-messages" id="dt-ai-messages">
            ${aiConversation.length === 0
            ? `<div class="dt-ai-welcome">
                    <div style="font-size:2rem">🤖</div>
                    <div style="font-weight:600">AI アシスタント</div>
                    <div style="color:var(--text-secondary);font-size:0.85rem">Cortex API (SSE Streaming) — ${esc(DEV_MODELS.find(m => m.id === aiModel)?.label ?? aiModel)}</div>
                    <div class="dt-ai-hints">
                        <span class="dt-ai-hint">ochema のテストを実行して</span>
                        <span class="dt-ai-hint">tools.py の構造を教えて</span>
                        <span class="dt-ai-hint">最新の git log を見せて</span>
                    </div>
                </div>`
            : aiConversation.map(m => `
                <div class="dt-ai-msg dt-ai-msg-${m.role}">
                    <div class="dt-ai-msg-role">${m.role === 'user' ? '👤' : '🤖'}</div>
                    <div class="dt-ai-msg-body">${m.role === 'user' ? esc(m.text) : (marked.parse(m.text) as string)}</div>
                </div>
            `).join('')
        }
        </div>
        <div class="dt-ai-input-area">
            <textarea id="dt-ai-input" class="dt-ai-input" placeholder="AI に指示... (Enter で送信、Shift+Enter で改行)" rows="1"></textarea>
            <button id="dt-ai-send" class="btn dt-ai-send-btn">送信</button>
        </div>
    `;

    // Model selector
    const modelSelect = document.getElementById('dt-ai-model') as HTMLSelectElement;
    modelSelect?.addEventListener('change', () => {
        aiModel = modelSelect.value;
    });

    const msgContainer = document.getElementById('dt-ai-messages')!;
    msgContainer.scrollTop = msgContainer.scrollHeight;

    const input = document.getElementById('dt-ai-input') as HTMLTextAreaElement;
    const sendBtn = document.getElementById('dt-ai-send')!;

    const send = async () => {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        input.style.height = 'auto';

        aiConversation.push({ role: 'user', text });
        aiConversation.push({ role: 'ai', text: '' });
        renderAI();

        try {
            const result = await streamAskSSE(text, aiModel, (fullText: string) => {
                // Incremental update of last AI message
                const last = aiConversation[aiConversation.length - 1];
                if (last) last.text = fullText;
                const msgBodies = document.querySelectorAll('.dt-ai-msg-body');
                const lastBody = msgBodies[msgBodies.length - 1];
                if (lastBody) {
                    lastBody.innerHTML = marked.parse(fullText) as string;
                    enhanceMarkdown(lastBody as HTMLElement);
                    const container = document.getElementById('dt-ai-messages');
                    if (container) container.scrollTop = container.scrollHeight;
                }
            });
            const last = aiConversation[aiConversation.length - 1];
            if (last) last.text = result;
        } catch (e) {
            const last = aiConversation[aiConversation.length - 1];
            if (last) last.text = `エラー: ${(e as Error).message}`;
        }
        renderAI();
        // Enhance code blocks in AI messages
        const msgContainer2 = document.getElementById('dt-ai-messages');
        if (msgContainer2) enhanceMarkdown(msgContainer2);
    };

    input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            void send();
        }
    });
    input?.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    });
    sendBtn?.addEventListener('click', () => void send());

    // Hint clicks
    panel.querySelectorAll('.dt-ai-hint').forEach(hint => {
        hint.addEventListener('click', () => {
            if (input) {
                input.value = hint.textContent ?? '';
                void send();
            }
        });
    });

    input?.focus();
}

// ─── Render: IDE ConnectRPC ───────────────────────────────────

async function renderConnect(): Promise<void> {
    const panel = document.getElementById('dt-connect-panel');
    if (!panel) return;

    panel.innerHTML = '<div class="dt-loading">🔌 IDE ステータス取得中...</div>';

    try {
        const status = await api.ideStatus();
        if (status.status !== 'connected') {
            panel.innerHTML = `
                <div style="padding:2rem;">
                    <h3 style="color:var(--text-error)">❌ IDE に接続できません</h3>
                    <p style="color:var(--text-secondary);margin-top:0.5rem">${esc(status.error || '不明なエラー')}</p>
                    <button class="btn" style="margin-top:1rem" id="dt-connect-retry">再試行</button>
                </div>
            `;
            document.getElementById('dt-connect-retry')?.addEventListener('click', () => void renderConnect());
            return;
        }

        panel.innerHTML = `
            <div style="padding:1rem; border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0;color:var(--text-success)">🟢 IDE Connected</h3>
                <span style="font-size:0.85rem;color:var(--text-secondary)">PID: ${status.pid} | Port: ${status.port}</span>
            </div>
            <div style="padding:1rem; display:flex; flex-direction:column; gap:1rem; overflow-y:auto;">
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <h4 style="margin:0">Workflows</h4>
                        <button class="btn btn-sm" id="btn-ide-workflows">取得</button>
                    </div>
                    <pre id="ide-workflows-out" style="max-height:250px; overflow-y:auto; background:var(--bg-secondary); padding:0.5rem; border-radius:4px; font-size:0.8rem; border:1px solid var(--border-color);"></pre>
                </div>
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <h4 style="margin:0">User Memories</h4>
                        <button class="btn btn-sm" id="btn-ide-memories">取得</button>
                    </div>
                    <pre id="ide-memories-out" style="max-height:250px; overflow-y:auto; background:var(--bg-secondary); padding:0.5rem; border-radius:4px; font-size:0.8rem; border:1px solid var(--border-color);"></pre>
                </div>
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <h4 style="margin:0">Trajectories</h4>
                        <button class="btn btn-sm" id="btn-ide-trajectories">取得</button>
                    </div>
                    <pre id="ide-trajectories-out" style="max-height:250px; overflow-y:auto; background:var(--bg-secondary); padding:0.5rem; border-radius:4px; font-size:0.8rem; border:1px solid var(--border-color);"></pre>
                </div>
            </div>
        `;

        const bindBtn = (btnId: string, outId: string, fetcher: () => Promise<any>) => {
            document.getElementById(btnId)?.addEventListener('click', async () => {
                const out = document.getElementById(outId)!;
                out.textContent = '読み込み中...';
                try {
                    const res = await fetcher();
                    out.textContent = JSON.stringify(res, null, 2);
                } catch (e) { out.textContent = String(e); }
            });
        };

        bindBtn('btn-ide-workflows', 'ide-workflows-out', api.ideWorkflows);
        bindBtn('btn-ide-memories', 'ide-memories-out', api.ideMemories);
        bindBtn('btn-ide-trajectories', 'ide-trajectories-out', api.ideTrajectories);

    } catch (e) {
        panel.innerHTML = `<div style="padding:2rem;"><h3 style="color:var(--text-error)">❌ エラー</h3><p>${esc((e as Error).message)}</p></div>`;
    }
}

// ─── Tab Switching ───────────────────────────────────────────

function switchTab(tab: 'files' | 'terminal' | 'ai' | 'connect'): void {
    document.querySelectorAll('.dt-tab').forEach(t =>
        t.classList.toggle('dt-tab-active', (t as HTMLElement).dataset.tab === tab)
    );

    const panelIds = ['dt-file-panel', 'dt-terminal-panel', 'dt-ai-panel', 'dt-connect-panel'];
    panelIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    const panelId = `dt-${tab === 'files' ? 'file' : tab}-panel`;
    const activePanel = document.getElementById(panelId);
    if (activePanel) {
        activePanel.style.display = 'flex';
        if (tab === 'connect') activePanel.style.flexDirection = 'column';
    }

    if (tab === 'terminal') renderTerminal();
    if (tab === 'ai') renderAI();
    if (tab === 'connect') void renderConnect();
}

// ─── Main Render ─────────────────────────────────────────────

export async function mountDevTools(container: HTMLElement): Promise<void> {
    container.innerHTML = `
        <div class="dt-container">
            <div class="dt-sidebar">
                <div class="dt-tabs">
                    <button class="dt-tab dt-tab-active" data-tab="files">📁 Files</button>
                    <button class="dt-tab" data-tab="terminal">💻 Terminal</button>
                    <button class="dt-tab" data-tab="ai">🤖 AI</button>
                    <button class="dt-tab" data-tab="connect">🔌 IDE</button>
                </div>
                <div id="dt-file-panel" class="dt-panel" style="display:flex"></div>
                <div id="dt-terminal-panel" class="dt-panel" style="display:none"></div>
                <div id="dt-ai-panel" class="dt-panel" style="display:none"></div>
                <div id="dt-connect-panel" class="dt-panel" style="display:none; flex-direction:column; overflow:hidden;"></div>
            </div>
            <div class="dt-main">
                <div id="dt-code-viewer" class="dt-code-viewer">
                    <div class="dt-viewer-empty">
                        <div style="font-size:3rem">📝</div>
                        <div style="font-weight:600;margin-top:0.5rem">DevTools</div>
                        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem">
                            ファイルを選択して表示<br>
                            Ctrl+\` でターミナル | Ctrl+I で AI
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Tab events
    container.querySelectorAll('.dt-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab((tab as HTMLElement).dataset.tab as 'files' | 'terminal' | 'ai' | 'connect');
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e: KeyboardEvent) => {
        const target = e.target as HTMLElement;
        if (target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA') return;
        if (e.ctrlKey && e.key === '\`') {
            e.preventDefault();
            switchTab('terminal');
        }
        if (e.ctrlKey && e.key === 'i') {
            e.preventDefault();
            switchTab('ai');
        }
    });

    // Load file tree
    await renderFileTree();
}

export async function renderDevToolsView(): Promise<void> {
    const app = document.getElementById('view-content');
    if (!app) return;
    await mountDevTools(app);
}
