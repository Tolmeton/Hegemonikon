# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_cache.py CAG PoC — Gemini Context Caching
# PURPOSE: Gemini 公開 API の Context Caching 機能を透過的に提供する
from __future__ import annotations
from typing import Any, Optional
"""CortexCache — Gemini Context Caching via google-genai SDK.

Boot Context (Handoff + KI + Hóros) を KV キャッシュとして永続化し、
セッション中の LLM 呼出でキャッシュ済みコンテキストを透過的に利用する。

API エンドポイント: generativelanguage.googleapis.com (公開 API)
認証: GEMINI_API_KEY (環境変数)
先例: NoesisClient (mekhane/poiema/flow/noesis_client.py L69-71)

Usage:
    from mekhane.ochema.cortex_cache import CortexCache

    cache = CortexCache()
    name = cache.create_cache(
        contents="Boot Context テキスト...",
        display_name="hgk-boot-2026-03-15",
        ttl=3600,
    )
    response = cache.ask("質問", cache_name=name)

    # 冪等な Boot Cache
    name = cache.get_or_create_boot_cache(boot_text, ttl=3600)

    # Context Rot 連動
    health = cache.cache_health()
    # => {"active": True, "ttl_remaining": 2400, "display_name": "...", ...}
"""


import hashlib
import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# デフォルトモデル — Context Caching 対応
# NOTE: preview モデルは createCachedContent 未対応 (404)
# NOTE: gemini-2.0-flash-001 は generateContent で廃止 (2025-04)
DEFAULT_CACHE_MODEL = "gemini-2.5-flash"
# デフォルト TTL: 1 時間 (HGK セッションの典型長)
DEFAULT_TTL_SECONDS = 3600
# Passive Keep-Alive 閾値: TTL 残りがこの値未満なら自動延長
KEEP_ALIVE_THRESHOLD_SECONDS = 900  # 15 分
# キャッシュ最小トークン数 (Gemini の制約 — 2026-03 時点で 1024)
MIN_CACHE_TOKENS = 1024


@dataclass
class CacheInfo:
    """キャッシュのメタデータ。"""
    name: str           # キャッシュリソース名 (e.g. "cachedContents/abc123")
    display_name: str   # 人間可読名
    model: str          # モデル名
    create_time: str    # 作成時刻 (ISO 8601)
    expire_time: str    # 有効期限 (ISO 8601)
    content_hash: str   # コンテンツの SHA256 ハッシュ (先頭 16 文字)
    token_count: int    # キャッシュ済みトークン数


@dataclass
class CacheState:
    """CortexCache のインメモリ状態。"""
    active_cache: Optional[CacheInfo] = None
    created_at: float = 0.0    # time.time()
    ttl_seconds: int = DEFAULT_TTL_SECONDS  # 作成時に指定した TTL
    hit_count: int = 0
    miss_count: int = 0


# PURPOSE: Gemini Context Caching API のラッパー
class CortexCache:
    """Gemini Context Caching API ラッパー。

    google-genai SDK を使い、公開 Gemini API 経由で
    Context Caching を管理する。
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = DEFAULT_CACHE_MODEL,
    ):
        """初期化。

        Args:
            api_key: Gemini API キー。空なら環境変数 GEMINI_API_KEY を使用。
            model: キャッシュに使うモデル。
        """
        self.model = model
        self._state = CacheState()
        self._client = None

        resolved_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
        )
        if not resolved_key:
            logger.warning("CortexCache: GEMINI_API_KEY / GOOGLE_API_KEY が未設定。キャッシュ機能は無効。")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=resolved_key)
            logger.info("CortexCache: genai.Client 初期化完了 (model=%s)", model)
        except ImportError:
            logger.warning("CortexCache: google-genai がインストールされていません")
        except Exception as e:  # noqa: BLE001
            logger.error("CortexCache: 初期化失敗: %s", e)

    @property
    def is_available(self) -> bool:
        """キャッシュ機能が利用可能か。"""
        return self._client is not None

    # =========================================================================
    # キャッシュ CRUD
    # =========================================================================

    # PURPOSE: Gemini Context Cache を作成する
    def create_cache(
        self,
        contents: str,
        system_instruction: str = "",
        ttl: int = DEFAULT_TTL_SECONDS,
        display_name: str = "",
    ) -> CacheInfo:
        """コンテンツをキャッシュに登録。

        Args:
            contents: キャッシュするテキスト。
            system_instruction: システム指示 (キャッシュに含める)。
            ttl: TTL 秒数 (デフォルト 3600)。
            display_name: 人間可読な表示名。

        Returns:
            CacheInfo: 作成されたキャッシュのメタデータ。

        Raises:
            RuntimeError: API 未初期化のとき。
            Exception: API エラー。
        """
        if not self._client:
            raise RuntimeError("CortexCache が未初期化。GEMINI_API_KEY を確認してください。")

        from google.genai import types

        content_hash = hashlib.sha256(contents.encode()).hexdigest()[:16]

        # config に contents/display_name/ttl/system_instruction を全て格納
        # SDK: Caches.create(*, model, config) — contents はトップレベルではなく config 内
        config_kwargs: dict[str, Any] = {
            "contents": [types.Content(
                role="user",
                parts=[types.Part(text=contents)],
            )],
            "display_name": display_name or f"hgk-cache-{content_hash}",
            "ttl": f"{ttl}s",
        }

        # system_instruction がある場合は追加
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        cache = self._client.caches.create(
            model=self.model,
            config=types.CreateCachedContentConfig(**config_kwargs),
        )

        info = CacheInfo(
            name=cache.name,
            display_name=cache.display_name or "",
            model=cache.model or self.model,
            create_time=str(getattr(cache, "create_time", "")),
            expire_time=str(getattr(cache, "expire_time", "")),
            content_hash=content_hash,
            token_count=getattr(cache.usage_metadata, "total_token_count", 0)
            if hasattr(cache, "usage_metadata") and cache.usage_metadata
            else 0,
        )

        # インメモリ状態を更新
        self._state.active_cache = info
        self._state.created_at = time.time()
        self._state.ttl_seconds = ttl
        self._state.hit_count = 0

        logger.info(
            "CortexCache: キャッシュ作成完了 name=%s tokens=%d ttl=%ds",
            info.name, info.token_count, ttl,
        )
        return info

    # PURPOSE: 既存キャッシュを名前で取得する
    def get_cache(self, cache_name: str) -> Optional[CacheInfo]:
        """既存キャッシュを取得。

        Args:
            cache_name: キャッシュリソース名。

        Returns:
            CacheInfo or None if not found.
        """
        if not self._client:
            return None

        try:
            cache = self._client.caches.get(name=cache_name)
            return CacheInfo(
                name=cache.name,
                display_name=cache.display_name or "",
                model=cache.model or "",
                create_time=str(getattr(cache, "create_time", "")),
                expire_time=str(getattr(cache, "expire_time", "")),
                content_hash="",
                token_count=getattr(cache.usage_metadata, "total_token_count", 0)
                if hasattr(cache, "usage_metadata") and cache.usage_metadata
                else 0,
            )
        except Exception as e:  # noqa: BLE001
            logger.debug("CortexCache: キャッシュ取得失敗 %s: %s", cache_name, e)
            return None

    # PURPOSE: 全キャッシュの一覧を返す
    def list_caches(self) -> list[CacheInfo]:
        """全キャッシュの一覧を返す。"""
        if not self._client:
            return []

        try:
            caches = []
            for cache in self._client.caches.list():
                caches.append(CacheInfo(
                    name=cache.name,
                    display_name=cache.display_name or "",
                    model=cache.model or "",
                    create_time=str(getattr(cache, "create_time", "")),
                    expire_time=str(getattr(cache, "expire_time", "")),
                    content_hash="",
                    token_count=getattr(cache.usage_metadata, "total_token_count", 0)
                    if hasattr(cache, "usage_metadata") and cache.usage_metadata
                    else 0,
                ))
            return caches
        except Exception as e:  # noqa: BLE001
            logger.warning("CortexCache: キャッシュ一覧取得失敗: %s", e)
            return []

    # PURPOSE: キャッシュを削除する
    def delete_cache(self, cache_name: str) -> bool:
        """キャッシュを削除。

        Returns:
            True if deleted successfully.
        """
        if not self._client:
            return False

        try:
            self._client.caches.delete(name=cache_name)
            # インメモリ状態をクリア
            if self._state.active_cache and self._state.active_cache.name == cache_name:
                self._state.active_cache = None
            logger.info("CortexCache: キャッシュ削除 %s", cache_name)
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning("CortexCache: キャッシュ削除失敗 %s: %s", cache_name, e)
            return False

    # PURPOSE: TTL 残りが閾値未満かどうかを判定する (API 呼出なし)
    def should_extend_ttl(
        self,
        threshold: int = KEEP_ALIVE_THRESHOLD_SECONDS,
    ) -> bool:
        """TTL が閾値未満で延長が必要かどうかを判定。

        API を呼ばずインメモリ状態のみで判定するため、
        ``ask_cortex`` の度に呼んでも quota を消費しない。

        Args:
            threshold: 延長トリガー閾値 (秒)。デフォルト 900 (15分)。

        Returns:
            True なら延長が必要。
        """
        if not self._state.active_cache or not self._state.created_at:
            return False
        elapsed = time.time() - self._state.created_at
        remaining = self._state.ttl_seconds - elapsed
        return remaining < threshold

    # PURPOSE: 必要な場合のみ TTL を延長する (Passive Keep-Alive)
    def maybe_extend_ttl(
        self,
        threshold: int = KEEP_ALIVE_THRESHOLD_SECONDS,
        ttl: int = DEFAULT_TTL_SECONDS,
    ) -> bool:
        """TTL が閾値未満のときだけ ``extend_ttl`` を呼ぶ。

        ``ask_cortex`` の CAG ルートから応答返却後に 1 行で呼べる。
        閾値を超えていれば何もしない → API quota 節約。

        Args:
            threshold: 延長トリガー閾値 (秒)。
            ttl: 延長後の新 TTL (秒)。

        Returns:
            True なら延長を実行して成功。False なら延長不要または失敗。
        """
        if not self.should_extend_ttl(threshold):
            return False
        logger.info(
            "CortexCache: Passive Keep-Alive トリガー (TTL 残り < %ds)",
            threshold,
        )
        return self.extend_ttl(ttl=ttl)

    # PURPOSE: 既存キャッシュの TTL を延長する
    def extend_ttl(self, cache_name: str = "", ttl: int = DEFAULT_TTL_SECONDS) -> bool:
        """既存キャッシュの TTL を延長。

        Gemini API の caches.update() を呼び、TTL をリセットする。
        セッション長時間化時にキャッシュ期限切れを防止。

        Args:
            cache_name: キャッシュリソース名。空ならアクティブキャッシュ。
            ttl: 新しい TTL 秒数 (デフォルト 3600)。

        Returns:
            True if updated successfully.
        """
        if not self._client:
            return False

        resolved_name = cache_name
        if not resolved_name and self._state.active_cache:
            resolved_name = self._state.active_cache.name

        if not resolved_name:
            logger.warning("CortexCache: TTL 延長対象のキャッシュがありません")
            return False

        try:
            from google.genai import types
            self._client.caches.update(
                name=resolved_name,
                config=types.UpdateCachedContentConfig(ttl=f"{ttl}s"),
            )
            # インメモリ状態を更新
            self._state.created_at = time.time()
            self._state.ttl_seconds = ttl
            logger.info(
                "CortexCache: TTL 延長完了 name=%s ttl=%ds",
                resolved_name, ttl,
            )
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning("CortexCache: TTL 延長失敗 %s: %s", resolved_name, e)
            return False

    # =========================================================================
    # キャッシュ付き生成
    # =========================================================================

    # PURPOSE: キャッシュ済みコンテキストを使って LLM に質問する
    def ask(
        self,
        message: str,
        cache_name: str = "",
        max_tokens: int = 65536,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """キャッシュ済みコンテキストを使って質問。

        Args:
            message: ユーザのメッセージ。
            cache_name: キャッシュ名。空ならアクティブキャッシュを使用。
            max_tokens: 最大出力トークン数。
            temperature: 温度。

        Returns:
            dict with text, model, token_usage, cached.
        """
        if not self._client:
            raise RuntimeError("CortexCache が未初期化。")

        from google.genai import types

        # キャッシュ名の解決
        resolved_name = cache_name
        if not resolved_name and self._state.active_cache:
            resolved_name = self._state.active_cache.name

        if not resolved_name:
            raise ValueError("キャッシュ名が指定されておらず、アクティブキャッシュもありません。")

        response = self._client.models.generate_content(
            model=self.model,
            contents=message,
            config=types.GenerateContentConfig(
                cached_content=resolved_name,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        # 統計更新
        self._state.hit_count += 1

        # token usage の抽出
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", 0),
                "cached_tokens": getattr(um, "cached_content_token_count", 0),
                "completion_tokens": getattr(um, "candidates_token_count", 0),
                "total_tokens": getattr(um, "total_token_count", 0),
            }

        return {
            "text": response.text if response.text else "",
            "model": self.model,
            "token_usage": usage,
            "cached": True,
            "cache_name": resolved_name,
        }

    # =========================================================================
    # Boot Cache (冪等)
    # =========================================================================

    # PURPOSE: Boot Context 用のキャッシュを冪等に作成する
    def get_or_create_boot_cache(
        self,
        boot_text: str,
        system_instruction: str = "",
        ttl: int = DEFAULT_TTL_SECONDS,
    ) -> CacheInfo:
        """Boot Context のキャッシュを作成 (冪等)。

        同一コンテンツのハッシュが一致する場合はスキップ。

        Args:
            boot_text: Boot Context テキスト。
            system_instruction: システム指示。
            ttl: TTL 秒数。

        Returns:
            CacheInfo: キャッシュのメタデータ。
        """
        content_hash = hashlib.sha256(boot_text.encode()).hexdigest()[:16]

        # 同一ハッシュのキャッシュが既にアクティブなら再利用
        if (
            self._state.active_cache
            and self._state.active_cache.content_hash == content_hash
        ):
            logger.info("CortexCache: 同一ハッシュのキャッシュが存在 — 再利用 (%s)", content_hash)
            return self._state.active_cache

        # 既存キャッシュを検索 (display_name でマッチング)
        target_display = f"hgk-boot-{content_hash}"
        for existing in self.list_caches():
            if existing.display_name == target_display:
                logger.info("CortexCache: 既存 Boot Cache 発見 — 再利用 (%s)", existing.name)
                self._state.active_cache = existing
                self._state.active_cache.content_hash = content_hash
                self._state.created_at = time.time()
                return existing

        # 新規作成
        return self.create_cache(
            contents=boot_text,
            system_instruction=system_instruction,
            ttl=ttl,
            display_name=target_display,
        )

    # =========================================================================
    # Context Rot 連動: cache_health
    # =========================================================================

    # PURPOSE: キャッシュの健全度を返す (Context Rot 統合用)
    def cache_health(self) -> dict[str, Any]:
        """キャッシュの健全度を返す。

        Context Rot の `context_rot_status` に統合する。
        TTL 残り → Context Rot の補助指標として使う。

        Returns:
            dict with active, ttl_remaining, display_name, hit_count, etc.
        """
        if not self._state.active_cache:
            return {
                "active": False,
                "ttl_remaining": 0,
                "display_name": "",
                "hit_count": 0,
                "miss_count": 0,
                "token_count": 0,
            }

        # TTL 残り推定 (作成/延長時刻 + TTL - 現在)
        elapsed = time.time() - self._state.created_at if self._state.created_at else 0
        estimated_ttl = max(0, self._state.ttl_seconds - elapsed)

        return {
            "active": True,
            "cache_name": self._state.active_cache.name,
            "display_name": self._state.active_cache.display_name,
            "content_hash": self._state.active_cache.content_hash,
            "ttl_remaining": int(estimated_ttl),
            "hit_count": self._state.hit_count,
            "miss_count": self._state.miss_count,
            "token_count": self._state.active_cache.token_count,
            "model": self._state.active_cache.model,
        }


# =============================================================================
# シングルトン
# =============================================================================

_default_cache: Optional[CortexCache] = None


# PURPOSE: CortexCache のシングルトンを取得する
def get_cache() -> CortexCache:
    """CortexCache のシングルトンを取得。"""
    global _default_cache
    if _default_cache is None:
        _default_cache = CortexCache()
    return _default_cache


# =============================================================================
# CLI テストモード
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    cache = CortexCache()
    if not cache.is_available:
        print("❌ GEMINI_API_KEY が未設定。終了。")
        sys.exit(1)

    print("✅ CortexCache 初期化完了")

    # テストキャッシュ作成
    test_text = (
        "これは Hegemonikón Boot Context の CAG PoC テストです。\n"
        "Kalon = Fix(G∘F) — 発散と収束のサイクルの不動点。\n"
        "FEP = 変分自由エネルギー最小化。\n"
        "HGK 体系: 1 公理 + 7 座標 + 24 動詞 = 32 実体。\n"
        * 20  # 最小トークン数を超えるように繰り返し
    )

    print(f"\n📝 テストテキスト: {len(test_text)} 文字")
    print("🔧 Boot Cache 作成中...")

    try:
        info = cache.get_or_create_boot_cache(test_text, ttl=300)
        print(f"✅ キャッシュ作成完了: {info.name}")
        print(f"   tokens: {info.token_count}")
        print(f"   display: {info.display_name}")
        print(f"   hash: {info.content_hash}")

        # キャッシュ付き質問
        print("\n💬 キャッシュ付き質問...")
        result = cache.ask("Kalon の定義を簡潔に述べてください。")
        print(f"   応答: {result['text'][:200]}")
        print(f"   token usage: {result['token_usage']}")

        # cache_health
        health = cache.cache_health()
        print(f"\n🏥 Cache Health: {health}")

        # 冪等性テスト
        print("\n🔄 冪等性テスト (同一テキスト再登録)...")
        info2 = cache.get_or_create_boot_cache(test_text, ttl=300)
        assert info2.name == info.name, "冪等性違反！"
        print("✅ 冪等性確認: 同一キャッシュが再利用された")

        # クリーンアップ
        print("\n🗑️ テストキャッシュ削除...")
        cache.delete_cache(info.name)
        print("✅ 削除完了")

    except Exception as e:  # noqa: BLE001
        logger.debug("Ignored exception: %s", e)
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
