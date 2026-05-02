#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- scripts/
# PURPOSE: Forge トリガー定義のリファインメント
"""
Forge モジュールの activation_triggers を精緻化
PURPOSE: "general" のままの triggers を具体的キーワードに置き換え
"""

import os
import yaml

FORGE_BASE = os.path.expanduser(
    "~/Sync/10_📚_ライブラリ｜Library/prompts/templates/forge"
)

# Forge ファイル名 → 具体的な triggers マッピング
FORGE_TRIGGERS = {
    # 01_find
    "脳内を吐き出す": ["吐き出す", "ブレインダンプ", "整理", "頭の中", "dump", "zet"],
    "情報を集める": ["情報", "収集", "リサーチ", "調べる", "gather", "sop"],
    "声を聞く": ["聞く", "傾聴", "ヒアリング", "意見", "listen"],
    "頭を切り替える": ["切り替え", "リフレッシュ", "行き詰まり", "switch"],
    "全体を眺める": ["全体", "俯瞰", "マップ", "鳥の目", "overview", "pan"],

    # 02_think_expand
    "状況を把握する": ["状況", "現状", "把握", "分析", "what_is", "kho"],
    "問題を特定する": ["問題", "課題", "特定", "定義", "problem", "zet"],
    "関係者を整理する": ["関係者", "ステークホルダー", "利害", "stakeholder", "kho"],
    "前提を疑う": ["前提", "仮定", "バイアス", "疑う", "assumption", "noe"],
    "アイデアを出す": ["アイデア", "発想", "ブレスト", "創造", "ideate", "zet"],
    "点をつなぐ": ["つなぐ", "結合", "関連", "パターン", "connect", "gno"],
    "逆転させる": ["逆転", "反転", "逆から", "invert", "noe"],
    "揺らぎを与える": ["ランダム", "揺らぎ", "偶然", "刺激", "randomize", "zet"],
    "前提を破壊する": ["破壊", "ゼロベース", "非連続", "disrupt", "noe"],

    # 03_think_focus
    "選択肢を比較する": ["比較", "選択", "どっち", "compare", "dia"],
    "決断を下す": ["決断", "決める", "決定", "decide", "dia"],
    "計画を立てる": ["計画", "プラン", "段取り", "plan", "hod"],
    "リスクを見積もる": ["リスク", "危険", "見積もり", "risk", "pre"],
    "優先順位をつける": ["優先", "順位", "重要度", "prioritize", "met"],
    "やめる決断をする": ["やめる", "中止", "撤退", "quit", "dia"],
    "未来を分岐させる": ["未来", "シナリオ", "分岐", "scenario", "euk"],
    "ボトルネックを突く": ["ボトルネック", "制約", "TOC", "constraint", "met"],
    "本質だけ残す": ["本質", "削ぎ落とす", "シンプル", "essential", "met"],
    "テコを見つける": ["テコ", "レバレッジ", "最小努力", "leverage", "met"],
    "悪魔の代弁をする": ["反論", "批判", "devil", "代弁", "dia"],

    # 04_act_prepare
    "働きかける": ["行動", "実行", "動く", "act", "pra"],
    "断る": ["断る", "NO", "拒否", "say_no", "pra"],
    "交渉する": ["交渉", "ネゴ", "合意", "negotiate", "pra"],
    "演じる": ["ロールプレイ", "演じる", "シミュレーション", "roleplay", "syn"],
    "クエスト化する": ["ゲーミフィケーション", "クエスト", "動機", "gamify", "pra"],
    "環境をデザインする": ["環境", "仕組み", "自動化", "environment", "kho"],
    "任せる": ["委託", "デレゲーション", "任せる", "delegate", "pra"],

    # 05_act_create
    "文章を書く": ["文章", "書く", "ライティング", "write", "pra"],
    "プレゼンを作る": ["プレゼン", "発表", "スライド", "present", "pra"],
    "仕組み化する": ["仕組み", "システム化", "自動", "systemize", "mek"],
    "名前をつける": ["命名", "名前", "ネーミング", "name", "noe"],
    "手順を組む": ["手順", "SOP", "マニュアル", "procedure", "mek"],
    "図解する": ["図解", "ビジュアル", "図", "visualize", "pra"],
    "プロトタイプを作る": ["プロトタイプ", "試作", "MVP", "prototype", "ene"],

    # 06_reflect
    "品質を確かめる": ["品質", "品質確認", "チェック", "quality", "dia"],
    "改善案を出す": ["改善", "カイゼン", "より良く", "improve", "zet"],
    "経験を振り返る": ["振り返り", "レトロスペクティブ", "教訓", "retrospect", "gno"],
    "記録する": ["記録", "保存", "アーカイブ", "archive", "dox"],
    "賢人に聞く": ["賢人", "助言", "メンター", "counsel", "syn"],
}


def refine_triggers():
    updated = 0
    for root, dirs, files in os.walk(FORGE_BASE):
        for f in files:
            if not f.endswith('.md'):
                continue

            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()

            if not content.startswith('---'):
                continue

            end = content.find('---', 3)
            if end == -1:
                continue

            yaml_str = content[3:end].strip()
            body = content[end + 3:]

            try:
                fm = yaml.safe_load(yaml_str)
            except yaml.YAMLError:
                continue

            if not isinstance(fm, dict):
                continue

            # ファイル名からキーを推定
            name_clean = fm.get('name', '').replace('Forge: ', '')
            triggers = fm.get('activation_triggers', [])

            # "general" のみの場合、または改善可能な場合
            if name_clean in FORGE_TRIGGERS:
                new_triggers = FORGE_TRIGGERS[name_clean]
                fm['activation_triggers'] = new_triggers

                yaml_out = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                new_content = f"---\n{yaml_out.strip()}\n---{body}"

                with open(path, 'w', encoding='utf-8') as fp:
                    fp.write(new_content)

                rel = os.path.relpath(path, FORGE_BASE)
                print(f"  ✅ {rel}: {name_clean} → {new_triggers[:3]}...")
                updated += 1

    print(f"\n✅ {updated} Forge モジュール triggers 精緻化完了")


if __name__ == "__main__":
    refine_triggers()
