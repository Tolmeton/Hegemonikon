#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→知識管理が必要→sophia_backlinker が担う
"""
Sophia Backlinker - 知識アイテム間のリンクグラフ構築

[[wikilink]] 構文を検出し、バックリンクを提供する。

Usage:
    python sophia_backlinker.py              # グラフ構築 + 統計表示
    python sophia_backlinker.py --backlinks "ki_name"  # バックリンク取得
"""

import sys
import re
import json
from pathlib import Path
from typing import Set, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import networkx as nx
except ImportError:
    print("❌ networkx not installed. Run: pip install networkx")
    sys.exit(1)


KNOWLEDGE_DIR = Path.home() / ".gemini" / "antigravity" / "knowledge"


# PURPOSE: NetworkX ベースのバックリンク検出システム
class SophiaBacklinker:
    """NetworkX ベースのバックリンク検出システム"""

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self):
        self.graph = nx.DiGraph()  # 方向性グラフ
        self.cache: Dict[str, Dict] = {}  # ノードキャッシュ

    # PURPOSE: [[wikilink]] パターンを抽出
    def extract_links(self, content: str) -> Set[str]:
        """[[wikilink]] パターンを抽出

        対応形式:
        - [[単純リンク]]
        - [[パス/付きリンク]]
        - [[リンク|別名]] (別名は無視)
        """
        # [[...]] 内のテキストを抽出 (| 以降は除外)
        pattern = r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]"
        matches = re.findall(pattern, content)
        return set(matches)

    # PURPOSE: KI ディレクトリからリンクを抽出
    def parse_ki_links(self, ki_path: Path) -> Set[str]:
        """KI ディレクトリからリンクを抽出"""
        links = set()

        # artifacts/*.md を走査
        artifacts_dir = ki_path / "artifacts"
        if artifacts_dir.exists():
            for md_file in artifacts_dir.rglob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                file_links = self.extract_links(content)
                links.update(file_links)

        return links

    # PURPOSE: 全 KI からグラフを構築
    def build_graph(self, ki_dir: Path = None) -> int:
        """全 KI からグラフを構築

        Returns:
            追加されたエッジ数
        """
        ki_dir = ki_dir or KNOWLEDGE_DIR
        edge_count = 0

        for ki_path in ki_dir.iterdir():
            if not ki_path.is_dir():
                continue

            ki_name = ki_path.name
            links = self.parse_ki_links(ki_path)

            # ノード追加
            if not self.graph.has_node(ki_name):
                self.graph.add_node(ki_name, type="ki")

            # エッジ追加 (outlinks)
            for link in links:
                self.graph.add_edge(ki_name, link)
                edge_count += 1

                # キャッシュ更新
                if ki_name not in self.cache:
                    self.cache[ki_name] = {"outlinks": set(), "backlinks": set()}
                self.cache[ki_name]["outlinks"].add(link)

        # バックリンクキャッシュ構築
        self._build_backlink_cache()

        return edge_count

    # PURPOSE: [L2-auto] _build_backlink_cache の関数定義
    def _build_backlink_cache(self):
        """逆方向リンク (バックリンク) のキャッシュを構築"""
        for node in self.graph.nodes():
            backlinks = set(self.graph.predecessors(node))
            if node not in self.cache:
                self.cache[node] = {"outlinks": set(), "backlinks": set()}
            self.cache[node]["backlinks"] = backlinks

    # PURPOSE: O(1) バックリンク検索
    def get_backlinks(self, note_name: str) -> Set[str]:
        """O(1) バックリンク検索"""
        if note_name in self.cache:
            return self.cache[note_name].get("backlinks", set())
        # キャッシュになければグラフから取得
        if self.graph.has_node(note_name):
            return set(self.graph.predecessors(note_name))
        return set()

    # PURPOSE: O(1) アウトリンク検索
    def get_outlinks(self, note_name: str) -> Set[str]:
        """O(1) アウトリンク検索"""
        if note_name in self.cache:
            return self.cache[note_name].get("outlinks", set())
        if self.graph.has_node(note_name):
            return set(self.graph.successors(note_name))
        return set()

    # PURPOSE: グラフ統計を返す
    def get_stats(self) -> Dict:
        """グラフ統計を返す"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "isolated": len(list(nx.isolates(self.graph))),
            "most_linked": self._get_most_linked(5),
        }

    # PURPOSE: [L2-auto] _get_most_linked の関数定義
    def _get_most_linked(self, n: int) -> List[tuple]:
        """最も多くのバックリンクを持つノード"""
        in_degrees = [(node, self.graph.in_degree(node)) for node in self.graph.nodes()]
        return sorted(in_degrees, key=lambda x: x[1], reverse=True)[:n]

    # PURPOSE: グラフを辞書形式でエクスポート
    def to_dict(self) -> Dict:
        """グラフを辞書形式でエクスポート"""
        return {
            "nodes": list(self.graph.nodes()),
            "edges": list(self.graph.edges()),
            "cache": {
                k: {"outlinks": list(v["outlinks"]), "backlinks": list(v["backlinks"])}
                for k, v in self.cache.items()
            },
        }

    # PURPOSE: Mermaid.js 形式でグラフをエクスポート
    def to_mermaid(self, direction: str = "LR", max_nodes: int = 50) -> str:
        """Mermaid.js 形式でグラフをエクスポート

        Args:
            direction: グラフの方向 (LR, TB, RL, BT)
            max_nodes: 警告を表示するノード数閾値

        Returns:
            Mermaid 記法の文字列
        """
        node_count = self.graph.number_of_nodes()
        lines = [f"graph {direction}"]

        # 大規模グラフ警告
        if node_count > max_nodes:
            lines.insert(
                0,
                f"%% ⚠️ 警告: {node_count} ノード (> {max_nodes}) — 可視化が崩壊する可能性",
            )

        # PURPOSE: ノード名をMermaid安全な形式に変換
        def sanitize(name: str) -> str:
            """ノード名をMermaid安全な形式に変換"""
            # 特殊文字を置換、引用符で囲む
            safe = name.replace('"', "'").replace("-", "_").replace(" ", "_")
            return f'"{safe}"'

        for src, dst in self.graph.edges():
            lines.append(f"    {sanitize(src)} --> {sanitize(dst)}")

        return "\n".join(lines)

    # PURPOSE: D3.js force-directed 用 JSON
    def to_json_for_d3(self) -> Dict:
        """D3.js force-directed 用 JSON

        Returns:
            D3.js 互換の nodes/links 構造
        """
        return {
            "nodes": [
                {"id": n, "type": self.graph.nodes[n].get("type", "unknown")}
                for n in self.graph.nodes()
            ],
            "links": [{"source": s, "target": t} for s, t in self.graph.edges()],
        }


# PURPOSE: main の処理
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sophia Backlinker")
    parser.add_argument("--backlinks", type=str, help="Get backlinks for a note")
    parser.add_argument("--outlinks", type=str, help="Get outlinks for a note")
    parser.add_argument("--stats", action="store_true", help="Show graph stats")
    parser.add_argument("--mermaid", action="store_true", help="Output Mermaid diagram")
    parser.add_argument("--json", action="store_true", help="Output D3.js JSON")
    args = parser.parse_args()

    backlinker = SophiaBacklinker()

    print("📊 Building knowledge graph...")
    edges = backlinker.build_graph()
    stats = backlinker.get_stats()

    print(f"✅ Graph built: {stats['nodes']} nodes, {stats['edges']} edges")

    if args.mermaid:
        print(f"\n📈 Mermaid diagram:")
        print(backlinker.to_mermaid())
        return

    if args.json:
        print(f"\n📈 D3.js JSON:")
        print(json.dumps(backlinker.to_json_for_d3(), indent=2, ensure_ascii=False))
        return

    if args.backlinks:
        backlinks = backlinker.get_backlinks(args.backlinks)
        print(f"\n🔙 Backlinks for '{args.backlinks}':")
        if backlinks:
            for link in sorted(backlinks):
                print(f"  ← {link}")
        else:
            print("  (no backlinks)")

    if args.outlinks:
        outlinks = backlinker.get_outlinks(args.outlinks)
        print(f"\n🔗 Outlinks from '{args.outlinks}':")
        if outlinks:
            for link in sorted(outlinks):
                print(f"  → {link}")
        else:
            print("  (no outlinks)")

    if args.stats or (not args.backlinks and not args.outlinks):
        print(f"\n📈 Stats:")
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")
        print(f"  Isolated: {stats['isolated']}")
        if stats["most_linked"]:
            print(f"  Most linked:")
            for name, count in stats["most_linked"]:
                if count > 0:
                    print(f"    {name}: {count} backlinks")


if __name__ == "__main__":
    main()
