```typos
#prompt skill-architecture
#syntax: v8
#depth: L2

<:role: Cursor Skill の構成要素アーキテクチャ定義。
  各要素を消費者×読込×スコープの3軸で定位し、判定フローを提供する。:>

<:goal: Skill に新コンポーネントを追加する際の配置判定基準を常時保持する :>

<:constraints:
  - 6要素は MECE: 3軸の組合せで一意に定位される。2要素が3軸すべて一致することはない
  - scripts/ の4条件: (1) Agent推論で代替不可 (2) スキル固有 (3) オンデマンド (4) 軽量
  - 共有されたら MCP に昇格。イベント駆動なら hooks/ に再分類
  - 正本: ~/.cursor/skills/ (ユーザーレベル)
/constraints:>

<:context:
  - [knowledge] 6構成要素:
    | 要素 | 消費者 | 読込 | スコープ |
    | SKILL.md | Agent推論 | 常時 | 固有 |
    | references/ | Agent推論 | 遅延 | 固有 |
    | assets/ | Agent出力 | 遅延 | 固有 |
    | scripts/ | Agent実行 | 遅延 | 固有 |
    | hooks/ | 環境 | イベント | 固有or共有 |
    | MCP | Agent実行 | 常駐 | 共有 |

  - [knowledge] 要素間の射:
    SKILL.md → references/ (参照, lazy read)
    SKILL.md → assets/ (テンプレート使用)
    SKILL.md → scripts/ (実行指示)
    scripts/ → MCP (共有されたら昇格)
    scripts/ → hooks/ (イベント駆動なら再分類)
    references/ → SKILL.md (小さければ吸収)

  - [knowledge] 判定フロー:
    Agent推論に使う→常時必要→SKILL.md / 必要時だけ→references/
    Agent出力を形作る→assets/
    コード実行→Agentトリガー→固有→scripts/ / 共有→MCP
    環境トリガー→hooks/

  - [knowledge] 境界判定:
    SKILL.md vs references/: 毎回読むべきか→Yes=SKILL.md, No=references/
    references/ vs assets/: 推論を助けるか (ref) vs 出力を形作るか (assets)
    scripts/ vs MCP: 固有か (scripts) vs 共有か (MCP)
    scripts/ vs hooks/: Agentが決めるか (scripts) vs 環境が決めるか (hooks)

  - [file] ~/.cursor/skills/README.md (ポインタ)
/context:>
```
