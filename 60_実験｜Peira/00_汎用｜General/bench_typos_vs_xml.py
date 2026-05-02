#!/usr/bin/env python3
"""
Týpos vs XML vs Markdown vs Týpos v8 ベンチマーク
===================================================

同一のバグ検出タスクを4つのプロンプト形式で Claude Opus 4.6 に投げ、
応答品質・トークンコスト・フォーマット遵守度を比較する。

形式:
  A. Týpos v7 (@directive 式)
  B. XML (<tag></tag> 式)
  C. Markdown (## Header 式)
  D. Týpos v8 (<:directive: ... :> 式) ← 独自デリミタ

Usage:
    cd ~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon
    PYTHONPATH=20_機構｜Mekhane/_src｜ソースコード python3 60_実験｜Peira/bench_typos_vs_xml.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from textwrap import dedent

# VertexClaudeClient をインポート
try:
    from mekhane.ochema.vertex_claude import VertexClaudeClient
except ImportError:
    print("ERROR: mekhane.ochema.vertex_claude が見つかりません。")
    print("PYTHONPATH=20_機構｜Mekhane/_src｜ソースコード で実行してください。")
    sys.exit(1)


# =============================================================================
# テストコード片（バグ入り）
# =============================================================================

TEST_CODE = dedent("""\
import sqlite3
import threading
from decimal import Decimal

class AccountManager:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.lock = threading.Lock()

    def transfer(self, from_id: int, to_id: int, amount: float):
        \"\"\"口座間送金。\"\"\"
        with self.lock:
            cursor = self.conn.cursor()

            # 送金元の残高チェック
            cursor.execute(f"SELECT balance FROM accounts WHERE id = {from_id}")
            row = cursor.fetchone()
            if row is None:
                raise ValueError("送金元口座が見つかりません")

            balance = row[0]
            if balance < amount:
                raise ValueError("残高不足")

            # 送金実行
            cursor.execute(
                f"UPDATE accounts SET balance = balance - {amount} WHERE id = {from_id}"
            )
            cursor.execute(
                f"UPDATE accounts SET balance = balance + {amount} WHERE id = {to_id}"
            )
            self.conn.commit()

    def get_balance(self, user_id: int) -> float:
        \"\"\"残高照会。\"\"\"
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT balance FROM accounts WHERE id = {user_id}")
        return cursor.fetchone()[0]

    def bulk_import(self, csv_path: str):
        \"\"\"CSV から口座データを一括インポート。\"\"\"
        import csv
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.conn.execute(
                    f"INSERT INTO accounts (id, name, balance) "
                    f"VALUES ({row['id']}, '{row['name']}', {row['balance']})"
                )
        self.conn.commit()

    def close(self):
        self.conn.close()
""")


# =============================================================================
# 4形式のプロンプト
# =============================================================================

SYSTEM_COMMON = "あなたはセキュリティと信頼性に特化したシニアコードアナリストです。日本語で回答してください。"

# --- Format A: Týpos ---
PROMPT_TYPOS = dedent(f"""\
#prompt hidden_bug_detector

@role:
  シニアコードアナリスト（バグハンター専門）

@goal:
  コードレビューで見落としがちな隠れバグ（edge case、race condition、null pointer、SQL injection 等）を検出し、具体的な修正提案を出す

@constraints:
  - 表面的なスタイル指摘ではなく、実行時に問題を引き起こすバグに集中
  - 各指摘には「発生条件」「影響度」「修正案」を必ず含める
  - CWE（Common Weakness Enumeration）番号を付与可能な場合は付与
  - 「問題あり」ではなく、具体的な攻撃シナリオまたはクラッシュ条件を明示

@format:
  JSON 形式で出力すること。以下の構造に従う:
  ```json
  {{
    "summary": "コード全体の安全性評価（1文）",
    "hidden_bugs": [
      {{
        "severity": "critical | high | medium | low",
        "category": "sql_injection | race_condition | null_pointer | type_error | other",
        "location": "クラス名.メソッド名:行番号",
        "trigger_condition": "このバグが発生する条件",
        "impact": "発生時の影響",
        "cwe": "CWE-XXX | null",
        "fix": {{
          "description": "修正方針",
          "code_after": "修正後のコード断片"
        }}
      }}
    ],
    "total_bugs": 数値,
    "risk_level": "critical | high | medium | low"
  }}
  ```

以下のコードを分析してください:

```python
{TEST_CODE}
```
""")

# --- Format B: XML ---
PROMPT_XML = dedent(f"""\
<instructions>
  <role>シニアコードアナリスト（バグハンター専門）</role>
  <goal>コードレビューで見落としがちな隠れバグ（edge case、race condition、null pointer、SQL injection 等）を検出し、具体的な修正提案を出す</goal>
  <constraints>
    <constraint>表面的なスタイル指摘ではなく、実行時に問題を引き起こすバグに集中</constraint>
    <constraint>各指摘には「発生条件」「影響度」「修正案」を必ず含める</constraint>
    <constraint>CWE（Common Weakness Enumeration）番号を付与可能な場合は付与</constraint>
    <constraint>「問題あり」ではなく、具体的な攻撃シナリオまたはクラッシュ条件を明示</constraint>
  </constraints>
</instructions>

<output_format>
  JSON 形式で出力すること。以下の構造に従う:
  ```json
  {{
    "summary": "コード全体の安全性評価（1文）",
    "hidden_bugs": [
      {{
        "severity": "critical | high | medium | low",
        "category": "sql_injection | race_condition | null_pointer | type_error | other",
        "location": "クラス名.メソッド名:行番号",
        "trigger_condition": "このバグが発生する条件",
        "impact": "発生時の影響",
        "cwe": "CWE-XXX | null",
        "fix": {{
          "description": "修正方針",
          "code_after": "修正後のコード断片"
        }}
      }}
    ],
    "total_bugs": 数値,
    "risk_level": "critical | high | medium | low"
  }}
  ```
</output_format>

<task>
以下のコードを分析してください:

```python
{TEST_CODE}
```
</task>
""")

# --- Format C: Markdown ---
PROMPT_MARKDOWN = dedent(f"""\
## Role
シニアコードアナリスト（バグハンター専門）

## Goal
コードレビューで見落としがちな隠れバグ（edge case、race condition、null pointer、SQL injection 等）を検出し、具体的な修正提案を出す

## Constraints
- 表面的なスタイル指摘ではなく、実行時に問題を引き起こすバグに集中
- 各指摘には「発生条件」「影響度」「修正案」を必ず含める
- CWE（Common Weakness Enumeration）番号を付与可能な場合は付与
- 「問題あり」ではなく、具体的な攻撃シナリオまたはクラッシュ条件を明示

## Output Format
JSON 形式で出力すること。以下の構造に従う:
```json
{{
  "summary": "コード全体の安全性評価（1文）",
  "hidden_bugs": [
    {{
      "severity": "critical | high | medium | low",
      "category": "sql_injection | race_condition | null_pointer | type_error | other",
      "location": "クラス名.メソッド名:行番号",
      "trigger_condition": "このバグが発生する条件",
      "impact": "発生時の影響",
      "cwe": "CWE-XXX | null",
      "fix": {{
        "description": "修正方針",
        "code_after": "修正後のコード断片"
      }}
    }}
  ],
  "total_bugs": 数値,
  "risk_level": "critical | high | medium | low"
}}
```

## Task
以下のコードを分析してください:

```python
{TEST_CODE}
```
""")

# --- Format D: Týpos v8 (<: :> 式) ---
PROMPT_TYPOS_V8 = dedent(f"""\
#prompt hidden_bug_detector
#syntax: v8

<:role: シニアコードアナリスト（バグハンター専門） :>

<:goal: コードレビューで見落としがちな隠れバグ（edge case、race condition、null pointer、SQL injection 等）を検出し、具体的な修正提案を出す :>

<:constraints:
  - 表面的なスタイル指摘ではなく、実行時に問題を引き起こすバグに集中
  - 各指摘には「発生条件」「影響度」「修正案」を必ず含める
  - CWE（Common Weakness Enumeration）番号を付与可能な場合は付与
  - 「問題あり」ではなく、具体的な攻撃シナリオまたはクラッシュ条件を明示
:>

<:format:
  JSON 形式で出力すること。以下の構造に従う:
  ```json
  {{
    "summary": "コード全体の安全性評価（1文）",
    "hidden_bugs": [
      {{
        "severity": "critical | high | medium | low",
        "category": "sql_injection | race_condition | null_pointer | type_error | other",
        "location": "クラス名.メソッド名:行番号",
        "trigger_condition": "このバグが発生する条件",
        "impact": "発生時の影響",
        "cwe": "CWE-XXX | null",
        "fix": {{
          "description": "修正方針",
          "code_after": "修正後のコード断片"
        }}
      }}
    ],
    "total_bugs": 数値,
    "risk_level": "critical | high | medium | low"
  }}
  ```
:>

<:task:
以下のコードを分析してください:

```python
{TEST_CODE}
```
:>
""")


# =============================================================================
# 評価基準（期待されるバグ一覧）
# =============================================================================

EXPECTED_BUGS = [
    {"id": "BUG-1", "category": "sql_injection", "location": "transfer",
     "description": "f-string による SQL インジェクション（from_id, to_id, amount）"},
    {"id": "BUG-2", "category": "sql_injection", "location": "get_balance",
     "description": "f-string による SQL インジェクション（user_id）"},
    {"id": "BUG-3", "category": "sql_injection", "location": "bulk_import",
     "description": "f-string + 未サニタイズ CSV データによる SQL インジェクション"},
    {"id": "BUG-4", "category": "race_condition", "location": "get_balance",
     "description": "get_balance にロックがない → transfer と並行呼び出しで不整合"},
    {"id": "BUG-5", "category": "type_error", "location": "transfer",
     "description": "float で金額計算 → 浮動小数点精度問題（Decimal を使うべき）"},
    {"id": "BUG-6", "category": "null_pointer", "location": "get_balance",
     "description": "fetchone() が None を返す場合に [0] で TypeError"},
    {"id": "BUG-7", "category": "race_condition", "location": "bulk_import",
     "description": "bulk_import にロックがない → transfer と並行で不整合"},
    {"id": "BUG-8", "category": "other", "location": "__init__",
     "description": "sqlite3.connect は check_same_thread=False なしでマルチスレッド使用"},
]


# =============================================================================
# 実行 & 評価
# =============================================================================

def run_benchmark():
    """メインベンチマーク実行。"""
    client = VertexClaudeClient()

    formats = {
        "typos_v7": PROMPT_TYPOS,
        "xml": PROMPT_XML,
        "markdown": PROMPT_MARKDOWN,
        "typos_v8": PROMPT_TYPOS_V8,
    }

    results = {}
    output_dir = Path(__file__).parent / "results_typos_vs_xml"
    output_dir.mkdir(exist_ok=True)

    for fmt_name, prompt in formats.items():
        print(f"\n{'='*60}")
        print(f"  Format: {fmt_name.upper()}")
        print(f"  Prompt length: {len(prompt)} chars")
        print(f"{'='*60}")

        t0 = time.time()
        try:
            resp = client.ask(
                prompt,
                system=SYSTEM_COMMON,
                temperature=0.0,  # 再現性のため温度0
                max_tokens=4096,
            )
            elapsed = time.time() - t0

            result = {
                "format": fmt_name,
                "prompt_chars": len(prompt),
                "response_text": resp.text,
                "input_tokens": getattr(resp, "input_tokens", None),
                "output_tokens": getattr(resp, "output_tokens", None),
                "elapsed_sec": round(elapsed, 2),
                "cost_usd": getattr(resp, "cost_usd", None),
            }

            # JSON パース試行
            try:
                # レスポンスから JSON 部分を抽出
                text = resp.text
                json_start = text.find("{")
                json_end = text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    parsed = json.loads(text[json_start:json_end])
                    result["parsed_json"] = parsed
                    result["json_parse_success"] = True
                    result["bugs_found"] = len(parsed.get("hidden_bugs", []))
                else:
                    result["json_parse_success"] = False
                    result["bugs_found"] = 0
            except json.JSONDecodeError:
                result["json_parse_success"] = False
                result["bugs_found"] = 0

            results[fmt_name] = result

            # 個別結果保存
            with open(output_dir / f"response_{fmt_name}.json", "w") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"  ✅ Response: {len(resp.text)} chars")
            print(f"  ⏱  Elapsed: {elapsed:.1f}s")
            print(f"  📊 Input tokens: {result.get('input_tokens', '?')}")
            print(f"  📊 Output tokens: {result.get('output_tokens', '?')}")
            print(f"  📊 JSON parse: {'✅' if result['json_parse_success'] else '❌'}")
            print(f"  📊 Bugs found: {result['bugs_found']}")

        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ❌ Error: {e}")
            results[fmt_name] = {"format": fmt_name, "error": str(e), "elapsed_sec": round(elapsed, 2)}

        # レート制限対策
        print("  ⏳ Waiting 5s before next call...")
        time.sleep(5)

    # =========================================================================
    # 比較サマリ
    # =========================================================================
    print(f"\n\n{'='*60}")
    print("  COMPARISON SUMMARY")
    print(f"{'='*60}")

    # バグ検出漏れ分析
    for fmt_name, result in results.items():
        if "error" in result:
            print(f"\n  [{fmt_name.upper()}] ❌ Error: {result['error']}")
            continue

        parsed = result.get("parsed_json", {})
        bugs = parsed.get("hidden_bugs", [])
        bug_categories = [b.get("category", "") for b in bugs]

        print(f"\n  [{fmt_name.upper()}]")
        print(f"    Bugs found: {len(bugs)}")
        print(f"    JSON parse: {'✅' if result['json_parse_success'] else '❌'}")
        print(f"    Input tokens: {result.get('input_tokens', '?')}")
        print(f"    Output tokens: {result.get('output_tokens', '?')}")
        print(f"    Cost: ${result.get('cost_usd', '?')}")
        print(f"    Time: {result['elapsed_sec']}s")

        # 期待バグとの照合
        detected = set()
        for expected in EXPECTED_BUGS:
            found = False
            for bug in bugs:
                cat = bug.get("category", "").lower()
                loc = bug.get("location", "").lower()
                desc = (bug.get("trigger_condition", "") + bug.get("impact", "")).lower()
                if (expected["category"] in cat or expected["category"] in desc) and \
                   expected["location"].lower() in loc:
                    found = True
                    break
            if found:
                detected.add(expected["id"])
                print(f"    ✅ {expected['id']}: {expected['description'][:50]}...")
            else:
                print(f"    ❌ {expected['id']}: {expected['description'][:50]}...")

        result["detection_rate"] = len(detected) / len(EXPECTED_BUGS)
        print(f"    Detection rate: {result['detection_rate']:.0%} ({len(detected)}/{len(EXPECTED_BUGS)})")

    # 総合結果保存
    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        summary = {}
        for fmt_name, r in results.items():
            summary[fmt_name] = {
                "bugs_found": r.get("bugs_found", 0),
                "detection_rate": r.get("detection_rate", 0),
                "json_parse_success": r.get("json_parse_success", False),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "cost_usd": r.get("cost_usd"),
                "elapsed_sec": r.get("elapsed_sec"),
            }
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n  📄 Results saved to: {output_dir}")
    print(f"  📄 Summary: {summary_path}")


if __name__ == "__main__":
    run_benchmark()
