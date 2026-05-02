import os, sys

sd = os.path.dirname(os.path.abspath(__file__))
# この debug スクリプトは scripts/ と同じ場所に置く
# 80_運用｜Ops/_src｜ソースコード/scripts/
hgk = os.path.normpath(os.path.join(sd, "..", "..", ".."))

result = []
result.append(f"SCRIPT_DIR: {sd}")
result.append(f"HGK: {hgk}")
result.append(f"HGK_EXISTS: {os.path.isdir(hgk)}")

try:
    all_dirs = os.listdir(hgk)
    dirs_20 = [d for d in all_dirs if d.startswith("20_")]
    result.append(f"20_DIRS: {dirs_20}")
    if dirs_20:
        full = os.path.join(hgk, dirs_20[0])
        subs = [s for s in os.listdir(full) if s.startswith("_src")]
        result.append(f"SRC_SUBS: {subs}")
        if subs:
            cand = os.path.join(full, subs[0])
            has_mekhane = os.path.isdir(os.path.join(cand, "mekhane"))
            result.append(f"CANDIDATE: {cand}")
            result.append(f"HAS_MEKHANE: {has_mekhane}")
            if has_mekhane:
                sys.path.insert(0, cand)
                try:
                    from mekhane.ochema.antigravity_client import AntigravityClient
                    result.append("IMPORT: OK")
                except ImportError as e:
                    result.append(f"IMPORT: FAIL - {e}")
except Exception as e:
    result.append(f"ERROR: {e}")

out_path = os.path.join(sd, "debug_result.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(result))
print("\n".join(result))
