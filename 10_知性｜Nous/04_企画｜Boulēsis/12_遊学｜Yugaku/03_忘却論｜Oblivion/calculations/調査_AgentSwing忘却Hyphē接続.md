# AgentSwing × Oblivion Theory × Hyphē — 未接続の縁 (MECE)

> SOURCE: AgentSwing (Feng et al. 2026, Tongyi Lab/Alibaba), Oblivion Theory (abstraction_oblivion_formalization_v1.md), Hyphē (linkage_hyphe.md v8), Context Rot (A3_context_rot.md)
> 日付: 2026-04-03
> 確信度: 全体 [推定 60%]
> /kat+ 較正 (2026-04-03): 「同型」→「整合的な構造的類比」に格下げ。共通テーマ [推定 80%], P1 [仮説 55%], P2 [推定 60%], P3 [仮説 50%]
> /noe+ 再較正 (2026-04-03): P2, P3 について構成的証明を実行 (proof_cm_categorical_2026-04-03.md)。P2 → [推定 80%] 数学的対応が構成的に成立。P3 → [推定 75%] 統計的随伴が成立。
> 撤回条件: P1→attention以外のメカニズムで完全説明時, P2→商関手の弱合成保存が反例で崩壊時, P3→η が統計的にも不成立のベンチマーク発見時
> /ene+ 統合 (2026-04-03): 4方向実行完了。Paper X draft 作成 (paper_X_agentswing_context_rot_draft.md)。① Case Study N=2 + N=240 統計で条件付き不可逆性を確立。② τ↔r 予測 [仮説 50%]。③ boot⊣bye 三者合流を定式化。④ 命題 X.1-X.7 + 確信度マップ完備。

---

## §0. 確立済みの接続 (背景)

| AgentSwing | Oblivion Theory | Hyphē |
|:-----------|:---------------|:------|
| Pass@1 = η × ρ | r ≤ √(ρ/(K+1)) | Fix(G∘F) = Kalon |
| Context Rot (Fig.2) | 薄い MB の恒常性限界 | Drift > 0.3 |
| 3 CM 戦略 = U の強度 | 忘却関手 U: 豊穣圏→前順序圏 | F⊣G 随伴 |
| 並列分岐+ルーティング | Layer 3 補正 | F (発散) ⊣ G (収束) |

---

## §1. 未接続の縁 — MECE 4象限

4つの未接続方向を **理論↔工学** × **静的↔動的** で MECE 分類:

```
                    静的 (パラメータ)          動的 (プロセス)
                ┌─────────────────────┬──────────────────────┐
    理論的      │  E1: τ ↔ r 臨界密度  │  E2: 不可逆性テーゼ   │
    (構造)      │  の同一性             │  → AgentSwing 限界予測 │
                ├─────────────────────┼──────────────────────┤
    工学的      │  E3: AY メトリクス    │  E4: Nucleator        │
    (実装)      │  → routing 品質測定   │  → Lookahead 対応     │
                └─────────────────────┴──────────────────────┘
```

---

### E1: τ ↔ r 臨界密度の同一性 [仮説 40%]

**問い**: Hyphē の τ_cos = 0.70 と AgentSwing の trigger ratio r ∈ {0.2, 0.4} は、同一の臨界密度の異スケール射影か？

**接続の根拠**:
- Hyphē: τ = 「自律性が出現する臨界密度」。ρ_MB > τ ⟹ Fix(G∘F) 存在保証
- AgentSwing: r = 「context management をトリガーする context 使用率」。r を超えると CM 発動
- 両者とも「これ以上蓄積すると品質が劣化する臨界点」を定義

**未接続の理由**:
- τ は情報幾何学的 (ρ_MB ∈ [0,1])、r は工学的 (context_length / max_length)
- スケール変換関数が不明 (§3.4a の τ スケール変換と同型の問題)

**検証方法**:
1. AgentSwing のデータで context budget ごとの terminal precision をプロット → 急落点を特定
2. Hyphē の τ_cos と AgentSwing の急落点の構造的対応を検証
3. 共通の相転移構造 (SNR=1, λ=1) が両方に現れるか

**予測**: τ と r は同一の分岐点の異なるスケーリングであり、τ_AgentSwing = f(r, max_context_length) なる変換 f が存在する。

---

### E2: 忘却の不可逆性テーゼ → AgentSwing の限界予測 [推定 70%]

**問い**: Oblivion Theory の U の非単射性は、AgentSwing のどの戦略にどのような限界を予測するか？

**接続の根拠**:
- U: 豊穣圏 → 前順序圏 (射の厚みを捨てる、多対一写像)
- Summary = U の適用 (軌道を圧縮) → 元の具体的軌道は復元不能
- Case Study: Summary が Lil Durk 仮説に固定 = U による情報の不可逆的喪失

**3つの限界予測** (§2 で詳細化):
- P-E2a: Summary Fixation — 圧縮が誤仮説を不可逆的に固定する
- P-E2b: Discard-All Amnesia — 全忘却が有望な手がかりを不可逆的に消去する
- P-E2c: Routing Ceiling — ルーターの評価精度が全戦略の天井を制約する

**検証方法**: AgentSwing の Case Study データから誤戦略選択のパターンを分類

---

### E3: AY メトリクス → routing 品質測定 [推定 60%]

**問い**: Hyphē の AY (Affordance Yield) メトリクスは AgentSwing の routing 品質を測定できるか？

**接続の根拠**:
- AY(f) = |Hom(f(K), −)| − |Hom(K, −)| (索引操作 f による発見可能性の変化)
- AgentSwing のルーティング: 3 ブランチから最有望を選択
- AY > 0 ⟺ ブランチが情報的に弁別可能 ⟺ routing が有意味

**未接続の理由**:
- AY は知識状態 K の Disc 集合で定義。軌道状態への翻訳が未定義
- ブランチ間の「弁別可能性」を AY で定量化する方法が未開発

**検証方法**:
1. 各ブランチの Lookahead K ターン後の状態を「知識状態」とみなす
2. AY_branch = |Disc(branch_i)| − |Disc(raw_context)| を計算
3. AY > 0 のブランチ数と routing 成功率の相関を測定

**予測**: AY が全ブランチで ≈ 0 のとき、routing はランダム選択と変わらない (Table 3 の random ≈ w/o Lookahead の状況)。

---

### E4: 多スケール Nucleator → Lookahead 対応 [推定 55%]

**問い**: Hyphē の多スケール Nucleator (§8.4) は AgentSwing の Lookahead routing の時間的実現か？

**接続の根拠**:
- Nucleator: τ をパラメータとして複数スケールで同時にチャンク境界を検出
- AgentSwing: 3 つの CM 戦略を並列に適用 → K ターン先読み → 最良選択
- 両者とも「複数の粒度で同時に分割し、最適な粒度を選択する」

**構造的対応**:

| Nucleator (空間) | AgentSwing (時間) |
|:-----------------|:-----------------|
| τ_high (Micro) → 細かいチャンク | Keep-Last-N → 局所保持 |
| τ_mid (Meso) → 中間チャンク | Summary → 中間圧縮 |
| τ_low (Macro) → 粗いチャンク | Discard-All → 全体リセット |
| 最適 τ 選択 | Lookahead routing |

**未接続の理由**:
- Nucleator は空間的 (テキスト内の位置)、Lookahead は時間的 (軌道のターン)
- 「空間的チャンキング」と「時間的文脈管理」の圏論的同型性が未証明

**検証方法**:
1. Hyphē の τ 感度分析 (§8.5) の drift 改善パターンと AgentSwing の k 感度 (Table 3) のパフォーマンス曲線を比較
2. 最適 τ が k=3 に対応するか (Hyphē: G∘F 1-2 回収束 ≈ AgentSwing: k=3 最適)

---

## §2. E2 詳細: 不可逆性テーゼ → AgentSwing 限界予測

→ [prediction_agentswing_irreversibility_2026-04-03.md](prediction_agentswing_irreversibility_2026-04-03.md) に詳細化

3 つのテスト可能な命題:
- **P-E2a** Summary Fixation Theorem: 誤仮説 majority 下での U_abstract による不可逆的固定化
- **P-E2b** Discard-All Amnesia Theorem: ε 近傍からの U_total による非効率回帰
- **P-E2c** Routing Ceiling Theorem: Router 自身の context rot によるメタレベル天井

統合: **最適忘却強度 U\*(state) は軌道状態の関数** — AgentSwing はこれを離散近似する

---

## §3. 優先順位

| ID | 方向 | 確信度 | 実行可能性 | 優先度 |
|:---|:-----|:------:|:----------:|:------:|
| **E2** | 不可逆性→限界予測 | 70% | 高 (理論導出のみ) | **★★★** |
| E3 | AY→routing品質 | 60% | 中 (実験設計必要) | ★★ |
| E1 | τ↔r 同一性 | 40% | 低 (AgentSwing生データ必要) | ★ |
| E4 | Nucleator→Lookahead | 55% | 低 (証明必要) | ★ |

---

*Updated: 2026-04-03*
