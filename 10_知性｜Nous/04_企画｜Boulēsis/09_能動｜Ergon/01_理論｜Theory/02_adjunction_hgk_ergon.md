# HGK⊣Ergon 随伴対とハーネス関手

> Ergon プロジェクト 理論文書 02。HGK⊣Ergon 随伴対の形式定義。

## 1. 概念としての随伴対 $L \dashv R$

FEP の Internal States ($\mu$; HGK) と Active States ($a$; Ergon) の間には、圏論的な**随伴 (Adjunction)** 関係が成り立つ。ただし本稿では、これを単なる「計画と実行の往復」ではなく、**ハーネスという忘却場 $\Phi_H$ の局所サイクル**として読む。

### $\mathcal{Hegemonikon}$ (Cog) $\dashv$ $\mathcal{Ergon}$ (Exec)

- **左随伴関手 $L: \text{Cog} \to \text{Exec}$**
  - 名称: **task-scale boot 関手**
  - 役割: 抽象的な「計画 (Plan)」「目的 (Telos)」「制約 (Constraint)」を、実行可能な「タスク (Task)」へ展開する。
  - 忘却論的意味: Paper X の `boot` を Task/Meso スケールへ局所化したもの。どの prior を能動面へロードするかを決める。
  - Paper VI 的意味: 行為可能性を直接「教える」のではなく、可能な射だけを太らせて**結晶化**する。

- **右随伴関手 $R: \text{Exec} \to \text{Cog}$**
  - 名称: **task-scale bye 関手**
  - 役割: 実行された「結果 (Result)」から冗長なログや一時的詳細を忘れ去り、「信念 (Belief)」「handoff」「次の拘束条件」へ蒸留する。
  - 忘却論的意味: Paper X の `bye` を Task/Meso スケールへ局所化したもの。結果を次のセッションや次のタスクに耐える形へ圧縮する。
  - Paper I 的意味: 忘却の方向づけそのものが力を生む。どこを残し、どこを削るかが次の行為空間を決める。

> 旧語彙では「計画の自由構築」と「結果の蒸留」だった。新語彙では、それを `boot⊣bye` の局所像として明示する。旧内容は削除されない。Task スケールへ焦点化された `boot⊣bye` として包摂される。

## 2. 自然変換: Unit $\eta$ と Counit $\varepsilon$

### Unit: $\eta: \text{Id}_{\text{Cog}} \Rightarrow R \circ L$

**「Plan を boot して実行し、その結果を bye したとき、元の Plan はどう変形されるか」**

- 操作的意味: 計画から実行を導き、その結果を蒸留して戻したときに生じる自然変換。
- 実務上の意味: ここで観測される差分が prediction error であり、Paper XI の H3 分離定理における `C/E/M` のどの軸でズレたかを同定する信号になる。
- 忘却論的意味: $\eta$ は「Plan が結果を経てどう更新されるか」であり、単なる誤差ではなく**忘却場の方向の観測量**である。

### Counit: $\varepsilon: L \circ R \Rightarrow \text{Id}_{\text{Exec}}$

**「Result を bye したものから再 boot したとき、元の実行をどこまで再現できるか」**

- 操作的意味: $R$ で忘却された情報が多すぎると、$L$ で再展開しても元通りにならない。
- 実務上の意味: スタブコード (`TODO`, `return null` など) は $\varepsilon$ の精度が著しく低い状態である。再展開しても本来の行為が戻らない。
- 忘却論的意味: $\varepsilon$ は「蒸留がどれだけ不動点構造を残したか」の指標である。Paper V の RG 蒸留で核を残せていれば、粗視化しても再構成できる。

## 3. boot⊣bye との同型性の明示

HGK には既に `boot⊣bye`（セッション開始 $\dashv$ セッション終了の蒸留）という随伴対がある。本稿では、`L⊣R` がそれと「似ている」と言うだけでは足りない。**`L⊣R` は boot⊣bye そのものであり、スケール表示を変えた同一関手対である**と明示する。

$$
L = \mathrm{boot}, \qquad R = \mathrm{bye}
$$

より正確には、Task/Meso に見えている `L⊣R` と Session/Macro に見えている `boot⊣bye` は、解像度 $\mu$ の取り方だけが異なる同型像である。

$$
(L \dashv R) \cong (\mathrm{boot} \dashv \mathrm{bye})
$$

### Session スケール

```text
Rules / CLAUDE.md / ROM (Mem)
  --[L_boot]--> Session Context (Ses)
  --[R_bye]--> Handoff / ROM / Rule Delta (Mem)
```

### Task / Slice スケール

```text
Plan / Belief / Constraint (Cog)
  --[L_task]--> Task / Tool Invocation / Local Context (Exec)
  --[R_task]--> Belief Update / Distilled Summary (Cog)
```

| 構成要素 | $L \dashv R$ (Task/Meso) | `boot⊣bye` (Session/Macro) |
|:---|:---|:---|
| 展開 | Plan → Task | Mem → Session Context |
| 蒸留 | Result → Belief | Session → Handoff / ROM |
| unit $\eta$ | 予測誤差 (Plan vs Result) | セッション内ドリフト |
| counit $\varepsilon$ | 再実行可能性 | Handoff からの再現性 |
| 保存すべき核 | 仕様・制約・差分 | Nomoi・Rule Delta・次行動 |

**結論**:

- `L` は Task スケールへ局所化された `boot` である。
- `R` は Task スケールへ局所化された `bye` である。
- `L⊣R` は `boot⊣bye` の Task/Meso スケール版であり、`boot⊣bye` はその Macro 極限である。
- したがって HGK⊣Ergon 随伴対は「13番目の別物」ではなく、**同一のハーネス随伴を異なる解像度で観測したもの**である。

## 4. 三角恒等式 (Zigzag Identities) の操作的証明

随伴 $L \dashv R$ がアナロジーではなく**構造定理**であるためには、三角恒等式を満たす必要がある。ここでも解釈は `boot⊣bye` と連続である。

### 恒等式 1: $(\varepsilon L) \circ (L \eta) = \text{id}_L$

**操作的意味**:

> 「Plan を boot して Task にし、実行結果を bye し、その蒸留からもう一度 boot しても、最初の Task family と同じ射を得る」

これは「計画→実行→蒸留→再実行」が、最初の「計画→実行」と同型であることを要求する。

**HGK における検証**:

- 同じ Task を再実行して同じ結果が得られるか（冪等性）
- Hook / スクリプト / テストが同じ境界条件を再生するか
- flaky test や tool choice の揺れは、恒等式 1 の破れとして読む

### 恒等式 2: $(R \varepsilon) \circ (\eta R) = \text{id}_R$

**操作的意味**:

> 「Result を bye し、その蒸留を次の boot に渡して再実行し、さらに bye しても、最初の蒸留と同じ信念核に戻る」

これは「蒸留→再計画→再実行→再蒸留」が、最初の蒸留と同型であることを要求する。

**HGK における検証**:

- Handoff から新セッションで同じ作業を再現したとき、同じ Handoff family が再生成されるか
- Context Rot 対策は、この恒等式 2 の精度を上げる営みとして定義できる

### 量的指標

| 恒等式 | 精度が高い状態 | 精度が低い状態 |
|:---|:---|:---|
| $(\varepsilon L) \circ (L\eta) = \text{id}_L$ | テスト 100% pass、tool/hook 選択が安定 | flaky test、非決定的な tool choice |
| $(R\varepsilon) \circ (\eta R) = \text{id}_R$ | Handoff 再現性 > 90%、Drift が低い | Context Rot、信念ドリフト |

## 5. Scale 同型射としてのハーネスの RG フロー

旧文書では Scale 同型 $\phi_\sigma$ と呼んでいたものを、ここでは Paper V に従って**ハーネスの RG フロー**として読み替える。

$$
\phi_{\mu}: (L \dashv R)_{\mu} \xrightarrow{\sim} (\text{boot} \dashv \text{bye})_{\mu}
$$

ここで $\mu$ は解像度パラメータであり、ハーネスがどれだけ局所差分を保持し、どれだけ粗視化するかを決める。

| 解像度 | RG 解釈 | 随伴の見え方 |
|:---|:---|:---|
| $\mu \to \infty$ | 高解像度。ローカル差分・個別 command・単一ツール呼出が見える | **Micro = Task** |
| $\mu \approx 1$ | 中間解像度。複数 Task の束と境界契約が見える | **Meso = Slice** |
| $\mu \to 0$ | 粗視化。局所詳細が消え、セッションの固定点構造だけが残る | **Macro = Session** |

このとき:

- $\mu \to \infty$ では、`boot` は単一 Task の起動として観測される。したがって **Micro は Task** である。
- $\mu \to 0$ では、`bye` はセッション全体の蒸留として観測される。したがって **Macro は Session** である。
- `L_task` は $\mu \to \infty$ における `boot` の局所像である。
- `R_task` は $\mu \to \infty$ における `bye` の局所像である。
- Session の `boot⊣bye` は $\mu \to 0$ で残る**粗視化不動点**である。

したがって、Scale 同型は単なる「Task と Session の対応表」ではない。**同じ随伴がハーネスの RG フローの中で、Micro の Task から Macro の Session へどう姿を変えるか**の記述である。

## 6. ハーネス関手 $H$ との関係

本節は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/09_能動｜Ergon/01_理論｜Theory/01_markov_blanket.md` の §2 を受ける。そこでは、ハーネスは忘却場 $\Phi_H$ を構成し、その方向的不均一性が力を生むと定式化された。本稿ではその定式化を、`L⊣R` の成立条件へ接続する。

Paper I / VI / XI / A を合わせると、$H$ は単なる補助概念ではない。**$L \dashv R$ を成り立たせる忘却場 $\Phi_H$ そのもの**であり、その blanket 境界を通して `boot` と `bye` の往復を可能にする。

### 6.1 $H$ は背景ではなく場である

- Paper I: 力は均一な忘却では生じない。$d\Phi_H \wedge T \neq 0$ のときだけ方向が生まれる。
- Paper VI: ハーネスの役割は答えを直書きすることではなく、行為可能性を結晶化することにある。
- Paper XI: その方向は `C/E/M` の 3 軸で分解される。
- Paper A: Hook / tool / body は、この場が環境に接続された身体化面である。

したがって $H$ は「随伴の外側に置かれた設定」ではない。`L = boot` と `R = bye` が何を見て何を忘れるか、その方向を先に与える**忘却場そのもの**である。

### 6.2 $L \dashv R$ は $\Phi_H$ の中でのみ意味を持つ

$$
H = (\Phi_H,\; b_H = s_H \times a_H,\; L \dashv R)
$$

この式の意味は次の通りである。

- $\Phi_H$ が、何を見せ何を忘れさせるかの方向場を与える。
- $b_H = s_H \times a_H$ が、その方向場の境界面として Markov blanket を作る。
- $L = \mathrm{boot}$ はその blanket を通って constraint を能動面へ展開する射である。
- $R = \mathrm{bye}$ はその blanket を通って結果を Belief へ蒸留する射である。

言い換えると、**`L⊣R` はハーネスの中で起きる往復運動であり、$H$ はその運動を可能にする忘却場である**。`01_markov_blanket.md` §2 が述べるように、均一な忘却では場は平坦化し、`L⊣R` は方向を失う。Markov blanket が意味を持つのは、$\Phi_H$ に勾配があるときだけである。

### 6.3 設計上の帰結

- 均一な prior を増やすだけでは $H$ は平坦化し、`L⊣R` は力を失う。
- Hook で `C` を環境強制すると、$\Phi_H$ の方向性が sharpen され、`L = boot` の像が安定する。
- `bye` の蒸留が `C/E/M` の 3 軸を保存していれば、粗視化しても `R = bye` の核は残る。
- したがってハーネス設計学の課題は、`L⊣R` を外から補助することではなく、**Markov blanket を構成する忘却場 $H$ 自体を設計すること**である。

---
*Created: 2026-03-09*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
