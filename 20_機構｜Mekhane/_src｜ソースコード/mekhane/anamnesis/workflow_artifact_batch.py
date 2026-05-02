#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/
"""
PROOF: [L3/ユーティリティ]

S2 → ワークフローの標準化が必要
   → Artifact セクション一括追加
   → workflow_artifact_batch が担う

Q.E.D.

---

Batch add Artifact Auto-save section to all workflows.
Hegemonikón Workflow Artifact Standardization
"""

from pathlib import Path
from mekhane.paths import OUTPUTS_DIR

WORKFLOWS_DIR = Path("/home/makaron8426/Sync/oikos/nous/workflows")
STANDARD_REF = (
    "file:///home/makaron8426/Sync/oikos/nous/standards/workflow_artifact_standard.md"
)
MNEME_PATH = str(OUTPUTS_DIR)

# Workflows to update (exclude already done: noe, bou, zet, ene)
# Also exclude hub workflows: o, h, s, p, k, a, x
# Also exclude session workflows: boot, bye
# Also exclude dialogue/reference: u, dev
WORKFLOWS_TO_UPDATE = {
    # Methodos Series (S1-S4)
    "ske": ("S1 Skepsis", "探索破壊"),
    "sag": ("S2 Synagōgē", "最適統合"),
    "pei": ("S3 Peira", "実験検証"),
    "tek": ("S4 Tekhnē", "技法構築"),
    # Krisis Series
    "kat": ("Katalēpsis", "確定・対象固定"),
    "epo": ("Epochē", "判断留保"),
    "pai": ("Proairesis", "決断・資源投入"),
    "dok": ("Dokimasia", "打診・テスト"),
    # Diástasis Series
    "lys": ("Analysis", "局所分析"),
    "ops": ("Synopsis", "全体俯瞰"),
    "akr": ("Akribeia", "精密操作"),
    "arc": ("Architektonikē", "全体展開"),
    # Orexis Series
    "beb": ("Bebaiōsis", "信念肯定"),
    "ele": ("Elenchos", "批判・反証"),
    "kop": ("Prokopē", "推進・前進"),
    "dio": ("Diorthōsis", "是正・修正"),
    # Chronos Series
    "hyp": ("Hypomnēsis", "過去想起"),
    "prm": ("Promētheia", "未来予見"),
    "ath": ("Anatheōrēsis", "教訓抽出"),
    "par": ("Proparaskeuē", "事前準備"),
    # X-series
    "ax": ("X-analysis", "多層分析"),
    # Other
    "eat": ("Digestion", "消化結果"),
}

ARTIFACT_TEMPLATE = """
---

## Artifact 自動保存

> **標準参照**: [workflow_artifact_standard.md]({standard_ref})

### 保存先

```
{mneme_path}/{workflow}_<topic>_<date>.md
```

例: `{workflow}_{example_topic}_{date}.md`

### チャット出力規則

**チャットには最小限の出力のみ。詳細は全てファイルに保存。**

```text
✅ /{workflow} 完了
📄 /mneme/05_状態｜State/workflows/{workflow}_{{topic}}_{{date}}.md
要約: {{{summary_placeholder}}}
→ {{{{推奨次ステップ}}}}
```

### 保存する理由

1. **コンテキスト節約**: チャット履歴を汚さない
2. **参照可能**: {purpose}を後から確認できる
3. **蓄積可能**: パターン分析に活用

"""


# PURPOSE: Generate artifact section for a workflow.
def generate_section(
    workflow: str, module: str, summary: str, date: str = "20260129"
) -> str:
    """Generate artifact section for a workflow."""
    example_topic = summary.replace("・", "_").replace(" ", "_")[:20]
    return ARTIFACT_TEMPLATE.format(
        standard_ref=STANDARD_REF,
        mneme_path=MNEME_PATH,
        workflow=workflow,
        example_topic=example_topic,
        date=date,
        summary_placeholder=f"{summary}サマリー",
        purpose=summary,
    )


# PURPOSE: Find the line number to insert artifact section.
def find_insertion_point(content: str) -> int:
    """Find the line number to insert artifact section."""
    lines = content.split("\n")

    # Look for "## Hegemonikon Status" or "---" before it
    for i, line in enumerate(lines):
        if "## Hegemonikon Status" in line or "## Hegemonikón Status" in line:
            # Insert before the "---" that precedes this section
            if i > 0 and lines[i - 1].strip() == "---":
                return i - 1
            return i

    # If not found, look for last "---" before EOF
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "---":
            return i

    return len(lines)


# PURPOSE: Update a single workflow file with artifact section.
def update_workflow(workflow: str, module: str, summary: str) -> bool:
    """Update a single workflow file with artifact section."""
    filepath = WORKFLOWS_DIR / f"{workflow}.md"

    if not filepath.exists():
        print(f"  ⚠️ {workflow}.md not found")
        return False

    content = filepath.read_text()

    # Skip if already has artifact section
    if "## Artifact 自動保存" in content or "Artifact 自動保存" in content:
        print(f"  ⏭️ {workflow}.md already has artifact section")
        return True

    # Skip if has old artifact section that needs manual update
    if "Artifact 出力保存規則" in content or "出力保存規則" in content:
        print(f"  ⚠️ {workflow}.md has old section - needs manual update")
        return False

    # Generate new section
    section = generate_section(workflow, module, summary)

    # Find insertion point
    lines = content.split("\n")
    insert_idx = find_insertion_point(content)

    # Insert section
    new_lines = lines[:insert_idx] + section.split("\n") + lines[insert_idx:]
    new_content = "\n".join(new_lines)

    # Write back
    filepath.write_text(new_content)
    print(f"  ✅ {workflow}.md updated")
    return True


# PURPOSE: CLI エントリポイント — 知識基盤の直接実行
def main():
    print("🚀 Hegemonikón Workflow Artifact Standardization")
    print(f"📁 Target: {WORKFLOWS_DIR}")
    print(f"📦 Workflows to update: {len(WORKFLOWS_TO_UPDATE)}")
    print()

    success = 0
    skipped = 0
    failed = 0

    for workflow, (module, summary) in WORKFLOWS_TO_UPDATE.items():
        result = update_workflow(workflow, module, summary)
        if result:
            success += 1
        else:
            failed += 1

    print()
    print(f"📊 Results: {success} updated, {failed} failed/needs manual")


if __name__ == "__main__":
    main()
