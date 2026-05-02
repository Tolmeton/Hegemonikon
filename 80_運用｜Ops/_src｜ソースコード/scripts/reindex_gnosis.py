#!/usr/bin/env python3
"""
Gnōsis FAISS Re-embedder: VertexEmbedder で全ベクトル置換

既存インデックスの非ベクトルデータを保持したまま、VertexEmbedder で再エンベディング。
デフォルトモデルは anamnesis/constants.py の EMBED_MODEL を参照。

Usage:
    python scripts/reindex_gnosis.py --dry-run       # データ件数・推定時間を表示
    python scripts/reindex_gnosis.py                 # Vertex で再エンベディング
    python scripts/reindex_gnosis.py --batch-size 10  # バッチサイズ変更
    python scripts/reindex_gnosis.py --use-bge       # bge-m3 で再エンベディング (フォールバック)
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_embedding_text(row) -> str:
    """レコードからエンベディング用テキストを生成."""
    title = str(row.get("title", ""))
    abstract = str(row.get("abstract", ""))
    content = str(row.get("content", ""))
    if content and content != "nan" and len(content) > 50:
        return f"{title}\n{content[:2000]}"
    elif abstract and abstract != "nan":
        return f"{title}\n{abstract}"
    return title


def main():
    parser = argparse.ArgumentParser(description="Gnōsis Re-embedder (FAISS + Vertex AI)")
    parser.add_argument("--dry-run", action="store_true", help="データ件数・推定時間のみ")
    parser.add_argument("--batch-size", type=int, default=10, help="バッチサイズ (default: 10, Vertex API 推奨)")
    parser.add_argument("--use-bge", action="store_true", help="bge-m3 でエンベディング (フォールバック)")
    parser.add_argument("--skip-backup", action="store_true", help="バックアップをスキップ")
    args = parser.parse_args()

    from mekhane.anamnesis.index import GnosisIndex

    idx = GnosisIndex()
    if not idx._table_exists():
        print("[reindex] FAISS インデックスが存在しません。終了。")
        return

    records = idx._backend.to_list()
    row_count = len(records)
    current_dim = idx._backend.get_vector_dimension()

    print(f"[reindex] 現在: {row_count} 行, {current_dim}d")

    # Load embedder
    if args.use_bge:
        from mekhane.anamnesis.index import Embedder
        print("[reindex] Embedder: bge-m3 (local)")
        embedder = Embedder(model_name="BAAI/bge-m3", dimension=1024)
        embedder_name = "bge-m3"
        est_rate = 10  # texts/sec on CPU
    else:
        from mekhane.anamnesis.vertex_embedder import VertexEmbedder
        from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
        print(f"[reindex] Embedder: {EMBED_MODEL} (Vertex AI, {EMBED_DIM}d)")
        embedder = VertexEmbedder(model_name=EMBED_MODEL, dimension=EMBED_DIM)
        embedder_name = EMBED_MODEL
        est_rate = 15  # texts/sec (batch=10, ~0.6s/batch)

    dim = getattr(embedder, '_dimension', None)
    print(f"[reindex] Embedder ready: {embedder_name}, dim={dim}")

    est_time = row_count / est_rate
    print(f"[reindex] 推定時間: ~{est_time:.0f}秒 ({est_time/60:.1f}分)")

    if args.dry_run:
        print("[reindex] --dry-run: 終了。")
        return

    # Backup
    if not args.skip_backup:
        from mekhane.paths import GNOSIS_DB_DIR
        base_dir = GNOSIS_DB_DIR
        backup_dir = base_dir.parent / f"{base_dir.name}_backup"
        if backup_dir.exists():
            print(f"[reindex] バックアップ '{backup_dir.name}' は既に存在。スキップ。")
        else:
            print(f"[reindex] バックアップ作成: {base_dir} → {backup_dir}")
            shutil.copytree(str(base_dir), str(backup_dir))
            print("[reindex] ✅ バックアップ完了")

    # Prepare texts
    print(f"[reindex] テキスト準備中...")
    texts = [make_embedding_text(row) for row in records]

    # Filter empty texts
    empty_count = sum(1 for t in texts if not t.strip())
    if empty_count > 0:
        print(f"[reindex] ⚠️ 空テキスト: {empty_count} 件 (フォールバック: 'empty')")
        texts = [t if t.strip() else "empty" for t in texts]

    # Batch embed
    print(f"[reindex] {row_count} 行を再エンベディング中...")
    all_vectors = []
    start_time = time.time()
    batch_size = args.batch_size
    errors = 0

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            vectors = embedder.embed_batch(batch)
            all_vectors.extend(vectors)
        except Exception as e:
            print(f"  ⚠️ バッチ {i}-{i+len(batch)} エラー: {e}")
            errors += 1
            # Retry one by one
            for j, text in enumerate(batch):
                try:
                    vec = embedder.embed(text)
                    all_vectors.append(vec)
                except Exception as e2:
                    print(f"  ❌ 行 {i+j} 個別エラー: {e2}")
                    # Zero vector as placeholder
                    all_vectors.append([0.0] * (dim or 3072))

        done = min(i + batch_size, len(texts))
        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (len(texts) - done) / rate if rate > 0 else 0
        if done % 500 == 0 or done == len(texts):
            print(f"  [{done}/{len(texts)}] {rate:.1f} texts/sec, ETA {eta:.0f}秒", flush=True)

    elapsed_total = time.time() - start_time
    print(f"[reindex] エンベディング完了: {elapsed_total:.1f}秒 ({errors} エラー)")

    # Rebuild table with explicit PyArrow schema
    print("[reindex] FAISS インデックス再構築中...")

    for record, vec in zip(records, all_vectors):
        record["vector"] = vec

    # Recreate index avoiding overwrite conflict
    idx._backend.delete("true")
    idx._backend.create(records)

    idx = GnosisIndex()
    new_dim = idx._backend.get_vector_dimension()
    new_count = idx._backend.count()

    print(f"\n[reindex] ✅ 再エンベディング完了!")
    print(f"  旧: {row_count} 行, {current_dim}d")
    print(f"  新: {new_count} 行, {new_dim}d ({embedder_name})")
    print(f"  時間: {elapsed_total:.1f}秒 ({elapsed_total/60:.1f}分)")

    if new_count != row_count:
        print(f"  ⚠️ 行数差異: {row_count} → {new_count}")

    # Search test
    print("\n[reindex] 検索テスト...")
    try:
        q_vec = embedder.embed("Free Energy Principle")
        results = idx._backend.search_vector(q_vec, k=5)
        print(f"  検索OK: {len(results)} 件")
        for r in results[:5]:
            title = str(r.get("title", "?"))[:60]
            dist = float(r.get("_distance", 1.0))
            print(f"    - {title} (dist={dist:.4f})")
    except Exception as e:
        print(f"  ⚠️ 検索テスト失敗: {e}")


if __name__ == "__main__":
    main()
