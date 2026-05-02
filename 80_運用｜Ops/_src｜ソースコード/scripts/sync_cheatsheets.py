#!/usr/bin/env python3
"""
HGK チートシート自動更新スクリプト (v1.0)
nous/workflows/ 配下の .md ファイルをスキャンし、HGK_WF_Cheatsheet_v4.1.md に
未記載のワークフローがあれば「Auto-Discovered Workflows」セクションに自動追記する。
"""

import os
import glob

# Paths
CHEATSHEET_PATH = os.path.expanduser("~/oikos/01_ヘゲモニコン｜Hegemonikon/nous/docs/HGK_WF_Cheatsheet_v4.1.md")
WORKFLOWS_DIR = os.path.expanduser("~/oikos/01_ヘゲモニコン｜Hegemonikon/nous/workflows")

def parse_frontmatter(filepath):
    """YAML frontmatterからdescriptionを抽出する"""
    desc = "No description"
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines or not lines[0].startswith('---'):
            return desc
        for line in lines[1:]:
            if line.startswith('---'):
                break
            if line.startswith('description:'):
                # description: "..." のクォートを外す
                desc = line.split('description:', 1)[1].strip().strip('"\'')
                break
    return desc

def main():
    if not os.path.exists(CHEATSHEET_PATH):
        print(f"❌ Cheatsheet not found at {CHEATSHEET_PATH}")
        return

    # 1. 既存チートシートの読み込み
    with open(CHEATSHEET_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. 全ワークフローファイルの抽出
    wf_files = glob.glob(os.path.join(WORKFLOWS_DIR, "*.md"))
    
    missing_wfs = []
    for wf_path in wf_files:
        basename = os.path.basename(wf_path).replace('.md', '')
        wf_cmd = f"/{basename}"
        
        # チートシート内にコマンド文字列が存在するかチェック
        if wf_cmd not in content:
            desc = parse_frontmatter(wf_path)
            missing_wfs.append({
                'cmd': wf_cmd,
                'desc': desc
            })
            
    if not missing_wfs:
        print("✅ すべてのワークフローはチートシートに記載済みです。")
        return

    print(f"🔄 未記載のワークフローを {len(missing_wfs)} 件発見しました。チートシートを更新します...")
    
    # 3. 自動追記ブロックの作成
    auto_block = "\n## 🔄 Auto-Discovered Workflows (自動検知)\n\n"
    auto_block += "> ⚠️ 以下のワークフローは `nous/workflows/` から自動検知されました。適切なセクションに手動で移動・統合してください。\n\n"
    auto_block += "| コマンド | 概要 |\n"
    auto_block += "|:---------|:-----|\n"
    for wf in missing_wfs:
        auto_block += f"| `{wf['cmd']}` | {wf['desc']} |\n"
    auto_block += "\n"

    # 4. 「関連チートシート」の直前（またはファイルの末尾）に挿入/置換
    marker = "## 🔗 関連チートシート"
    old_marker = "## 🔄 Auto-Discovered Workflows (自動検知)"
    
    # 既に自動検知ブロックがある場合は、それをまるごと置換する
    if old_marker in content:
        parts = content.split(old_marker)
        before_old = parts[0]
        after_old = parts[1]
        
        if marker in after_old:
            parts2 = after_old.split(marker)
            rest = marker + parts2[1]
            content = before_old + auto_block + rest
        else:
            content = before_old + auto_block
    else:
        # 新規作成: 関連チートシートの直前に挿入
        if marker in content:
            content = content.replace(marker, auto_block + marker)
        else:
            content += auto_block

    # 5. 上書き保存
    with open(CHEATSHEET_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ {CHEATSHEET_PATH} の自動更新が完了しました。")

if __name__ == "__main__":
    main()
