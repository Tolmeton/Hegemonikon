#!/usr/bin/env python3
# PROOF: [L2/コア] <- mekhane/pks/
# PURPOSE: Gateway Bridge — Ideas/Doxa/Handoff を PKS の KnowledgeNugget に変換
"""
Gateway Bridge — HGK 内部データを PKS プッシュ対象に統合

Phase 3 の核心: Ideas/Doxa/Handoff → KnowledgeNugget 変換により、
論文だけでなく HGK 自身の知識も「自ら語る」ようになる。

使用例:
    bridge = GatewayBridge()
    nuggets = bridge.scan()  # 全ソースをスキャン → Nuggets 生成
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .pks_engine import KnowledgeNugget, SessionContext
from mekhane.paths import INCOMING_DIR, ARTIFACTS_DIR, HANDOFF_DIR, KI_DIR


# --- Topic Alias Expansion ---
# 短縮形 → 関連語への展開。コンテキスト一致の偽陰性を低減する。
_TOPIC_ALIASES: dict[str, list[str]] = {
    "fep": ["自由エネルギー", "free energy", "予測誤差", "prediction error", "active inference", "能動推論"],
    "ccl": ["cognitive control", "認知制御", "ワークフロー", "workflow", "マクロ"],
    "hegemonikón": ["hgk", "ヘゲモニコン", "公理", "定理", "axiom"],
    "hgk": ["hegemonikón", "ヘゲモニコン", "公理", "定理"],
    "圏論": ["category theory", "関手", "自然変換", "随伴"],
    "category theory": ["圏論", "functor", "natural transformation", "adjunction"],
    "pks": ["proactive", "プロアクティブ", "push", "knowledge surfacing"],
    "autophōnos": ["autophonos", "一人称", "advocacy", "self-advocate"],
    "poiema": ["生成", "テンプレート", "出力", "epoche", "metron"],
    "synteleia": ["監査", "audit", "白血球", "wbc"],
    "desktop": ["tauri", "ui", "dashboard", "vite"],
    "jules": ["gemini code assist", "コーディング", "coding"],
}


# --- Data Source Configuration ---

# PURPOSE: [L2-auto] GatewaySource のクラス定義
@dataclass
class GatewaySource:
    """Gateway データソースの設定。"""
    name: str
    directory: Path
    glob_pattern: str
    parse_fn: str  # GatewayBridge のメソッド名
    enabled: bool = True


# PURPOSE: [L2-auto] GatewayBridge のクラス定義
class GatewayBridge:
    """HGK 内部データと PKS を橋渡しするブリッジ。

    Ideas, Doxa, Handoff, KI の各データソースをスキャンし、
    文脈との関連性があるものを KnowledgeNugget に変換する。
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        ideas_dir: Optional[Path] = None,
        doxa_dir: Optional[Path] = None,
        sessions_dir: Optional[Path] = None,
        ki_dir: Optional[Path] = None,
        max_age_days: int = 30,
    ):
        self.max_age_days = max_age_days
        self._sources = [
            GatewaySource(
                name="ideas",
                directory=ideas_dir or INCOMING_DIR,
                glob_pattern="idea_*.md",
                parse_fn="_parse_idea",
            ),
            GatewaySource(
                name="doxa",
                directory=doxa_dir or ARTIFACTS_DIR,
                glob_pattern="dox*.md",
                parse_fn="_parse_doxa",
            ),
            GatewaySource(
                name="handoff",
                directory=sessions_dir or HANDOFF_DIR,
                glob_pattern="handoff_*.md",
                parse_fn="_parse_handoff",
            ),
            GatewaySource(
                name="ki",
                directory=ki_dir or KI_DIR,
                glob_pattern="*.md",
                parse_fn="_parse_ki",
            ),
        ]

    # PURPOSE: 全ソースをスキャンし KnowledgeNugget に変換する
    def scan(
        self,
        context: Optional[SessionContext] = None,
        sources: Optional[list[str]] = None,
        max_results: int = 20,
    ) -> list[KnowledgeNugget]:
        """全 Gateway ソースをスキャンし、コンテキスト関連のナゲットを返す。

        Args:
            context: 現在のセッションコンテキスト (None = フィルタなし)
            sources: 対象ソース名リスト (None = 全ソース)
            max_results: 最大結果数
        """
        all_nuggets: list[KnowledgeNugget] = []

        for source in self._sources:
            if not source.enabled:
                continue
            if sources and source.name not in sources:
                continue
            if not source.directory.exists():
                continue

            parse_fn = getattr(self, source.parse_fn, None)
            if not parse_fn:
                continue

            files = sorted(
                source.directory.glob(source.glob_pattern),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )[:max_results * 2]  # pre-filter buffer

            for f in files:
                try:
                    nugget = parse_fn(f)
                    if nugget:
                        all_nuggets.append(nugget)
                except (OSError, ValueError):
                    continue

        # Context-based relevance filtering
        if context and context.topics:
            all_nuggets = self._filter_by_context(all_nuggets, context)

        # Sort by relevance, then recency
        all_nuggets.sort(key=lambda n: n.relevance_score, reverse=True)
        return all_nuggets[:max_results]

    # PURPOSE: Ideas ファイルを KnowledgeNugget に変換する
    def _parse_idea(self, path: Path) -> Optional[KnowledgeNugget]:
        """idea_*.md を KnowledgeNugget に変換する。"""
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract tags
        tag_match = re.search(r"\*\*タグ\*\*:\s*(.+)", content)
        tags = tag_match.group(1).strip() if tag_match else ""

        # Extract date from filename
        fname_match = re.search(r"idea_(\d{4})(\d{2})(\d{2})", path.stem)
        date_str = ""
        if fname_match:
            g = fname_match.groups()
            date_str = f"{g[0]}-{g[1]}-{g[2]}"

        # Extract H2 sections as abstract
        sections = re.findall(r"^## (.+)$", content, re.MULTILINE)
        abstract = f"アイデア: {title}\nセクション: {', '.join(sections[:5])}"
        if tags:
            abstract += f"\nタグ: {tags}"

        nugget = KnowledgeNugget(
            title=title or path.stem,
            abstract=abstract,
            source=f"gateway:ideas:{path.name}",
            relevance_score=0.6,  # base score, adjusted by context
            push_reason=f"💡 アイデアメモ ({date_str})",
        )
        # Preserve tags as metadata for direct matching
        if tags:
            nugget.metadata = {"tags": [t.strip() for t in tags.split(",")]}
        return nugget

    # PURPOSE: Doxa ファイルを KnowledgeNugget に変換する
    def _parse_doxa(self, path: Path) -> Optional[KnowledgeNugget]:
        """doxa_*.md / dox_*.md を KnowledgeNugget に変換する。"""
        if path.name == "README.md":
            return None

        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract date
        date_match = re.search(r"\*\*日付\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
        date_str = date_match.group(1) if date_match else ""

        # Extract DX- identifiers
        dx_ids = re.findall(r"(DX-\d{3})", content)

        # Extract confidence
        conf_match = re.search(r"\[確信:\s*(\d+)%\]", content)
        confidence = int(conf_match.group(1)) if conf_match else 70

        abstract = f"信念: {title}"
        if dx_ids:
            abstract += f"\n識別子: {', '.join(dx_ids)}"

        nugget = KnowledgeNugget(
            title=title or path.stem,
            abstract=abstract,
            source=f"gateway:doxa:{path.name}",
            relevance_score=confidence / 100.0 * 0.8,
            push_reason=f"📜 信念記録 ({date_str})",
        )
        # Preserve DX-IDs as tag metadata for direct matching
        if dx_ids:
            nugget.metadata = {"tags": dx_ids}
        return nugget

    # PURPOSE: Handoff ファイルを KnowledgeNugget に変換する
    def _parse_handoff(self, path: Path) -> Optional[KnowledgeNugget]:
        """handoff_*.md を KnowledgeNugget に変換する。直近30日のみ。"""
        # Age filter
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age_days = (datetime.now() - mtime).days
        if age_days > self.max_age_days:
            return None

        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract primary_task from YAML frontmatter
        task_match = re.search(r"primary_task:\s*(.+)", content)
        primary_task = task_match.group(1).strip() if task_match else ""

        # Extract date from filename: handoff_YYYYMMDD_HHMM.md
        fname_match = re.search(r"handoff_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})", path.stem)
        date_str = ""
        if fname_match:
            g = fname_match.groups()
            date_str = f"{g[0]}-{g[1]}-{g[2]} {g[3]}:{g[4]}"

        abstract = f"引き継ぎ: {primary_task or title}"

        # Recency boost: newer = higher score
        recency_boost = max(0, 1.0 - age_days / self.max_age_days) * 0.3

        return KnowledgeNugget(
            title=primary_task or title or path.stem,
            abstract=abstract,
            source=f"gateway:handoff:{path.name}",
            relevance_score=0.5 + recency_boost,
            push_reason=f"📋 引き継ぎ ({date_str}, {age_days}日前)",
        )

    # PURPOSE: KI ファイルを KnowledgeNugget に変換する
    def _parse_ki(self, path: Path) -> Optional[KnowledgeNugget]:
        """Knowledge Item (.md) を KnowledgeNugget に変換する。"""
        if path.name == "README.md":
            return None

        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract KI type
        ki_type_match = re.search(r"\*\*KI 種別\*\*:\s*(.+)", content)
        ki_type = ki_type_match.group(1).strip() if ki_type_match else "unknown"

        # Extract confidence
        conf_match = re.search(r"\[確信:\s*(\d+)%\]", content)
        confidence = int(conf_match.group(1)) if conf_match else 75

        abstract = f"知識: {title}\n種別: {ki_type}"

        nugget = KnowledgeNugget(
            title=title or path.stem,
            abstract=abstract,
            source=f"gateway:ki:{path.name}",
            relevance_score=confidence / 100.0 * 0.85,
            push_reason=f"🧠 Knowledge Item ({ki_type})",
        )
        # Preserve KI type as tag metadata for direct matching
        nugget.metadata = {"tags": [ki_type.strip()]}
        return nugget

    # PURPOSE: コンテキストに基づく多段階フィルタリング
    def _filter_by_context(
        self,
        nuggets: list[KnowledgeNugget],
        context: SessionContext,
    ) -> list[KnowledgeNugget]:
        """多段階マッチングでコンテキスト関連度を調整する。

        3段階:
          1. 直接一致 — トピック名がテキスト内に存在
          2. エイリアス展開 — FEP→自由エネルギー等の関連語で一致
          3. タグ直接マッチ — Ideas/KI のタグメタデータで一致
        """
        topic_set = {t.lower() for t in context.topics}

        # Expand topics with aliases
        expanded: set[str] = set(topic_set)
        for topic in topic_set:
            if topic in _TOPIC_ALIASES:
                expanded.update(a.lower() for a in _TOPIC_ALIASES[topic])

        result = []

        for nugget in nuggets:
            text = f"{nugget.title} {nugget.abstract}".lower()
            match_score = 0.0
            match_labels: list[str] = []

            # Stage 1: Direct topic match (highest weight)
            direct_matches = sum(1 for t in topic_set if t in text)
            if direct_matches > 0:
                match_score += direct_matches * 0.15
                match_labels.append(f"直接{direct_matches}")

            # Stage 2: Alias expansion match
            alias_terms = expanded - topic_set
            alias_matches = sum(1 for a in alias_terms if a in text)
            if alias_matches > 0:
                match_score += alias_matches * 0.08  # lower weight than direct
                match_labels.append(f"関連{alias_matches}")

            # Stage 3: Tag metadata match
            tags = getattr(nugget, 'metadata', {}).get('tags', []) if hasattr(nugget, 'metadata') else []
            if tags:
                tag_set = {t.lower() for t in tags}
                tag_matches = len(tag_set & expanded)
                if tag_matches > 0:
                    match_score += tag_matches * 0.12
                    match_labels.append(f"タグ{tag_matches}")

            if match_score > 0:
                boost = min(match_score, 0.5)
                nugget.relevance_score = min(nugget.relevance_score + boost, 1.0)
                nugget.push_reason += f" [一致: {'+'.join(match_labels)}]"
                result.append(nugget)
            elif nugget.relevance_score >= 0.7:
                # High base relevance passes through without topic match
                result.append(nugget)

        return result

    # PURPOSE: 統計情報を返す
    def stats(self) -> dict[str, Any]:
        """Gateway ソースの統計を返す。"""
        stats: dict[str, Any] = {}
        for source in self._sources:
            if not source.directory.exists():
                stats[source.name] = {"exists": False, "count": 0}
                continue
            files = list(source.directory.glob(source.glob_pattern))
            stats[source.name] = {
                "exists": True,
                "count": len(files),
                "directory": str(source.directory),
            }
        return stats
