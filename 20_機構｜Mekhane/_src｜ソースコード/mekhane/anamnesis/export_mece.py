#!/usr/bin/env python3
# PROOF: [L1/機能] <- mekhane/anamnesis/export_mece.py A0→MECE Export→全セッションデータ統合エクスポート
# PURPOSE: 全セッションログを5層 (trajectorySummaries + Handoffs + Brain Artifacts + Ochēma Sessions + IDE Logs)
#   で MECE にエクスポートし、単一の出力ディレクトリにまとめる。CDP 不要。WIN 移行準備用。

import argparse
import json
import os
import shutil
import sqlite3
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# PURPOSE: デフォルトパス定義
HGK_ROOT = Path(os.environ.get(
    "HGK_ROOT",
    os.path.expanduser("~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
))
HANDOFF_DIR = HGK_ROOT / "30_記憶｜Mneme" / "01_記録｜Records" / "a_引継｜handoff"
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"
ANTIGRAVITY_CONFIG = Path.home() / ".config" / "Antigravity"
STATE_VSCDB = ANTIGRAVITY_CONFIG / "User" / "globalStorage" / "state.vscdb"
OCHEMA_SESSIONS_DB = Path.home() / ".config" / "ochema" / "sessions.db"
LOGS_DIR = ANTIGRAVITY_CONFIG / "logs"


# PURPOSE: Layer 1 — trajectorySummaries の抽出
def export_layer1_trajectory(output_dir: Path, dry_run: bool = False) -> dict:
    """Extract trajectorySummaries from Antigravity state.vscdb.
    
    Data is stored as Base64-encoded protobuf containing conversation UUIDs
    and Base64-encoded metadata (titles, timestamps, etc).
    """
    import base64
    import re
    
    result = {"layer": "01_trajectory_summaries", "status": "skipped", "count": 0}
    
    if not STATE_VSCDB.exists():
        result["error"] = f"state.vscdb not found: {STATE_VSCDB}"
        return result
    
    # Copy to /tmp for faster I/O (NFS/Syncthing can be slow)
    tmp_db = Path("/tmp/ag_state_export.vscdb")
    shutil.copy2(STATE_VSCDB, tmp_db)
    
    try:
        conn = sqlite3.connect(str(tmp_db))
        cur = conn.cursor()
        
        # Extract trajectorySummaries
        row = cur.execute(
            "SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'"
        ).fetchone()
        
        if not row:
            result["error"] = "trajectorySummaries key not found in state.vscdb"
            conn.close()
            return result
        
        raw_data = row[0]
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        
        # Try JSON first (in case format changes)
        try:
            parsed = json.loads(raw_data)
            is_json = True
        except json.JSONDecodeError:
            is_json = False
        
        if is_json:
            # JSON format — direct export
            if not dry_run:
                with open(output_dir / "01_trajectory_summaries.json", "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
            result["count"] = len(parsed) if isinstance(parsed, (dict, list)) else 1
        else:
            # Base64 + Protobuf format — decode and extract
            try:
                decoded = base64.b64decode(raw_data)
            except Exception:  # noqa: BLE001
                decoded = raw_data.encode("utf-8") if isinstance(raw_data, str) else raw_data
            
            # Extract UUIDs (conversation IDs)
            uuid_pattern = rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            uuids = re.findall(uuid_pattern, decoded)
            uuids = [u.decode("ascii") for u in uuids]
            
            # Extract Base64 segments and try to decode titles
            ascii_strings = re.findall(rb'[\x20-\x7e]{10,}', decoded)
            
            # Parse conversation entries: UUIDs alternate with Base64 metadata
            conversations = []
            seen_uuids = set()
            for uid in uuids:
                if uid not in seen_uuids:
                    seen_uuids.add(uid)
                    conversations.append({"id": uid})
            
            # Try extracting titles from Base64 segments between UUIDs
            for seg in ascii_strings:
                seg_str = seg.decode("ascii", errors="ignore").strip()
                if len(seg_str) > 20 and not seg_str.startswith("$") and not re.match(r'^[0-9a-f-]{36}$', seg_str):
                    # Try Base64 decode for embedded titles
                    try:
                        inner = base64.b64decode(seg_str + "==")
                        # Extract readable text from decoded protobuf
                        text_parts = re.findall(rb'[\x20-\x7e]{5,}', inner)
                        for part in text_parts:
                            part_str = part.decode("ascii", errors="ignore")
                            # Skip UUIDs and file paths
                            if re.match(r'^[0-9a-f-]{36}$', part_str):
                                continue
                            if part_str.startswith("file://"):
                                continue
                            # This might be a conversation title
                            if len(part_str) > 5 and len(part_str) < 200:
                                # Match to nearest conversation
                                for conv in conversations:
                                    if "title" not in conv:
                                        conv["title"] = part_str
                                        break
                    except Exception:  # noqa: BLE001
                        pass
            
            result["count"] = len(conversations)
            
            if not dry_run:
                # Save raw decoded data
                with open(output_dir / "01_trajectory_summaries.bin", "wb") as f:
                    f.write(decoded)
                
                # Save parsed conversations as JSON
                with open(output_dir / "01_trajectory_summaries.json", "w", encoding="utf-8") as f:
                    json.dump(conversations, f, ensure_ascii=False, indent=2)
                
                # Generate Markdown index
                with open(output_dir / "01_trajectory_summaries.md", "w", encoding="utf-8") as f:
                    f.write("# Trajectory Summaries (Protobuf Extracted)\n\n")
                    f.write(f"Extracted: {datetime.now().isoformat()}\n")
                    f.write(f"Raw data: {len(decoded)} bytes (protobuf)\n")
                    f.write(f"Conversations found: {len(conversations)}\n\n")
                    f.write("| # | Conversation ID | Title |\n")
                    f.write("|---|----------------|-------|\n")
                    for i, conv in enumerate(conversations, 1):
                        title = conv.get("title", "(untitled)")
                        f.write(f"| {i} | `{conv['id'][:12]}...` | {title} |\n")
        
        # Also extract other interesting keys
        interesting_keys = [
            "antigravityUnifiedStateSync.agentManagerWindow",
            "antigravityUnifiedStateSync.agentPreferences",
            "chat.participantNameRegistry",
        ]
        extras = {}
        for key in interesting_keys:
            erow = cur.execute(
                "SELECT value FROM ItemTable WHERE key = ?", (key,)
            ).fetchone()
            if erow:
                val = erow[0]
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                try:
                    extras[key] = json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    extras[key] = val
        
        if extras and not dry_run:
            with open(output_dir / "01_antigravity_state_extras.json", "w", encoding="utf-8") as f:
                json.dump(extras, f, ensure_ascii=False, indent=2)
        
        conn.close()
        result["status"] = "ok"
        result["extras_keys"] = list(extras.keys())
        
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(e)
    finally:
        if tmp_db.exists():
            tmp_db.unlink()
    
    return result


# PURPOSE: Layer 2 — Handoff ファイル収集
def export_layer2_handoffs(output_dir: Path, dry_run: bool = False) -> dict:
    """Collect all Handoff files with timestamp index."""
    result = {"layer": "02_handoffs", "status": "skipped", "count": 0}
    
    if not HANDOFF_DIR.exists():
        result["error"] = f"Handoff directory not found: {HANDOFF_DIR}"
        return result
    
    handoff_files = sorted(HANDOFF_DIR.glob("*.md"))
    result["count"] = len(handoff_files)
    
    if not dry_run:
        dest = output_dir / "02_handoffs"
        dest.mkdir(parents=True, exist_ok=True)
        
        # Copy all handoff files
        for f in handoff_files:
            shutil.copy2(f, dest / f.name)
        
        # Generate index
        index_path = dest / "_index.md"
        with open(index_path, "w", encoding="utf-8") as idx:
            idx.write("# Handoff Index\n\n")
            idx.write(f"Total: {len(handoff_files)} files\n\n")
            idx.write("| # | Date | Filename | Size |\n")
            idx.write("|---|------|----------|------|\n")
            for i, f in enumerate(handoff_files, 1):
                size_kb = f.stat().st_size / 1024
                # Extract date from filename: handoff_YYYY-MM-DD_HHMM.md
                name = f.stem
                date_part = name.replace("handoff_", "")
                idx.write(f"| {i} | {date_part} | [{f.name}]({f.name}) | {size_kb:.1f} KB |\n")
    
    result["status"] = "ok"
    return result


# PURPOSE: Layer 3 — Brain Artifacts 収集
def export_layer3_brain(output_dir: Path, dry_run: bool = False) -> dict:
    """Collect all Brain artifacts (task.md, walkthrough.md, etc)."""
    result = {"layer": "03_brain_artifacts", "status": "skipped", "count": 0}
    
    if not BRAIN_DIR.exists():
        result["error"] = f"Brain directory not found: {BRAIN_DIR}"
        return result
    
    conv_dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    result["count"] = len(conv_dirs)
    
    if not dry_run:
        dest = output_dir / "03_brain_artifacts"
        dest.mkdir(parents=True, exist_ok=True)
        
        index_entries = []
        
        for i, conv_dir in enumerate(sorted(conv_dirs), 1):
            conv_id = conv_dir.name
            conv_dest = dest / f"{i:03d}_{conv_id[:8]}"
            conv_dest.mkdir(parents=True, exist_ok=True)
            
            # Copy all .md files
            md_files = list(conv_dir.glob("*.md"))
            for f in md_files:
                shutil.copy2(f, conv_dest / f.name)
            
            # Also check .system_generated
            sys_dir = conv_dir / ".system_generated" / "logs"
            if sys_dir.exists():
                for f in sys_dir.glob("*.txt"):
                    shutil.copy2(f, conv_dest / f"_system_{f.name}")
            
            # Collect metadata for index
            mtime = conv_dir.stat().st_mtime
            index_entries.append({
                "num": i,
                "conv_id": conv_id,
                "files": [f.name for f in md_files],
                "mtime": datetime.fromtimestamp(mtime).isoformat(),
            })
        
        # Generate index
        index_path = dest / "_index.md"
        with open(index_path, "w", encoding="utf-8") as idx:
            idx.write("# Brain Artifacts Index\n\n")
            idx.write(f"Total conversations: {len(conv_dirs)}\n\n")
            idx.write("| # | Conv ID | Files | Last Modified |\n")
            idx.write("|---|---------|-------|---------------|\n")
            for e in index_entries:
                files_str = ", ".join(e["files"][:3])
                if len(e["files"]) > 3:
                    files_str += f" (+{len(e['files'])-3})"
                idx.write(f"| {e['num']} | {e['conv_id'][:12]} | {files_str} | {e['mtime'][:16]} |\n")
    
    result["status"] = "ok"
    return result


# PURPOSE: Layer 4 — Ochēma SessionStore エクスポート
def export_layer4_ochema(output_dir: Path, dry_run: bool = False) -> dict:
    """Export Ochēma SessionStore (Cortex API sessions) from SQLite."""
    result = {"layer": "04_ochema_sessions", "status": "skipped", "count": 0}
    
    if not OCHEMA_SESSIONS_DB.exists():
        result["error"] = f"sessions.db not found: {OCHEMA_SESSIONS_DB}"
        return result
    
    try:
        # Copy for faster I/O
        tmp_db = Path("/tmp/ochema_sessions_export.db")
        shutil.copy2(OCHEMA_SESSIONS_DB, tmp_db)
        
        conn = sqlite3.connect(str(tmp_db))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get all sessions
        sessions = cur.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        result["count"] = len(sessions)
        
        if not dry_run:
            dest = output_dir / "04_ochema_sessions"
            dest.mkdir(parents=True, exist_ok=True)
            
            # Export each session
            for session in sessions:
                session_id = session["id"]
                account = session["account"]
                model = session["model"]
                created = session["created_at"]
                
                # Get turns for this session
                turns = cur.execute(
                    "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at",
                    (session_id,)
                ).fetchall()
                
                # Write session file
                safe_id = session_id[:12]
                session_path = dest / f"session_{safe_id}.md"
                with open(session_path, "w", encoding="utf-8") as f:
                    f.write(f"# Session: {session_id}\n\n")
                    f.write(f"- **Account**: {account}\n")
                    f.write(f"- **Model**: {model}\n")
                    f.write(f"- **Created**: {created}\n")
                    f.write(f"- **Turns**: {len(turns)}\n\n")
                    f.write("---\n\n")
                    
                    for turn in turns:
                        role = turn["role"]
                        content = turn["content"]
                        ts = turn["created_at"]
                        f.write(f"### [{role}] {ts}\n\n")
                        f.write(f"{content}\n\n")
            
            # Generate index
            index_path = dest / "_index.md"
            with open(index_path, "w", encoding="utf-8") as idx:
                idx.write("# Ochēma Sessions Index\n\n")
                idx.write(f"Total sessions: {len(sessions)}\n\n")
                idx.write("| # | Session ID | Account | Model | Created | Turns |\n")
                idx.write("|---|-----------|---------|-------|---------|-------|\n")
                for i, s in enumerate(sessions, 1):
                    turns_count = cur.execute(
                        "SELECT COUNT(*) FROM turns WHERE session_id = ?",
                        (s["id"],)
                    ).fetchone()[0]
                    idx.write(f"| {i} | {s['id'][:12]} | {s['account']} | {s['model'][:20]} | {s['created_at'][:16]} | {turns_count} |\n")
        
        conn.close()
        if tmp_db.exists():
            tmp_db.unlink()
        
        result["status"] = "ok"
        
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


# PURPOSE: Layer 5 — IDE ログの圧縮コピー
def export_layer5_logs(output_dir: Path, dry_run: bool = False) -> dict:
    """Compress and copy Antigravity IDE logs."""
    result = {"layer": "05_logs", "status": "skipped", "count": 0}
    
    if not LOGS_DIR.exists():
        result["error"] = f"Logs directory not found: {LOGS_DIR}"
        return result
    
    log_sessions = sorted([d for d in LOGS_DIR.iterdir() if d.is_dir()])
    result["count"] = len(log_sessions)
    
    if not dry_run:
        dest = output_dir / "05_logs"
        dest.mkdir(parents=True, exist_ok=True)
        
        # Compress all log sessions into a single tarball
        tar_path = dest / "antigravity_logs.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for log_dir in log_sessions:
                tar.add(log_dir, arcname=log_dir.name)
        
        result["archive_size_mb"] = tar_path.stat().st_size / (1024 * 1024)
        
        # Also create a readable index
        index_path = dest / "_index.md"
        with open(index_path, "w", encoding="utf-8") as idx:
            idx.write("# Antigravity IDE Logs\n\n")
            idx.write(f"Total log sessions: {len(log_sessions)}\n")
            idx.write(f"Archive: `antigravity_logs.tar.gz`\n\n")
            idx.write("| # | Session | Files |\n")
            idx.write("|---|---------|-------|\n")
            for i, d in enumerate(log_sessions, 1):
                files = list(d.glob("*.log"))
                idx.write(f"| {i} | {d.name} | {len(files)} log files |\n")
    
    result["status"] = "ok"
    return result


# PURPOSE: MECE カバレッジ分析
def generate_coverage_report(output_dir: Path, results: list[dict]) -> None:
    """Generate MECE coverage analysis report."""
    report_path = output_dir / "MECE_coverage.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# MECE Coverage Analysis\n\n")
        f.write(f"Export Date: {datetime.now().isoformat()}\n\n")
        
        f.write("## Layer Summary\n\n")
        f.write("| Layer | Status | Count | Notes |\n")
        f.write("|-------|--------|-------|-------|\n")
        
        total_items = 0
        for r in results:
            status_icon = "✅" if r["status"] == "ok" else "❌" if r["status"] == "error" else "⏭️"
            notes = r.get("error", r.get("archive_size_mb", ""))
            if isinstance(notes, float):
                notes = f"{notes:.1f} MB"
            f.write(f"| {r['layer']} | {status_icon} {r['status']} | {r['count']} | {notes} |\n")
            total_items += r["count"]
        
        f.write(f"\n**Total items exported: {total_items}**\n\n")
        
        f.write("## Coverage Map\n\n")
        f.write("| Data Type | Covered By | MECE Status |\n")
        f.write("|-----------|-----------|-------------|\n")
        f.write("| Session summaries | Layer 1 (trajectorySummaries) | ✅ |\n")
        f.write("| Session-end knowledge | Layer 2 (Handoffs) | ✅ |\n")
        f.write("| Task/plan artifacts | Layer 3 (Brain) | ✅ |\n")
        f.write("| MCP LLM conversations | Layer 4 (Ochēma) | ✅ |\n")
        f.write("| IDE operation logs | Layer 5 (Logs) | ✅ |\n")
        f.write("| **Chat full text** | **CDP only** | ⚠️ **Not covered** |\n")
        
        f.write("\n## Gap Analysis\n\n")
        f.write("> [!WARNING]\n")
        f.write("> Chat full text (IDE Agent chat messages) is stored server-side on GCP.\n")
        f.write("> To export, start IDE with `--remote-debugging-port=9334` and run `export_chats.py`.\n")


# PURPOSE: マスターインデックス生成
def generate_master_index(output_dir: Path, results: list[dict]) -> None:
    """Generate master index file."""
    index_path = output_dir / "00_index.md"
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# MECE Session Export\n\n")
        f.write(f"Export Date: {datetime.now().isoformat()}\n")
        f.write(f"Source: WSL (Antigravity IDE)\n")
        f.write(f"Purpose: WIN migration preparation\n\n")
        
        f.write("## Contents\n\n")
        for r in results:
            status = "✅" if r["status"] == "ok" else "❌"
            f.write(f"- {status} **{r['layer']}** — {r['count']} items\n")
        
        f.write("\n## Quick Reference\n\n")
        f.write("| Directory | Description |\n")
        f.write("|-----------|-------------|\n")
        f.write("| `01_trajectory_summaries.*` | Antigravity session summaries |\n")
        f.write("| `02_handoffs/` | Session-end handoff documents |\n")
        f.write("| `03_brain_artifacts/` | Task plans, walkthroughs |\n")
        f.write("| `04_ochema_sessions/` | Cortex API conversation logs |\n")
        f.write("| `05_logs/` | IDE operation logs (compressed) |\n")
        f.write("| `MECE_coverage.md` | Coverage analysis |\n")


# PURPOSE: メインエントリポイント
def main():
    parser = argparse.ArgumentParser(description="MECE Session Log Export")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path.home() / f"export_mece_{datetime.now().strftime('%Y%m%d_%H%M')}",
        help="Output directory"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--layer", type=int, choices=[1, 2, 3, 4, 5], help="Export specific layer only")
    args = parser.parse_args()
    
    output_dir = args.output
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"╔══════════════════════════════════════════╗")
    print(f"║  MECE Session Export                     ║")
    print(f"║  Output: {str(output_dir)[:30]:30s}   ║")
    print(f"║  Dry run: {str(args.dry_run):5s}                        ║")
    print(f"╚══════════════════════════════════════════╝")
    print()
    
    layers = {
        1: ("Layer 1: Trajectory Summaries", export_layer1_trajectory),
        2: ("Layer 2: Handoffs", export_layer2_handoffs),
        3: ("Layer 3: Brain Artifacts", export_layer3_brain),
        4: ("Layer 4: Ochēma Sessions", export_layer4_ochema),
        5: ("Layer 5: IDE Logs", export_layer5_logs),
    }
    
    results = []
    for num, (name, func) in layers.items():
        if args.layer and args.layer != num:
            continue
        print(f"  ▶ {name}...", end=" ", flush=True)
        try:
            result = func(output_dir, dry_run=args.dry_run)
            status_icon = "✅" if result["status"] == "ok" else "❌"
            print(f"{status_icon} {result['count']} items")
            if result.get("error"):
                print(f"    ⚠️  {result['error']}")
        except Exception as e:  # noqa: BLE001
            result = {"layer": name, "status": "error", "count": 0, "error": str(e)}
            print(f"❌ {e}")
        results.append(result)
    
    if not args.dry_run:
        generate_master_index(output_dir, results)
        generate_coverage_report(output_dir, results)
        print()
        print(f"  ✅ Master index: {output_dir / '00_index.md'}")
        print(f"  ✅ Coverage: {output_dir / 'MECE_coverage.md'}")
    
    print()
    print("Done.")


if __name__ == "__main__":
    main()
