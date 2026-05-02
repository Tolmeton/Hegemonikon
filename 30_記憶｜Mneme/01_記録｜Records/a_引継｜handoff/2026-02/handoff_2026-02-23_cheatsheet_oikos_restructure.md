# Handoff — 2026-02-23 チートシート改善 + oikos 引越し

> **Session ID**: 64609c84-259f-40ec-ba2e-356482782302
> **日時**: 2026-02-23 17:30 ~ 21:36 JST
> **Agent**: Claude (Antigravity)

---

## 🎯 達成したこと

### 1. HGK WF チートシート v4.1 完全改訂

- **`<details>` → Obsidian Callout** (`> [!abstract]-`) に変換。折りたたみ + Markdown レンダリングが正常動作
- **24動詞全てに Phase ごとの詳細説明** (各5-7段落) を追加
- **Wikilink** (`[[noe]]`, `[[bou]]` 等) でクリック→WF定義が直接開ける
- **τ層・CCLマクロにも正本リンク** を追加
- **出力**: `~/oikos/hegemonikon/nous/docs/HGK_WF_Cheatsheet_v4.1.md`

### 2. oikos → Sync 引越し (大規模ファイルシステム再構成)

| 変更 | 詳細 |
|:-----|:-----|
| `~/oikos` → `~/Sync/oikos` | 全プロジェクトを Syncthing 管理下に移動 |
| `~/oikos` | symlink → `~/Sync/oikos` (後方互換) |
| `.stignore` | .venv, **pycache**, .git/objects 等を同期除外 |

### 3. Nous テキスト層の分離

hegemonikon 内のテキスト系コンテンツを `nous/` に集約:

| nous/ に移動 | 内容 |
|:-------------|:-----|
| `workflows/` | 89 WF 定義 |
| `rules/` | 28 BC/安全ルール |
| `skills/` | 35 Skill 定義 |
| `kernel/` | SACRED_TRUTH, 公理体系 |
| `docs/` | チートシート, READMEs |
| `handoffs/`, `templates/`, `standards/`, `tape/` | 記憶・テンプレート |

`.agent/` 内の symlink が `nous/` を指すよう更新。コード (mekhane, hermeneus, hgk) はそのまま。

### 4. Sync 統合

- 全番号付きフォルダ (`00_仮置き` ~ `90_保管庫`) を `oikos/` 内に移動
- `15_ヘゲモニコン｜Hegemonikon` に正式リネーム + `hegemonikon` symlink で後方互換
- `.obsidian/` を `oikos/` 内に移動 (oikos = Obsidian ボールトルート)
- 旧 `15_ヘゲモニコン｜Hegemonikon/` (Sync直下) を削除

---

## 🏗️ 最終構造

```
~/Sync/                                    ← Syncthing ルート
├── .stignore
└── oikos/                                 ← 家 (= Obsidian ボールト)
    ├── 00_仮置き｜Inbox/
    ├── 10_ライブラリ｜Library/
    ├── 15_ヘゲモニコン｜Hegemonikon/       ← 実体
    │   ├── nous/                          ← テキスト層
    │   │   ├── workflows/ (89 WF)
    │   │   ├── rules/ (28 rules)
    │   │   ├── skills/ (35 skills)
    │   │   ├── kernel/ (SACRED_TRUTH等)
    │   │   └── docs/ (チートシート等)
    │   ├── mekhane/                        ← コード層 (暗黙のsoma)
    │   ├── hermeneus/
    │   ├── hgk/
    │   └── .agent/ → nous/ (symlinks)
    ├── 20_作業場｜Workspace/
    ├── 30_スクリーンショット｜Screenshots/
    ├── 90_保管庫｜Archive/
    ├── hegemonikon → 15_ヘゲモニコン｜Hegemonikon  ← 後方互換
    └── .obsidian/

~/oikos → ~/Sync/oikos                     ← 後方互換
```

---

## ⚠️ 未完了・注意事項

1. **`.stignore` が未適用の可能性あり** — ターミナルハングのため手動貼り付け済みか不明。確認: `cat ~/Sync/.stignore`
2. **Windows 側の同期確認** — Syncthing が新構造を正しく同期しているか確認
3. **Antigravity IDE workspace** — パス変更不要 (symlink で吸収済み) だが、IDE 再起動後の動作確認推奨
4. **G Drive バックアップ** — 不要という結論。Syncthing の P2P 同期で十分
5. **nous/docs/ 内に Python スクリプト混入** (`enrich_*.py`, `generate_wf_data.py` 等) — 旧 `15_ヘゲモニコン` から移動された。コード層に移すべき

---

## 💡 設計判断の記録

| 判断 | 理由 |
|:-----|:-----|
| soma/ は明示的に作らない | Python import パスが全壊するため。コードはそのまま hegemonikon/ 直下に残し「nous/ 以外 = soma」|
| hegemonikon symlink で後方互換 | 15_ヘゲモニコン｜Hegemonikon への全パス参照を壊さないため |
| .env は Sync に含める | P2P 暗号化で自分のマシン間のみ。API キー再設定の手間を省く |
| Obsidian callout (`> [!abstract]-`) | `<details>` は Obsidian で Markdown レンダリングが効かないため |

---

## 📊 セッション統計

- 開始: 17:30 JST (チートシート改善)
- 終了: 21:36 JST (約4時間)
- git diff: 903 files changed, 48765 insertions, 3832 deletions (大半はファイルシステム再構成)

---

*Handoff generated: 2026-02-23T21:36 JST*
