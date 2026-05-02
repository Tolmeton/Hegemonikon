# IMPL_SPEC: F7 — 3D Knowledge Base (3DKB)

## 1. 概要
Three.js/React ベースの3Dナレッジベース。KI、論文、セッションをノードとして、関連度をエッジとして表現する。3Dビジュアライゼーション、フィルタリング、ズーム機能により、知識の構造を直感的に理解できる。

## 2. アーキテクチャ

### 2.1 コンポーネント図

```
KI/Paper/Session Data
    ↓
Data Ingestion
    ↓
Data Transformation (関連度計算)
    ↓
Graph Database (ノード + エッジ)
    ↓
3D Visualization Engine
    ↓
Three.js/React UI
    ├── Filtering Controls (種類・関連度フィルタ)
    └── Zoom Controls (ズームイン/アウト)
```

### 2.2 データフロー

1. **データ入力**: KI/Paper/Session Data が Data Ingestion に入力
2. **データ変換**: グラフDB向け形式に変換、関連度計算
3. **グラフDB格納**: ノード（KI/論文/セッション）＋エッジ（関連度）
4. **3Dシーン生成**: Three.js で3D空間にノード・エッジを配置
5. **UI操作**: React UI でフィルタリング・ズーム操作

### 2.3 ノード/エッジ仕様 (AMBITION.md準拠)

| ノード種別 | ソース | 色 |
|:-----------|:-------|:---|
| KI (Sophia) | Sophia インデックス | 青 |
| 論文 (Gnōsis) | Gnōsis インデックス | 緑 |
| セッション | F2 のリンク構造 | 白 |

| エッジ種別 | 意味 | 色 |
|:-----------|:-----|:---|
| KI → 論文 | 参照関係 | 黄 |
| セッション → セッション | F2 リンク | 白 |
| KI → KI | 概念的関連 | 紫 |

## 3. API仕様
TODO — `/api/3dkb/graph`, `/api/3dkb/nodes`, `/api/3dkb/edges`

## 4. データモデル
TODO — GraphNode, GraphEdge, GraphFilter

## 5. 実装ステップ (Phase)
TODO — sprint1_three_js_spec.md 参照

## 6. テスト戦略
TODO

## 7. 依存関係
- Three.js r128+ / React
- Sophia (KI), Gnōsis (論文), Kairos (セッション)
- PKS Search (関連度ベクトル)
- `90_保管庫｜Archive/20_Mekhane_Archive/hgk_docs_archive/_archive/sprint1_three_js_spec.md` (既存仕様)
