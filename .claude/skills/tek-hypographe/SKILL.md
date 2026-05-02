---
name: tek-hypographe
description: 自然言語プロンプトを Typos v8.4 に構造化する軽量前処理器 (論文XI ベース)。/tek.hypographē または /tek.hypographe で呼出。
triggers:
  - /tek.hypographe
  - /tek.hypographē
---

# /tek.hypographē — Prompt Forging Engine

自然言語プロンプトを Typos v8.4 構造化プロンプトに昇華する。論文XI「プロンプトは忘却である」の知見に基づく。

## 使い方

```
/tek.hypographe "自然言語プロンプト"
/tek.hypographe "プロンプト" -t opus46
/tek.hypographe "プロンプト" -t gpt54 -f "忘却させたいこと"
```

## 引数

| 引数 | 説明 | デフォルト |
|------|------|------------|
| 第1引数 (必須) | 自然言語プロンプト | - |
| `-t`, `--target` | opus46 / gpt54 / generic | generic |
| `-f`, `--forget` | π_low ヒント (排除したい領域) | (なし) |

## 例

```bash
# 基本
/tek.hypographe "このリポジトリのテスト網羅率を上げたい"

# Codex 向け
/tek.hypographe "JSONをCSVに変換するスクリプト" -t gpt54

# Claude 向け + 忘却指定
/tek.hypographe "認証フローを実装" -t opus46 -f "セキュリティは別チームが担当"
```

## 出力

Typos v8.4 形式のプロンプトが stdout に出力される。

## 実行方法

このスキルは Gemini CLI を使用する。以下のコマンドで実行:

```bash
python3 .claude/skills/tek-hypographe/forge.py "プロンプト" -t TARGET -f "FORGET"
```
