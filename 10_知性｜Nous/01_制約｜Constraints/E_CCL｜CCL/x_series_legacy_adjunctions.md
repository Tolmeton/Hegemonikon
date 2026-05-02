---
description: 旧 S-series 随伴対の X-series 射としての明示化
origin: S-series 完全吸収 Plan A (2026-02-26)
status: absorbed
---

# X-series Legacy Adjunctions

> 旧 v3.x Schema 座標に存在した随伴対を、v4.1 体系の X-series 射として再定義する。
> これらの対は v4.1 動詞間の自然変換として既に内包されているが、
> 歴史的経緯の明示と、`/met` `/mek` `/sta` `/pra` を打った時の
> 認知的文脈の保存のために記録する。

---

## 旧随伴対 → v4.1 射の対応

### Metron ⊣ Stathmos → Analysis ⊣ Synopsis + Krisis 族

| 旧対 | v4.1 射 | 意味 |
|:-----|:--------|:-----|
| Metron (F: 測る) | V13 Analysis `/lys` | 局所的に深く測る → 分析 |
| Stathmos (G: 基準を置く) | V09 Katalēpsis `/kat` | 基準を確定する → 信念固定 |
| F ⊣ G (測定⊣基準) | `/lys` → `/kat` | 分析結果を基準として確定する射 |

**FEP 解釈**: Metron は precision weighting (π) の**計算**、Stathmos は π の**固定**。
v4.1 では `/lys` が計算を、`/kat` が固定を担い、この随伴対は Methodos×Krisis 間の
X-series 射 `X[lys→kat]` として保存される。

**派生の帰属先**:

| 旧派生 | 個数 | 帰属先 |
|:-------|:-----|:-------|
| /met 派生 | 14 | /ops, /lys, /kat, /sag, /ske, /epo, /akr |
| /sta 派生 | 17 | /kat, /ops, /sag, /dok, /pei, /pai |

---

### Mekhanē ⊣ Praxis → Tekhnē ⊣ Peira (既存)

| 旧対 | v4.1 射 | 意味 |
|:-----|:--------|:-----|
| Mekhanē (F: 方法を作る) | V08 Tekhnē `/tek` | 既知手法で確実に実行 |
| Praxis (G: 実践する) | V07 Peira `/pei` | 未知領域で実験する |
| F ⊣ G (方法⊣実践) | `/pei` ⊣ `/tek` | v4.1 の Peira ⊣ Tekhnē そのもの |

**FEP 解釈**: Mekhanē は Action × Function の**Exploit 側** = 手法の確実適用、
Praxis は Action × Function の**Explore 側** = 実践的実験。
v4.1 の Peira ⊣ Tekhnē 随伴対は**そのまま**この旧対を継承している。

**派生の帰属先**:

| 旧派生 | 個数 | 帰属先 |
|:-------|:-----|:-------|
| /mek 派生 | 3 (+サブモジュール) | /tek (tekhne, +サブモジュール6種), /ele (diag), /dio (impr) |
| /pra 派生 | 3 | /pei (prax), /tek (pois), /par (temp) |

---

## エイリアス (expander.py)

| 旧コマンド | リダイレクト先 | 理由 |
|:-----------|:--------------|:-----|
| `/met` | `/lys` (V13 Analysis) | Metron の主機能 = 測定・分析 |
| `/mek` | `/tek` (V08 Tekhnē) | Mekhanē の主機能 = 手法適用 |
| `/sta` | `/kat` (V09 Katalēpsis) | Stathmos の主機能 = 基準確定 |
| `/pra` | `/pei` (V07 Peira) | Praxis の主機能 = 実践・実験 |

---

*Created: 2026-02-26 — S-series 完全吸収 Phase 3*
