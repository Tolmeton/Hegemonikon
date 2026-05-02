# arXiv 整合修正チェックリスト

**作成日:** 2026-04-11  
**基準レポート:** `/home/makaron8426/.copilot/session-state/d9d22e43-f432-4a82-8727-720304f1bba8/files/consistency-check-report.md`  
**状態値:** `解消 / 注記で吸収 / 次版へ明示繰越`

---

## 投稿前必須 (🔴)

| ID | 項目 | 状態 | 処理 |
|:---|:---|:---:|:---|
| 1 | I-D1 / バンドル記号 F | 解消 | Paper XI の prompt 関手表記を `P / P₁ / P₂ / P₃` に統一し、`統一記号表.md` に反映 |
| 2 | II-D1 / cell convention | 解消 | Paper II に `d_dR / d_hier` 注記、Paper III に bridge note を追加 |
| 3 | XI→III 参照 | 解消 | Paper XI 依存関係と §9.6 に Paper III の Z₂ / α-セクター参照を追加 |
| 4 | IV-D2 / 参考文献 TODO | 解消 | Yue / Dong / Yao / Cui を正式書誌 + arXiv ID に置換 |
| 5 | IV-D1 / ヘッダー v3.8 | 解消 | Header / footer を `v3.8 (2026-04-09)` に統一 |

## 投稿前推奨 (🟡)

| ID | 項目 | 状態 | 処理 |
|:---|:---|:---:|:---|
| 6 | I-O1 / II-O1 / III-O1 / CPS0' | 解消 | I・II・III に共通脚注を追加し、`統一記号表.md` でも再定義 |
| 7 | I-D2 / 曲率公式の完全形 | 解消 | Paper I §3.3 に一般形と指数族簡約の boxed note を追加 |
| 8 | I-D3 / N⊣U 記法統一 | 解消 | Paper XI で随伴をローカルに `N ⊣ U` と定義し、誤帰属と `U⊣N` を除去 |
| 9 | I-O2 / 擬人化表現の修正 | 注記で吸収 | Paper I §1 / §5 / §9 で `U を通じて知覚者が情報を失う` に寄せた |
| 10 | II-D2 / blanket 仮定の注記 | 注記で吸収 | Paper II §3.7 に「指数族では定理化、一般には leak あり」の注記を追加 |

## 次版で対応可 (⚪)

| ID | 項目 | 状態 | 処理 |
|:---|:---|:---:|:---|
| 11 | I-O3 / CAN→MUST | 注記で吸収 | Paper I §9 に Paper V への前方参照を追加 |
| 12 | I-O4 / IV-O1 / スケーリング指数 | 注記で吸収 | Paper I §9 と Paper IV 結論で Paper V の `n^{-1}` 精密化へ前方参照 |
| 13 | II-O2 / Face Lemma スコープ | 注記で吸収 | Paper II §3.4 に `F×` 精密化への前方参照を追加 |
| 14 | II-O3 / CPS3 の地位 | 注記で吸収 | Paper II §3.2 に VIII / IX での再解釈への言及を追加 |
| 15 | II-O4 / 意識定義の精密化 | 注記で吸収 | Paper II §6.2 に `F≠0 かつ α<0` への前方参照を追加 |
| 16 | III-D1 / α≤0 エントロピー不可能性 | 注記で吸収 | Paper III §5.3.4 後に Perrone エントロピー不可能性の範囲注を追加 |
| 17 | III-O3 / α-Δd 対応の近似性 | 注記で吸収 | Paper III 冒頭 bridge note で双対平坦 / holonomy 補正の射程を明示 |
| 18 | IV-O2 / K>0 の統一導出 | 注記で吸収 | Paper IV 結論で Paper V による単一原理からの再導出を前方参照 |

---

## 対象ファイル

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/統一記号表.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文II_相補性は忘却である_草稿.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文III_Markov圏の向こう側_草稿.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文IV_なぜ効果量は小さいか_草稿.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文XI_プロンプトは忘却である_草稿.md`
