#!/usr/bin/env python3
"""Doxa の project/global 昇降格を扱う CLI。"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


# PURPOSE: HGK ルートを自動検出する
def _detect_hgk_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "00_核心｜Kernel").is_dir():
            return parent
    raise RuntimeError("HGK root を検出できませんでした。")


HGK_ROOT = _detect_hgk_root()
BELIEFS_DIR = HGK_ROOT / "30_記憶｜Mneme/00_信念｜Beliefs"
PROJECT_DIR = BELIEFS_DIR / "_project"
GLOBAL_DIR = BELIEFS_DIR / "_global"
README_PATH = BELIEFS_DIR / "README.md"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
EVIDENCE_BLOCK_RE = re.compile(r"(<:content evidence:\s*)(.*?)(\n/content:>)", re.DOTALL)

SCHEMA_ORDER = [
    "id",
    "trigger",
    "confidence",
    "scope",
    "domain",
    "source",
    "origin_session",
    "created_at",
    "updated_at",
    "evidence_count",
]


@dataclass
class DoxaFile:
    """Doxa ファイルの frontmatter + body。"""

    path: Path
    frontmatter: dict[str, object]
    body: str

    @property
    def belief_id(self) -> str:
        return str(self.frontmatter.get("id", ""))


# PURPOSE: README の schema 正本を読み、存在を確認する
def _ensure_schema_exists() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError(f"Schema README が見つかりません: {README_PATH}")
    README_PATH.read_text(encoding="utf-8")


# PURPOSE: YAML scalar を簡易変換する
def _parse_scalar(value: str) -> object:
    stripped = value.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        return stripped[1:-1]
    if stripped.startswith("'") and stripped.endswith("'"):
        return stripped[1:-1]
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)
    return stripped


# PURPOSE: frontmatter + body を分離する
def _parse_doxa_file(path: Path) -> DoxaFile:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"frontmatter がありません: {path}")

    frontmatter: dict[str, object] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        frontmatter[key.strip()] = _parse_scalar(value)

    body = text[match.end():]
    return DoxaFile(path=path, frontmatter=frontmatter, body=body)


# PURPOSE: schema 順で frontmatter をレンダする
def _render_doxa(doxa_file: DoxaFile) -> str:
    lines = ["---"]
    for key in SCHEMA_ORDER:
        if key not in doxa_file.frontmatter:
            continue
        value = doxa_file.frontmatter[key]
        if key in {"trigger", "domain", "source", "origin_session", "created_at", "updated_at"}:
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.extend(["---", "", doxa_file.body.lstrip("\n")])
    return "\n".join(lines)


# PURPOSE: evidence block に昇降格メモを追記する
def _append_evidence_note(body: str, note: str) -> str:
    formatted_note = f"  - {note}"
    match = EVIDENCE_BLOCK_RE.search(body)
    if not match:
        append_block = "\n<:content evidence:\n" + formatted_note + "\n/content:>\n"
        return body.rstrip() + append_block

    prefix, existing, suffix = match.groups()
    merged = existing.rstrip() + "\n" + formatted_note
    return body[:match.start()] + prefix + merged + suffix + body[match.end():]


# PURPOSE: date 文字列を ISO として読む
def _parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


# PURPOSE: 昇格候補を列挙する
def _scan_promotions() -> list[DoxaFile]:
    candidates: list[DoxaFile] = []
    for path in sorted(PROJECT_DIR.glob("doxa_*.typos")):
        doxa_file = _parse_doxa_file(path)
        evidence_count = int(doxa_file.frontmatter.get("evidence_count", 0) or 0)
        confidence = float(doxa_file.frontmatter.get("confidence", 0.0) or 0.0)
        if evidence_count >= 2 and confidence >= 0.8:
            candidates.append(doxa_file)
    return candidates


# PURPOSE: 降格候補を列挙する
def _scan_demotions() -> list[DoxaFile]:
    candidates: list[DoxaFile] = []
    today = date.today()
    for path in sorted(GLOBAL_DIR.glob("doxa_*.typos")):
        doxa_file = _parse_doxa_file(path)
        confidence = float(doxa_file.frontmatter.get("confidence", 0.0) or 0.0)
        updated_at = _parse_iso_date(doxa_file.frontmatter.get("updated_at"))
        if updated_at is None:
            continue
        stale_days = (today - updated_at).days
        if confidence < 0.2 and stale_days > 30:
            candidates.append(doxa_file)
    return candidates


# PURPOSE: project → global へコピー昇格する
def _promote(doxa_file: DoxaFile, dry_run: bool) -> None:
    today_iso = date.today().isoformat()
    promoted = DoxaFile(
        path=GLOBAL_DIR / doxa_file.path.name,
        frontmatter=dict(doxa_file.frontmatter),
        body=doxa_file.body,
    )
    promoted.frontmatter["scope"] = "global"
    promoted.frontmatter["updated_at"] = today_iso

    if dry_run:
        print(f"PROMOTE {doxa_file.path} -> {promoted.path}")
        return

    GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    promoted.path.write_text(_render_doxa(promoted), encoding="utf-8")
    print(f"PROMOTED {doxa_file.path} -> {promoted.path}")


# PURPOSE: global → project へ移動降格する
def _demote(doxa_file: DoxaFile, dry_run: bool) -> None:
    today_iso = date.today().isoformat()
    demoted_path = PROJECT_DIR / doxa_file.path.name
    confidence = float(doxa_file.frontmatter.get("confidence", 0.0) or 0.0)
    note = (
        f"[SYSTEM: DEMOTION {today_iso}] global から project に降格。"
        f"confidence={confidence:.2f}, updated_at が 30 日超 stale。"
    )

    demoted = DoxaFile(
        path=demoted_path,
        frontmatter=dict(doxa_file.frontmatter),
        body=_append_evidence_note(doxa_file.body, note),
    )
    demoted.frontmatter["scope"] = "project"
    demoted.frontmatter["updated_at"] = today_iso

    if dry_run:
        print(f"DEMOTE {doxa_file.path} -> {demoted.path}")
        return

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    demoted.path.write_text(_render_doxa(demoted), encoding="utf-8")
    if doxa_file.path.exists():
        doxa_file.path.unlink()
    print(f"DEMOTED {doxa_file.path} -> {demoted.path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Doxa project/global 昇降格")
    parser.add_argument("--dry-run", action="store_true", help="変更せず対象だけ表示")
    parser.add_argument("--promote", action="store_true", help="project -> global 昇格を実行")
    parser.add_argument("--demote", action="store_true", help="global -> project 降格を実行")
    args = parser.parse_args()

    _ensure_schema_exists()

    promotions = _scan_promotions()
    demotions = _scan_demotions()

    print(f"promotion_candidates={len(promotions)} demotion_candidates={len(demotions)}")

    if not args.promote and not args.demote:
        for doxa_file in promotions:
            print(f"PROMOTE READY {doxa_file.path}")
        for doxa_file in demotions:
            print(f"DEMOTE READY {doxa_file.path}")
        return

    if args.promote:
        for doxa_file in promotions:
            _promote(doxa_file, args.dry_run)

    if args.demote:
        for doxa_file in demotions:
            _demote(doxa_file, args.dry_run)


if __name__ == "__main__":
    main()
