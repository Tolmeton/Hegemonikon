# Codex App 設定大全

Windows 前提 / HGK 実務者向け

最終確認: 2026-04-10

この文書は、OpenAI 公式ドキュメントに分散している Codex App の設定情報を、Windows で実務運用する順番に並べ直したものです。

- 対象: Codex App を日常的に使う Windows 利用者
- 主眼: `Settings` 画面、`config.toml`、承認/サンドボックス、Windows、local environments、managed configuration を 1 本で把握すること
- 非対象: Tolmetes の現行 `~/.codex/config.toml` 監査、運用中プロファイルの個別診断

表記:

- `SOURCE`: OpenAI 公式 docs に明示されている内容
- `INFERENCE`: この文書で使った公式ページ群には明示キーがなく、現時点では「UI 側設定として扱うのが妥当」と判断した内容

参照元:

- [Settings](https://developers.openai.com/codex/app/settings)
- [Config basics](https://developers.openai.com/codex/config-basic)
- [Advanced configuration](https://developers.openai.com/codex/config-advanced)
- [Configuration reference](https://developers.openai.com/codex/config-reference)
- [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)
- [Windows](https://developers.openai.com/codex/windows)
- [Local environments](https://developers.openai.com/codex/app/local-environments)
- [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration)

既存の HGK Windows 全体セットアップは [hgk-zero-setup-windows.md](./hgk-zero-setup-windows.md) を参照してください。この文書は、その後の「Codex 自体の設定面」にだけ絞っています。

## 0. 先に結論

まず押さえるべきことは 4 つです。

1. 日常運用の中心は `Settings` 画面と `~/.codex/config.toml` です。
2. リポジトリ共有は `<repo>/.codex/config.toml` と project root の `.codex/` 配下で行います。
3. project を `trusted` にしない限り、Codex は project 側 `.codex/` レイヤを読みません。
4. 管理対象環境では、通常の `config.toml` 優先順位に加えて、`requirements.toml` と `managed_config.toml` が上から被さります。

公式の安全寄りな出発点は、概ね次です。

- バージョン管理された作業フォルダでは `Auto = workspace-write + on-request`
- ネットワークは既定でオフ
- Web 検索は既定で `cached`
- Windows ネイティブ運用では `elevated` が推奨

HGK 上の常用推奨は、上の公式出発点をほぼ維持しつつ、`personality = "pragmatic"`、`windows.sandbox_private_desktop = true`、`network_access = false` を明示して運用することです。

## 1. 設定面の全体地図

### 1.1 どこに何があるか

| 面 | 代表場所 | 役割 | 共有単位 |
| --- | --- | --- | --- |
| App Settings | Codex App の `Settings` 画面 | 日常 UI から触る設定入口 | ユーザー単位 |
| User config | `~/.codex/config.toml` | 個人既定値 | ユーザー単位 |
| Project config | `<repo>/.codex/config.toml` | リポジトリ固有の上書き | リポジトリ単位 |
| Local environments | `<repo>/.codex/` 配下の生成ファイル | worktree 用 setup / actions | リポジトリ単位 |
| Managed defaults | Windows では `~/.codex/managed_config.toml` | 起動時の管理既定値 | 管理対象端末単位 |
| Requirements | `requirements.toml` 系 | 破れない制約 | 組織単位 |

### 1.2 非管理端末での基本優先順位

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic)

非管理端末では、Codex は次の順で値を解決します。

1. CLI flags と `--config`
2. `--profile <name>` で選んだ profile
3. trusted project の `.codex/config.toml`
4. `~/.codex/config.toml`
5. `/etc/codex/config.toml` on Unix
6. built-in defaults

補足:

- project config は project root から現在ディレクトリまで順に読み、同じキーなら「より近い `.codex/config.toml`」が勝ちます。
- project を `untrusted` にすると、project 側 `.codex/` レイヤは丸ごと無視されます。

### 1.3 管理対象端末では読み方が変わる

`SOURCE`: [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration)

管理対象端末では、優先順位を 2 層に分けて読む方が安全です。

1. ベース設定層
2. 制約層

ベース設定層:

- 通常の `config.toml`
- その上に `managed_config.toml`
- macOS MDM の managed preferences はさらに上

制約層:

- `requirements.toml`
- cloud-managed requirements

重要なのは次です。

- `managed_config.toml` は起動時の開始値を上から被せる
- `requirements.toml` は「許される値の範囲」を縛る
- つまり「見た目上 set できても、requirements に反すれば Codex 側で互換値へ戻される」

## 2. `Settings` 画面をどう読むか

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings)

App Settings は、すべてが `config.toml` に 1 対 1 で対応しているとは限りません。まず「UI 入口」なのか「共有 config の表現」なのかを分けて読む必要があります。

| Section | 何を触るか | `config.toml` との関係 |
| --- | --- | --- |
| `General` | ファイルの開き方、thread に出すコマンド出力量、複数行送信、スリープ抑止 | `file_opener` は `SOURCE`。その他はこの原典セットでは対応キー未確認 |
| `Notifications` | turn 完了通知、通知権限プロンプト | App 通知 UI。`notify` とは別物 |
| `Agent configuration` | モデル、承認、サンドボックスなどの共通設定入口 | `SOURCE`: App / IDE / CLI で同じ設定レイヤを共有 |
| `Appearance` | テーマ、色、UI/code font | `INFERENCE`: 現 source set の config reference に対応キーなし |
| `Git` | branch naming、force push、commit/PR prompt | `INFERENCE`: 現 source set の config reference に対応キーなし |
| `Integrations & MCP` | MCP 連携の有効化、OAuth | `SOURCE`: `config.toml` と共有 |
| `Personalization` | personality、custom instructions | `SOURCE`: `personality` と personal `AGENTS.md` に接続 |
| `Archived threads` | archived chat の一覧と復元 | UI 状態。設定キーではない |

### 2.1 誤読しやすい 3 点

#### `Notifications` と `notify` は同じではない

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings), [Configuration reference](https://developers.openai.com/codex/config-reference)

- `Settings > Notifications` はアプリの完了通知 UI
- `notify` は「Codex が JSON payload を渡して呼ぶ外部コマンド」

つまり `notify` は「デスクトップ通知の ON/OFF」ではなく、より低レベルの通知フックです。

#### `Personalization` の custom instructions は `AGENTS.md` に繋がる

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings)

公式 docs では、custom instructions を編集すると personal instructions in `AGENTS.md` が更新されると明記されています。

#### `Integrations & MCP` は app 専用設定ではない

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings)

MCP 設定は `config.toml` に住むため、Codex App・CLI・IDE extension で共有されます。

## 3. 中核 `config.toml` キー

この節では、日常的に誤設定の影響が大きいキーだけを先にまとめます。

### 3.1 まず覚えるキー一覧

| キー | 値 | 意味 | 実務メモ |
| --- | --- | --- | --- |
| `model` | 例: `"gpt-5.4"` | 既定モデル | モデル固定の基点 |
| `model_reasoning_effort` | `minimal | low | medium | high | xhigh` | 推論強度 | `xhigh` は model dependent |
| `approval_policy` | `untrusted | on-request | never | granular` | いつ止まって承認を求めるか | `on-failure` は deprecated |
| `sandbox_mode` | `read-only | workspace-write | danger-full-access` | 実行時の境界 | フルアクセスは別格で危険 |
| `[sandbox_workspace_write] network_access` | `true | false` | workspace-write 内での外向き通信 | 既定はオフで考える |
| `web_search` | `disabled | cached | live` | Web 検索モード | 通常は `cached` |
| `personality` | `none | friendly | pragmatic` | 既定話法 | App UI の Personalization と接続 |
| `file_opener` | `vscode | vscode-insiders | windsurf | cursor | none` | 参照リンクをどこで開くか | `General` と接続 |
| `notify` | `array<string>` | 通知コマンド | App の通知トグルとは別 |
| `[projects."<path>"] trust_level` | `"trusted" | "untrusted"` | project `.codex/` を読むかどうか | 共有設定に直結 |
| `[windows] sandbox` | `"elevated" | "unelevated"` | Windows ネイティブ sandbox 方式 | 基本は `elevated` |
| `[windows] sandbox_private_desktop` | `true | false` | private desktop 利用 | `false` は互換性用のみ |

### 3.2 代表的な書き方

#### モデル

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
model = "gpt-5.4"
```

#### 推論強度

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
model_reasoning_effort = "high"
```

#### 承認ポリシー

`SOURCE`: [Configuration reference](https://developers.openai.com/codex/config-reference), [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)

```toml
approval_policy = "on-request"
```

granular approval も使えます。

```toml
approval_policy = { granular = { sandbox_approval = true, rules = true, mcp_elicitations = true, request_permissions = false, skill_approval = false } }
```

#### サンドボックス

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false
```

#### Web 検索

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
web_search = "cached"
```

#### Personality

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings), [Config basics](https://developers.openai.com/codex/config-basic), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
personality = "pragmatic"
```

#### File opener

`SOURCE`: [Settings](https://developers.openai.com/codex/app/settings), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
file_opener = "cursor"
```

#### 通知フック

`SOURCE`: [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
notify = ["pwsh", "-NoLogo", "-Command", "Write-Host notification"]
```

#### Windows sandbox

`SOURCE`: [Config basics](https://developers.openai.com/codex/config-basic), [Windows](https://developers.openai.com/codex/windows), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
[windows]
sandbox = "elevated"
sandbox_private_desktop = true
```

#### Project trust

`SOURCE`: [Advanced configuration](https://developers.openai.com/codex/config-advanced), [Configuration reference](https://developers.openai.com/codex/config-reference)

```toml
[projects.'C:\path\to\repo']
trust_level = "trusted"
```

### 3.3 HGK 常用の最小ベース

これは `SOURCE` の既定値そのものではなく、上の公式情報から組んだ HGK 常用ベースです。

```toml
model = "gpt-5.4"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"
personality = "pragmatic"

[sandbox_workspace_write]
network_access = false

[windows]
sandbox = "elevated"
sandbox_private_desktop = true
```

意図:

- 普段の編集は許す
- 境界越えとネットワークは承認で止める
- Web は live ではなく cached を起点にする
- Windows は stronger sandbox を優先する

## 4. Windows 実務

`SOURCE`: [Windows](https://developers.openai.com/codex/windows), [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)

### 4.1 まず OS 前提

公式の整理は次です。

- Windows 11: `Recommended`
- fully updated な recent Windows 10: `Best effort`
- 古い Windows 10: `Not recommended`

したがって、Windows 11 を基準に考えるのが安全です。

### 4.2 `elevated` と `unelevated`

| モード | 位置づけ | 使うべき場面 |
| --- | --- | --- |
| `elevated` | preferred native Windows sandbox | 標準運用 |
| `unelevated` | fallback native sandbox | 管理者承認や必要 setup が通らない時の暫定運用 |

公式 docs の読み方としては単純です。

- 使えるなら `elevated`
- だめなら `unelevated`
- それでも合わない、または Linux-native toolchain が必要なら WSL

### 4.3 private desktop

公式では、両 sandbox mode とも既定で private desktop を使います。

```toml
[windows]
sandbox_private_desktop = true
```

`false` にしてよいのは、古い `Winsta0\Default` 互換が必要な場合だけです。

### 4.4 `approval_policy = "never"` と `danger-full-access` は別物

ここは誤読しやすいので決定表で分けます。

| 設定 | 何が起こるか | 危険度 |
| --- | --- | --- |
| `sandbox_mode = "workspace-write"` + `approval_policy = "never"` | 承認なしで動くが、まだ sandbox 内 | 中 |
| `sandbox_mode = "read-only"` + `approval_policy = "never"` | 読み取り専用で無人実行 | 低 |
| `sandbox_mode = "danger-full-access"` + `approval_policy = "never"` | sandbox なし、承認なし | 極高 |
| `--yolo` | 実質 `danger-full-access` + no approvals | 極高 |

要点:

- `never` は「黙って実行する」だけ
- `danger-full-access` は「境界そのものを外す」
- 両者は同義ではありません

### 4.5 Windows で困った時の最短手

`SOURCE`: [Windows](https://developers.openai.com/codex/windows)

- sandbox が読めないディレクトリに当たったら `/sandbox-add-read-dir C:\absolute\directory\path`
- native sandbox の setup が企業ポリシーで詰まるなら、まず `unelevated` で継続
- workflow が最初から Linux 寄りなら WSL に寄せる

### 4.6 WSL を選ぶ判断

WSL を選ぶのは、次のような時です。

- repo と toolchain が Linux 前提
- native Windows sandbox の 2 モードがどちらも運用に合わない
- すでに日常開発が WSL 上にある

公式 docs でも、WSL を使うなら repo は `/home/...` 側に置くことが勧められています。

## 5. project 共有: `.codex` と local environments

`SOURCE`: [Advanced configuration](https://developers.openai.com/codex/config-advanced), [Local environments](https://developers.openai.com/codex/app/local-environments)

### 5.1 shared config の基本

project 共有は主に 2 つです。

1. `<repo>/.codex/config.toml`
2. `<repo>/.codex/` 配下の local environment 設定

project config について公式 docs が明示している点:

- project root から current working directory までの `.codex/config.toml` を順に読む
- 同じキーは「より近い `.codex/config.toml`」が勝つ
- project が `trusted` でないと無視される
- relative path は、その `config.toml` を含む `.codex/` フォルダ基準で解決される

### 5.2 local environments

local environments は、worktree と common actions の共有設定です。

- 設定場所は project root の `.codex/`
- Codex App Settings から編集する
- Git に commit して他メンバーへ共有できる

### 5.3 Setup scripts

setup scripts は、新しい thread の開始時に Codex が worktree を作ったとき、自動実行されます。

主な用途:

- dependency install
- 初回 build
- platform ごとの環境初期化

公式 example:

```text
npm install
npm run build
```

platform ごとの差分がある場合は、macOS / Windows / Linux で分けて定義します。

### 5.4 Actions

actions は app 上部の quick action として出る「よく使うコマンド」です。

主な用途:

- dev server 起動
- test suite 実行
- build

actions は app の integrated terminal 内で走ります。setup scripts と違って、こちらは「毎回自動」ではなく「すぐ叩ける共通コマンド」の位置づけです。

### 5.5 実務上の分担

混ぜない方がよい責務は次です。

- 個人既定値: `~/.codex/config.toml`
- repo 共通既定値: `<repo>/.codex/config.toml`
- worktree 初期化と common task: local environments

## 6. 管理者向け付録

`SOURCE`: [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration)

### 6.1 `requirements.toml` と `managed_config.toml` の違い

| ファイル | 役割 | 破れるか |
| --- | --- | --- |
| `requirements.toml` | 許可境界を縛る | 破れない |
| `managed_config.toml` | 起動時既定値を被せる | セッション中は変えられるが次回起動で戻る |

### 6.2 requirements が縛るもの

公式 docs で明示されている代表例:

- `approval_policy`
- `sandbox_mode`
- `web_search`
- `mcp_servers` allowlist
- `[features]` pinning

例:

```toml
allowed_approval_policies = ["untrusted", "on-request"]
allowed_sandbox_modes = ["read-only", "workspace-write"]
allowed_web_search_modes = ["cached"]
```

この場合:

- `never` は禁止
- `danger-full-access` は禁止
- live web search は禁止

### 6.3 managed defaults の優先順位

公式 docs の要点は次です。

- `managed_config.toml` は user `config.toml` より上
- CLI `--config` overrides よりも managed defaults が勝つ
- Windows / non-Unix では場所が `~/.codex/managed_config.toml`

例:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false
```

### 6.4 管理側の設計原則

公式 docs に沿うなら、まず次で十分です。

- 大半の利用者は `workspace-write + approvals`
- `network_access = false` を起点にする
- full access は container など統制された場だけに寄せる

## 7. 設定プリセット早見表

### 7.1 安全閲覧

用途:

- 読み取り中心
- repo 調査
- 実行を極力させたくない

```toml
approval_policy = "on-request"
sandbox_mode = "read-only"
web_search = "cached"
```

### 7.2 通常開発

用途:

- 日常の修正
- テスト実行
- 必要なら承認を取りつつ前進

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"
personality = "pragmatic"

[sandbox_workspace_write]
network_access = false

[windows]
sandbox = "elevated"
sandbox_private_desktop = true
```

### 7.3 無人バッチ

用途:

- CI 的な静かな実行
- 手元で確認済みの狭いワークフロー

```toml
approval_policy = "never"
sandbox_mode = "workspace-write"
web_search = "disabled"

[sandbox_workspace_write]
network_access = false

[windows]
sandbox = "elevated"
```

注意:

- `never` でも sandbox は残る
- だからこれは full access ではない

### 7.4 フルアクセス緊急時

用途:

- どうしても sandbox 外まで触る必要がある
- 危険性を理解した上で一時的に使う

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = "live"
```

注意:

- 常用しない
- `web_search = "live"` は full access 系で live が既定になりやすい文脈に合わせた例。不要なら `disabled` でもよい
- 組織管理下では requirements によって禁止されることがある

### 7.5 共有 worktree セットアップ

用途:

- repo を開いた誰でも同じ setup と common action を使いたい

方針:

- `<repo>/.codex/config.toml` に repo 既定値を書く
- local environments の setup scripts / actions を project root `.codex/` で共有する
- project を `trusted` にする

## 8. ソース対応表

| この文書の節 | 主ソース |
| --- | --- |
| 設定面の全体地図 | [Config basics](https://developers.openai.com/codex/config-basic), [Advanced configuration](https://developers.openai.com/codex/config-advanced) |
| App Settings の読み方 | [Settings](https://developers.openai.com/codex/app/settings) |
| 中核 `config.toml` キー | [Configuration reference](https://developers.openai.com/codex/config-reference), [Config basics](https://developers.openai.com/codex/config-basic) |
| 承認とサンドボックス | [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security) |
| Windows 実務 | [Windows](https://developers.openai.com/codex/windows) |
| local environments | [Local environments](https://developers.openai.com/codex/app/local-environments) |
| 管理者向け付録 | [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration) |

## 9. 最後の判断軸

設定で迷ったら、次の順に決めると破綻しにくいです。

1. sandbox をどこまで残すか
2. approval をどこで止めるか
3. network と web_search をどこまで開くか
4. その設定を個人に置くか、repo に共有するか、管理層で縛るか

この順を逆にすると、`never` や `live` だけ先に開いてしまい、意図せず `danger-full-access` 的な運用へ滑りやすくなります。
