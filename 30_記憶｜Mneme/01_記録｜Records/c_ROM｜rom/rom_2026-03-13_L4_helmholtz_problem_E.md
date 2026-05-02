---
rom_id: rom_2026-03-13_L4_helmholtz_problem_E
session_id: 2d70b0ef-8c59-4075-9254-82a5d1839122
created_at: 2026-03-13 11:20
rom_type: rag_optimized
reliability: Medium
topics: [L4, Helmholtz decomposition, information geometry, bicategory, m-connection, e-connection, problem_E, non-equilibrium steady state, NESS, Fokker-Planck, double-well potential, OU process, solenoidal flow, dissipative flow, Amari, Friston, axiom_hierarchy]
exec_summary: |
  L4 (Time → BiCat) に Helmholtz 分解を導入し、時間圏 T に Γ_T⊣Q_T 双対構造を付与する構想を展開。
  最大のブロッカー「問題 E (m-connection の力学的実現)」を二重井戸ポテンシャルで手掘り分析し、
  世界線 γ (solenoidal flow ≈ m-方向成分) が最有望であることを [推定 60%] で暫定判定。
---

# L4 Helmholtz BiCat 構想 + 問題 E 分析 {#sec_01_overview}

> **[DISCOVERY]** L4 の核心: 時間圏 T が前順序圏のままでは「セッション間の構造変化」を捉えられない。Helmholtz 分解 f = f_d + f_s を T 自体に適用することで、T に内部構造が生まれる。

> **[DECISION]** L4 の定式化方針: T を Helmholtz 圏 (Γ_T, Q_T) として構成し、Γ_T = 非可逆学習 (散逸), Q_T = 保存的循環 (回転) に対応させる。

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "L4 とは何か？ 正方形モデルの右下を超える構造とは？"
  - "Helmholtz 分解と情報幾何の関係は？"
  - "問題 E の解決状況は？ solenoidal flow と m-connection の関係は？"
  - "Drift の物理的意味は？"
answer_strategy: "L4 は L3 (弱2-圏) の時間変動版。Helmholtz 分解が時間圏 T に内部構造を付与し、Drift に物理的意味を与える。問題 E は世界線 γ (修正された利用可能性) で暫定解決。"
confidence_notes: "全体構想は [仮説] レベル。問題 E の世界線 γ 判定は [推定 60%]。数値検証が未完了。"
related_roms: ["rom_2026-03-08_typos_table_adjoint", "rom_2026-03-09_coordinate_rescue_valence_temporality"]
-->

---

## §1 L4 の動機と位置づけ {#sec_02_motivation}

> **[FACT]** 正方形モデル (axiom_hierarchy.md v4.2.0):
> - L1: 前順序圏 + ガロア接続 ✅
> - L2: [0,1]-豊穣圏 (Drift = Hom値) ✅
> - L3: 弱2-圏 (bicategory, 思考順序の保存) 🟢
> - L4: Time → BiCat (経験により認知構造自体が変わる) 💭

> **[DISCOVERY]** L3 までは「構造の中での操作」。L4 は「構造自体の変動」。関手圏 [T, BiCat] としてのセッション列。

### L4 の圏論的構成 {#sec_03_construction}

> **[DEF]** L4 関手: F: T → BiCat
> - T = 時間圏 (セッション列 t₁ → t₂ → ...)
> - F(tₙ) = そのセッション時点での認知 bicategory
> - F(tₙ→tₙ₊₁) = セッション間の認知構造変化 (pseudofunctor)

> **[FACT]** 問題: T が離散順序集合のままでは、F は単なる列にすぎず、T 自体に構造がない。→ Helmholtz 分解で T に内部構造を付与する。

---

## §2 Helmholtz の T への適用 {#sec_04_helmholtz_on_T}

> **[DEF]** Helmholtz 構造付き時間圏:
> ```
> T = (T, Γ_T, Q_T) where:
>   Γ_T: 非可逆成分 = 散逸流 f_d 由来 = 不可逆な学習
>   Q_T: 保存的成分 = 回転流 f_s 由来 = 循環的パターン
> ```

> **[RULE]** HGK 認知的対応:
> | 成分 | 力学 | 情報幾何 | HGK 意味 |
> |:-----|:-----|:---------|:---------|
> | Γ_T (散逸) | f_d = -∇ℑ | e-projection 的 | 世界モデルの不可逆更新 |
> | Q_T (保存) | f_s (div-free) | m-方向の成分 | 認知パターンの回帰・振動 |

> **[DECISION]** Drift の物理的意味:
> ```
> Drift = ||ΔΓ|| / (||ΔΓ|| + ||ΔQ||)
>       = 学習量 / (学習量 + 循環量)
> Drift → 1: 急激な学習 (構造変化大)
> Drift → 0: 安定した循環 (構造変化小)
> ```

---

## §3 問題 E: m-connection の力学的実現 {#sec_05_problem_E}

> **[FACT]** task_B_helmholtz_dual_bridge.md の結論:
> - f_d (散逸流) ↔ e-projection (mode-seeking) — 明確に対応
> - f_s (回転流) ↔ m-projection — 直接対応しない！
> - f_s はファイバー上のゲージ流であり、m-測地線ではない

> **[DISCOVERY]** これが問題 E の核心: solenoidal flow と m-connection の関係は自明ではない。3つの世界線を構成して分析。

### 3つの世界線 {#sec_06_worldlines}

> **[DEF]** 世界線 α (使える): f_s が接続 ω を定義し、m-測地線が直接持ち上がる。情報幾何の定理がそのまま適用可能。
> - 条件: π_*(f_s) が M 上で m-接続のクリストッフェル記号を再現
> - 判定: [仮説 30%] — 条件が厳しすぎる

> **[DEF]** 世界線 β (使えない): f_s と m-connection は無関係。情報幾何の定理は適用不可。
> - 含意: L4 は情報幾何なしで別の理論が必要
> - 判定: [推定 20%] — β でも L4 自体は構成可能だが貧弱

> **[DEF]** 世界線 γ (修正して使える): f_s のホロノミーが M の m-曲率に対応。情報幾何が修正された形で適用可能。
> - 含意: 「solenoidal ≈ m-方向成分」だが「solenoidal = m-測地線」ではない
> - 判定: **[推定 60%]** — 最有望

---

## §4 OU 過程での検算 {#sec_07_ou_verification}

> **[FACT]** 2D 回転 OU 過程: dx = (-Bx)dt + σdW, B = ((γ, -ω),(ω, γ))
> - Helmholtz 分解: f_d = -γx (勾配), f_s = ω(-x₂, x₁) (回転)
> - NESS 分布: N(0, Σ), Σ = (σ²/2γ)I

> **[DISCOVERY]** Gaussian NESS の核心的発見:
> - 統計多様体 M = {N(0, Σ)} は平坦 (flat)
> - 平坦 → e-接続 = m-接続 → 問題 E が消える!
> - f_s は Σ の回転対称性に「吸収」され、分布レベルで不可視

> **[RULE]** 問題 E が発現する条件:
> - M が曲がっている (非 Gaussian NESS)
> - 捩率 T ≠ 0 (e-接続と m-接続が異なる)
> → 非 Gaussian モデルでの検証が必須

---

## §5 二重井戸ポテンシャルでの検証 {#sec_08_double_well}

> **[FACT]** 二重井戸: ℑ(x₁,x₂) = (x₁²-1)²/4 + x₂²/2
> - f_d = (-∂₁ℑ, -∂₂ℑ) = (x₁-x₁³, -x₂) — 井戸への勾配降下
> - f_s = ω(-∂₂ℑ, ∂₁ℑ) = ω(-x₂, x₁³-x₁) — 等高面上の回転

> **[DISCOVERY]** NESS 分布は非 Gaussian (双峰分布):
> p_ss ∝ exp(-2ℑ/σ²) = exp(-(x₁²-1)²/2σ² - x₂²/σ²)
> → 統計多様体 M は曲がっている → e ≠ m → 問題 E が発現

> **[DISCOVERY]** Helmholtz-Amari 対応 (定理候補):
> | | e-座標 θ (密度の形) | m-座標 η (期待値) |
> |:---|:---|:---|
> | f_d | ✅ 決定する | — |
> | f_s | ❌ 変えない (∇·f_s=0) | ✅ 交差成分 ⟨x₁x₂⟩ に効く |

> **[DISCOVERY]** 核心の物理的直観:
> ```
> Solenoidal flow は「密度の形」(e) を変えずに
> 「確率の流れ方」(m) を制御する。
> 
> Gaussian: Σ が f_s を吸収 → 見えない
> 非 Gaussian: ⟨x₁x₂⟩ が f_s の新自由度 → m-方向で可視
> ```

> **[FACT]** 交差モーメントへの効果:
> d⟨x₁x₂⟩/dt = ⟨x₁(x₁³-x₁)⟩ω - ⟨x₂(x₁³-x₁)⟩ω + (f_d 寄与) + 拡散項
> → ω に依存する項が存在 = f_s が m-座標 η₅=⟨x₁x₂⟩ を制御

---

## §6 L4 へのフィードバック {#sec_09_L4_feedback}

> **[DECISION]** L4 の Γ_T / Q_T の認知的意味確定:
> ```
> Γ_T (学習) = 密度の形 (e-座標 θ) を変える = 世界モデルの更新
> Q_T (循環) = 相関構造 (m-座標 η_cross) を回す = 認知パターンの回帰
> Drift = ||Δθ|| / (||Δθ|| + ||Δη_cross||)
> ```

> **[OPINION]** 世界線 γ が成立する [推定 60%]。情報幾何の定理は「修正された形で」使える。ただし ≈ と = の差 (solenoidal ≈ m-方向成分 vs solenoidal = m-測地線) が次の問い。

---

## §7 未解決問題と次ステップ {#sec_10_open_problems}

> **[CONFLICT]** ≈ vs = の問題:
> solenoidal flow は m-座標の成分に影響するが、m-測地線そのものを定義するかは不明。
> この差が L4 の定理の強さを決定する。

> **[FACT]** 残タスク:
> 1. 数値検証: ⟨x₁x₂⟩(ω) の ω 依存性を Fokker-Planck で計算
> 2. m-測地線との厳密距離: σ_*(f_s) と m-接続 ∇^(m) の関係を定式化
> 3. 他の未解決問題 (A,B,C,D) への波及効果を分析
> 4. L4 夢見文書への統合と /fit 検証

## 関連情報 {#sec_11_references}

- 関連ファイル: `00_核心/A_公理/L4_helmholtz_bicat_dream.md`
- 関連ファイル: `00_核心/A_公理/problem_E_m_connection.md`
- 関連ファイル: `30_記憶/01_記録/d_成果物/task_B_helmholtz_dual_bridge_2026-03-08.md`
- 関連 KI: axiom_hierarchy, kalon, category-foundations
- 関連 WF: /noe, /lys, /rom, /fit
- 学術参照: Amari (情報幾何), Friston (FEP/Helmholtz), Graham (NESS), Qian (circulation)
