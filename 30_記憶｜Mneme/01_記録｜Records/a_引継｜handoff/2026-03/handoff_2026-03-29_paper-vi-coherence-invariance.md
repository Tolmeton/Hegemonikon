# Handoff: Paper VI「行為可能性は忘却である」骨子 + 実験実装

**日時**: 2026-03-29
**セッション種別**: AY-2 Coherence Invariance の他ドメインへの転用
**V[session]**: 0.3

---

## S — Situation

AY-2 (Coherence Invariance の他ドメイン転用) に着手。Paper VI を立ち上げ、理論骨子 (§2.3 + §3) を精密化し、実験コードを実装した。パイロット実行で LLM-as-judge の ρ スコア分布問題を発見。

## B — Background

- AY-3 は別セッションで実行中 (Creator 指示)
- Paper II §1.1 は前セッションで d = ker(d) への商写像に精密化済み
- Hyphē PoC: 130+ 実験, τ-invariance 実証 (range = 0.008), ker(G) = {Scale, Valence}

## A — Assessment

### 主要成果

| # | 成果 | ファイル |
|:--|:--|:--|
| 1 | Paper VI §2.3 — d = ker(d) と G = ker(G) の構造的同型 (4サブセクション, 80行) | `drafts/paper_VI_draft.md` |
| 2 | Paper VI §3 — τ-invariance 十分条件 S1-S3 + 証明スケッチ (6サブセクション, 150行) | 同上 |
| 3 | ρ 測度抽象化 + LLM-as-judge 実装 + gf_iterate_with_rho | `HyphePoC/rho_judge.py` |
| 4 | Layer 2 実験ランナー (E2' Cognition + E3' Description + 分析) | `HyphePoC/run_paper_vi_experiment.py` |
| 5 | 2層実験設計書 (/exe W1-W5 修正済み) | `HyphePoC/EXPERIMENT_paper_vi.md` |

### 決定事項

| 決定 | 理由 | 却下肢 |
|:--|:--|:--|
| D1: 核心命題「忘却 (G) が行為可能性 (AY) を増大させる」 | 商写像は同値類を作り射を増やす = AY > 0。Paper II の d=ker(d) と同型 | G∘F の汎用性を核心に → Euporía 接続が弱い |
| D2: G∘F = 結晶化 (テキスト分割ではない) | Creator 4指摘。3ドメイン同型: Kalon な情報単位の演繹的生成 | Linkage = 簡単 / 他 = 難しい → ドメイン混同 |
| D3: 2層実験構造 | /exe が Hyphē そのままでは Linkage の再測定 (W1) と発見 | Layer 1 のみ → ドメイン混同未解決 |
| D4: LLM-as-judge をドメイン固有 ρ として使用 | S1 (共通測度条件) を満たす。embedding sim → ker(G) が Linkage と同一 (W5) | embedding sim のまま |
| D5: Cortex API (ochema) で judge 実行 | 接続確認済み。`CortexClient().ask(message=..., model='gemini-2.0-flash', max_tokens=10)` | direct Google API → scope 認証エラー |

### /exe 構造的欠陥 (5件) と修正

| # | 重要度 | 欠陥 | 修正 |
|:--|:--|:--|:--|
| W1 | 🔴 | Hyphē そのままでは Linkage の再測定 | Layer 2: LLM-as-judge ρ |
| W2 | 🔴 | τ = similarity threshold (depth/granularity ではない) | E2': depth = token budget / E3': granularity = 分割数 N |
| W3 | 🟡 | depth 離散3条件 | 5条件 (50/200/500/1000/2000 tokens) |
| W4 | 🟡 | granularity = 情報量変化 | 同一内容の分割数 N |
| W5 | 🟡 | ker(G) が Linkage と同一 | LLM-as-judge ρ |

### パイロット結果と未解決問題

```
E2' math task, 8 steps:
G∘F ON  range: 0.0714 (FAIL)  values: [1.0, 0.9286, 1.0, 1.0, 1.0]
G∘F OFF range: 0.0000          values: [1.0, 1.0, 1.0, 1.0, 1.0]
```

**問題**: judge が全ペアにほぼ 1.0 を返す。数学証明のステップ間 coherence が高すぎて ρ のバラつきが不足 → split 未発動。

**修正方針** (未実装):
1. judge プロンプトを direct logical dependency rubric に変更 (5段階: 0.0-0.2 / 0.3-0.4 / 0.5-0.6 / 0.7-0.8 / 0.9-1.0)
2. 多様なタスクでテスト (比較分析・創造タスクは非連続ステップが混在)
3. ρ 分布を G∘F 前に事前確認

### Creator の4指摘

1. **離散は幻想** → depth は連続量の恣意的離散化
2. **split = 忘却 = 力の生成** → G = 商写像 = 自由度の解放 (忘却論 Paper II と同型)
3. **統計で測れる** → 一般論での一貫性は統計的に問える
4. **Linkage も結晶化** → 3ドメイン同型

### 変更ファイル一覧

**新規**:
- `10_知性｜Nous/.../drafts/paper_VI_draft.md` — Paper VI 骨子 v0.1 (500行)
- `60_実験｜Peira/06_Hyphē実験｜HyphePoC/EXPERIMENT_paper_vi.md`
- `60_実験｜Peira/06_Hyphē実験｜HyphePoC/rho_judge.py`
- `60_実験｜Peira/06_Hyphē実験｜HyphePoC/run_paper_vi_experiment.py`
- `30_記憶｜Mneme/.../c_ROM｜rom/rom_2026-03-29_paper_vi_coherence_invariance.md`
- `30_記憶｜Mneme/.../c_ROM｜rom/rom_2026-03-29_paper_vi_experiment_impl.md`

**修正**:
- `10_知性｜Nous/.../TASKS_euporia_hyphe_fusion.md` — AY-2 状態「着手中」+ 成果物リンク

## R — Recommendation

### 次セッション (優先順序)

1. **judge プロンプト修正** — `rho_judge.py` L51-70 の `_JUDGE_PROMPTS["cognition"]` を 5段階 rubric に変更
2. **パイロット再実行** — math + compare + creative の3タスクで ρ 分散確認
3. **E2' 本実行** → **E3' 本実行** → Paper VI §5/§6 に結果記入
4. **Paper VI §4** (Linkage 130+ 実験まとめ — results_analysis.md から転載)

### 実行コマンド

```bash
cd "60_実験｜Peira/06_Hyphē実験｜HyphePoC"
python run_paper_vi_experiment.py --domain cognition --backend ochema
```

## Session Metrics

- WF: /boot×1, /noe+×1, /u+×1, /ske>>noe>>sag×1, /exe×1, /ene+×2, /rom×2, /bye×1
- コミット: 0 (次セッションで実験結果と合わせてコミット推奨)

## Self-Profile (id_R)

- Hyphē をそのまま使えば正しいと即断 → Creator 指摘 + /exe で破壊。「実装 = 理論」の短絡に注意
- LLM-as-judge の ρ 分布を事前確認せず G∘F を回した。次回は similarity_trace を先に表示

## SFBT 例外分析

1. Creator の4指摘を /u+ で前提再構築できた — 防御なく受容
2. /exe が W1 W2 を🔴として発見 — 実験前に構造的欠陥を捕捉
3. 再現条件: Creator の指摘 + /u+ 内省 + /exe 構造チェック

## 🧠 信念 (Doxa)

- **DX-new**: G∘F = 結晶化。3ドメイン同型。商写像は射を増やす = 忘却が行為可能性を生む
- **DX-new**: ker(G) の次元が τ-invariance 強度を予言する (Linkage 33% → range 0.008)

---

*R(S) 生成: 2026-03-29 — /bye v9.0-cc*
