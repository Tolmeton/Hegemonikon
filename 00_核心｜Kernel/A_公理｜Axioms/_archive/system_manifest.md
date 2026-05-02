---
doc_id: "SYSTEM_MANIFEST"
version: "5.3.0"
tier: "KERNEL"
status: "CANONICAL"
lineage: "v1.0 (96要素) → v4.1 (32実体) → v5.0 (44実体) → v5.1 (H-series 12) → v5.2 (体系核45+準核12) → v5.3 (三角柱モデル: L3 48 0-cell) → **v5.4 (K₄柱モデル: 体系核57, H-series昇格)**"
---

# System Manifest — 体系核 57 (v5.4)

> **唯一の公理**: FEP (予測誤差最小化)
> **体系核**: 57 = 1 + 8 + 48
> **修飾/関係**: パラメータとして分離 (体系核外)

---

## 公理 (1)

| ID | 名称 | 定義箇所 | 存在証明 |
|:---|:-----|:---------|:---------|
| A0 | FEP (Free Energy Principle) | [axiom_hierarchy.md](axiom_hierarchy.md) | FEP 自体が公理 — 証明不要 |

---

## 座標 (8 = 2+3+3)

| d | Question | 座標 | Opposition | 定義箇所 |
|:-:|:---------|:-----|:-----------|:---------|
| 1 | Who (input) | **Afferent** | Yes (∂f/∂η≠0) ↔ No | [axiom_hierarchy.md](axiom_hierarchy.md) |
| 1 | Who (output) | **Efferent** | Yes (∂f/∂μ≠0) ↔ No | 同上 |
| 2 | Why | **Value** | E (認識) ↔ P (実用) | 同上 |
| 2 | How | **Function** | Explore ↔ Exploit | 同上 |
| 2 | How much | **Precision**| C (確信) ↔ U (留保) | 同上 |
| 3 | Where | **Scale** | Micro ↔ Macro | 同上 |
| 3 | Which | **Valence** | + (接近) ↔ - (回避) | 同上 |
| 2 | When | **Temporality**| Past (過去) ↔ Future (未来) | 同上 |

> **v5.2-v5.4 変更**: Flow を Afferent×Efferent の2座標に分解 (v5.2)。
> 4象限: S (Aff=Y,Eff=N), I (N,N), A (N,Y), S∩A (Y,Y)。
> v5.4 にて第4象限 S∩A から生じる H-series (12) を準核から体系核へ昇格。4象限対等な K₄柱モデルへ移行。

---

## 認知操作 (48 = 4象限 × 6族 × 2極)

> Afferent×Efferentの4象限 (S/I/A/S∩A) × 6修飾座標 × 2極 = 48 (体系核)。doing/being は Hom空間 Drift で連続的に表現される。

### Telos 族 (Flow × Value: 目的軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V01 | Noēsis (理解) | I × E | 世界像を認識目的で更新する | `/noe` |
| V02 | Boulēsis (意志) | I × P | 目標を実用目的で設定する | `/bou` |
| V03 | Zētēsis (探求) | A × E | 認識のために環境に働きかける | `/zet` |
| V04 | Energeia (実行) | A × P | 実用のために環境に働きかける | `/ene` |
| V25 | Theōria (観照) | S × E | 認識目的で世界を受容的に観照する | `/the` |
| V26 | Antilepsis (検知) | S × P | 実用目的で環境変化を検知する | `/ant` |
| H01 | Tropē (向変) | S∩A × E | 外的信号に無意識的に向かう | `[tr]` |
| H02 | Synaisthēsis (体感) | S∩A × P | 内的信号に無意識的に応答する | `[sy]` |

### Methodos 族 (Flow × Function: 戦略軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V05 | Skepsis (発散) | I × Explore | 仮説空間を広げる | `/ske` |
| V06 | Synagōgē (収束) | I × Exploit | 仮説空間を絞り込む | `/sag` |
| V07 | Peira (実験) | A × Explore | 未知領域で情報を集める | `/pei` |
| V08 | Tekhnē (適用) | A × Exploit | 既知解法を使って確実に成果を出す | `/tek` |
| V27 | Ereuna (探知) | S × Explore | 探索的に環境の信号を走査する | `/ere` |
| V28 | Anagnōsis (参照) | S × Exploit | 既知パターンと照合して信号を読み取る | `/agn` |
| H03 | Paidia (遊戯) | S∩A × Explore | 考えず試す感覚運動的遊び | `[pa]` |
| H04 | Hexis (習態) | S∩A × Exploit | 考えず繰り返す習慣化した技能 | `[he]` |

### Krisis 族 (Flow × Precision: コミットメント軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V09 | Katalēpsis (確定) | I × C | 信念を固定しコミットする | `/kat` |
| V10 | Epochē (留保) | I × U | 判断を開いて複数可能性を保持する | `/epo` |
| V11 | Proairesis (決断) | A × C | 確信を持って資源を投入する | `/pai` |
| V12 | Dokimasia (打診) | A × U | 小さく一歩を打って反応を見る | `/dok` |
| V29 | Saphēneia (精読) | S × C | 高精度で入力信号を明確に知覚する | `/sap` |
| V30 | Skiagraphia (走査) | S × U | 低精度で広範に入力を走査する | `/ski` |
| H05 | Ekplēxis (驚愕) | S∩A × C | 高確信の即時反応 (alarm) | `[ek]` |
| H06 | Thambos (戸惑い) | S∩A × U | 言語化以前の「何かおかしい」 | `[th]` |

### Diástasis 族 (Flow × Scale: 空間スケール軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V13 | Analysis (詳細分析)| I × Mi | 局所的に深く推論する | `/lys` |
| V14 | Synopsis (俯瞰) | I × Ma | 広域的に全体を推論する | `/ops` |
| V15 | Akribeia (精密操作)| A × Mi | 局所的に正確に行動する | `/akr` |
| V16 | Architektonikē (全体)| A × Ma | 広域的に一斉に行動する | `/arh` |
| V31 | Prosochē (注視) | S × Mi | 微視的に対象に注意を集中する | `/prs` |
| V32 | Perioptē (一覧) | S × Ma | 巨視的に全体を見渡す | `/per` |
| H07 | Euarmostia (微調和) | S∩A × Mi | 無意識の局所的調和 | `[eu]` |
| H08 | Synhorasis (一望) | S∩A × Ma | 一瞬のゲシュタルト認識+応答 | `[sh]` |

### Orexis 族 (Flow × Valence: 価値方向軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V17 | Bebaiōsis (肯定) | I × + | 信念を強化・承認する | `/beb` |
| V18 | Elenchos (批判) | I × - | 信念を問い直し問題を検知する | `/ele` |
| V19 | Prokopē (推進) | A × + | 成功方向をさらに前進させる | `/kop` |
| V20 | Diorthōsis (是正) | A × - | 問題を修正し方向を変える | `/dio` |
| V33 | Apodochē (傾聴) | S × + | 好意的に入力信号を受容する | `/apo` |
| V34 | Exetasis (吟味) | S × - | 批判的に入力信号を精査する | `/exe` |
| H09 | Hormē (衝動) | S∩A × + | 対象に向かう原初的接近 | `[ho]` |
| H10 | Phobos (恐怖) | S∩A × - | 対象から離れる原初的退避 | `[ph]` |

### Chronos 族 (Flow × Temporality: 時間方向軸)

| ID | 名称 (ギリシャ語) | 生成 | 意味 | WF |
|:---|:------------------|:-----|:-----|:---|
| V21 | Hypomnēsis (想起) | I × Past | 過去の信念状態にアクセスする | `/hyp` |
| V22 | Promētheia (予見) | I × Future| 未来の状態を推論・予測する | `/prm` |
| V23 | Anatheōrēsis (省顧)| A × Past | 過去の行動を評価し教訓を抽出する | `/ath` |
| V24 | Proparaskeuē (仕掛)| A × Future| 未来を形成するための先制行動をとる | `/par` |
| V35 | Historiā (回顧) | S × Past | 過去の入力を調査・再検討する | `/his` |
| V36 | Prognōsis (予感) | S × Future| 未来の入力信号を予感する | `/prg` |
| H11 | Anamnēsis (想起再現)| S∩A × Past | 記憶が自動的に行動を再現 | `[an]` |
| H12 | Prolepsis (予期反射)| S∩A × Future| 予測が自動的に準備行動を生む | `[pl]` |

---

## 修飾・関係 (体系核外)

| 項目 | 数 | 意味 |
|:-----|---:|:-----|
| Dokimasia (修飾) | **60** | 6修飾座標間の直積 (15辺 × 4極)。動詞のパラメータ。 |
| X-series (結合) | **15** | K₆ の辺。G_{ij} (対称): 平衡的結合強度。 |
| Q-series (循環) | **15** | K₆ の辺。Q_{ij} (反対称): 非平衡的循環強度。 |

---

## 体系カバレッジ総括 (v5.3)

| 層 | 要素数 | 分類 |
|:---|------:|:----:|
| 公理 | 1 | 体系核 |
| 座標 (Afferent+Efferent+6修飾) | 8 | 体系核 |
| 認知操作 (4象限 × 6mod × 2極) | 48 | 体系核 |
| **体系核 合計** | **57** | ✅ |

> v5.4: Flow を Afferent×Efferent に分解し4象限が対等の K₄柱モデルへ。S∩A 象限 (H-series) を体系核に統合。

---

*Generated: 2026-02-21 — v4.1 (32実体)*
*Updated: 2026-03-22 — v5.0 (44実体: Flow 三値化、S極12動詞追加)*
*Updated: 2026-03-22 — v5.1 (H-series 前動詞12個追加。体系核外)*
*Updated: 2026-03-23 — v5.2 (体系核45: Afferent×Efferent 分解、座標8、H-series 体系準核昇格)*
*Updated: 2026-03-25 — v5.4 (K₄柱モデル: 体系核57、H-series 体系核昇格、各族 8動詞/族)*
*Updated: 2026-03-25 — v5.4 (K₄柱モデル: 体系核57, S∩A象制限撤廃と体系核昇格)*
