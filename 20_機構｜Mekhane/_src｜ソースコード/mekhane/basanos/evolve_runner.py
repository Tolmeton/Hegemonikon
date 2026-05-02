#!/usr/bin/env python3
# PROOF: [L2/機構] <- mekhane/basanos/evolve_runner.py A0→WF進化→WFTrendAnalyzer+CortexClient
# PURPOSE: WF 進化ループを実行するオーケストレーター (autoresearch パターン)
"""evolve_runner — WF 進化ループのコード実装。

autoresearch パターンの HGK 転用:
  1. WFTrendAnalyzer.scan_workflows() → 弱い WF を検出
  2. WFMutator.build_prompt() → 変異プロンプトを構築
  3. CortexClient.ask() → LLM に変異を依頼
  4. WFTrendAnalyzer.evaluate_mutation() → keep/discard 判定
  5. kept=True → WF ファイルを実際に書き換え (--apply 時のみ)

使い方:
  # Dry run (デフォルト): 変異プロンプトを生成し評価するが書き換えない
  python -m mekhane.basanos.evolve_runner

  # 特定 WF + 特定戦略
  python -m mekhane.basanos.evolve_runner --wf noe.md --strategy clarify

  # 実際に書き換え (apply)
  python -m mekhane.basanos.evolve_runner --apply

  # 弱い WF 上位 N 件に対して実行
  python -m mekhane.basanos.evolve_runner --top 3
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from mekhane.basanos.wf_evolver import (
    WFMutator,
    WFQualityScorer,
    WFTrendAnalyzer,
)
from mekhane.paths import WORKFLOWS_DIR, OUTPUTS_DIR

logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_MAX_TOKENS = 8192
EVOLUTION_LOG = OUTPUTS_DIR / "wf_evolution.jsonl"


# PURPOSE: [L2] CortexClient を遅延生成してインポートエラーを回避
def _get_cortex_client(model: str = DEFAULT_MODEL):
    """CortexClient を遅延ロードする。"""
    from mekhane.ochema.cortex_client import CortexClient
    return CortexClient(model=model)


# PURPOSE: [L2] LLM に WF 変異を依頼し、結果テキストを返す
def mutate_wf(
    wf_content: str,
    strategy: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """LLM に WF の変異を依頼する。

    Args:
        wf_content: 元の WF テキスト
        strategy: 変異戦略名
        model: 使用する LLM モデル
        max_tokens: 最大出力トークン数

    Returns:
        LLM が生成した変異 WF テキスト
    """
    prompt = WFMutator.build_prompt(wf_content, strategy)
    client = _get_cortex_client(model)

    logger.info("Mutating with strategy=%s model=%s", strategy, model)
    response = client.ask(
        message=prompt,
        system_instruction=(
            "あなたは Hegemonikón ワークフローの品質改善専門家です。"
            "指示された改善方針に従い、改善された WF のみを出力してください。"
            "説明は不要です。frontmatter (---) から始めてください。"
        ),
        max_tokens=max_tokens,
        temperature=0.7,
    )

    return response.text


# PURPOSE: [L2] 単一 WF に対して全戦略で進化ループを回す
def evolve_one(
    wf_path: Path,
    analyzer: WFTrendAnalyzer,
    strategies: Optional[list[str]] = None,
    model: str = DEFAULT_MODEL,
    apply: bool = False,
    log_file: Path = EVOLUTION_LOG,
) -> list[dict]:
    """1つの WF に対して進化ループを実行する。

    Args:
        wf_path: WF ファイルのパス
        analyzer: WFTrendAnalyzer インスタンス
        strategies: 使用する変異戦略 (None=全戦略)
        model: LLM モデル
        apply: True なら kept=True の変異を実際に書き込む
        log_file: 進化ログファイル

    Returns:
        各変異の結果リスト
    """
    wf_content = wf_path.read_text(encoding="utf-8")
    try:
        rel_path = str(wf_path.relative_to(analyzer.wf_dir))
    except ValueError:
        rel_path = wf_path.name

    # 1. evolve() でプロンプトを生成
    results = analyzer.evolve(
        wf_path=rel_path,
        wf_content=wf_content,
        mutation_types=strategies,
        log_file=log_file,
    )

    evaluated = []
    best_result = None
    best_score = analyzer.scorer.score(wf_content)

    for result in results:
        strategy = result["mutation_type"]
        logger.info(
            "  [%s] original=%.3f → mutating...",
            strategy, result["original_score"],
        )

        try:
            # 2. LLM に変異を依頼
            mutated_text = mutate_wf(wf_content, strategy, model=model)

            # 3. 評価
            ev = analyzer.evaluate_mutation(
                result, mutated_text, log_file=log_file,
            )
            evaluated.append(ev)

            status = "✓ KEPT" if ev["kept"] else "✗ DISCARD"
            logger.info(
                "  [%s] mutated=%.3f %s (Δ=%+.3f)",
                strategy,
                ev["mutated_score"],
                status,
                ev["mutated_score"] - ev["original_score"],
            )

            # 最良の変異を追跡
            if ev["kept"] and ev["mutated_score"] > best_score:
                best_score = ev["mutated_score"]
                best_result = ev

        except Exception as e:  # noqa: BLE001
            logger.error("  [%s] FAILED: %s", strategy, e)
            result["error"] = str(e)
            evaluated.append(result)

    # 4. apply モードなら最良の変異を書き込む
    if apply and best_result and best_result.get("mutated_content"):
        backup = wf_path.with_suffix(".md.bak")
        backup.write_text(wf_content, encoding="utf-8")
        wf_path.write_text(best_result["mutated_content"], encoding="utf-8")
        logger.info(
            "  ✓ APPLIED best mutation (strategy=%s, score=%.3f → %.3f)",
            best_result["mutation_type"],
            best_result["original_score"],
            best_result["mutated_score"],
        )
        logger.info("  Backup saved to %s", backup)

    return evaluated


# PURPOSE: [L2] メインのオーケストレーション — scan → weak → evolve
def run(
    wf_dir: Path = WORKFLOWS_DIR,
    top_n: int = 3,
    strategies: Optional[list[str]] = None,
    model: str = DEFAULT_MODEL,
    apply: bool = False,
    target_wf: Optional[str] = None,
) -> dict:
    """WF 進化ループのメインエントリポイント。

    Args:
        wf_dir: WF ディレクトリ
        top_n: 弱い WF の上位 N 件を対象
        strategies: 使用する変異戦略 (None=全戦略)
        model: LLM モデル
        apply: True なら kept=True の変異を書き込む
        target_wf: 特定 WF ファイル名 (指定時は top_n 無視)

    Returns:
        実行結果のサマリ dict
    """
    reviews_dir = OUTPUTS_DIR / "wf_reviews"
    log_file = OUTPUTS_DIR / "wf_evolution.jsonl"

    analyzer = WFTrendAnalyzer(wf_dir=wf_dir, reviews_dir=reviews_dir)

    # ターゲット選定
    if target_wf:
        targets = [wf_dir / target_wf]
        if not targets[0].exists():
            # サブディレクトリも探索
            found = list(wf_dir.rglob(target_wf))
            if not found:
                logger.error("WF not found: %s", target_wf)
                return {"error": f"WF not found: {target_wf}"}
            targets = found[:1]
    else:
        # scan → weak の順で弱い WF を検出
        logger.info("Scanning %s for weak WFs...", wf_dir)
        scan = analyzer.scan_workflows()  # uses self.wf_dir
        if not scan:
            logger.info("No WFs found in %s", wf_dir)
            return {"targets": 0, "results": []}

        # スコア昇順でソート → 弱い WF 上位 N 件
        # scan keys are relative paths from wf_dir
        sorted_wfs = sorted(scan.items(), key=lambda kv: kv[1])
        targets = [wf_dir / rel_path for rel_path, _ in sorted_wfs[:top_n]]

        logger.info(
            "Found %d WFs, targeting %d weakest:",
            len(scan), len(targets),
        )
        for t in targets:
            rel = str(t.relative_to(wf_dir)) if t.is_relative_to(wf_dir) else t.name
            score = scan.get(rel, 0.0)
            logger.info("  %.3f  %s", score, t.name)

    # 進化ループ
    all_results = []
    for target in targets:
        logger.info("\n━━━ Evolving: %s ━━━", target.name)
        results = evolve_one(
            wf_path=target,
            analyzer=analyzer,
            strategies=strategies,
            model=model,
            apply=apply,
            log_file=log_file,
        )
        all_results.extend(results)

    # サマリ
    kept = sum(1 for r in all_results if r.get("kept"))
    discarded = sum(1 for r in all_results if r.get("kept") is False)
    errors = sum(1 for r in all_results if r.get("error"))

    summary = {
        "timestamp": datetime.now().isoformat(),
        "targets": len(targets),
        "mutations_total": len(all_results),
        "kept": kept,
        "discarded": discarded,
        "errors": errors,
        "applied": apply,
        "model": model,
    }

    logger.info("\n━━━ Evolution Summary ━━━")
    logger.info("  Targets: %d WFs", summary["targets"])
    logger.info("  Mutations: %d total", summary["mutations_total"])
    logger.info("  Kept: %d / Discarded: %d / Errors: %d", kept, discarded, errors)
    logger.info("  Applied: %s", apply)

    return summary


# PURPOSE: [L2] CLI エントリポイント
def main():
    parser = argparse.ArgumentParser(
        description="WF Evolution Runner — autoresearch-style WF improvement",
    )
    parser.add_argument(
        "--wf", type=str, default=None,
        help="Target a specific WF file (e.g., noe.md)",
    )
    parser.add_argument(
        "--strategy", type=str, default=None,
        help="Use a specific mutation strategy (clarify, restructure, densify, decompose, strengthen)",
    )
    parser.add_argument(
        "--top", type=int, default=3,
        help="Number of weakest WFs to target (default: 3)",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help=f"LLM model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually apply best mutations to WF files (default: dry run)",
    )
    parser.add_argument(
        "--wf-dir", type=str, default=None,
        help=f"WF directory to scan (default: {WORKFLOWS_DIR})",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # ログ設定
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    strategies = [args.strategy] if args.strategy else None
    wf_dir = Path(args.wf_dir) if args.wf_dir else WORKFLOWS_DIR

    summary = run(
        wf_dir=wf_dir,
        top_n=args.top,
        strategies=strategies,
        model=args.model,
        apply=args.apply,
        target_wf=args.wf,
    )

    # JSON サマリを stdout に出力
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
