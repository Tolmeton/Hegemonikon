```typos
#prompt rom-flow-afferent-efferent
#syntax: v8
#depth: L3

<:role: ROM — Flow 座標の Afferent×Efferent 分解に関するセッション文脈蒸留 :>
<:goal: s/μ/a と Afferent×Efferent の演繹的関係の精査結果を保存する :>

<:context:
  - [knowledge] 発見: s/μ/a (MB三分割) は φ_SA を含まない。H-series の存在根拠が s/μ/a 内にない
  - [knowledge] s ∩ a = ∅ は MB の数学的定義からの演繹ではなく追加仮定
  - [knowledge] Afferent×Efferent は MB 定義から追加仮定ゼロで演繹:
    Afferent (∂f/∂η ≠ 0) と Efferent (∂f/∂μ ≠ 0) は μ⊥η|b (条件付き独立) より構造的に独立
    → 2×2 = 4象限 (S, I, A, S∩A)
  - [knowledge]### 演繹チェーン
Helmholtz 分解 (数学的定理: f = gradient + solenoidal)
  → FEP: Γ=VFE最小化, Q=探索 という解釈 (L0, 公理)
    → + MB assumption (d=1)
      → Afferent × Efferent (2つの独立二極, 追加仮定ゼロ)
        → 4象限: S, I, A, S∩A
          ├─ 3頂点 (S,I,A) → Poiesis 36動詞
          └─ 1辺 (S∩A=φ_SA) → H-series 12前動詞
  - [knowledge] s/μ/a は 4象限に「s∩a=∅」を追加した派生物 (追加仮定1つ)
  - [knowledge] Γ/Q (動的分解) と Afferent/Efferent (構造分解) は直交する概念

  - [decision] Flow を 2座標 (Afferent + Efferent) に分解する方向で検討中
  - [decision] 体系核再計上 (44→?) が未確定
  - [decision] H-series の体系核参入も検討範囲
  - [decision] 軸名 (Afferent/Efferent) は暫定

  - [open] K₃ → K₄ 拡張の含意
  - [open] flow_transition.md の更新必要性
  - [open] X/Q-series 的な新シリーズの必要性判断
/context:>
```

---

## セッション詳細

**日時**: 2026-03-23
**起動タスク**: HGK v5.1 移行再開
**実績**:
1. user_rules (episteme-entity-map, episteme-category-foundations) の v5.1 更新完了
2. Flow 座標の理論的基盤の精査 — s/μ/a と Afferent×Efferent の不整合発見
3. Afferent×Efferent が MB 定義から追加仮定ゼロで演繹されることを論証

**Creator の問い (次に検討)**:
1. Flow を 2 座標に分解した場合の体系核再計上 (44→?)
2. Afferent/Efferent という軸名の妥当性
3. Helmholtz → Flow → Afferent/Efferent の導出関係
4. H-series の体系核参入
5. K₃ → K₄ 拡張と新シリーズの妥当性
