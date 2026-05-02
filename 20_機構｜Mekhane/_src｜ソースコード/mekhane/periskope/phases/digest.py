from __future__ import annotations
# PROOF: mekhane/periskope/phases/digest.py
# PURPOSE: Phase 4b — Auto-digest to /eat incoming
"""
Phase 4b: Auto-digest.

Writes research results to Digestor incoming as eat_*.md files
compatible with the /eat workflow (F⊣G adjunction).

Extracted from engine.py:
  - _phase_digest (L3090-3212)
  - _quick_template (L3216-3225)
  - _standard_template (L3229-3246)
  - _deep_template (L3250-3305)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from mekhane.paths import INCOMING_DIR

if TYPE_CHECKING:
    from mekhane.periskope.engine import ResearchReport

logger = logging.getLogger(__name__)


def quick_template() -> str:
    """Quick /eat- template — minimal Phase 0."""
    return """## Phase 0: 圏の特定

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext | <!-- 外部構造 --> |
| 圏 Int | <!-- 内部構造 --> |
| F (取込) | <!-- Ext → Int --> |
| G (忘却) | <!-- Int → Ext --> |"""


def standard_template() -> str:
    """Standard /eat template — Phase 0 + /fit checklist."""
    return """## Phase 0: 圏の特定 (テンプレート)

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext (外部構造) | <!-- Periskopē が収集した研究知見 --> |
| 圏 Int (内部構造) | <!-- HGK 内の対応する圏 --> |
| 関手 F (取込) | <!-- Ext → Int へのマッピング --> |
| 関手 G (忘却) | <!-- Int → Ext への写像 --> |
| η (情報保存) | <!-- 取り込んで忘却→元情報をどの程度復元できるか --> |
| ε (構造保存) | <!-- 忘却して取込→HGK構造がどの程度維持されるか --> |

## /fit チェックリスト

- [ ] η 検証: 研究知見が HGK 内で再現可能
- [ ] ε 検証: HGK 既存構造との整合性確認
- [ ] Drift 測定: 1-ε の許容範囲内"""


def deep_template() -> str:
    """Deep /eat+ template — full 7-phase digestion."""
    return """## Phase 0: 圏の特定

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext (外部構造) | <!-- Periskopē が収集した研究知見 --> |
| 圏 Int (内部構造) | <!-- HGK 内の対応する圏 --> |
| 関手 F (取込) | <!-- Ext → Int へのマッピング --> |
| 関手 G (忘却) | <!-- Int → Ext への写像 --> |
| η (情報保存) | <!-- 取り込んで忘却→元情報をどの程度復元できるか --> |
| ε (構造保存) | <!-- 忘却して取込→HGK構造がどの程度維持されるか --> |

## Phase 1: 構造抽出

> 主要概念・メカニズム・依存関係を構造化抽出する。

- [ ] 主要概念の列挙
- [ ] 依存関係グラフ (概念間)
- [ ] HGK 既存概念との対応付け

## Phase 2: 変換設計 (F: Ext → Int)

> 外部知見を HGK 内部構造にマッピングする具体設計。

- [ ] T1: 既知の再発見 (Rediscovery)
- [ ] T2: 既知の拡張 (Extension)
- [ ] T3: 新規概念 (Novel)
- [ ] T4: 不要/矛盾 (Reject)

## Phase 3: 忘却設計 (G: Int → Ext)

> HGK 構造から外部に投影したとき何が失われるかを分析。

- [ ] 忘却される情報の特定
- [ ] 許容できる情報損失の判定
- [ ] 情報保存の対策

## Phase 4: 統合検証

- [ ] η 検証: F→G→F = id (情報保存)
- [ ] ε 検証: G→F→G = id (構造保存)
- [ ] Drift 測定: 1-ε の許容範囲内
- [ ] 構造整合性確認

## Phase 5: 行動提案

- [ ] 実装すべき変更のリスト
- [ ] 優先順位付け
- [ ] 見積もり

## Phase 6: 反芻

- [ ] 消化プロセスの振り返り
- [ ] 信念更新 (/dox)
- [ ] 知識永続化 (/epi)"""


def phase_digest(report: 'ResearchReport', depth: str = "quick") -> Path | None:
    """Phase 4b: Write research results to Digestor incoming.

    Creates an eat_*.md file in incoming/ compatible with the /eat workflow.

    Args:
        report: Completed research report.
        depth: Template depth — "quick" (/eat-), "standard" (/eat), "deep" (/eat+).

    Returns:
        Path to the created file, or None on failure.
    """
    try:
        incoming_dir = INCOMING_DIR
        incoming_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        safe_query = "".join(
            ch if ch.isalnum() or ch in "-_ " else ""
            for ch in report.query[:40]
        ).strip().replace(" ", "_")
        filename = f"eat_{timestamp}_periskope_{safe_query}.md"
        filepath = incoming_dir / filename

        if filepath.exists():
            logger.info("Digest file already exists: %s", filename)
            return filepath

        # Build synthesis content
        synth_content = ""
        confidence = 0.0
        for s in report.synthesis:
            synth_content += s.content + "\n\n"
            confidence = max(confidence, s.confidence)

        # Citation summary
        citation_lines = []
        for c in report.citations:
            score = f"{c.similarity:.0%}" if c.similarity is not None else "—"
            citation_lines.append(
                f"| {c.claim[:50]}... | {c.taint_level.value} | {score} |"
            )
        citation_table = ""
        if citation_lines:
            citation_table = (
                "| Claim | Level | Score |\n"
                "|:------|:------|------:|\n"
                + "\n".join(citation_lines[:10])
            )

        # Decision Frame (Φ4)
        decision_frame_md = ""
        if report.decision_frame:
            df = report.decision_frame
            decision_frame_md = "## Φ4 Decision Frame\n\n"
            if df.key_findings:
                decision_frame_md += "### Key Findings\n"
                decision_frame_md += "\n".join(f"- {f}" for f in df.key_findings)
                decision_frame_md += "\n\n"
            if df.open_questions:
                decision_frame_md += "### Open Questions\n"
                decision_frame_md += "\n".join(f"- ❓ {q}" for q in df.open_questions)
                decision_frame_md += "\n\n"
            if df.decision_options:
                decision_frame_md += "### Decision Options\n"
                decision_frame_md += "\n".join(f"- ➡️ {o}" for o in df.decision_options)
                decision_frame_md += "\n\n"
            decision_frame_md += f"**Confidence**: {df.confidence:.0%}\n\n"

        # Source count
        sources_str = ", ".join(
            f"{k}: {v}" for k, v in report.source_counts.items()
        )

        # Depth-dependent sections
        if depth == "deep":
            phase_template = deep_template()
        elif depth == "standard":
            phase_template = standard_template()
        else:
            phase_template = quick_template()

        content = f"""---
title: "Periskopē: {report.query[:60]}"
source: periskope
url: N/A
score: {confidence:.2f}
matched_topics: [periskope_research]
digest_to: []
generated: {timestamp}
depth: {depth}
---

# /eat 候補: Periskopē Research — {report.query[:60]}

> **Confidence**: {confidence:.0%} | **Sources**: {sources_str}
> **Elapsed**: {report.elapsed_seconds:.1f}s | **Results**: {len(report.search_results)}
> **Depth**: {depth} | **Auto-generated by Periskopē → /eat auto-digest**

## Synthesis

{synth_content.strip()}

## Citation Verification

{citation_table or '(no citations verified)'}

{decision_frame_md}

{phase_template}

---

*Auto-generated by Periskopē auto-digest ({timestamp}, depth={depth})*
*消化するには: `/eat` で読み込み、上記のテンプレートに従って統合*
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    except Exception as e:  # noqa: BLE001
        logger.error("Auto-digest failed: %s", e)
        return None
