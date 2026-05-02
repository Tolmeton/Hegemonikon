from __future__ import annotations
# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/pks/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 能動的知識表面化には操作インターフェースが必要
→ pks_cli.py が担う

# PURPOSE: PKS v2 CLI — 能動的知識プッシュの対話インターフェース
"""


import argparse
import sys
from pathlib import Path
from mekhane.paths import MNEME_DIR

_PKS_DIR = Path(__file__).resolve().parent
_MEKHANE_DIR = _PKS_DIR.parent
_HEGEMONIKON_ROOT = _MEKHANE_DIR.parent

if str(_HEGEMONIKON_ROOT) not in sys.path:
    sys.path.insert(0, str(_HEGEMONIKON_ROOT))

# --- Path constants (一元管理) ---
MNEME_ROOT = MNEME_DIR
INDICES_DIR = MNEME_ROOT / "indices"
SESSIONS_DIR = MNEME_ROOT / "sessions"


# PURPOSE: SelfAdvocate 一人称メッセージを出力するヘルパー
def _print_advocacy(nuggets, engine) -> None:
    """SelfAdvocate で論文一人称メッセージを生成・出力"""
    try:
        from mekhane.pks.self_advocate import SelfAdvocate
    except ImportError:
        print("\n⚠️ SelfAdvocate が利用できません。")
        return

    advocate = SelfAdvocate()
    context = engine.tracker.context if hasattr(engine, 'tracker') else None

    advocacies = advocate.generate_batch(nuggets, context)
    if advocacies:
        report = advocate.format_report(advocacies)
        print("\n" + report)
    else:
        print("\n📭 Advocacy メッセージの生成に失敗しました。")


# PURPOSE: `pks stats` — 知識基盤の全体統計を表示
def cmd_stats(args: argparse.Namespace) -> None:
    """知識基盤 (Mnēmē + Gnōsis + PKS) の統計ダッシュボード"""
    import os
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(key, None)
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

    print("## 📊 PKS Knowledge Stats\n")

    # --- Gnōsis ---
    gnosis_count = 0
    try:
        from mekhane.anamnesis.index import GnosisIndex as AnamnesisGnosisIndex
        gi = AnamnesisGnosisIndex()
        stats = gi.stats()
        gnosis_count = stats.get('total', stats.get('total_papers', 0))
    except Exception:  # noqa: BLE001
        pass

    # --- Mnēmē indices ---
    indices_dir = INDICES_DIR
    kairos_count = 0
    sophia_count = 0
    chronos_count = 0
    if indices_dir.exists():
        for name in ["kairos", "sophia", "chronos"]:
            pkl = indices_dir / f"{name}.pkl"
            if pkl.exists():
                try:
                    from mekhane.symploke.adapters.vector_store import VectorStore
                    adapter = VectorStore()
                    adapter.load(str(pkl))
                    count = adapter.count()
                    if name == "kairos":
                        kairos_count = count
                    elif name == "sophia":
                        sophia_count = count
                    else:
                        chronos_count = count
                except Exception:  # noqa: BLE001
                    pass

    # --- Handoffs ---
    handoff_dir = SESSIONS_DIR
    handoff_count = len(list(handoff_dir.glob("handoff_20??-??-??_????.md"))) if handoff_dir.exists() else 0

    # --- KI (Knowledge Items) ---
    ki_dir = Path.home() / ".gemini" / "antigravity" / "knowledge"
    ki_count = len(list(ki_dir.glob("*.md"))) if ki_dir.exists() else 0

    # --- Cooldown ---
    cooldown = os.environ.get("PKS_COOLDOWN_HOURS", "24.0")

    # --- Gateway (v4) ---
    gw_stats = {}
    try:
        from mekhane.pks.gateway_bridge import GatewayBridge
        gw = GatewayBridge()
        gw_stats = gw.stats()
    except Exception:  # noqa: BLE001
        pass

    # --- Output ---
    total = gnosis_count + kairos_count + sophia_count + chronos_count
    print("| ソース | 件数 | 備考 |")
    print("|:-------|-----:|:-----|")
    print(f"| 🔬 Gnōsis | **{gnosis_count:,}** | 論文・外部知識 |")
    print(f"| 📋 Kairos (.pkl) | **{kairos_count:,}** | Handoff + 会話ログ |")
    print(f"| 📖 Sophia (.pkl) | **{sophia_count:,}** | Knowledge Items |")
    print(f"| 🕐 Chronos (.pkl) | **{chronos_count:,}** | 時系列チャット履歴 |")
    print(f"| **合計** | **{total:,}** | |")
    print()
    print(f"📁 Handoff ファイル: **{handoff_count}** 件")
    print(f"📁 KI ファイル: **{ki_count}** 件")
    print(f"⏱️ クールダウン: **{cooldown}** 時間 (`PKS_COOLDOWN_HOURS`)")

    # v4: Gateway ソース統計
    if gw_stats:
        print()
        print("### 🌉 Gateway ソース (v4)")
        print("| ソース | 件数 | ディレクトリ |")
        print("|:-------|-----:|:------------|")
        for name in ["ideas", "doxa", "handoff", "ki"]:
            info = gw_stats.get(name, {})
            cnt = info.get("count", 0)
            directory = info.get("directory", "N/A")
            exists = "✅" if info.get("exists", False) else "❌"
            print(f"| {exists} {name} | **{cnt}** | `{directory}` |")
    print()


# PURPOSE: `pks health` — Autophōnos 全スタックのヘルスチェック
def cmd_health(args: argparse.Namespace) -> None:
    """Autophōnos 全コンポーネントの一括検証"""
    import os, time
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(key, None)
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

    print("## 🏥 Autophōnos Health Check\n")
    checks = []

    # PURPOSE: [L2-auto] _check の関数定義
    def _check(name: str, fn):
        t0 = time.time()
        try:
            result = fn()
            elapsed = time.time() - t0
            checks.append((name, "✅", result, f"{elapsed:.1f}s"))
        except Exception as e:  # noqa: BLE001
            elapsed = time.time() - t0
            checks.append((name, "❌", str(e)[:60], f"{elapsed:.1f}s"))

    # 1. Gnōsis
    # PURPOSE: Gnōsis の疎通を確認
    def check_gnosis():
        from mekhane.anamnesis.index import GnosisIndex as AI
        gi = AI()
        s = gi.stats()
        return f"{s.get('total', 0):,} docs"
    _check("Gnōsis", check_gnosis)

    # 2. Kairos index
    # PURPOSE: Kairos .pkl インデックスの存在と読込を確認
    def check_kairos():
        pkl = INDICES_DIR / "kairos.pkl"
        if not pkl.exists():
            raise FileNotFoundError("kairos.pkl not found")
        from mekhane.symploke.adapters.vector_store import VectorStore
        a = VectorStore(); a.load(str(pkl))
        return f"{a.count():,} docs"
    _check("Kairos (.pkl)", check_kairos)

    # 3. Sophia index
    # PURPOSE: Sophia .pkl インデックスの存在と読込を確認
    def check_sophia():
        pkl = INDICES_DIR / "sophia.pkl"
        if not pkl.exists():
            raise FileNotFoundError("sophia.pkl not found")
        from mekhane.symploke.adapters.vector_store import VectorStore
        a = VectorStore(); a.load(str(pkl))
        return f"{a.count():,} docs"
    _check("Sophia (.pkl)", check_sophia)

    # 4. Embedder
    # PURPOSE: embedder_factory の動作を確認
    def check_embedder():
        from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension
        embed_fn = get_embed_fn()
        v = embed_fn("test query")
        return f"dim={len(v)}"
    _check("Embedder", check_embedder)

    # 5. GnosisBridge
    # PURPOSE: Gnōsis-Lance 間のブリッジ検索を確認
    def check_bridge():
        from mekhane.symploke.indices.gnosis_bridge import GnosisBridge
        b = GnosisBridge()
        r = b.search("active inference", k=1)
        return f"{len(r)} results, score={r[0].score:.3f}" if r else "0 results"
    _check("GnosisBridge", check_bridge)

    # 6. PKSEngine
    # PURPOSE: PKSEngine の基本プッシュ機能を確認
    def check_engine():
        from mekhane.pks.pks_engine import PKSEngine
        e = PKSEngine(enable_questions=False, enable_serendipity=False)
        e.set_context(topics=["FEP"])
        n = e.proactive_push(k=3)
        return f"{len(n)} nuggets"
    _check("PKSEngine", check_engine)

    # 7. TopicExtractor
    # PURPOSE: Handoff からのトピック自動抽出を確認
    def check_topics():
        from mekhane.pks.pks_engine import PKSEngine
        e = PKSEngine(enable_questions=False)
        t = e.auto_context_from_handoff()
        return f"{len(t)} topics: {', '.join(t[:3])}"
    _check("TopicExtractor", check_topics)

    # 8. SelfAdvocate
    # PURPOSE: SelfAdvocate の初期化と LLM 状態を確認
    def check_advocate():
        from mekhane.pks.self_advocate import SelfAdvocate
        a = SelfAdvocate()
        return f"LLM={'ok' if a.llm_available else 'template mode'}"
    _check("SelfAdvocate", check_advocate)

    # 9. Chronos index
    # PURPOSE: Chronos .pkl インデックスの存在と読込を確認
    def check_chronos():
        pkl = INDICES_DIR / "chronos.pkl"
        if not pkl.exists():
            raise FileNotFoundError("chronos.pkl not found")
        from mekhane.symploke.adapters.vector_store import VectorStore
        a = VectorStore(); a.load(str(pkl))
        return f"{a.count():,} docs"
    _check("Chronos (.pkl)", check_chronos)

    # Output
    print("| コンポーネント | 状態 | 詳細 | 時間 |")
    print("|:--------------|:----:|:-----|-----:|")
    ok = 0
    for name, status, detail, elapsed in checks:
        print(f"| {name} | {status} | {detail} | {elapsed} |")
        if status == "✅":
            ok += 1
    print()
    total = len(checks)
    print(f"**結果: {ok}/{total} OK** {'🎉' if ok == total else '⚠️'}")
    print()


# PURPOSE: `pks search` — 全インデックス横断検索 (ソース間スコア正規化付き)
def cmd_search(args: argparse.Namespace) -> None:
    """Gnōsis, Kairos, Sophia, Chronos を横断検索

    各ソースの生スコアをソース内 min-max 正規化で [0,1] に統一し、
    異なるスコアスケール (L2距離 vs cosine) の問題を解消する。
    """
    import os, time
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(key, None)
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

    query = args.query
    k = args.k
    sources = args.sources.split(",") if args.sources else ["gnosis", "kairos", "sophia", "chronos"]

    print(f"## 🔎 PKS Search: \"{query}\"\n")
    t0 = time.time()

    # Source icons
    icons = {"gnosis": "🔬", "kairos": "📋", "sophia": "📖", "chronos": "🕐"}

    # Collect results per source (for per-source normalization)
    results_by_source: dict[str, list[tuple[str, float, str, str]]] = {}

    # 1. Gnōsis
    if "gnosis" in sources:
        try:
            from mekhane.anamnesis.index import GnosisIndex as AI
            gi = AI()
            results = gi.search(query, k=k)
            gnosis_results = []
            for r in results:
                title = r.get("title", r.get("primary_key", "?"))
                dist = float(r.get("_distance", 1.0))
                # L2 distance → raw similarity
                score = max(0.0, min(1.0, 1.0 - dist / 2.0))
                snippet = r.get("abstract", r.get("content", ""))[:120]
                gnosis_results.append(("gnosis", score, title, snippet))
            if gnosis_results:
                results_by_source["gnosis"] = gnosis_results
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ Gnōsis: {e}")

    # 2-4. pkl indices (Kairos, Sophia, Chronos)
    indices_dir = INDICES_DIR
    pkl_names = [n for n in ["kairos", "sophia", "chronos"] if n in sources]

    if pkl_names:
        try:
            from mekhane.symploke.adapters.vector_store import VectorStore
            from mekhane.symploke.embedder_factory import get_embed_fn
            embed_fn = get_embed_fn()
            query_vec = embed_fn(query)

            for name in pkl_names:
                pkl = indices_dir / f"{name}.pkl"
                if not pkl.exists():
                    continue
                try:
                    idx = VectorStore()
                    idx.load(str(pkl))
                    hits = idx.search(query_vec, k=k)
                    src_results = []
                    for hit in hits:
                        meta = hit.metadata if hasattr(hit, 'metadata') else {}
                        doc_id = meta.get("doc_id", meta.get("title", str(hit.id)))
                        score = hit.score if hasattr(hit, 'score') else 0
                        title = meta.get("title", doc_id)
                        src_results.append((name, score, title, ""))
                    if src_results:
                        results_by_source[name] = src_results
                except Exception as e:  # noqa: BLE001
                    print(f"  ⚠️ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ Embedder: {e}")

    elapsed = time.time() - t0

    # Max-ratio normalization: divide each score by its source's max score
    # This preserves relative ordering within sources while scaling across sources
    # gnosis max ~0.75 → 1.0, kairos max ~0.11 → 1.0, etc.
    all_results = []
    for src, src_results in results_by_source.items():
        src_max = max(s for _, s, _, _ in src_results)
        if src_max <= 0:
            continue
        for src_name, raw_score, title, snippet in src_results:
            normalized = raw_score / src_max
            all_results.append((src_name, normalized, raw_score, title, snippet))

    # Hybrid reranking: keyword boost on top of vector similarity
    # Tokenize query into keywords (min 2 chars), compute hit ratio, add bonus
    import re
    query_tokens = [t.lower() for t in re.split(r'[\s　,、。・/]+', query) if len(t) >= 2]
    KW_BOOST_MAX = 0.3  # max boost for 100% keyword match

    for i, (src, norm_score, raw_score, title, snippet) in enumerate(all_results):
        if query_tokens:
            text = (title + " " + snippet).lower()
            hits = sum(1 for t in query_tokens if t in text)
            kw_ratio = hits / len(query_tokens)
            boost = kw_ratio * KW_BOOST_MAX
            all_results[i] = (src, norm_score + boost, raw_score, title, snippet)

    # Sort by boosted score descending
    all_results.sort(key=lambda x: x[1], reverse=True)

    if not all_results:
        print("📭 結果が見つかりませんでした。")
        return

    # Display top results
    top = all_results[:k]
    print(f"| # | ソース | スコア | 生スコア | タイトル / ID | スニペット |")
    print(f"|--:|:-------|-------:|--------:|:--------------|:-----------|")
    for i, (src, norm_score, raw_score, title, snippet) in enumerate(top, 1):
        icon = icons.get(src, "📦")
        title_short = title[:40] + "…" if len(title) > 40 else title
        snippet_short = snippet.replace("\n", " ")[:60]
        print(f"| {i} | {icon} {src} | {norm_score:.3f} | {raw_score:.3f} | {title_short} | {snippet_short} |")

    # Summary
    src_counts: dict[str, int] = {}
    for src, _, _, _, _ in top:
        src_counts[src] = src_counts.get(src, 0) + 1
    breakdown = ", ".join(f"{icons.get(s, '📦')}{c}" for s, c in sorted(src_counts.items()))
    print(f"\n**{len(top)} 件** ({breakdown}) — {elapsed:.1f}s")
    print()


# PURPOSE: `pks rebuild` — Chronos インデックスの再構築
def cmd_rebuild(args: argparse.Namespace) -> None:
    """Chronos インデックスを Handoff ファイルから再構築する"""
    import os, re, time
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(key, None)
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

    target = args.target
    if target != "chronos":
        print(f"❌ 未対応のターゲット: {target} (現在は 'chronos' のみ対応)")
        return

    print("## 🔄 Chronos Index Rebuild\n")
    t0 = time.time()

    handoff_dir = SESSIONS_DIR
    handoffs = sorted(handoff_dir.glob("handoff_20??-??-??_????.md"))
    print(f"📁 Handoff ファイル: {len(handoffs)} 件")

    if not handoffs:
        print("📭 Handoff ファイルが見つかりません。")
        return

    # Split into chunks by ## headers
    chunks = []
    for hf in handoffs:
        content = hf.read_text(encoding='utf-8', errors='ignore')
        session_id = hf.stem
        sections = re.split(r'\n(?=## )', content)
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) < 50:
                continue
            if len(section) > 2000:
                section = section[:2000]
            chunks.append((f"{session_id}_s{i}", section,
                          {"session_id": session_id, "chunk": i}))

    print(f"📝 チャンク: {len(chunks)} 件")

    # Encode and index
    import numpy as np
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.embedder_factory import get_embed_fn
    embed_fn = get_embed_fn()
    adapter = VectorStore()
    adapter.create_index(dimension=3072)

    batch_size = 32
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        texts = [c[1] for c in batch]
        vecs = np.array([embed_fn(t) for t in texts], dtype=np.float32)
        metas = [{"doc_id": c[0], **c[2]} for c in batch]
        adapter.add_vectors(vecs, metadata=metas)
        done = start + len(batch)
        if done % 128 == 0 or done == len(chunks):
            print(f"  進捗: {done}/{len(chunks)}")

    out_path = INDICES_DIR / "chronos.pkl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    adapter.save(str(out_path))

    elapsed = time.time() - t0
    print(f"\n✅ chronos.pkl 保存完了: **{adapter.count():,}** docs ({elapsed:.1f}s)")
    print()


# PURPOSE: `pks push` — コンテキストに基づく能動的プッシュ
def cmd_push(args: argparse.Namespace) -> None:
    """コンテキストに基づく能動的プッシュ"""
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(
        threshold=args.threshold,
        max_push=args.max,
        enable_questions=not args.no_questions,
        enable_serendipity=True,
    )

    if args.topics:
        topics = [t.strip() for t in args.topics.split(",")]
        engine.set_context(topics=topics)
        print(f"[PKS] トピック設定: {topics}")
    elif args.auto:
        topics = engine.auto_context_from_handoff()
        if not topics:
            print("[PKS] Handoff からのトピック抽出に失敗しました。--topics を指定してください。")
            return
    elif hasattr(args, 'infer') and args.infer:
        user_input = args.infer
        topics = engine.auto_context_from_input(user_input)
        if not topics:
            print("[PKS] Attractor によるコンテキスト推論に失敗しました。")
            return
    else:
        print("[PKS] --topics / --auto / --infer を指定してください。")
        return

    # v4: ソース指定
    sources = None
    if hasattr(args, 'sources') and args.sources:
        sources = [s.strip() for s in args.sources.split(",")]

    src_label = ", ".join(sources) if sources else "gnosis + gateway"
    print(f"[PKS] {src_label} 検索中...")
    nuggets = engine.proactive_push(k=args.k, sources=sources)

    if not nuggets:
        print("📭 プッシュ対象の知識はありません。")
        return

    # 質問生成
    if not args.no_questions:
        print("[PKS] 質問生成中...")
        nuggets = engine.suggest_questions(nuggets)

    # レポート出力
    report = engine.format_push_report(nuggets)
    print(report)

    # Advocacy: 論文一人称メッセージ
    if getattr(args, 'advocacy', False):
        _print_advocacy(nuggets, engine)


# PURPOSE: `pks suggest` — トピック指定で「聞くべき質問」を生成
def cmd_suggest(args: argparse.Namespace) -> None:
    """トピック指定で「聞くべき質問」を生成"""
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(enable_questions=True, enable_serendipity=False)

    topic = args.topic
    engine.set_context(topics=[topic])

    print(f"[PKS] '{topic}' に関する知識を検索中...")
    nuggets = engine.search_and_push(topic, k=args.k)

    if not nuggets:
        print(f"📭 '{topic}' に関連する知識がありません。")
        return

    # 上位 N 件に質問を生成
    top_nuggets = nuggets[: args.max]
    top_nuggets = engine.suggest_questions(top_nuggets)

    for i, nugget in enumerate(top_nuggets, 1):
        print(f"\n### [{i}] {nugget.title}")
        print(f"_関連度: {nugget.relevance_score:.2f} | ソース: {nugget.source}_")
        if nugget.suggested_questions:
            print("\n**💡 聞くべき質問:**")
            for q in nugget.suggested_questions:
                print(f"  - {q}")
    print()


# PURPOSE: `pks backlinks` — 擬似バックリンクを表示
def cmd_backlinks(args: argparse.Namespace) -> None:
    """指定トピックの擬似バックリンクを表示"""
    from mekhane.pks.matrix_view import PKSBacklinks
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(enable_questions=False, enable_serendipity=False)

    query = args.query
    print(f"[PKS] '{query}' の擬似バックリンクを検索中...")

    nuggets = engine.search_and_push(query, k=args.k)

    if not nuggets:
        print(f"📭 '{query}' に関連する知識がありません。")
        return

    backlinks = PKSBacklinks()
    report = backlinks.generate(query, nuggets)
    print(report)


# PURPOSE: `pks auto` — Handoff から自動でプッシュ
def cmd_auto(args: argparse.Namespace) -> None:
    """Handoff から自動的にトピック抽出してプッシュ"""
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(
        enable_questions=not args.no_questions,
        enable_serendipity=True,
    )

    topics = engine.auto_context_from_handoff()
    if not topics:
        print("📭 Handoff からのトピック抽出に失敗しました。")
        return

    print(f"[PKS] 抽出トピック: {topics}")
    print("[PKS] Gnōsis 検索中...")

    # verbose: 検索結果の距離・スコアを表示
    verbose = getattr(args, 'verbose', False)
    if verbose:
        context = engine.tracker.context
        query_text = context.to_embedding_text()
        print(f"[PKS verbose] Query: {query_text[:200]}")
        print(f"[PKS verbose] Threshold: {engine.detector.threshold}")

        index = engine._get_index()
        results = index.search(query_text, k=args.k)
        print(f"[PKS verbose] 検索結果: {len(results)} 件")
        for i, r in enumerate(results[:10]):
            dist = r.get('_distance', float('inf'))
            score = max(0.0, 1.0 - (dist / 2.0))
            passed = '✅' if score >= engine.detector.threshold else '❌'
            print(f"  {i+1}. [{r.get('source', '?'):8s}] {r.get('title', '?')[:50]:50s}"
                  f" dist={dist:.3f} score={score:.3f} {passed}")

    nuggets = engine.proactive_push(k=args.k)

    if verbose:
        print(f"[PKS verbose] Nuggets after scoring+filter: {len(nuggets)}")

    if not nuggets:
        print("📭 プッシュ対象の知識はありません。")
        return

    if not args.no_questions:
        print("[PKS] 質問生成中...")
        nuggets = engine.suggest_questions(nuggets)

    report = engine.format_push_report(nuggets)
    print(report)

    # Advocacy: 論文一人称メッセージ
    if getattr(args, 'advocacy', False):
        _print_advocacy(nuggets, engine)


# PURPOSE: `pks infer` — Attractor ベースのコンテキスト推論 + プッシュ
def cmd_infer(args: argparse.Namespace) -> None:
    """ユーザー入力から Attractor でコンテキスト推論してプッシュ"""
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(
        enable_questions=not args.no_questions,
        enable_serendipity=True,
    )

    user_input = " ".join(args.input)
    topics = engine.auto_context_from_input(user_input)
    if not topics:
        print("📭 Attractor コンテキスト推論に失敗しました。")
        return

    print(f"[PKS] 推論トピック: {topics}")
    print("[PKS] Gnōsis 検索中...")

    nuggets = engine.proactive_push(k=args.k)

    if not nuggets:
        print("📭 プッシュ対象の知識はありません。")
        return

    if not args.no_questions:
        print("[PKS] 質問生成中...")
        nuggets = engine.suggest_questions(nuggets)

    report = engine.format_push_report(nuggets)
    print(report)


# PURPOSE: `pks feedback` — プッシュ反応を記録
def cmd_feedback(args: argparse.Namespace) -> None:
    """プッシュされた知識へのリアクションを記録"""
    from mekhane.pks.pks_engine import PKSEngine

    engine = PKSEngine(
        enable_questions=False,
        enable_serendipity=False,
        enable_feedback=True,
    )

    if args.stats:
        # 統計表示
        if engine._feedback:
            stats = engine._feedback.get_stats()
            if not stats:
                print("📭 フィードバック履歴がありません。")
                return
            print("## 📊 PKS Feedback Stats\n")
            print("| Series | Count | Avg Score | Threshold Adj |")
            print("|:------:|------:|----------:|--------------:|")
            for series, s in sorted(stats.items()):
                adj = s['threshold_adjustment']
                sign = "+" if adj >= 0 else ""
                print(f"| {series} | {s['count']} | {s['avg_score']:.2f} | {sign}{adj:.3f} |")
        return

    # 反応記録
    engine.record_feedback(
        nugget_title=args.title,
        reaction=args.reaction,
        series=args.series or "",
    )
    print(f"✅ Feedback recorded: '{args.title}' → {args.reaction}")


# PURPOSE: `pks dialog` — プッシュされた知識への対話
def cmd_dialog(args: argparse.Namespace) -> None:
    """プッシュされた知識に対して対話的に探索"""
    from mekhane.pks.pks_engine import PKSEngine
    from mekhane.pks.push_dialog import PushDialog

    engine = PKSEngine(
        enable_questions=False,
        enable_serendipity=False,
    )

    # title で nugget を検索
    title = args.title
    nuggets = engine.search_and_push(title, k=3)
    if not nuggets:
        print(f"📭 '{title}' に該当する知識が見つかりません。")
        return

    nugget = nuggets[0]  # 最も関連度が高いもの
    dialog = PushDialog(on_feedback=engine.make_feedback_callback())

    action = args.action
    if action == "why":
        print(dialog.why(nugget))
    elif action == "ask":
        if not args.question:
            print("質問を指定してください: pks dialog ask <title> -q '質問'")
            return
        print(dialog.deeper(nugget, args.question))
    elif action == "related":
        related = dialog.related(nugget, k=args.k)
        if not related:
            print(f"📭 '{nugget.title}' の関連知識は見つかりませんでした。")
            return
        print(f"## 🔗 '{nugget.title}' の関連知識\n")
        for i, r in enumerate(related, 1):
            print(f"{i}. **{r.title}** (関連度: {r.relevance_score:.2f}) [{r.source}]")
    else:
        print(f"不明なアクション: {action}")


# PURPOSE: メインエントリポイント
def main() -> None:
    """PKS CLI メインエントリポイント"""
    parser = argparse.ArgumentParser(
        description="PKS v2 — Proactive Knowledge Surface CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  pks push --topics 'FEP,CCL'     # 指定トピックでプッシュ\n"
            "  pks push --auto                  # Handoff から自動検出\n"
            "  pks push --infer 'FEPを調査'     # Attractor 推論でプッシュ\n"
            "  pks infer 'FEPの理論的基盤'       # Attractor 推論 + プッシュ\n"
            "  pks suggest 'Active Inference'   # 質問生成\n"
            "  pks backlinks 'FEP'              # 擬似バックリンク\n"
            "  pks auto                         # 全自動プッシュ\n"
            "  pks feedback -t 'paper' -r used   # 反応記録\n"
            "  pks feedback --stats              # 統計表示\n"
            "  pks stats                         # 知識基盤統計\n"
            "  pks health                        # 全スタックヘルスチェック\n"
            "  pks search 'FEP precision'        # 全インデックス横断検索\n"
            "  pks search 'active inference' -s gnosis,chronos  # ソース限定\n"
            "  pks rebuild chronos               # Chronos インデックス再構築\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # --- stats ---
    p_stats = subparsers.add_parser("stats", help="知識基盤の統計ダッシュボード")
    p_stats.set_defaults(func=cmd_stats)

    # --- health ---
    p_health = subparsers.add_parser("health", help="Autophōnos 全スタックのヘルスチェック")
    p_health.set_defaults(func=cmd_health)

    # --- search ---
    p_search = subparsers.add_parser("search", help="全インデックス横断検索")
    p_search.add_argument("query", help="検索クエリ")
    p_search.add_argument("--k", type=int, default=10, help="取得件数 (default: 10)")
    p_search.add_argument("--sources", "-s", default=None,
                          help="検索ソース (カンマ区切り: gnosis,kairos,sophia,chronos)")
    p_search.set_defaults(func=cmd_search)

    # --- rebuild ---
    p_rebuild = subparsers.add_parser("rebuild", help="インデックスの再構築")
    p_rebuild.add_argument("target", choices=["chronos"], help="再構築対象")
    p_rebuild.set_defaults(func=cmd_rebuild)

    # --- push ---
    p_push = subparsers.add_parser("push", help="能動的プッシュを実行")
    p_push.add_argument("--topics", "-t", help="トピック (カンマ区切り)")
    p_push.add_argument("--auto", "-a", action="store_true", help="Handoff からトピック自動抽出")
    p_push.add_argument("--infer", "-i", help="Attractor でコンテキスト推論 (テキスト入力)")
    p_push.add_argument("--threshold", type=float, default=0.50, help="関連度閾値 (default: 0.50)")
    p_push.add_argument("--max", "-m", type=int, default=5, help="最大プッシュ件数 (default: 5)")
    p_push.add_argument("--k", type=int, default=20, help="検索候補数 (default: 20)")
    p_push.add_argument("--no-questions", action="store_true", help="質問生成を無効化")
    p_push.add_argument("--sources", "-s", default=None,
                        help="データソース (カンマ区切り: gnosis,gateway,ideas,doxa,handoff,ki)")
    p_push.add_argument("--advocacy", action="store_true", help="論文一人称メッセージを生成 (Autophōnos)")
    p_push.set_defaults(func=cmd_push)

    # --- suggest ---
    p_suggest = subparsers.add_parser("suggest", help="「聞くべき質問」を生成")
    p_suggest.add_argument("topic", help="トピック")
    p_suggest.add_argument("--max", "-m", type=int, default=3, help="対象件数 (default: 3)")
    p_suggest.add_argument("--k", type=int, default=10, help="検索候補数 (default: 10)")
    p_suggest.set_defaults(func=cmd_suggest)

    # --- backlinks ---
    p_backlinks = subparsers.add_parser("backlinks", help="擬似バックリンクを表示")
    p_backlinks.add_argument("query", help="検索クエリ")
    p_backlinks.add_argument("--k", type=int, default=15, help="検索候補数 (default: 15)")
    p_backlinks.set_defaults(func=cmd_backlinks)

    # --- auto ---
    p_auto = subparsers.add_parser("auto", help="Handoff から全自動プッシュ")
    p_auto.add_argument("--k", type=int, default=20, help="検索候補数 (default: 20)")
    p_auto.add_argument("--no-questions", action="store_true", help="質問生成を無効化")
    p_auto.add_argument("--verbose", "-v", action="store_true", help="検索結果のスコア詳細を表示")
    p_auto.add_argument("--advocacy", action="store_true", help="論文一人称メッセージを生成 (Autophōnos)")
    p_auto.set_defaults(func=cmd_auto)

    # --- infer ---
    p_infer = subparsers.add_parser("infer", help="Attractor 推論でプッシュ")
    p_infer.add_argument("input", nargs="+", help="推論入力テキスト")
    p_infer.add_argument("--k", type=int, default=20, help="検索候補数 (default: 20)")
    p_infer.add_argument("--no-questions", action="store_true", help="質問生成を無効化")
    p_infer.set_defaults(func=cmd_infer)

    # --- feedback ---
    p_feedback = subparsers.add_parser("feedback", help="プッシュ反応を記録")
    p_feedback.add_argument("--title", "-t", help="ナゲットタイトル")
    p_feedback.add_argument(
        "--reaction", "-r",
        choices=["used", "dismissed", "deepened", "ignored"],
        help="反応タイプ",
    )
    p_feedback.add_argument("--series", "-s", help="Attractor series (任意)")
    p_feedback.add_argument("--stats", action="store_true", help="フィードバック統計を表示")
    p_feedback.set_defaults(func=cmd_feedback)

    # --- dialog ---
    p_dialog = subparsers.add_parser("dialog", help="プッシュ知識への対話")
    p_dialog.add_argument("action", choices=["why", "ask", "related"], help="アクション")
    p_dialog.add_argument("title", help="ナゲットタイトル (検索クエリ)")
    p_dialog.add_argument("--question", "-q", help="質問 (ask 用)")
    p_dialog.add_argument("--k", type=int, default=5, help="関連知識件数 (default: 5)")
    p_dialog.set_defaults(func=cmd_dialog)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
