# CCL-CoT SFT — メタデータ

> 対応本体 (未起票): `paper_ccl_cot_sft_draft.md` (Tier 3, 別セッション)
> 対応 spec: `ccl_cot_converter_spec.md` (Tier 2, 本セッションで併設起票)
> 位置づけ: Lethe ROADMAP §8.3 H1 (CoT → ρ 増加) の拡張独立稿。論文 VII §6.4(iv) と論文 XI §7.6 の同時補強として独立投稿候補
> 起票日: 2026-04-29
> 状態: Tier 1 骨格起票 (§M0/§M1/§M2/§M6 中核, §M3-§M5/§M7-§M9 は scaffold)

---

## §M0 起票コンテキスト

### §M0.1 背景

Tolmetes 投稿の Abstract-CoT (arXiv 2604.22709, "Thinking Without Words") のファクトチェックから出発。論文の主要主張は方向性レベルでは正確 (64 抽象記号 / Qwen3-8B/4B + Granite-4.0 / 11.6× 圧縮 / 92.6 → 90.8% 維持) だが、統計報告は point estimate only (CI/SD/p なし、N=500)。

このため、論文 VII 系 6.1.5 [SOURCE: 論文VII L590] の予測 (Ker(η) > 0 は常に成立、予測は原理的に消滅しない) と Drift -1.8 pt の対応を確証する案 C は paired 95% CI 算出不能のため棚上げ。代替案として、Lethe ROADMAP §8.3 H1 (CoT → ρ 増加) の自然な拡張として **CCL-CoT SFT (粒度 3) を独立稿で起票** する案 B を採用。

### §M0.2 関連 ROM

- `rom_2026-04-29_ccl_cot_sft_lethe_extension.typos` — 本起票の親 ROM。D-001〜D-008 を確定
  - D-001 案 C 棄却 (Drift -1.8 pt の CI 未確定)
  - D-002 案 B 採用 (CCL-CoT SFT 実証経路)
  - D-003 (iii) Lethe 拡張として独立起票
  - D-007 Tier 1 + Tier 2 を本セッション内で起票

### §M0.3 既存資産マップ

| 種別 | パス | 役割 |
|:---|:---|:---|
| CCL parser | `02_解釈｜Hermeneus/`, `80_運用｜Ops/scripts/start_hermeneus_stdio.sh` | CCL 式 → AST 実行 (既存) |
| Code → CCL transpiler | `20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_ingest.py` | AST + 9 変換ルール、LLM 不要 (既存) |
| 自然言語 CoT → CCL CoT 変換器 | (HGK 内に存在せず) | **新規実装が必要** ← Tier 2 spec で契約 |
| Lethe 理論母体 | `14_忘却｜Lethe/ROADMAP.md` §8.3 H1 (L172-188) | CoT → ρ 増加。本実験はこの三項拡張 |
| 統計予算 | Colab Pro+ (A100 40GB) + GCE L4 24GB / 28,000 円 (≈ 270h × 0.7 USD/h) | 粒度 3 (SFT) は範囲内、粒度 4 (RL) は不可 |

### §M0.4 本実験の射程と非射程

**射程:**
- 自然言語 CoT / CCL-CoT / CoT なし の三項比較を MATH-500 paired protocol で測定
- 測定指標: accuracy (paired McNemar), Δρ_CoT (Phase B2 attentive probing 流用), shuffle robustness
- 訓練リソース: Gemma 4 E4B (主), 26B-A4B MoE (scale-up 時) + Unsloth + QLoRA

**非射程:**
- Abstract-CoT (arXiv 2604.22709) の再現実験そのもの — 別タスク
- 粒度 4 (RL emergent CCL token learning) — GPU-week オーダーで予算外
- η の同型化主張 — 論文 VII 系 6.1.5 で原理的禁止

---

## §M1 F⊣G 宣言 (論文開始時に固定、途中変更禁止)

> **状態: 暫定提案 [仮説 60%]。Tolmetes 確認待ち。確認後に固定日を確定する。**

- **F (発散関手)** = 三層複合発散
  - **メタファー三連**: 圧縮 (Abstract-CoT 11.6×) / 翻訳 (NL → CCL) / 構造保存 (関手の像)
  - **4 分野展開**:
    1. 圏論 (Yoneda 補題 / 関手の充満性 / U_compose 修復)
    2. FEP (生成モデルの中間表現精度・予測誤差最小化)
    3. 情報理論 (Information Bottleneck / Data Processing Inequality)
    4. 認知科学 (chain-of-thought の認知負荷分割と作業記憶外部化)
  - **文体ガイド対応**: §3.2.6 (メタファー三連) + §2.4.1 (4 分野展開)

- **G (収束関手)** = 三柱収束
  - **柱 1: Yoneda 補題** — 自然変換 $\eta_X = \mathrm{Hom}(X, -)$ による中間対象の表現可能性
  - **柱 2: IB/DPI** — $I(X; Y) \geq I(X; Z)$ の単調性で「圧縮しても精度を保持できる帯域」を限定
  - **柱 3: 論文 VII §6.1 構造保存定理** [SOURCE: 論文VII L575] + §6.4(iv) CoT-双対性 [SOURCE: 論文VII L695] — 忘却関手 F: S → D は構造を保存し値を忘却する。CoT は U_compose 層を修復する

- **固定日**: 2026-04-29 (Tolmetes 確認後に確定)

- **F⊣G 事後選択禁止の宣言**: 本実験で C1-C3 が ✗ となった場合、F または G の定義変更による「Kalon に見せる」逆算は禁止。✗ なら主張側を縮小・撤回する

---

## §M2 核主張リスト (L3 対象)

> **状態: 暫定提案 [仮説 60%]。Round 1 前。Tolmetes 確認待ち。**

### C1: 構造保存差分主張 (理論側)

**CCL は自然言語 CoT より少ない値で U_compose を修復する。**

- 射程: $\forall$ MATH-500 サブセット (paired discordant 計算可能領域) において、CCL-CoT による U_compose 像の拡大率は自然言語 CoT のそれを下回らない
- 形式化: $|\mathrm{img}(U_{\mathrm{compose}}) \cap \mathrm{CCL}| / |\mathrm{tokens}_{\mathrm{CCL}}| \geq |\mathrm{img}(U_{\mathrm{compose}}) \cap \mathrm{NL}| / |\mathrm{tokens}_{\mathrm{NL}}|$
- SOURCE: Lethe ROADMAP §8.3 H1 [SOURCE: Lethe/ROADMAP.md L172-188] の精緻化

### C2: 実証目標主張 (経験側)

**CCL-CoT SFT は MATH-500 paired N≥200, seeds=5 で、自然言語 CoT に対する accuracy 差の 95% CI が 0 をまたがない accuracy 維持を達成する。**

- 射程: paired McNemar test (b, c discordant pairs 測定) + Wilson 法 95% CI で 0 をまたがず ±2pt 以内
- 失敗条件 (撤回トリガー): 95% CI が 0 をまたいだ場合 (Tolmetes ルール「CI が 0 をまたいだら論外」)
- SOURCE: Abstract-CoT (arXiv 2604.22709) の方法論を paired 化 + seeds=5 で精緻化

### C3: 順序撹乱耐性主張 (副次主張)

**CCL-CoT は順序撹乱に対する耐性が自然言語 CoT より高い (shuffle robustness 差が paired CI で正側)。**

- 射程: ランダム並べ替え後の accuracy drop が NL CoT の -11.0 pt より小さい
- SOURCE: Abstract-CoT のシャッフル耐性差分 (Abstract-CoT -7.8 pt vs Verbal CoT -11.0 pt = 3.2 pt 差) [SOURCE: arxiv.org/html/2604.22709v1] の CCL 版検証
- 仮説的意味: CCL の 1.5-cell 性 (合成律) が値より射構造を優先保持する → 順序情報がより圧縮された形で残る

### C4: 結語側総合主張 (§8 結語に対応)

**CCL-CoT は論文 VII §6.4(iv) の CoT 双対性 (U_compose 修復) を、自然言語 CoT より小さい値表面で実現する工学的純化である。**

- 射程: C1 ∧ C2 ∧ C3 が成立した場合に限り主張可能
- 失敗条件: C1-C3 のいずれかが ✗ なら C4 は不成立 (合成命題)

---

## §M3 Kalon 判定履歴

> 状態: scaffold (Round 1 前 / 実験前)。判定は Tier 3 本体起票 + 実験完了後に追記する。

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-29 | C1 | (Round 1 前 — 判定保留) | Step -1 浮遊大言テスト: §M6 が暫定的に埋まっているが SOURCE は未 Read 直接確認なし。Tier 3 起票時に判定 |
| 2026-04-29 | C2 | (Round 1 前 — 判定保留) | 実証目標は実験完了まで判定不可。実験前は ✗ 自動 |
| 2026-04-29 | C3 | (Round 1 前 — 判定保留) | 実証目標は実験完了まで判定不可 |
| 2026-04-29 | C4 | (Round 1 前 — 判定保留) | 合成主張。C1-C3 確定後 |

---

## §M4 σ ゲート履歴

### §M4.1 静的 ±3σ (Gauntlet 入口/出口)

> 状態: scaffold。Tier 3 起票時に入口検査を実行する。

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-29 | C1 | (未検査) | — | Tier 3 起票時に入口ゲート実行 |
| 2026-04-29 | C2 | (未検査) | — | 実証目標。事前登録 protocol で σ 評価 |
| 2026-04-29 | C3 | (未検査) | — | 同上 |

### §M4.2 Future-Proof Test (時間軸 σ)

> 状態: scaffold。Tier 3 起票時に Step F1-F4 を実行する。

| 日付 | 対象 | 想定モデル進化 | 影響予測 | future-proof σ | 判定 |
|:---|:---|:---|:---|:---|:---|
| 2026-04-29 | C1 | (未検査) | — | — | Tier 3 起票時 |
| 2026-04-29 | C2 | (未検査) | — | — | Tier 3 起票時 |
| 2026-04-29 | C3 | (未検査) | — | — | Tier 3 起票時 |

---

## §M5 Refutation Gauntlet ログ

> 状態: scaffold (Round 1 前)。Tier 3 起票・実験計画レビュー時から記録開始。

### 想定される反論の予備リスト (Round 1 起票前の brainstorm)

- r-pre-1: 「CCL embedding 改善は U_compose 修復ではなく単なる token 効率改善ではないか?」 (C1 への射程縮小要求)
- r-pre-2: 「Abstract-CoT の 11.6× 圧縮は CCL に直接転用できないのではないか?」 (C2 への前提崩し)
- r-pre-3: 「Gemma 4 + Unsloth は HGK 内 SOURCE が薄い」 (実装基盤への信頼性指摘)
- r-pre-4: 「自然言語 CoT → CCL CoT 変換器が新規実装である以上、変換忠実度が C1-C3 の confound 要因」 (Tier 2 spec への回帰)

---

## §M6 虚→実変換面

### C1 (構造保存差分主張)

- **野望**: CCL ≅ 圏論 (Lethe README 主要発見 1) を実証データで補強し、CCL が自然言語 CoT を構造保存的に超えることを示す
- **現在まだ虚な点**:
  1. img(U_compose) の operational 定義 (どの probe で測るか未確定)
  2. CCL token / NL token のカウント等価性 (BPE base か symbol base か未確定)
  3. 「修復」の閾値 (ρ_attentive のどの値以上か未確定)
- **実へ引くための SOURCE**:
  - 論文 VII §6.1 構造保存定理 [L575], §6.4(iv) CoT 双対性 [L695]
  - Lethe ROADMAP §8.3 H1 (Phase B2 attentive probing protocol)
  - Lethe `experiments/ccl_categorical_semantics.md` (CCL ≅ 圏論の 14 演算子対応)
- **実化の判定条件**: Phase B2 protocol で ρ_CCL > ρ_NL かつ paired 95% CI が正側 (差分 ≥ 0.02)
- **次の実化操作**:
  1. Lethe Phase B2 attentive probing の SOURCE Read
  2. img(U_compose) の operational 定義 (probe 設計を Tier 3 で確定)
  3. token カウント基準を Tier 2 spec で固定
- **最新状態**: 虚 (Tier 1 起票時点)

### C2 (実証目標主張)

- **野望**: paired 95% CI で 0 をまたがない accuracy 維持を、自前実験で確証する (Abstract-CoT 論文の統計水準を超える)
- **現在まだ虚な点**:
  1. paired protocol の seeds=5 で MATH-500 を回す compute (Gemma 4 E4B 推論コスト未測定)
  2. 自然言語 CoT → CCL CoT 変換器の出力品質 (変換忠実度が confound)
  3. Unsloth + QLoRA の VRAM 要件 (README レベルの SOURCE のみ)
- **実へ引くための SOURCE**:
  - arXiv 2604.22709 (Abstract-CoT 元論文の方法論) — paired 化への拡張
  - PINAKAS_COMPUTE.yaml (Phase C QLoRA 実績データ) [L24-35, L98-103]
  - Unsloth README + Gemma 4 model card (VRAM 実測)
- **実化の判定条件**: 事前登録 protocol で N≥200, seeds=5 を回しきり、paired McNemar + Wilson 95% CI で差分が 0 をまたがない
- **次の実化操作**:
  1. Tier 2 converter spec の入出力契約確定
  2. Tier 3 で事前登録 protocol 起票 (P-0 〜 P-8 形式 = 既存 H3 plan に倣う)
  3. Unsloth notebook を実走し VRAM 実測 (粒度 0 — 訓練前準備)
- **最新状態**: 虚 (Tier 1 起票時点)

### C3 (順序撹乱耐性主張)

- **野望**: 1.5-cell 性 (合成律) を保持する CCL が、値表面の順序冗長性に依存する自然言語 CoT を順序撹乱で逆転的に上回ることを示す
- **現在まだ虚な点**:
  1. 「順序撹乱」の operational 定義 (token shuffle / step shuffle / clause shuffle のどれか未確定)
  2. CCL の 1.5-cell 性が token shuffle にどう写るか (CCL 式の AST レベルで shuffle するか文字列レベルか)
  3. shuffle 評価の paired protocol (同一問題に対する shuffled / non-shuffled の対応付け)
- **実へ引くための SOURCE**:
  - arXiv 2604.22709 §X (シャッフル実験の正確な手順) — 要再 Read
  - 論文 XI §7.6 H₃ (制約-符号化分離) [L637, L709-713]
  - Hermeneus AST 仕様 (CCL 式の構造的 shuffle 可能性)
- **実化の判定条件**: paired N≥200 で shuffle robustness 差分が paired 95% CI で正側
- **次の実化操作**:
  1. Abstract-CoT 論文のシャッフル手順を WebFetch で精読
  2. CCL AST レベル shuffle の operational 定義を Tier 3 で確定
  3. Hermeneus による parse 通過率を pre-shuffle / post-shuffle で対比
- **最新状態**: 虚 (Tier 1 起票時点)

### C4 (結語側総合主張)

- **野望**: 論文 VII §6.4(iv) CoT 双対性の工学的純化版を CCL で実装し、HGK 体系内の理論-実装橋渡しを 1 件追加する
- **現在まだ虚な点**: C1 ∧ C2 ∧ C3 が未確定なため、C4 全体が虚
- **実へ引くための SOURCE**: C1-C3 の SOURCE を継承
- **実化の判定条件**: C1-C3 すべてが ✓
- **次の実化操作**: C1-C3 の実化操作完了を待つ
- **最新状態**: 虚 (合成命題)

---

## §M7 棄却された代替案 (±3σ 併記義務の記録)

> 状態: 起票時点での棄却を記録。Round 1 進行で追記。

### 棄却 1: 案 C (Drift -1.8 pt を Ker(η) > 0 の定量痕跡として使う)

- **棄却日**: 2026-04-29
- **理由**: Abstract-CoT 論文の統計報告は point estimate only。paired discordant pairs (b, c) が論文未報告で 95% CI が unpaired 近似で [-1.6%, +5.2%] と 0 をまたぐ。Tolmetes ルール「CI が 0 をまたいだら案 C は論外」を適用
- **再起動条件**: 著者問い合わせで paired discordant が判明、または自前再現で paired CI が確定し 0 をまたがないと判明した場合
- **σ 評価**: 案 C は ±2.5σ (μ 近傍ではないが、SOURCE 不確定で浮遊大言リスク)。代替の案 B は ±3σ 候補 (Lethe ROADMAP H1 の精緻化として接地)

### 棄却 2: 粒度 4 (RL emergent CCL token learning)

- **棄却日**: 2026-04-29
- **理由**: Abstract-CoT の RL warm-up loop は GPU-week オーダー。Tolmetes 予算 28,000 円 (≈ 270h × 0.7 USD/h) では 1 condition 1 seed すら不可
- **再起動条件**: GPU-month オーダーの compute 確保 (現状射程外)
- **σ 評価**: 粒度 4 は ±3.5σ 候補 (Abstract-CoT を構造的に超える) だが §M6 接地が compute 不足で空。「浮遊大言」相当のため棚上げ

---

## §M8 タスクログ (任意)

### TASK-CCL-1: Tier 1 起票

- **日付**: 2026-04-29
- **状態**: 完了 (Tier 1 骨格 §M0/§M1/§M2/§M6 中核 + §M3-§M5/§M7-§M9 scaffold)
- **次**: Tier 2 converter spec 起票

### TASK-CCL-2: Tier 2 converter spec 起票

- **日付**: 2026-04-29
- **状態**: 進行中 (本セッション内)
- **配置**: `14_忘却｜Lethe/ccl_cot_converter_spec.md`
- **射程**: 設計目標 + 入出力契約のみ。実装詳細は別セッション

### TASK-CCL-3 (将来): Tier 3 本体起票

- **配置**: `14_忘却｜Lethe/paper_ccl_cot_sft_draft.md`
- **依存**: Tolmetes による §M1 F⊣G 確認 + §M2 C1-C3 文言確認

### TASK-CCL-4 (将来): 事前登録 protocol 起票

- **配置**: `14_忘却｜Lethe/experiments/ccl_cot_sft_protocol.md`
- **依存**: Tier 3 本体 + Tier 2 spec の入出力契約確定

---

## §M9 接続 — 他論文 / 他 program との back-link

| 接続先 | 種別 | 役割 |
|:---|:---|:---|
| 論文 VII §6.1 (構造保存定理) | SOURCE 引用 | C1 / C4 の理論的母体 |
| 論文 VII §6.4(iv) (CoT 双対性) | SOURCE 引用 | C1 / C4 の工学的純化対象 |
| 論文 VII 系 6.1.5 (Ker(η) > 0) | 整合性 | 案 C 棄却の理論根拠 |
| 論文 XI §7.6 H₃ (制約-符号化分離) | SOURCE 引用 | C2 / C3 の射程設定 |
| 論文 XI §7.6.5 (brevity constraint = C 軸境界) | 整合性 | 11.6× 圧縮の解釈で確認要 |
| Lethe ROADMAP §8.3 H1 (CoT → ρ 増加) | 拡張母体 | 本実験の三項拡張 |
| Lethe `experiments/ccl_categorical_semantics.md` | SOURCE 引用 | CCL ≅ 圏論 14 演算子対応 |
| Lethe `experiments/ccl_functor_proof.md` | SOURCE 引用 | CCL の関手性証明 |
| Lethe `paper_distance_stratification_draft.md` | 同 program 内同位 | Lethe 配下の他独立稿との整合性 |
| Hermeneus (`02_解釈｜Hermeneus/`) | 既存資産 | CCL parser として変換器の検証側で使用 |
| Mekhane `code_ingest.py` | 既存資産 | Code → CCL transpiler。Tier 2 設計の参照実装 |

---

*v0.1 — 2026-04-29 — Tier 1 骨格起票 (本セッション)*
*次版予定: Tolmetes による §M1 F⊣G 確認 + §M2 C1-C3 確認後に v0.2 で固定日確定*
