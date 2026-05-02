
シリーズ「記憶スタック」の第2回です。

前回の記事では、個人の全デジタルデータを資産化する「記憶スタック」の全体像についてお話ししました。今回は、その核心部分である**「検索エンジン」**を、あなたのPCの中に作り上げます。

---

# 【完全ローカル】GPUなし・APIなしで動く「日本語セマンティック検索」の作り方

「RAG（検索拡張生成）を作ってみたいけれど、OpenAIのAPI利用料が気になる…」
「個人の日記や社外秘のドキュメントを、外部のサーバーに送信するのは怖い…」

そんな悩みをお持ちではないでしょうか？

AI開発において「APIを叩く」ことは手軽ですが、個人開発やPoC（概念実証）の段階では、**コスト・プライバシー・レイテンシ（応答速度）**の3重苦に悩まされることがよくあります。

そこで今回は、**「完全ローカル・オフライン」**で動作する日本語セマンティック検索（意味検索）システムを構築します。

GPUは不要です。高価なサーバーも要りません。
あなたの手元にあるノートPC（CPUのみ）で、サクサク動く検索エンジンをPythonだけで実装します。

## なぜ「ローカル」にこだわるのか？

技術的な詳細に入る前に、API利用と比較したメリットを整理しておきましょう。

| 比較項目 | OpenAI API (Embeddings) | **今回のローカル構成** |
| :--- | :--- | :--- |
| **コスト** | 従量課金（円安で痛い） | **0円** |
| **プライバシー** | データ送信が必要 | **外部送信一切なし** |
| **速度** | ネットワーク状況に依存 | **CPUでも爆速（メモリ内完結）** |
| **制限** | レートリミットあり | **無制限** |

特に「プライバシー」は重要です。自分の思考のログである「記憶」を扱う以上、データは自分のPCから一歩も出したくないはずです。

## 技術スタック：軽量・高速な「四天王」

今回の実装では、以下の4つのライブラリを組み合わせます。これらは「軽量かつ強力」な選りすぐりのスタックです。

1.  **BGE-small (ONNX)**: ベクトル化モデル
    *   日本語性能が高い比較的小さなモデル（384次元）。これをONNX形式に変換して高速化します。
2.  **ONNX Runtime**: 推論エンジン
    *   PyTorchなどの重いフレームワークを使わず、CPUに最適化された推論を行います。
3.  **Janome**: 日本語形態素解析
    *   テキストの前処理（チャンキング）に使います。`pip install` だけで入り、MeCabのような複雑な環境構築が不要です。
4.  **HNSWlib**: 近似最近傍探索
    *   数万〜数十万件のデータから、類似するものをミリ秒単位で探し出すライブラリです。

## 実装ステップ

それでは、実際にコードを書いていきましょう。
※ 実際の動作にはモデルファイル（ONNX）のダウンロードが必要ですが、ここではロジックの流れを中心に解説します。

### 1. 環境構築

必要なのはPython環境のみです。以下のコマンドでライブラリをインストールします。

```bash
pip install onnxruntime janome hnswlib numpy tokenizers
```
※ モデルへの入力用に`tokenizers`も併用します。

### 2. テキストの前処理（Janomeの活用）

長い文章をそのままベクトル化すると、意味がぼやけてしまいます。そこで、Janomeを使って文章を「意味のある単位（文など）」に分割します。

MeCabは導入がハードルになりがちですが、Janomeは純粋なPython製なので、OSを問わず一瞬で導入できるのが魅力です。

```python
from janome.tokenizer import Tokenizer

def split_text(text):
    t = Tokenizer()
    sentences = []
    current_sentence = ""
    
    # 単純な「。」区切りではなく、形態素解析を使って
    # 文の区切りをより正確に判定することも可能ですが、
    # ここではシンプルに「。」で区切りつつ、Janomeで名詞抽出などを
    # 行い、検索の補助情報（メタデータ）を作る例を想定します。
    
    for token in t.tokenize(text):
        # ここで「名詞」だけ抽出してキーワード検索用のインデックスを作るなど
        # ハイブリッド検索への拡張も容易です
        pass 
        
    # 簡易的な実装として、改行や句点で分割
    return [s.strip() for s in text.replace('。', '。\n').split('\n') if s.strip()]

text = "昨日は雨でした。でも、今日は晴れです！"
chunks = split_text(text)
print(chunks)
#出力: ['昨日は雨でした。', 'でも、今日は晴れです！']
```

### 3. ベクトル化（ONNX Runtime）

ここが心臓部です。PyTorchを使わず、ONNX Runtimeを使うことで、CPUでも実用的な速度（100件/秒以上）が出せます。モデルには日本語性能に定評のある `BAAI/bge-small-zh-v1.5` などをONNX化したものを使用します。

```python
import onnxruntime as ort
from tokenizers import Tokenizer
import numpy as np

class Vectorizer:
    def __init__(self, model_path, vocab_path):
        # CPUで実行する設定
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.tokenizer = Tokenizer.from_file(vocab_path)

    def encode(self, texts):
        # トークナイズ
        encoded = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.array([e.type_ids for e in encoded], dtype=np.int64)

        # ONNXランタイムで推論
        inputs = {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'token_type_ids': token_type_ids
        }
        outputs = self.session.run(None, inputs)
        
        # 最後の隠れ層の先頭トークン(CLS)のベクトルを取得
        embeddings = outputs[0][:, 0, :]
        
        # 正規化（コサイン類似度計算のため）
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

# ※実際にはHuggingFaceからモデルとtokenizer.jsonをDLしてパス指定します
# vectorizer = Vectorizer("model.onnx", "tokenizer.json")
```

### 4. 高速検索インデックス（HNSWlib）

ベクトル化したデータをHNSWlibに突っ込みます。これはSpotifyなども採用しているアルゴリズムで、精度と速度のバランスが絶妙です。

```python
import hnswlib

class SearchIndex:
    def __init__(self, dim=384):
        # コサイン類似度空間を定義
        self.p = hnswlib.Index(space='cosine', dim=dim)
        self.p.init_index(max_elements=10000, ef_construction=200, M=16)
        self.data_map = {} # IDとテキストの紐付け用

    def add_items(self, vectors, texts):
        num_items = len(texts)
        ids = np.arange(len(self.data_map), len(self.data_map) + num_items)
        
        self.p.add_items(vectors, ids)
        
        for i, text in zip(ids, texts):
            self.data_map[i] = text

    def search(self, query_vector, k=3):
        # 近似最近傍探索
        labels, distances = self.p.knn_query(query_vector, k=k)
        results = []
        for label, dist in zip(labels[0], distances[0]):
            results.append({
                "text": self.data_map[label],
                "score": 1 - dist # 距離を類似度に変換
            })
        return results
```

## 実際に動かしてみる

これらを組み合わせると、以下のようなフローになります。

1.  **ドキュメント**：「会議の議事録」「技術メモ」「日記」
2.  **Janome**：文単位に分割
3.  **ONNX**：ベクトル化（数値の配列に変換）
4.  **HNSWlib**：インデックスに保存

そして、検索時：

```python
query = "Pythonでベクトル検索を高速化する方法は？"
query_vec = vectorizer.encode([query])
results = index.search(query_vec)

for res in results:
    print(f"Score: {res['score']:.4f} | Text: {res['text']}")
```

**結果例:**
> Score: 0.8921 | Text: ONNX Runtimeを使用すると、CPU環境でも推論速度が大幅に向上します。
> Score: 0.8105 | Text: HNSWlibは近似最近傍探索を行うためのライブラリです。

キーワードが一致していなくても、「高速化」と「推論速度向上」のような**意味の繋がり**を捉えて検索できています。これがローカル環境で、ネットなしで動くのです。

## 読者が次に試せること

この記事を読み終えたら、ぜひ以下の「小さな実験」を試してみてください。

1.  **自分のテキストデータを用意する**: 最近書いたメモや日記を10件ほどテキストファイルにする。
2.  **ライブラリを入れる**: `pip install onnxruntime janome hnswlib`
3.  **HuggingFaceからモデルをDL**: `Quantized BGE-small` などのONNXモデルを探してダウンロードしてみる。
4.  **検索してみる**: 自分の言葉で検索し、過去の自分が書いたメモが「意味」でヒットする感動を味わってください。

ローカル環境であれば、10万件のデータがあっても検索にかかる時間は**10ms（0.01秒）以下**です。自分だけの「第二の脳」が、指先で瞬時に反応する感覚は病みつきになります。

---

さて、検索エンジンは完成しました。しかし、検索できるだけではまだ「記憶の活用」としては片手落ちです。
日々増え続ける膨大な情報（論文、記事、ログ）を、どうやってこの検索エンジンに効率よく放り込めばいいのでしょうか？

次回は、**「596本の論文を自動消化するパイプライン」**について解説します。今回作った検索エンジンに、自動で知識を供給し続ける仕組みを作りましょう。

**次の記事へ**: [596論文を自動消化するパイプライン (03_digestor.md)](./03_digestor.md)