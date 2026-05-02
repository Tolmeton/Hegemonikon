from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/backends/storage_backend.py
"""StorageBackend Protocol — GnosisIndex のストレージ抽象化層。

GnosisIndex の公開 API を変更せずに、内部ストレージを
FAISS / NumPy 等で切替可能にする Protocol。

全 Backend はこの Protocol を実装する。
"""


from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """ベクトルストレージの統一インターフェース。

    GnosisIndex が内部で使うストレージ操作を定義する。
    FAISS / NumPy 等の各 Backend がこれを実装する。
    """

    def exists(self) -> bool:
        """テーブル/インデックスが存在するか。"""
        ...

    def create(self, data: list[dict]) -> None:
        """新規テーブル/インデックスを作成し、初期データを投入する。"""
        ...

    def add(self, records: list[dict]) -> int:
        """レコードを追加する。

        Args:
            records: vector フィールドを含むレコードのリスト

        Returns:
            追加されたレコード数
        """
        ...

    def search_vector(
        self,
        query_vector: list[float],
        k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> list[dict]:
        """ベクトル検索を行う。

        Args:
            query_vector: クエリベクトル
            k: 返す最大件数
            filter_expr: フィルタ式 (例: "source = 'handoff'")

        Returns:
            検索結果のリスト (_distance フィールド付き)
        """
        ...

    def search_fts(
        self,
        query: str,
        k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> list[dict]:
        """全文検索を行う。

        Args:
            query: テキストクエリ
            k: 返す最大件数
            filter_expr: フィルタ式

        Returns:
            検索結果のリスト
        """
        ...

    def delete(self, filter_expr: str) -> int:
        """条件に合致するレコードを削除する。

        Args:
            filter_expr: フィルタ式 ("true" で全削除)

        Returns:
            削除されたレコード数
        """
        ...

    def count(self) -> int:
        """レコード総数を返す。"""
        ...

    def to_list(self) -> list[dict]:
        """全レコードを辞書のリストとして返す。"""
        ...

    def to_pandas(self) -> "pd.DataFrame":
        """全レコードを pandas DataFrame として返す。"""
        ...

    def schema_fields(self) -> set[str]:
        """スキーマのフィールド名の集合を返す。"""
        ...

    def migrate_schema(self, columns: dict[str, object]) -> int:
        """スキーマに不足フィールドを追加する。

        既存レコードに columns で指定されたフィールドが欠損していれば、
        デフォルト値で埋める。全フィールドが揃っていれば何もしない (冪等)。

        Args:
            columns: {フィールド名: デフォルト値} の辞書

        Returns:
            更新されたレコード数 (変更不要なら 0)
        """
        ...

    def get_vector_dimension(self) -> Optional[int]:
        """ベクトルの次元数を返す。未設定なら None。"""
        ...
