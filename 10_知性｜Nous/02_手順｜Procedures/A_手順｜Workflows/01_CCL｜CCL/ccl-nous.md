---
description: "問う — /noe[Vl:±, Pr:U]+_(/ske+*/sag+)_R:{F:[×2]{/u+*^/u^}}_~(/noe+*/ele+)_/epo+"
lcm_state: stable
version: "3.0"
lineage: "v1.0 (旧体系) → v2.0 (24動詞置換+Elenchos) → v3.0 (複合式+深層化: /s→(/ske*/sag), 全-→+)"
ccl_signature: "@nous"
hegemonikon: Telos × Methodos × Orexis × Krisis
layer: "CCL マクロ"
trigonon:
  verbs: [V01, V05, V06, V18, V10]
  coordinates: [I/E, I/Explore, I/Exploit, I/-, I/U]
---

# /ccl-nous: 問いの深化マクロ (νοῦς)

> **CCL**: `@nous = /noe[Vl:±, Pr:U]+_(/ske*/sag)+_R:{F:[×2]{/u+*^/u^}}_~(/noe+*/ele+)_/epo+`
> **用途**: 再帰的に深く問いたいとき
> **認知骨格**: Prior → Likelihood → Posterior
> **深度**: 全ステップ `+` (深層)。問いの深化に軽量版はない。

## v3.0 再構成の根拠

| 旧 (v1.0) | v2.0 | v3.0 | 変更根拠 |
| :--- | :--- | :--- | :--- |
| `/pro` | `/noe[Vl:±, Pr:U]-` | `/noe[Vl:±, Pr:U]+` | 深層化。直感を深く掘る |
| `/s-` | `/ops-` | **`(/ske*/sag)+`** | 1動詞→複合式。Methodos 族の Explore×Exploit 融合 |
| `~(/noe*/dia)` | `~(/noe*/ele)` | `~(/noe+*/ele+)` | 深層化。理解と反駁を本気で振動させる |
| `/pis_/dox-` | `/epo-` | `/epo+` | 深層化。問いの保持を構造化する |

### なぜ `/s` → `(/ske*/sag)` か

旧 `/s` = Methodos 族の Peras (4定理の極限演算)。

**1動詞で代替するのは不可能** — `/s` は族のハブであり、単一の動詞ではない。
CCL 複合式 `(/ske*/sag)` = V05 Skepsis × V06 Synagōgē の融合:

| 動詞 | 座標 | 役割 |
| :--- | :--- | :--- |
| `/ske` (V05) | I × Explore | 仮説空間を **拡げ**、前提を破壊する |
| `/sag` (V06) | I × Exploit | 仮説空間を **絞り込み**、最適構造を統合する |
| `(/ske*/sag)` | **Explore ⊗ Exploit** | 拡げつつ絞る — Methodos 族の推論的核心 |

> V07 `/pei` (実験) と V08 `/tek` (技法) は行為軸 (A) であり、問いの Prior (推論的方向性設定) には不要。推論軸の2動詞で十分。

## 展開

| 相 | ステップ | 動詞 (v4.1) | 座標 | 意味 |
| :--- | :--- | :--- | :--- | :--- |
| Prior | `/noe[Vl:±, Pr:U]+` | V01 Noēsis | I×E + Dok[Vl:±, Pr:U] | 何が引っかかるかを深く感じる (直感的認識) |
| Prior | `(/ske*/sag)+` | V05 × V06 | I×Explore ⊗ I×Exploit | 問いの空間を拡げつつ絞り込む (Methodos 融合) |
| Likelihood | `R:{F:[×2]{/u+*^/u^}}` | — | — | 主観→メタ融合→メタ主観を2回再帰 |
| Posterior | `~(/noe+*/ele+)` | V01 × V18 | I×E ~ I×− | 深い理解と体系的反駁の振動 |
| Posterior | `/epo+` | V10 Epochē | I×U | 問いの到達地点を構造化して保持する |

> **設計原則**: 問いの深化マクロに軽量版 (`-`) は存在しない。全ステップ `+` で本気で問う。

## 使用例

```ccl
@nous                      # 標準問い（2回再帰、全+）
@nous _ @learn             # 問い直し後に永続化
F:[×3]{@nous}              # 3回再帰で深く問う
@nous _ /kat+              # 問い→確定（確信が得られた場合）
```

## 射の提案 (完了時)

| 条件 | 射 | 意味 |
| :--- | :--- | :--- |
| 問いが深まった | `>> /epo+` | 保持を継続、再訪条件を設定 |
| 確信が得られた | `>> /kat+` | 確定・コミット |
| 矛盾を発見した | `>> /ele+` | 体系的反駁に昇格 |
| 行動に移りたい | `>> /dok+` | 本格打診 |

---
*v1.0 — 初版 (旧体系依存)*
*v2.0 — v4.1 再構成: 24動詞厳密版。Elenchos 検証済 (2026-02-27)*
*v3.0 — 複合式+深層化: /s→(/ske*/sag)、全-→+。Creator 指摘反映 (2026-02-27)*
