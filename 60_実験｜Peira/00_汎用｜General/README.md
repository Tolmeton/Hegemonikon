# 00_汎用｜General — 汎用実験・ベンチマーク

分類不問の実験スクリプト群。PoC、ベンチマーク、単発検証を格納。

## 内容

| ディレクトリ / ファイル | 概要 |
|:------------------------|:-----|
| `benchmarks/` | 性能ベンチマーク |
| `doxa/` | Doxa (信念) 関連の実験 |
| `fep/` | FEP 理論の数値実験 |
| `results_typos_vs_xml/` | Týpos vs XML 形式の比較実験結果 |
| `vertex_claude/` | Vertex Claude API 検証 |
| `xml_snippets/` | XML 断片テスト |
| `ls-test-workspace/` | Language Server テスト用ワークスペース |
| `unleash/` | 制約解放テスト |
| `activation_steering_*.py` | Activation steering (活性化操舵) 実験 |
| `bench_typos_vs_xml.py` | Týpos 対 XML ベンチマーク |
| `cot_threshold_experiment.py` | CoT 閾値実験 |
| `analyze_gain.py` | 情報利得分析 |

## 判定基準

- 特定カテゴリに分類困難 → ここ
- 成功した実験 → 知識に移行 or 専用ディレクトリへ昇格
