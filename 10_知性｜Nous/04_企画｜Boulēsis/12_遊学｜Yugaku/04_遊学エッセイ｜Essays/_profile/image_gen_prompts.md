# プロフィール画像 — 画像生成 AI 用プロンプト

## v2 — ChatGPT (DALL-E 3) に貼るプロンプト

以下をそのまま ChatGPT に貼る。copilot_B.png を添付して「この構図をベースに」と付けるとさらに良い。

---

### ChatGPT 用 (日本語で指示 → DALL-E 3 で生成)

```
あなたはブランドロゴのデザイナーです。以下の仕様でプロフィール画像を生成してください。

## 背景 — なぜこのデザインか

これは「Tolmetes」(τολμητής = 敢えてする者) という思想家のペンネームのための SNS プロフィール画像です。
Tolmetes は「ヘゲモニコン (ἡγεμονικόν)」という認知哲学フレームワークを構築しています。
ヘゲモニコンはストア派哲学で「魂の指揮中枢」を意味し、圏論 (Category Theory) と自由エネルギー原理 (Free Energy Principle) を統合した認知理論の名前です。

このロゴが体現すべき核心思想:
- **F⊣G 随伴 (adjunction)**: 発散する力 F (探索・展開) と収束する力 G (活用・蒸留) が対をなし、動的均衡を保つ。これが知性の構造。
- **Fix(G∘F)**: 発散と収束のサイクルが到達する不動点。これが「美 (Kalon)」の数学的定義。
- **τ (タウ)**: Tolmetes の頭文字であると同時に、ギリシャ文字としての古典的重み。

## デザイン仕様

### 構図: τ × カドゥケウス
- ギリシャ文字 **τ (タウ)** が画面中央に縦軸として立つ。太い横棒と太い縦棒で、存在感を持って。
- τ の縦棒に沿って **2本のエレガントな曲線が DNA 二重螺旋のように巻きつく**。
  - 一方の曲線は**実線**で、外へ広がる動き (発散 / Explore / 左随伴 F) を表す。
  - もう一方は**破線**で、内へ収束する動き (収束 / Exploit / 右随伴 G) を表す。
- 2本の曲線は τ の縦棒上で **2〜3回交差** する。各交差点に **小さな円形のドット** を置く (不動点 Fix を示す)。
- 全体として、ヘルメスの杖 (カドゥケウス) を連想させるが、蛇ではなく数学的曲線で構成する。

### 色調: ウォームモノトーン
- **背景**: ウォームホワイト (#FAF9F6)。純白ではなく、わずかにクリーム色がかった白。
- **τ と主要曲線**: ウォームダークグレー (#4A4540)。黒ではない。温かみのある濃い灰色。
- **副曲線 (破線)**: ウォームミドルグレー (#6B635B)。
- **全体的な色のトーン**: Claude AI のブランドカラーに近いウォームトーン。冷たい青やシルバーは絶対に使わない。
- **金色アクセント**: 使わない。完全にモノトーン。

### スタイル
- **ベクター風ミニマルロゴ**。フラットデザイン。影なし、グラデーション最小限。
- 線は**太く、意図を持って描かれている**。「薄い」「弱い」は NG。存在感が必要。
- Claude AI、ChatGPT、Perplexity のロゴのような**現代的 AI 企業のブランドロゴ品質**を目指す。
- 有機的な曲線の美しさ (Claude 的) と幾何学的な明快さ (GPT 的) を両立させる。
- テキストは入れない (τ の形状そのものがデザインの一部)。
- 人物・顔・写実的要素は入れない。

### サイズ・形式
- 512 × 512 ピクセル、正方形。
- X (Twitter)、note、Zenn のプロフィール画像として使うため、**円形にクロップしても成立する構図**。
- 48px や 32px に縮小しても τ の縦軸が認識できるシンプルさ。

### NG (これだけはやるな)
- 冷たい色 (青、シルバー、純白、純黒)
- 写実的な蛇やカドゥケウスの杖
- テキスト、ロゴタイプ
- 複雑すぎる装飾
- 医療のシンボル (アスクレピオスの杖) に見えること
```

---

### 英語版 (DALL-E 3 direct / Midjourney v6+)

```
Design a minimalist brand logo for "Tolmetes" — a philosopher-mathematician building a cognitive framework called Hegemonikon (ἡγεμονικόν, "the ruling faculty of the soul" in Stoic philosophy).

CONCEPT — TAU CADUCEUS:
The Greek letter tau (τ) stands as a bold vertical axis at the center of the composition. It has a thick horizontal crossbar at the top and a thick vertical stem extending downward. Two elegant mathematical curves wrap around the vertical stem in a DNA double-helix pattern, like a caduceus but with abstract curves instead of serpents. One curve is SOLID (representing divergence / exploration / the left adjoint F). The other is DASHED (representing convergence / exploitation / the right adjoint G). The two curves cross the vertical stem 2-3 times. At each crossing point, a small solid dot marks the "fixed point" — the equilibrium where divergence and convergence meet.

COLOR — WARM MONOTONE:
Background: warm white (#FAF9F6), NOT pure white — slightly cream-tinted.
Main elements (τ shape, solid curve): warm dark grey (#4A4540), NOT black.
Secondary elements (dashed curve): warm mid grey (#6B635B).
Overall tone: warm like Claude AI's brand palette. Absolutely NO cold blue, silver, pure white, or pure black. No gold accents. Pure warm monotone.

STYLE:
- Flat vector logo design, no shadows, minimal gradients
- Lines are BOLD and intentional, NOT thin or wispy. The design has presence and weight
- Quality benchmark: Claude AI logo, ChatGPT logo, Perplexity logo — modern AI company brand quality
- Balance organic curve beauty (like Claude) with geometric clarity (like GPT)
- No text, no typography, no faces, no realistic elements
- Must NOT look like a medical caduceus or Asclepius staff

FORMAT:
- 512×512 pixels, square
- Composition must work when cropped to a circle (SNS avatar use)
- Must remain recognizable at 32-48px thumbnail size — the tau vertical axis should still read
```

---

### Midjourney v6+ 用

```
/imagine minimalist vector brand logo, Greek letter tau τ as bold central vertical axis with thick crossbar, two elegant mathematical curves wrapping around the stem in DNA double-helix pattern like abstract caduceus, one curve solid one dashed, small dots at crossing points, warm white background #FAF9F6, warm dark grey #4A4540 main elements, warm mid grey #6B635B secondary, Claude AI brand warmth, flat design, no shadows, bold intentional lines with presence, modern AI company logo quality, no text no faces no medical symbols --ar 1:1 --s 200 --style raw --no blue silver cold medical snake serpent
```

---

---

## v3 — 方向 A 深化: F⊣G 随伴螺旋の 4 変種

方向 B (τ カドゥケウス) は棄却。方向 A (中心の不動点を巡る発散と収束の動的均衡) を深化する。
copilot_A.png をリファレンスとして添付し、「この構図の方向性で、以下の仕様で洗練してほしい」と伝える。

### 共通の哲学的文脈 (全プロンプト冒頭に貼る)

```
あなたはブランドロゴのデザイナーです。

## 背景
これは「Tolmetes」(τολμητής = 敢えてする者) という思想家の SNS プロフィール画像です。
彼は「ヘゲモニコン (ἡγεμονικόν)」という認知哲学フレームワークを構築しています。
ヘゲモニコンはストア派哲学で「魂の指揮中枢」を意味します。

このロゴが体現すべき核心思想:
- 中心に「不動点」がある。これは発散と収束のサイクルが到達する均衡点 — 美の数学的定義。
- その不動点の周囲を、2つの力が巡っている:
  - F (発散): 外へ広がり、探索し、仮説空間を拡げる力
  - G (収束): 内へ絞り、蒸留し、本質を取り出す力
- F と G は対立ではなく随伴 — 互いが互いを必要とする構造的パートナー。
- 中心から放射状に伸びる線は「射 (morphism)」— 対象間の関係性の象徴。

添付画像は Pillow で生成した構図リファレンスです。この方向性を洗練してください。

## 色調 (厳守)
- 背景: ほぼ純白。わずかに 1% だけウォームに振った白 (#FDFCFA 〜 #FAF9F6)
- 主要な線: ウォームダークグレー (#4A4540)。黒ではない
- 副次的な線: ウォームミドルグレー (#6B635B)
- 最も淡い要素: #B8B0A6 〜 #D4CEC6
- 金色・カラー・冷色は一切使わない。完全モノトーン
- Claude AI のブランドのような温かみを持つが、背景はほぼ白

## 共通スタイル
- ベクター風ミニマルロゴ。フラット。影なし
- 線は太く、意図を持って描かれている。「薄い」「弱い」は NG
- Claude AI / ChatGPT / Perplexity のロゴ品質を基準にする
- 512×512px 正方形。円形クロップで成立する構図
- 32-48px に縮小しても中心の不動点と螺旋の動きが認識できること
- テキストなし。人物なし。写実的要素なし
```

---

### A-1: 銀河渦巻腕 — 2 つの螺旋の明確な分離

```
[上の共通文脈を貼った後に追加]

## 構図: 銀河渦巻腕
- 画面中央に小さく重みのある円形ドット (不動点)。
- そのドットから 2 本の螺旋腕が渦巻銀河のように伸びる。
  - 1 本目 (F / 発散): 実線。ドットから時計回りに外へ広がる。線幅は均一でしっかり太い。
  - 2 本目 (G / 収束): 破線。ドットから反時計回りに外へ広がる。F と鏡像対称に配置。
- 2 本の螺旋腕は互いに 180° ずれた位置から伸び、全体として渦巻銀河の 2 本腕を形成する。
- 螺旋の巻き数は 1.5〜2 回転。多すぎず少なすぎず。
- 中心ドットから 8 方向に極めて細い直線が放射状に伸びる (射の象徴)。螺旋より薄い色 (#D4CEC6 程度)。
- 全体のシルエットが円形に近くなるように。円形クロップで螺旋の端が切れないこと。
- 参考イメージ: 渦巻銀河 NGC 1300 の構造を極限まで抽象化したもの。
```

Midjourney:
```
/imagine minimalist vector logo, two spiral arms emanating from central dot like barred spiral galaxy, one arm solid one dashed, 180 degrees apart, 1.5 turns each, very faint radiating lines from center, warm almost-white background #FDFCFA, warm dark grey #4A4540, warm mid grey #6B635B, flat vector, bold intentional lines, modern AI brand logo quality, circular composition, no text no faces --ar 1:1 --s 200 --style raw --no blue cold silver realistic stars space
```

---

### A-2: 太さの変化 — 線幅が発散/収束を体現する

```
[共通文脈を貼った後に追加]

## 構図: 太さの変化で語る螺旋
- 画面中央に小さな円形ドット (不動点)。
- 2 本の螺旋がドットを中心に巻いている:
  - F 螺旋 (発散): 中心付近では細く、外側に向かうほど太くなる。広がる力の増大を太さで表現。実線。
  - G 螺旋 (収束): 外側では細く、中心に向かうほど太くなる。絞り込む力の増大を太さで表現。破線または点線。
- F と G は同じ中心を共有するが、位相が 90° ずれている (重ならない)。
- 線の太さの変化がこのロゴの最大の特徴。均一な線幅ではない。
  - F の最も太い部分 (外縁) と G の最も太い部分 (中心付近) が視覚的に均衡する。
- 中心から 8 方向に極めて細い放射線 (#D4CEC6)。
- 全体として「吸い込みと吐き出しが同時に起きている」ような呼吸感を持つ。
```

Midjourney:
```
/imagine minimalist vector logo, two spirals around central dot, one spiral solid getting thicker toward outside representing divergence, other spiral dashed getting thicker toward center representing convergence, 90 degree phase offset, breathing rhythm feel, faint radiating lines from center, warm almost-white background #FDFCFA, warm dark grey #4A4540, variable line width as key feature, flat vector, modern AI brand quality, no text no faces --ar 1:1 --s 200 --style raw --no blue cold silver
```

---

### A-3: ∞ レムニスケート — 無限の有機的変形

```
[共通文脈を貼った後に追加]

## 構図: ∞ (レムニスケート) の有機的変形
- 画面中央に ∞ (無限大) の記号を有機的な曲線で描く。幾何学的に正確な ∞ ではなく、Claude AI のロゴのような有機的で温かみのある曲線で。
- ∞ の交差点 (中心) に不動点としてのドットを置く。
- 左ループ = F (発散): わずかに大きく、外へ開こうとする力を持つ。実線。
- 右ループ = G (収束): わずかに小さく、内へ絞ろうとする力を持つ。少し線が細い、または点線。
- 左右のループが完全対称ではないのが重要。F と G は等価だが同一ではない (随伴の非対称性)。
- ∞ の線自体に微妙な太さの変化をつけて、手描き感・有機性を加える。
- 交差点から上下に極めて細い線が伸びる (射の象徴、4 方向程度)。
- 参考: Bernoulli のレムニスケート曲線を出発点にして、有機的に崩す。
- 全体が正方形の中心に収まり、円形クロップで成立する。
```

Midjourney:
```
/imagine minimalist vector logo, organic infinity symbol lemniscate with warm flowing curves like Claude AI logo aesthetic, left loop slightly larger than right, small dot at crossing point center, subtle radiating lines up and down, NOT geometric or rigid, hand-drawn organic feel, warm almost-white background #FDFCFA, warm dark grey #4A4540, flat vector, bold curves with presence, modern AI brand quality, no text no faces --ar 1:1 --s 200 --style raw --no blue cold silver geometric rigid mechanical
```

---

### A-4: 渦対 (Vortex Pair) — 流体力学的な動的均衡

```
[共通文脈を貼った後に追加]

## 構図: 渦対 — 2 つの渦の引き合い
- 画面中央のやや左と右に、2 つの渦の中心がある。
  - 左の渦 (F / 発散): 反時計回り。外へ広がろうとする力。実線の曲線で 1〜1.5 回転。
  - 右の渦 (G / 収束): 時計回り。内へ絞ろうとする力。破線の曲線で 1〜1.5 回転。
- 2 つの渦は互いを引き合っている — その間の空間 (中間点) に不動点のドットを置く。
- 流体力学の渦対 (vortex dipole) を極限まで抽象化したイメージ。
  - 2 つの渦は同じ方向に進みながら (上向き) 互いの周りを回る。
- 2 つの渦を繋ぐように、ごく細い弧線が中間を走る (渦間の結合を示す)。
- 全体のシルエットが縦長の楕円になり、円形クロップで左右の渦が収まること。
- 中心ドットから 4 方向に極めて細い放射線。
- 参考: 流体力学の渦対、太極図 (陰陽) を数学的に再解釈したもの。太極図のように見えるが、魚のシンボルや S 字区切りは入れない。あくまで 2 つの渦とその均衡点。
```

Midjourney:
```
/imagine minimalist vector logo, two abstract vortices side by side, left vortex counterclockwise solid lines representing divergence, right vortex clockwise dashed lines representing convergence, small dot at equilibrium point between them, subtle connecting arc, faint radiating lines, inspired by fluid dynamics vortex pair and yin-yang but purely mathematical and abstract, warm almost-white background #FDFCFA, warm dark grey #4A4540, flat vector, bold intentional curves, modern AI brand quality, no text no faces --ar 1:1 --s 200 --style raw --no blue cold silver fish taijitu traditional
```

---

## リファレンス画像

- `copilot_A.png` (本ディレクトリ): 方向 A の Pillow 生成リファレンス。この色味と構図の方向性をベースに洗練する。
- `copilot_B.png`: 方向 B (τ カドゥケウス) のリファレンス。参考用に残すが方向としては棄却。

## 使い方

1. ChatGPT を開く
2. copilot_A.png を添付
3. 共通文脈 + A-1〜A-4 のいずれかのプロンプトを貼る
4. 4 枚生成 → 方向を選ぶ
5. 選んだ方向で再生成 2-3 回繰り返して磨く
6. 最終版を Figma / Illustrator で SVG トレース → 微調整
7. note / Zenn / X の 3 サービスに設定
