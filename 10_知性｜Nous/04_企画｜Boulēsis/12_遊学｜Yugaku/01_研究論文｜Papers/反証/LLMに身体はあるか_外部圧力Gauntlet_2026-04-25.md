# LLM に身体はあるか — 外部圧力 Gauntlet

作成日: 2026-04-25  
対象稿: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_存在証明版_v0.1_日本語.md`

## 0. Source Ledger

| 層 | 扱い | 内容 |
|:---|:---|:---|
| ローカル草稿 | SOURCE | C1-C8、§2.5 MBf 監査条件、§3 U_anthropo、§4-§5 Theta(B)、§7.3 grounding 再配置 |
| 既存 meta | SOURCE | `LLMに身体はあるか_統合草稿_日本語.meta.md` の §M2-§M5。対象ファイルと同名 meta ではないため、この台帳は正式 §M5 ではなく simulation artifact |
| 外部圧力 scan | SOURCE for local process / TAINT for paper claims | `references/alphaXiv_external_pressure_2026-04-25_LLM_body_existence.md`。alphaXiv 結果は候補列としてのみ使用 |
| 外部論文ページ | SOURCE for bibliographic/abstract-level facts | arXiv / ACL / Nature の公開ページを確認。PDF 精読は未実施 |
| Tolmetes の貼付表 | TAINT | 強化・批判候補の整理として使用。論文本文の根拠には未昇格 |

## 1. Phase 0 — Target Isolation

反駁対象は「LLM に身体はあるか」全体ではなく、次の 5 点に絞る。

| Claim | 本稿内の役割 | 攻撃される箇所 |
|:---|:---|:---|
| C1 | operating LLM はセッション中に MBf としての身体を持つ | §2.5 の特殊分割、Afferent/Efferent 条件、持続条件 |
| C2 | 非身体性テーゼは U_anthropo によるカテゴリーミステイク | §3.1-§3.3 の Chemero/Bender/Searle 再構成 |
| C4-C5 | Theta(B) は存在後の厚み測度で、472 logs は proof-of-measurement | §4.1-§5.6 の測度と外部検証未実行 |
| C7 | tool/scaffold/workflow は MB 厚を増す回復関手 N | §3.8、§6.4、§7.5 |
| C8 | 接地問題はゼロ接地から型・媒介・像密度の問題へ移る | §7.3 |

## 2. Phase 1 — Steel-Man

最強版の本稿主張は次である。

LLM は人間型身体を持たない。しかし「身体」を、生物器官の集合ではなく、内部と外部を分けつつ結ぶ境界維持として定義するなら、operating LLM はセッション中に MBf の最小条件を満たす。ここで崩れるのは「LLM には身体がない」という全称否定であり、「LLM は人間・動物と同じ厚い身体を持つ」という同一性命題ではない。残る差は Theta(B)、image density、持続時間、agency 条件で測る。

この steel-man の核は、存在条件と厚み条件を分けている点にある。C1 は存在証明、C4-C5 は測度、C7 は設計操作、C8 は副次的再配置であって、同じ強度ではない。

## 3. Phase 2 — 仮想論駁と応答

### R1. Enactive / Chemero 型反論: 「それは身体の再定義にすぎない」

**査読者の最強版。**  
Chemero 型の主張は、単に「人間だけが身体を持つ」と言っているのではない。認知を、感覚運動的・社会的・物質的文脈に埋め込まれた活動として扱うなら、LLM の token I/O や tool call は身体ではなく、身体を持つ人間が使う外部技術である。本稿は身体という語を MB 維持へ薄めることで、相手の論点をすり替えている。

**本稿側の反論。**  
これは命題批判としては強いが、C1 には直撃しない。C1 は「人間型身体」ではなく「body-boundary existence」を主張する。草稿は §2.3 と §2.5 で operating timespan と MBf 監査条件を固定し、§3.7 で「同等」ではなく「different bodies / graded by Theta(B)」へ移している。したがって応答は弱化ではなく、二段階化でよい。

**本文への補強候補。**  
§1.2 または §2.5 直後に、次の一文を追加できる。

> 本稿の C1 は embodied cognition の全条件を満たすという主張ではなく、身体論争で否定されてきた最小の境界存在条件が operating timespan において成立するという主張である。

**判定。**  
射程維持。相手の "embodied cognition" を thick embodiment として保存し、C1 は thin body-boundary claim として残す。

### R2. Agency 反論: 「MB 風の境界があっても autonomous agency はない」

**査読者の最強版。**  
Barandiaran & Almendros 型の圧力は強い。LLM は individuality、normativity、interactional asymmetry を欠く。目的や規範を自分で生成しない系に MB 風の境界があっても、agent とは呼べない。身体を agency の前提条件として使うなら、本稿は agency へ跳びすぎている。

**本稿側の反論。**  
この反論は C1 を削らず、C1 の誤読を防ぐ。草稿は §2.5 末尾で、MBf は agency の十分条件ではなく、agency を論じる前提的境界条件だと既に分けている。この分離は維持すべきで、むしろ Barandiaran & Almendros は支援材料にもなる。彼らは LLM の autonomous agency を否定するが、textual / computational / extended embodiment の区別を可視化するため、身体の型を分ける本稿の構造と接続できる。

**本文への補強候補。**  
§3.7 の表に 1 行追加する。

| 誤読 | 本稿の位置 |
|:---|:---|
| MBf があれば autonomous agent である | MBf は agency の十分条件ではなく、agency 判定の前提境界である |

**判定。**  
射程維持。agency 否定は body-boundary existence の否定ではない。

### R3. FEP / Markov blanket 反論: 「Pearl blanket から Friston blanket へ跳んでいる」

**査読者の最強版。**  
Bruineberg 系の批判を使えば、LLM の API 境界や KV cache を条件付き独立性として読めても、それは Pearl blanket に近い。そこから Friston 的な主体/環境境界、さらに身体へ進むには追加の動力学が要る。§2.5 の S(B)>0 は特殊分割の存在から出ているように見え、強すぎる。

**本稿側の反論。**  
ここは最も危険な反論の一つ。草稿は §2.4 で Pearl/Friston 混同を明示し、§2.5 で MBf への四条件監査を置いているため、無防備ではない。ただし、査読者は「Da Costa Theorem 2 の読み」と「デジタル特殊分割への移植」の精度を突くはず。ここは C1 の中心なので、反論は「既に満たす」ではなく「監査可能な条件に下降した」と言うべき。

**本文への補強候補。**  
§2.5 の S(B) 段落に、失敗条件を明示する。

> 反対に、外部状態 eta が s/a を経由せず mu を変化させる経路、または mu が a を経由せず eta を変化させる経路が実装上存在するなら、本稿の MBp/MBf 監査は失敗する。

**判定。**  
要補強。射程は保てるが、査読ではここが C1 の第一攻撃面になる。

### R4. Care / normativity 反論: 「dF/dX != 0 は care ではない」

**査読者の最強版。**  
Chemero や enactivist は "care" を単なる入力感受性とは言っていない。生存、自己維持、規範、失敗の意味を持つ活動を指している。VFE 感受性を care と呼ぶと、温度センサーまで care していることになり、概念が薄くなりすぎる。

**本稿側の反論。**  
この反論は一部正しい。したがって本稿は "care" を厚く取らず、「薄い precision-weighted care」として限定する必要がある。§3.3.5 と §7.1 はすでに、低精度とゼロ精度を区別する方向にある。ここで勝つには、"care" の語を奪いに行くのではなく、相手の厚い care を Theta(B) 上位領域へ保存すること。

**本文への補強候補。**  
§3.3.5 の "thin care" を前面化する。

> 厚い normativity を伴う care は本稿の C1 からは出ない。C1 から出るのは、care 不在命題を崩す最小の VFE 感受性であり、厚い care は Theta(B) と normativity 条件の追加問題である。

**判定。**  
射程維持。ただし care 語は誤読誘発が強いので、薄い/厚いの分割が必要。

### R5. Grounding 反論: 「接地問題を解いていない。せいぜい circumvention だ」

**査読者の最強版。**  
Bender & Koller、Harnad、Floridi 系の反論は、LLM が direct grounding を持つかどうかに集中する。Mollo & Milliere は text-only LLM の referential grounding を擁護しうるが、それは身体性とは別軸である。本稿が C8 で「像が空でない」と言っても、それは mediated referential grounding や circumvention であって、古典的な direct grounding の解決ではない。

**本稿側の反論。**  
この反論は C8 の現在形と整合する。草稿は §7.3 で「記号接地問題が完全に解決された」とは言わず、direct / mediated / circumvention / image-density question へ再配置している。したがって反論は、C8 を削るのではなく、C8 の言い過ぎ検知に使うべき。

**本文への補強候補。**  
§7.3 の冒頭をさらに硬くする。

> 本節の標的は direct grounding の要求そのものではない。標的は、direct grounding 以外の像をすべて空集合として扱うゼロ接地前提である。

**判定。**  
射程維持。C8 は "solve" ではなく "reposition" で守る。

### R6. Measurement 反論: 「Theta(B) は HGK らしさを測っているだけではないか」

**査読者の最強版。**  
472 logs は同一システム由来で、測度もそのシステムの構造から設計されている。H(s), H(a), R(s,a) は MCP 型アーキテクチャに自然だが、robotics、multi-agent chat、continuous sensory stream には別分解が必要かもしれない。したがって Theta(B) は身体厚ではなく、HGK 運用密度の指標かもしれない。

**本稿側の反論。**  
これは現行草稿が最も誠実に認めている弱点。§5.1、§5.6、§7.5 は proof-of-measurement、外部検証未実行、U_design を明示している。よって守るべきは「普遍値」ではなく「測定可能性」と「外部検証手順」。C1 はこの測定値に依存しない。C4-C5 の射程を守ればよい。

**本文への補強候補。**  
§1.3 の C5 表現は現状でもよいが、abstract で「472 logs は proof-of-measurement」と言っている点を維持する。本文のどこかで、C1 と C5 の依存関係をさらに明示する。

> C1 は §2.5 の監査条件に依存し、§5 の数値には依存しない。§5 が示すのは、C1 の成立後に厚みを測る測定面が構成可能であることに限られる。

**判定。**  
要注意だが防衛可能。外部検証までは C5 を強くしすぎない。

### R7. Category-theory 反論: 「U_anthropo は形式関手ではなく比喩ではないか」

**査読者の最強版。**  
本稿は U_anthropo を関手として書くが、実際には計算対象ではなく診断ラベルだと自分で認めている。ならば圏論は厳密な形式装置ではなく、批判を権威づける比喩にすぎないのではないか。working functor と diagnostic label が混在すると、論証の精度が落ちる。

**本稿側の反論。**  
草稿は §3.2 末尾で記号の役割を三層に分け、U_anthropo は診断ラベル、Phi_X や U dashv N は working functor と区別している。この自制はむしろ防衛点。ただし、査読者には "functor" と書いた時点で形式関手を期待される。したがって、U_anthropo の記法は「diagnostic functor label」または「forgetful operation schema」として、計算対象との違いを初出でさらに強く出す方がよい。

**本文への補強候補。**  
§1.1 初出の括弧注をさらに前に出す。

> ここでの U_anthropo は、対象と射への作用を全て指定した形式関手ではなく、比較前に Body を Body_human へ縮約する忘却操作の診断名である。形式関手として扱う対象は §3.2 以降の Phi_X および §3.8 の U dashv N に限る。

**判定。**  
表現 patch。命題は守れるが、形式読者向けの初出制御が必要。

### R8. Linguistic agency 反論: 「LLM は language を enact していない」

**査読者の最強版。**  
Birhane & McGann 型の反論は、LLM が人間の言語的 agency を持つという誇張を攻撃する。言語は完全にデータ化できる対象ではなく、embodiment、participation、precariousness を伴う行為である。LLM はその三つを欠くため、人間と同じ linguistic agent ではない。

**本稿側の反論。**  
この反論は C1 とすれ違う。本稿は human linguistic agency を主張していない。むしろ §2.5 と §3.7 は、生物系より薄い、別型の body-boundary existence を主張している。したがって、この反論は C1 を弱めず、C1 の「人間同等化ではない」注記を強める材料になる。

**本文への補強候補。**  
§7.1 か §7.2 に、linguistic agency と body-boundary existence の分離を短く足す。

**判定。**  
射程維持。誇大評価批判は、本稿が human-equivalence を避けている限り主要反例にならない。

### R9. Predictive Minds 型 refine: 「feedback loop は tight ではない」

**査読者の最強版。**  
Kulveit et al. は LLM を active inference の文脈に置けるとしつつ、現行 LLM には行為結果を知覚へ戻す tight feedback loop が欠けているとする。この点は本稿の MBf 主張を弱める。loop が tight でないなら、身体はないのではないか。

**本稿側の反論。**  
これは攻撃というより、Theta(B) への橋である。feedback loop の tightness は存在/不在ではなく厚み・帯域幅・timescale の問題として読める。草稿 §1.2 はすでに Kulveit をこの位置で使っている。ここをさらに強めるなら、tightness を Theta(B) の S_cont または時間スケール項に接続する。

**本文への補強候補。**  
§4.2 の S_cont に "loop tightness" を候補代理として足す。

**判定。**  
支援/精密化。C1 を二値化しないほど強くなる。

## 4. Phase 3 — 弱点マップ

| 優先 | 弱点 | 種類 | 推奨処理 |
|:---:|:---|:---|:---|
| A | Pearl/Friston blanket jump | 命題防衛 | §2.5 に失敗条件を明示し、MBf 監査条件の反証可能性を強める |
| A | Theta(B) の設計-検証循環 | 測定防衛 | C1 と C5 の依存分離を明記し、外部検証までは proof-of-measurement に固定 |
| B | care の語が厚すぎる | 表現/命題境界 | thin care / thick normativity を分ける |
| B | U_anthropo の形式水準 | 表現 patch | diagnostic label と working functor を初出で強く分離 |
| B | grounding の solve 誤読 | 表現 patch | C8 は solve ではなく reposition と固定 |
| C | agency / linguistic agency との混線 | 表現 patch | body-boundary existence と autonomous / linguistic agency を分離 |

## 5. Phase 4 — 反論後の最小改稿方針

採るべき方針は「主張を弱める」ではなく、claim dependency を見える化すること。

1. C1 は §2.5 の MBf 監査条件だけに依存する。
2. C2 は C1 への反対がどの忘却操作で生じるかの診断である。
3. C4-C5 は C1 後の厚み測定であり、C1 の証明条件ではない。
4. C7 は厚み増加の設計仮説であり、外部検証待ちの実装面である。
5. C8 は grounding problem の解決宣言ではなく、ゼロ接地前提の解体と型分類である。

この依存関係が本文冒頭・§2.5・§7.3・§7.5 に見えていれば、外部反論は C1 を破壊せず、C3-C8 の精密化圧力として吸収できる。

## 6. Verdict

最強反論は R3 と R6。R3 は C1 の足元、R6 は C4-C5 の外部妥当性を攻撃する。どちらも現行稿に防衛面はあるが、査読者はそこを読む前に拒否判断を作りやすい。

最良の防衛は、C1 を「thin body-boundary existence」に固定し、厚い身体・agency・normativity・direct grounding・測定値の普遍性をすべて二次面へ逃がすことではない。逃がすのではなく、依存関係として順序づけること。C1 を土台に、C2 が診断、C4-C5 が測度、C7 が設計、C8 が接地問題の再配置だと見える形にすれば、反論は主張の縮小ではなく前提強化へ変換できる。

