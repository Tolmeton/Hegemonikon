# SWE-bench 全件検証 (N=80,036) — データパイプライン設計書

**Version:** v0.1 (計画策定段階)
**依存:** Paper IV (効果量減衰定理 v0.1), Paper I §5.5 (選択的忘却定理, N=416 統制実験)

---

## §1. 目的

Paper IV 定理 3.1.1 (効果量減衰定理) の全件検証を行う。

**中核仮説:** SWE-bench 全件 (N=80,036) において、忘却スペクトラム指標 Ξ_Gini とタスク成功 P の間に r ≈ 0.1 (95% CI 推定幅 ±0.007) の正の相関が検出される。

**副次目標:**
1. Paper IV §6.2 の4つの予測 (P-IV.1〜P-IV.4) の検証
2. r ≈ 0.1 の解釈弁別: 解釈 A (忘却が成功を駆動) vs 解釈 C (交絡による疑似相関) の識別
3. 効果量減衰定理のパラメータ (ρ, K) の精密推定

---

## §2. 層別化 (サブグループ分析) 要件

### 2.1 第一層別軸: trajectory 長 T

Paper IV 予測 P-IV.2 の検証。

| サブグループ | T 範囲 | 予測 | 検証基準 |
|:--|:--|:--|:--|
| 短 trajectory | T < 10 | r ↓ (Ξ_Gini の推定精度低下) | r_short < r_full - 0.03 |
| 中 trajectory | 10 ≤ T ≤ 30 | r ≈ 0.1 (安定域) | |r_mid - r_full| < 0.02 |
| 長 trajectory | T > 30 | r 安定 (飽和) | |r_long - r_full| < 0.02 |

### 2.2 第二層別軸: タスク難度

タスク成功率 P̄ (全モデル平均) による層別。

| サブグループ | P̄ 範囲 | 予測 | 根拠 |
|:--|:--|:--|:--|
| 容易タスク | P̄ > 0.5 | r ≈ 0 (天井効果) | K_eff → 0: 忘却以外の要因でも成功 |
| 中間タスク | 0.1 ≤ P̄ ≤ 0.5 | r 最大 | 忘却パターンの差が最も弁別的 |
| 困難タスク | P̄ < 0.1 | r ↓ (床効果) | 忘却パターンだけでは不足 |

### 2.3 第三層別軸: 行動空間サイズ n

Paper IV 予測 P-IV.1 の検証。行動空間のサイズ proxy として修正ファイル数 + 修正行数を使用。

**予測:** r ∝ n_eff^{−1/2}。行動空間が大きいほど r は減衰する。

### 2.4 第四層別軸: モデルサイズ

Llama-70B / Llama-8B / その他のモデル間で ρ の差異を検出。

**予測:** 大モデルほど ρ が高い (忘却スペクトラムの表現力が豊か)。

---

## §3. 解釈 A/C 弁別のための評価メトリクス設計

### 3.1 問題設定

r ≈ 0.1 は以下の2つの解釈を許す:

- **解釈 A (因果):** 忘却パターン Ξ が直接的にタスク成功 P に因果的に寄与する。効果量減衰定理が正しく、真の内部相関 r_theory ≈ 0.75 が 2層の減衰を受けて r ≈ 0.1 として観測される。
- **解釈 C (交絡):** 第三変数 Z (例: モデルのタスク理解度) が Ξ と P の双方に影響し、疑似相関を生む。真の因果効果は 0 に近い。

### 3.2 弁別メトリクス

| メトリクス | 解釈 A 予測 | 解釈 C 予測 | 弁別力 |
|:--|:--|:--|:--|
| **M-1: 減衰構造テスト** | r(ρ↑) > r(ρ↓) かつ r(K↓) > r(K↑) | ρ, K に依存しない | 高 |
| **M-2: 全保持統制** | dΦ ≈ 0 で r ≈ 0 (Paper I 結果の再現) | 交絡で r > 0 残存 | 高 |
| **M-3: T 長プロファイル** | T < 10 で r ↓、T > 30 で飽和 | T に依存しないフラット | 中 |
| **M-4: 残差分析** | P ~ Z + Ξ で Ξ の偏回帰係数有意 | Z 投入後 Ξ 係数消失 | 高 |
| **M-5: Causal Forest** | 異質性検出: 忘却変動が大きいサブグループで効果増大 | 一様なゼロ効果 | 高 |

### 3.3 M-1 減衰構造テストの詳細

効果量減衰定理の核心的予測: r_obs = √ρ · r_theory / √(K+1)。

**手順:**
1. ρ を操作: observation 表現の次元 d_eff を変化させる (主成分数のカットオフ変更)
2. K を操作: 交絡因子を逐次統制 (回帰モデルへの段階的投入)
3. r_obs(ρ, K) の曲面を推定し、理論曲面 r = √ρ / √(K+1) との適合度を検定

**帰無仮説 (解釈 C):** r_obs は ρ, K に依存しない定数。
**対立仮説 (解釈 A):** r_obs は理論曲面に従う。

### 3.4 M-4 残差分析の詳細

交絡候補変数 Z:
1. Z₁: タスクの SLoC (ソースコード行数)
2. Z₂: テスト数 (テスト難度の proxy)
3. Z₃: リポジトリの star 数 (コード品質の proxy)
4. Z₄: issue の記述長 (仕様の明確さ)
5. Z₅: 修正に必要な diff サイズ
6. Z₆: プログラミング言語
7. Z₇: リポジトリのドメイン (web/ML/system/etc.)
8. Z₈: モデルサイズ

**階層的回帰:** P ~ Z₁ + ... + Z₈ + Ξ_Gini で Ξ_Gini の偏回帰係数の有意性を検定。

---

## §4. データパイプライン設計

### 4.1 パイプライン概要

```
[Stage 1] データ取得
  SWE-bench リポジトリ → 全件メタデータ (N=80,036)
  ↓
[Stage 2] Trajectory 生成
  各タスク × モデル → LLM trajectory (observation 列)
  ↓
[Stage 3] 特徴量抽出
  trajectory → Ξ_Gini + 交絡変数 Z₁-Z₈ + 成功/失敗 P
  ↓
[Stage 4] 統計分析
  主分析 (r 推定) + 層別分析 + A/C 弁別メトリクス
  ↓
[Stage 5] レポート生成
  Paper IV §7.1 への結果統合
```

### 4.2 Stage 1: データ取得

- ソース: `princeton-nlp/SWE-bench` (GitHub)
- フィールド: instance_id, repo, base_commit, patch, test_patch, problem_statement
- 推定サイズ: ~500MB (メタデータのみ)

### 4.3 Stage 2: Trajectory 生成

**最大コスト工程。** 各タスクに対して LLM を実行し trajectory を取得する。

| モデル | 推定コスト/タスク | N=80,036 合計 | 備考 |
|:--|:--|:--|:--|
| Llama-8B (ローカル) | $0 (GPU 時間のみ) | ~200 GPU-hours | A100 x 1 |
| Llama-70B (ローカル) | $0 (GPU 時間のみ) | ~1600 GPU-hours | A100 x 4 |
| API (GPT-4等) | ~$0.05/task | ~$4,000 | 比較用 |

**代替戦略:** SWE-bench Lite (N=300) + SWE-bench Verified (N=500) の既存 trajectory を活用し、Stage 2 のコストを大幅に削減。

### 4.4 Stage 3: 特徴量抽出

```python
# 擬似コード: Ξ_Gini 計算
def compute_xi_gini(trajectory: list[Observation]) -> float:
    """observation 長分布から Gini 係数を計算"""
    lengths = [len(obs.content) for obs in trajectory]
    return gini_coefficient(lengths)

# 交絡変数の抽出
def extract_confounders(instance: SWEBenchInstance) -> dict:
    return {
        'sloc': count_sloc(instance.repo, instance.base_commit),
        'test_count': count_tests(instance.test_patch),
        'stars': get_repo_stars(instance.repo),
        'issue_length': len(instance.problem_statement),
        'diff_size': count_diff_lines(instance.patch),
        'language': detect_language(instance.repo),
        'domain': classify_domain(instance.repo),
    }
```

### 4.5 Stage 4: 統計分析スクリプト仕様

```python
# 主分析
r, p = pearsonr(xi_gini, success)  # 全件相関
ci = bootstrap_ci(xi_gini, success, n_bootstrap=10000)  # 95% CI

# 層別分析
for axis in [trajectory_length, task_difficulty, action_space, model_size]:
    for subgroup in stratify(data, axis):
        r_sub, p_sub = pearsonr(subgroup.xi, subgroup.p)

# A/C 弁別
# M-1: 減衰構造テスト
for rho_cutoff in np.linspace(0.05, 0.5, 10):
    for K_control in range(0, 9):
        r_obs = compute_partial_r(data, rho_cutoff, K_control)

# M-4: 階層的回帰
import statsmodels.api as sm
model_base = sm.OLS(P, Z).fit()
model_full = sm.OLS(P, pd.concat([Z, Xi], axis=1)).fit()
f_test = model_full.compare_f_test(model_base)

# M-5: Causal Forest
from econml.dml import CausalForestDML
cf = CausalForestDML().fit(Y=P, T=Xi, X=Z)
```

### 4.6 Stage 5: 出力フォーマット

- JSON: 全件の (instance_id, Ξ_Gini, P, Z₁-Z₈) テーブル
- CSV: 層別分析結果
- Markdown: Paper IV §7.1 に統合可能な結果表
- Figures: r(T) プロファイル, r(ρ, K) 曲面, Causal Forest heterogeneity map

---

## §5. リソース見積もり

### 5.1 計算リソース

| 工程 | 必要リソース | 推定所要時間 | 代替案 |
|:--|:--|:--|:--|
| Stage 1 (データ取得) | CPU, 10GB storage | 1時間 | — |
| Stage 2a (Llama-8B) | A100 x 1 | ~200 GPU-hours (~8日) | RunPod ~$400 |
| Stage 2b (Llama-70B) | A100 x 4 | ~1600 GPU-hours (~17日) | RunPod ~$3200 |
| Stage 2c (API) | API credits | ~3日 | ~$4000 |
| Stage 3 (特徴量) | CPU, 50GB storage | 6時間 | — |
| Stage 4 (分析) | CPU (+ GPU for Causal Forest) | 12時間 | — |
| Stage 5 (レポート) | — | 手動 | — |

### 5.2 最小実行可能計画 (MVP)

**Phase A (低コスト, 即時実行可能):**
- SWE-bench Lite (N=300) の既存 trajectory を使用
- Ξ_Gini 計算 + 全メトリクス (M-1〜M-5) の予備検証
- 所要: CPU のみ, 1日

**Phase B (中コスト):**
- SWE-bench Verified (N=500) で Stage 2〜5 を完全実行
- Paper IV §5.2 の結果を再現 + 拡張
- 所要: API $50 + CPU 2日

**Phase C (本格検証):**
- 全件 (N=80,036) での完全実行
- 所要: GPU-hours + API $4000 + 3週間

### 5.3 依存パッケージ

```
numpy, scipy, pandas, statsmodels
scikit-learn, econml (Causal Forest)
matplotlib, seaborn
swebench (princeton-nlp/SWE-bench toolkit)
transformers, vllm (trajectory 生成)
```

---

## §6. r ≈ 0.1 の解釈に関する判定基準

### 6.1 判定マトリクス

| M-1 | M-2 | M-4 | M-5 | 判定 |
|:--|:--|:--|:--|:--|
| 理論曲面適合 | r ≈ 0 再現 | Ξ 偏回帰有意 | 異質性あり | **解釈 A 支持** |
| フラット | r > 0 | Ξ 消失 | 一様ゼロ | **解釈 C 支持** |
| 部分適合 | r ≈ 0 再現 | Ξ 部分有意 | 弱い異質性 | **混合: 因果+交絡** |

### 6.2 停止条件

1. **Phase A で r < 0.03:** 効果が検出限界以下。パイプライン設計の再検討。
2. **Phase B で M-4 Ξ 消失:** 交絡仮説が有力。r_theory の再推定が必要。
3. **Phase C で全メトリクス解釈 A 支持:** 効果量減衰定理の全件検証完了。Paper IV を v1.0 に昇格。

---

## §7. Paper VIII §6.3 有限主体定理との接続

Paper VIII 定理 6.3.2 (有限主体定理) は「有限な主体は必然的にある α > 0 でしか同定できない」と主張する。SWE-bench における LLM エージェントは有限主体のインスタンスであり:

- **Ξ_Gini** = LLM の忘却パターンの観測可能な proxy
- **r ≈ 0.1** = 有限主体定理の予測する情報損失の定量的発現
- **ρ ≈ 0.2** = α-忘却濾過における観測可能な α 水準の制約

全件検証は、有限主体定理の初の大規模経験的検証となる。

---

*SWE-bench Verification Plan v0.1*
