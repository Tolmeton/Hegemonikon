from __future__ import annotations
# PROOF: [L2/機能] <- mekhane/agent_guard/compaction.py A0→Context Rot 防止
# PURPOSE: トークン推定・履歴分割・閾値判定のユーティリティ層
"""Compaction Utilities — Context Rot 防止のための低レベルユーティリティ。

本モジュールはトークン推定・履歴分割・圧縮判定の **ユーティリティ関数** を提供する。

実際のコンテキスト管理 (Lossless Eviction) は apotheke.py が担う:
  apotheke.py — 対話を LLM で Týpos ナレッジに変換し KI として永続化 (無損失)
  cortex_tools.py — ask_with_tools ループ内で 70% 閾値で自動 eviction を発火
  rom_distiller.py — /rom+ で summarize_history を使用

提供するユーティリティ:
- estimate_tokens: chars/4 ヒューリスティックによるトークン推定
- estimate_history_tokens: generateChat 形式の履歴トークン推定
- split_by_token_share: 履歴をトークン均等分割
- chunk_by_max_tokens: 最大トークン制限で分割
- summarize_history: LLM 呼び出しによる要約 (rom_distiller.py が使用)
- needs_compaction: 履歴が予算超過かの軽量判定 (Gateway が使用)

See also:
  mekhane.agent_guard.apotheke — Lossless Eviction パイプライン (本体)
  mekhane.ochema.cortex_tools — ask_with_tools 内での eviction 発火点
"""


import logging
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# --- Constants ---

# OpenClaw の SAFETY_MARGIN に対応: トークン推定の不正確さを吸収
SAFETY_MARGIN = 1.2

# 履歴がコンテキストウィンドウの何割を占めたら圧縮するか
DEFAULT_MAX_HISTORY_SHARE = 0.5

# 要約プロンプトのオーバーヘッド (prompt + system + response 枠)
SUMMARIZATION_OVERHEAD_TOKENS = 4096

# 要約に使う軽量モデル
DEFAULT_SUMMARY_MODEL = "gemini-2.0-flash"

# 要約が生成できなかった場合のフォールバック
DEFAULT_SUMMARY_FALLBACK = "No prior history."

# 識別子保持指示 (OpenClaw の IDENTIFIER_PRESERVATION_INSTRUCTIONS に対応)
IDENTIFIER_PRESERVATION_INSTRUCTIONS = (
    "Preserve all opaque identifiers exactly as written (no shortening or reconstruction), "
    "including UUIDs, hashes, IDs, tokens, API keys, hostnames, IPs, ports, URLs, file names, "
    "and CCL expressions (e.g. /noe+, /dia>>*/ele)."
)

# 要約プロンプト
SUMMARIZE_PROMPT = (
    "You are a conversation summarizer. Summarize the following conversation history "
    "into a concise but comprehensive summary. Preserve:\n"
    "- Key decisions and their rationale\n"
    "- TODOs and open questions\n"
    "- Constraints and requirements\n"
    "- File paths and code references\n"
    f"\n{IDENTIFIER_PRESERVATION_INSTRUCTIONS}\n\n"
    "Conversation:\n{conversation}"
)

MERGE_SUMMARIES_PROMPT = (
    "Merge these partial summaries into a single cohesive summary. "
    "Preserve decisions, TODOs, open questions, and any constraints.\n"
    f"\n{IDENTIFIER_PRESERVATION_INSTRUCTIONS}\n\n"
    "Summaries:\n{summaries}"
)


# --- データ構造 ---


@dataclass
class PruneResult:
    """プルーニング結果。"""
    history: list[dict]
    """圧縮後の履歴 (先頭に要約メッセージが含まれる場合あり)"""
    dropped_count: int
    """削除されたメッセージ数"""
    dropped_tokens: int
    """削除されたトークン数 (推定)"""
    kept_tokens: int
    """保持されたトークン数 (推定)"""
    summary: str
    """生成された要約テキスト (空 = 圧縮不要だった)"""
    budget_tokens: int
    """履歴に割り当てられたトークン予算"""


# --- トークン推定 ---


# PURPOSE: chars/4 ヒューリスティックによるトークン推定 (OpenClaw 互換)
def estimate_tokens(text: str) -> int:
    """テキストのトークン数を概算する。

    chars/4 ヒューリスティック。OpenClaw の estimateTokens() と同等。
    CJK 文字は1文字あたり ~2 トークンなので、chars/4 は過小推定になるが、
    SAFETY_MARGIN (1.2x) で吸収する設計。

    Args:
        text: 推定対象のテキスト

    Returns:
        推定トークン数 (最低1)
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


# PURPOSE: generateChat 形式の履歴 [{author: int, content: str}, ...] のトークン推定
def estimate_history_tokens(history: list[dict]) -> int:
    """履歴全体のトークン数を概算する。

    generateChat 形式: [{"author": 1, "content": "..."}, {"author": 2, "content": "..."}]

    Args:
        history: generateChat 形式の会話履歴

    Returns:
        推定トークン数合計
    """
    total = 0
    for msg in history:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
    return total


# --- 分割 ---


# PURPOSE: 履歴をトークン比率で均等分割 (OpenClaw の splitMessagesByTokenShare)
def split_by_token_share(
    history: list[dict],
    parts: int = 2,
) -> list[list[dict]]:
    """履歴をトークン均等分割する。

    Args:
        history: 分割対象
        parts: 分割数 (default: 2)

    Returns:
        分割されたチャンクのリスト
    """
    if not history:
        return []

    parts = max(1, min(parts, len(history)))
    if parts <= 1:
        return [list(history)]

    total_tokens = estimate_history_tokens(history)
    target_per_part = total_tokens / parts

    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0

    for msg in history:
        msg_tokens = estimate_tokens(msg.get("content", ""))
        if (
            len(chunks) < parts - 1
            and current
            and current_tokens + msg_tokens > target_per_part
        ):
            chunks.append(current)
            current = []
            current_tokens = 0

        current.append(msg)
        current_tokens += msg_tokens

    if current:
        chunks.append(current)

    return chunks


# PURPOSE: 最大トークン制限で分割 (OpenClaw の chunkMessagesByMaxTokens)
def chunk_by_max_tokens(
    history: list[dict],
    max_tokens: int,
) -> list[list[dict]]:
    """履歴を最大トークン制限で分割する。

    Args:
        history: 分割対象
        max_tokens: チャンクあたりの最大トークン数

    Returns:
        分割されたチャンクのリスト
    """
    if not history:
        return []

    effective_max = max(1, int(max_tokens / SAFETY_MARGIN))

    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0

    for msg in history:
        msg_tokens = estimate_tokens(msg.get("content", ""))

        if current and current_tokens + msg_tokens > effective_max:
            chunks.append(current)
            current = []
            current_tokens = 0

        current.append(msg)
        current_tokens += msg_tokens

        # 巨大メッセージ: 単独でも超過 → 即座にチャンク化
        if msg_tokens > effective_max:
            chunks.append(current)
            current = []
            current_tokens = 0

    if current:
        chunks.append(current)

    return chunks


# --- 要約 ---


# PURPOSE: 履歴チャンクを LLM で要約する
def summarize_history(
    history: list[dict],
    ask_fn: Callable[[str, str], str],
    model: str = DEFAULT_SUMMARY_MODEL,
    previous_summary: str = "",
) -> str:
    """履歴を LLM で要約する。

    ask_fn は同期的な LLM 呼び出し関数。
    Ochema の cortex_api._call_api 等を注入する。

    Args:
        history: 要約対象の履歴
        ask_fn: LLM 呼び出し関数 (message: str, model: str) -> str
        model: 使用するモデル名
        previous_summary: 過去の要約 (あれば先頭に含める)

    Returns:
        要約テキスト
    """
    if not history:
        return previous_summary or DEFAULT_SUMMARY_FALLBACK

    # 会話をテキスト化
    lines: list[str] = []
    if previous_summary:
        lines.append(f"[Previous Summary]\n{previous_summary}\n")

    role_map = {0: "System", 1: "User", 2: "Model"}
    for msg in history:
        role = role_map.get(msg.get("author", 1), "Unknown")
        content = msg.get("content", "")
        # 冗長なツール結果を除去 (セキュリティ + トークン節約)
        if len(content) > 2000:
            content = content[:2000] + "\n[...truncated...]"
        lines.append(f"[{role}]: {content}")

    conversation_text = "\n\n".join(lines)
    prompt = SUMMARIZE_PROMPT.format(conversation=conversation_text)

    try:
        result = ask_fn(prompt, model)
        return result if result else DEFAULT_SUMMARY_FALLBACK
    except Exception as e:  # noqa: BLE001
        logger.warning("Compaction summarization failed: %s", e)
        return DEFAULT_SUMMARY_FALLBACK


# --- Lossless Eviction (本体は apotheke.py) ---
#
# 旧 prune_history (Lossy 要約圧縮) はここにあったが、AMBITION F2 要件
# 「具体を全く損ねずに保存」に反するため削除された。
#
# 現在のコンテキスト管理は Lossless Eviction:
#   1. cortex_tools.py: 履歴が 70% に達すると apotheke.extract_evictable() を発火
#   2. apotheke.py: 古いメッセージを LLM で Týpos ナレッジに変換 (narrate)
#   3. apotheke.py: KI ファイルとして永続化 (save_ki)
#   4. apotheke.py: 次回セッションでベクトル検索により復元 (retrieve_context)
#
# See: mekhane.agent_guard.apotheke for full pipeline


# --- ユーティリティ ---


# PURPOSE: 履歴がコンテキスト予算を超えているかの判定 (ガード連携用)
def needs_compaction(
    history: list[dict],
    context_window: int,
    max_share: float = DEFAULT_MAX_HISTORY_SHARE,
) -> bool:
    """履歴がコンテキスト予算を超えているか判定する。

    prune_history を呼ぶ前の軽量チェック。

    Args:
        history: チェック対象
        context_window: モデルのコンテキストウィンドウサイズ
        max_share: 履歴に割り当てるコンテキストの最大比率

    Returns:
        True = 圧縮が必要
    """
    budget = max(1, int(context_window * max_share))
    return estimate_history_tokens(history) > budget
