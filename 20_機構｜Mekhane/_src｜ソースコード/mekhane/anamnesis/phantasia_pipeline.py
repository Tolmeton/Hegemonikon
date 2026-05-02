from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/phantasia_pipeline.py
"""PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 場⊣結晶パイプラインが必要
   → 溶解 (Dissolve) と結晶化 (Recrystallize) のオーケストレーションが必要
   → PhantasiaPipeline が統合パイプラインを提供
   → phantasia_pipeline.py が production 実装

Q.E.D.

---

PhantasiaPipeline — 場⊣結晶パイプライン (Dissolve ⇒ Recrystallize)

PURPOSE: Compaction を不要にするアーキテクチャ。
  セッションテキストを逐次溶解し、必要時に場から結晶化する。
  OpenClaw の summarizeWithFallback に相当する3段フォールバック蒸留も統合。

理論→実装マッピング:
  F: Source → Field (左随伴 = 溶解)     → dissolve() / auto_dissolve()
  G: Field → Crystal (右随伴 = 結晶化)  → recrystallize()
  Fix(G∘F): 溶解と結晶化の不動点        → 場の安定状態
  3段フォールバック:                     → distill_with_fallback()

依存:
  - mekhane.anamnesis.phantasia_field.PhantasiaField (場のファサード)
  - mekhane.anamnesis.chunker_nucleator (NucleatorChunker のアルゴリズム)
"""


import logging
import time
from dataclasses import dataclass, field as dc_field
from typing import Optional

log = logging.getLogger(__name__)


# ── データ構造 ──────────────────────────────────────────────────────

@dataclass
class DissolveResult:
    """溶解結果。"""
    chunks_count: int
    session_id: str
    trigger: str = "manual"
    elapsed_ms: float = 0.0
    error: str = ""

    @property
    def success(self) -> bool:
        return self.chunks_count > 0 and not self.error


@dataclass
class Crystal:
    """結晶化されたチャンク — recall 結果のラッパー。

    PhantasiaField.recall() の dict を型安全にラップする。
    """
    chunk_id: str
    content: str
    title: str = ""
    source: str = ""
    session_id: str = ""
    score: float = 0.0
    epistemic_value: float = 0.0
    pragmatic_value: float = 0.0
    metadata: dict = dc_field(default_factory=dict)

    @classmethod
    def from_recall_result(cls, result: dict) -> "Crystal":
        """PhantasiaField.recall() の結果 dict から Crystal を生成する。"""
        return cls(
            chunk_id=result.get("id", ""),
            content=result.get("content", ""),
            title=result.get("title", ""),
            source=result.get("source", ""),
            session_id=result.get("session_id", ""),
            score=result.get("_field_score", 0.0),
            epistemic_value=result.get("_epistemic_value", 0.0),
            pragmatic_value=result.get("_pragmatic_value", 0.0),
            metadata={
                k: v for k, v in result.items()
                if not k.startswith("_") and k not in {
                    "id", "content", "title", "source", "session_id",
                }
            },
        )


@dataclass
class RecrystallizeResult:
    """結晶化結果。"""
    crystals: list[Crystal]
    intent: str
    mode: str = "exploit"
    elapsed_ms: float = 0.0

    @property
    def total_tokens_estimate(self) -> int:
        """結晶化テキストの推定トークン数 (4文字/token 概算)。"""
        return sum(len(c.content) // 4 for c in self.crystals)


@dataclass
class DistillResult:
    """蒸留結果 (3段フォールバック)。"""
    level: str  # "L1" / "L2" / "L3"
    success: bool
    rom_path: str = ""
    chunks_dissolved: int = 0
    error: str = ""
    fallback_chain: list[str] = dc_field(default_factory=list)


# ── パイプライン本体 ─────────────────────────────────────────────────

class PhantasiaPipeline:
    """場⊣結晶パイプライン — Compaction を不要にする。

    linkage_hyphe.md §7: Field (場) から Chunk が Crystallize。

    Usage:
        from mekhane.anamnesis.phantasia_field import PhantasiaField
        field = PhantasiaField(chunker_mode="nucleator")
        pipeline = PhantasiaPipeline(field)

        # 溶解
        result = pipeline.dissolve("セッションテキスト...", session_id="abc")

        # 結晶化
        crystals = pipeline.recrystallize("FEP と能動推論")

        # 自動溶解 (セッション進行中)
        result = pipeline.auto_dissolve(steps, session_id="abc")
    """

    # PURPOSE: パイプラインの初期化
    def __init__(
        self,
        field: "PhantasiaField",
        auto_dissolve_interval: int = 20,
        auto_dissolve_enabled: bool = True,
        on_dissolve: "Callable[[str, int, int], None] | None" = None,
    ):
        """PhantasiaPipeline を初期化する。

        Args:
            field: PhantasiaField インスタンス (溶解・想起の実体)
            auto_dissolve_interval: 自動溶解の間隔 (ステップ数)
            auto_dissolve_enabled: 自動溶解を有効にするか
            on_dissolve: 溶解成功時のコールバック (session_id, chunk_count, total_chars)
        """
        self.field = field
        self.auto_dissolve_interval = auto_dissolve_interval
        self.auto_dissolve_enabled = auto_dissolve_enabled
        self._on_dissolve = on_dissolve
        self._step_counter: int = 0
        self._dissolved_sessions: set[str] = set()

    # PURPOSE: セッションテキストを場に溶解 (F: Source → Field)
    def dissolve(
        self,
        text: str,
        session_id: str = "",
        source: str = "session",
        title: str = "",
        trigger: str = "manual",
    ) -> DissolveResult:
        """テキストを場に溶解する。

        PhantasiaField.dissolve() に委譲し、結果をラップする。

        Args:
            text: 溶解するテキスト
            session_id: セッション ID
            source: データソース種別
            title: ドキュメントタイトル
            trigger: 溶解トリガー ("manual" / "interval" / "health")

        Returns:
            DissolveResult: 溶解結果
        """
        start = time.monotonic()

        try:
            count = self.field.dissolve(
                text=text,
                source=source,
                session_id=session_id,
                title=title,
            )

            elapsed = (time.monotonic() - start) * 1000

            if session_id:
                self._dissolved_sessions.add(session_id)

            log.info(
                f"[PhantasiaPipeline] 溶解完了: {count} chunks "
                f"(session={session_id}, trigger={trigger}, {elapsed:.0f}ms)"
            )

            # コールバック: PhantazeinStore 等の外部永続化に通知
            if self._on_dissolve is not None:
                try:
                    # total_chars の計算: 溶解対象のテキスト長
                    total_chars = len(text) if text else 0
                    self._on_dissolve(session_id or "", count, total_chars)
                except Exception as cb_err:  # noqa: BLE001
                    log.warning(
                        f"[PhantasiaPipeline] on_dissolve コールバック失敗: {cb_err}"
                    )

            return DissolveResult(
                chunks_count=count,
                session_id=session_id,
                trigger=trigger,
                elapsed_ms=round(elapsed, 1),
            )

        except Exception as e:  # noqa: BLE001
            elapsed = (time.monotonic() - start) * 1000
            log.error(f"[PhantasiaPipeline] 溶解失敗: {e}")
            return DissolveResult(
                chunks_count=0,
                session_id=session_id,
                trigger=trigger,
                elapsed_ms=round(elapsed, 1),
                error=str(e),
            )

    # PURPOSE: 場から意図に合致するチャンクを結晶化 (G: Field → Crystal)
    def recrystallize(
        self,
        intent: str,
        session_id: str = "",
        mode: str = "exploit",
        budget: int = 10,
    ) -> RecrystallizeResult:
        """場から意図に合致するチャンクを結晶化する。

        PhantasiaField.recall() に委譲し、結果を Crystal 形式でラップする。

        Args:
            intent: 何のために結晶化するか (検索クエリ)
            session_id: 特定セッションに限定 (空なら全場)
            mode: "exploit" (既知復元) / "explore" (新奇発見)
            budget: 結晶化するチャンク数上限 (コンテキスト予算)

        Returns:
            RecrystallizeResult: 結晶化結果
        """
        start = time.monotonic()

        results = self.field.recall(
            query=intent,
            mode=mode,
            limit=budget,
            session_filter=session_id or None,
        )

        crystals = [Crystal.from_recall_result(r) for r in results]
        elapsed = (time.monotonic() - start) * 1000

        log.info(
            f"[PhantasiaPipeline] 結晶化完了: {len(crystals)} crystals "
            f"(mode={mode}, {elapsed:.0f}ms)"
        )

        return RecrystallizeResult(
            crystals=crystals,
            intent=intent,
            mode=mode,
            elapsed_ms=round(elapsed, 1),
        )

    # PURPOSE: 自動溶解 — セッション進行中に N ステップごとに呼ばれる
    def auto_dissolve(
        self,
        steps: list[dict],
        session_id: str,
        trigger: str = "interval",
    ) -> Optional[DissolveResult]:
        """自動溶解 — ステップリストをテキストに変換して溶解する。

        auto_dissolve_interval ごとに自動実行される。
        trigger="health" の場合はインターバルに関係なく即時実行。

        Args:
            steps: ステップのリスト (各 dict に "text" キー)
            session_id: セッション ID
            trigger: 溶解トリガー ("interval" / "health" / "manual")

        Returns:
            DissolveResult or None (溶解スキップ時)
        """
        if not self.auto_dissolve_enabled and trigger != "health":
            return None

        self._step_counter += len(steps)

        # health トリガーは即時実行
        if trigger != "health":
            if self._step_counter < self.auto_dissolve_interval:
                return None

        # インターバルリセット
        self._step_counter = 0

        text = self._steps_to_text(steps)
        if not text.strip():
            return None

        return self.dissolve(
            text=text,
            session_id=session_id,
            source="session",
            trigger=trigger,
        )

    # PURPOSE: 3段フォールバック蒸留 (OpenClaw summarizeWithFallback 対応)
    def distill_with_fallback(
        self,
        text: str,
        session_id: str,
        rom_save_fn: Optional[callable] = None,
    ) -> DistillResult:
        """3段フォールバック蒸留。

        L1: 全文蒸留 → ROM ファイル生成 (rom_save_fn に委譲)
        L2: 場に溶解のみ (ROM なし、場で保持)
        L3: メタ情報のみ ROM (identifier 保持)

        Args:
            text: 蒸留するテキスト
            session_id: セッション ID
            rom_save_fn: ROM 保存関数 (text: str, session_id: str) -> str
                         返り値は保存パス。None の場合 L1 はスキップ。

        Returns:
            DistillResult: 蒸留結果
        """
        chain: list[str] = []

        # L1: 全文蒸留 → ROM 生成
        if rom_save_fn is not None:
            try:
                chain.append("L1:attempt")
                rom_path = rom_save_fn(text, session_id)
                chain.append("L1:success")

                # L1 成功時も場に溶解 (場の密度を維持)
                dissolve = self.dissolve(text, session_id, trigger="distill")

                return DistillResult(
                    level="L1",
                    success=True,
                    rom_path=rom_path,
                    chunks_dissolved=dissolve.chunks_count,
                    fallback_chain=chain,
                )
            except Exception as e:  # noqa: BLE001
                chain.append(f"L1:failed({e})")
                log.warning(f"[PhantasiaPipeline] L1 蒸留失敗: {e}")

        # L2: 場に溶解のみ (ROM なし)
        try:
            chain.append("L2:attempt")
            dissolve = self.dissolve(text, session_id, trigger="distill")

            if dissolve.success:
                chain.append("L2:success")

                # 密度更新
                try:
                    self.field.update_density()
                except Exception:  # noqa: BLE001
                    pass  # 密度更新失敗は致命的ではない

                return DistillResult(
                    level="L2",
                    success=True,
                    chunks_dissolved=dissolve.chunks_count,
                    fallback_chain=chain,
                )
            else:
                chain.append(f"L2:failed({dissolve.error})")

        except Exception as e:  # noqa: BLE001
            chain.append(f"L2:failed({e})")
            log.warning(f"[PhantasiaPipeline] L2 溶解失敗: {e}")

        # L3: メタ情報のみ ROM (identifier 保持)
        try:
            chain.append("L3:attempt")
            meta_text = self._extract_identifiers(text)

            if rom_save_fn is not None:
                rom_path = rom_save_fn(meta_text, session_id)
                chain.append("L3:success")
                return DistillResult(
                    level="L3",
                    success=True,
                    rom_path=rom_path,
                    fallback_chain=chain,
                )
            else:
                # rom_save_fn もない場合、メタ情報だけ溶解
                dissolve = self.dissolve(
                    meta_text, session_id,
                    source="meta",
                    trigger="distill",
                )
                chain.append("L3:success(dissolve_only)")
                return DistillResult(
                    level="L3",
                    success=dissolve.success,
                    chunks_dissolved=dissolve.chunks_count,
                    fallback_chain=chain,
                )

        except Exception as e:  # noqa: BLE001
            chain.append(f"L3:failed({e})")
            log.error(f"[PhantasiaPipeline] L3 蒸留失敗: {e}")

        # 全段階失敗
        return DistillResult(
            level="NONE",
            success=False,
            error="全段階の蒸留に失敗",
            fallback_chain=chain,
        )

    # PURPOSE: パイプラインの状態
    def status(self) -> dict:
        """パイプラインの現在状態を返す。"""
        field_health = self.field.health()
        return {
            "step_counter": self._step_counter,
            "auto_dissolve_interval": self.auto_dissolve_interval,
            "auto_dissolve_enabled": self.auto_dissolve_enabled,
            "dissolved_sessions": len(self._dissolved_sessions),
            "field": field_health,
        }

    # ── プライベートメソッド ───────────────────────────────────────────

    @staticmethod
    def _steps_to_text(steps: list[dict]) -> str:
        """ステップリストをテキストに変換する。"""
        parts = []
        for step in steps:
            text = step.get("text", "")
            if text.strip():
                parts.append(text.strip())
        return "\n\n".join(parts)

    @staticmethod
    def _extract_identifiers(text: str) -> str:
        """テキストから識別子 (UUID, パス, API 名) を抽出してメタ情報テキストを生成する。

        L3 フォールバック用: 最小限の情報を保持する。
        """
        import re

        identifiers: list[str] = []

        # UUID パターン
        uuids = re.findall(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            text, re.IGNORECASE,
        )
        for u in set(uuids):
            identifiers.append(f"UUID: {u}")

        # ファイルパス (/ で始まる)
        paths = re.findall(r'(/[\w./\-_\|｜]+(?:\.\w+)?)', text)
        for p in set(paths):
            if len(p) > 5:  # 短すぎるパスは除外
                identifiers.append(f"PATH: {p}")

        # API エンドポイント (http:// or https://)
        urls = re.findall(r'https?://[\w./\-_?&=]+', text)
        for u in set(urls):
            identifiers.append(f"URL: {u}")

        # セッション ID パターン
        session_ids = re.findall(r'session[_-]?[iI][dD]\s*[:=]\s*["\']?([^"\';\s,]+)', text)
        for sid in set(session_ids):
            identifiers.append(f"SESSION: {sid}")

        if not identifiers:
            # 識別子がない場合、冒頭 500 文字を保持
            return text[:500]

        header = f"# L3 メタ情報 (identifier 保持)\n\n元テキスト: {len(text)} 文字\n\n"
        return header + "\n".join(sorted(set(identifiers)))
