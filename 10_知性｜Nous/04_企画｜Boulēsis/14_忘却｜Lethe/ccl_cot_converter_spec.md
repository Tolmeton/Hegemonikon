# CCL-CoT Converter Spec

> 対応 meta.md: `paper_ccl_cot_sft_draft.meta.md` (Tier 1)
> 対応本体: `paper_ccl_cot_sft_draft.md` (Tier 3, 別セッション)
> 起票日: 2026-04-29
> 状態: Tier 2 — 設計目標 + 入出力契約のみ。実装詳細は別セッション
> 役割: 自然言語 chain-of-thought (NL-CoT) を CCL chain-of-thought (CCL-CoT) に変換する converter の **入出力契約** を固定する
> 位置づけ: HGK 内に存在する隣接資産 (Hermeneus = CCL parser, `code_ingest.py` = Code → CCL transpiler) との直交軸。NL → CCL は新規実装

---

## §1 核

この spec は converter 実装そのものではない。
やることは 1 つだけで、**「どの入力を、どの形式で、どの保証付きで、CCL-CoT に変換するか」を契約として固定する**ことである。

実装方式 (LLM-based / AST-based / hybrid) の選択は本 spec の射程外。Tier 3 (paper 本体) または別 spec で確定する。本 spec は実装方式を切り替えても契約が破綻しないように書く。

---

## §2 設計目標

### §2.1 機能目標 (Functional Goals)

| 番号 | 目標 | 測定方法 |
|:---|:---|:---|
| F1 | NL-CoT を Hermeneus が parse 可能な CCL-CoT 文字列に変換する | Hermeneus parse 通過率 ≥ 99% (実証目標、Tier 3 で検証) |
| F2 | 元解 (NL-CoT) と CCL-CoT の間の論理同型性を保つ | 構造保存率 (後述 §6) ≥ 0.9 |
| F3 | 同一入力に対して決定論的出力 (seed 固定下) | 100% 再現 (LLM-based の場合は temperature=0 + seed 固定) |
| F4 | 自然言語 token 数 vs CCL token 数の比率を変換ログに記録する | 各変換ごとに `token_ratio` フィールドを emit |
| F5 | 失敗ケース (parse 不可・構造同型性違反) を blocking 例外として返す | silent fallback 禁止 |

### §2.2 非機能目標 (Non-Functional Goals)

| 番号 | 目標 | 備考 |
|:---|:---|:---|
| N1 | 単一プロセス内で stateless | converter 自体は session 状態を持たない |
| N2 | LLM-based 実装の場合: token 数 ≤ NL-CoT 入力 × 4 | 暴走防止 |
| N3 | AST-based 実装の場合: 中間 graph はメモリ内のみ (永続化禁止) | 副作用最小化 |
| N4 | 設定は YAML 1 枚 (`config.yaml`) | 環境変数経由は禁止 |
| N5 | ログは JSONL (1 行 = 1 変換) | downstream 集計用 |

### §2.3 非目標 (Non-Goals)

| 番号 | やらないこと | 理由 |
|:---|:---|:---|
| ¬G1 | NL-CoT の論理誤りの修正 | 変換器は意味保存器であり修正器ではない。誤った CoT は誤ったまま CCL に写す |
| ¬G2 | CCL-CoT → NL-CoT の逆変換 | C1-C3 主張に不要 |
| ¬G3 | CCL の意味的蒸留 (e.g. tautology の除去) | 蒸留は別 skill (/lys や /sag) の領分 |
| ¬G4 | 多言語 NL-CoT (英語以外) のサポート | 初版は英語と日本語のみ。MATH-500 が英語前提 |
| ¬G5 | 実時間 streaming 変換 | batch 前提。streaming は別 spec |

---

## §3 入力契約

### §3.1 入力データ型

```yaml
ConversionRequest:
  request_id: str              # UUID v4 推奨
  source: NL_CoT               # 必須
  metadata:
    problem_id: str            # MATH-500 の問題 ID 等 (downstream 集計のため)
    language: enum [en, ja]    # ¬G4 により en | ja のみ
    expected_answer: str|null  # converter は使わないが log に記録 (audit trail)
    seed: int|null             # LLM-based 実装で再現性確保するときに使う
  config_ref: str              # config.yaml の version hash (再現性のため)

NL_CoT:
  text: str                    # 自然言語 chain-of-thought 全文
  step_separators: list[str]|null  # 例: ["Step 1:", "Step 2:"] (階段が明示されている場合)
  token_count: int             # NL token 数 (BPE base, 計測 tokenizer は config.yaml で固定)
```

### §3.2 入力前提

- `source.text` は UTF-8 で empty でない (空文字は §5 で例外)
- `source.text` の token 数 ≤ 4096 (Gemma 4 E4B context 制限の半分以下、出力余裕を確保)
- `metadata.language` が `en` の場合: tokenizer は `gemma-tokenizer-v4` (config.yaml で固定)
- `metadata.language` が `ja` の場合: tokenizer は同じ。日本語の場合は文字数 ≈ token 数 × 1.5 を目安とするが、契約は token 数で測る

### §3.3 入力 SOURCE/TAINT 区別

- `source.text` 自体は外部入力 (Tolmetes か MATH-500 dataset) → INPUT TAINT
- `metadata` は呼び出し側責任 → INPUT TAINT
- converter 内部で `metadata` を信用しない (例: `expected_answer` を変換に使ってはならない)

---

## §4 出力契約

### §4.1 出力データ型

```yaml
ConversionResponse:
  request_id: str              # 入力と一致
  status: enum [ok, error]
  result:
    ccl_cot: CCL_CoT|null      # status=ok の時のみ非 null
  error:
    code: str|null              # エラーコード (§5 参照)
    message: str|null
  diagnostics:
    token_ratio: float          # ccl_cot.token_count / source.token_count
    structural_isomorphism: float   # 構造保存率 (§6 参照, 0.0-1.0)
    parse_validity: bool        # Hermeneus parse 通過したか
    fidelity_signals: dict      # §6 の 4 signal を全て格納
  audit:
    converter_version: str      # 実装バージョン (semver)
    config_hash: str            # config.yaml の SHA-256
    timestamp_utc: str          # ISO 8601
    elapsed_ms: int

CCL_CoT:
  ccl_text: str                 # CCL 式 (Hermeneus parse 可能)
  step_count: int               # CCL ステップ数 (`/verb` 出現数 or 同等)
  token_count: int              # CCL token 数 (CCL token 化規則は config.yaml)
  ast: dict|null                # AST-based 実装の中間 graph (任意, デバッグ時のみ)
```

### §4.2 出力保証

**status=ok の時に限り、以下すべてが成立する。**

1. `result.ccl_cot.ccl_text` は Hermeneus が `start_hermeneus_stdio.sh` 経由で parse 通過する (F1)
2. `diagnostics.parse_validity == true`
3. `diagnostics.structural_isomorphism >= 0.9` (F2 — 閾値は config.yaml で調整可)
4. `diagnostics.token_ratio` は記録されている (F4)
5. `audit.config_hash` が呼び出し時の config.yaml と一致する (F3)

**いずれかが破れる場合、status=error を返さなければならない (silent fallback 禁止 — F5)。**

### §4.3 出力 SOURCE/TAINT 区別

- `result.ccl_cot.ccl_text` は converter 内部生成 → OUTPUT TAINT (LLM 由来 / AST 変換由来 のいずれでも TAINT)
- `diagnostics.parse_validity` は Hermeneus 実行結果 → SOURCE
- `diagnostics.structural_isomorphism` は converter 自己採点 → OUTPUT TAINT (downstream で独立検証要)

---

## §5 エラー契約

### §5.1 エラーコード

| code | 意味 | リカバリ方針 |
|:---|:---|:---|
| `E_EMPTY_INPUT` | `source.text` が空 | 呼び出し側が input 検証 |
| `E_OVERSIZED_INPUT` | token 数が 4096 超 | 呼び出し側が分割 |
| `E_UNSUPPORTED_LANG` | `metadata.language` が en/ja 以外 | 別 spec で対応 |
| `E_PARSE_FAILED` | 出力 CCL が Hermeneus parse 失敗 | 内部リトライ最大 3 回後に error |
| `E_STRUCTURAL_VIOLATION` | 構造保存率が閾値未満 | 同上 |
| `E_LLM_TIMEOUT` | LLM-based 実装での timeout | 同上 |
| `E_INTERNAL` | 上記以外 | bug report |

### §5.2 silent fallback 禁止

- どのエラーケースでも、converter は **partial result を返してはならない**
- 「parse 失敗したが文字列は返す」は禁止
- 「構造保存率は低いが ok 扱い」は禁止
- F5 の血痕: 過去の HGK 実験で silent fallback が confound 要因になった例 → 本 spec で禁止

---

## §6 構造保存率の operational 定義

C1 (構造保存差分主張) の confound を避けるため、converter 自身の「構造保存」をどう測るかを契約として固定する。

### §6.1 構造保存の 4 signal

converter は出力ごとに以下 4 signal を `diagnostics.fidelity_signals` に格納する。

| signal | 測定対象 | 算出 |
|:---|:---|:---|
| `step_count_match` | NL-CoT の step 数 vs CCL-CoT の step 数 | min(a,b) / max(a,b) (1.0 で完全一致) |
| `entity_preservation` | NL-CoT 中の数式・変数名・数値が CCL-CoT に保持されているか | jaccard(entities_NL, entities_CCL) |
| `dependency_preservation` | NL-CoT のステップ依存 DAG vs CCL-CoT の依存 DAG | edge-jaccard |
| `final_answer_preservation` | NL-CoT 末尾の数値解答 vs CCL-CoT 末尾の数値解答 | 完全一致なら 1.0、形式違いなら 0.5、不一致なら 0.0 |

### §6.2 構造保存率の合成

```
structural_isomorphism = (
    0.2 * step_count_match +
    0.3 * entity_preservation +
    0.3 * dependency_preservation +
    0.2 * final_answer_preservation
)
```

重み (0.2/0.3/0.3/0.2) は config.yaml で調整可。初版はこの値で固定する。

### §6.3 確証ガード

- `final_answer_preservation < 1.0` の時は **必ず警告ログ出力** (silent ok 禁止)
- 4 signal すべてが ≥ 0.7 でないと structural_isomorphism ≥ 0.9 に到達しない設計
- 「全体スコアが高ければ部分は妥協できる」を防ぐ — F2 の前提

---

## §7 Hermeneus 連携

### §7.1 検証経路

converter 出力後、以下の検証を converter 内部で完結させる。

1. `result.ccl_cot.ccl_text` を `02_解釈｜Hermeneus/` 経由で parse
2. parse 通過 → `parse_validity = true`
3. parse 失敗 → リトライ (最大 3 回) → 全失敗で `E_PARSE_FAILED`

### §7.2 Hermeneus は SOURCE

- Hermeneus parse 通過 = SOURCE 判定 (式が CCL syntax として有効)
- ただし「parse 通過 ⇏ 構造保存」(parse は syntax のみ、§6 が semantic を担う)
- C1 (構造保存差分) の検証では Hermeneus parse + §6 の両方を使う

### §7.3 Hermeneus 自身の改修禁止

- 本 spec は Hermeneus を **既存資産として参照** する
- converter のために Hermeneus を改修することは禁止
- Hermeneus の制限が converter に影響する場合、converter 側で適応する (例: 未対応 CCL 演算子は使わない)

---

## §8 設定契約 (config.yaml)

### §8.1 必須フィールド

```yaml
# config.yaml schema (Tier 3 で fix)
version: "v0.1"                # semver
implementation: enum [llm, ast, hybrid]
tokenizer:
  name: str                    # 例: "gemma-tokenizer-v4"
  version: str
hermeneus:
  binary_path: str             # 02_解釈｜Hermeneus/ 配下の startup
  timeout_ms: int              # 既定 5000
fidelity:
  weights:
    step_count_match: 0.2
    entity_preservation: 0.3
    dependency_preservation: 0.3
    final_answer_preservation: 0.2
  threshold: 0.9
limits:
  max_input_tokens: 4096
  max_output_tokens: int       # max_input_tokens × 4 (N2)
  max_retries: 3
llm:                           # implementation=llm のみ
  model: str
  temperature: 0.0             # 決定論性確保 (F3)
  seed: int|null
ast:                           # implementation=ast のみ
  intermediate_graph: enum [networkx, igraph]  # 永続化禁止 (N3)
```

### §8.2 設定変更の追跡

- `config.yaml` 変更時は SHA-256 を `audit.config_hash` に記録
- 変換結果と config.yaml は 1:1 対応 (F3 / 再現性)

---

## §9 評価契約

### §9.1 単体評価 (converter 単独)

| 評価項目 | 指標 | 合格基準 |
|:---|:---|:---|
| parse 通過率 | F1 | ≥ 0.99 (Tier 3 の事前登録 protocol で検証) |
| 構造保存率分布 | F2 | 中央値 ≥ 0.9, 最低 ≥ 0.7 |
| 決定論性 | F3 | 同一入力で 100% 再現 |
| 失敗時の blocking | F5 | 全 error path で partial result を返さない |

### §9.2 統合評価 (CCL-CoT SFT 実験への入力品質)

- C1-C3 の confound 要因として converter 品質を切り分ける
- Tier 3 paper §X (Methods) で converter 品質の sensitivity analysis を実施
- **converter 品質が低いと C1-C3 主張全体が弱まる** ことを paper で明示

---

## §10 実装方式の比較 (informative — 契約外)

> **本節は契約ではない。Tier 3 で方式選択の参考にするための比較メモ。**

| 方式 | 利点 | 欠点 | F1-F5 達成度予測 |
|:---|:---|:---|:---|
| LLM-based (Claude/Gemini few-shot) | 自然言語の柔軟性に対応 | 決定論性 (F3) の確保が難 / 構造保存 (F2) が unstable | F3 中, F2 中 |
| AST-based (NL parse → graph → CCL emit) | 決定論性◎ / 構造保存◎ | NL parser の robustness 不足 / 自然言語の表現の幅に追従しきれない | F3 高, F2 高, F1 中 |
| Hybrid (NL parse → graph → LLM emit) | 構造保存 + 自然言語柔軟性の両立 | 実装コスト大 | F3 中, F2 高 |

### §10.1 第一候補 (推定)

- **AST-based を第一候補** とする推定 [仮説 60%]
- 理由:
  1. F3 (決定論性) が C2/C3 paired protocol で必須
  2. Code → CCL transpiler (`code_ingest.py`) が AST + 9 ルールで実装済み — 設計の参照実装が HGK 内に存在
  3. NL parse の robustness 不足は、MATH-500 の構造化された CoT (LaTeX 数式 + 段落分割) が比較的扱いやすいことで緩和される

### §10.2 第二候補

- **Hybrid** を fallback とする
- AST-based で robust に処理できない NL 表現を LLM emit で補完
- ただし F3 (決定論性) を維持するため、LLM 部分は temperature=0 + seed 固定

---

## §11 撤回条件 (本 spec 自体の)

以下のいずれかが起きた場合、本 spec を撤回または大幅改訂する。

1. F1 (parse 通過率 ≥ 0.99) が 3 種類の実装方式すべてで未達 → 仕様自体が現実的でない可能性
2. §6 の 4 signal で構造保存を測ることが Tier 3 の paper レビューで批判され、代替指標が提案された場合
3. Hermeneus 仕様変更で CCL syntax が破壊的に変わった場合
4. NL-CoT → CCL-CoT という変換が、Tolmetes 判断で「不要 (CCL の native CoT を直接生成すべき)」と判定された場合

撤回時は本 spec の §M0 相当の理由を記録し、後続 spec から back-link する。

---

## §12 接続 — 隣接資産との関係

| 接続先 | 種別 | 関係 |
|:---|:---|:---|
| `02_解釈｜Hermeneus/` (CCL parser) | 既存資産 | 検証側として参照。改修禁止 (§7.3) |
| `20_機構｜Mekhane/_src｜.../symploke/code_ingest.py` (Code → CCL transpiler) | 既存資産 | AST-based 実装の参照設計 |
| `paper_ccl_cot_sft_draft.meta.md` (Tier 1) | 同 program | C1-C3 の confound 要因として converter 品質を吸収 |
| `paper_ccl_cot_sft_draft.md` (Tier 3, 未起票) | 同 program | converter 評価結果を Methods 節で報告 |
| `experiments/ccl_cot_sft_protocol.md` (未起票) | 同 program | converter 経由で生成された CCL-CoT で SFT |
| `experiments/ccl_categorical_semantics.md` | 既存 | CCL ≅ 圏論 14 演算子対応。converter 出力の演算子集合の射程設定 |

---

*v0.1 — 2026-04-29 — Tier 2 起票 (本セッション)*
*次版予定: Tier 3 paper 本体起票時に §10 の方式選択を確定 → v0.2 で contract 詳細化*
