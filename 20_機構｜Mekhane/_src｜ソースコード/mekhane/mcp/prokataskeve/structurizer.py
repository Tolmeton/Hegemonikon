from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/structurizer.py
"""
Structurizer — Týpos MECE 構造化モジュール。

PURPOSE: Creator の自由記述テキストを Týpos プロンプトに基づき
MECE (Mutually Exclusive, Collectively Exhaustive) に構造化する。
情報量を一切損なわず、構造だけを付与する「下ごしらえ」。

Functions:
  - structurize (L2, async) — LLM で MECE 分解 + WF 提案
  - parse_structured_output (L2, sync) — LLM 出力を StructuredBlock に変換

FEP: Skepsis→Synagōgē 随伴対 — 発散 (分解) と収束 (統合) の不動点。
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from mekhane.mcp.prokataskeve.models import (
    Entity,
    IntentClassification,
    StructuredBlock,
    StructureResult,
    TraceEntry,
)

logger = logging.getLogger(__name__)

# Týpos プロンプトのパス
_TYPOS_PATH = (
    Path(__file__).resolve().parents[4]
    / "10_知性｜Nous" / "05_素材｜Hylē" / "prokataskeve_structurize.typos"
)

# コンパイル済みシステムプロンプトのキャッシュ
_compiled_prompt: str | None = None


# PURPOSE: Týpos プロンプトをコンパイルしてキャッシュする
def _get_system_prompt() -> str:
    """Týpos プロンプトをコンパイルしてシステムプロンプトとして返す。

    Týpos MCP が利用可能な場合はそちらで compile、
    利用不可の場合はファイルをそのまま読み込む (raw fallback)。
    """
    global _compiled_prompt  # noqa: PLW0603
    if _compiled_prompt is not None:
        return _compiled_prompt

    # Týpos ファイルを読み込む
    typos_content = ""
    if _TYPOS_PATH.exists():
        typos_content = _TYPOS_PATH.read_text(encoding="utf-8")
        logger.debug("Loaded Týpos prompt from %s (%d chars)", _TYPOS_PATH, len(typos_content))
    else:
        logger.warning("Týpos file not found: %s", _TYPOS_PATH)

    if not typos_content:
        # フォールバック: 最小プロンプト
        _compiled_prompt = (
            "You are a text structurizer. Decompose the input into MECE blocks "
            "(A=tasks, B=ideas, C=meta). Output JSON array of blocks."
        )
        return _compiled_prompt

    # Týpos MCP でコンパイルを試みる (同期)
    try:
        from mekhane.mcp.typos_facade import compile_typos
        _compiled_prompt = compile_typos(typos_content, model="gemini")
        logger.debug("Týpos compiled via facade (%d chars)", len(_compiled_prompt))
        return _compiled_prompt
    except Exception as e:  # noqa: BLE001
        logger.debug("Týpos facade unavailable, using raw: %s", e)

    # Raw フォールバック: <:...:> タグを読みやすく変換
    _compiled_prompt = typos_content
    return _compiled_prompt


# PURPOSE: LLM 出力をパースして StructureResult に変換する
def parse_structured_output(raw_text: str) -> StructureResult:
    """LLM の構造化出力をパースして StructureResult に変換する。

    JSON 配列形式と Markdown 形式の両方をサポート。
    v4: サマリ行、トレーサビリティ表、priority、WF根拠分離もパース。
    """
    blocks: list[StructuredBlock] = []
    summary = ""
    traceability: list[TraceEntry] = []

    # サマリ行の抽出 ("**サマリ: 3タスク + 2構想**" パターン)
    summary_match = re.search(r"\*\*サマリ[::：]\s*(.*?)\*\*", raw_text)
    if summary_match:
        summary = summary_match.group(1).strip()

    # トレーサビリティ表の抽出 ("| 原文 | ブロック |" 以降の行)
    trace_pattern = re.compile(
        r"^\|\s*(.+?)\s*\|\s*([A-C][-\d\s\[\]条件]+?)\s*\|\s*$",
        re.MULTILINE,
    )
    for tmatch in trace_pattern.finditer(raw_text):
        orig = tmatch.group(1).strip()
        bid = tmatch.group(2).strip()
        # ヘッダ行やセパレータ行をスキップ
        if orig in ("原文", "---", "--") or bid in ("ブロック", "---", "--"):
            continue
        traceability.append(TraceEntry(original=orig, block_id=bid))

    # JSON 形式を試す
    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = json.loads(raw_text)

        if isinstance(data, list):
            for item in data:
                blocks.append(_dict_to_block(item))
            return StructureResult(
                blocks=blocks, raw_output=raw_text,
                summary=summary, traceability=traceability,
            )
        elif isinstance(data, dict):
            if "blocks" in data:
                for item in data["blocks"]:
                    blocks.append(_dict_to_block(item))
            if "summary" in data and not summary:
                summary = str(data["summary"])
            if "traceability" in data and not traceability:
                for t in data["traceability"]:
                    traceability.append(TraceEntry(
                        original=str(t.get("original", "")),
                        block_id=str(t.get("block_id", "")),
                    ))
            return StructureResult(
                blocks=blocks, raw_output=raw_text,
                summary=summary, traceability=traceability,
            )
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Markdown 形式をパース (- **A-1** [指示] ... パターン)
    # ハイフンあり (A-1) とハイフンなし (A1) の両方にマッチ
    block_pattern = re.compile(
        r"-\s+\*\*([ABC]-?\d+)\*\*\s+"  # ID: A-1, B-1, C-1 or A1, B1
        r"\[([^\]]+)\]\s+"              # トーン: [指示], [提案], [仮説 40%]
        r"(.*?)$",                      # 内容
        re.MULTILINE,
    )

    for match in block_pattern.finditer(raw_text):
        block_id = match.group(1)
        tone = match.group(2)
        content = match.group(3).strip()

        # 系列の判定
        series = block_id[0]  # A, B, C

        # 確信度の抽出
        confidence = _extract_confidence(tone)

        # 依存関係の抽出 (依存/関連/独立)
        dep_match = re.search(r"\[(依存|関連)[::：]\s*(.*?)\]", content)
        dependencies = []
        if dep_match:
            dependencies = [d.strip() for d in dep_match.group(2).split(",")]
            content = content[:dep_match.start()].strip()
        elif "[独立]" in content:
            content = content.replace("[独立]", "").strip()

        # priority の抽出
        priority = 0
        pri_match = re.search(r"\[priority[::：]\s*(\d+)\]", content)
        if pri_match:
            priority = int(pri_match.group(1))
            content = content[:pri_match.start()].strip()

        # HELD ステータスの検出
        is_held = "[HELD]" in content
        if is_held:
            content = content.replace("[HELD]", "").strip()

        # WF 提案の抽出 (新形式: [→WF: /xxx — 根拠])
        # content 行内 or ブロック領域 (次行以降) の両方を探索
        suggested_wf = ""
        wf_rationale = ""
        # まず content 内を探す
        wf_match = re.search(r"\[→WF[::：]\s*(.*?)\]", content)
        if wf_match:
            wf_full = wf_match.group(1).strip()
            content = content[:wf_match.start()].strip()
        else:
            # content に無い場合、ブロック領域 (voice と同じ範囲) を探す
            block_end_wf = raw_text.find("\n- **", match.end())
            if block_end_wf == -1:
                block_end_wf = len(raw_text)
            block_region_wf = raw_text[match.start():block_end_wf]
            wf_match = re.search(r"\[→WF[::：]\s*(.*?)\]", block_region_wf)
            wf_full = wf_match.group(1).strip() if wf_match else ""
        if wf_full:
            # " — " or " - " で WF 名と根拠を分離
            if " — " in wf_full:
                parts = wf_full.split(" — ", 1)
                suggested_wf = parts[0].strip()
                wf_rationale = parts[1].strip()
            elif " - " in wf_full:
                parts = wf_full.split(" - ", 1)
                suggested_wf = parts[0].strip()
                wf_rationale = parts[1].strip()
            else:
                suggested_wf = wf_full

        # voice の抽出 (<:voice: ... :>) — ブロック開始位置以降で探索
        voice = ""
        # ブロック行から次のブロック行までの範囲で voice を探す
        block_end = raw_text.find("\n- **", match.end())
        if block_end == -1:
            block_end = len(raw_text)
        block_region = raw_text[match.start():block_end]
        voice_match = re.search(r"<:voice[::：]\s*(.*?)\s*:\s*>", block_region)
        if voice_match:
            voice = voice_match.group(1).strip()

        blocks.append(StructuredBlock(
            block_id=block_id,
            series=series,
            tone=tone,
            content=content,
            confidence=confidence,
            dependencies=dependencies,
            suggested_wf=suggested_wf,
            wf_rationale=wf_rationale,
            voice=voice,
            is_held=is_held,
            priority=priority,
        ))

    if not blocks:
        # 最終フォールバック: 全文を1ブロックとして扱う
        blocks.append(StructuredBlock(
            block_id="A-1",
            series="A",
            tone="指示",
            content=raw_text[:500],
            confidence=0.5,
        ))

    return StructureResult(
        blocks=blocks,
        raw_output=raw_text,
        summary=summary,
        traceability=traceability,
    )


# PURPOSE: 辞書から StructuredBlock に変換
def _dict_to_block(d: dict[str, Any]) -> StructuredBlock:
    """辞書を StructuredBlock に変換する。"""
    # WF 名と根拠の分離 (JSON 側で結合されている場合)
    wf = str(d.get("suggested_wf", d.get("wf", "")))
    rationale = str(d.get("wf_rationale", d.get("rationale", "")))
    if not rationale and " — " in wf:
        parts = wf.split(" — ", 1)
        wf = parts[0].strip()
        rationale = parts[1].strip()

    return StructuredBlock(
        block_id=str(d.get("id", d.get("block_id", "X-1"))),
        series=str(d.get("series", d.get("id", "A")[0])),
        tone=str(d.get("tone", "")),
        content=str(d.get("content", "")),
        confidence=float(d.get("confidence", 0.5)),
        dependencies=list(d.get("dependencies", d.get("deps", []))),
        suggested_wf=wf,
        wf_rationale=rationale,
        voice=str(d.get("voice", "")),
        is_held=bool(d.get("is_held", d.get("held", False))),
        priority=int(d.get("priority", 0)),
    )


# PURPOSE: トーン文字列から確信度を抽出する
def _extract_confidence(tone: str) -> float:
    """トーン文字列から確信度 (0.0-1.0) を抽出する。"""
    # 数値が含まれている場合 (例: "仮説 40%")
    pct_match = re.search(r"(\d+)%", tone)
    if pct_match:
        return int(pct_match.group(1)) / 100.0

    # キーワードベース
    tone_lower = tone.lower()
    if any(k in tone_lower for k in ["確信", "指示"]):
        return 0.9
    elif any(k in tone_lower for k in ["推定", "提案"]):
        return 0.7
    elif any(k in tone_lower for k in ["仮説", "質問"]):
        return 0.4

    return 0.5


# PURPOSE: L2 MECE 構造化 (Skepsis×Synagōgē — 発散分解と収束統合)
async def structurize(
    text: str,
    intent: IntentClassification | None = None,
    entities: list[Entity] | None = None,
) -> StructureResult:
    """L2 テキストを MECE 構造化する。

    Týpos プロンプト (prokataskeve_structurize.typos) を
    システムプロンプトとして Gemini に渡し、構造化結果を返す。

    短いテキスト (50文字未満) はスキップし、フォールバック結果を返す。

    Args:
        text: 構造化対象のテキスト。
        intent: L1 で分類済みの意図 (参考情報として渡す)。
        entities: L0 で抽出済みのエンティティ。

    Returns:
        StructureResult: MECE 構造化結果。
    """
    # 短いテキストはスキップ (構造化の意味がない)
    if len(text.strip()) < 50:
        return StructureResult(
            blocks=[StructuredBlock(
                block_id="A1",
                series="A",
                tone="指示",
                content=text.strip(),
                confidence=0.9,
            )],
            raw_output="",
            is_fallback=True,
        )

    # システムプロンプトの取得
    system_prompt = _get_system_prompt()

    # ユーザープロンプトの構築
    user_prompt = f"以下のテキストを MECE 構造化してください。\n\n---\n{text}\n---"

    # 意図情報があれば追加
    if intent is not None:
        user_prompt += f"\n\n[参考] 意図分類: {intent.intent.value} (確信度: {intent.confidence})"

    # LLM 呼び出し
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex(max_tokens=2048, timeout=10.0)
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        response = await asyncio.to_thread(
            client.chat,
            message=user_prompt,
            model="gemini-3-flash-preview",
            system_instruction=system_prompt,
            timeout=10.0,
        )

        raw_output = response.text.strip() if hasattr(response, "text") else str(response).strip()
        result = parse_structured_output(raw_output)
        result.is_fallback = False

        return result

    except Exception as e:  # noqa: BLE001
        logger.warning("Structurize LLM failed, using fallback: %s", e)

        # フォールバック: テキストを段落分割で簡易構造化
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        blocks = []
        for i, para in enumerate(paragraphs[:10], 1):
            blocks.append(StructuredBlock(
                block_id=f"A{i}",
                series="A",
                tone="指示",
                content=para,
                confidence=0.3,
            ))

        if not blocks:
            blocks.append(StructuredBlock(
                block_id="A1",
                series="A",
                tone="指示",
                content=text[:500],
                confidence=0.3,
            ))

        return StructureResult(
            blocks=blocks,
            raw_output=f"[fallback: {e}]",
            is_fallback=True,
        )
