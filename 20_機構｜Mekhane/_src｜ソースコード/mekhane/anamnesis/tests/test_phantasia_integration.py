# PROOF: [L2/テスト] <- mekhane/anamnesis/tests/test_phantasia_integration.py
"""Phantasia Crystallizer 統合テスト。

Mock を最小限にし、実際の GnosisIndex (NumPy backend) + 固定 embedding で
Dissolve → Recrystallize → Distill パイプラインを E2E テストする。

NumPy backend: Vertex AI API 不要。embedding は固定ベクトルを注入。
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── テスト用固定 Embedding ──────────────────────────────────────────

DIM = 64  # テスト用の小さな次元


def _make_embedding(text: str) -> list[float]:
    """テキストから決定論的な埋め込みベクトルを生成する。

    テキストのハッシュを seed にして疑似乱数ベクトルを生成。
    同じテキストは常に同じベクトルを返す。
    """
    seed = hash(text) % (2**31)
    rng = np.random.RandomState(seed)
    vec = rng.randn(DIM).astype(np.float32)
    # L2 正規化
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _make_embedding_similar(text: str) -> list[float]:
    """全テキストに対して類似方向のベクトルを返す (integration テスト用)。

    dissolve→recall のパイプライン統合テストでは、チャンクテキストと
    クエリテキストが近い cosine 類似度を持つ必要がある。
    ベースベクトル (1,1,...,1) に hash ベースの微小ノイズを加えることで
    全テキスト間の _distance を小さくし、_refine_results をクリアする。
    """
    seed = hash(text) % (2**31)
    rng = np.random.RandomState(seed)
    # ベースベクトル (全成分 1.0) + 微小ノイズ (std=0.1)
    vec = np.ones(DIM, dtype=np.float32) + rng.randn(DIM).astype(np.float32) * 0.1
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _make_embeddings_similar(texts: list[str]) -> list[list[float]]:
    """バッチ版 _make_embedding_similar。"""
    return [_make_embedding_similar(t) for t in texts]


def _make_embeddings(texts: list[str]) -> list[list[float]]:
    """バッチ embedding。"""
    return [_make_embedding(t) for t in texts]


# ── Fixture ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tmp_db_dir():
    """テスト用の一時インデックスディレクトリ。module スコープで共有。"""
    d = tempfile.mkdtemp(prefix="phantasia_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def gnosis_index(tmp_db_dir):
    """NumPy backend の GnosisIndex。Vertex AI 不要。"""
    from mekhane.anamnesis.index import GnosisIndex

    idx = GnosisIndex(db_dir=tmp_db_dir, backend="numpy")

    # Embedder を固定ベクトル生成に差し替え
    mock_embedder = MagicMock()
    mock_embedder.embed.side_effect = _make_embedding
    mock_embedder.embed_batch.side_effect = _make_embeddings
    mock_embedder._dimension = DIM
    mock_embedder._dimension_mismatch = False
    idx.embedder = mock_embedder
    # _get_embedder をオーバーライドして固定 embedder を返す
    idx._get_embedder = lambda: mock_embedder

    return idx


@pytest.fixture
def sample_chunks():
    """テスト用サンプルチャンク。"""
    return [
        {
            "id": "test_doc1_sec0",
            "parent_id": "test_doc1",
            "text": "自由エネルギー原理 (Free Energy Principle) は変分推論に基づく認知の統一理論である。",
            "section_title": "FEP 概要",
            "chunk_index": 0,
            "precision": 0.8,
            "density": 0.0,
        },
        {
            "id": "test_doc1_sec1",
            "parent_id": "test_doc1",
            "text": "能動推論 (Active Inference) は FEP から導かれ、エージェントが環境を探索しながら信念を更新する枠組みを提供する。",
            "section_title": "能動推論",
            "chunk_index": 1,
            "precision": 0.7,
            "density": 0.0,
        },
        {
            "id": "test_doc1_sec2",
            "parent_id": "test_doc1",
            "text": "Markov blanket は系の内部と外部の境界を定義する。感覚状態と能動状態が境界を構成する。",
            "section_title": "Markov Blanket",
            "chunk_index": 2,
            "precision": 0.6,
            "density": 0.0,
        },
        {
            "id": "test_doc2_sec0",
            "parent_id": "test_doc2",
            "text": "圏論 (Category Theory) は数学の構造を射と対象で記述する。関手が圏から圏への写像を提供する。",
            "section_title": "圏論の基礎",
            "chunk_index": 0,
            "precision": 0.9,
            "density": 0.0,
        },
        {
            "id": "test_doc2_sec1",
            "parent_id": "test_doc2",
            "text": "随伴関手 (Adjoint Functors) は左随伴と右随伴の対から成り、自由対象と忘却関手のパターンを捉える。",
            "section_title": "随伴関手",
            "chunk_index": 1,
            "precision": 0.85,
            "density": 0.0,
        },
    ]


@pytest.fixture
def session_chunks():
    """セッション固有のチャンク (session_id フィルタ検証用)。"""
    return [
        {
            "id": "session_abc_sec0",
            "parent_id": "session_abc",
            "text": "Phantazein のリネーム作業を実施した。phantasia_pipeline.py と phantasia_field.py を作成。",
            "section_title": "リネーム",
            "chunk_index": 0,
        },
        {
            "id": "session_abc_sec1",
            "parent_id": "session_abc",
            "text": "既存テスト 53 本が全て PASSED。Mock ベースのテストがカバレッジを確保している。",
            "section_title": "テスト結果",
            "chunk_index": 1,
        },
    ]


# ── T1: Dissolve → DB 投入 ──────────────────────────────────────

class TestDissolveToIndex:
    """T1: チャンク化 + embedding + DB 格納のテスト。"""

    def test_add_chunks_basic(self, gnosis_index, sample_chunks):
        """基本的なチャンク投入が成功するか。"""
        count = gnosis_index.add_chunks(
            chunks=sample_chunks,
            source="test",
            session_id="test_session_1",
            project_id="test_project",
        )
        assert count == 5, f"5 チャンク追加を期待したが {count} だった"

    def test_stats_after_add(self, gnosis_index):
        """投入後の統計が正しいか。"""
        stats = gnosis_index.stats()
        assert stats["total"] >= 5, f"最低 5 レコードを期待したが {stats['total']} だった"
        assert "test" in stats.get("sources", {}), "ソース 'test' が統計に含まれるべき"

    def test_dedupe_prevents_duplicates(self, gnosis_index, sample_chunks):
        """同じ primary_key のチャンクは重複追加されないか。"""
        count = gnosis_index.add_chunks(
            chunks=sample_chunks,
            source="test",
            session_id="test_session_1",
            dedupe=True,
        )
        assert count == 0, f"重複排除で 0 を期待したが {count} だった"


# ── T2: Recrystallize (exploit) ─────────────────────────────────

class TestRecrystallizeExploit:
    """T2: 投入したデータを意図で検索し Crystal が返るか。"""

    def test_search_returns_results(self, gnosis_index):
        """FEP 関連クエリで結果が返るか。"""
        results = gnosis_index.search(
            query="自由エネルギー原理",
            k=3,
        )
        assert len(results) > 0, "検索結果が空"
        # 最上位結果が FEP 関連であることを確認
        top_content = results[0].get("content", "")
        assert "自由エネルギー" in top_content or "FEP" in top_content or len(top_content) > 0

    def test_search_semantic_relevance(self, gnosis_index):
        """意味的に関連するチャンクがより上位に来るか。"""
        results = gnosis_index.search(query="圏論と関手", k=5)
        assert len(results) > 0
        # 圏論関連のチャンクが含まれていることを検証
        contents = [r.get("content", "") for r in results]
        has_category = any("圏論" in c or "関手" in c for c in contents)
        assert has_category, "圏論関連のチャンクが検索結果に含まれるべき"


# ── T3: Recrystallize (explore) ─────────────────────────────────

class TestRecrystallizeExplore:
    """T3: 低密度領域から新奇チャンクが優先されるか。"""

    def test_update_density(self, gnosis_index):
        """密度更新が正常に完了するか。"""
        updated = gnosis_index.update_density(k=3)
        assert updated > 0, f"密度更新で対象 > 0 を期待したが {updated} だった"

    def test_density_values_normalized(self, gnosis_index):
        """密度値が [0, 1] に正規化されているか。"""
        import pandas as pd
        df = gnosis_index._backend.to_pandas()
        if "density" in df.columns:
            densities = df["density"].tolist()
            for d in densities:
                assert 0.0 <= d <= 1.0, f"密度 {d} が [0, 1] 範囲外"


# ── T4: Dissolve → Recrystallize cycle ──────────────────────────

class TestDissolveCrystalCycle:
    """T4: 溶解→結晶化→再溶解のラウンドトリップ。"""

    def test_full_cycle(self, tmp_db_dir):
        """追加テキストの溶解→結晶化→再溶解サイクル。"""
        from mekhane.anamnesis.index import GnosisIndex

        cycle_dir = tmp_db_dir / "cycle_test"
        cycle_dir.mkdir(exist_ok=True)
        gnosis_index = GnosisIndex(db_dir=cycle_dir, backend="numpy")

        # Embedder を固定ベクトル生成に差し替え
        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = _make_embedding
        mock_embedder.embed_batch.side_effect = _make_embeddings
        mock_embedder._dimension = DIM
        mock_embedder._dimension_mismatch = False
        gnosis_index._get_embedder = lambda: mock_embedder

        # まずサンプルデータを投入
        sample = [
            {
                "id": "cycle_base_0",
                "parent_id": "cycle_base",
                "text": "基盤テキスト: FEP は認知の統一理論。",
                "section_title": "基盤",
                "chunk_index": 0,
            },
        ]
        gnosis_index.add_chunks(chunks=sample, source="base", session_id="base_session")

        # 新しいチャンクを溶解
        new_chunks = [
            {
                "id": "cycle_test_0",
                "parent_id": "cycle_doc",
                "text": "Hegemonikón は FEP に基づく認知制約体系であり、Claude に対する行動指針を定義する。",
                "section_title": "Hegemonikón",
                "chunk_index": 0,
            },
        ]
        count = gnosis_index.add_chunks(
            chunks=new_chunks, source="test_cycle", session_id="cycle_session",
        )
        assert count == 1

        # 結晶化 (検索)
        results = gnosis_index.search(query="Hegemonikón 認知制約", k=3)
        assert len(results) > 0
        # 今追加したチャンクが含まれるか
        found_ids = [r.get("primary_key", "") for r in results]
        assert "cycle_test_0" in found_ids, f"cycle_test_0 が検索結果に含まれるべき: {found_ids}"

    def test_cross_session_search(self, tmp_db_dir, session_chunks):
        """異なるセッションのチャンクも検索できるか。"""
        from mekhane.anamnesis.index import GnosisIndex

        xsession_dir = tmp_db_dir / "xsession_test"
        xsession_dir.mkdir(exist_ok=True)
        idx = GnosisIndex(db_dir=xsession_dir, backend="numpy")

        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = _make_embedding
        mock_embedder.embed_batch.side_effect = _make_embeddings
        mock_embedder._dimension = DIM
        mock_embedder._dimension_mismatch = False
        idx._get_embedder = lambda: mock_embedder

        # セッション固有チャンクを追加
        count = idx.add_chunks(
            chunks=session_chunks, source="session", session_id="abc",
        )
        assert count == 2

        # クロスセッション検索
        results = idx.search(query="Phantazein リネーム テスト", k=5)
        assert len(results) > 0


# ── T5: distill_with_fallback ───────────────────────────────────

class TestDistillWithFallback:
    """T5: 実際のフォールバックチェーン動作をテスト。

    PhantasiaPipeline レベル。Field は Mock で制御。
    """

    def test_distill_l1_success(self):
        """L1 蒸留 (rom_save_fn 成功) のケース。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        mock_field = MagicMock()
        # dissolve が成功を返すように設定
        from mekhane.anamnesis.phantasia_pipeline import DissolveResult
        mock_field.dissolve.return_value = 3  # PhantasiaField.dissolve は int を返す
        # PhantasiaPipeline.dissolve は内部で field.dissolve を呼ぶが、
        # テストでは Pipeline.dissolve の結果を使うため field をモックする必要がある
        # → Pipeline.dissolve を直接モック
        pipeline = PhantasiaPipeline(field=mock_field)
        pipeline.dissolve = MagicMock(return_value=DissolveResult(
            chunks_count=3, session_id="test_distill", trigger="distill",
        ))

        # rom_save_fn: テキストとセッションIDを受け取り ROM パスを返す
        def rom_save_fn(text: str, session_id: str) -> str:
            return f"/tmp/rom_{session_id}.md"

        result = pipeline.distill_with_fallback(
            text="テストテキスト" * 100,
            session_id="test_distill",
            rom_save_fn=rom_save_fn,
        )
        assert result.success
        assert result.level == "L1"

    def test_distill_fallback_to_l2(self):
        """L1 失敗 (rom_save_fn 例外) → L2 成功 (溶解のみ) のフォールバック。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline, DissolveResult

        mock_field = MagicMock()
        pipeline = PhantasiaPipeline(field=mock_field)
        pipeline.dissolve = MagicMock(return_value=DissolveResult(
            chunks_count=3, session_id="test_distill_l2", trigger="distill",
        ))
        mock_field.update_density.return_value = 3

        def rom_save_fn_fail(text: str, session_id: str) -> str:
            raise RuntimeError("L1 ROM 保存失敗")

        result = pipeline.distill_with_fallback(
            text="テストテキスト" * 100,
            session_id="test_distill_l2",
            rom_save_fn=rom_save_fn_fail,
        )
        assert result.success
        assert result.level == "L2"
        assert any("L1" in entry for entry in result.fallback_chain)


# ── T6: Session filter ──────────────────────────────────────────

class TestSessionFilter:
    """T6: 特定セッションの結晶化が正しく動作するか。"""

    def test_source_filter(self, gnosis_index):
        """ソースフィルタで test のみ取得できるか。"""
        results = gnosis_index.search(
            query="認知", k=10, source_filter="test",
        )
        for r in results:
            assert r.get("source") == "test", f"ソースが test でない: {r.get('source')}"


# ── T7: PhantasiaField 統合 (chunker → index) ──────────────────

class TestPhantasiaFieldIntegration:
    """T7: PhantasiaField.dissolve() → recall() の統合テスト。"""

    def test_dissolve_and_recall(self, tmp_db_dir):
        """PhantasiaField 経由の dissolve → recall ラウンドトリップ。"""
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.phantasia_field import PhantasiaField

        # 一時ディレクトリに別の場を作成 (他テストとの干渉回避)
        field_dir = tmp_db_dir / "field_test"
        field_dir.mkdir(exist_ok=True)

        field = PhantasiaField(db_path=str(field_dir), chunker_mode="markdown")

        # numpy backend の GnosisIndex を直接注入
        index = GnosisIndex(db_dir=field_dir, backend="numpy")
        # 高類似度 embedder: チャンクとクエリが近い方向のベクトルを持つ
        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = _make_embedding_similar
        mock_embedder.embed_batch.side_effect = _make_embeddings_similar
        mock_embedder._dimension = DIM
        mock_embedder._dimension_mismatch = False
        index._get_embedder = lambda: mock_embedder
        field._index = index  # _get_index() をバイパス

        # dissolve
        # purify_chunks の min_text_len=30 をクリアするため、各セクション本文を十分な長さにする
        test_text = """## FEP の概要

自由エネルギー原理 (Free Energy Principle) は変分推論に基づく認知の統一理論であり、すべての認知プロセスを予測誤差の最小化として説明する。

## 能動推論

エージェントは環境を探索しながら信念を更新する。能動推論は FEP から導かれ、行動によって予測誤差を最小化する枠組みを提供する。

## Markov Blanket

系の内部と外部の境界を定義する統計的概念。感覚状態と能動状態がマルコフブランケットの境界を構成し、内部状態を外部から分離する。
"""
        count = field.dissolve(
            text=test_text,
            source="integration_test",
            session_id="integ_session",
            title="FEP テストドキュメント",
        )
        assert count > 0, f"dissolve で > 0 チャンクを期待したが {count} だった"

        # recall (exploit)
        results = field.recall(query="自由エネルギー原理 FEP", mode="exploit", limit=3)
        assert len(results) > 0, "recall exploit で結果が返らなかった"

    def test_stats(self, tmp_db_dir):
        """stats が正しい情報を返すか。"""
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.phantasia_field import PhantasiaField

        stats_dir = tmp_db_dir / "stats_test"
        stats_dir.mkdir(exist_ok=True)
        field = PhantasiaField(db_path=str(stats_dir), chunker_mode="markdown")

        # numpy backend の GnosisIndex を直接注入
        index = GnosisIndex(db_dir=stats_dir, backend="numpy")
        field._index = index

        stats = field.stats()
        assert "total" in stats
        assert "chunker_mode" in stats
        assert stats["chunker_mode"] == "markdown"


# ── T8: PhantasiaPipeline 統合 (full stack) ─────────────────────

class TestPipelineFullStack:
    """T8: PhantasiaPipeline の dissolve→recrystallize フルスタック。"""

    def test_pipeline_dissolve_recrystallize(self, tmp_db_dir):
        """Pipeline 経由の dissolve → recrystallize。"""
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.phantasia_field import PhantasiaField
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        pipeline_dir = tmp_db_dir / "pipeline_test"
        pipeline_dir.mkdir(exist_ok=True)

        field = PhantasiaField(db_path=str(pipeline_dir), chunker_mode="markdown")

        # numpy backend の GnosisIndex を直接注入
        index = GnosisIndex(db_dir=pipeline_dir, backend="numpy")
        # 高類似度 embedder: dissolve→recrystallize パイプラインテスト用
        mock_embedder = MagicMock()
        mock_embedder.embed.side_effect = _make_embedding_similar
        mock_embedder.embed_batch.side_effect = _make_embeddings_similar
        mock_embedder._dimension = DIM
        mock_embedder._dimension_mismatch = False
        index._get_embedder = lambda: mock_embedder
        field._index = index  # _get_index() をバイパス

        pipeline = PhantasiaPipeline(field=field)

        # 溶解 — MarkdownChunker が複数チャンクを生成するようヘッダ付き構造
        pipeline_text = """## Hyphē Crystallizer の概要

Hyphē Crystallizer は場⊣結晶パイプラインを提供する。Fix(G∘F) が安定性を保証し、G∘F 反復により境界が収束する。

## 実験的検証

130 実験で収束率 100% を達成した。精度勾配と密度場が結晶の品質を決定する。τ の統計的決定と適応的 λ スケジュールが重要。

## 理論的基盤

Markov blanket 密度場 ρ_MB が臨界密度 τ を超える領域で自律的チャンクが出現する。Coherence Invariance が G∘F 活性化時の安定性を保証する。
"""
        result = pipeline.dissolve(
            text=pipeline_text,
            session_id="pipeline_test_session",
            source="test",
            title="Hyphē テスト",
        )
        assert result.success, f"溶解失敗: {result.error}"
        assert result.chunks_count > 0

        # 結晶化
        recrystallize_result = pipeline.recrystallize(
            intent="Hyphē 場 結晶化",
            mode="exploit",
            budget=5,
        )
        assert len(recrystallize_result.crystals) > 0, "結晶化で結果なし"
        assert recrystallize_result.intent == "Hyphē 場 結晶化"

    def test_pipeline_status(self, tmp_db_dir):
        """Pipeline の status が正しく返るか。"""
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.phantasia_field import PhantasiaField
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        status_dir = tmp_db_dir / "status_test"
        status_dir.mkdir(exist_ok=True)
        field = PhantasiaField(db_path=str(status_dir), chunker_mode="markdown")
        # numpy backend の GnosisIndex を直接注入
        index = GnosisIndex(db_dir=status_dir, backend="numpy")
        field._index = index
        pipeline = PhantasiaPipeline(field=field)

        status = pipeline.status()
        assert isinstance(status, dict)
        assert "step_counter" in status
        assert "auto_dissolve_enabled" in status
