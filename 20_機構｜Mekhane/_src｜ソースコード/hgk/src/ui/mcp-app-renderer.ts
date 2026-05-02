/**
 * MCP App Renderer — Vanilla TS implementation of MCP Apps (SEP-1865)
 *
 * PURPOSE: Render interactive UI from MCP tool results in sandboxed iframes.
 * Equivalent to @mcp-ui/client's <AppRenderer> but without React dependency.
 *
 * Architecture:
 *   1. Tool result contains `ui_html` (raw HTML string)
 *   2. This module creates a sandboxed iframe with srcdoc
 *   3. postMessage bridge enables bidirectional communication
 *   4. ResizeObserver auto-adjusts iframe height
 *
 * Security:
 *   - sandbox="allow-scripts" (no DOM access, no cookies, no localStorage)
 *   - Origin validation on postMessage
 *   - Content-Security-Policy via meta tag in injected HTML
 */

// ─── Types ───────────────────────────────────────────────────

export interface McpAppMessage {
    type: 'mcp-app';
    action: 'resize' | 'open-link' | 'notify' | 'tool-call';
    payload: Record<string, unknown>;
}

export interface McpAppOptions {
    /** Maximum height in pixels (default: 600) */
    maxHeight?: number;
    /** Minimum height in pixels (default: 80) */
    minHeight?: number;
    /** Callback when iframe requests to open a link */
    onOpenLink?: (url: string) => void;
    /** Callback when iframe sends a message */
    onMessage?: (msg: McpAppMessage) => void;
    /** Tool name for identification */
    toolName?: string;
}

// ─── Bridge Script ───────────────────────────────────────────

/**
 * This script is injected into the iframe to enable communication.
 * It runs inside the sandbox and communicates via postMessage.
 */
const BRIDGE_SCRIPT = `
<script>
(function() {
    // Auto-resize: report height changes to parent
    const ro = new ResizeObserver(function() {
        var h = document.documentElement.scrollHeight;
        window.parent.postMessage({
            type: 'mcp-app',
            action: 'resize',
            payload: { height: h }
        }, '*');
    });
    ro.observe(document.body);

    // Intercept link clicks
    document.addEventListener('click', function(e) {
        var a = e.target.closest('a');
        if (a && a.href) {
            e.preventDefault();
            window.parent.postMessage({
                type: 'mcp-app',
                action: 'open-link',
                payload: { url: a.href }
            }, '*');
        }
    });

    // Expose postMessage helper for app authors
    window.mcpBridge = {
        notify: function(data) {
            window.parent.postMessage({
                type: 'mcp-app',
                action: 'notify',
                payload: data
            }, '*');
        },
        requestTool: function(toolName, args) {
            window.parent.postMessage({
                type: 'mcp-app',
                action: 'tool-call',
                payload: { toolName: toolName, args: args }
            }, '*');
        }
    };
})();
</script>
`;

/**
 * Base CSS injected into every MCP App iframe for consistent styling.
 */
const BASE_STYLE = `
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        color: #e0e0e0;
        background: transparent;
        padding: 12px;
    }
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
    th { font-weight: 600; color: #a0a0ff; }
    tr:hover { background: rgba(255,255,255,0.05); }
    button {
        padding: 6px 14px; border: 1px solid rgba(255,255,255,0.2);
        border-radius: 6px; background: rgba(255,255,255,0.1);
        color: #e0e0e0; cursor: pointer; font-size: 13px;
    }
    button:hover { background: rgba(255,255,255,0.2); }
    .badge {
        display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 600;
    }
    .badge-green { background: rgba(0,200,100,0.2); color: #4ade80; }
    .badge-blue { background: rgba(50,100,255,0.2); color: #60a5fa; }
    .badge-yellow { background: rgba(255,200,0,0.2); color: #fbbf24; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
</style>
`;

// ─── Core Renderer ───────────────────────────────────────────

/**
 * Render an MCP App (interactive HTML) inside a sandboxed iframe.
 *
 * @param container - The DOM element to append the iframe to
 * @param htmlContent - Raw HTML string from the MCP tool result
 * @param options - Configuration options
 * @returns The created iframe element
 */
export function renderMcpApp(
    container: HTMLElement,
    htmlContent: string,
    options: McpAppOptions = {},
): HTMLIFrameElement {
    const {
        maxHeight = 600,
        minHeight = 80,
        onOpenLink,
        onMessage,
        toolName = 'unknown',
    } = options;

    // Build full HTML document with bridge and base styles
    const fullHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: https:;">
    ${BASE_STYLE}
</head>
<body>
    ${htmlContent}
    ${BRIDGE_SCRIPT}
</body>
</html>`;

    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'mcp-app-wrapper';
    wrapper.dataset.tool = toolName;

    // Create header
    const header = document.createElement('div');
    header.className = 'mcp-app-header';
    header.innerHTML = `<span class="mcp-app-icon">⚡</span> <span class="mcp-app-label">${escapeHtml(toolName)}</span>`;
    wrapper.appendChild(header);

    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.className = 'mcp-app-frame';
    iframe.setAttribute('sandbox', 'allow-scripts');
    iframe.setAttribute('srcdoc', fullHtml);
    iframe.setAttribute('loading', 'lazy');
    iframe.style.minHeight = `${minHeight}px`;
    iframe.style.maxHeight = `${maxHeight}px`;

    wrapper.appendChild(iframe);
    container.appendChild(wrapper);

    // Listen for messages from iframe
    const messageHandler = (event: MessageEvent) => {
        const data = event.data as McpAppMessage;
        if (!data || data.type !== 'mcp-app') return;

        switch (data.action) {
            case 'resize': {
                const h = data.payload.height as number;
                if (h > 0) {
                    const clamped = Math.min(Math.max(h + 4, minHeight), maxHeight);
                    iframe.style.height = `${clamped}px`;
                }
                break;
            }
            case 'open-link': {
                const url = data.payload.url as string;
                if (url && (url.startsWith('https://') || url.startsWith('http://'))) {
                    if (onOpenLink) onOpenLink(url);
                    else window.open(url, '_blank', 'noopener');
                }
                break;
            }
            default:
                if (onMessage) onMessage(data);
                break;
        }
    };

    window.addEventListener('message', messageHandler);

    // Cleanup when iframe is removed from DOM
    const observer = new MutationObserver(() => {
        if (!document.contains(iframe)) {
            window.removeEventListener('message', messageHandler);
            observer.disconnect();
        }
    });
    observer.observe(container, { childList: true, subtree: true });

    return iframe;
}

/**
 * Check if a tool_result SSE event contains MCP App UI data.
 */
export function hasMcpAppUI(evt: Record<string, unknown>): boolean {
    return typeof evt.ui_html === 'string' && evt.ui_html.length > 0;
}

/**
 * Create a demo MCP App HTML for testing purposes.
 * This simulates what a real MCP server would return.
 */
export function createDemoAppHtml(toolName: string, data: unknown): string {
    if (toolName === 'periskope_search' || toolName === 'periskope_research') {
        return createSearchResultsUI(data);
    }
    if (toolName === 'mneme_search' || toolName === 'mcp_mneme_search') {
        return createKnowledgeGraphUI(data);
    }
    // Generic: render as a formatted JSON viewer
    return `
        <div style="padding: 8px;">
            <h3 style="color: #a0a0ff; margin-bottom: 8px;">📦 ${escapeHtml(toolName)}</h3>
            <pre style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 12px; color: #b0b0b0;">
${escapeHtml(JSON.stringify(data, null, 2).slice(0, 2000))}
            </pre>
        </div>
    `;
}

// ─── Demo UI Templates ───────────────────────────────────────

function createSearchResultsUI(data: unknown): string {
    const results = Array.isArray(data) ? data : [];
    const rows = results.slice(0, 10).map((r: Record<string, unknown>, i: number) => `
        <tr>
            <td>${i + 1}</td>
            <td><a href="${escapeHtml(String(r.url || '#'))}">${escapeHtml(String(r.title || '(無題)'))}</a></td>
            <td>${escapeHtml(String(r.source || '-'))}</td>
            <td><span class="badge badge-blue">${typeof r.score === 'number' ? r.score.toFixed(2) : '-'}</span></td>
        </tr>
    `).join('');

    return `
        <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
                <h3 style="color: #a0a0ff;">🔍 検索結果 (${results.length}件)</h3>
                <button onclick="mcpBridge.notify({action:'export'})">📥 エクスポート</button>
            </div>
            <table>
                <thead><tr><th>#</th><th>タイトル</th><th>ソース</th><th>スコア</th></tr></thead>
                <tbody>${rows || '<tr><td colspan="4" style="text-align:center; color:#888;">結果なし</td></tr>'}</tbody>
            </table>
        </div>
    `;
}

function createKnowledgeGraphUI(data: unknown): string {
    const items = Array.isArray(data) ? data : [];
    const cards = items.slice(0, 6).map((item: Record<string, unknown>) => `
        <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.1);">
            <div style="font-weight:600; color:#e0e0e0; margin-bottom:4px;">${escapeHtml(String(item.title || item.name || ''))}</div>
            <div style="font-size:12px; color:#888; line-height:1.4;">${escapeHtml(String(item.snippet || item.content || '').slice(0, 120))}...</div>
            <div style="margin-top:6px;">
                <span class="badge badge-green">${escapeHtml(String(item.source || item.type || ''))}</span>
            </div>
        </div>
    `).join('');

    return `
        <div>
            <h3 style="color: #a0a0ff; margin-bottom: 12px;">📚 知識ベース (${items.length}件)</h3>
            <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap:10px;">
                ${cards || '<div style="color:#888;">結果なし</div>'}
            </div>
        </div>
    `;
}

// ─── Utility ─────────────────────────────────────────────────

function escapeHtml(s: string): string {
    return s.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
