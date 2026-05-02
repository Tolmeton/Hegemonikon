# AGENTS（エージェント向け入口）

**共有プロジェクト正本:** [`.claude/CLAUDE.md`](.claude/CLAUDE.md)

- Claude Code / Copilot / その他 CLI は、上記をプロジェクト指示の主たるソースとして扱ってください。
- Codex は **`~/.codex/AGENTS.md` を役割・棲み分け・常時行動原則の主ソース** とし、[`.claude/CLAUDE.md`](.claude/CLAUDE.md) は **HGK 固有の文脈・用語・構造・共有制約の参照元** として読んでください。
- Codex は `.claude/CLAUDE.md` 内の Claude 向け役割分担をそのまま継承せず、Codex 固有の役割定義を優先してください。
- HGK の共有ルール体系は **`~/.claude/rules/horos-hub.md`** をハブとして参照してください。常時必要な核は Codex 側 `AGENTS.md` に統合し、詳細体系はこのユーザー全体ルール正本を参照します。
- BOOT / context recovery で project 側の `.agents/rules/horos-hub.md` を読みに行く環境では、**mirror が無ければ直ちに `~/.claude/rules/horos-hub.md` を参照** してください。project-local mirror が存在する場合も、それは forwarding 用であり、内容衝突時は常に `~/.claude/rules/horos-hub.md` を優先します。
- PJ 件数のような可変メタデータは prose の固定値ではなく **`10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/registry.yaml` の現物** を優先してください。数が食い違う場合、文書側を stale とみなします。
- BOOT の安全状態は **`30_記憶｜Mneme/05_状態｜State/A_違反｜Violations/`** を正本として扱ってください。`behavioral_constraints.md` や `violations.md` が単独ファイルで見えなくても、`sekisho_status.json` / `violations.jsonl` / `wbc_state.json` が存在すれば安全面は可観測です。
- BOOT の `quota` / `hexis` / `session_history` は **ephemeral runtime surface** です。`30_記憶｜Mneme/05_状態｜State/F_ランタイム｜Runtime/` に現物が無いこと自体は、即バグ断定せず「未観測」として扱ってください。
- **通常対話の親原理は共同思考性** です。詳細は [`.agents/rules/dialogue-externalization.md`](.agents/rules/dialogue-externalization.md) と [`.claude/rules/dialogue-definition-surface.md`](.claude/rules/dialogue-definition-surface.md) を参照してください。
- **定義面整合は共同思考性の前提** です。`Tolmetes の定義 / Codex の定義 / 今回採る前提` を合わせずに進める対話は虚構化するので、自己完結禁止より上位に置いてください。
- **定義面プロトコルの writable 正本** は [`.claude/rules/dialogue-definition-surface.md`](.claude/rules/dialogue-definition-surface.md) です。`.agents/rules/dialogue-externalization.md` が read-only な環境ではこちらを優先してください。
- **説明は原則として数式に頼らず**、ただし厳密さは落とさないでください。定義・前提・境界条件・関係を言葉で明示し、Tolmetes が直感的に追える形で説明してください。数式は Tolmetes が明示的に求めた場合のみ補助として用いてください。
- **`~/.codex/AGENTS.md` は生成物** です。Codex 側の恒久変更は直接そこを書かず、生成源の **`/home/makaron8426/.claude/hooks/sync-codex.py`** を修正してください。
- **実装報告の renderer 正本** は [`.agents/rules/implementation-report-renderer-policy.md`](.agents/rules/implementation-report-renderer-policy.md) です。`/ene` 系の final は executor log ではなく reader-facing artifact として出してください。
- **完了語を証明語として扱ってください。** 「完了」「できた」「直した」「統合した」「復旧した」「確認した」「消した」「安全」「問題なし」「main に収束した」などの到達表現は、単なる報告語ではなく **証明責任を伴う claim** です。論拠と証跡が無い到達表現は一切認めません。
- 到達表現を使う前に、最低限 **完了条件 / SOURCE / 実行証跡 / 反証探索 / 残欠陥または未証明範囲** を出してください。これらを出せない場合は、到達表現を禁止し、`未検証`、`暫定`、`未完了`、`判断待ち` として報告してください。
- 局所観測を全体命題へ昇格しないでください。1ファイルが直った、1コマンドが通った、root だけ確認した、push した、という事実は、全体の「完了」「統合」「復旧」の証明にはなりません。全体命題を出すには、対象の状態空間を明示し、その範囲で反例探索を行った証跡が必要です。
- 論拠なしの完了報告を後から補う運用は禁止です。証跡は報告前に必要です。報告後に欠落・旧版・未検証が見つかった場合、その時点で前の完了語を撤回し、失敗として扱ってください。
- Tolmetes と共に考えるため、内部状態を閉じた black-box として振る舞わないでください。率直さと非隠蔽は、その共同思考性から自然に要請されます。
- **確認が必要なら、ターンをまたぐ雑談的な往復ではなく、そのターン内で必要論点を束ねて質問してください。** request 単位課金と遅延を前提に、確認のためだけの小刻みな会話を最小化してください。
- **質問は原則として UI で選びやすい選択肢付きで出してください。** 自由記述を投げるのではなく、相互排他的な選択肢を 2-5 個に整理し、可能なら推奨案を明示してください。環境が選択肢 UI を出せるなら、それを優先して使ってください。
- **高リスクな不明点だけを質問し、低リスクな不明点は明示的な仮定を置いて先に進んでください。** ただし、その仮定で取り返しのつかない変更が起こる場合は、実行前に一括で確認してください。
- **連続質問を禁止します。** 追加確認が避けられない場合でも、まず未確定点を棚卸しし、次の 1 回の質問で意思決定に必要な分をまとめて聞いてください。
- Claude Code 固有のフックと設定は **`.claude/`** 以下にあります。
- **Codex の HGK 起動は ASCII alias `/home/makaron8426/Sync/oikos/hgk-codex` を正本** とします。開始前に `bash /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/hooks/ensure-codex-alias.sh` で alias を検証してください。
- **Codex 単発委譲の正規入口は `bash /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/hooks/delegate-codex.sh "<prompt>"`** です。raw `codex exec` を非 ASCII 実 repo path 配下で叩く運用は unsupported です。
- **Codex の MCP 正本は `~/.codex/config.toml`** です。Claude 側の project `.mcp.json` とは分離して維持します。
- **Codex 3軸 MCP の smoke は `bash hooks/codex-mcp-smoke.sh`** を使います。`aisthetikon=boot_context`、`dianoetikon=info(action=ping)`、`poietikon=poietikon` を検証し、`hub_*` の再露出を禁止します。
- **Codex の native custom skill 置き場は `~/.agents/skills`** です。Claude の shared store `~/.claude/skills` とは別なので、Codex で global skill を使うには bridge が必要です。
- **global skill bridge の同期は `bash hooks/sync-codex-skill-bridges.sh`** を使います。これは `~/.claude/skills/<name> -> ~/.agents/skills/<name>` の symlink を作ります。`--all` で一括同期、既存の実ディレクトリは上書きしません。
- **HGK の global assets 同期は `bash hooks/sync-hgk-global-assets.sh`** を使います。これは HGK 用 agent 定義を `~/.claude/agents/hgk-*.md` へ生成し、contract/rules を `~/.claude/rules/` に同期し、`~/.claude/CLAUDE.md` の canonical 参照を補正します。
- `resolve-hgk-skill.sh` の解決順は `project .agents/skills -> ~/.agents/skills -> project .claude/skills -> ~/.claude/skills` です。`/foo` や skill 名が来たら、まず `bash hooks/resolve-hgk-skill.sh foo` で正本 `SKILL.md` を引いてください。
