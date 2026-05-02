---
doc_id: "SYSTEM_MANIFEST"
version: "5.1.0"
tier: "KERNEL"
status: "CANONICAL"
lineage: "v1.0 (96要素) → v4.1 (32実体: 1公理+7座標+24動詞) → v5.0 (44実体: 1公理+7座標+36動詞) → v5.1 (H-series 前動詞（中動態）12, [] 記法)"
---

# System Manifest — 44実体体系一覧

> **唯一の公理**: FEP (予測誤差最小化)
> **体系核**: 44 = 1 + 7 + 36
> **修飾/関係**: パラメータとして分離 (体系核外)

---

## 公理 (1)

| ID | 名称 | 定義箇所 | 存在証明 |
|:---|:-----|:---------|:---------|
| A0 | FEP (Free Energy Principle) | [axiom_hierarchy.md](axiom_hierarchy.md) | FEP 自体が公理 — 証明不要 |

---

## 座標 (7)

| d | Question | 座標 | Opposition | 定義箇所 |
|:-:|:---------|:-----|:-----------|:---------|
| 0 | Who | **Flow** | S (感覚) / I (推論) / A (行為) | [axiom_hierarchy.md](axiom_hierarchy.md) |
| 1 | Why | **Value** | E (認識) ↔ P (実用) | 同上 |
| 1 | How | **Function** | Explore ↔ Exploit | 同上 |
| 1 | How much | **Precision**| C (確信) ↔ U (留保) | 同上 |
| 2 | Where | **Scale** | Micro ↔ Macro | 同上 |
| 2 | Which | **Valence** | + (接近) ↔ - (回避) | 同上 |
| 2 | When | **Temporality**| Past (過去) ↔ Future (未来) | 同上 |

> **v5.0 変更**: Flow 座標を二値 (I↔A) から三値 (S/I/A) に拡張。
> MB (Markov Blanket) の s (感覚) / μ (内部) / a (行為) パーティションに対応。
> I (Internal) = μ (内部状態)、S (Sensory) = s (感覚状態)。
>
> **v5.1 追加**: Flow を Afferent×Efferent で 2×2 分解。第4象限 S∩A (反射弧 = φ_SA) を発見。
> φ_SA × 6修飾座標 = H-series 前動詞（中動態）12個 (体系核外)。

---

## 動詞 (Poiesis: 36 = 6族 × 6極)

> **v5.0 変更**: Flow の三値化により、各族に S極 (感覚) 2動詞を追加。24→36動詞。

### Telos 族 (Flow × Value: 目的軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V01 | Noēsis (理解) | I × E | 世界像を認識目的で更新する | `/noe` |
| V02 | Boulēsis (意志) | I × P | 目標を実用目的で設定する | `/bou` |
| V03 | Zētēsis (探求) | A × E | 認識のために環境に働きかける | `/zet` |
| V04 | Energeia (実行) | A × P | 実用のために環境に働きかける | `/ene` |
| V25 | Theōria (観照) | S × E | 認識目的で世界を受容的に観照する | `/the` |
| V26 | Antilepsis (検知) | S × P | 実用目的で環境変化を検知する | `/ant` |

### Methodos 族 (Flow × Function: 戦略軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V05 | Skepsis (発散) | I × Explore | 仮説空間を広げる | `/ske` |
| V06 | Synagōgē (収束) | I × Exploit | 仮説空間を絞り込む | `/sag` |
| V07 | Peira (実験) | A × Explore | 未知領域で情報を集める | `/pei` |
| V08 | Tekhnē (適用) | A × Exploit | 既知解法を使って確実に成果を出す | `/tek` |
| V27 | Ereuna (探知) | S × Explore | 探索的に環境の信号を走査する | `/ere` |
| V28 | Anagnōsis (参照) | S × Exploit | 既知パターンと照合して信号を読み取る | `/agn` |

### Krisis 族 (Flow × Precision: コミットメント軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V09 | Katalēpsis (確定) | I × C | 信念を固定しコミットする | `/kat` |
| V10 | Epochē (留保) | I × U | 判断を開いて複数可能性を保持する | `/epo` |
| V11 | Proairesis (決断) | A × C | 確信を持って資源を投入する | `/pai` |
| V12 | Dokimasia (打診) | A × U | 小さく一歩を打って反応を見る | `/dok` |
| V29 | Saphēneia (精読) | S × C | 高精度で入力信号を明確に知覚する | `/sap` |
| V30 | Skiagraphia (走査) | S × U | 低精度で広範に入力を走査する | `/ski` |

### Diástasis 族 (Flow × Scale: 空間スケール軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V13 | Analysis (詳細分析)| I × Mi | 局所的に深く推論する | `/lys` |
| V14 | Synopsis (俯瞰) | I × Ma | 広域的に全体を推論する | `/ops` |
| V15 | Akribeia (精密操作)| A × Mi | 局所的に正確に行動する | `/akr` |
| V16 | Architektonikē (全体)| A × Ma | 広域的に一斉に行動する | `/arc` |
| V31 | Prosochē (注視) | S × Mi | 微視的に対象に注意を集中する | `/prs` |
| V32 | Perioptē (一覧) | S × Ma | 巨視的に全体を見渡す | `/per` |

### Orexis 族 (Flow × Valence: 価値方向軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V17 | Bebaiōsis (肯定) | I × + | 信念を強化・承認する | `/beb` |
| V18 | Elenchos (批判) | I × - | 信念を問い直し問題を検知する | `/ele` |
| V19 | Prokopē (推進) | A × + | 成功方向をさらに前進させる | `/kop` |
| V20 | Diorthōsis (是正) | A × - | 問題を修正し方向を変える | `/dio` |
| V33 | Apodochē (傾聴) | S × + | 好意的に入力信号を受容する | `/apo` |
| V34 | Exetasis (吟味) | S × - | 批判的に入力信号を精査する | `/exe` |

### Chronos 族 (Flow × Temporality: 時間方向軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V21 | Hypomnēsis (想起) | I × Past | 過去の信念状態にアクセスする | `/hyp` |
| V22 | Promētheia (予見) | I × Future| 未来の状態を推論・予測する | `/prm` |
| V23 | Anatheōrēsis (省顧)| A × Past | 過去の行動を評価し教訓を抽出する | `/ath` |
| V24 | Proparaskeuē (仕掛)| A × Future| 未来を形成するための先制行動をとる | `/par` |
| V35 | Historiā (回顧) | S × Past | 過去の入力を調査・再検討する | `/his` |
| V36 | Prognōsis (予感) | S × Future| 未来の入力信号を予感する | `/prg` |

---

## 修飾・関係・前動詞 (体系核外)

> v4.1 パラダイムにおいて、これらは独立したモジュールではなく、Poiesis (動詞) の**実行パラメータおよびその結合規則**として再定義された。体系核には含まれない。

| 項目 | 数 | 意味 |
|:-----|---:|:-----|
| Dokimasia (修飾) | **60** | 6修飾座標間の直積 (15辺 × 4極)。動詞のパラメータ。 |
| H-series 前動詞（中動態）| **12** | φ_SA × 6修飾座標 × 2極。μ を迂回する being。`[略記]` 記法。 |
| X-series (結合) | **15** | K₆ の辺。G_{ij} (対称): 平衡的結合強度 (Fisher 情報)。 |
| Q-series (循環) | **15** | K₆ の辺。Q_{ij} (反対称): 非平衡的循環強度。 |

---

## 体系核カバレッジ総括 (44実体)

| 層 | 要素数 | 定義 |
|:---|------:|:----:|
| 公理 | 1 | ✅ |
| 座標 | 7 | ✅ |
| 動詞 (Poiesis) | 36 | ✅ |
| **合計** | **44** | **✅** |

> v4.1 の 32実体から v5.0 で 44実体に拡張。Flow 座標の三値化 (S/I/A) により S極 12動詞を追加。
> v5.1 で H-series 前動詞（中動態）12個を体系核外に追加 (φ_SA × 6修飾座標)。
> 修飾 (Dokimasia)・関係 (X/Q-series)・前動詞 (H-series) は引き続きパラメータとして体系核外。

---

*Generated: 2026-02-21 — v4.1 (32実体)*
*Restored: 2026-02-25 — ca465729f による巻き戻しを修正。WF 列を全24動詞に補完。*
*Updated: 2026-03-22 — v5.0 (44実体: Flow 三値化、S極12動詞追加)*
*Updated: 2026-03-22 — v5.1 (H-series 前動詞（中動態）12個追加。体系核外。[] 記法)*
