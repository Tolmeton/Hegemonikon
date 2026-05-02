#!/usr/bin/env python3
"""
ワークフロー命名規則ドキュメントの自動更新スクリプト

Usage:
    python nous/scripts/update-workflow-registry.py

機能:
    - nous/workflows/ 内の全ワークフローをスキャン
    - フロントマターから description, modules, pair を抽出
    - nous/docs/workflow-naming-convention.md の τ層セクションを更新
"""

import re
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"
CONVENTION_FILE = Path(__file__).parent.parent / "docs" / "workflow-naming-convention.md"

# τ層の定義（3-4文字）
TAU_COMMANDS = {
    "boot", "bye", "dev", "exp", "hist", "now", "plan", "pri", 
    "rec", "rev", "sop", "src", "vet", "why"
}


def parse_frontmatter(content: str) -> dict:
    """YAML フロントマターを解析"""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    
    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            # リスト形式の処理
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1].replace(' ', '')
            frontmatter[key] = value
    
    return frontmatter


def scan_workflows() -> list[dict]:
    """全ワークフローをスキャンしてメタデータを収集"""
    workflows = []
    
    for file in sorted(WORKFLOWS_DIR.glob("*.md")):
        cmd = file.stem
        
        # τ層のみ対象
        if cmd not in TAU_COMMANDS:
            continue
        
        content = file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)
        
        workflows.append({
            "cmd": f"/{cmd}",
            "modules": meta.get("modules", "-"),
            "description": meta.get("description", "-"),
            "pair": meta.get("pair", "-")
        })
    
    return workflows


def generate_table(workflows: list[dict]) -> str:
    """Markdownテーブルを生成"""
    lines = ["| cmd | modules | description | pair |"]
    lines.append("|:----|:--------|:------------|:-----|")
    
    for wf in workflows:
        # description を短縮
        desc = wf["description"]
        if len(desc) > 60:
            desc = desc[:57] + "..."
        
        lines.append(f"| `{wf['cmd']}` | {wf['modules']} | {desc} | `{wf['pair']}` |")
    
    return '\n'.join(lines)


def update_convention_file(table: str):
    """命名規則ファイルのτ層セクションを更新"""
    content = CONVENTION_FILE.read_text(encoding='utf-8')
    
    # AUTO_GENERATED マーカー間を置換
    pattern = r'(<!-- AUTO_GENERATED_START -->)\n.*?\n(<!-- AUTO_GENERATED_END -->)'
    replacement = f'\\1\n{table}\n\\2'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Last updated を更新
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    new_content = re.sub(
        r'\*Last updated: .*\*',
        f'*Last updated: {today}*',
        new_content
    )
    
    CONVENTION_FILE.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated: {CONVENTION_FILE}")


def main():
    print("🔍 Scanning workflows...")
    workflows = scan_workflows()
    print(f"   Found {len(workflows)} τ-layer workflows")
    
    print("📝 Generating table...")
    table = generate_table(workflows)
    
    print("💾 Updating convention file...")
    update_convention_file(table)
    
    print("\n📋 τ層ワークフロー一覧:")
    for wf in workflows:
        print(f"   {wf['cmd']}: {wf['modules']}")


if __name__ == "__main__":
    main()
