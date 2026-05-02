#!/usr/bin/env python3
"""brain/ の step data から過去セッションの会話を復元する。

出力: Markdown ファイル (セッションごと)。
内容: step output (アシスタント応答) + brain 内のアーティファクト一覧。
"""
import os
import sys
import time
from datetime import datetime

def recover_sessions(brain_root, output_dir):
    """全 brain ディレクトリからセッションを復元する。"""
    os.makedirs(output_dir, exist_ok=True)
    
    dirs = sorted(os.listdir(brain_root))
    stats = {"total": 0, "recovered": 0, "skipped": 0, "total_bytes": 0}
    
    for d in dirs:
        dpath = os.path.join(brain_root, d)
        if not os.path.isdir(dpath):
            continue
        
        steps_dir = os.path.join(dpath, ".system_generated", "steps")
        if not os.path.isdir(steps_dir):
            stats["skipped"] += 1
            continue
        
        # ステップディレクトリを数値順にソート
        step_dirs = []
        for s in os.listdir(steps_dir):
            sp = os.path.join(steps_dir, s)
            if os.path.isdir(sp):
                try:
                    step_dirs.append((int(s), sp))
                except ValueError:
                    step_dirs.append((0, sp))
        step_dirs.sort(key=lambda x: x[0])
        
        if not step_dirs:
            stats["skipped"] += 1
            continue
        
        stats["total"] += 1
        
        # セッション情報を収集
        cascade_id = d
        short_id = d[:12]
        
        # ディレクトリの mtime からタイムスタンプ推定
        try:
            mtime = os.path.getmtime(dpath)
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            date_str = "unknown"
            time_str = "unknown"
        
        # brain 直下のアーティファクトを収集
        artifacts = []
        for f in os.listdir(dpath):
            if f.startswith("."):
                continue
            fp = os.path.join(dpath, f)
            if os.path.isfile(fp):
                artifacts.append(f"{f} ({os.path.getsize(fp)} bytes)")
            elif os.path.isdir(fp):
                items = len(os.listdir(fp))
                artifacts.append(f"{f}/ ({items} items)")
        
        # タイトル推定: task.md があればそこから、なければ最初の step output から
        title = "Unknown Session"
        task_md = os.path.join(dpath, "task.md")
        if os.path.exists(task_md):
            try:
                with open(task_md, "r", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("#"):
                        title = first_line.lstrip("#").strip()
            except:
                pass
        
        # Markdown 生成
        lines = []
        lines.append(f"# {title}")
        lines.append(f"")
        lines.append(f"- **Cascade ID**: `{cascade_id}`")
        lines.append(f"- **Last Modified**: {time_str}")
        lines.append(f"- **Steps**: {len(step_dirs)}")
        lines.append(f"- **Source**: brain/ step data (アシスタント応答のみ)")
        lines.append(f"")
        
        if artifacts:
            lines.append(f"## アーティファクト")
            lines.append(f"")
            for a in artifacts:
                lines.append(f"- {a}")
            lines.append(f"")
        
        lines.append(f"---")
        lines.append(f"")
        
        # 各ステップの output を追加
        for step_num, step_path in step_dirs:
            out_file = os.path.join(step_path, "output.txt")
            if not os.path.exists(out_file):
                continue
            
            try:
                with open(out_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read().strip()
            except:
                continue
            
            if not content:
                continue
            
            lines.append(f"## Step {step_num}")
            lines.append(f"")
            lines.append(content)
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
        
        # ファイル書き出し
        out_name = f"brain_{short_id}_{date_str}.md"
        out_path = os.path.join(output_dir, out_name)
        content = "\n".join(lines)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        file_size = os.path.getsize(out_path)
        stats["recovered"] += 1
        stats["total_bytes"] += file_size
        
        # 進捗表示
        pct = stats["recovered"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  [{stats['recovered']:3d}] {out_name} ({file_size:,} bytes) — {title[:40]}")
    
    return stats


def main():
    brain_root = os.path.expanduser(r"~\.gemini\antigravity\brain")
    
    # HGK_ROOT 配下のセッション記録ディレクトリに出力
    hgk_root = os.environ.get("HGK_ROOT", "")
    if hgk_root:
        output_dir = os.path.join(hgk_root, "30_記憶｜Mneme", "01_記録｜Records", "sessions", "brain_recovery")
    else:
        output_dir = os.path.expanduser(r"~\.gemini\antigravity\sessions\brain_recovery")
    
    print(f"Brain root: {brain_root}")
    print(f"Output dir: {output_dir}")
    print(f"")
    
    stats = recover_sessions(brain_root, output_dir)
    
    total_kb = stats["total_bytes"] / 1024
    print(f"")
    print(f"=== 復元完了 ===")
    print(f"  復元: {stats['recovered']} セッション")
    print(f"  スキップ: {stats['skipped']} (step data なし)")
    print(f"  合計サイズ: {total_kb:.1f} KB")
    print(f"  出力先: {output_dir}")


if __name__ == "__main__":
    main()
