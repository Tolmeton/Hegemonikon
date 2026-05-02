---
rom_id: rom_2026-03-23_cps_directed_complementarity
session_id: b7a746ea-8994-4c8c-8336-afd536233c14
created_at: 2026-03-23 17:20
rom_type: distilled
reliability: High
topics: [CPS, 方向付き相補性, Θパラメータ, Fourier マスク, 3双対性, QM, GR, MB, 容器内容非対称]
exec_summary: |
  ④「力とは忘却である」§4.6c を全面修正。CPS1 (対称的相補性) → CPS1'' (方向付き相補性) に更新。
  Θ パラメータで QM/MB/GR を連続族として統一。Fourier のマスク効果の正体を定式化。
  確信度 55% → 75%。
---

# CPS1'' 方向付き相補性と Θ パラメータ統一

> **[DECISION]** CPS1 の対称性仮定を放棄。CPS1'' (方向付き相補性) に修正。

## 核心的発見: 相補性は非対称

> **[DISCOVERY]** 3ケース全てで「容器 > 内容」の非対称性が存在:
> - QM: 位置 > 運動量 (p = m·dx/dt は x を前提)
> - GR: 時空 > 質量 (T=0 の真空解が存在)
> - MB: 身体 > 心 (岩は身体のみで存在)

> **[DISCOVERY]** QM の「対称性」は Fourier のマスク効果:
> ψ̃(k) = ∫ψ(x)e^{-ikx}dx — 運動量表現は位置表現から構成される。
> Fourier は「導出操作」であって「独立定義」ではない。
> Θ = 0 (完全同型) が存在論的非対称性を表現的対称性でマスクする。

## Θ パラメータによる統一

| Θ | 領域 | 架橋 T | 非対称性 | 容器/内容 |
|:--|:--|:--|:--|:--|
| 0 | QM | Fourier (同型) | マスク | 位置/運動量 |
| (0,∞) | MB | blanket (非同型) | 可視 | 身体/心 |
| ∞ | GR真空 | 不在 | 完全 | 時空/— |

## CPS1'' 公理 (改訂版)

```
(CPS1'') U_ctr は独立に well-defined。U_cnt は U_ctr に依存。
(CPS5)   Θ ∈ [0, ∞]: T の同型度。Θ↑ → 非対称性↑
```

## 帰結

> **[DISCOVERY]** QM = MB の極限 (Θ→0), GR真空 = MB の退化 (Θ→∞)
> **[DISCOVERY]** ビッグバン = Θ=∞ → Θ<∞ の位相転移 (対称性の自発的破れの CPS 版)

## 確信度と残存課題

> [推定 75%]: CPS1'' は水準 B。Θ 統一は水準 B-。
> 残存: GR の圏論的定式化、Θ の物理的定量化、Fourier のマスク効果の圏論的証明。

## 関連情報
- 変更ファイル: [力とは忘却である_v1.md](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/力とは忘却である_v1.md) §4.6c
- 前提 ROM: rom_2026-03-23_integration_proposition.md (kalon.typos §2.6-2.8)
- 関連 Session: b7a746ea (本セッション)

<!-- ROM_GUIDE
primary_use: CPS 方向付き相補性とΘパラメータによる3双対性の統一理論
retrieval_keywords: CPS, CPS1'', 方向付き相補性, Θ, マスクパラメータ, Fourier マスク, 容器内容, directed complementarity
expiry: permanent
-->
