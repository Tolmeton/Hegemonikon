/**
 * Log Classifier — stderr 分類パターン (from ClawX adjoint analysis)
 * SSE/Agent ストリーム内のメッセージを severity で分類する。
 * ClawX の classifyStderrMessage() を HGK の SSE コンテキストに適用。
 */

export type LogLevel = 'drop' | 'debug' | 'warn' | 'error';

export interface ClassifiedMessage {
    level: LogLevel;
    normalized: string;
}

// drop: ノイズ — ユーザーに表示しない
const DROP_PATTERNS = [
    /^:\s*$/,                     // SSE keepalive (コロン行)
    /^\s*$/,                      // 空行
    /^data:\s*$/,                 // 空 data フィールド
    /\[DONE\]/,                   // SSE 完了マーカー
    /^ping$/i,                    // WebSocket ping
    /^connection established/i,   // 接続確立メッセージ
];

// debug: 開発者向け — console.debug のみ
const DEBUG_PATTERNS = [
    /thinking/i,                  // thinking chunk
    /tool_call/i,                 // ツール呼び出し開始
    /tool_result/i,               // ツール呼び出し結果
    /^iteration/i,                // Agent イテレーション
    /^phase/i,                    // Colony フェーズ
    /chunk$/i,                    // ストリーミングチャンク
];

// error: 致命的 — ユーザーに即座に表示
const ERROR_PATTERNS = [
    /^(4[0-9]{2}|5[0-9]{2})\b/,  // HTTP エラーコード
    /API [Ee]rror/,               // API エラー
    /ECONNREFUSED/,               // 接続拒否
    /ETIMEDOUT/,                  // タイムアウト
    /abort/i,                     // ストリーム中断
    /fatal/i,                     // 致命的エラー
    /unreachable/i,               // 到達不能
];

/**
 * メッセージを severity で分類する。
 * drop → debug → error の順でマッチし、いずれにも一致しなければ warn を返す。
 */
export function classifyLogMessage(raw: string): ClassifiedMessage {
    const trimmed = raw.trim();

    for (const pattern of DROP_PATTERNS) {
        if (pattern.test(trimmed)) {
            return { level: 'drop', normalized: trimmed };
        }
    }

    for (const pattern of DEBUG_PATTERNS) {
        if (pattern.test(trimmed)) {
            return { level: 'debug', normalized: trimmed };
        }
    }

    for (const pattern of ERROR_PATTERNS) {
        if (pattern.test(trimmed)) {
            return { level: 'error', normalized: trimmed };
        }
    }

    // デフォルト: warn — 分類不明なメッセージはユーザーに表示
    return { level: 'warn', normalized: trimmed };
}
