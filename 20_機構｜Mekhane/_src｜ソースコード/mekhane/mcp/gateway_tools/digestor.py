# PROOF: mekhane/mcp/gateway_tools/digestor.py
# PURPOSE: mcp モジュールの digestor
"""Gateway tools: digestor domain."""
import time
import json
from pathlib import Path
from datetime import datetime


def register_digestor_tools(mcp):
    """Register digestor domain tools (5 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced

    # PURPOSE: [L2-auto] incoming/ の未消化ファイルを確認する。

    # PURPOSE: [L2-auto] hgk_digest_check の関数定義
    @mcp.tool()
    @_traced
    def hgk_digest_check() -> str:
        """
        incoming/ の未消化ファイルを確認する。
        消化待ちの論文候補一覧を返す。
        """
        if not INCOMING_DIR.exists():
            return "## ⚠️ incoming/ ディレクトリが見つかりません"

        files = sorted(INCOMING_DIR.glob("eat_*.md"))
        if not files:
            return "## 📭 消化待ちの候補はありません (0 件)"

        lines = [f"## 📥 消化待ち候補: {len(files)} 件\n"]

        for i, f in enumerate(files, 1):
            try:
                content = f.read_text(encoding="utf-8")
                title = "(タイトル不明)"
                score = ""
                topics_str = ""

                in_frontmatter = False
                for line in content.split("\n"):
                    if line.strip() == "---":
                        if in_frontmatter:
                            break
                        in_frontmatter = True
                        continue
                    if in_frontmatter:
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip("\"'")
                        elif line.startswith("score:"):
                            score = line.split(":", 1)[1].strip()
                        elif line.startswith("topics:"):
                            topics_str = line.split(":", 1)[1].strip()

                lines.append(f"### {i}. {title}")
                if score:
                    lines.append(f"- **Score**: {score}")
                if topics_str:
                    lines.append(f"- **Topics**: {topics_str}")
                lines.append(f"- **File**: `{f.name}`\n")
            except Exception as e:  # noqa: BLE001
                lines.append(f"### {i}. {f.name} (読取エラー: {e})\n")

        # processed 件数も表示
        processed_count = len(list(PROCESSED_DIR.glob("eat_*.md"))) if PROCESSED_DIR.exists() else 0
        lines.append(f"---\n📦 processed/: {processed_count} 件 消化済")

        return "\n".join(lines)
    # =============================================================================
    # Digestor: Mark Processed (消化完了マーク)
    # =============================================================================

    # PURPOSE: 消化完了ファイルを processed/ に移動する
    @mcp.tool()
    @_traced
    def hgk_digest_mark(filenames: str = "") -> str:
        """
        消化完了したファイルを incoming/ → processed/ に移動する。

        Args:
            filenames: 移動するファイル名 (カンマ区切り)。空の場合は全 eat_*.md を移動。
        """
        try:
            from mekhane.ergasterion.digestor.pipeline import mark_as_processed

            file_list = [f.strip() for f in filenames.split(",") if f.strip()] if filenames else None
            result = mark_as_processed(filenames=file_list)

            lines = [f"## ✅ processed/ 移動結果\n"]
            lines.append(f"**移動成功**: {result['count']} 件\n")

            for f in result["moved"]:
                lines.append(f"- ✅ `{f}`")
            for e in result["errors"]:
                lines.append(f"- ❌ `{e['file']}`: {e['error']}")

            return "\n".join(lines)
        except ImportError:
            return "❌ DigestorPipeline が利用できません"
        except Exception as e:  # noqa: BLE001
            return f"❌ エラー: {e}"
    # =============================================================================
    # Digestor: List Candidates (候補評価)
    # =============================================================================

    # PURPOSE: Digestor selector で候補を評価する
    @mcp.tool()
    @_traced
    def hgk_digest_list(
        topics: str = "",
        max_candidates: int = 10,
    ) -> str:
        """
        Digestor の selector で論文候補を評価する (dry-run)。
        incoming/ には書き込まず、評価結果のみ返す。

        Args:
            topics: 対象トピック (カンマ区切り)。最大 500 文字。空=全トピック。
            max_candidates: 最大候補数 (1-20、デフォルト 10)。
        """
        if len(topics) > 500:
            return "❌ トピックが長すぎます (最大 500 文字)"
        max_candidates = max(1, min(20, max_candidates))

        try:
            import urllib.request
            import json

            url = "http://127.0.0.1:9696/api/digestor/run"
            payload = json.dumps({
                "topics": [t.strip() for t in topics.split(",") if t.strip()] if topics else None,
                "max_papers": 30,
                "max_candidates": max_candidates,
                "dry_run": True,
            }).encode("utf-8")
        
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}
            )
        
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
                lines = [f"## 🔍 消化候補リスト (via API dry-run)\n"]
                lines.append(f"- **取得論文数**: {data.get('total_papers', 0)}")
                lines.append(f"- **選定候補数**: {data.get('candidates_selected', 0)}\n")

                candidates = data.get("candidates", [])
                for i, c in enumerate(candidates[:max_candidates], 1):
                    # APIのレスポンス構造に合わせる
                    lines.append(f"### {i}. [{c.get('score', 0):.2f}] {c.get('title', '')[:80]}")
                    authors = c.get('authors', [])
                    if authors:
                        authors_str = ", ".join(authors[:3])
                        lines.append(f"- **著者**: {authors_str}")
                    lines.append("")

                return "\n".join(lines)
            
        except Exception as e:  # noqa: BLE001
            return f"❌ 候補リストエラー (API Timeout等): {e}"
    # =============================================================================
    # Digestor: Topics (トピック一覧)
    # =============================================================================

    # PURPOSE: 消化対象トピック一覧を表示する
    @mcp.tool()
    @_traced
    def hgk_digest_topics() -> str:
        """
        消化対象トピック一覧を表示する。
        topics.yaml に定義されたテーマと設定を返す。
        """
        try:
            import yaml

            topics_file = PROJECT_ROOT / "mekhane" / "ergasterion" / "digestor" / "topics.yaml"
            if not topics_file.exists():
                return "## ⚠️ topics.yaml が見つかりません"

            data = yaml.safe_load(topics_file.read_text(encoding="utf-8"))
            settings = data.get("settings", {})
            topics_list = data.get("topics", [])

            lines = [f"## 📋 消化対象トピック ({len(topics_list)} テーマ)\n"]
            lines.append(f"- **最大候補数**: {settings.get('max_candidates', '?')}")
            lines.append(f"- **最小スコア**: {settings.get('min_score', '?')}")
            lines.append(f"- **マッチモード**: {settings.get('match_mode', '?')}\n")

            for t in topics_list:
                tid = t.get("id", "?")
                desc = t.get("description", "")
                digest_to = ", ".join(t.get("digest_to", []))
                lines.append(f"### `{tid}`")
                lines.append(f"- {desc}")
                lines.append(f"- → {digest_to}\n")

            return "\n".join(lines)
        except ImportError:
            return "❌ PyYAML が利用できません"
        except Exception as e:  # noqa: BLE001
            return f"❌ トピック読取エラー: {e}"
    # =============================================================================
    # Digest Run (消化パイプライン)
    # =============================================================================

    # PURPOSE: Digestor パイプラインを実行し、消化候補を生成する
    @mcp.tool()
    @_traced
    def hgk_digest_run(
        topics: str = "",
        max_papers: int = 20,
        dry_run: bool = True,
    ) -> str:
        """
        Digestor パイプラインを実行する。
        デフォルトは dry_run (レポートのみ)。dry_run=False で .md ファイルを生成。

        Args:
            topics: 対象トピック (カンマ区切り)。最大 500 文字。空の場合は全トピック。
            max_papers: 取得する最大論文数 (1-50、デフォルト 20)。
            dry_run: True=レポートのみ、False=.md ファイル生成 (incoming/ に出力)。
        """
        # Input validation
        if len(topics) > 500:
            return "❌ トピックが長すぎます (最大 500 文字)"
        max_papers = max(1, min(50, max_papers))

        try:
            import urllib.request
            import json

            url = "http://127.0.0.1:9696/api/digestor/run"
            payload = json.dumps({
                "topics": [t.strip() for t in topics.split(",") if t.strip()] if topics else None,
                "max_papers": max_papers,
                "dry_run": dry_run,
            }).encode("utf-8")
        
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}
            )
        
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
                mode_label = "🧪 DRY RUN" if dry_run else "🚀 LIVE"
                result = f"## {mode_label} 消化パイプライン実行結果 (via API)\n\n"
            
                result += f"- **取得論文数**: {data.get('total_papers', 0)}\n"
                result += f"- **候補数**: {data.get('candidates_selected', 0)}\n"
                if not dry_run:
                    result += f"- **生成ファイル**: {data.get('generated_files_count', 0)} 件\n"

                return result
            
        except Exception as e:  # noqa: BLE001
            return f"❌ 消化パイプラインエラー (API Timeout等): {e}"
