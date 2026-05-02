# SE Principles — Structural Enforcement 原則

## 概要

Hegemonikón における設計・実装の基本原則。

---

## SE-1: PROOF (存在証明)

すべてのファイルは存在理由を持つ。

```text
assertion: ∀ file ∃ reason
```

---

## SE-2: DRY (Don't Repeat Yourself)

情報源は唯一であるべき。

```text
assertion: ∀ info ∃! source
```

---

## SE-3: YAGNI (You Aren't Gonna Need It)

必要になるまで作らない。

```text
assertion: ∀ feature → justification
```

---

## SE-4: KISS (Keep It Simple, Stupid)

シンプルを保つ。

```text
assertion: complexity < threshold
```

---

## SE-5: Observability (可観測性)

状態は常に検証可能であるべき。

```text
assertion: ∀ state → verifiable
```

---

## SE-6: Scalable Foundation (スケーラブル土台) 🆕

**定義**: 土台の美しさは、そこから派生可能なものの総量と土台自身のシンプルさの比で測られる。

```text
美(F) = lim[n→∞] Σ 派生(F, n) / cost(F)
```

**公理**:

- 技術的負債 = 0 (必須条件)
- 対処療法 = 美しくない
- スケールし続ける設計

**テスト**:

```yaml
question: "新規追加時の工数は O(1) か？"
pass: "1行追加 + 1コマンドで完了"
fail: "複数箇所の手動更新が必要"
```

**例証**:

- CCL: 1記法 → 245派生
- 定理体系: 1公理 + 7座標 → 24定理 → 209実装
- THEOREM_MAP: 1テーブル → 全双方向リンク

**CCL表記**: `/mek.sfp`

---

## 適用ガイドライン

| 原則 | 確認タイミング | 違反時の対応 |
|:-----|:---------------|:-------------|
| SE-1 | ファイル追加時 | PROOF注釈追加 |
| SE-2 | 情報重複検出時 | 単一情報源化 |
| SE-3 | 機能追加時 | 必要性証明 |
| SE-4 | 複雑化検出時 | 分割/簡素化 |
| SE-5 | 状態変更時 | 検証手段追加 |
| SE-6 | 設計決定時 | スケール性検証 |
