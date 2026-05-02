from __future__ import annotations
"""Phantasia Field — 埋め込み空間のファサードクラス (v0.5 + precision gradient)。

PROOF: Phantasia Field は Phantazein Trinity アーキテクチャの「場」層を提供する。
GnosisIndex (FAISS) をストレージとして使い、NumPy でフィールド演算を行う。

設計思想:
  - 溶解 (dissolve): ソースデータ → チャンク → embedding → 場に投入
  - 想起 (recall): クエリ → embedding → 場から結晶化
    - Exploit: 高類似度チャンクを precision-weighted スコアで取得
    - Explore: 密度ベースの precision で α を動的調整し新奇チャンクを発掘
  - 密度更新 (update_density): k-NN 密度推定で ρ_MB を再計算

precision gradient (linkage_hyphe.md §3.5):
  precision(ρ) = 1 - λ(ρ) = ρ² (3 - 2ρ)  [Hermite 補間]
  高密度 = 高精度 = exploit 寄り / 低密度 = 低精度 = explore 寄り

依存:
  - mekhane.anamnesis.index.GnosisIndex (FAISS)
  - mekhane.anamnesis.chunker.MarkdownChunker / NucleatorChunker
  - numpy (フィールド演算)
"""


import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# PURPOSE: テキスト重複率の簡易計算 (母液分離の重複検出用)
def _text_overlap(a: str, b: str) -> float:
    """2つのテキストの重複率を 2-gram Jaccard 係数で計算する。

    Args:
        a, b: 比較するテキスト (先頭200文字程度を想定)

    Returns:
        重複率 [0.0, 1.0]
    """
    if not a or not b:
        return 0.0
    # 2-gram 集合
    ngrams_a = {a[i:i+2] for i in range(len(a) - 1)} if len(a) >= 2 else {a}
    ngrams_b = {b[i:i+2] for i in range(len(b) - 1)} if len(b) >= 2 else {b}
    intersection = ngrams_a & ngrams_b
    union = ngrams_a | ngrams_b
    return len(intersection) / len(union) if union else 0.0


# PURPOSE: metadata_json から rich metrics を展開する (Gap 2: recall でのメトリクス活用)
def _expand_metadata(results: list[dict]) -> list[dict]:
    """search 結果の metadata_json を展開し、coherence/drift/efe をトップレベルに昇格する。

    GnosisIndex.add_chunks は NucleatorChunker 由来の coherence/drift/efe を
    metadata_json (JSON 文字列) に格納している。recall 時にこれらを直接参照
    できるようにする。既にトップレベルに存在するフィールドは上書きしない。

    Args:
        results: GnosisIndex.search() の返り値

    Returns:
        metadata 展開済みの結果リスト (in-place 変更)
    """
    for r in results:
        raw = r.get("metadata_json")
        if not raw or raw == "{}":
            continue
        try:
            meta = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            continue
        # coherence, drift, efe をトップレベルに昇格 (既存値がなければ)
        for key in ("coherence", "drift", "efe"):
            if key in meta and key not in r:
                r[key] = meta[key]
    return results


# PURPOSE: 密度から precision gradient を計算 (linkage_hyphe.md §3.5)
def compute_precision_from_density(density: float) -> float:
    """密度 (ρ) から precision gradient を計算する。

    linkage_hyphe.md §3.5 の λ(ρ) = 1 - ρ²(3 - 2ρ) の逆像:
    precision(ρ) = 1 - λ(ρ) = ρ²(3 - 2ρ)  [Hermite 補間 smoothstep]

    高密度 → 高精度 (exploit 寄り)
    低密度 → 低精度 (explore 寄り)

    Args:
        density: k-NN 密度推定値 [0, 1]

    Returns:
        precision gradient 値 [0, 1]
    """
    rho = max(0.0, min(1.0, density))
    return rho * rho * (3 - 2 * rho)


class PhantasiaField:
    """Phantasia Field — 多次元埋め込み空間のファサード。

    GnosisIndex を内部に保持し、溶解 (dissolve)・想起 (recall)・
    密度更新 (update_density) の統一インターフェースを提供する。

    Usage:
        field = PhantasiaField()
        field.dissolve(text, source="session", session_id="abc123")
        results = field.recall("FEP と能動推論", mode="exploit")
        field.update_density()
    """

    # PURPOSE: 場の初期化
    def __init__(
        self,
        db_path: Optional[str] = None,
        chunker_mode: str = "markdown",
        embed_model: str | None = None,
        backend: str = "faiss",
    ):
        """Phantasia Field を初期化する。

        Args:
            db_path: インデックスのパス (None = デフォルトパス)
            chunker_mode: チャンカー種別 ("markdown" or "nucleator")
            embed_model: 埋め込みモデル名
            backend: ストレージバックエンド ("faiss", "numpy")
        """
        self._db_path = db_path
        self._chunker_mode = chunker_mode
        self._embed_model = embed_model
        self._backend = backend
        self._index: Optional["GnosisIndex"] = None
        self._chunker = None

    # PURPOSE: 遅延初期化 (GnosisIndex)
    def _get_index(self) -> "GnosisIndex":
        """GnosisIndex を遅延初期化して返す。"""
        if self._index is None:
            from mekhane.anamnesis.index import GnosisIndex

            if self._db_path:
                self._index = GnosisIndex(db_dir=Path(self._db_path), backend=self._backend)
            else:
                self._index = GnosisIndex(backend=self._backend)
        return self._index

    # PURPOSE: 遅延初期化 (Chunker)
    def _get_chunker(self):
        """チャンカーを遅延初期化して返す。"""
        if self._chunker is None:
            if self._chunker_mode == "nucleator":
                from mekhane.anamnesis.chunker import NucleatorChunker
                self._chunker = NucleatorChunker()
            else:
                from mekhane.anamnesis.chunker import MarkdownChunker
                self._chunker = MarkdownChunker()
        return self._chunker

    # PURPOSE: ソースデータを場に溶解 (F: Source → Field)
    def dissolve(
        self,
        text: str,
        source: str = "session",
        session_id: str = "",
        project_id: str = "",
        title: str = "",
        parent_id: str = "",
        dedupe: bool = True,
    ) -> int:
        """テキストをチャンク化し、場に溶解する。

        チャンク → embedding → GnosisIndex 投入の一連のパイプラインを実行。

        Args:
            text: 溶解するテキスト
            source: データソース種別 ("session", "handoff", "rom", "ki")
            session_id: 関連セッション ID
            project_id: 関連プロジェクト ID
            title: ドキュメントのタイトル (context header に使用)
            parent_id: 親ドキュメント ID (チャンクの parent_id に設定)
            dedupe: 重複排除を行うか

        Returns:
            溶解されたチャンク数
        """
        if not text or not text.strip():
            log.warning("[PhantasiaField] 空テキスト: 溶解スキップ")
            return 0

        # チャンク化
        chunker = self._get_chunker()
        chunks = chunker.chunk(text, source_id=source, title=title)

        if not chunks:
            log.warning("[PhantasiaField] チャンクなし: 溶解スキップ")
            return 0

        # ③ 熱時濾過 — 不溶性不純物を溶解前に除去
        # (linkage_hyphe.md §7: 場⊣結晶原理、化学の再結晶化アナロジー)
        raw_count = len(chunks)
        chunks = self.purify_chunks(chunks)
        purified = raw_count - len(chunks)
        if purified > 0:
            log.info(
                f"[PhantasiaField] 🧪 熱時濾過: {purified}/{raw_count} チャンク除去"
            )

        if not chunks:
            log.warning("[PhantasiaField] 濾過後チャンクなし: 溶解スキップ")
            return 0

        # parent_id を外部から上書き
        if parent_id:
            for chunk in chunks:
                chunk["parent_id"] = parent_id

        # GnosisIndex に投入
        index = self._get_index()
        count = index.add_chunks(
            chunks=chunks,
            source=source,
            session_id=session_id,
            project_id=project_id,
            dedupe=dedupe,
        )

        log.info(f"[PhantasiaField] ✅ Dissolved {count} chunks (source={source})")
        return count

    # PURPOSE: 場から想起 (G: Field → Crystal)
    def recall(
        self,
        query: str,
        mode: str = "exploit",
        limit: int = 10,
        source_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
    ) -> list[dict]:
        """場からチャンクを想起する。

        Args:
            query: 検索クエリ
            mode: 想起モード
                - "exploit": 高類似度チャンクを返す (通常検索)
                - "explore": 低密度領域から新奇なチャンクを返す (EFE 最大化)
            limit: 返すチャンク数
            source_filter: ソースでフィルタ ("session", "handoff" 等)
            session_filter: セッション ID でフィルタ

        Returns:
            チャンクのリスト (各要素は dict)
        """
        index = self._get_index()

        if mode == "explore":
            return self._recall_explore(query, limit, source_filter, session_filter)
        else:
            return self._recall_exploit(query, limit, source_filter, session_filter)

    # PURPOSE: Exploit 想起 — precision-weighted スコアで高類似度チャンクを取得
    def _recall_exploit(
        self,
        query: str,
        limit: int = 10,
        source_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
    ) -> list[dict]:
        """Exploit モード: ベクトル類似度 × precision gradient で重み付けした結果を返す。

        precision gradient は density から動的に計算される (linkage_hyphe.md §3.5)。
        高密度チャンク (= 高精度) のスコアが相対的に上がる。
        """
        index = self._get_index()

        # 既存 search メソッドを活用
        try:
            results = index.search(
                query=query,
                k=limit * 2,  # フィルタ後に limit まで絞り込むため余分に取得
            )
        except Exception as e:  # noqa: BLE001
            log.error(f"[PhantasiaField] Exploit recall failed: {e}")
            return []

        # フィルタ適用
        filtered = self._apply_filters(results, source_filter, session_filter)

        # metadata_json から rich metrics を展開
        _expand_metadata(filtered)

        # precision gradient で重み付けスコアリング
        for r in filtered:
            base_score = r.get("_distance", 0.0)
            # DB に NucleatorChunker 由来の precision があればそれを使用
            # なければ density から近似計算 (MarkdownChunker 経由のフォールバック)
            stored_precision = r.get("precision")
            if stored_precision is not None and stored_precision != 0.5:
                precision = stored_precision
            else:
                density = r.get("density", 0.5)
                precision = compute_precision_from_density(density)
            r["precision"] = precision
            # スコア = 類似度 × (0.5 + precision * 0.5)
            # precision が高いほど (= 高密度 = 情報集約地帯) スコア上昇
            r["_field_score"] = (1.0 - base_score) * (0.5 + precision * 0.5)

        # スコア降順でソート → limit まで
        filtered.sort(key=lambda x: x.get("_field_score", 0), reverse=True)

        # ⑤ 母液分離 — 想起後の不純物除去
        refined = self._refine_results(filtered[:limit * 2], mode="exploit")
        return refined[:limit]

    # PURPOSE: Explore 想起 — precision-adaptive α で低密度領域から新奇チャンクを発掘
    def _recall_explore(
        self,
        query: str,
        limit: int = 10,
        source_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
    ) -> list[dict]:
        """Explore モード: 低密度 × 適度な関連性のチャンクを返す (EFE 最大化)。

        precision gradient でクエリ周辺の密度から α を動的調整:
        - 低精度領域 (density 低い) → α ↑ (explore 寄り)
        - 高精度領域 (density 高い) → α ↓ (exploit 寄り)
        """
        index = self._get_index()

        # 広めに候補を取得
        try:
            results = index.search(
                query=query,
                k=limit * 5,
            )
        except Exception as e:  # noqa: BLE001
            log.error(f"[PhantasiaField] Explore recall failed: {e}")
            return []

        filtered = self._apply_filters(results, source_filter, session_filter)

        # metadata_json から rich metrics を展開
        _expand_metadata(filtered)

        # クエリ周辺の平均密度から precision gradient を計算
        if filtered:
            mean_density = sum(r.get("density", 0.5) for r in filtered) / len(filtered)
        else:
            mean_density = 0.5
        query_precision = compute_precision_from_density(mean_density)

        # precision → α 動的調整
        # α_base = 0.7 (explore 寄り)
        # 高精度 → α 減少 (exploit 方向) / 低精度 → α 維持·増加 (explore 方向)
        # α = 0.7 - 0.3 * precision  → [0.4, 0.7]
        alpha = 0.7 - 0.3 * query_precision

        # EFE スコア = epistemic_value (1 - density) + pragmatic_value (similarity)
        for r in filtered:
            similarity = 1.0 - r.get("_distance", 1.0)
            density = r.get("density", 0.5)
            # DB の NucleatorChunker 由来 precision を優先使用
            stored_precision = r.get("precision")
            if stored_precision is not None and stored_precision != 0.5:
                precision = stored_precision
            else:
                precision = compute_precision_from_density(density)
            r["precision"] = precision
            # epistemic value: 低密度 = 高情報量 (サプライズ最大化)
            epistemic = 1.0 - density
            # pragmatic value: 適度な関連性 (完全無関係は除外)
            pragmatic = similarity
            # EFE = α * epistemic + (1 - α) * pragmatic
            r["_field_score"] = alpha * epistemic + (1 - alpha) * pragmatic
            r["_epistemic_value"] = epistemic
            r["_pragmatic_value"] = pragmatic
            r["_alpha"] = alpha

        # EFE 降順ソート → limit まで
        # ただし similarity が 0.1 未満のものは除外 (完全無関係の排除)
        filtered = [r for r in filtered if (1.0 - r.get("_distance", 1.0)) > 0.1]
        filtered.sort(key=lambda x: x.get("_field_score", 0), reverse=True)

        # ⑤ 母液分離 — explore でも重複除去は有効
        refined = self._refine_results(filtered[:limit * 2], mode="explore")
        return refined[:limit]

    # PURPOSE: フィルタ適用 (共通ユーティリティ)
    @staticmethod
    def _apply_filters(
        results: list[dict],
        source_filter: Optional[str] = None,
        session_filter: Optional[str] = None,
    ) -> list[dict]:
        """ソース・セッション ID でフィルタする。"""
        filtered = results
        if source_filter:
            filtered = [r for r in filtered if r.get("source") == source_filter]
        if session_filter:
            filtered = [r for r in filtered if r.get("session_id") == session_filter]
        return filtered

    # ── 純度錬成 (Purity Filtration) ────────────────────────────
    # 化学の再結晶化アナロジー (linkage_hyphe.md §7 場⊣結晶原理)
    #   ③ 熱時濾過 → purify_chunks()   : 溶解前に不溶性不純物を除去
    #   ⑤ 母液分離 → _refine_results() : 想起後に可溶性不純物を除去

    # PURPOSE: ③ 熱時濾過 — 溶解前の不純物チャンク除去
    @staticmethod
    def purify_chunks(
        chunks: list[dict],
        min_text_len: int = 30,
        min_coherence: float = 0.15,
        max_drift: float = 0.85,
        min_efe: float = 0.05,
    ) -> list[dict]:
        """チャンクの品質メトリクスで不純物を除去する (熱時濾過)。

        化学アナロジー: 加熱溶解後、冷却結晶化の前に不溶性不純物を
        フィルタで除去する工程。結晶格子に不純物が取り込まれるのを防ぐ。

        U パターン (忘却関手) との対応:
          - U_depth (表面性): len(text) < min_text_len
          - U_arrow (無関係性): coherence < min_coherence
          - U_context (文脈喪失): drift > max_drift
          - U_epistemic (情報不足): efe < min_efe

        閾値の理論的根拠:
          - coherence < 0.15 ≈ ρ_MB < τ (linkage_hyphe.md §3.5)
          - drift > 0.85 ≈ L(c) Drift 項が支配的 (§3.6)
          - efe < 0.05 ≈ epistemic + pragmatic value ≈ 0 (§3.6)

        Args:
            chunks: NucleatorChunker が返したチャンク dict のリスト
            min_text_len: 最小テキスト長 (未満は U_depth として除去)
            min_coherence: 最小 coherence (未満は U_arrow として除去)
            max_drift: 最大 drift (超過は U_context として除去)
            min_efe: 最小 EFE (未満は U_epistemic として除去)

        Returns:
            濾過後のチャンクリスト
        """
        purified = []
        for chunk in chunks:
            text = chunk.get("text", "")

            # U_depth: テキストが短すぎる (表面的)
            if len(text.strip()) < min_text_len:
                log.debug("  🔻 U_depth 除去: len=%d < %d", len(text), min_text_len)
                continue

            # Nucleator メトリクスが存在する場合のみ品質ゲート適用
            coherence = chunk.get("coherence")
            drift = chunk.get("drift")
            efe = chunk.get("efe")

            # U_arrow: 内部 coherence が低い (意味的にバラバラ)
            if coherence is not None and coherence < min_coherence:
                log.debug(
                    "  🔻 U_arrow 除去: coherence=%.3f < %.3f",
                    coherence, min_coherence,
                )
                continue

            # U_context: drift が高い (文脈から逸脱)
            if drift is not None and drift > max_drift:
                log.debug(
                    "  🔻 U_context 除去: drift=%.3f > %.3f",
                    drift, max_drift,
                )
                continue

            # U_epistemic: EFE が低い (情報価値なし)
            if efe is not None and efe < min_efe:
                log.debug(
                    "  🔻 U_epistemic 除去: efe=%.4f < %.4f",
                    efe, min_efe,
                )
                continue

            purified.append(chunk)

        return purified

    # PURPOSE: ⑤ 母液分離 — 想起後の不純物除去
    @staticmethod
    def _refine_results(
        results: list[dict],
        mode: str = "exploit",
        min_similarity: float = 0.15,
        dedupe_threshold: float = 0.95,
        max_drift: float = 0.85,
    ) -> list[dict]:
        """想起結果から不純物を除去する (母液分離)。

        化学アナロジー: 冷却結晶化後、結晶を母液 (不純物を含む溶液) から
        分離する工程。高純度の結晶のみを収穫する。

        U パターンとの対応:
          - U_self (自己反復): 重複チャンクの除去 (意味的類似度 > dedupe_threshold)
          - U_adjoint (片面性): 極端に低い類似度のチャンクの除去
          - U_context (文脈逸脱): drift が高すぎるチャンクの除去

        Args:
            results: recall 結果のリスト
            mode: "exploit" or "explore"
            min_similarity: 最小類似度 (未満は除去)
            dedupe_threshold: 重複判定閾値 (content の文字列類似度)
            max_drift: 最大 drift (超過は U_context として除去、0.85 = §3.6 閾値)

        Returns:
            精製後の結果リスト
        """
        if not results:
            return results

        refined = []
        seen_texts: list[str] = []

        for r in results:
            # U_adjoint: 類似度が低すぎるものを除去
            distance = r.get("_distance", 1.0)
            similarity = 1.0 - distance
            if similarity < min_similarity:
                continue

            # U_context: drift が高すぎるものを除去 (文脈逸脱)
            drift = r.get("drift")
            if drift is not None and drift > max_drift:
                continue

            # U_self: 重複除去 (content の先頭200文字を比較)
            content = r.get("content", r.get("text", ""))[:200]
            is_dup = False
            for seen in seen_texts:
                # 簡易文字列重複: 先頭200文字の一致率
                overlap = _text_overlap(content, seen)
                if overlap > dedupe_threshold:
                    is_dup = True
                    break

            if is_dup:
                continue

            seen_texts.append(content)
            refined.append(r)

        return refined

    # PURPOSE: 密度 (ρ_MB) を再計算
    def update_density(self, k: int = 10) -> int:
        """場全体の密度を k-NN 密度推定で更新する。

        GnosisIndex.update_density() に委譲する。

        Args:
            k: 近傍数

        Returns:
            更新されたレコード数
        """
        index = self._get_index()
        count = index.update_density(k=k)
        log.info(f"[PhantasiaField] Updated density for {count} records")
        return count

    # PURPOSE: 場の統計情報
    def stats(self) -> dict:
        """場の統計情報を返す。"""
        index = self._get_index()
        base_stats = index.stats()

        # Hyphē 固有の統計を追加
        base_stats["chunker_mode"] = self._chunker_mode
        base_stats["embed_model"] = self._embed_model

        return base_stats

    # PURPOSE: 場の健全性チェック
    def health(self) -> dict:
        """場の健全性を返す。"""
        try:
            stats = self.stats()
            total = stats.get("total", 0)

            if total == 0:
                status = "empty"
            elif total < 100:
                status = "sparse"
            elif total < 1000:
                status = "growing"
            else:
                status = "healthy"

            return {
                "status": status,
                "total_chunks": total,
                "sources": stats.get("sources", {}),
                "chunker_mode": self._chunker_mode,
            }
        except Exception as e:  # noqa: BLE001
            return {
                "status": "error",
                "error": str(e),
            }
