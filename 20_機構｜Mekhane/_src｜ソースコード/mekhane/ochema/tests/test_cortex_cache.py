# PROOF: [L2/テスト] <- mekhane/ochema/tests/test_cortex_cache.py CAG PoC テスト
# PURPOSE: CortexCache のスモークテスト + Context Rot 連動テスト
"""CortexCache smoke tests.

Requires: GEMINI_API_KEY environment variable (for real API tests).
Tests without API key will only verify initialization and error handling.

Run:
    cd ~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon && \
      PYTHONPATH=20_機構｜Mekhane/_src｜ソースコード \
      .venv/bin/python -m pytest \
      20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/tests/test_cortex_cache.py -v
"""

from __future__ import annotations
import os
import pytest
from unittest.mock import patch, MagicMock

from mekhane.ochema.cortex_cache import (
    CortexCache,
    CacheInfo,
    CacheState,
    get_cache,
    DEFAULT_CACHE_MODEL,
)


# API キーがあるか (GEMINI_API_KEY or GOOGLE_API_KEY)
HAS_API_KEY = bool(
    os.environ.get("GEMINI_API_KEY", "").strip()
    or os.environ.get("GOOGLE_API_KEY", "").strip()
)
skip_no_key = pytest.mark.skipif(not HAS_API_KEY, reason="GEMINI_API_KEY が未設定")


class TestCacheInit:
    """初期化テスト。"""

    def test_no_api_key_graceful(self):
        """API キーなしでもクラッシュしない。"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            cache = CortexCache(api_key="")
            assert not cache.is_available
            assert cache.cache_health()["active"] is False

    def test_with_api_key(self):
        """API キーありで初期化成功。"""
        if not HAS_API_KEY:
            pytest.skip("GEMINI_API_KEY が未設定")
        cache = CortexCache()
        assert cache.is_available

    def test_default_model(self):
        """デフォルトモデルが設定される。"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            cache = CortexCache(api_key="")
            assert cache.model == DEFAULT_CACHE_MODEL

    def test_singleton(self):
        """get_cache() はシングルトンを返す。"""
        # シングルトンをリセット
        import mekhane.ochema.cortex_cache as mod
        mod._default_cache = None
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2
        mod._default_cache = None  # クリーンアップ


class TestCacheHealth:
    """cache_health テスト (オフライン)。"""

    def test_inactive_health(self):
        """アクティブキャッシュなしの health。"""
        cache = CortexCache(api_key="")
        health = cache.cache_health()
        assert health["active"] is False
        assert health["ttl_remaining"] == 0
        assert health["hit_count"] == 0

    def test_active_health(self):
        """アクティブキャッシュありの health。"""
        cache = CortexCache(api_key="")
        # 手動で state を設定
        import time
        cache._state = CacheState(
            active_cache=CacheInfo(
                name="cachedContents/test",
                display_name="test-cache",
                model=DEFAULT_CACHE_MODEL,
                create_time="2026-03-15T00:00:00Z",
                expire_time="2026-03-15T01:00:00Z",
                content_hash="abc123",
                token_count=5000,
            ),
            created_at=time.time() - 600,  # 10 分前
            hit_count=3,
            miss_count=1,
        )
        health = cache.cache_health()
        assert health["active"] is True
        assert health["hit_count"] == 3
        assert health["token_count"] == 5000
        assert health["ttl_remaining"] > 0
        assert health["display_name"] == "test-cache"


class TestCacheCreate:
    """キャッシュ作成テスト (実 API)。"""

    @skip_no_key
    def test_create_and_delete(self):
        """キャッシュ作成 + 削除の往復テスト。"""
        cache = CortexCache()

        # 最小トークン数 (4096) を超えるテキスト
        test_text = "HGK Boot Context テスト。Kalon = Fix(G∘F)。FEP = 自由エネルギー原理。32実体体系。\n" * 500

        info = cache.create_cache(
            contents=test_text,
            display_name="hgk-test-ephemeral",
            ttl=60,  # 1 分 (テスト用最短)
        )
        assert info.name.startswith("cachedContents/")
        assert info.token_count > 0

        # クリーンアップ
        deleted = cache.delete_cache(info.name)
        assert deleted

    @skip_no_key
    def test_list_caches(self):
        """キャッシュ一覧の取得。"""
        cache = CortexCache()
        caches = cache.list_caches()
        assert isinstance(caches, list)


class TestIdempotent:
    """冪等性テスト。"""

    def test_same_hash_skips_creation(self):
        """同一ハッシュのキャッシュは再作成しない (インメモリ)。"""
        cache = CortexCache(api_key="")
        # 手動で state を設定
        cache._state.active_cache = CacheInfo(
            name="cachedContents/existing",
            display_name="hgk-boot-abc123",
            model=DEFAULT_CACHE_MODEL,
            create_time="",
            expire_time="",
            content_hash="",
            token_count=5000,
        )

        import hashlib
        test_text = "test content"
        expected_hash = hashlib.sha256(test_text.encode()).hexdigest()[:16]
        cache._state.active_cache.content_hash = expected_hash

        # API は呼ばれないはず (client=None でも成功する)
        result = cache.get_or_create_boot_cache(test_text)
        assert result.name == "cachedContents/existing"


class TestAskWithCache:
    """キャッシュ付き質問テスト (実 API)。"""

    @skip_no_key
    def test_ask_with_cache(self):
        """キャッシュ付き質問で応答を取得。"""
        cache = CortexCache()
        test_text = "HGK 体系の公理 (Axiom): FEP = 自由エネルギー原理。Kalon = Fix(G∘F) 不動点。\n" * 500

        info = cache.create_cache(
            contents=test_text,
            display_name="hgk-test-ask",
            ttl=60,
        )

        try:
            result = cache.ask("FEP の正式名称は？", cache_name=info.name)
            assert len(result["text"]) > 0
            assert result["cached"] is True
            assert "token_usage" in result
        finally:
            cache.delete_cache(info.name)

    def test_ask_no_cache_raises(self):
        """キャッシュなしで質問するとエラー。"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            cache = CortexCache(api_key="")
            with pytest.raises(RuntimeError):
                cache.ask("質問")


class TestExtendTTL:
    """TTL 延長テスト。"""

    def test_extend_ttl_no_client(self):
        """未初期化時は False を返す。"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            cache = CortexCache(api_key="")
            assert cache.extend_ttl() is False

    def test_extend_ttl_no_active_cache(self):
        """アクティブキャッシュなしで cache_name も空なら False。"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            cache = CortexCache(api_key="")
            # client はないが、ロジックのテスト用に手動設定
            cache._client = MagicMock()
            result = cache.extend_ttl(cache_name="", ttl=3600)
            assert result is False

    @skip_no_key
    def test_extend_ttl_real_api(self):
        """実 API での TTL 延長テスト。"""
        cache = CortexCache()
        test_text = "HGK Boot Context テスト。Kalon = Fix(G∘F)。FEP = 自由エネルギー原理。32実体体系。\n" * 500

        info = cache.create_cache(
            contents=test_text,
            display_name="hgk-test-extend-ttl",
            ttl=300,  # 5分
        )

        try:
            # TTL を延長
            result = cache.extend_ttl(cache_name=info.name, ttl=600)
            assert result is True
            # インメモリ状態が更新されている
            assert cache._state.ttl_seconds == 600
        finally:
            cache.delete_cache(info.name)

    def test_ttl_seconds_tracked_in_state(self):
        """create_cache で ttl_seconds が CacheState に記録される。"""
        import time
        cache = CortexCache(api_key="")
        cache._state = CacheState(
            active_cache=CacheInfo(
                name="cachedContents/test",
                display_name="test",
                model=DEFAULT_CACHE_MODEL,
                create_time="",
                expire_time="",
                content_hash="abc123",
                token_count=5000,
            ),
            created_at=time.time() - 600,
            ttl_seconds=1800,  # 30分
            hit_count=0,
            miss_count=0,
        )
        health = cache.cache_health()
        # 1800 - 600 = 1200 (±数秒)
        assert 1100 < health["ttl_remaining"] < 1300


class TestPassiveKeepAlive:
    """Passive Keep-Alive (should_extend_ttl / maybe_extend_ttl) のテスト。"""

    def test_should_extend_no_cache(self):
        """アクティブキャッシュなし → False."""
        cache = CortexCache(api_key="")
        assert cache.should_extend_ttl() is False

    def test_should_extend_ttl_sufficient(self):
        """TTL 残り十分 (> 閾値) → False."""
        import time
        cache = CortexCache(api_key="")
        cache._state = CacheState(
            active_cache=CacheInfo(
                name="cachedContents/test",
                display_name="test",
                model=DEFAULT_CACHE_MODEL,
                create_time="",
                expire_time="",
                content_hash="abc123",
                token_count=5000,
            ),
            created_at=time.time() - 60,  # 60秒前に作成
            ttl_seconds=3600,  # TTL=1h → 残り ~3540s >> 900s
        )
        assert cache.should_extend_ttl() is False

    def test_should_extend_ttl_low(self):
        """TTL 残りが閾値未満 → True."""
        import time
        cache = CortexCache(api_key="")
        cache._state = CacheState(
            active_cache=CacheInfo(
                name="cachedContents/test",
                display_name="test",
                model=DEFAULT_CACHE_MODEL,
                create_time="",
                expire_time="",
                content_hash="abc123",
                token_count=5000,
            ),
            created_at=time.time() - 3000,  # 50分前 → 残り ~600s < 900s
            ttl_seconds=3600,
        )
        assert cache.should_extend_ttl() is True

    def test_maybe_extend_no_client(self):
        """クライアントなし → should_extend=True でも extend_ttl=False."""
        import time
        cache = CortexCache(api_key="")
        cache._state = CacheState(
            active_cache=CacheInfo(
                name="cachedContents/test",
                display_name="test",
                model=DEFAULT_CACHE_MODEL,
                create_time="",
                expire_time="",
                content_hash="abc123",
                token_count=5000,
            ),
            created_at=time.time() - 3000,
            ttl_seconds=3600,
        )
        # should_extend は True だが、client がないので extend_ttl が False
        assert cache.should_extend_ttl() is True
        assert cache.maybe_extend_ttl() is False
