from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/ V-003 Context Rot MCP ツール
"""
Context Rot MCP Tools — セッションの Context Rot 健全度と蒸留を提供。

PURPOSE: Claude が自分の Context Rot 状態を照会し、/rom+ で蒸留を実行するための
MCP ツールを提供する。Ochema MCP サーバーに組み込んで使う。

ツール:
  - context_rot_status: 健全度を返す (green/yellow/orange/red)
  - context_rot_distill: 蒸留を実行し ROM ファイルを生成
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ROM 保存先
ROM_DIR = Path(os.getenv(
    "HGK_ROM_DIR",
    os.path.expanduser(
        "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
        "/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom"
    ),
))


# =============================================================================
# Tool: context_rot_status
# =============================================================================


# PURPOSE: セッションの Context Rot 健全度を返す
async def context_rot_status(
    cascade_id: str = "",
) -> dict[str, Any]:
    """現在のセッション Context Rot 状態を返す。

    Args:
        cascade_id: セッション ID (空なら全セッション一覧から最新を使用)

    Returns:
        step_count: int
        estimated_tokens: int
        health: "green" | "yellow" | "orange" | "red"
        recommendation: str
        rom_files: list[str]  (このセッション関連の ROM)
    """
    from mekhane.mcp.rom_distiller import assess_health

    step_count = 0
    estimated_tokens = 0

    # session_info から step 数を取得
    try:
        from mekhane.ochema.antigravity_client import AntigravityClient
        client = AntigravityClient()

        if cascade_id:
            info = client.session_info(cascade_id=cascade_id)
        else:
            info = client.session_info()

        # session_info の戻り値から step_count を抽出
        if isinstance(info, dict):
            if "sessions" in info:
                # 全セッション一覧 → 最新を使用
                sessions = info["sessions"]
                if sessions:
                    latest = sessions[0]
                    step_count = latest.get("step_count", 0)
                    cascade_id = latest.get("cascade_id", "")
            else:
                step_count = info.get("step_count", 0)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to get session info: %s", e)

    # 健全度判定
    health_info = assess_health(step_count)

    # ROM ファイル一覧 (今日の ROM)
    rom_files: list[str] = []
    if ROM_DIR.exists():
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        rom_files = sorted(
            [f.name for f in ROM_DIR.glob(f"rom_{today}_*.md")],
            reverse=True,
        )

    # Pre-Evacuation Notification: mandatory/critical で Sympatheia 自動通知
    urgency = health_info.get("evacuation_urgency", "none")
    notification_sent = False
    if urgency in ("mandatory", "critical"):
        try:
            notification_sent = await _send_evacuation_notification(
                health=health_info["health"],
                urgency=urgency,
                step_count=health_info["step_count"],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to send evacuation notification: %s", e)

    # CAG: キャッシュ健全度を統合
    cache_health: dict[str, Any] = {}
    try:
        from mekhane.ochema.cortex_cache import get_cache
        cache_health = get_cache().cache_health()
    except Exception as e:  # noqa: BLE001
        logger.debug("CortexCache health unavailable: %s", e)

    return {
        **health_info,
        "cascade_id": cascade_id,
        "estimated_tokens": estimated_tokens,
        "rom_files": rom_files,
        "notification_sent": notification_sent,
        "cache_health": cache_health,
    }


# =============================================================================
# Tool: context_rot_distill
# =============================================================================


# PURPOSE: 蒸留パイプラインを実行し ROM ファイルを生成する
async def context_rot_distill(
    cascade_id: str = "",
    topic: str = "",
    depth: str = "L3",
    context: str = "",
) -> dict[str, Any]:
    """セッション履歴を蒸留して ROM ファイルに保存する。

    /rom+ の実行エンジン。Phase 0-4 を自動実行する。

    Args:
        cascade_id: セッション ID
        topic: ROM のトピック名 (省略時は自動推定)
        depth: 蒸留深度 (L1=snapshot, L2=distilled, L3=rag_optimized)
        context: Claude が渡すセッションコンテキスト全文 (/rom+ 的な全量渡し)

    Returns:
        rom_path: str
        quality: dict
        health_after: dict
        summary: str
    """
    from mekhane.mcp.rom_distiller import run_distillation, extract_session, _conversation_to_text
    from mekhane.anamnesis.phantasia_field import PhantasiaField
    from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

    # context が渡された場合: LS 読取りではなく直接蒸留
    conversation: list[dict] | None = None
    if context:
        # context テキストを会話形式に変換
        conversation = [
            {"author": 2, "content": context},  # Model = 蒸留対象
        ]
        text_for_hyphe = context
    else:
        conversation = extract_session(cascade_id)
        text_for_hyphe = _conversation_to_text(conversation)

    # LLM ask_fn の準備 (Cortex Client)
    ask_fn = None
    try:
        from mekhane.ochema.cortex_client import CortexClient
        cortex = CortexClient(model="gemini-3-flash-preview", max_tokens=2048)

        def _ask(message: str, model: str = "gemini-3-flash-preview") -> str:
            response = cortex.chat(message=message, model=model, timeout=10.0)
            return response.text if response else ""

        ask_fn = _ask
    except Exception as e:  # noqa: BLE001
        logger.debug("CortexClient unavailable, using heuristic only: %s", e)

    # PhantasiaPipeline セットアップ (PhantazeinStore コールバック注入)
    try:
        field = PhantasiaField(chunker_mode="nucleator")
        # PhantazeinStore の record_dissolve をコールバックとして注入
        # 溶解イベントが SQLite に永続化される (GAP-2 統合)
        dissolve_callback = None
        try:
            from mekhane.symploke.phantazein_store import PhantazeinStore
            store = PhantazeinStore()
            dissolve_callback = store.record_dissolve
            logger.debug("PhantazeinStore コールバック注入: record_dissolve")
        except Exception as store_err:  # noqa: BLE001
            logger.warning(
                "PhantazeinStore 初期化失敗 (コールバックなしで続行): %s", store_err
            )
        pipeline = PhantasiaPipeline(field, on_dissolve=dissolve_callback)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to initialize PhantasiaPipeline: %s", e)
        raise RuntimeError(f"PhantasiaPipeline setup failed: {e}")

    # ===== Hyphē Precision Gate (CacheBlend HKVD 原理 — Dual Path) =====
    # 閾値: 実験的決定 (5セッション×64チャンク, Otsu/k-means/Percentile コンセンサス)
    THETA_HIGH = 0.67  # ≥ → high (KV cache reuse)
    THETA_LOW = 0.34   # < → low (full recomputation)

    # インライン classify_gate (precision_gate.py からの最小抽出)
    def _classify(precision: float) -> str:
        """precision → gate ラベル (high/mid/low)。"""
        if precision >= THETA_HIGH:
            return "high"
        elif precision < THETA_LOW:
            return "low"
        return "mid"

    try:
        from mekhane.anamnesis.phantasia_field import compute_precision_from_density

        # === Path A: Field Recall (embedding ベースの precision) ===
        # session のチャンクが field に溶解済みなら、density → precision を使う
        recalled = []
        if cascade_id:
            try:
                recalled = field.recall(
                    query=topic or "session context",
                    mode="exploit",
                    session_filter=cascade_id,
                    limit=200,
                )
            except Exception as e:  # noqa: BLE001
                logger.debug("Field recall failed (session=%s): %s", cascade_id, e)

        if recalled:
            # density ベースの precision (compute_precision_from_density は Hermite 補間)
            logger.info(
                "Hyphē Gate: Field Recall path — %d chunks with density-based precision",
                len(recalled),
            )
            processed_parts: list[str] = []
            gate_counts = {"high": 0, "mid": 0, "low": 0}

            for chunk in recalled:
                precision = chunk.get("precision", 0.5)
                gate = _classify(precision)
                gate_counts[gate] += 1
                chunk_txt = chunk.get("content", "")

                if gate == "high":
                    # KV cache reuse: そのまま保持
                    processed_parts.append(chunk_txt)
                elif gate == "mid":
                    # selective recomputation: 要約
                    if ask_fn and chunk_txt:
                        summary = ask_fn(
                            f"以下のテキストの核心部分を簡潔に要約してください:\n\n{chunk_txt}"
                        )
                        processed_parts.append(summary if summary else chunk_txt)
                    else:
                        processed_parts.append(chunk_txt)
                else:
                    # full recomputation: 再構成
                    if ask_fn and chunk_txt:
                        analysis = ask_fn(
                            f"以下のテキストの論理構造を整理し、暗黙の文脈を補完して再構成してください:\n\n{chunk_txt}"
                        )
                        processed_parts.append(analysis if analysis else chunk_txt)
                    else:
                        processed_parts.append(chunk_txt)

            text_for_hyphe = "\n\n".join(p for p in processed_parts if p)
            logger.info(
                "Hyphē Gate (Field): high=%d mid=%d low=%d",
                gate_counts["high"], gate_counts["mid"], gate_counts["low"],
            )

        else:
            # === Path B: ABPP v5 + Heuristic フォールバック (field データなし) ===
            chunker = field._get_chunker()
            try:
                chunks = chunker.chunk(text_for_hyphe, source_id="ctx_rot", title=topic)
            except TypeError:
                # MarkdownChunker フォールバック時の引数不一致を吸収
                chunks = chunker.chunk(text_for_hyphe, title=topic)

            if chunks:
                # ABPP v5 の利用可否を判定 (embedding ベースの高精度 precision)
                abpp_available = False
                abpp_fn = None
                try:
                    from hermeneus.src.precision_router import compute_abpp
                    abpp_fn = compute_abpp
                    abpp_available = True
                    logger.info(
                        "Hyphē Gate: ABPP v5 enabled — %d chunks with embedding-based precision",
                        len(chunks),
                    )
                except ImportError:
                    logger.debug("ABPP v5 not available, using heuristic fallback")

                processed_parts = []
                gate_counts = {"high": 0, "mid": 0, "low": 0}
                precision_source = "heuristic"  # ログ用: abpp or heuristic

                for c in chunks:
                    chunk_txt = c.get("text", c.get("content", ""))

                    # --- ABPP v5 (Path B-1): embedding ベースの precision ---
                    abpp_prec = None
                    if abpp_available and abpp_fn and chunk_txt:
                        try:
                            abpp_result = abpp_fn(chunk_txt)
                            # ABPPResult.ensemble は 0.0-1.0 に正規化済みの加重アンサンブル値
                            abpp_prec = abpp_result.ensemble
                            precision_source = "abpp"
                        except Exception as e:  # noqa: BLE001
                            logger.debug("ABPP compute failed for chunk, falling back: %s", e)

                    if abpp_prec is not None:
                        # ABPP 成功: embedding ベースの precision を使用
                        chunk_precision = abpp_prec
                    else:
                        # --- Heuristic (Path B-2): テキスト特徴量ベースの precision proxy ---
                        precision_source = "heuristic"
                        tokens = chunk_txt.split()
                        n_tokens = max(len(tokens), 1)
                        unique_ratio = len(set(tokens)) / n_tokens
                        lines = chunk_txt.split("\n")
                        has_structure = any(
                            ln.startswith("#") or ln.startswith("- ") or ln.startswith("```")
                            for ln in lines
                        )
                        # heuristic precision: 情報密度 × 構造性ボーナス × 長さペナルティ
                        # 短文 (< 30 tokens) は unique_ratio が artificially 高い → 抑制
                        length_factor = min(1.0, n_tokens / 30.0)
                        chunk_precision = unique_ratio * (1.15 if has_structure else 0.85) * length_factor
                        chunk_precision = max(0.0, min(1.0, chunk_precision))

                    gate = _classify(chunk_precision)
                    gate_counts[gate] += 1

                    if gate == "high":
                        # KV cache reuse: そのまま保持
                        processed_parts.append(chunk_txt)
                    elif gate == "mid":
                        # selective recomputation: 要約
                        if ask_fn and chunk_txt:
                            summary = ask_fn(
                                f"以下のテキストの核心部分を簡潔に要約してください:\n\n{chunk_txt}"
                            )
                            processed_parts.append(summary if summary else chunk_txt)
                        else:
                            processed_parts.append(chunk_txt)
                    else:
                        # full recomputation: 再構成
                        if ask_fn and chunk_txt:
                            analysis = ask_fn(
                                f"以下のテキストの論理構造を整理し、暗黙の文脈を補完して再構成してください:\n\n{chunk_txt}"
                            )
                            processed_parts.append(analysis if analysis else chunk_txt)
                        else:
                            processed_parts.append(chunk_txt)

                text_for_hyphe = "\n\n".join(p for p in processed_parts if p)
                logger.info(
                    "Hyphē Gate (%s): high=%d mid=%d low=%d",
                    precision_source.upper(), gate_counts["high"], gate_counts["mid"], gate_counts["low"],
                )

    except Exception as e:  # noqa: BLE001
        logger.warning("Hyphē Precision Gate failed, using raw text: %s", e)
    # ==========================================================

    # ROM 保存関数
    def rom_save_fn(txt: str, sid: str) -> str:
        # L1 のときは元の conversation を維持するが、L3 の場合はメタテキストを使う
        conv = [{"author": 1, "content": txt}] if txt != text_for_hyphe else conversation
        res = run_distillation(
            cascade_id=sid,
            topic=topic,
            depth=depth,
            conversation=conv,
            ask_fn=ask_fn,
        )
        if "error" in res:
            logger.warning("run_distillation error: %s", res["error"])
        return res.get("rom_path", "")

    # 3段フォールバック蒸留の実行 (depth=="L2" は溶解のみで ROM 生成不要)
    save_fn = rom_save_fn if depth in ("L1", "L3") else None

    result = pipeline.distill_with_fallback(
        text=text_for_hyphe,
        session_id=cascade_id,
        rom_save_fn=save_fn,
    )

    # CAG: キャッシュの TTL を延長 (セッション長時間化時のキャッシュ期限切れ防止)
    cache_extended = False
    try:
        from mekhane.ochema.cortex_cache import get_cache
        ctx_cache = get_cache()
        health = ctx_cache.cache_health()
        if health.get("active"):
            cache_extended = ctx_cache.extend_ttl()
            if cache_extended:
                logger.info("CAG TTL 延長完了 (/rom 連動)")
    except Exception as e:  # noqa: BLE001
        logger.debug("CAG TTL extension skipped: %s", e)

    # 戻り値を従来のディクショナリ形式に互換マッピング
    return {
        "success": result.success,
        "level_achieved": result.level,
        "rom_path": result.rom_path,
        "chunks_dissolved": result.chunks_dissolved,
        "fallback_chain": result.fallback_chain,
        "cache_extended": cache_extended,
        # 古いクライアント向けの互換キー
        "quality": {
            "quality_verdict": "PASS" if result.success else "FAIL",
            "quality_score": 5 if result.success else 0,
            "compression_ratio": 0.5,
        },
        "health_after": {
            "health": "green" if result.success else "red",
            "step_count": 5 if result.success else 99,
            "evacuation_urgency": "none",
        },
    }


# =============================================================================
# Pre-Evacuation Notification Helper
# =============================================================================


# PURPOSE: Sympatheia 通知システムにコンテキスト退避アラートを送信する
async def _send_evacuation_notification(
    health: str,
    urgency: str,
    step_count: int,
) -> bool:
    """Sympatheia の通知ファイルにコンテキスト退避アラートを書き込む。

    Sympatheia MCP サーバーを直接呼ぶのではなく (循環依存回避)、
    通知 JSONL ファイルに直接書き込む。

    Returns:
        True if notification was successfully written.
    """
    import json
    from datetime import datetime

    # Sympatheia 通知ファイルパス
    notifications_dir = Path(os.getenv(
        "HGK_SYMPATHEIA_DIR",
        os.path.expanduser(
            "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
            "/20_機構｜Mekhane/05_自律神経｜Sympatheia/state/"
        ),
    ))

    notifications_file = notifications_dir / "notifications.jsonl"

    level_map = {
        "mandatory": "HIGH",
        "critical": "CRITICAL",
    }

    notification = {
        "id": f"ctx_rot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "source": "context_rot",
        "level": level_map.get(urgency, "HIGH"),
        "title": f"⚠️ Context Rot: {health.upper()} ({urgency})",
        "body": (
            f"ステップ数 {step_count} — コンテキスト劣化が "
            f"{'危険水準' if urgency == 'critical' else '警戒水準'}に到達。\n"
            f"→ /rom+ を実行して重要情報を退避してください。"
            + (" /bye でセッション終了を推奨。" if urgency == "critical" else "")
        ),
        "dismissed": False,
    }

    try:
        notifications_dir.mkdir(parents=True, exist_ok=True)
        with open(notifications_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(notification, ensure_ascii=False) + "\n")
        logger.info("Evacuation notification sent: %s (%s)", health, urgency)
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to write notification: %s", e)
        return False
