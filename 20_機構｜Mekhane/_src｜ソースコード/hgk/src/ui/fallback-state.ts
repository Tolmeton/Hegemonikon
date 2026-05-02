/**
 * FallbackState — 統一的なエラー/空状態コンポーネント
 *
 * PURPOSE: 全ビューで一貫したエラーハンドリングと空状態表示を提供する。
 * 503 生テキストの露出を防ぎ、リトライ・代替アクションを案内する。
 *
 * KALON_AUDITOR L3/L5 指摘対応: エラーハンドリング統一 + Craftsmanship
 */

import { esc } from '../utils';

// --- Types ---

export interface FallbackOptions {
    /** アイコン (emoji or HTML) */
    icon?: string;
    /** メインタイトル */
    title: string;
    /** 詳細メッセージ */
    message?: string;
    /** リトライコールバック */
    onRetry?: () => void;
    /** 追加アクション */
    actions?: Array<{ label: string; onClick: () => void; variant?: 'primary' | 'ghost' }>;
    /** スタイルバリアント */
    variant?: 'error' | 'empty' | 'offline' | 'info';
}

// --- Render ---

/**
 * 統一的なフォールバック状態をレンダリングする。
 * コンテナの innerHTML を置き換える。
 */
export function renderFallbackState(container: HTMLElement, opts: FallbackOptions): void {
    const variant = opts.variant ?? 'error';
    const icon = opts.icon ?? VARIANT_ICONS[variant];

    const actionsHtml = (opts.actions ?? [])
        .map(a => `<button class="fallback-action ${a.variant === 'ghost' ? 'fallback-action--ghost' : ''}">${esc(a.label)}</button>`)
        .join('');

    const retryHtml = opts.onRetry
        ? `<button class="fallback-action fallback-action--retry">↻ リトライ</button>`
        : '';

    container.innerHTML = `
    <div class="fallback-state fallback-state--${variant}">
      <div class="fallback-icon">${icon}</div>
      <h2 class="fallback-title">${esc(opts.title)}</h2>
      ${opts.message ? `<p class="fallback-message">${esc(opts.message)}</p>` : ''}
      <div class="fallback-actions">
        ${retryHtml}
        ${actionsHtml}
      </div>
    </div>
  `;

    // Bind retry
    if (opts.onRetry) {
        const retryBtn = container.querySelector('.fallback-action--retry');
        retryBtn?.addEventListener('click', opts.onRetry);
    }

    // Bind custom actions
    if (opts.actions) {
        const buttons = container.querySelectorAll('.fallback-action:not(.fallback-action--retry)');
        buttons.forEach((btn, i) => {
            btn.addEventListener('click', () => opts.actions?.[i]?.onClick());
        });
    }
}

/**
 * API エラーからフォールバック状態をレンダリングするショートカット。
 */
export function renderApiError(container: HTMLElement, error: Error, onRetry?: () => void): void {
    const status = extractStatusCode(error.message);

    const messages: Record<number, { title: string; message: string }> = {
        503: { title: 'サービス一時停止中', message: 'バックエンドが応答していません。しばらく待ってから再試行してください。' },
        502: { title: 'ゲートウェイエラー', message: 'API ゲートウェイに到達できません。' },
        500: { title: 'サーバーエラー', message: '予期しないエラーが発生しました。' },
        404: { title: 'リソースが見つかりません', message: '要求された API エンドポイントが存在しません。' },
        401: { title: '認証が必要です', message: 'セッションの有効期限が切れている可能性があります。' },
        0: { title: '接続エラー', message: 'ネットワーク接続を確認してください。' },
    };

    const info = messages[status] ?? { title: 'エラーが発生しました', message: error.message };

    renderFallbackState(container, {
        variant: status === 0 ? 'offline' : 'error',
        title: info.title,
        message: info.message,
        onRetry,
    });
}

/**
 * 空状態 (ゼロステート) をレンダリングするショートカット。
 */
export function renderEmptyState(
    container: HTMLElement,
    title: string,
    message?: string,
    actions?: FallbackOptions['actions'],
): void {
    renderFallbackState(container, {
        variant: 'empty',
        title,
        message,
        actions,
    });
}

// --- Helpers ---

const VARIANT_ICONS: Record<string, string> = {
    error: '⚠️',
    empty: '📭',
    offline: '🔌',
    info: 'ℹ️',
};

function extractStatusCode(msg: string): number {
    const match = msg.match(/(\d{3})/);
    const code = match?.[1];
    return code ? parseInt(code, 10) : 0;
}
