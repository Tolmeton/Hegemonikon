"""
BBH rho_fine direct measurement - FILE LOG VERSION
===================================================
All output goes to log file, not stdout.
"""
import json, math, os, re, ssl, sys, time, urllib.request, urllib.error

ENV_PATH = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\.env"
TASKS = ["temporal_sequences", "formal_fallacies", "boolean_expressions"]
N_SAMPLES = 30
MODEL = "gemini-3.1-flash-lite-preview"
OUT_DIR = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\10_知性｜Nous\04_企画｜Boulēsis\12_遊学｜Yugaku\03_忘却論｜Oblivion\experiments\results"
LOG_PATH = os.path.join(OUT_DIR, "experiment_log.txt")

os.makedirs(OUT_DIR, exist_ok=True)

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Clear log
with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write("")

log(f"=== BBH rho_fine experiment START ===")
log(f"Model: {MODEL}")

# === Load keys ===
keys = []
KEY_NAMES = {"GOOGLE_API_KEY", "GOOGLE_API_KEY_MOVEMENT", "GOOGLE_API_KEY_TOLMETON",
             "GOOGLE_API_KEY_RAIRAIXOXOXO", "GOOGLE_API_KEY_HRAIKI"}
with open(ENV_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() in KEY_NAMES:
                keys.append(v.strip())
log(f"Keys loaded: {len(keys)}")

key_idx = 0
def next_key():
    global key_idx
    k = keys[key_idx % len(keys)]
    key_idx += 1
    return k

# === Fetch BBH ===
def fetch_task(name):
    url = f"https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/main/bbh/{name}.json"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode())["examples"]

# === Prompt variants ===
VNAMES = ["v1_std", "v2_persona", "v3_struct", "v4_concise", "v5_verbose"]

def make_variants(q):
    return {
        "v1_std": f"{q}\n\nLet's think step by step.",
        "v2_persona": f"You are an expert logician.\n\n{q}\n\nLet's think step by step.",
        "v3_struct": f"{q}\n\nStep 1: Identify key info.\nStep 2: Reason logically.\nStep 3: State your answer.",
        "v4_concise": f"{q}\n\nThink carefully, then answer concisely.",
        "v5_verbose": f"Read carefully and think through every detail.\n\n{q}\n\nLet's think step by step.\nShow all reasoning, then clearly state your final answer.",
    }

# === Call Gemini ===
def call_api(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 512}
    }).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=payload,
                                        headers={"Content-Type": "application/json"}, method="POST")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                r = json.loads(resp.read().decode())
            cands = r.get("candidates", [])
            if cands:
                parts = cands[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 5
                log(f"  429 rate limit, wait {wait}s")
                time.sleep(wait)
            elif e.code == 503:
                time.sleep(3)
            else:
                log(f"  HTTP {e.code}")
                return ""
        except Exception as e:
            log(f"  Err: {type(e).__name__}: {e}")
            time.sleep(2)
    return ""

# === Check answer ===
def check_answer(response, target):
    t = target.strip().upper()
    r = response.upper()
    ms = re.findall(r'\(([A-Z])\)', r)
    if ms and t.startswith("("):
        return f"({ms[-1]})" == t
    for w in ["TRUE", "FALSE", "YES", "NO", "VALID", "INVALID"]:
        if t == w and w in r.split()[-15:]:
            return True
    return t in r

# === Main ===
log(f"Tasks: {TASKS}")
log(f"Samples/task: {N_SAMPLES}, Variants: {len(VNAMES)}")
log(f"Total calls: {len(TASKS) * N_SAMPLES * len(VNAMES)}")

all_results = {}
t0 = time.time()

for task in TASKS:
    log(f"--- TASK: {task} ---")
    try:
        examples = fetch_task(task)[:N_SAMPLES]
        log(f"  Loaded {len(examples)} examples")
    except Exception as e:
        log(f"  FETCH ERROR: {e}")
        continue

    tr = {v: [] for v in VNAMES}

    for i, ex in enumerate(examples):
        vs = make_variants(ex["input"])
        for vn in VNAMES:
            resp = call_api(vs[vn], next_key())
            ok = check_answer(resp, ex["target"]) if resp else False
            tr[vn].append(1 if ok else 0)
            time.sleep(0.15)

        if (i + 1) % 5 == 0:
            accs = {v: sum(tr[v]) / len(tr[v]) * 100 for v in tr}
            s = " ".join([f"{v[3:]}:{accs[v]:.0f}" for v in accs])
            elapsed = time.time() - t0
            log(f"  [{i+1}/{N_SAMPLES}] {s} ({elapsed:.0f}s)")

    all_results[task] = tr
    acc_str = " ".join([f"{v[3:]}={sum(tr[v])/len(tr[v])*100:.1f}%" for v in tr])
    log(f"  DONE: {acc_str}")

# === Compute eta-squared ===
log("--- ETA-SQUARED ---")
eta2s = []
for task in TASKS:
    tr = all_results[task]
    accs = {v: sum(tr[v]) / len(tr[v]) * 100 for v in tr}
    gm = sum(accs.values()) / len(accs)
    ss_b = N_SAMPLES * sum((accs[v] - gm) ** 2 for v in accs)
    all_scores = []
    for v in tr:
        all_scores.extend([x * 100 for x in tr[v]])
    tm = sum(all_scores) / len(all_scores)
    ss_t = sum((x - tm) ** 2 for x in all_scores)
    e2 = ss_b / ss_t if ss_t > 0 else 0
    eta2s.append(e2)
    acc_str = ", ".join([f"{v[3:]}={accs[v]:.1f}" for v in accs])
    log(f"  {task}: eta2={e2:.6f} ({acc_str})")

rho = sum(eta2s) / len(eta2s)
sd = math.sqrt(sum((x - rho) ** 2 for x in eta2s) / len(eta2s))
log(f"--- FINAL ---")
log(f"rho_fine = {rho:.6f} (SD={sd:.6f})")
log(f"range = [{min(eta2s):.6f}, {max(eta2s):.6f}]")
for K in [5, 8]:
    r_ceil = math.sqrt(rho / (K + 1)) if rho > 0 else 0
    log(f"r_ceiling (K={K}) = {r_ceil:.4f} ({r_ceil*100:.1f}%)")

if 0.005 <= rho <= 0.10:
    log("VERDICT: SUPPORTED")
elif rho < 0.005:
    log("VERDICT: LOWER")
else:
    log("VERDICT: HIGHER")

elapsed = time.time() - t0
log(f"Total: {elapsed:.0f}s ({elapsed/60:.1f}min)")

# Save JSON
out = {
    "experiment": "bbh_rho_fine_direct",
    "model": MODEL,
    "n_samples": N_SAMPLES,
    "tasks": TASKS,
    "variants": VNAMES,
    "rho_fine_mean": rho,
    "rho_fine_sd": sd,
    "per_task_eta2": {t: eta2s[i] for i, t in enumerate(TASKS)},
    "per_task_accs": {
        t: {v: sum(all_results[t][v]) / len(all_results[t][v]) * 100 for v in all_results[t]}
        for t in TASKS
    },
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "elapsed_seconds": elapsed,
}
outpath = os.path.join(OUT_DIR, "rho_fine_direct.json")
with open(outpath, "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
log(f"JSON saved: {outpath}")
log("=== DONE ===")

# Also print final to stdout for terminal
print(f"DONE. rho_fine={rho:.6f}. See {LOG_PATH}", flush=True)
