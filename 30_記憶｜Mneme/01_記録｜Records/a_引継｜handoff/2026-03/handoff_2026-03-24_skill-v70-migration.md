# Handoff: SKILL v7.0 移行 — I/A 象限 24動詞完了

**日付**: 2026-03-24 12:28 JST
**セッションID**: 713fff32-fe86-4efe-8a59-64535790bf34
**Agent**: Claude (Antigravity)

## S — 状況

HGK SKILL フレームワークの Týpos v8.4 移行作業。I/A 象限 24動詞の v7.0 化を完了させるセッション。

## B — 背景

- Diástasis 族 (V13-V16) は前セッションで v7.0 化済み
- 並行セッション群で Telos/Methodos/Orexis/Chronos の一部が既に v7.0 に到達していた
- 残りの差分適用 (U⊣N + ρ_hard/soft + Phase-U) が本セッションの目的

## A — 実施内容

### 1. V03 /zet (Telos 族) — v6.0 → v7.0
- **U⊣N 5種追加**: 即検索/表層問い/迎合採用(CD-5)/検索偽装/フレーム内問い
- **ρ 2層設計**: ρ_hard (3極欠損+Kill基準違反+産婆術違反) / ρ_soft (問いの種不足)
- **Phase-U**: P-0=U₃ / P-1=U₀+U₁ / P-2=U₄ / P-4=U₂
- **PQS⊥ρ**: ZQS品質×ρ_hard で /noe 遷移判定
- 507行 → 531行 (+5%)

### 2. Krisis 族 (V09-V12) — v6.0 → v7.0

| 動詞 | 追加内容 |
|:--|:--|
| V09 /kat | U⊣N 5種 (即断/確証バイアス/確信度歪み/迎合確定/形式的反証) + Phase-U |
| V10 /epo | Phase-U 明示化 (U_dogma等は既にPhase名に埋込済み) |
| V11 /pai | U⊣N 5種 (Hormē/サンクコスト/総花主義/楽観バイアス/撤退回避) + Phase-U |
| V12 /dok | U⊣N 5種 (過大打診/曖昧基準/主観的観察/ゴールポスト移動/不可逆性過小評価) + Phase-U |

> V09/V11 は version が並行セッションで既に v7.0.0 に更新済みだった。U⊣N + Phase-U の差分のみ適用。

### 3. Chronos 族 (V21-V24) — 既に v7.0 (並行セッション完了)
- 全4動詞が U⊣N + Phase-U 込みで v7.0.0 を確認。差分適用不要。

## R — 推奨

### 完了状態
```
I/A 象限 24/24 動詞 = v7.0+
├ Telos (V01-V04)     ✅ v7.0+ (V01 は v9.4.0)
├ Methodos (V05-V08)  ✅ v7.0
├ Krisis (V09-V12)    ✅ v7.0 ← 今回
├ Diástasis (V13-V16) ✅ v7.0 ← 前回
├ Orexis (V17-V20)    ✅ v7.0
└ Chronos (V21-V24)   ✅ v7.0 (並行完了)
```

### 未踏
- **S-series (V25-V36)**: 12動詞が v1-3 の旧世代。並行セッション群で進行中と推定される
- V13 /lys の rubric 修正を Creator が手動で適用 ("Quadrant Deep Dive" → "Emergent Dimension Deep Dive")

### 変更ファイル一覧
- `V03_探求｜Zetesis/SKILL.md` — v6.0 → v7.0
- `V09_確定｜Katalepsis/SKILL.md` — U⊣N + Phase-U 追加
- `V10_留保｜Epoche/SKILL.md` — Phase-U + version + Status 更新
- `V11_決断｜Proairesis/SKILL.md` — U⊣N + Phase-U 追加
- `V12_打診｜Dokimasia/SKILL.md` — U⊣N + Phase-U 追加
