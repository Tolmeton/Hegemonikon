from __future__ import annotations
# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/pks/links/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 知識間の関係性把握が予測精度を向上させる
→ Obsidian の wikilink/backlink 機構を再現
→ link_engine.py が担う

# PURPOSE: 構造化ディレクトリ内のファイル間リレーション管理
# [[wikilink]] の解析、backlinks の自動検出、orphan detection, graph export
"""


import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# --- Pattern ---

# Obsidian 互換の [[wikilink]] パターン
# [[target]] or [[target|alias]]
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


# --- Data Models ---


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: ファイル間リンク
class Link:
    """ファイル間リンク"""

    source: Path  # リンク元
    target: str  # リンク先（ファイル名 or パス）
    alias: Optional[str] = None  # 表示テキスト
    line_number: int = 0  # リンクが存在する行番号
    context: str = ""  # リンク前後のテキスト


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: リンクインデックス — 全ファイル間リレーションの索引
class LinkIndex:
    """リンクインデックス — 全ファイル間リレーションの索引"""

    forward_links: dict[str, list[Link]] = field(default_factory=lambda: defaultdict(list))
    backlinks: dict[str, list[Link]] = field(default_factory=lambda: defaultdict(list))
    orphans: list[str] = field(default_factory=list)  # どこからもリンクされていないファイル

    # PURPOSE: link_engine の total files 処理を実行する
    @property
    # PURPOSE: total_files — 知識プッシュの処理
    def total_files(self) -> int:
        all_files = set(self.forward_links.keys())
        for links in self.backlinks.values():
            for link in links:
                all_files.add(str(link.source))
        return len(all_files)

    # PURPOSE: link_engine の total links 処理を実行する
    @property
    # PURPOSE: total_links — 知識プッシュの処理
    def total_links(self) -> int:
        return sum(len(links) for links in self.forward_links.values())


# --- Engine ---
# PURPOSE: 構造化ディレクトリ内のファイル間リレーション管理


# PURPOSE: [L2-auto] LinkEngine のクラス定義
class LinkEngine:
    """構造化ディレクトリ内のファイル間リレーション管理

    Obsidian の wikilink/backlink 機構の mekhane 再現。

    機能:
        - [[wikilink]] パターンの解析
        - Forward links: ファイル → 参照先の抽出
        - Backlinks: ファイル ← 被参照元の自動検出
        - Orphan Detection: どこからもリンクされていないファイルの発見
        - Graph Export: リレーショングラフの JSON/Mermaid 出力
    """

    # PURPOSE: LinkEngine の初期化 — ディレクトリ全体をスキャンしてリンクインデックスを構築
    def __init__(self, root_dir: Path, extensions: tuple[str, ...] = (".md",)):
        self.root_dir = root_dir.resolve()
        self.extensions = extensions
        self._index: Optional[LinkIndex] = None

    # PURPOSE: ディレクトリ全体をスキャンしてリンクインデックスを構築
    def build_index(self) -> LinkIndex:
        """ディレクトリ全体をスキャンしてリンクインデックスを構築"""
        index = LinkIndex()

        # 対象ファイルを収集
        all_files: dict[str, Path] = {}  # stem -> path
        for ext in self.extensions:
            for path in self.root_dir.rglob(f"*{ext}"):
                rel = path.relative_to(self.root_dir)
                all_files[path.stem] = rel
                all_files[str(rel)] = rel

        # 各ファイルのリンクを解析
        for ext in self.extensions:
            for path in self.root_dir.rglob(f"*{ext}"):
                rel_path = str(path.relative_to(self.root_dir))
                links = self._extract_links(path)

                if links:
                    index.forward_links[rel_path] = links

                    # バックリンク登録
                    for link in links:
                        index.backlinks[link.target].append(link)

        # Orphan 検出
        all_file_stems = set(all_files.keys())
        linked_targets = set()
        for links in index.forward_links.values():
            for link in links:
                linked_targets.add(link.target)

        # バックリンクがゼロのファイルを orphan とする
        for stem, rel in all_files.items():
            rel_str = str(rel)
            if (
                rel_str not in linked_targets
                and stem not in linked_targets
                and rel_str in index.forward_links  # ファイル自体は存在
            ):
                # 自身がリンクを持っているが、誰からもリンクされていない
                if stem not in linked_targets:
                    index.orphans.append(rel_str)

        # 重複除去
        index.orphans = sorted(set(index.orphans))

        self._index = index
        return index

    # PURPOSE: ファイルから [[wikilink]] を抽出
    def _extract_links(self, file_path: Path) -> list[Link]:
        """ファイルから [[wikilink]] を抽出"""
        links = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError):
            return links

        for line_num, line in enumerate(content.split("\n"), 1):
            for match in WIKILINK_PATTERN.finditer(line):
                target = match.group(1).strip()
                alias = match.group(2)
                if alias:
                    alias = alias.strip()

                # コンテキスト：リンク前後 50 文字
                start = max(0, match.start() - 50)
                end = min(len(line), match.end() + 50)
                context = line[start:end].strip()

                links.append(
                    Link(
                        source=file_path.relative_to(self.root_dir),
                        target=target,
                        alias=alias,
                        line_number=line_num,
                        context=context,
                    )
                )

        return links

    # PURPOSE: 特定ファイルの被参照元を取得
    def get_backlinks(self, target: str) -> list[Link]:
        """特定ファイルの被参照元を取得"""
        if self._index is None:
            self.build_index()
        assert self._index is not None
        return self._index.backlinks.get(target, [])

    # PURPOSE: 特定ファイルの参照先を取得
    def get_forward_links(self, source: str) -> list[Link]:
        """特定ファイルの参照先を取得"""
        if self._index is None:
            self.build_index()
        assert self._index is not None
        return self._index.forward_links.get(source, [])

    # PURPOSE: どこからもリンクされていないファイルを取得
    def get_orphans(self) -> list[str]:
        """どこからもリンクされていないファイルを取得"""
        if self._index is None:
            self.build_index()
        assert self._index is not None
        return self._index.orphans

    # --- Export ---

    # PURPOSE: リレーショングラフを JSON 出力
    def export_graph_json(self) -> str:
        """リレーショングラフを JSON 出力"""
        if self._index is None:
            self.build_index()
        assert self._index is not None

        nodes = set()
        edges = []

        for source, links in self._index.forward_links.items():
            nodes.add(source)
            for link in links:
                nodes.add(link.target)
                edges.append(
                    {
                        "source": source,
                        "target": link.target,
                        "alias": link.alias,
                    }
                )

        graph = {
            "nodes": [{"id": n, "orphan": n in self._index.orphans} for n in sorted(nodes)],
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "orphans": len(self._index.orphans),
            },
        }

        return json.dumps(graph, ensure_ascii=False, indent=2)

    # PURPOSE: リレーショングラフを Mermaid 形式で出力
    def export_graph_mermaid(self, max_nodes: int = 50) -> str:
        """リレーショングラフを Mermaid 形式で出力"""
        if self._index is None:
            self.build_index()
        assert self._index is not None

        lines = ["graph LR"]
        seen_edges = set()
        node_count = 0

        for source, links in self._index.forward_links.items():
            if node_count >= max_nodes:
                break

            # ノード ID をサニタイズ
            src_id = self._sanitize_mermaid_id(source)
            node_count += 1

            for link in links:
                tgt_id = self._sanitize_mermaid_id(link.target)
                edge_key = f"{src_id}->{tgt_id}"

                if edge_key not in seen_edges:
                    label = link.alias or ""
                    if label:
                        lines.append(f'    {src_id}["{source}"] -->|"{label}"| {tgt_id}["{link.target}"]')
                    else:
                        lines.append(f'    {src_id}["{source}"] --> {tgt_id}["{link.target}"]')
                    seen_edges.add(edge_key)

        return "\n".join(lines)

    # PURPOSE: [L2-auto] _sanitize_mermaid_id の関数定義
    @staticmethod
    # PURPOSE: Mermaid ノード ID をサニタイズ
    def _sanitize_mermaid_id(name: str) -> str:
        """Mermaid ノード ID をサニタイズ"""
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # PURPOSE: インデックスのサマリーを Markdown で出力
    def summary_markdown(self) -> str:
        """インデックスのサマリーを Markdown で出力"""
        if self._index is None:
            self.build_index()
        assert self._index is not None

        idx = self._index
        lines = [
            "## 🔗 Link Engine Summary",
            "",
            f"| 項目 | 値 |",
            f"|:-----|:---|",
            f"| ファイル数 | {idx.total_files} |",
            f"| リンク数 | {idx.total_links} |",
            f"| Orphan 数 | {len(idx.orphans)} |",
        ]

        if idx.orphans:
            lines.append("")
            lines.append("### Orphan Files")
            for orphan in idx.orphans[:20]:
                lines.append(f"- `{orphan}`")

        # 最もリンクされているファイル Top 5
        backlink_counts = {
            target: len(links) for target, links in idx.backlinks.items()
        }
        if backlink_counts:
            top = sorted(backlink_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append("")
            lines.append("### Most Linked (Top 5)")
            lines.append("| File | Backlinks |")
            lines.append("|:-----|:---------|")
            for name, count in top:
                lines.append(f"| `{name}` | {count} |")

        return "\n".join(lines)
