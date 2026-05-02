# Agora — Skill 配布フォーマット仕様

> SKILL.md 単体で動く設計。コピー1回で「使える」状態までもっていく。
> 消化元: `onboarding_strategy.md` §3 (Plugin = Skill 軽量版)

---

## 設計原則

| # | 原則 | 理由 |
|:--|:-----|:-----|
| 1 | **Single-file first** | コピー1回で動く。依存ゼロ |
| 2 | **Progressive enhancement** | scripts/ は任意。なくても動く |
| 3 | **Slash command 発動** | ユーザーは `/xxx` だけ覚えればいい |
| 4 | **自己記述的** | SKILL.md を読めば何ができるか全部わかる |

---

## 配布レイヤー (4-Tier)

```
T0: SKILL.md のみ (Single-file)
    └── 最低配布単位。これだけで動く
         ↓
T1: SKILL.md + examples/
    └── 使い方の具体例を同梱
         ↓
T2: SKILL.md + examples/ + scripts/
    └── 自動化スクリプト付き
         ↓
T3: SKILL.md + examples/ + scripts/ + REFERENCE.md
    └── 完全パッケージ。品質保証済み
```

---

## T0 SKILL.md 最小構造

```yaml
---
name: {Skill 名}
description: {1行の説明}
version: "1.0"
triggers:
  - "{発動キーワード1}"
  - "{発動キーワード2}"
---
```

```markdown
# {Skill 名}

## いつ使うか
{発動条件を1-3行で}

## 手順
1. {ステップ1}
2. {ステップ2}
3. {ステップ3}

## 出力フォーマット
{期待する出力の形}

## 制約
- {守るべきルール}
```

### T0 チェックリスト

- [ ] YAML frontmatter に `name`, `description`, `triggers` がある
- [ ] 手順が番号付きリストで書かれている
- [ ] 出力フォーマットが具体的に定義されている
- [ ] SKILL.md 単体でコピーして動作する
- [ ] triggers に日本語キーワードを含む (日本語ユーザー向け)

---

## 配布チャネル

| チャネル | 形式 | 対象 |
|:---------|:-----|:-----|
| GitHub Gist | 単一 .md | T0 (最速配布) |
| GitHub repo | ディレクトリ | T1-T3 |
| ZIP | アーカイブ | 非技術者向け |
| Agora マーケット (将来) | パッケージ | T2-T3 (品質保証済み) |

---

## 品質ゲート

Agora で公開する Skill は以下を満たすこと:

| レベル | 要件 | 検証方法 |
|:-------|:-----|:---------|
| **必須** | YAML frontmatter 完備 | 自動チェック |
| **必須** | 手順が3ステップ以上 | 目視 |
| **必須** | 出力フォーマット定義あり | 目視 |
| **推奨** | examples/ に実行例 1 つ以上 | 目視 |
| **推奨** | `/dok` で動作確認済み | 実行テスト |
| **上級** | Dendron PROOF ヘッダ付き | dendron_check |

---

*作成日: 2026-03-09 | 設計根拠: onboarding_strategy.md §3*
