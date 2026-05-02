
シリーズ「品質管理」第3回です。

前回の記事では、AIエージェントの思考プロセスを可視化する「トレーシング」について解説しました。今回は、システム全体が正常に稼働しているかを定常的に監視するための**「ヘルスチェック（定期健康診断）」**の実装について掘り下げます。

---

# 【品質管理 vol.3】AIエージェントの「定期健康診断」— 9つの指標でシステムの死活を監視する

「昨日はあんなに賢かったのに、今日はなんだか様子がおかしい……」

AIアプリケーションを運用していると、こんな経験はないでしょうか？
エラーログは出ていない。サーバーも落ちていない。けれど、回答の精度が落ちていたり、参照すべき最新のデータを無視していたりする。

従来のWebシステムであれば「死活監視（Ping）」で生存確認ができましたが、**AIシステムには「元気かどうか（健全性）」という曖昧な指標が存在します。**

ベクトルデータベースのインデックスは最新か？ 外部ツール（MCP）との接続は切れていないか？ APIの利用枠は残っているか？

これらを人間が毎日手動で確認するのは不可能です。
そこで今回は、私が開発しているAIシステム運用フレームワーク（コードネーム: Peira）で実際に稼働している**「9項目のヘルスチェックシステム」**と、それを自動化する仕組みについて紹介します。

## なぜ「ヘルスチェック」が必要なのか

AIシステムは、従来のソフトウェアよりも「依存関係」が複雑で動的です。

1.  **データの鮮度:** 知識ベースが古くなると、AIは自信満々に嘘をつきます。
2.  **外部連携の不安定さ:** 検索ツールやAPIツールが沈黙すると、AIはただの「おしゃべりな箱」になります。
3.  **コストとリソース:** トークン制限やAPIクォータは、突然システムを停止させます。

これらを未然に防ぐために、コマンド一発で全機能を診断する `health` コマンドを実装します。

## 監視すべき「9つのバイタルサイン」

私のプロジェクトでは、以下の9項目をシステムの「健康状態」として定義しています。プロジェクト固有のモジュール名が含まれていますが、皆さんのシステムに置き換えて読んでみてください。

| カテゴリ | 項目名 (モジュール) | チェック内容 | AIシステム特有の理由 |
| :--- | :--- | :--- | :--- |
| **知識** | **1. Gnōsis (論文DB)** | ベクトルDBの整合性とインデックス状態 | 検索漏れを防ぐため。追加されたPDFが正しくVector化されているか。 |
| | **2. Sophia (KI)** | Knowledge Instructions (システムプロンプト) の鮮度 | 指示書が最新のビジネスロジックを反映しているか確認するため。 |
| **文脈** | **3. Kairos (Handoff)** | 直近のセッションハンドオフ状況 | 長期記憶の引き継ぎが失敗していないか（AIの記憶喪失防止）。 |
| | **4. CCL Parser** | 独自言語パーサーの稼働状況 | AIの出力を構造化データに変換する機能が生きているか。 |
| **機能** | **5. MCP Server** | Model Context Protocol サーバー接続 | 外部ツール（Web検索、ファイル操作等）が利用可能か。 |
| | **6. Dendron** | エージェントの目的達成率 (PURPOSE) | 最近のタスク完了率が極端に低下していないか（ロジック崩壊の検知）。 |
| **インフラ** | **7. テスト通過率** | ユニット/統合テストのパス状況 | コード変更によるリグレッション検知。 |
| | **8. ディスク使用量** | ログ・キャッシュの容量 | ログ肥大化によるシステム停止防止。 |
| | **9. API クォータ** | OpenAI/Anthropic等の残高・レート制限 | 突然のサービス停止（Rate Limit）を回避するため。 |

これらを網羅することで、「動いているけど、頭が悪い」状態を「異常」として検知できるようになります。

## 実装：`peira health` コマンドを作る

これらのチェックをCLIから簡単に実行できるように実装します。Pythonであれば `click` や `typer`、表示には `rich` ライブラリを使うと視認性が高まります。

### 1. チェッカーの基底クラス
まず、全てのチェック処理の共通インターフェースを定義します。

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    OK = "✅"
    WARNING = "⚠️"
    CRITICAL = "❌"

@dataclass
class HealthResult:
    name: str
    status: HealthStatus
    message: str
    latency_ms: float

class BaseHealthChecker(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def check(self) -> HealthResult:
        """診断ロジックを実装"""
        pass
```

### 2. 具体的なチェッカーの実装例（APIクォータ）
例えば、APIの残量をチェックするクラスは以下のようになります。

```python
import time
import openai

class APIQuotaChecker(BaseHealthChecker):
    @property
    def name(self) -> str:
        return "OpenAI API Quota"

    async def check(self) -> HealthResult:
        start = time.time()
        try:
            # 実際にはBilling APIなどを叩くか、直近のエラー率を見る
            # ここでは簡易的な接続確認として記載
            models = await openai.Model.list()
            latency = (time.time() - start) * 1000
            return HealthResult(
                name=self.name,
                status=HealthStatus.OK,
                message="Connection established. Models available.",
                latency_ms=latency
            )
        except Exception as e:
            return HealthResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"API Error: {str(e)}",
                latency_ms=0
            )
```

### 3. コマンドラインでの実行結果
これらを束ねて実行するコマンド `peira health` を叩いた時の出力イメージです。`rich` ライブラリを使うと、以下のように美しく表示できます。

```text
$ peira health

🏥 Running System Health Check...

| Status | Component          | Latency | Message                                  |
| :---:  | :---               | :---:   | :---                                     |
|   ✅   | Gnōsis (DB)        | 45ms    | Index synced. 14,203 vectors active.     |
|   ✅   | Sophia (KI)        | 12ms    | Instructions loaded (v2.4.1).            |
|   ⚠️   | Kairos (Handoff)   | 120ms   | 2 sessions flagged for manual review.    |
|   ✅   | CCL Parser         | 5ms     | Parser operational.                      |
|   ❌   | MCP Server         | -       | Connection refused (port 8080).          |
|   ✅   | Dendron (PURPOSE)  | 200ms   | Recent success rate: 98%.                |
|   ✅   | Test Suite         | -       | 142/142 passed.                          |
|   ✅   | Disk Usage         | -       | 45% used (20GB free).                    |
|   ✅   | API Quota          | 320ms   | Usage within limits.                     |

🚨 Health Check Failed! Please check MCP Server.
```

一目で「MCPサーバーが落ちている」ことと「Kairos（記憶引継ぎ）に少し不安がある」ことがわかります。

## 運用の自動化：Daily CRONとSlack通知

手動でコマンドを叩くのは開発中だけです。運用フェーズでは **GitHub Actions** や **Cron** を使って毎朝自動実行し、Slackにレポートを飛ばします。

### GitHub Actions の設定例 (Daily Check)

```yaml
name: Daily Health Check

on:
  schedule:
    - cron: '0 0 * * *' # 毎日AM9:00 (JST)
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Health Check
        id: health
        run: |
          # 結果をJSONで出力し、失敗時はexit code 1を返す
          python -m peira health --format=json > result.json
        continue-on-error: true

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1.24.0
        with:
          # 結果JSONをパースしてSlackに整形投稿するスクリプトを呼び出す
          payload-file-path: "./payload-generated-from-result.json"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

朝起きてSlackを見たとき、全てグリーン（✅）なら安心してコーヒーが飲めます。レッド（❌）なら、ユーザーが気づく前に対応できます。

## さらに進んだ「自己修復（Self-Healing）」

ヘルスチェックの究極系は、**「異常を見つけたら勝手に直す」**ことです。

例えば、「1. Gnōsis (論文DB)」のチェックでインデックスの不整合が見つかった場合、アラートを出すだけでなく、バックグラウンドで `reindex` ジョブをトリガーするように実装します。

```python
async def run_checks():
    for checker in checkers:
        result = await checker.check()
        if result.status == HealthStatus.CRITICAL:
            # 自己修復を試みる
            if hasattr(checker, 'heal'):
                print(f"🚑 Attempting to heal {checker.name}...")
                await checker.heal()
                # 再チェック
                result = await checker.check()
        
        print_result(result)
```

これにより、一時的な不具合であればエンジニアが寝ている間にシステムが自力で回復してくれます。

---

## 読者が今すぐ試せること

いきなり9項目すべてを実装するのは大変です。まずは以下の3つから「ヘルスチェック・スクリプト」を作ってみてください。

1.  **API接続チェック:** OpenAI等のAPIキーが有効で、レスポンスが返ってくるか？
2.  **データベース接続チェック:** ベクトルDBやRDBに接続できるか？
3.  **基本機能チェック:** 「こんにちは」と入力して、AIが期待通りのフォーマットで返答するか？

これらを1つの `.py` ファイルにまとめ、毎朝実行するだけでも、運用の安心感は劇的に変わります。

次回は、これらの監視項目を逆手に取り、**「システムを意図的に壊すことで、堅牢な設計を導き出す」**というアプローチについて解説します。

👉 **次の記事:** 「壊す方法」から設計する — Via Negativa (04_via_negativa.md)