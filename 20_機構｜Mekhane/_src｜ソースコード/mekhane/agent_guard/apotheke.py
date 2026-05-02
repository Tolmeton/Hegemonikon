from __future__ import annotations
# PROOF: [L2/機能] <- mekhane/agent_guard/apotheke.py A0→対話の後処理が必要→apotheke が担う
# PURPOSE: 対話チャンクを LLM で Týpos 記法のナレッジに変換し、Sophia KI として永続化する
"""Apothēkē (ἀποθήκη) — 対話の後処理パイプライン。

V-001 前処理 (Prokataskevē) の随伴対 (F⊣G)。
前処理が入力の precision を上げるなら、後処理は記憶の precision を上げる。

パイプライン:
  1. extract_evictable — contents から古いメッセージを抽出
  2. narrate           — LLM で Týpos フォーマットのナレッジに変換
  3. save_ki           — Sophia KI ディレクトリに .md として保存
  4. retrieve_context   — Mneme ベクトル検索で関連 KI を取得
"""


import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# --- Constants ---

# 最新 N ターン (user+model ペア) は eviction 対象外
DEFAULT_KEEP_RECENT_TURNS = 4

# narrate に使うモデル (軽量で高速)
DEFAULT_NARRATE_MODEL = "gemini-3-flash-preview"

# KI 保存先ディレクトリ (session memory 専用)
DEFAULT_KI_DIR = Path.home() / ".gemini" / "antigravity" / "knowledge" / "session_memory"

# Týpos ナレッジ化プロンプト
NARRATE_PROMPT = """\
以下の対話チャンクを、Týpos v8 記法で構造化されたナレッジに変換せよ。

## 要件
- **具体を全く損ねないこと** — 数値・固有名詞・判断根拠・コード断片は原文のまま保持
- **情報密度を上げること** — 冗長な対話（挨拶・確認・やり取り）を凝縮し、知識として蒸留する
- **Týpos v8 記法**で記述: #prompt, <:role:>, <:goal:>, <:context:>, <:constraints:> 等
- メタデータを <:context:> 内に含める: session_id, timestamp, 関連 PJ/ファイル

## Týpos v8 フォーマット例

```typos
#prompt session-note-YYYYMMDD-HHMM
#syntax: v8
#depth: L1

<:role: セッションノート — [トピック概要] :>

<:goal: [この対話で達成された/議論されたこと] :>

<:constraints:
  - [決定事項 1]
  - [決定事項 2]
/constraints:>

<:context:
  - [knowledge] [事実情報 1]
  - [knowledge] [事実情報 2]
  - [file] [言及されたファイル] (priority: [重要度])
/context:>
```

## 対話チャンク

{chunks}
"""


# --- Data structures ---


@dataclass
class EvictionResult:
    """Eviction の結果。"""
    kept: list[dict[str, Any]]      # 保持された contents
    evicted: list[dict[str, Any]]   # evict された contents
    evicted_turns: int              # evict されたターン数


@dataclass
class NarrateResult:
    """ナレッジ化の結果。"""
    typos_content: str   # Týpos フォーマットのナレッジ
    model_used: str      # 使用されたモデル
    input_turns: int     # 入力ターン数
    success: bool = True
    error: str = ""


@dataclass
class KIRecord:
    """保存された KI のメタデータ。"""
    path: Path
    session_id: str
    timestamp: str
    tags: list[str] = field(default_factory=list)


# --- ① Extract Evictable ---


def extract_evictable(
    contents: list[dict[str, Any]],
    keep_recent: int = DEFAULT_KEEP_RECENT_TURNS,
) -> EvictionResult:
    """contents から古いメッセージを抽出する。

    contents は Gemini API のメッセージリスト形式:
      [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}, ...]

    最新の keep_recent 個のメッセージは保持し、それより古いものを evict する。

    Args:
        contents: Gemini API 形式のメッセージリスト
        keep_recent: 保持する最新メッセージ数

    Returns:
        EvictionResult with kept and evicted messages
    """
    if len(contents) <= keep_recent:
        return EvictionResult(kept=contents, evicted=[], evicted_turns=0)

    split_point = len(contents) - keep_recent
    evicted = contents[:split_point]
    kept = contents[split_point:]

    logger.info(
        "Apothēkē: evicting %d messages (keeping %d recent)",
        len(evicted), len(kept),
    )

    return EvictionResult(
        kept=kept,
        evicted=evicted,
        evicted_turns=len(evicted),
    )


# --- ② Narrate (LLM × Týpos) ---


def _format_chunks_for_prompt(chunks: list[dict[str, Any]]) -> str:
    """contents 形式のチャンクを人間可読なテキストに変換。"""
    lines = []
    for msg in chunks:
        role = msg.get("role", "unknown")
        parts = msg.get("parts", [])
        for part in parts:
            if isinstance(part, dict):
                if "text" in part:
                    lines.append(f"[{role}]: {part['text']}")
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    lines.append(f"[{role}:tool_call]: {fc.get('name', '?')}({fc.get('args', {})})")
                elif "functionResponse" in part:
                    fr = part["functionResponse"]
                    result_text = str(fr.get("response", ""))[:500]
                    lines.append(f"[{role}:tool_result]: {fr.get('name', '?')} → {result_text}")
            elif isinstance(part, str):
                lines.append(f"[{role}]: {part}")
    return "\n".join(lines)


async def narrate(
    chunks: list[dict[str, Any]],
    session_id: str,
    ask_fn: Callable[..., Any],
    model: str = DEFAULT_NARRATE_MODEL,
) -> NarrateResult:
    """対話チャンクを LLM で Týpos ナレッジに変換する。

    Args:
        chunks: evict された contents (Gemini API 形式)
        session_id: セッション ID
        ask_fn: LLM 呼び出し関数 (CortexAPI.ask 互換)
            Signature: ask_fn(message, model, ...) -> LLMResponse
        model: ナレッジ化に使うモデル

    Returns:
        NarrateResult with Týpos content
    """
    if not chunks:
        return NarrateResult(
            typos_content="", model_used=model,
            input_turns=0, success=False, error="No chunks to narrate",
        )

    formatted = _format_chunks_for_prompt(chunks)
    prompt = NARRATE_PROMPT.format(chunks=formatted)

    try:
        # ask_fn は同期の CortexAPI.ask を想定 → asyncio.to_thread で非同期化
        result = await asyncio.to_thread(
            ask_fn,
            message=prompt,
            model=model,
            temperature=0.3,
            max_tokens=4096,
        )

        typos_content = result.text if hasattr(result, "text") else str(result)

        logger.info(
            "Apothēkē: narrated %d chunks → %d chars Týpos",
            len(chunks), len(typos_content),
        )

        return NarrateResult(
            typos_content=typos_content,
            model_used=model,
            input_turns=len(chunks),
            success=True,
        )

    except Exception as e:  # noqa: BLE001
        logger.error("Apothēkē narrate failed: %s", e)
        return NarrateResult(
            typos_content="", model_used=model,
            input_turns=len(chunks), success=False, error=str(e),
        )


# --- ③ Save KI ---


def save_ki(
    content: str,
    session_id: str,
    tags: Optional[list[str]] = None,
    ki_dir: Path = DEFAULT_KI_DIR,
) -> KIRecord:
    """Týpos ナレッジを KI ファイルとして保存する。

    Args:
        content: Týpos フォーマットのナレッジテキスト
        session_id: セッション ID
        tags: メタデータタグ
        ki_dir: 保存先ディレクトリ

    Returns:
        KIRecord with file path and metadata
    """
    ki_dir.mkdir(parents=True, exist_ok=True)
    tags = tags or []

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    filename = f"session_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.md"
    filepath = ki_dir / filename

    # KI ファイルのヘッダ
    header = (
        f"---\n"
        f"type: session_memory\n"
        f"session_id: {session_id}\n"
        f"created: {timestamp}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"source: apotheke\n"
        f"---\n\n"
    )

    filepath.write_text(header + content, encoding="utf-8")

    logger.info("Apothēkē: saved KI at %s (%d bytes)", filepath, filepath.stat().st_size)

    return KIRecord(
        path=filepath,
        session_id=session_id,
        timestamp=timestamp,
        tags=tags,
    )


# --- ④ Retrieve Context (RAG) ---


def retrieve_context(
    query: str,
    top_k: int = 3,
) -> list[str]:
    """Mneme/Sophia ベクトル検索で関連 KI を取得する。

    Args:
        query: 検索クエリ
        top_k: 返す結果の最大数

    Returns:
        関連 KI のテキストリスト
    """
    try:
        from mekhane.symploke.sophia_ingest import (
            load_sophia_index,
            search_loaded_index,
            DEFAULT_INDEX_PATH,
        )

        if not DEFAULT_INDEX_PATH.exists():
            logger.debug("Apothēkē: Sophia index not found at %s", DEFAULT_INDEX_PATH)
            return []

        adapter = load_sophia_index(str(DEFAULT_INDEX_PATH))
        results = search_loaded_index(adapter, query, top_k=top_k)

        texts = []
        for r in results:
            content = r.metadata.get("content", "") if hasattr(r, "metadata") else str(r)
            if content:
                texts.append(content[:2000])  # 各 KI から最大 2000 文字

        logger.info("Apothēkē: retrieved %d relevant KIs for query", len(texts))
        return texts

    except Exception as e:  # noqa: BLE001
        logger.warning("Apothēkē: RAG retrieval failed: %s", e)
        return []


# --- Pipeline Orchestrator ---


async def run_postprocess(
    evicted_chunks: list[dict[str, Any]],
    session_id: str,
    ask_fn: Callable[..., Any],
    model: str = DEFAULT_NARRATE_MODEL,
    tags: Optional[list[str]] = None,
    ki_dir: Path = DEFAULT_KI_DIR,
) -> Optional[KIRecord]:
    """後処理パイプラインを実行する。

    Args:
        evicted_chunks: evict されたメッセージ
        session_id: セッション ID
        ask_fn: LLM 呼び出し関数
        model: ナレッジ化モデル
        tags: KI タグ
        ki_dir: KI 保存先

    Returns:
        KIRecord if successful, None otherwise
    """
    if not evicted_chunks:
        return None

    # ② Narrate
    narrate_result = await narrate(evicted_chunks, session_id, ask_fn, model)

    if not narrate_result.success:
        logger.error("Apothēkē: narrate failed: %s", narrate_result.error)
        return None

    # ③ Save KI
    ki_record = save_ki(
        content=narrate_result.typos_content,
        session_id=session_id,
        tags=tags or ["auto-evict"],
        ki_dir=ki_dir,
    )

    logger.info(
        "Apothēkē: pipeline complete — %d chunks → KI at %s",
        len(evicted_chunks), ki_record.path,
    )

    return ki_record
