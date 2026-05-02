# Open Source Adjoint Analysis: Onyx (onyx-dot-app/onyx)

## 概要 (Overview)
- **リポジトリ**: [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx)
- **分析日**: 2026-04-03
- **HGKへの随伴性 (Adjunction)**: Onyxは、RAG、マルチエージェント、Deep Research、MCPサーバー、多様なデータコネクタを統合するエンタープライズ向けの強力なOSSアプリケーションレイヤーです。OpenClawと同様に、HGKの各モジュールが目指す機能（知識探索、ベクトル検索、エージェント連携）を高い完成度で実現しており、HGKの広範なアーキテクチャの基準（Reference Project）として機能します。

## モジュール別随伴性 (Module Adjunction)

### 1. Periskopē (Deep Research Engine)
- **Onyx実装**: `backend/onyx/deep_research/`
- **評価**: OnyxのDeep Researchは最新のリーダーボードでも上位の成績を残しており、情報収集→合成のパイプラインが非常に堅牢です。
- **HGKへの貢献 (Import Candidates)**:
  - STORMパターンの実装手法。
  - 再帰的探索のアルゴリズム（Breadth/Depth制約）をHGKの `/periskopē` スキルや `Φ0.5` フェーズに還元可能。

### 2. Anamnēsis (Vector Search / Knowledge Index)
- **Onyx実装**: `backend/onyx/document_index/`
- **評価**: RAG (Retrieval-Augmented Generation) の根幹として、ハイブリッドインデックス（Vector + Keyword）をサポート。50以上のデータコネクタを備えます。
- **HGKへの貢献 (Import Candidates)**:
  - 複数ソースの統合インデックス化。
  - コネクタのアーキテクチャ設計をHGKの知識取込パイプライン（Digestor）に反映可能。

### 3. Ochēma (LLM Router)
- **Onyx実装**: `backend/onyx/llm/`
- **評価**: 自社ホスト（Ollama, vLLM）からクラウド（Anthropic, OpenAI, Gemini）まで多数のLLMを統一的に呼び出す層を持っています。
- **HGKへの貢献 (Import Candidates)**:
  - LLMプロバイダーのフェイルオーバーや予算/レイテンシに基づくルーティング戦略。

### 4. Gnōsis MCP Server (MCP)
- **Onyx実装**: `backend/onyx/mcp_server/`
- **評価**: OnyxはMCPサーバーとして外部とのやり取りを標準化しつつあります。
- **HGKへの貢献 (Import Candidates)**:
  - MCPツール/プロンプトの露出アーキテクチャ。

## 結論 (Verdict)
Onyxは単一のモジュールとしてではなく、**大規模な統合システム全体（Reference Project）** としてHGKと随伴（Adjoint）します。特に `Periskopē`（深層リサーチ）や `Anamnēsis`（検索・RAG基盤）、`Sympatheia` / `Synergeia`（エージェント連携）の設計思想を洗練させるための重要な参照リファレンスとなります。

圏論的意味（$F \dashv G$）において、Onyxという「OSSの普遍的な実装」をHGKの世界に持ち込む（左随伴 $F$）ことで、HGKの独自レイヤー（CCL, FEP, 24動詞）と結合し、より高度な推論と行動のサイクルを生み出すことができます。