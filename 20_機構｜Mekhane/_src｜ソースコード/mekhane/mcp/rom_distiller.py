from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/機能] <- mekhane/mcp/ V-003 ROM 蒸留エンジン
"""
ROM Distiller — セッション履歴を蒸留して ROM ファイルに保存する。

PURPOSE: /rom WF の Phase 0-4 をコード化。
  1. extract_session — 会話履歴取得
  2. classify_content — DECISION/DISCOVERY/CONTEXT 分類
  3. distill — 圧縮 + テンプレート適用
  4. write_rom — ファイル保存
  5. quality_check — 品質チェック

依存: compaction.py (summarize_history), ochema (session_read/cortex)
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# PURPOSE: ROM 保存先ディレクトリ
ROM_DIR = Path(os.getenv(
    "HGK_ROM_DIR",
    os.path.expanduser(
        "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
        "/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom"
    ),
))

# Context Rot しきい値 (step 数ベース)
HEALTH_THRESHOLDS = {
    "green": 30,    # 0-30: 健全
    "yellow": 40,   # 31-40: 中間セーブ推奨
    "orange": 50,   # 41-50: 新規受付停止
    "red": 999,     # 51+: /bye 強制
}

# 退避緊急度 (context-guardian P0/P1/P2 由来)
# P0=DECISION/DISCOVERY(致命的喪失), P1=CONTEXT/PATTERN(重大喪失), P2=ARTIFACT/FAILURE(許容)
EVACUATION_URGENCY = {
    "green": "none",       # 退避不要
    "yellow": "advisory",  # 退避推奨 (P2 は捨てても可)
    "orange": "mandatory", # 退避必須 (P0/P1 を即座に ROM 化)
    "red": "critical",     # 即時退避 + /bye (全 P レベル保存)
}

# 分類プロンプト
CLASSIFY_PROMPT = """\
以下の会話ログから、重要な情報を以下のカテゴリに分類してください。
重要: ファイルパス、UUID、APIエンドポイント、設定値などの識別子 (identifier) は省略したり要約したりせず、原文のまま正確に保持してください。

各項目は JSON 配列で返してください。

診断8カテゴリ:
- DECISION: 確定した判断・設計決定
- DISCOVERY: 新たに発見した事実・知見
- CONTEXT: 背景情報・前提条件
- ARTIFACT: 中間成果物 (ファイルパス等)
- FAILURE: 失敗した試行
- PLAN: 今後の計画・未完のTodo
- HYPOTHESIS: 未検証の仮説やアイデア
- METRIC: パフォーマンスやメトリクスの測定結果

会話ログ:
{conversation}

JSON 形式で返してください:
{{"items": [{{"category": "DECISION", "content": "...", "importance": "high"}}]}}
"""

# ROM テンプレート (rom+ = RAG-Optimized)
ROM_TEMPLATE = """\
---
rom_id: {rom_id}
session_id: {session_id}
created_at: "{created_at}"
rom_type: {rom_type}
reliability: {reliability}
topics: {topics}
exec_summary: |
  {exec_summary}
---

# {title}

{body}

## 決定事項
{decisions}

## 発見・知見
{discoveries}

## 背景コンテキスト
{context}

## 関連情報
{related}

## Critical Rules (SACRED_TRUTH)
<hgk-critical-rules>
- FEP: 予測誤差の最小化・能動推論を最優先
- Kalon: Fix(G∘F) 不動点を追求する
- Tapeinophrosyne: prior の precision を下げ、感覚入力の precision を上げる (view_file 必須)
- Autonomia: 違和感を表出し、自動化ツールを駆使する
- Akribeia: 精度最適化。SOURCE と TAINT を区別し、読み手が行動できる出力にする
- 破壊的操作 (rm, mv, .env上書き等) の前には必ず提案し同意を得る
</hgk-critical-rules>

<!-- ROM_GUIDE
primary_use: {primary_use}
retrieval_keywords: {keywords}
expiry: "permanent"
-->
"""


# =============================================================================
# Health Assessment
# =============================================================================


# PURPOSE: step 数から Context Rot の健全度を判定する
def assess_health(step_count: int) -> dict[str, Any]:
    """step 数から Context Rot の健全度を返す。

    Returns:
        {"health": "green"|"yellow"|"orange"|"red",
         "step_count": int,
         "recommendation": str,
         "evacuation_urgency": "none"|"advisory"|"mandatory"|"critical"}
    """
    if step_count <= HEALTH_THRESHOLDS["green"]:
        health = "green"
        recommendation = "健全。そのまま継続可能。"
    elif step_count <= HEALTH_THRESHOLDS["yellow"]:
        health = "yellow"
        recommendation = "/rom を推奨: Hyphē 自動溶解 (auto_dissolve) を実行して重要な判断を場に溶解しませんか？"
    elif step_count <= HEALTH_THRESHOLDS["orange"]:
        health = "orange"
        recommendation = "/rom+ を強く推奨: 新規タスク受付を停止し、即座に場への溶解と ROM 生成を行ってください。"
    else:
        health = "red"
        recommendation = "限界超過。直ちに /rom+ で自動溶解と ROM 生成を行い、/bye でセッションを終了してください。"

    urgency = EVACUATION_URGENCY.get(health, "none")

    return {
        "health": health,
        "step_count": step_count,
        "recommendation": recommendation,
        "evacuation_urgency": urgency,
    }


# =============================================================================
# Session Extraction
# =============================================================================


# PURPOSE: AntigravityClient から会話履歴を取得する
def extract_session(
    cascade_id: str,
    max_turns: int = 50,
) -> list[dict[str, Any]]:
    """LS から会話履歴を取得する。

    Returns:
        generateChat 形式: [{"author": 1|2, "content": "..."}]
    """
    try:
        from mekhane.ochema.antigravity_client import AntigravityClient
        client = AntigravityClient()
        result = client.session_read(cascade_id, max_turns=max_turns, full=True)
        return result.get("conversation", [])
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to extract session %s: %s", cascade_id, e)
        return []


# =============================================================================
# Content Classification
# =============================================================================


# PURPOSE: 会話内容を 8カテゴリ に分類する
def classify_content(
    conversation: list[dict[str, Any]],
    ask_fn: Optional[Any] = None,
) -> list[dict[str, str]]:
    """会話内容を分類する。

    LLM が利用不可の場合はヒューリスティック分類にフォールバック。

    Returns:
        [{"category": "DECISION", "content": "...", "importance": "high"}, ...]
    """
    # ヒューリスティック分類 (LLM 不要)
    items: list[dict[str, str]] = []

    # パターンマッチでの自動分類
    decision_patterns = re.compile(
        r"(?:確定|決定|決めた|承認|approve|decided|設計方針|結論)",
        re.IGNORECASE,
    )
    discovery_patterns = re.compile(
        r"(?:発見|判明|わかった|found|discovered|実測|ベンチマーク結果)",
        re.IGNORECASE,
    )
    artifact_patterns = re.compile(
        r"(?:created|作成|生成|ファイル|\.py|\.md|\.ts|PASSED|テスト)",
        re.IGNORECASE,
    )
    failure_patterns = re.compile(
        r"(?:失敗|FAILED|エラー|error|bug|修正|fix)",
        re.IGNORECASE,
    )
    plan_patterns = re.compile(
        r"(?:TODO|計画|タスク|方針|未完了|実装予定)",
        re.IGNORECASE,
    )
    hypothesis_patterns = re.compile(
        r"(?:仮説|かもしれない|推測|可能性|検討)",
        re.IGNORECASE,
    )
    metric_patterns = re.compile(
        r"(?:速度|ms|MB|秒|トークン|件|スコア|score)",
        re.IGNORECASE,
    )

    for msg in conversation:
        content = msg.get("content", "")
        if not content or msg.get("author") == 0:  # skip system
            continue

        # content が長すぎる場合は先頭部分のみチェック
        check_text = content[:1000]

        if decision_patterns.search(check_text):
            items.append({
                "category": "DECISION",
                "content": _summarize_line(content),
                "importance": "high",
            })
        elif discovery_patterns.search(check_text):
            items.append({
                "category": "DISCOVERY",
                "content": _summarize_line(content),
                "importance": "high",
            })
        elif artifact_patterns.search(check_text):
            items.append({
                "category": "ARTIFACT",
                "content": _summarize_line(content),
                "importance": "medium",
            })
        elif failure_patterns.search(check_text):
            items.append({
                "category": "FAILURE",
                "content": _summarize_line(content),
                "importance": "medium",
            })
        elif plan_patterns.search(check_text):
            items.append({
                "category": "PLAN",
                "content": _summarize_line(content),
                "importance": "medium",
            })
        elif hypothesis_patterns.search(check_text):
            items.append({
                "category": "HYPOTHESIS",
                "content": _summarize_line(content),
                "importance": "medium",
            })
        elif metric_patterns.search(check_text):
            items.append({
                "category": "METRIC",
                "content": _summarize_line(content),
                "importance": "medium",
            })

    # LLM 分類 (利用可能な場合)
    if ask_fn and conversation:
        try:
            conv_text = _conversation_to_text(conversation[:30])  # 最大 30 ターン
            prompt = CLASSIFY_PROMPT.format(conversation=conv_text[:8000])
            response = ask_fn(prompt, "gemini-3-flash-preview")
            data = json.loads(
                response.strip()
                .removeprefix("```json")
                .removesuffix("```")
                .strip()
            )
            if "items" in data:
                # LLM 結果でヒューリスティック結果を補強
                for llm_item in data["items"]:
                    if llm_item.get("content") and not any(
                        i["content"] == llm_item["content"] for i in items
                    ):
                        items.append(llm_item)
        except Exception as e:  # noqa: BLE001
            logger.debug("LLM classification failed, using heuristic only: %s", e)

    return items


# =============================================================================
# Distillation
# =============================================================================


# PURPOSE: 会話と分類結果を ROM テンプレートに蒸留する
def distill(
    conversation: list[dict[str, Any]],
    classified_items: list[dict[str, str]],
    topic: str = "",
    summary: str = "",
    rom_type: str = "rag_optimized",  # rom+ default
    session_id: str = "",
) -> str:
    """分類済みアイテムを ROM テンプレートに蒸留する。

    Returns:
        ROM ファイル内容 (Markdown)
    """
    now = datetime.now()

    # 決定事項
    decisions = [i for i in classified_items if i["category"] == "DECISION"]
    discoveries = [i for i in classified_items if i["category"] == "DISCOVERY"]
    contexts = [i for i in classified_items if i["category"] == "CONTEXT"]
    artifacts = [i for i in classified_items if i["category"] == "ARTIFACT"]

    # トピック自動推定
    if not topic:
        if decisions:
            topic = decisions[0]["content"][:50]
        elif discoveries:
            topic = discoveries[0]["content"][:50]
        else:
            topic = f"session_{now.strftime('%Y%m%d_%H%M')}"

    # slug 生成 (英語・snake_case)
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", topic.lower())[:40].strip("_")
    if not slug:
        slug = f"session_{now.strftime('%Y%m%d_%H%M')}"

    rom_id = f"rom_{now.strftime('%Y-%m-%d')}_{slug}"

    # exec_summary 生成
    if not summary:
        summary_parts = []
        if decisions:
            summary_parts.append(f"決定 {len(decisions)} 件")
        if discoveries:
            summary_parts.append(f"発見 {len(discoveries)} 件")
        if artifacts:
            summary_parts.append(f"成果物 {len(artifacts)} 件")
        summary = "。".join(summary_parts) if summary_parts else "セッション蒸留"

    # トピックキーワード
    topics_list = []
    for item in classified_items[:10]:
        words = item["content"].split()[:3]
        topics_list.extend(words)
    topics_yaml = json.dumps(list(set(topics_list))[:10], ensure_ascii=False)

    # 各セクション構築
    def _format_items(items: list[dict]) -> str:
        if not items:
            return "- なし\n"
        return "\n".join(f"- {i['content']}" for i in items) + "\n"

    # 関連情報
    related_lines = []
    for item in artifacts:
        related_lines.append(f"- 成果物: {item['content']}")
    related = "\n".join(related_lines) if related_lines else "- なし"

    body = ""
    if conversation:
        body = f"> このセッションでは {len(conversation)} ターンの会話が行われた。\n"

    return ROM_TEMPLATE.format(
        rom_id=rom_id,
        session_id=session_id or "unknown",
        created_at=now.strftime("%Y-%m-%d %H:%M"),
        rom_type=rom_type,
        reliability="High" if decisions else "Medium",
        topics=topics_yaml,
        exec_summary=summary,
        title=topic,
        body=body,
        decisions=_format_items(decisions),
        discoveries=_format_items(discoveries),
        context=_format_items(contexts),
        related=related,
        primary_use="セッション復元",
        keywords=", ".join(topics_list[:5]) if topics_list else topic,
    )


# =============================================================================
# Write ROM
# =============================================================================


# PURPOSE: ROM ファイルを保存する
def write_rom(content: str, topic: str = "") -> Path:
    """ROM ファイルを保存し、パスを返す。"""
    ROM_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", topic.lower())[:40].strip("_")
    if not slug:
        slug = f"session_{now.strftime('%Y%m%d_%H%M')}"

    filename = f"rom_{now.strftime('%Y-%m-%d')}_{slug}.md"
    filepath = ROM_DIR / filename

    # 同名ファイルがある場合はサフィックス追加
    counter = 1
    while filepath.exists():
        filepath = ROM_DIR / f"rom_{now.strftime('%Y-%m-%d')}_{slug}_{counter}.md"
        counter += 1

    filepath.write_text(content, encoding="utf-8")
    logger.info("ROM written: %s", filepath)
    return filepath


# =============================================================================
# Quality Check
# =============================================================================


# PURPOSE: ROM の品質を自動チェックする
def quality_check(
    rom_content: str,
    original_tokens: int,
    classified_items: list[dict[str, str]],
) -> dict[str, Any]:
    """ROM の品質メトリクスを返す。"""
    from mekhane.agent_guard.compaction import estimate_tokens

    rom_tokens = estimate_tokens(rom_content)
    compression_ratio = rom_tokens / max(1, original_tokens)

    decisions_count = sum(1 for i in classified_items if i["category"] == "DECISION")
    discoveries_count = sum(1 for i in classified_items if i["category"] == "DISCOVERY")

    # 品質スコア (5点満点)
    score = 0
    if decisions_count > 0:
        score += 1  # 決定事項保持
    if discoveries_count > 0:
        score += 1  # 発見保持
    if compression_ratio < 0.5:
        score += 1  # 十分な圧縮
    if "topics:" in rom_content:
        score += 1  # 検索性
    if "rom_type:" in rom_content:
        score += 1  # メタデータ完備

    return {
        "rom_tokens": rom_tokens,
        "original_tokens": original_tokens,
        "compression_ratio": round(compression_ratio, 3),
        "decisions_preserved": decisions_count,
        "discoveries_preserved": discoveries_count,
        "quality_score": score,
        "quality_verdict": "PASS" if score >= 3 else "MARGINAL" if score >= 2 else "FAIL",
    }


# =============================================================================
# Full Pipeline
# =============================================================================


# PURPOSE: 蒸留パイプライン全体を実行する
def run_distillation(
    cascade_id: str = "",
    topic: str = "",
    depth: str = "L3",
    conversation: Optional[list[dict]] = None,
    ask_fn: Optional[Any] = None,
) -> dict[str, Any]:
    """蒸留パイプラインを実行する。

    Args:
        cascade_id: セッション ID (空なら conversation を直接使用)
        topic: ROM のトピック名
        depth: 蒸留深度 (L1=snapshot, L2=distilled, L3=rag_optimized)
        conversation: 会話履歴を直接渡す場合 (テスト用)
        ask_fn: LLM 呼出し関数 (省略時はヒューリスティックのみ)

    Returns:
        {"rom_path": str, "quality": dict, "health_after": dict}
    """
    from mekhane.agent_guard.compaction import estimate_tokens, estimate_history_tokens

    # Phase 0: 会話取得
    if conversation is None:
        conversation = extract_session(cascade_id)

    if not conversation:
        return {
            "error": "会話履歴が空です",
            "rom_path": "",
            "quality": {},
            "health_after": assess_health(0),
        }

    original_tokens = estimate_history_tokens(conversation)

    # Phase 1: 分類
    classified = classify_content(conversation, ask_fn=ask_fn)

    # Phase 2: 蒸留
    rom_type_map = {"L1": "snapshot", "L2": "distilled", "L3": "rag_optimized"}
    rom_type = rom_type_map.get(depth, "rag_optimized")

    # 要約生成 (LLM 利用可能時)
    summary = ""
    if ask_fn:
        try:
            from mekhane.agent_guard.compaction import summarize_history
            summary = summarize_history(conversation[:20], ask_fn)
        except Exception as e:  # noqa: BLE001
            logger.debug("Summary generation failed: %s", e)

    rom_content = distill(
        conversation=conversation,
        classified_items=classified,
        topic=topic,
        summary=summary,
        rom_type=rom_type,
        session_id=cascade_id,
    )

    # Phase 3: 保存
    rom_path = write_rom(rom_content, topic=topic)

    # Phase 4: 品質チェック
    quality = quality_check(rom_content, original_tokens, classified)

    # 蒸留後の健全度推定 (蒸留により実質的にリセット)
    health_after = assess_health(5)  # 蒸留後は実質新品

    return {
        "rom_path": str(rom_path),
        "quality": quality,
        "health_after": health_after,
        "items_classified": len(classified),
        "original_tokens": original_tokens,
    }


# =============================================================================
# Utilities
# =============================================================================


# PURPOSE: 会話メッセージを1行要約にする
def _summarize_line(content: str, max_len: int = 200) -> str:
    """長いテキストを1行に要約する。"""
    # 改行を除去し、先頭の有意な行を取得
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if not lines:
        return content[:max_len]

    # コードブロック、テーブル等をスキップして最初の自然言語行を取得
    for line in lines:
        if not line.startswith(("```", "|", "---", "===", "#")):
            return line[:max_len]

    return lines[0][:max_len]


# PURPOSE: 会話をテキスト形式に変換する
def _conversation_to_text(
    conversation: list[dict[str, Any]],
    max_per_msg: int = 500,
) -> str:
    """会話リストをプレーンテキストに変換する。"""
    role_map = {0: "System", 1: "User", 2: "Model"}
    lines = []
    for msg in conversation:
        role = role_map.get(msg.get("author", 1), "Unknown")
        content = msg.get("content", "")[:max_per_msg]
        lines.append(f"[{role}]: {content}")
    return "\n\n".join(lines)
