#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/peira/ A0→note.com記事収集が必要→note-collectorが担う
"""
note.com 記事収集スクリプト v2
シンプル版 - 即時実行
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from mekhane.paths import MNEME_DIR

# 設定
USER_URLNAME = "tasty_dunlin998"
OUTPUT_DIR = MNEME_DIR / "raw" / "note"
API_BASE = "https://note.com/api/v2"

# PURPOSE: CLI エントリポイント — データパイプラインの直接実行
def main():
    print(f"🔍 Collecting articles from note.com/{USER_URLNAME}")
    
    # 出力ディレクトリを作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_articles = []
    page = 1
    
    # 全ページを取得
    while page <= 20:  # 最大20ページ
        print(f"📄 Fetching page {page}...", flush=True)
        
        url = f"{API_BASE}/creators/{USER_URLNAME}/contents"
        params = {"kind": "note", "page": page, "per_page": 20}
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            
            contents = result.get("data", {}).get("contents", [])
            
            if not contents:
                print(f"📭 No more articles")
                break
            
            all_articles.extend(contents)
            print(f"   Found {len(contents)} articles (total: {len(all_articles)})", flush=True)
            
            if result.get("data", {}).get("isLastPage", True):
                break
            
            page += 1
            time.sleep(0.5)
            
        except Exception as e:  # noqa: BLE001
            print(f"❌ Error: {e}")
            break
    
    print(f"\n📊 Total: {len(all_articles)} articles")
    
    # 各記事を保存
    for i, article in enumerate(all_articles, 1):
        key = article.get("key", "unknown")
        title = article.get("name", "untitled")
        body = article.get("body", "")
        publish_at = article.get("publishAt", "")
        
        # ファイル名生成
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:40])
        filename = f"{key}_{safe_title}.md"
        
        # Markdown 生成
        md = f"""# {title}

> **Source**: https://note.com/{USER_URLNAME}/n/{key}
> **Published**: {publish_at}
> **Collected**: {datetime.now().isoformat()}

---

{body}
"""
        
        filepath = OUTPUT_DIR / filename
        filepath.write_text(md, encoding="utf-8")
        print(f"[{i}/{len(all_articles)}] ✅ {filename[:50]}", flush=True)
    
    # マニフェスト保存
    manifest = {
        "user": USER_URLNAME,
        "collected_at": datetime.now().isoformat(),
        "total_articles": len(all_articles),
        "articles": [
            {"key": a.get("key"), "name": a.get("name"), "publishAt": a.get("publishAt")}
            for a in all_articles
        ]
    }
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n✅ Done! {len(all_articles)} articles saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
