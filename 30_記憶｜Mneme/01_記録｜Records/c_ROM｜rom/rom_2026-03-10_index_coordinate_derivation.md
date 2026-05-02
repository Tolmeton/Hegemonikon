---
rom_id: rom_2026-03-10_index_coordinate_derivation
session_id: 0e1a0ad4-5dea-40bd-a473-10dcbd6c9617
created_at: 2026-03-10 12:24
rom_type: distilled
reliability: High
topics: [unified_index, axiom, chunk, morphism, renormalization_group, fep_coordinates, derivation]
---

# ROM: 統一インデックス公理 — チャンク意味空間からの座標導出

## セッション文脈
- /noe+ で統一インデックス公理 v0.1 (5+1公理) を生成
- /ele+ で全6公理を論駁。「設計決定であり公理ではない」
- 米田 (Yoneda) を単一公理として提案 → Creator が「全インデックスを説明できる？情報理論は？」
- IB (Information Bottleneck) に修正 → 正しいが ugly (Kalon ではない)
- Creator の直感: 「索引 = チャンク最小単位の射の構造化」+ 「インデックスの再帰」
- Friston 2025 "From pixels to planning: scale-free active inference" (RGM) が直接接続
  - 繰り込み群 (Renormalization Group) による階層的粗視化 = Creator の「再帰的インデックス」
  - FEP + RG = scale-free active inference
- Creator の新指示: 「チャンクの意味空間の特性からインデックス座標を導出したい」
  - FEP 座標導出ファイル (derivation_correct_fep_coordinates) の方法論と同型

## 核心的到達点

### FEP 座標導出の方法論 (SOURCE: derivation_correct_fep_coordinates_2026-03-09.md)
```
FEP (公理) → NESS定理 → MB → VFE最小化 → mean-field因子化 → 7座標
```
- Layer A: 純粋演繹 (FEP → Flow)
- Layer B: 半演繹 (VFE/EFE → Value/Function/Precision)
- Layer C: FEP内追加定理 (Temporality/Scale/Valence)
- 核心発見: mean-field 因子化は「近似」ではなく VFE complexity 最小化の「帰結」

### 転写すべきアナロジー
```
FEP 座標導出:    FEP → VFE最小化 → mean-field因子化 → 座標 → 随伴対 → 7
索引座標導出(?): チャンク意味空間 → ???最小化 → ???因子化 → 座標 → ??? → N
```

### 候補: RG による粗視化が「因子化」に対応
- FEP: VFE complexity 最小化 → 因子化 q(s)·q(π)·q(ω)
- 索引: 検索 VFE 最小化 → 粗視化 (RG) → スケール別因子化
- 各スケールの因子が「索引の座標」に対応する可能性

## 未解決の問い
1. チャンク意味空間の「公理」は何か？(FEP に対応するもの)
2. 索引の「VFE」は何か？(Information Bottleneck の max I(T;Y) - β·I(X;T)?)
3. 粗視化の各レベルが「座標」として分離できるか？
4. 射 (morphism) としてのマッチ度スペクトラムの形式化
5. 再帰的インデックスの停止条件

## 直前文脈
- Creator は「ともに模索しよう」と宣言。共同探索モード。
- /u で本音を述べるフェーズ。

---
*Burned at 2026-03-10 12:24 — Session 0e1a0ad4*
