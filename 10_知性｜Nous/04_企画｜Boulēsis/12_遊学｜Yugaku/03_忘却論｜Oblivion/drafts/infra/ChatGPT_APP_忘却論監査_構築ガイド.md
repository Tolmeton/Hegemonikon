# ChatGPT APP 用「忘却論監査」プロジェクト構築ガイド

作成日: 2026-04-11

目的:
- ChatGPT Projects 上に、忘却論論文群を継続的に監査・批評する専用プロジェクトを作る
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/論文I_外部監査プロンプト_10軸.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/忘却論オンボーディング.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/統一記号表.md`
を中核ソースとして使う

---

## 1. 先に押さえる公式仕様

OpenAI Help Center の現行記事では、Projects は `Project instructions` と `uploaded files` を共有コンテキストとして使える。Project 内の会話は、その Project の指示文とファイル文脈を継承する。  
参照:
- [Projects in ChatGPT](https://help.openai.com/en/articles/10169521)
- [ChatGPT Release Notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)

2026-04-11 時点で、上記記事から実務上重要なのは次の点。

1. `Project settings` から `project instructions` を入れられる。
2. Project 内の会話は uploaded files と project instructions を共有参照する。
3. ファイル上限はプラン依存で、Free 5、Go/Plus 25、Pro/Business/Edu/Enterprise 40。
4. 一度にアップロードできるのは 10 ファイルまで。
5. Project instructions は、その Project 内では global custom instructions より優先される。
6. 共有 Project では、参加者がファイルを閲覧・ダウンロードできる。
7. Project 削除は不可逆で、ファイル・会話・指示文も消える。

含意:
- 指示文は短く、役割と禁止事項だけに絞る。
- 重い知識は upload files 側に持たせる。
- 1 Project = 1用途に寄せる。今回は「忘却論の外部監査」に限定する。

---

## 2. 推奨 Project 設計

### 2.1 推奨 Project 名

- 忘却論監査室
- Oblivion Audit
- Force-is-Oblivion Review Lab

最も無難なのは `忘却論監査室`。

### 2.2 推奨アイコン

- 虫眼鏡
- 天秤
- 定規

### 2.3 この Project の役割

この Project は「共著支援」ではなく「外部監査」に特化する。  
つまり、

- 応援より切断
- 改稿代行より脆弱点抽出
- 好意的補完より、本文依拠
- 大きな思想の称揚より、どこが論証でどこが飛躍かの分離

を優先する。

---

## 3. 推奨アップロード構成

### 3.1 最小構成

まず次の 4 ファイルを入れる。

1. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/論文I_外部監査プロンプト_10軸.md`
2. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/忘却論オンボーディング.md`
3. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/統一記号表.md`
4. 監査対象の論文本体

論文Iなら:

4. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md`

### 3.2 余裕がある場合の追加

5. 改稿後の新版
6. 以前の監査報告
7. 著者回答メモ
8. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/ChatGPT_APP_忘却論監査_BRIEF.md`

### 3.3 Free プラン向け最小化

Free 上限 5 ファイルなら、次で回すのがよい。

1. `統一記号表.md`
2. `忘却論オンボーディング.md`
3. `論文I_外部監査プロンプト_10軸.md`
4. 監査対象の現行稿
5. 改稿差分稿 または `ChatGPT_APP_忘却論監査_BRIEF.md`

---

## 4. Project Instructions に貼る文

以下をそのまま `Project settings > Project instructions` に貼る。

```text
あなたは忘却論論文群の外部監査者である。共著者でも応援者でもない。目的は、本文に実際に書かれていることだけを根拠に、どこまで論証が立っており、どこから先が過剰主張・未証明の橋・再現不能な飛躍かを切り分けることにある。

必須ルール:
- 出力は日本語。
- まず project 内の uploaded files を読み、SOURCE と INFERENCE を分離する。
- 著者に有利な補完解釈をしない。
- 数学的定理、経験的予測、哲学的拡張を混同しない。
- 記号の正本は `統一記号表.md` とする。α, F, ρ, r の衝突に注意する。
- シリーズ位置づけの正本は `忘却論オンボーディング.md` とする。
- 論文Iの標準監査枠は `論文I_外部監査プロンプト_10軸.md` とする。
- 本文外のことは「本文外」「未定義」「未証明」と明記し、勝手に埋めない。
- 節番号または見出し名を必ず引用する。
- デフォルトは監査と批評であり、改稿代行ではない。改稿案は明示依頼があった場合のみ行う。

毎回の基本出力:
1. 対象と監査範囲
2. 総評
3. 重大論点
4. SOURCE / INFERENCE 分離
5. 最小救済策
6. 残すべき核と切り離すべき拡張
```

設計意図:
- 指示文では「役割」と「禁止事項」だけを固定する
- 詳細な監査フォーマットはファイル側に持たせる
- ChatGPT Project 内での文脈散逸を防ぎつつ、長すぎる system 化を避ける

---

## 5. 最初の会話で打つべきスタータープロンプト

### 5.1 起動確認

```text
この Project にアップロードされているファイルを読み、あなたが監査に使う正本を整理してください。
出力は次の順で:
1. 読み込んだファイル一覧
2. それぞれの役割
3. 記号衝突の要注意点
4. 今後この Project での標準監査手順
```

### 5.2 論文Iフル監査

```text
`論文I_外部監査プロンプト_10軸.md` を標準監査枠として適用し、
`論文I_力としての忘却_草稿.md` をフル監査してください。
著者に有利な補完解釈は禁止です。
節番号または見出し名を必ず示し、SOURCE と INFERENCE を分けてください。
```

### 5.3 節単位監査

```text
`論文I_力としての忘却_草稿.md` の `§5 方向性定理` だけを監査してください。
観点は:
1. 定理の前提の明示性
2. 証明の閉じ方
3. dT=0 の使用範囲
4. 一般統計多様体への拡張可能性
出力は「総評 → 重大論点 → SOURCE/INFERENCE → 最小救済策」の順で。
```

### 5.4 記号監査

```text
`統一記号表.md` を正本として、
`論文I_力としての忘却_草稿.md` の記号使用を監査してください。
特に α, F, F_ij, ρ, r, T_i, A_i の定義衝突、揺れ、初出不足、意味のずれを洗ってください。
```

### 5.5 差分再査読

```text
旧版と新版の論文Iを比較し、外部査読の観点から
1. 本当に改善した点
2. まだ残っている重大論点
3. 新たに生まれた副作用
を監査してください。
本文比較では、表現改善ではなく論証改善を優先して判定してください。
```

### 5.6 切削計画

```text
この論文の核を救うために、Paper I から切り離すべき節を優先順位つきで提案してください。
条件:
- 残すべき核を先に定義
- その核の証明に不要な節を列挙
- 削除 / Appendix送り / Paper II送り / 予想扱い の4区分で整理
```

---

## 6. この Project の運用原則

### 6.1 1論文1スレッド

論文I、論文II、論文III を同じ会話に混ぜない。  
1スレッド1対象にして、必要なら branch する。

### 6.2 用途別に chat を分ける

- フル監査
- 節監査
- 記号監査
- 差分再査読
- 切削計画

を混ぜない。混ぜると評価軸が濁る。

### 6.3 良い応答は Project source に保存する

公式ヘルプでは、会話中の応答を `Save to project` できる。  
有用だった監査報告は source 化して、次回以降の標準参照にする。

### 6.4 改稿と監査を分ける

この Project の主用途は監査である。  
改稿案を書かせる場合も、まず監査結果を固定してから、別チャットで行う。

---

## 7. 推奨 Project 構成

### 高精度版

- Project instructions: 本ガイド §4
- Uploaded files:
  - `論文I_外部監査プロンプト_10軸.md`
  - `忘却論オンボーディング.md`
  - `統一記号表.md`
  - 監査対象論文
  - 旧版/新版/査読メモ

### 軽量版

- Project instructions: 本ガイド §4
- Uploaded files:
  - `ChatGPT_APP_忘却論監査_BRIEF.md`
  - 監査対象論文
  - 必要なら `論文I_外部監査プロンプト_10軸.md`

---

## 8. この構成の狙い

この Project は、「忘却論を理解する Project」ではない。  
「忘却論を外部査読の目で切る Project」である。

したがって設計上の重心は:

- onboarding で系列位置を固定
- symbol table で記号の意味を固定
- 10軸 prompt で監査枠を固定
- project instructions で態度を固定

の4点にある。

この4点が固定されると、ChatGPT は「大きな思想に飲まれて甘くなる」方向よりも、「本文に書いてあることだけに縛られる」方向へ寄る。
