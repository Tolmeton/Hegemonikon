/**
 * Chat Types — 型定義・ToolStatus (ClawX adjoint: God Object 分割)
 * chat.ts から抽出した純粋な型宣言。
 */

// ─── Message Types ───────────────────────────────────────────

export interface ChatMessage {
    role: 'user' | 'model';
    content: string;
    timestamp: Date;
    model?: string;
    attachments?: Attachment[];
}

export interface Attachment {
    name: string;
    path: string;
    mime: string;
    size: number;
    dataUrl?: string; // for image preview
}

export interface BranchPoint {
    atIndex: number;              // メッセージインデックス（分岐が発生した位置）
    branches: ChatMessage[][];    // 各分岐のメッセージ配列 (atIndex 以降)
    activeBranch: number;         // 現在表示中の分岐インデックス
}

// ─── API Types ───────────────────────────────────────────────

export interface GeminiContent {
    role: string;
    parts: { text: string }[];
}

export interface GeminiResponse {
    candidates?: {
        content: {
            parts: { text: string }[];
            role: string;
        };
        finishReason: string;
    }[];
    error?: { message: string; code: number };
}

export interface Conversation {
    id: string;
    title: string;
    messages: ChatMessage[];
    branchPoints?: BranchPoint[];  // 分岐記録（後方互換: 省略可）
    createdAt: Date;
}

// ─── Tool Status (ClawX adjoint: 欺瞞3 解決) ────────────────

export type ToolState = 'running' | 'completed' | 'error' | 'approval_required';

export interface ToolStatus {
    name: string;
    args: Record<string, unknown>;
    state: ToolState;
    startedAt: number;
    duration?: number;
    output?: string;
    error?: string;
    iteration?: number;
    maxIterations?: number;
    requestId?: string;    // Safety Gate approval
}

// ─── Streaming Dependencies ──────────────────────────────────
// chat-streaming.ts が chat.ts の UI 関数を呼ぶためのコールバック

export interface StreamingDeps {
    renderMessages: () => void;
    saveAllConversations: () => void;
    updateTerminalTab: () => void;
    showApprovalUI: (requestId: string, toolName: string, args: Record<string, unknown>, diffText: string | null) => void;
    terminalLog: string[];
    renderMcpApp: (container: HTMLElement, html: string, opts: { toolName: string; onOpenLink: (url: string) => void }) => void;
    hasMcpAppUI: (evt: Record<string, unknown>) => boolean;
}
