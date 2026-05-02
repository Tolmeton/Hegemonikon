# Handoff: Paper III α-τ 対応 + 実験的検証 + 止揚

**Session**: 2026-03-31 PM
**Status**: 理論構築→批判→止揚→実験→実験批判→再実験 の全サイクル完了

---

## 完了タスク

| ID | 成果 | 記載先 |
|:---|:-----|:-------|
| T-001 | α(ρ) = A·sgn(ρ-τ)·√\|ρ-τ\| 導出 | Paper III §4.8 |
| T-002 | E9-E12 統合。ker(G) = ノイズ空間 (座標無相関) | PINAKAS note |
| T-003 | E14 Description CI + E14b 3ドメイン CI 全 PASS | linkage_crystallization.md |
| T-004 | 定理 5.5.1 Copy-Computability 対応 | Paper III §5.5 |

## 止揚 (/exe → /dio)

/exe で §4.8 + §5.5 に W1-W5 の構造的欠陥を発見。記述を弱めず止揚:

| W | 問題 | 止揚 |
|:--|:-----|:-----|
| W1 | λ_eff = C·η(ρ) が heuristic | → **定理 4.8.1 (勾配降下-曲率同一性)**: d(G∘F) = I - μ·g⁻¹Hess(F) から η = μ·λ_eff を導出 |
| W2 | λ_mass = 0 が循環的 | → §4.4 Landau-Ginzburg 臨界条件 α(τ)=0 の帰結 |
| W3+W4 | NP 記述が不正確 | → 因果連鎖 copy→単調→収縮→P を補題分離。NP は脚注で正確化 |
| W5 | sgn 未導出 | → §4.4 曲率選択則 + §4.5 定理 4.5.1 経由で sgn(α) = sgn(ρ-τ) |

## 実験的検証

### E11 (13 sessions) フィット → /exe で批判 → E11b (30 sessions) で再検証

| 指標 | E11 (13 sess, G∘F) | E11b (30 sess, 1-pass) |
|:-----|:-------------------|:-----------------------|
| R²_uw | 0.969 | 0.928 |
| R²_w (逆分散) | 0.854 | 0.719 |
| β_crit (full) | 0.600 | **1.082** |
| β_crit (excl sat) | 0.875 | **1.363** |
| Session CV | 48% | **31%** (改善) |
| CI CV | 0.44% | 5.74% (G∘F なしで悪化) |

**核心の発見**:
1. β_crit = 0.600 は飽和 + 小サンプルの artifact。30 sessions では β ≈ 1.0
2. **CI は G∘F の性質** — G∘F を除去すると CI CV が 0.44% → 5.74% に一桁悪化
3. β_crit は [0.5, 1.4] の範囲制約のみ。精密値は現データからは決定不能
4. τ_c = 0.62 ± 0.02 (μ_noise と一致、ただし事後最適化)

## 次セッションで必要なこと

### 最優先: G∘F ありの 30-session E11b
- embedding_cache_100.pkl (30 sess, 6053 steps) を chunk_session() で τ sweep
- 今回 NaN が出た原因: Step オブジェクトの互換性。cache 内の steps が chunk_session の期待する型と不一致
- 修正方法: hyphe_chunker.py の Step 型を確認し、cache のデータ構造を合わせる

### 次優先
- W1 の定理 4.8.1 をさらに強化: Possati (2025) の変調降下則 μ = (1-ρ) を定理に組込み、μ を ρ の関数にする (現在は局所定数近似)
- session-level フィット: 13 or 30 の各セッション個別に R² を出し、集団平均と分離

## 変更ファイル一覧

| ファイル | 変更 |
|:---------|:-----|
| paper_III_draft.md | §4.8 (定理 4.8.1 昇格 + α² 導出 + 平方根則 + sgn 導出 + E11/E11b フィット), §5.5 (Copy-Computability 補題分離 + NP 脚注) |
| ckdf_theory.md | §10 逆参照 4行追記 |
| linkage_crystallization.md | E14 結果 + E14b 3ドメイン CI (別セッションで追記済み) |
| rho_judge.py | model: gemini-2.0-flash → gemini-2.5-flash |
| PINAKAS_TASK.yaml | T-001~T-004 done |
| e3_description_results.json | E14 120点 |
| e11b_30session_results.json | E11b 30-session 1-pass 結果 |
| cache_e3_*.json (15 files) | LLM-as-judge キャッシュ |

---

*Created: 2026-03-31 | Session: AY-5*
