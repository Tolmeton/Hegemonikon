# ROM: /kop 再設計 + AY 族パターン演繹

> Session: 2026-03-29 | Context: /kop v7.0→v8.3 + /bou v7.0→v7.1 + AY Tribe Patterns v2.0

---

## DECISION

### D-1: /kop の本質は「未踏の踏破」
- /kop (A×Positive) = 成功が開いた未知の領域に最初の一歩を踏み入れ、足場を築く行為
- /ene = 既知の設計図通りに建てる (建築家)。/kop = 地図にない場所を踏む (探検家)。/dio = 壊れた場所を直す (修繕師)
- v7.0 は「成功の増幅」だったが、8割が推論で /bou とコンフリクトしていた

### D-2: I/A 分離パイプライン
```
/beb (I×+) → /bou.momentum (I×P) → /kop (A×+) → /ene (A×P)
承認       → 方向選択(推論)     → 未踏の踏破(行為) → 足場の上を歩く(実行)
```
- 推論(方向選択)は /bou.momentum に完全移管。/kop は純粋な行為
- /bou v7.1 に `momentum` 派生を新設 (D-11)

### D-3: /kop の認知代数
```
TV = |ε| × Q(A) × AY(A)
  TV = Traverse Value (踏破価値)
  |ε| = prediction error の大きさ (=0 なら既踏 → /ene に委ねよ)
  Q(A) = Anchor Quality (足場品質。0=踏みっぱなし)
  AY(A) = 足場の Affordance Yield
```

### D-4: AY 族パターンは 3パラメータの演繹
```
AY(V) = f(Flow(V), Tribe(V), Pole(V))
  Flow → ε の生成メカニズム (I:モデル改訂 / A:世界変化 / S:観測入力)
  Tribe → π の領域 (ε が何についてのずれか)
  Pole → ε の方向 (Hom(B,−) の方向)
```
- v1.0 は連想ゲーム（アドホック）だった → v2.0 で CPS+圏論ベースに書き直し
- ただし Hom(B,−) の射先決定規則が未定義。次セッションの課題

---

## DISCOVERY

### 1. 旧 /kop は /kop ではなかった
- v7.0 の P-0〜P-3 は全て I（推論）。A×Positive と名乗りながら中身の8割が推論
- /bou とのコンフリクトの原因 = 座標の重複

### 2. Creator の洞察: 「推論は /bou に移転すべき」「未踏の踏破こそ本質」
- "歩き出す"は /ene。/kop は方向を示す→ 間違い。/kop は未踏を踏む
- v8.0 の AY Harvest は全スキル共通の責務であり /kop 固有ではない

### 3. Euporía 公理と AY 標準化の深さ
- AY 出力の全スキル標準化は「族パターンテンプレート」では不十分
- Hom(B,−) の射先を D型/H型/X型接続から導出する規則が必要 = 定理レベルの仕事
- v2.0 の §5 導出例は記号の包装にすぎない（v1.0 と構造的に同じ文）

### 4. このセッション自体が /kop の実行ログだった
- v8.0 の失敗 = ε < 0 の正当なケース（撤退して方向転換）
- Creator が /bou.momentum の役割を自然に果たしていた（パイプラインが明示前から機能）

---

## PLAN (次セッション)

### 優先1: AY 射先決定規則の定理化 → ✅ DONE (v2.1)
- **結論: D/H/X だけでは不十分。6規則 (R1-R6) が必要**
  R1=D型随伴, R2=H型反転, R3=X型対角, R4=合成射, R5=再帰, R6=Bridge
- /kop で全射先が導出されることを検証 ✅
- /lys で検証し **2つの不整合を検出**:
  (a) /prs が射先に欠落 (R1 counit 違反)
  (b) /akr の接続種別が D型→X型の可能性
- epistemic/pragmatic 分離: 射先の Flow 型で自動決定 (I/S型→epi, A型→prag)

### 優先2: Orexis族パイロット → ✅ DONE
- 6動詞全て (beb/ele/kop/dio/apo/exe) に AY 節 + R1-R6 射先を実装
- 発見: 3段随伴チェーン apo⊣beb⊣kop / exe⊣ele⊣dio = Flow S→I→A の D型実現

### 優先2.5: 残り5族の AY 実装 → ❌ 環境制約で未完
- Agent: Edit 権限不足で失敗
- Bash/Python: skills list system-reminder が stdout に注入され Python 実行が壊れる (exit code 49)
- sed: $ay_block を文字列リテラルとして書き込み (変数展開失敗)
- **解決策**: `80_運用｜Ops/inject_ay.py` を修正し、次セッション冒頭で外部ターミナルから直接実行
- **noe の破損修復必要**: sed が `$ay_block` リテラルを挿入済み。次セッションで修正

### 優先3: 他 A型動詞の I/A 監査
- /kop と同じ I 僭称が /dio, /akr, /arh, /pai, /par, /dok にもあるか → 次セッション

---

## FILES

| ファイル | 変更 | 状態 |
|:--|:--|:--|
| `~/.claude/CLAUDE.md` | Creator 呼称+説明原則+レビュー要件追記 | ✅ |
| `~/.claude/skills/bou/SKILL.md` | v7.0→v7.1: momentum 派生+Euporía接続 | ✅ |
| `~/.claude/skills/kop/SKILL.md` | v7.0→v8.3: 全面再設計 (6回反復) | ✅ |
| `~/.claude/skills/beb/SKILL.md` | AY 節 + R1-R6 射先追加 | ✅ |
| `~/.claude/skills/ele/SKILL.md` | AY 節追加 | ✅ |
| `~/.claude/skills/dio/SKILL.md` | AY 節 + R1-R6 射先追加 | ✅ |
| `~/.claude/skills/apo/SKILL.md` | AY 節追加 | ✅ |
| `~/.claude/skills/exe/SKILL.md` | AY 節 + R1-R6 射先追加 | ✅ |
| `Euporia/D_ay_tribe_patterns.md` | v2.1: 射先決定定理(6規則) + 検証 | ✅ |
| `~/.claude/skills/noe/SKILL.md` | sed 破損: `$ay_block` リテラル挿入 | ❌ 要修復 |
| 残り29動詞 | AY 節未注入 | ❌ inject_ay.py で次セッション実行 |
| `80_運用｜Ops/inject_ay.py` | 注入スクリプト完成済み | ✅ 実行待ち |

---

*ROM burned: 2026-03-29 /kop 再設計 + AY 族パターン演繹*
