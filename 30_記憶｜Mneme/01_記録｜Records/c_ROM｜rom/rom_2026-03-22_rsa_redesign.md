---
rom_id: rom_2026-03-22_rsa_redesign
session_id: 7e81ab81-ee69-4a76-8d26-9ee21e993b55
created_at: 2026-03-22 00:53
rom_type: distilled
reliability: High
topics: [R(s,a), mutual_information, bigram, CCL, BUTTONInstruct, Toucan, theta_b, FEP, Value_axis]
exec_summary: |
  R(s,a) を統一的情報理論手法で再計算。HGK+ (conv/ 456 セッション, 37,606 イベント) で R=0.1098、
  BUTTONInstruct (ICLR 2025, 8K件) で R=0.9812。R(s,a) は環境依存パラメータ。
  v3 ハードコード値 (0.67/0.71) は MCPToolBench++ (1問1答) 由来で廃棄。
---

# R(s,a) 再設計: 環境依存パラメータとしての再定式化

> **[DECISION]** R(s,a) は固定値ではなく環境・タスク・認知スタイルに依存するパラメータ。
> Θ(B) 計算式の中で sensitivity analysis の対象として扱う。

## 定義

> **[DEF]** R(s,a) = I(S;A) = H(S) + H(A) - H(S,A)
> S, A は認知イベントの Value 軸 (I=Internal/Sensory, A=Ambient/Active) の bigram カウント。
> CCL 24 動詞は FEP Value 軸で I/A に分類済み。

## 結果比較

> **[FACT]** 3データセットの R(s,a) 値:

| データセット | R(s,a) | R_norm | イベント数 | I→I | I→A | A→I | A→A |
|:--|--:|--:|--:|--:|--:|--:|--:|
| HGK+ tape (WF のみ) | 0.034 | 0.037 | 507 | — | — | — | — |
| HGK+ conv/ (全認知活動) | 0.1098 | 0.1162 | 37,606 | 78% | 22% | 39% | 61% |
| BUTTONInstruct (ICLR 2025) | 0.9812 | 1.000 | 57,626 | 0% | 100% | 100% | 0% |

> **[DISCOVERY]** HGK+ の I→I = 78% は「考えてから動く」認知スタイルの定量的証拠。
> /noe→/ele→/ops のような認識の連鎖が支配的で、認識フェーズと行動フェーズが分離。

> **[DISCOVERY]** BUTTONInstruct の R≈1.0 は「構造的退屈」— user→assistant→tool の
> 完全交互パターン。情報理論的最大結合だが認知の豊かさを反映しない。

## スクリプト

| ファイル | 用途 | 場所 |
|:--|:--|:--|
| compute_rsa_conv.py | conv/ 全認知活動 R(s,a) | theta_b_external/ |
| compute_rsa_button.py | BUTTONInstruct R(s,a) | /tmp/ (要移動) |

## 決定事項

> **[DECISION]** MCPToolBench++ (v3 値 0.67/0.71) は廃棄。1問1答ベンチマークで R(s,a) を測定する意味がない。

> **[DECISION]** 論文では R(s,a) を以下の3値で報告:
> - R(s,a)_HGK = 0.11 (実セッション、認識凝集型)
> - R(s,a)_benchmark = 0.98 (ベンチマーク上界、機械的交互型)
> - R(s,a) は Θ(B) の sensitivity analysis パラメータ

## 未完了: Toucan 取得

> **[CONTEXT]** Toucan (IBM + U of Washington, HuggingFace Agent-Ark/Toucan-1.5M):
> - 150万 trajectory, 495 MCP, 2000+ tools
> - multi-turn subset あり (single-turn-original/irrelevant/single-turn-diversify/multi-turn)
> - HuggingFace API が一貫して応答なし (データセット巨大すぎてサーバー側タイムアウト)
> - **ネットワーク安定時に再試行**: `datasets` ライブラリ (pip install datasets) で streaming=True で取得する
> - 目的: BUTTONInstruct とは異なる multi-turn パターンで R(s,a) の変動幅を検証

## 関連情報
- 関連 WF: /t, /m (Peras 系)
- 関連 KI: circulation_taxis.md (Q-series)
- 関連論文: llm_body_draft.md §4.4.1, §5.9

<!-- ROM_GUIDE
primary_use: R(s,a) の値を論文に統合する際の参照
retrieval_keywords: R(s,a), mutual information, bigram, sensory-active coupling, BUTTONInstruct, Toucan, HGK+, θ(B), environment parameter
expiry: permanent (計測結果)
-->
