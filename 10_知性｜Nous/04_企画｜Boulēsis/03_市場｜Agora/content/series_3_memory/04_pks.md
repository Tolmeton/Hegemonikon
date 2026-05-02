
技術記事ライターとして、NoteやZennでの公開を想定した記事を作成しました。
シリーズ最終回として、技術的な詳細と全体の世界観を統合する構成にしています。

---

# 34,085のドキュメントを瞬時に横断検索するCLIツール「PKS」を作った話【記憶スタック #4】

「あれ、この話ってどこで見たんだっけ？」

エンジニアやリサーチャーなら、1日に何度もこの感覚に襲われるはずです。
読み込んだ論文の中だったか、自分で書いた技術メモ（KI）だったか、あるいは昨日の作業ログ（Handoff）だったか。

情報は増える一方なのに、それを探すための「場所」は散らばっています。論文はPDF管理ツール、メモはObsidian、ログはNotionやテキストファイル……。これでは、せっかく蓄積した知識も、いざという時に引き出せなければ死蔵されているのと同じです。

**「AIのための記憶」を設計するシリーズ「記憶スタック」、最終回となる第4回は、これまでに構築したすべての知識ソースをたった一つのコマンドで横断検索するCLIツール、「PKS (Polis Knowledge System)」の実装について解説します。**

34,085件（執筆時点）のドキュメントから、論文も、個人的なメモも、日々のログも、すべてをフラットに検索し、ランク付けして提示するシステムです。

## なぜ「統合検索」が必要なのか？

これまでの連載で、私たちは以下の3つのシステムを構築してきました。

1.  **Kairos (カイロス):** 毎日のコンテキストを受け渡すHandoffシステム
2.  **Sophia (ソフィア):** 技術的知見を蓄積するナレッジベース
3.  **Gnōsis (グノーシス):** 論文を消化・要約するパイプライン

これらは個別に機能していますが、人間の脳（あるいは高度なAIアシスタント）が思考する際、ソースの違いは重要ではありません。「TransformerのAttention機構」について考えるとき、論文の定義も、自分が過去に書いた実装メモも、同時に参照できるべきです。

そこで開発したのが、これらを束ねる **PKS (Polis Knowledge System)** です。

### 統合対象となる4つの柱

PKSが検索対象とするのは以下の4つの領域です。

| システム名 | 役割 | データ形式 | 件数(概算) |
| :--- | :--- | :--- | :--- |
| **Gnōsis** | 論文・書籍の要約と原文 | PDF / Markdown | 4,200+ |
| **Sophia** | 構造化された技術ナレッジ | Markdown (Obsidian) | 1,500+ |
| **Kairos** | 日々の作業ログ・Handoff | Markdown / JSON | 800+ |
| **Chronos** | 自動収集された時系列ログ | Log / JSON | 27,000+ |
| **Total** | **全知識ベース** | | **34,085** |

これらを個別のツールで開いて検索するのは時間の無駄です。ターミナルから一発で引けるようにします。

## アーキテクチャ：異なる世界を繋ぐ

PKSはPython製のCLIツールとして実装されています。
最大の課題は、**「性質の異なるデータソースをどうやって横断検索し、同一の基準でスコアリングするか」**という点にありました。

### Adapterパターンの採用

各データソース（Gnōsis, Sophia, Kairos...）は保存場所もフォーマットも検索ロジックも異なります。そこで、共通のインターフェースを持つ `Adapter` を用意しました。

```python
class SearchAdapter(ABC):
    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        pass

# 例: 論文検索用アダプタ
class GnosisAdapter(SearchAdapter):
    def search(self, query: str):
        # ベクトル検索とキーワード検索のハイブリッド
        ...
```

PKS本体（Core）は、登録されたアダプタに対して並列にリクエストを投げ、返ってきた結果を統合（Merge & Rank）して表示するだけです。これにより、将来的に「Slackのログ」や「GitHubのIssue」を検索対象に加えたくなっても、新しいAdapterを書くだけで拡張可能です。

## CLIでの検索体験

実際に動いている様子を見てみましょう。
例えば、**「FEP (Free Energy Principle) における attention (注意) の役割」**について調べたいとします。

コマンド一発です。

```bash
$ pks search "FEP attention" --limit 5
```

出力結果（イメージ）は以下のようになります。

```text
🔍 PKS Search Result for: "FEP attention"
------------------------------------------------------------
[1] 📄 Gnōsis (Paper) | Score: 0.92
    Title: A Free Energy Principle for a Particular Physics
    Summary: ...attention is conceptualized as precision weighting of prediction errors...
    Path: /mnt/data/papers/friston_2019.pdf

[2] 🧠 Sophia (Knowledge) | Score: 0.88
    Title: 実装メモ: 能動的推論エージェントの注意機構
    Snippet: ...カルマンフィルタのゲインとしてAttentionを実装する際の注意点...
    Path: /obsidian/dev/active_inference_impl.md

[3] 🔄 Kairos (Handoff) | Score: 0.75
    Date: 2023-10-14
    Context: 昨日読んだFEPの論文、Attentionの定式化がTransformerと似ていることに気づいた。
    Path: /daily/2023/10/14.md

... (以下略)
```

**ここでのポイントは、論文（理論）と、実装メモ（実践）と、過去の日記（思考の過程）が、関連度順に混ざって出てくることです。**
「あ、そういえば去年の10月にこれについて考えてたな」という再発見が、このツール最大の価値です。

## 実装の工夫：スコアの正規化

技術的に最も苦労したのはランキングです。
全文検索エンジン（Elasticsearch等）のスコアと、ベクトル検索（OpenAI Embeddings等）のコサイン類似度は、数値のスケールが全く異なります。

そのままソートすると、特定のソースばかりが上位に来てしまいます。そこで、各アダプタ内でスコアを **0.0 〜 1.0 に正規化** するロジックを組み込みました。

```python
def normalize_scores(results: List[RawResult]) -> List[SearchResult]:
    if not results:
        return []
    
    # スコアの最大値・最小値を取得
    max_score = max(r.score for r in results)
    min_score = min(r.score for r in results)
    
    if max_score == min_score:
        return [SearchResult(..., normalized_score=1.0) for r in results]

    # Min-Max Scaling
    for r in results:
        r.normalized_score = (r.score - min_score) / (max_score - min_score)
        
        # ソースごとの重み付け（論文は信頼度が高いので係数を掛けるなど）
        r.final_score = r.normalized_score * SOURCE_WEIGHT[r.source_type]
    
    return results
```

このように「正規化 + ソース別重み付け」を行うことで、直感的に納得感のある検索順位を実現しています。

## ヘルスチェック機能

3万件以上のドキュメントと複数のパイプラインが動いていると、「いつの間にか同期が止まっていた」という事故が起きます。
そこで、PKSには全システムの健康診断コマンドも実装しました。

```bash
$ pks health
```

```text
🏥 PKS System Health Report
----------------------------------------
✅ [Gnōsis]  Vector DB Connection: OK (4,215 records)
✅ [Sophia]  Obsidian Vault: OK (Last sync: 10min ago)
⚠️ [Kairos]  Daily Log: WARNING (Today's log not created yet)
✅ [Chronos] Log Stream: OK
----------------------------------------
System Status: 🟡 DEGRADED (Check Kairos)
```

これにより、朝一番にこのコマンドを叩くだけで、自分の「外部記憶」が正常に機能しているかを確認できます。

## シリーズまとめ：AI時代の「記憶」を設計する

全4回にわたり、「記憶スタック」の構築について解説してきました。最後に全体を振り返ります。

1.  **第1回：Handoff (Kairos)**
    *   **課題:** AIとの対話や作業コンテキストが毎回リセットされる。
    *   **解決:** 「申し送り」の概念を導入し、昨日の自分から今日の自分（とAI）へコンテキストを繋ぐ。
2.  **第2回：Local RAG (Sophia)**
    *   **課題:** 一般的なAIは私の個人的な技術メモを知らない。
    *   **解決:** Obsidian等のローカルメモをベクトル化し、AIが参照できる「長期記憶」にする。
3.  **第3回：Paper Pipeline (Gnōsis)**
    *   **課題:** 論文を積読するだけで消化できない。
    *   **解決:** LLMを使った自動要約パイプラインを構築し、構造化データとして保存する。
4.  **第4回：Unified Search (PKS)**
    *   **課題:** 情報源が増えすぎて探せない。
    *   **解決:** 全ソースを横断検索するCLIを構築し、知識を統合する。

### 結論：記憶は「溜める」ものではなく「設計」するもの

このシリーズを通じて伝えたかったのは、**「ただログやメモを溜め込むだけでは、AI時代のアセットにはならない」**ということです。

*   検索可能なフォーマットにする
*   文脈（コンテキスト）を含める
*   システム間で連携させる

この「記憶の設計（Memory Design）」を行うことで、初めてAIは単なるチャットボットを超え、あなたの思考を拡張するパートナーになります。

## 読者が明日から試せること

いきなりPKSのような統合ツールを作るのは大変です。まずは以下のステップから始めてみてください。

1.  **検索エイリアスの統合:**
    `grep` や `ripgrep` などのコマンドで、ソースコードディレクトリとメモディレクトリを同時に検索するエイリアスを作ってみましょう。
    ```bash
    # .bashrc / .zshrc
    function search_all() {
        echo "=== Code ==="
        rg "$1" ~/projects
        echo "=== Notes ==="
        rg "$1" ~/obsidian_vault
    }
    ```
2.  **情報の「場所」を意識する:**
    自分が普段情報をどこに保存しているかリストアップし、「フロー情報（チャットなど）」と「ストック情報（Wikiなど）」に分類してみてください。
3.  **Handoffの実践:**
    ツールを作らなくても、一日の終わりに「明日やるべきこと、今日わかったこと」を3行で書く習慣をつけるだけで、記憶の定着率は劇的に変わります。

私の「記憶スタック」の旅はここで一区切りですが、システムは日々進化しています。
皆さんも、自分だけの「最強の記憶」を設計してみてください。

---

*シリーズ「記憶スタック」をお読みいただきありがとうございました。感想や、皆さんの構築したシステムがあれば、ぜひコメントで教えてください！*