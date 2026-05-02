#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/ A0→Library検索エンジンが必要→library_searchが担う
"""
Library Search Engine — 3層検索で Library 112プロンプトを発動する

Layer 1: activation_triggers キーワードマッチ (高速・正確)
Layer 2: hegemonikon_mapping ベース WF 連携 (構造的)
Layer 3: GnosisIndex ベクトル検索 (セマンティック)

USAGE:
    from mekhane.anamnesis.library_search import LibrarySearch
    searcher = LibrarySearch()
    results = searcher.search_by_triggers("品質")
"""

import sys
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.anamnesis.models.prompt_module import PromptModule

# Library ベースパス
LIBRARY_BASE = Path.home() / "Sync" / "10_📚_ライブラリ｜Library" / "prompts"

TABLE_NAME = "prompts"


# PURPOSE: Library プロンプト検索エンジン
class LibrarySearch:
    """Library プロンプト検索エンジン (GnosisIndex 経由)"""

    # PURPOSE: LibrarySearch の初期化 — GnosisIndex に遅延接続
    def __init__(self, db_dir: Optional[str] = None):
        self._db_dir = Path(db_dir) if db_dir else None
        self._index = None

    # PURPOSE: GnosisIndex に遅延接続
    def _connect(self):
        """GnosisIndex に遅延接続"""
        if self._index is None:
            from mekhane.anamnesis.index import GnosisIndex

            kwargs = {"table_name": TABLE_NAME}
            if self._db_dir:
                kwargs["db_dir"] = self._db_dir
            self._index = GnosisIndex(**kwargs)
            if not self._index.table_exists():
                raise RuntimeError(
                    f"テーブル '{TABLE_NAME}' が見つかりません。"
                    f"先に index_library.py を実行してください。"
                )

    # ── Layer 1: activation_triggers キーワードマッチ ──

    # PURPOSE: activation_triggers のキーワード部分一致検索
    def search_by_triggers(self, keyword: str, limit: int = 20) -> list[PromptModule]:
        """
        activation_triggers のキーワード部分一致検索

        Args:
            keyword: 検索キーワード (部分一致、大小文字無視)
            limit: 最大件数

        Returns:
            マッチした PromptModule のリスト
        """
        self._connect()
        keyword_lower = keyword.lower()

        # GnosisIndex 経由で全レコード取得しフルスキャン
        all_rows = self._index.filter_to_pandas()
        results = []

        for _, row in all_rows.iterrows():
            triggers_str = row.get("activation_triggers", "")
            name = row.get("name", "")
            mapping = row.get("hegemonikon_mapping", "")

            # triggers, name, mapping のいずれかにマッチ
            searchable = f"{triggers_str} {name} {mapping}".lower()
            if keyword_lower in searchable:
                module = PromptModule.from_dict(row.to_dict())
                results.append(module)

            if len(results) >= limit:
                break

        return results

    # ── Layer 2: hegemonikon_mapping ベース WF 連携 ──

    # PURPOSE: hegemonikon_mapping ベースの WF 連携検索
    def search_by_mapping(self, wf_name: str) -> list[PromptModule]:
        """
        hegemonikon_mapping ベースの WF 連携検索

        Args:
            wf_name: WF 名 (例: "/dia", "A2 Krisis", "O1 Noēsis")

        Returns:
            マッチした PromptModule のリスト
        """
        self._connect()

        # WF 名から HGK シリーズを推定
        wf_to_series = {
            "/noe": "O1", "/bou": "O2", "/zet": "O3", "/ene": "O4",
            "/ske": "S1", "/sag": "S2", "/pei": "S3", "/tek": "S4",
            "/pro": "H1", "/pis": "H2", "/ore": "H3", "/dox": "H4",
            "/kho": "P1", "/hod": "P2", "/tro": "P3",
            "/euk": "K1", "/chr": "K2", "/tel": "K3", "/sop": "K4",
            "/pat": "A1", "/dia": "A2", "/gno": "A3", "/epi": "A4",
        }

        # 入力を正規化
        search_terms = [wf_name]
        clean_wf = wf_name.lstrip("/").lower()

        # WF 短縮名 → シリーズ ID
        for wf, series in wf_to_series.items():
            if clean_wf == wf.lstrip("/") or clean_wf == series.lower():
                search_terms.append(series)
                search_terms.append(wf)
                break

        all_rows = self._index.filter_to_pandas()
        results = []
        seen_ids = set()

        for _, row in all_rows.iterrows():
            mapping = row.get("hegemonikon_mapping", "").lower()
            for term in search_terms:
                if term.lower() in mapping:
                    module = PromptModule.from_dict(row.to_dict())
                    if module.id not in seen_ids:
                        results.append(module)
                        seen_ids.add(module.id)
                    break

        return results

    # ── Layer 3: GnosisIndex ベクトル検索 ──

    # PURPOSE: セマンティック検索 (GnosisIndex vector search)
    def search_semantic(self, query: str, limit: int = 5) -> list[dict]:
        """
        セマンティック検索 (GnosisIndex vector search)

        Args:
            query: 自然言語クエリ
            limit: 最大件数

        Returns:
            検索結果の辞書リスト (score, module 情報含む)
        """
        self._connect()
        from mekhane.anamnesis.index import Embedder

        embedder = Embedder()
        query_vec = embedder.embed(query)

        raw_results = self._index.search(query, query_vector=query_vec, k=limit)

        results = []
        for r in raw_results:
            module = PromptModule.from_dict(r)
            results.append({
                "module": module,
                "score": r.get("_distance", 0.0),
                "name": module.name,
                "mapping": module.hegemonikon_mapping,
                "essence": module.essence[:200] if module.essence else "",
            })

        return results

    # ── ユーティリティ ──

    # PURPOSE: ID からモジュールを取得
    def get_module(self, module_id: str) -> Optional[PromptModule]:
        """ID からモジュールを取得"""
        self._connect()
        all_rows = self._index.filter_to_pandas()

        for _, row in all_rows.iterrows():
            if row.get("id") == module_id:
                return PromptModule.from_dict(row.to_dict())
        return None

    # PURPOSE: カテゴリ別のモジュール数を返す
    def list_categories(self) -> dict[str, int]:
        """カテゴリ別のモジュール数を返す"""
        self._connect()
        all_rows = self._index.filter_to_pandas()

        categories: dict[str, int] = {}
        for _, row in all_rows.iterrows():
            cat = row.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return dict(sorted(categories.items()))

    # PURPOSE: インデックス内のモジュール総数
    def count(self) -> int:
        """インデックス内のモジュール総数"""
        self._connect()
        return len(self._index.list_primary_keys())
