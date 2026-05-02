#!/usr/bin/env python3
"""ROM から Doxa 候補を採掘する CLI。"""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter, defaultdict
from itertools import combinations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


# PURPOSE: HGK ルートを自動検出する
def _detect_hgk_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "00_核心｜Kernel").is_dir():
            return parent
    raise RuntimeError("HGK root を検出できませんでした。")


HGK_ROOT = _detect_hgk_root()
ROM_DIR = HGK_ROOT / "30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom"
DEFAULT_OUTPUT_DIR = HGK_ROOT / "30_記憶｜Mneme/00_信念｜Beliefs/_project"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
CONTENT_BLOCK_RE = re.compile(r"<:content(?:\s+[^\n>]*?)?:(.*?)/content:>", re.DOTALL)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}|[一-龠々ぁ-んァ-ヶー]{2,}")

JAPANESE_STOPWORDS = {
    "は", "の", "が", "を", "に", "で", "と", "も", "た", "だ",
    "する", "ある", "なる", "いる", "れる", "られる", "ない",
    "この", "その",
}

GENERIC_TERMS = {
    "decision", "discovery", "rule", "fact", "content", "summary",
    "決定", "判断", "理由", "根拠", "方針", "対象", "追加", "修正", "実装",
    "設計", "検証", "結果", "構造", "以下", "今回", "次回", "現在",
    "rom", "hgk", "source", "session", "project", "content",
    "phase", "api", "paper", "file", "files", "test", "tests",
}

DOMAIN_KEYWORDS = {
    "cognition": {
        "belief", "confidence", "memory", "source", "taint", "hallucination",
        "認知", "信念", "確信", "記憶", "違和感", "観測", "prior", "探索",
    },
    "architecture": {
        "architecture", "schema", "layer", "責務", "設計", "構造", "階層",
        "統合", "graph", "ssot", "adjoint", "index",
    },
    "process": {
        "process", "workflow", "phase", "review", "loop", "手順", "運用",
        "反復", "移行", "検証", "テスト", "レビュー", "方針", "mvp",
    },
    "tool-usage": {
        "tool", "script", "cli", "mcp", "api", "daemon", "systemd", "service",
        "pytest", "import", "settings", "python", "server", "timeout",
        "ツール", "コマンド", "環境変数", "ブリッジ",
    },
    "philosophy": {
        "axiom", "theorem", "fep", "epistemic", "philosophy", "公理", "定理",
        "理論", "本質", "原理", "哲学", "主定理", "存在",
    },
    "writing": {
        "essay", "draft", "writer", "writing", "source-anchor", "本文", "長編",
        "ノート", "表現", "執筆", "節", "章", "文体", "callout",
    },
}

DOMAIN_ORDER = [
    "tool-usage",
    "architecture",
    "process",
    "cognition",
    "philosophy",
    "writing",
]


@dataclass
class DecisionRecord:
    """ROM から抽出した DECISION 断片。"""

    file_path: Path
    file_stem: str
    decision_id: str | None
    summary: str
    rationale: str
    terms: set[str]

    @property
    def evidence_text(self) -> str:
        if self.rationale:
            return f"{self.summary}\n{self.rationale}"
        return self.summary


@dataclass
class DoxaCandidate:
    """生成された Doxa 候補。"""

    belief_id: str
    domain: str
    trigger: str
    action: str
    evidence_count: int
    theme_text: str
    evidence_lines: list[str]


# PURPOSE: frontmatter を除去して本文を返す
def _strip_frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return text
    return text[match.end():]


# PURPOSE: DECISION ヘッダ/本文から余計な装飾を剥ぐ
def _clean_line(line: str) -> str:
    cleaned = line.rstrip()
    cleaned = re.sub(r"^\s*>+\s*", "", cleaned)
    cleaned = re.sub(r"^\s*[-*]\s*", "", cleaned)
    cleaned = re.sub(r"^\s*\d+\.\s*", "", cleaned)
    cleaned = cleaned.replace("**", "")
    cleaned = cleaned.replace("```typos", "")
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.replace("<:highlight:>", "")
    cleaned = cleaned.replace("/highlight:>", "")
    cleaned = re.sub(r"^\s*<:highlight:\s*", "", cleaned)
    cleaned = re.sub(r"\s*:>\s*$", "", cleaned)
    return cleaned.strip()


# PURPOSE: DECISION の開始/終了を切る境界行か判定
def _is_boundary_line(line: str) -> bool:
    stripped = line.strip()
    if "[DECISION" in stripped:
        return True
    if re.search(r"\[(DISCOVERY|RULE|FACT|CONTEXT|DEF)\]", stripped):
        return True
    if stripped.startswith("## "):
        return True
    if stripped.startswith("---"):
        return True
    return False


# PURPOSE: ヘッダ行から decision_id と summary を抽出
def _parse_decision_header(header_line: str) -> tuple[str | None, str]:
    cleaned = _clean_line(header_line)
    match = re.search(r"\[DECISION(?:\s+([^\]]+))?\]\s*(.*)", cleaned)
    if not match:
        return None, cleaned

    explicit_id = (match.group(1) or "").strip() or None
    remainder = match.group(2).strip()
    if explicit_id:
        return explicit_id, remainder

    implicit = re.match(r"([A-Z][A-Z0-9_-]*[-_][A-Z0-9_-]+)\s+(.*)", remainder)
    if implicit:
        return implicit.group(1), implicit.group(2).strip()

    return None, remainder


# PURPOSE: DECISION 本文の行を整える
def _clean_rationale_lines(lines: Iterable[str]) -> list[str]:
    cleaned_lines: list[str] = []
    for line in lines:
        cleaned = _clean_line(line)
        if cleaned == "":
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        cleaned_lines.append(cleaned)
    while cleaned_lines and cleaned_lines[0] == "":
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()
    return cleaned_lines


# PURPOSE: 日本語/英語混在テキストから粗い語幹集合を作る
def _extract_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for raw_token in TOKEN_RE.findall(text):
        token = raw_token.strip("._- ").lower()
        if not token or token in GENERIC_TERMS:
            continue

        if re.fullmatch(r"[a-z0-9_-]+", token):
            token = re.sub(r"(ing|ed|es|s)$", "", token)
        else:
            for stopword in JAPANESE_STOPWORDS:
                if token.endswith(stopword) and len(token) - len(stopword) >= 2:
                    token = token[: -len(stopword)]
                if token.startswith(stopword) and len(token) - len(stopword) >= 2:
                    token = token[len(stopword):]

        token = token.strip("._- ")
        if len(token) < 2 or token in JAPANESE_STOPWORDS or token in GENERIC_TERMS:
            continue
        terms.add(token)
    return terms


# PURPOSE: 行ベースで DECISION 区間を抽出する
def _extract_decisions_from_lines(lines: list[str], file_path: Path) -> list[DecisionRecord]:
    decisions: list[DecisionRecord] = []
    current_header: str | None = None
    current_body: list[str] = []

    def flush_current() -> None:
        nonlocal current_header, current_body
        if current_header is None:
            return

        decision_id, summary = _parse_decision_header(current_header)
        rationale_lines = _clean_rationale_lines(current_body)

        if not summary and rationale_lines:
            summary = rationale_lines.pop(0)

        summary = summary.strip()
        rationale = "\n".join(rationale_lines).strip()
        if summary:
            term_basis = summary
            decisions.append(
                DecisionRecord(
                    file_path=file_path,
                    file_stem=file_path.stem,
                    decision_id=decision_id,
                    summary=summary,
                    rationale=rationale,
                    terms=_extract_terms(term_basis),
                )
            )

        current_header = None
        current_body = []

    for line in lines:
        if "[DECISION" in line:
            flush_current()
            current_header = line
            current_body = []
            continue

        if current_header is not None and _is_boundary_line(line):
            flush_current()
            continue

        if current_header is not None:
            current_body.append(line)

    flush_current()
    return decisions


# PURPOSE: `.typos` ROM から DECISION を抽出
def _parse_typos_rom(path: Path) -> list[DecisionRecord]:
    text = path.read_text(encoding="utf-8")
    blocks = CONTENT_BLOCK_RE.findall(text)
    decisions: list[DecisionRecord] = []
    for block in blocks:
        decisions.extend(_extract_decisions_from_lines(block.splitlines(), path))
    return decisions


# PURPOSE: `.md` ROM から DECISION を抽出
def _parse_markdown_rom(path: Path) -> list[DecisionRecord]:
    text = _strip_frontmatter(path.read_text(encoding="utf-8"))
    return _extract_decisions_from_lines(text.splitlines(), path)


# PURPOSE: ROM ディレクトリ全体から DECISION を収集する
def _load_all_decisions() -> list[DecisionRecord]:
    decisions: list[DecisionRecord] = []
    for path in sorted(ROM_DIR.rglob("*")):
        if path.suffix == ".typos":
            decisions.extend(_parse_typos_rom(path))
        elif path.suffix == ".md":
            decisions.extend(_parse_markdown_rom(path))
    return decisions


# PURPOSE: 語の文書頻度を見て汎用語を落とす
def _filter_ubiquitous_terms(decisions: list[DecisionRecord]) -> list[DecisionRecord]:
    term_document_frequency: Counter[str] = Counter()
    for decision in decisions:
        term_document_frequency.update(decision.terms)

    threshold = max(6, int(len(decisions) * 0.08))
    filtered: list[DecisionRecord] = []
    for decision in decisions:
        kept_terms = {
            term for term in decision.terms
            if term_document_frequency[term] <= threshold
        }
        filtered.append(
            DecisionRecord(
                file_path=decision.file_path,
                file_stem=decision.file_stem,
                decision_id=decision.decision_id,
                summary=decision.summary,
                rationale=decision.rationale,
                terms=kept_terms or decision.terms,
            )
        )
    return filtered


# PURPOSE: decision ごとに共有 2 語署名を作る
def _build_signature_clusters(decisions: list[DecisionRecord]) -> list[list[DecisionRecord]]:
    buckets: dict[tuple[str, str], dict[str, DecisionRecord]] = defaultdict(dict)

    for decision in decisions:
        if len(decision.terms) < 2:
            continue

        ranked_terms = sorted(
            decision.terms,
            key=lambda term: (-len(term), term),
        )[:4]

        for pair in combinations(ranked_terms, 2):
            signature = tuple(sorted(pair))
            buckets[signature][f"{decision.file_stem}:{decision.summary}"] = decision

    clusters: list[list[DecisionRecord]] = []
    seen_signatures: set[tuple[str, ...]] = set()
    for bucket in buckets.values():
        cluster = sorted(
            bucket.values(),
            key=lambda item: (item.file_stem, item.summary),
        )
        if len(cluster) < 2:
            continue
        signature = tuple(f"{item.file_stem}:{item.summary}" for item in cluster)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        clusters.append(cluster)

    return clusters


# PURPOSE: クラスタのテーマ語を決める
def _cluster_theme_terms(cluster: list[DecisionRecord]) -> list[str]:
    counter: Counter[str] = Counter()
    for decision in cluster:
        counter.update(decision.terms)

    common_terms = [
        term for term, count in counter.items()
        if count >= 2 and term not in GENERIC_TERMS
    ]
    common_terms.sort(key=lambda term: (-counter[term], -len(term), term))
    if common_terms:
        return common_terms[:3]

    fallback_terms: list[str] = []
    for decision in cluster:
        fallback_terms.extend(sorted(decision.terms))
    return fallback_terms[:3]


# PURPOSE: テーマ語から kebab-case id を作る
def _slugify_theme(theme_terms: list[str], fallback_text: str) -> str:
    ascii_terms: list[str] = []
    for term in theme_terms:
        slug = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")
        if slug:
            ascii_terms.append(slug)

    if ascii_terms:
        return "-".join(dict.fromkeys(ascii_terms))[:64].strip("-")

    digest = hashlib.sha1(fallback_text.encode("utf-8")).hexdigest()[:10]
    return f"cluster-{digest}"


# PURPOSE: クラスタの domain を雑に自動分類する
def _classify_domain(cluster: list[DecisionRecord], theme_terms: list[str]) -> str:
    combined = "\n".join(
        [decision.summary for decision in cluster] +
        [decision.rationale for decision in cluster] +
        theme_terms
    ).lower()

    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in combined:
                scores[domain] += 1

    best_domain = "process"
    best_score = -1
    for domain in DOMAIN_ORDER:
        score = scores[domain]
        if score > best_score:
            best_domain = domain
            best_score = score
    return best_domain


# PURPOSE: trigger/action をクラスタから合成する
def _synthesize_trigger_and_action(theme_terms: list[str], domain: str) -> tuple[str, str, str]:
    if theme_terms:
        theme_text = " / ".join(theme_terms)
        trigger = f"{theme_text} に関する判断が反復して現れた時"
        action = (
            f"{theme_text} では、複数 ROM に反復した共通判断を既定方針として優先する。\n"
            f"{domain} 上の局所最適ではなく、再出現したパターンを先に疑似標準として扱う。"
        )
        return trigger, action, theme_text

    theme_text = "反復判断パターン"
    trigger = "同型の DECISION が複数 ROM で再出現した時"
    action = (
        "複数 ROM で再出現した判断パターンを既定方針として扱う。\n"
        "単発の判断ではなく、反復観測された共通重心を優先する。"
    )
    return trigger, action, theme_text


# PURPOSE: evidence block 用の行を構築する
def _build_evidence_lines(cluster: list[DecisionRecord]) -> list[str]:
    evidence: list[str] = []
    for decision in cluster:
        header = decision.summary
        if decision.decision_id:
            header = f"{decision.decision_id}: {header}"
        rationale = decision.rationale.replace("\n", " / ").strip()
        if rationale:
            evidence.append(
                f"  - [SOURCE: {decision.file_path}] {header} | {rationale}"
            )
        else:
            evidence.append(f"  - [SOURCE: {decision.file_path}] {header}")
    return evidence


# PURPOSE: Doxa 候補の本文を組み立てる
def _render_candidate(candidate: DoxaCandidate, today_iso: str) -> str:
    frontmatter = [
        "---",
        f"id: {candidate.belief_id}",
        f'trigger: "{candidate.trigger}"',
        "confidence: 0.5",
        "scope: project",
        f'domain: "{candidate.domain}"',
        'source: "cross-session-observation"',
        f'origin_session: "rom-mining-{today_iso}"',
        f'created_at: "{today_iso}"',
        f'updated_at: "{today_iso}"',
        f"evidence_count: {candidate.evidence_count}",
        "---",
        "",
        f"#prompt doxa_{candidate.belief_id}",
        "#syntax: v8.4",
        "",
        "<:content action:",
        f"  {candidate.action.splitlines()[0]}",
    ]

    if len(candidate.action.splitlines()) > 1:
        for extra_line in candidate.action.splitlines()[1:]:
            frontmatter.append(f"  {extra_line}")

    frontmatter.extend(
        [
            "/content:>",
            "",
            "<:content evidence:",
            *candidate.evidence_lines,
            "/content:>",
            "",
        ]
    )
    return "\n".join(frontmatter)


# PURPOSE: 重複 slug を回避する
def _uniquify_ids(candidates: list[DoxaCandidate], output_dir: Path) -> list[DoxaCandidate]:
    existing_ids = {
        path.stem.removeprefix("doxa_")
        for path in output_dir.glob("doxa_*.typos")
    }
    used_ids = set(existing_ids)
    unique_candidates: list[DoxaCandidate] = []

    for candidate in candidates:
        base_id = candidate.belief_id
        current_id = base_id
        suffix = 2
        while current_id in used_ids:
            current_id = f"{base_id}-{suffix}"
            suffix += 1

        used_ids.add(current_id)
        unique_candidates.append(
            DoxaCandidate(
                belief_id=current_id,
                domain=candidate.domain,
                trigger=candidate.trigger,
                action=candidate.action,
                evidence_count=candidate.evidence_count,
                theme_text=candidate.theme_text,
                evidence_lines=candidate.evidence_lines,
            )
        )

    return unique_candidates


# PURPOSE: クラスタから Doxa 候補を生成する
def _build_candidates(decisions: list[DecisionRecord], min_cluster: int, output_dir: Path) -> list[DoxaCandidate]:
    filtered_decisions = _filter_ubiquitous_terms(decisions)
    clusters = _build_signature_clusters(filtered_decisions)

    candidates: list[DoxaCandidate] = []
    for cluster in clusters:
        distinct_stems = {decision.file_stem for decision in cluster}
        if len(cluster) < min_cluster or len(distinct_stems) < min_cluster:
            continue

        theme_terms = _cluster_theme_terms(cluster)
        trigger, action, theme_text = _synthesize_trigger_and_action(
            theme_terms,
            _classify_domain(cluster, theme_terms),
        )
        domain = _classify_domain(cluster, theme_terms)
        belief_id = _slugify_theme(theme_terms, theme_text or trigger)
        candidates.append(
            DoxaCandidate(
                belief_id=belief_id,
                domain=domain,
                trigger=trigger,
                action=action,
                evidence_count=len(cluster),
                theme_text=theme_text,
                evidence_lines=_build_evidence_lines(cluster),
            )
        )

    candidates.sort(key=lambda item: (-item.evidence_count, item.belief_id))
    return _uniquify_ids(candidates, output_dir)


# PURPOSE: dry-run / write の実行
def _emit_candidates(candidates: list[DoxaCandidate], output_dir: Path, dry_run: bool) -> None:
    today_iso = date.today().isoformat()

    if dry_run:
        print(f"ROM decisions scanned from: {ROM_DIR}")
        print(f"Candidate count: {len(candidates)}")
        print("")
        for index, candidate in enumerate(candidates, start=1):
            print(f"===== Candidate {index}: doxa_{candidate.belief_id}.typos =====")
            print(_render_candidate(candidate, today_iso))
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        target_path = output_dir / f"doxa_{candidate.belief_id}.typos"
        target_path.write_text(_render_candidate(candidate, today_iso), encoding="utf-8")
        print(f"WROTE {target_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ROM から Doxa 候補を採掘する")
    parser.add_argument("--dry-run", action="store_true", help="stdout に候補を出力")
    parser.add_argument("--min-cluster", type=int, default=2, help="候補化する最小クラスタサイズ")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Doxa 出力先ディレクトリ",
    )
    args = parser.parse_args()

    decisions = _load_all_decisions()
    candidates = _build_candidates(decisions, max(args.min_cluster, 2), args.output_dir)
    _emit_candidates(candidates, args.output_dir, args.dry_run)


if __name__ == "__main__":
    main()
