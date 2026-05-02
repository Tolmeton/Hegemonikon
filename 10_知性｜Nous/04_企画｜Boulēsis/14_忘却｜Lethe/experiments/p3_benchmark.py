#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→P3検証→CCL embedding vs text embedding
"""
P3 検証実験: CCL embedding vs Text embedding — 構造的同型検出の比較

VISION.md §5.2 P3:
  「CCL embedding が text embedding より構造的同型の検出率で優れる」

実験設計:
  1. 構造的に同型な関数ペア (名前は違うが構造は同一) を 20+ 組作成
  2. 各関数を (a) ソースコードそのまま (b) CCL 構造式に変換 の2通りで embedding
  3. ペア内の cosine 類似度を比較 + recall@k を計算
  4. CCL embedding が text embedding を上回れば P3 支持

理論的基盤:
  - code_ingest.py の python_to_ccl(): 忘却関手 U: Code → CCL
  - aletheia.md の U⊣N 随伴: 構造保存マッチング

Usage:
  python p3_benchmark.py --dry-run   # CCL 変換のみ確認 (API 呼出なし)
  python p3_benchmark.py             # 本実験
  python p3_benchmark.py --verbose   # 詳細出力
"""

# PURPOSE: P3 検証実験のベンチマークデータ + 実験ハーネス

import sys
import os
import ast
import json
import argparse
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# パス設定
_HGK_ROOT = Path(__file__).parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.symploke.code_ingest import python_to_ccl


# ============================================================
# ベンチマークデータ: 構造的同型コードペア
# ============================================================

# PURPOSE: 1つの関数ペア (構造的に同型、名前は異なる)
@dataclass
class StructuralPair:
    """構造的に同型な関数ペア。"""
    pair_id: str
    pattern: str           # 構造パターンの説明
    func_a_source: str     # 関数 A のソースコード
    func_b_source: str     # 関数 B のソースコード
    expected_ccl: str = "" # 期待される CCL 構造式 (検証用、空でも可)


# PURPOSE: 構造パターン別のベンチマークデータを生成
def create_benchmark_pairs() -> list[StructuralPair]:
    """構造的に同型な関数ペアをカテゴリ別に生成する。

    各ペアは「名前は完全に異なるが、構造 (射) は同型」。
    Aletheia §2.1 の U_arrow (n=1) テストケース。
    """
    pairs = []

    # --- パターン 1: filter → map → aggregate ---
    pairs.append(StructuralPair(
        pair_id="P01",
        pattern="filter → map → aggregate",
        func_a_source=textwrap.dedent("""\
            def process_orders(orders):
                valid = [o for o in orders if o.status == "active"]
                totals = [calculate_total(o) for o in valid]
                return sum(totals) / len(totals)
        """),
        func_b_source=textwrap.dedent("""\
            def average_score(students):
                enrolled = [s for s in students if s.enrolled]
                scores = [s.grade for s in enrolled]
                return sum(scores) / len(scores)
        """),
    ))

    # --- パターン 2: validate → transform → persist ---
    pairs.append(StructuralPair(
        pair_id="P02",
        pattern="validate → transform → persist",
        func_a_source=textwrap.dedent("""\
            def process_user_input(raw_data):
                if not raw_data.get("name"):
                    raise ValueError("Name required")
                cleaned = sanitize(raw_data)
                save_to_database(cleaned)
                return cleaned
        """),
        func_b_source=textwrap.dedent("""\
            def ingest_log_entry(log_line):
                if not log_line.strip():
                    raise ValueError("Empty log")
                parsed = parse_log_format(log_line)
                write_to_storage(parsed)
                return parsed
        """),
    ))

    # --- パターン 3: fetch → parse → cache ---
    pairs.append(StructuralPair(
        pair_id="P03",
        pattern="fetch → parse → cache",
        func_a_source=textwrap.dedent("""\
            def load_config(url):
                response = requests.get(url)
                config = json.loads(response.text)
                cache[url] = config
                return config
        """),
        func_b_source=textwrap.dedent("""\
            def download_image_metadata(endpoint):
                data = http_client.fetch(endpoint)
                metadata = parse_exif(data)
                store[endpoint] = metadata
                return metadata
        """),
    ))

    # --- パターン 4: iterate → check → accumulate ---
    pairs.append(StructuralPair(
        pair_id="P04",
        pattern="iterate → check → accumulate",
        func_a_source=textwrap.dedent("""\
            def count_valid_entries(records):
                count = 0
                for record in records:
                    if record.is_valid():
                        count += 1
                return count
        """),
        func_b_source=textwrap.dedent("""\
            def sum_active_balances(accounts):
                total = 0
                for account in accounts:
                    if account.is_active():
                        total += 1
                return total
        """),
    ))

    # --- パターン 5: try → operation → except → fallback ---
    pairs.append(StructuralPair(
        pair_id="P05",
        pattern="try → operation → except → fallback",
        func_a_source=textwrap.dedent("""\
            def safe_file_read(path):
                try:
                    with open(path) as f:
                        return f.read()
                except FileNotFoundError:
                    return default_content()
        """),
        func_b_source=textwrap.dedent("""\
            def resilient_api_call(url):
                try:
                    response = requests.get(url)
                    return response.json()
                except ConnectionError:
                    return cached_response()
        """),
    ))

    # --- パターン 6: map → sort → take_top ---
    pairs.append(StructuralPair(
        pair_id="P06",
        pattern="map → sort → slice",
        func_a_source=textwrap.dedent("""\
            def top_performers(employees):
                scored = [(e, evaluate(e)) for e in employees]
                ranked = sorted(scored, key=lambda x: x[1], reverse=True)
                return ranked[:10]
        """),
        func_b_source=textwrap.dedent("""\
            def best_products(catalog):
                rated = [(p, compute_rating(p)) for p in catalog]
                ordered = sorted(rated, key=lambda x: x[1], reverse=True)
                return ordered[:10]
        """),
    ))

    # --- パターン 7: group_by → aggregate_each ---
    pairs.append(StructuralPair(
        pair_id="P07",
        pattern="group_by → aggregate_each",
        func_a_source=textwrap.dedent("""\
            def sales_by_region(transactions):
                groups = {}
                for t in transactions:
                    groups.setdefault(t.region, []).append(t.amount)
                return {k: sum(v) for k, v in groups.items()}
        """),
        func_b_source=textwrap.dedent("""\
            def errors_by_service(logs):
                buckets = {}
                for log in logs:
                    buckets.setdefault(log.service, []).append(log.severity)
                return {k: len(v) for k, v in buckets.items()}
        """),
    ))

    # --- パターン 8: chain of transforms ---
    pairs.append(StructuralPair(
        pair_id="P08",
        pattern="linear pipeline (3 transforms)",
        func_a_source=textwrap.dedent("""\
            def text_to_features(raw_text):
                tokens = tokenize(raw_text)
                filtered = remove_stopwords(tokens)
                return compute_tfidf(filtered)
        """),
        func_b_source=textwrap.dedent("""\
            def audio_to_spectrum(signal):
                windowed = apply_window(signal)
                transformed = fft(windowed)
                return magnitude_spectrum(transformed)
        """),
    ))

    # --- パターン 9: conditional branching with return ---
    pairs.append(StructuralPair(
        pair_id="P09",
        pattern="if-elif-else routing",
        func_a_source=textwrap.dedent("""\
            def classify_age(age):
                if age < 13:
                    return "child"
                elif age < 20:
                    return "teen"
                else:
                    return "adult"
        """),
        func_b_source=textwrap.dedent("""\
            def categorize_weight(kg):
                if kg < 50:
                    return "light"
                elif kg < 80:
                    return "medium"
                else:
                    return "heavy"
        """),
    ))

    # --- パターン 10: recursive accumulation ---
    pairs.append(StructuralPair(
        pair_id="P10",
        pattern="recursive flatten",
        func_a_source=textwrap.dedent("""\
            def flatten_tree(node):
                result = [node.value]
                for child in node.children:
                    result.extend(flatten_tree(child))
                return result
        """),
        func_b_source=textwrap.dedent("""\
            def collect_files(directory):
                paths = [directory.name]
                for sub in directory.subdirs:
                    paths.extend(collect_files(sub))
                return paths
        """),
    ))

    # --- パターン 11: dict lookup with default ---
    pairs.append(StructuralPair(
        pair_id="P11",
        pattern="lookup → default → transform",
        func_a_source=textwrap.dedent("""\
            def get_user_display_name(user_id, registry):
                user = registry.get(user_id, None)
                if user is None:
                    return "Unknown"
                return format_name(user)
        """),
        func_b_source=textwrap.dedent("""\
            def resolve_symbol(token, symbol_table):
                entry = symbol_table.get(token, None)
                if entry is None:
                    return "undefined"
                return format_type(entry)
        """),
    ))

    # --- パターン 12: map-filter pipeline with comprehension ---
    pairs.append(StructuralPair(
        pair_id="P12",
        pattern="comprehension: map + filter",
        func_a_source=textwrap.dedent("""\
            def active_emails(users):
                return [u.email for u in users if u.active and u.email]
        """),
        func_b_source=textwrap.dedent("""\
            def published_titles(articles):
                return [a.title for a in articles if a.published and a.title]
        """),
    ))

    # --- パターン 13: wrap → execute → unwrap (decorator pattern) ---
    pairs.append(StructuralPair(
        pair_id="P13",
        pattern="wrap → execute → unwrap",
        func_a_source=textwrap.dedent("""\
            def timed_execution(func, args):
                start = time.time()
                result = func(*args)
                elapsed = time.time() - start
                return result, elapsed
        """),
        func_b_source=textwrap.dedent("""\
            def metered_call(handler, params):
                begin = time.monotonic()
                output = handler(*params)
                duration = time.monotonic() - begin
                return output, duration
        """),
    ))

    # --- パターン 14: reduce / fold ---
    pairs.append(StructuralPair(
        pair_id="P14",
        pattern="reduce (left fold)",
        func_a_source=textwrap.dedent("""\
            def merge_configs(configs):
                result = {}
                for cfg in configs:
                    result.update(cfg)
                return result
        """),
        func_b_source=textwrap.dedent("""\
            def combine_patches(patches):
                merged = {}
                for patch in patches:
                    merged.update(patch)
                return merged
        """),
    ))

    # --- パターン 15: enumerate with index tracking ---
    pairs.append(StructuralPair(
        pair_id="P15",
        pattern="enumerate + conditional collect",
        func_a_source=textwrap.dedent("""\
            def find_error_lines(lines):
                errors = []
                for i, line in enumerate(lines):
                    if "ERROR" in line:
                        errors.append((i, line))
                return errors
        """),
        func_b_source=textwrap.dedent("""\
            def locate_keywords(paragraphs):
                matches = []
                for idx, para in enumerate(paragraphs):
                    if "IMPORTANT" in para:
                        matches.append((idx, para))
                return matches
        """),
    ))

    # --- パターン 16: nested iteration → flat result ---
    pairs.append(StructuralPair(
        pair_id="P16",
        pattern="nested loop → flat collect",
        func_a_source=textwrap.dedent("""\
            def all_pairs(items):
                result = []
                for i in items:
                    for j in items:
                        if i != j:
                            result.append((i, j))
                return result
        """),
        func_b_source=textwrap.dedent("""\
            def cross_product(set_a, set_b):
                pairs = []
                for a in set_a:
                    for b in set_b:
                        if a != b:
                            pairs.append((a, b))
                return pairs
        """),
    ))

    # --- パターン 17: factory (条件による生成) ---
    pairs.append(StructuralPair(
        pair_id="P17",
        pattern="factory dispatch",
        func_a_source=textwrap.dedent("""\
            def create_shape(shape_type):
                if shape_type == "circle":
                    return Circle()
                elif shape_type == "square":
                    return Square()
                else:
                    return Default()
        """),
        func_b_source=textwrap.dedent("""\
            def make_handler(protocol):
                if protocol == "http":
                    return HttpHandler()
                elif protocol == "grpc":
                    return GrpcHandler()
                else:
                    return FallbackHandler()
        """),
    ))

    # --- パターン 18: zip → merge ---
    pairs.append(StructuralPair(
        pair_id="P18",
        pattern="zip two lists → dict",
        func_a_source=textwrap.dedent("""\
            def build_mapping(keys, values):
                result = {}
                for k, v in zip(keys, values):
                    result[k] = v
                return result
        """),
        func_b_source=textwrap.dedent("""\
            def create_bindings(names, addresses):
                table = {}
                for name, addr in zip(names, addresses):
                    table[name] = addr
                return table
        """),
    ))

    # --- パターン 19: while loop with break ---
    pairs.append(StructuralPair(
        pair_id="P19",
        pattern="while search → break on find",
        func_a_source=textwrap.dedent("""\
            def find_first_match(items, predicate):
                idx = 0
                while idx < len(items):
                    if predicate(items[idx]):
                        return items[idx]
                    idx += 1
                return None
        """),
        func_b_source=textwrap.dedent("""\
            def locate_entry(records, check):
                pos = 0
                while pos < len(records):
                    if check(records[pos]):
                        return records[pos]
                    pos += 1
                return None
        """),
    ))

    # --- パターン 20: batch processing ---
    pairs.append(StructuralPair(
        pair_id="P20",
        pattern="batch split → process each → collect",
        func_a_source=textwrap.dedent("""\
            def process_in_batches(items, batch_size):
                results = []
                for i in range(0, len(items), batch_size):
                    batch = items[i:i+batch_size]
                    results.extend(transform_batch(batch))
                return results
        """),
        func_b_source=textwrap.dedent("""\
            def upload_chunks(data, chunk_size):
                responses = []
                for start in range(0, len(data), chunk_size):
                    chunk = data[start:start+chunk_size]
                    responses.extend(send_chunk(chunk))
                return responses
        """),
    ))

    # === 対照群: 構造的に非同型なペア (negative samples) ===

    pairs.append(StructuralPair(
        pair_id="N01",
        pattern="[NEGATIVE] linear vs recursive",
        func_a_source=textwrap.dedent("""\
            def sum_list(numbers):
                total = 0
                for n in numbers:
                    total += n
                return total
        """),
        func_b_source=textwrap.dedent("""\
            def flatten_tree(node):
                result = [node.value]
                for child in node.children:
                    result.extend(flatten_tree(child))
                return result
        """),
    ))

    pairs.append(StructuralPair(
        pair_id="N02",
        pattern="[NEGATIVE] simple vs complex branching",
        func_a_source=textwrap.dedent("""\
            def double(x):
                return x * 2
        """),
        func_b_source=textwrap.dedent("""\
            def complex_dispatch(data):
                if data.type == "A":
                    result = handle_a(data)
                    if result.ok:
                        save(result)
                    else:
                        log_error(result)
                else:
                    fallback(data)
                return result
        """),
    ))

    pairs.append(StructuralPair(
        pair_id="N03",
        pattern="[NEGATIVE] map vs try-except",
        func_a_source=textwrap.dedent("""\
            def transform_all(items):
                return [process(item) for item in items]
        """),
        func_b_source=textwrap.dedent("""\
            def safe_operation(value):
                try:
                    result = risky_compute(value)
                    return result
                except Exception:
                    return default_value()
        """),
    ))

    pairs.append(StructuralPair(
        pair_id="N04",
        pattern="[NEGATIVE] filter vs nested loop",
        func_a_source=textwrap.dedent("""\
            def get_active(users):
                return [u for u in users if u.active]
        """),
        func_b_source=textwrap.dedent("""\
            def matrix_multiply(a, b):
                result = []
                for row in a:
                    new_row = []
                    for col_idx in range(len(b[0])):
                        val = sum(row[i] * b[i][col_idx] for i in range(len(row)))
                        new_row.append(val)
                    result.append(new_row)
                return result
        """),
    ))

    pairs.append(StructuralPair(
        pair_id="N05",
        pattern="[NEGATIVE] aggregate vs factory",
        func_a_source=textwrap.dedent("""\
            def total_revenue(orders):
                return sum(o.amount for o in orders)
        """),
        func_b_source=textwrap.dedent("""\
            def create_connection(db_type):
                if db_type == "postgres":
                    return PostgresConn()
                elif db_type == "mysql":
                    return MysqlConn()
                else:
                    raise ValueError(f"Unknown: {db_type}")
        """),
    ))

    # === Hard Negative: 構造的に近いが微細に異なるペア ===

    # N06: for + if + accumulate vs for + accumulate (分岐の有無)
    pairs.append(StructuralPair(
        pair_id="N06",
        pattern="[HARD NEG] with-branch vs no-branch accumulate",
        func_a_source=textwrap.dedent("""\
            def count_valid(items):
                count = 0
                for item in items:
                    if item.is_valid():
                        count += 1
                return count
        """),
        func_b_source=textwrap.dedent("""\
            def sum_all(items):
                total = 0
                for item in items:
                    total += item.value
                return total
        """),
    ))

    # N07: for ループ vs while ループ (同じ accumulate だがループ種類が異なる)
    pairs.append(StructuralPair(
        pair_id="N07",
        pattern="[HARD NEG] for-loop vs while-loop accumulate",
        func_a_source=textwrap.dedent("""\
            def collect_names(users):
                names = []
                for user in users:
                    names.append(user.name)
                return names
        """),
        func_b_source=textwrap.dedent("""\
            def read_lines(stream):
                lines = []
                line = stream.readline()
                while line:
                    lines.append(line)
                    line = stream.readline()
                return lines
        """),
    ))

    # N08: filter→map vs map→filter (操作順序の逆転)
    pairs.append(StructuralPair(
        pair_id="N08",
        pattern="[HARD NEG] filter-then-map vs map-then-filter",
        func_a_source=textwrap.dedent("""\
            def active_names(users):
                active = [u for u in users if u.active]
                return [u.name for u in active]
        """),
        func_b_source=textwrap.dedent("""\
            def valid_results(items):
                transformed = [process(item) for item in items]
                return [r for r in transformed if r.is_valid()]
        """),
    ))

    # N09: 単一 return vs 多段 return (早期 return の有無)
    pairs.append(StructuralPair(
        pair_id="N09",
        pattern="[HARD NEG] single-return vs early-return",
        func_a_source=textwrap.dedent("""\
            def compute_price(item):
                base = item.base_price
                tax = base * 0.1
                return base + tax
        """),
        func_b_source=textwrap.dedent("""\
            def compute_discount(item):
                if item.is_member:
                    return item.price * 0.8
                if item.has_coupon:
                    return item.price * 0.9
                return item.price
        """),
    ))

    # N10: 純粋な写像 vs 副作用を伴う写像
    pairs.append(StructuralPair(
        pair_id="N10",
        pattern="[HARD NEG] pure-map vs side-effecting map",
        func_a_source=textwrap.dedent("""\
            def double_all(numbers):
                return [n * 2 for n in numbers]
        """),
        func_b_source=textwrap.dedent("""\
            def process_and_log(items):
                results = []
                for item in items:
                    result = transform(item)
                    logger.info(f"Processed {item}")
                    results.append(result)
                return results
        """),
    ))

    # === Easy Negative: 構造的に全く異なるペア ===

    # N11: 再帰的木探索 vs 線形 3段パイプライン
    pairs.append(StructuralPair(
        pair_id="N11",
        pattern="[EASY NEG] recursive-tree vs linear-pipeline",
        func_a_source=textwrap.dedent("""\
            def search_tree(node, target):
                if node.value == target:
                    return node
                for child in node.children:
                    result = search_tree(child, target)
                    if result:
                        return result
                return None
        """),
        func_b_source=textwrap.dedent("""\
            def clean_text(raw):
                stripped = raw.strip()
                lowered = stripped.lower()
                return lowered.replace("  ", " ")
        """),
    ))

    # N12: ジェネレータ (yield) vs 即時 dict 構築
    pairs.append(StructuralPair(
        pair_id="N12",
        pattern="[EASY NEG] generator vs dict-builder",
        func_a_source=textwrap.dedent("""\
            def fibonacci(n):
                a, b = 0, 1
                for _ in range(n):
                    yield a
                    a, b = b, a + b
        """),
        func_b_source=textwrap.dedent("""\
            def build_index(documents):
                index = {}
                for doc in documents:
                    for word in doc.words:
                        index.setdefault(word, []).append(doc.id)
                return index
        """),
    ))

    # N13: クラス初期化 vs 関数合成
    pairs.append(StructuralPair(
        pair_id="N13",
        pattern="[EASY NEG] class-init vs function-composition",
        func_a_source=textwrap.dedent("""\
            def create_config(name, port, debug):
                config = {}
                config["name"] = name
                config["port"] = port
                config["debug"] = debug
                config["version"] = "1.0"
                return config
        """),
        func_b_source=textwrap.dedent("""\
            def pipeline(data):
                step1 = normalize(data)
                step2 = validate(step1)
                step3 = enrich(step2)
                step4 = compress(step3)
                return encrypt(step4)
        """),
    ))

    # N14: エラー処理チェーン vs 数学計算
    pairs.append(StructuralPair(
        pair_id="N14",
        pattern="[EASY NEG] error-chain vs math-computation",
        func_a_source=textwrap.dedent("""\
            def safe_parse(text):
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    try:
                        data = yaml.safe_load(text)
                    except yaml.YAMLError:
                        return None
                return data
        """),
        func_b_source=textwrap.dedent("""\
            def distance(p1, p2):
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                return (dx ** 2 + dy ** 2) ** 0.5
        """),
    ))

    # N15: 状態機械 (while + state) vs 内包表記
    pairs.append(StructuralPair(
        pair_id="N15",
        pattern="[EASY NEG] state-machine vs comprehension",
        func_a_source=textwrap.dedent("""\
            def tokenize(text):
                tokens = []
                current = ""
                state = "start"
                for ch in text:
                    if state == "start":
                        if ch.isalpha():
                            current = ch
                            state = "word"
                    elif state == "word":
                        if ch.isalpha():
                            current += ch
                        else:
                            tokens.append(current)
                            current = ""
                            state = "start"
                if current:
                    tokens.append(current)
                return tokens
        """),
        func_b_source=textwrap.dedent("""\
            def even_squares(numbers):
                return [n ** 2 for n in numbers if n % 2 == 0]
        """),
    ))

    return pairs


# ============================================================
# CCL 変換ユーティリティ
# ============================================================

# PURPOSE: ソースコード文字列 → AST → CCL 構造式
def source_to_ccl(source: str) -> str:
    """Python ソースコードを CCL 構造式に変換する。

    忘却関手 U: Code → CCL の適用。
    名前 (対象) を忘却し、射 (構造) のみを保存する。
    """
    source = textwrap.dedent(source).strip()
    tree = ast.parse(source)

    # 最初の関数定義を取得
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return python_to_ccl(node)

    # 関数定義がない場合はモジュール全体をステートメント列として処理
    from mekhane.symploke.code_ingest import _stmt_to_ccl
    parts = []
    for stmt in tree.body:
        ccl = _stmt_to_ccl(stmt)
        if ccl:
            parts.append(ccl)
    return " >> ".join(parts) if parts else "_"


# ============================================================
# 実験ハーネス
# ============================================================

@dataclass
class PairResult:
    """1ペアの実験結果。"""
    pair_id: str
    pattern: str
    is_positive: bool          # True=同型ペア, False=非同型
    ccl_a: str
    ccl_b: str
    text_similarity: float = 0.0
    ccl_similarity: float = 0.0
    ccl_exact_match: bool = False  # CCL 構造式が完全一致するか


# PURPOSE: 全ペアの CCL 変換を実行し、dry-run 結果を表示
def run_dry(pairs: list[StructuralPair], verbose: bool = False) -> list[PairResult]:
    """Dry-run: CCL 変換のみ実行し、結果を表示。"""
    results = []
    print("=" * 80)
    print("  P3 検証実験 — Dry Run (CCL 変換のみ)")
    print("=" * 80)

    for pair in pairs:
        is_positive = not pair.pair_id.startswith("N")
        ccl_a = source_to_ccl(pair.func_a_source)
        ccl_b = source_to_ccl(pair.func_b_source)
        exact_match = ccl_a == ccl_b

        result = PairResult(
            pair_id=pair.pair_id,
            pattern=pair.pattern,
            is_positive=is_positive,
            ccl_a=ccl_a,
            ccl_b=ccl_b,
            ccl_exact_match=exact_match,
        )
        results.append(result)

        marker = "✅" if is_positive else "❌"
        match_icon = "≡" if exact_match else "≠"
        print(f"\n{marker} {pair.pair_id}: {pair.pattern}")
        print(f"   CCL A: {ccl_a}")
        print(f"   CCL B: {ccl_b}")
        print(f"   一致 : {match_icon} {'完全一致' if exact_match else '不一致'}")

        if verbose:
            print(f"   SRC A: {pair.func_a_source.strip()[:80]}...")
            print(f"   SRC B: {pair.func_b_source.strip()[:80]}...")

    # 統計
    positives = [r for r in results if r.is_positive]
    negatives = [r for r in results if not r.is_positive]
    pos_exact = sum(1 for r in positives if r.ccl_exact_match)
    neg_exact = sum(1 for r in negatives if r.ccl_exact_match)

    print("\n" + "=" * 80)
    print("  CCL 変換 統計")
    print("=" * 80)
    print(f"  正例ペア: {len(positives)} 件 (CCL 完全一致 {pos_exact}/{len(positives)})")
    print(f"  負例ペア: {len(negatives)} 件 (CCL 完全一致 {neg_exact}/{len(negatives)})")
    print(f"  → CCL 完全一致率: 正例={pos_exact/len(positives)*100:.0f}% / 負例={neg_exact/len(negatives)*100:.0f}%")
    print()

    if pos_exact / len(positives) > 0.5:
        print("  [主観] CCL 変換だけで正例の過半数が完全一致。")
        print("         embedding 以前に、CCL 構造式レベルで構造的同型が検出できている。")
        print("         → P3 は CCL 変換の品質次第で P2 に帰着する可能性がある。")
    else:
        print("  [主観] CCL 変換の完全一致率が低い。")
        print("         embedding による「近似マッチング」が重要になる。")
        print("         → P3 の本来の実験 (embedding 比較) が意味を持つ。")

    return results


# PURPOSE: 本実験 — embedding 比較
def run_experiment(pairs: list[StructuralPair], verbose: bool = False) -> list[PairResult]:
    """本実験: text embedding と CCL embedding の比較。"""
    # CCL 変換
    print("📋 Step 1: CCL 変換...")
    ccl_data = []
    for pair in pairs:
        ccl_a = source_to_ccl(pair.func_a_source)
        ccl_b = source_to_ccl(pair.func_b_source)
        ccl_data.append((ccl_a, ccl_b))

    # Embedder 初期化
    print("🔌 Step 2: Embedder 初期化...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    from mekhane.anamnesis.vertex_embedder import VertexEmbedder
    embedder = VertexEmbedder()
    print(f"   Model: {embedder.model_name}, Dim: {embedder._dimension}")

    # テキスト embedding (ソースコードそのまま)
    print("📊 Step 3: Text embedding 取得...")
    text_sources = []
    for pair in pairs:
        text_sources.append(pair.func_a_source.strip())
        text_sources.append(pair.func_b_source.strip())
    text_embeddings = embedder.embed_batch(text_sources)

    # CCL embedding
    print("📊 Step 4: CCL embedding 取得...")
    ccl_sources = []
    for ccl_a, ccl_b in ccl_data:
        ccl_sources.append(ccl_a)
        ccl_sources.append(ccl_b)
    ccl_embeddings = embedder.embed_batch(ccl_sources)

    # 類似度計算
    print("📊 Step 5: 類似度計算...")
    from mekhane.anamnesis.embedder_mixin import _l2_normalize

    results = []
    for i, pair in enumerate(pairs):
        is_positive = not pair.pair_id.startswith("N")
        ccl_a, ccl_b = ccl_data[i]

        # L2 正規化してコサイン類似度を計算
        text_vec_a = _l2_normalize(text_embeddings[i * 2])
        text_vec_b = _l2_normalize(text_embeddings[i * 2 + 1])
        text_sim = sum(a * b for a, b in zip(text_vec_a, text_vec_b))
        text_sim = max(0.0, min(1.0, text_sim))

        ccl_vec_a = _l2_normalize(ccl_embeddings[i * 2])
        ccl_vec_b = _l2_normalize(ccl_embeddings[i * 2 + 1])
        ccl_sim = sum(a * b for a, b in zip(ccl_vec_a, ccl_vec_b))
        ccl_sim = max(0.0, min(1.0, ccl_sim))

        result = PairResult(
            pair_id=pair.pair_id,
            pattern=pair.pattern,
            is_positive=is_positive,
            ccl_a=ccl_a,
            ccl_b=ccl_b,
            text_similarity=text_sim,
            ccl_similarity=ccl_sim,
            ccl_exact_match=(ccl_a == ccl_b),
        )
        results.append(result)

    # recall@k 計算
    print("📊 Step 6: Recall@k 計算...")
    recall_results = compute_recall_at_k(
        pairs, text_embeddings, ccl_embeddings, k_values=[1, 3, 5]
    )

    # 結果出力
    # 統計的検定
    print("📊 Step 6b: 統計的検定...")
    stat_results = compute_statistical_tests(results)

    print_results(results, recall_results, stat_results, verbose)

    # 結果ファイル保存
    output_path = Path(__file__).parent / "p3_results.md"
    save_results(results, recall_results, stat_results, output_path)
    print(f"\n💾 結果を保存: {output_path}")

    return results


# ============================================================
# 統計的検定
# ============================================================

import math
import random

# PURPOSE: 統計的有意性検定を一括計算
def compute_statistical_tests(results: list[PairResult]) -> dict:
    """正例で CCL > Text を統計的に検定し、正負分離の効果量を計算する。

    返り値:
      wilcoxon: {statistic, p_value, effect_r, n, significant}
      auc: {text, ccl, text_ci, ccl_ci}
      cohens_d: {text, ccl}
    """
    positives = [r for r in results if r.is_positive]
    negatives = [r for r in results if not r.is_positive]

    # --- Wilcoxon signed-rank test (正例のみ: CCL sim vs Text sim) ---
    text_sims = [r.text_similarity for r in positives]
    ccl_sims = [r.ccl_similarity for r in positives]
    wilcoxon_result = _wilcoxon_test(text_sims, ccl_sims)

    # --- AUC-ROC (正例 vs 負例の判別力) ---
    pos_text_sims = [r.text_similarity for r in positives]
    neg_text_sims = [r.text_similarity for r in negatives]
    pos_ccl_sims = [r.ccl_similarity for r in positives]
    neg_ccl_sims = [r.ccl_similarity for r in negatives]

    auc_text = _compute_auc(pos_text_sims, neg_text_sims)
    auc_ccl = _compute_auc(pos_ccl_sims, neg_ccl_sims)
    ci_text = _bootstrap_auc_ci(pos_text_sims, neg_text_sims)
    ci_ccl = _bootstrap_auc_ci(pos_ccl_sims, neg_ccl_sims)

    # --- Cohen's d (正負分離の効果量) ---
    d_text = _cohens_d(pos_text_sims, neg_text_sims)
    d_ccl = _cohens_d(pos_ccl_sims, neg_ccl_sims)

    return {
        "wilcoxon": wilcoxon_result,
        "auc_text": {"auc": auc_text, "ci_95": ci_text},
        "auc_ccl": {"auc": auc_ccl, "ci_95": ci_ccl},
        "cohens_d": {"text": d_text, "ccl": d_ccl},
    }


# PURPOSE: Wilcoxon signed-rank test (scipy あればそちらを使う)
def _wilcoxon_test(x: list[float], y: list[float]) -> dict:
    """対応あるペア (x_i, y_i) について y > x を片側検定する。"""
    diffs = [yi - xi for xi, yi in zip(x, y)]
    n = len(diffs)

    try:
        from scipy.stats import wilcoxon as scipy_wilcoxon
        stat, p_two = scipy_wilcoxon(diffs, alternative="greater")
        effect_r = stat / (n * (n + 1) / 2)  # 効果量 r
        return {
            "statistic": float(stat),
            "p_value": float(p_two),
            "effect_r": float(effect_r),
            "n": n,
            "significant": p_two < 0.05,
            "method": "scipy.stats.wilcoxon",
        }
    except ImportError:
        pass

    # フォールバック: 符号検定 (sign test)
    # 正の差の数をカウントし、二項検定の近似で p 値を推定
    positive_count = sum(1 for d in diffs if d > 0)
    negative_count = sum(1 for d in diffs if d < 0)
    total = positive_count + negative_count
    if total == 0:
        return {"statistic": 0, "p_value": 1.0, "effect_r": 0, "n": n,
                "significant": False, "method": "sign_test (fallback)"}

    # 片側 p 値: P(X >= positive_count | H0: p=0.5) の正規近似
    # z = (positive_count - total/2) / sqrt(total/4)
    z = (positive_count - total / 2) / math.sqrt(total / 4) if total > 0 else 0
    # 正規分布の上側確率の近似 (Abramowitz and Stegun)
    p_value = 0.5 * math.erfc(z / math.sqrt(2))
    effect_r = (positive_count - negative_count) / total
    return {
        "statistic": positive_count,
        "p_value": p_value,
        "effect_r": effect_r,
        "n": n,
        "significant": p_value < 0.05,
        "method": "sign_test (fallback, scipy not available)",
    }


# PURPOSE: AUC-ROC を計算 (Mann-Whitney U ベース)
def _compute_auc(positives: list[float], negatives: list[float]) -> float:
    """正例のスコアが負例のスコアより大きい確率 (= AUC)。"""
    n_pos = len(positives)
    n_neg = len(negatives)
    if n_pos == 0 or n_neg == 0:
        return 0.0
    count = 0
    for p in positives:
        for n in negatives:
            if p > n:
                count += 1
            elif p == n:
                count += 0.5
    return count / (n_pos * n_neg)


# PURPOSE: Bootstrap で AUC の 95% 信頼区間を推定
def _bootstrap_auc_ci(
    positives: list[float],
    negatives: list[float],
    n_bootstrap: int = 1000,
    ci: float = 0.95,
) -> tuple[float, float]:
    """Bootstrap resampling による AUC の信頼区間。"""
    random.seed(42)  # 再現性
    aucs = []
    for _ in range(n_bootstrap):
        pos_sample = random.choices(positives, k=len(positives))
        neg_sample = random.choices(negatives, k=len(negatives))
        aucs.append(_compute_auc(pos_sample, neg_sample))
    aucs.sort()
    lower_idx = int((1 - ci) / 2 * n_bootstrap)
    upper_idx = int((1 + ci) / 2 * n_bootstrap) - 1
    return (aucs[lower_idx], aucs[upper_idx])


# PURPOSE: Cohen's d (正負分離の効果量)
def _cohens_d(group1: list[float], group2: list[float]) -> float:
    """2群間の標準化された平均差 (pooled SD)。"""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)
    pooled_sd = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return float('inf') if mean1 != mean2 else 0.0
    return (mean1 - mean2) / pooled_sd



def compute_recall_at_k(
    pairs: list[StructuralPair],
    text_embeddings: list[list[float]],
    ccl_embeddings: list[list[float]],
    k_values: list[int] = [1, 3, 5],
) -> dict:
    """全関数から構造的同型のペアを検索し、recall@k を計算する。

    各正例ペアの関数 A をクエリとし、全関数 B の中から
    ペア相手の関数 B が上位 k 件に含まれるかを判定。
    """
    from mekhane.anamnesis.embedder_mixin import _l2_normalize

    positive_pairs = [(i, p) for i, p in enumerate(pairs) if not p.pair_id.startswith("N")]

    # 全関数の embedding を正規化
    n = len(pairs)
    text_vecs = [_l2_normalize(text_embeddings[i * 2]) for i in range(n)]
    text_vecs_b = [_l2_normalize(text_embeddings[i * 2 + 1]) for i in range(n)]
    ccl_vecs = [_l2_normalize(ccl_embeddings[i * 2]) for i in range(n)]
    ccl_vecs_b = [_l2_normalize(ccl_embeddings[i * 2 + 1]) for i in range(n)]

    # 全ての B 関数を候補プール化
    all_b_text = text_vecs_b
    all_b_ccl = ccl_vecs_b

    def _cosine(a, b):
        return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b))))

    text_recalls = {k: 0 for k in k_values}
    ccl_recalls = {k: 0 for k in k_values}

    for pair_idx, pair in positive_pairs:
        # テキスト: A をクエリ → 全 B と比較 → ランク取得
        text_query = text_vecs[pair_idx]
        text_sims = [_cosine(text_query, b) for b in all_b_text]
        text_ranked = sorted(range(n), key=lambda i: text_sims[i], reverse=True)
        text_rank = text_ranked.index(pair_idx) + 1  # 正解のランク (1-indexed)

        # CCL: A をクエリ → 全 B と比較 → ランク取得
        ccl_query = ccl_vecs[pair_idx]
        ccl_sims = [_cosine(ccl_query, b) for b in all_b_ccl]
        ccl_ranked = sorted(range(n), key=lambda i: ccl_sims[i], reverse=True)
        ccl_rank = ccl_ranked.index(pair_idx) + 1

        for k in k_values:
            if text_rank <= k:
                text_recalls[k] += 1
            if ccl_rank <= k:
                ccl_recalls[k] += 1

    total = len(positive_pairs)
    return {
        "text": {k: v / total for k, v in text_recalls.items()},
        "ccl": {k: v / total for k, v in ccl_recalls.items()},
        "total_positive_pairs": total,
    }


# PURPOSE: 結果の表示
def print_results(
    results: list[PairResult],
    recall: dict,
    stat_results: dict | None = None,
    verbose: bool = False,
):
    """実験結果をテーブル形式で表示。"""
    print("\n" + "=" * 80)
    print("  P3 検証実験 — 結果")
    print("=" * 80)

    # ペアごとの類似度
    print(f"\n{'ID':>4} {'種別':>4} {'パターン':<30} {'Text':>6} {'CCL':>6} {'Δ':>7} {'CCL一致':>6}")
    print("-" * 80)

    for r in results:
        kind = "✅" if r.is_positive else "❌"
        delta = r.ccl_similarity - r.text_similarity
        delta_str = f"{delta:+.3f}"
        match_str = "≡" if r.ccl_exact_match else " "
        print(f"{r.pair_id:>4} {kind:>4} {r.pattern:<30} {r.text_similarity:.3f} {r.ccl_similarity:.3f} {delta_str:>7} {match_str:>6}")

    # 集計
    positives = [r for r in results if r.is_positive]
    negatives = [r for r in results if not r.is_positive]

    avg_text_pos = sum(r.text_similarity for r in positives) / len(positives)
    avg_ccl_pos = sum(r.ccl_similarity for r in positives) / len(positives)
    avg_text_neg = sum(r.text_similarity for r in negatives) / len(negatives) if negatives else 0
    avg_ccl_neg = sum(r.ccl_similarity for r in negatives) / len(negatives) if negatives else 0

    print("\n" + "-" * 80)
    print(f"  正例 平均類似度: Text={avg_text_pos:.3f}  CCL={avg_ccl_pos:.3f}  (Δ={avg_ccl_pos - avg_text_pos:+.3f})")
    print(f"  負例 平均類似度: Text={avg_text_neg:.3f}  CCL={avg_ccl_neg:.3f}  (Δ={avg_ccl_neg - avg_text_neg:+.3f})")

    # 分離度 (正例平均 - 負例平均)
    text_sep = avg_text_pos - avg_text_neg
    ccl_sep = avg_ccl_pos - avg_ccl_neg
    print(f"  分離度:          Text={text_sep:.3f}  CCL={ccl_sep:.3f}  (Δ={ccl_sep - text_sep:+.3f})")

    # Recall@k
    print(f"\n  Recall@k (正例 {recall['total_positive_pairs']} ペア):")
    for k in sorted(recall["text"].keys()):
        t = recall["text"][k]
        c = recall["ccl"][k]
        print(f"    @{k}: Text={t:.2%}  CCL={c:.2%}  (Δ={c-t:+.2%})")

    # 統計的検定結果
    if stat_results:
        print("\n" + "-" * 80)
        print("  統計的検定:")

        # Wilcoxon 符号順位検定
        wilcoxon = stat_results.get("wilcoxon", {})
        if wilcoxon.get("error"):
            print(f"    Wilcoxon:  ⚠️ {wilcoxon['error']}")
        else:
            p = wilcoxon.get("p_value", 1.0)
            sig = "✅ 有意 (p < 0.05)" if p < 0.05 else "❌ 非有意"
            print(f"    Wilcoxon:  p={p:.4f}  統計量={wilcoxon.get('statistic', 'N/A')}  {sig}")

        # AUC-ROC
        auc_text = stat_results.get("auc_text", {})
        auc_ccl = stat_results.get("auc_ccl", {})
        if auc_text and auc_ccl:
            t_auc = auc_text.get("auc", 0)
            c_auc = auc_ccl.get("auc", 0)
            t_ci = auc_text.get("ci_95", (0, 0))
            c_ci = auc_ccl.get("ci_95", (0, 0))
            print(f"    AUC-ROC Text: {t_auc:.3f}  95%CI=[{t_ci[0]:.3f}, {t_ci[1]:.3f}]")
            print(f"    AUC-ROC CCL:  {c_auc:.3f}  95%CI=[{c_ci[0]:.3f}, {c_ci[1]:.3f}]")
            ccl_auc_wins = "✅ CCL > Text" if c_auc > t_auc else "❌ Text ≥ CCL"
            print(f"    AUC 判定:  {ccl_auc_wins}")

        # Cohen's d
        cohens = stat_results.get("cohens_d", {})
        d_text = cohens.get("text", 0)
        d_ccl = cohens.get("ccl", 0)
        if d_text or d_ccl:
            def _d_label(d: float) -> str:
                ad = abs(d)
                if ad < 0.2: return "無視可能"
                if ad < 0.5: return "小"
                if ad < 0.8: return "中"
                return "大"
            print(f"    Cohen's d Text: {d_text:.3f} ({_d_label(d_text)})")
            print(f"    Cohen's d CCL:  {d_ccl:.3f} ({_d_label(d_ccl)})")

    # 判定
    print("\n" + "=" * 80)
    ccl_wins_sim = avg_ccl_pos > avg_text_pos
    ccl_wins_sep = ccl_sep > text_sep
    ccl_wins_recall = all(
        recall["ccl"][k] >= recall["text"][k] for k in recall["text"]
    )

    # 統計的有意性の判定
    stat_significant = False
    if stat_results:
        wilcoxon = stat_results.get("wilcoxon", {})
        stat_significant = wilcoxon.get("p_value", 1.0) < 0.05

    print(f"  P3 判定:")
    print(f"    類似度:  {'✅ CCL > Text' if ccl_wins_sim else '❌ Text ≥ CCL'}")
    print(f"    分離度:  {'✅ CCL > Text' if ccl_wins_sep else '❌ Text ≥ CCL'}")
    print(f"    Recall:  {'✅ CCL ≥ Text' if ccl_wins_recall else '❌ Text > CCL (一部)'}")
    if stat_results:
        print(f"    統計:    {'✅ p < 0.05' if stat_significant else '❌ p ≥ 0.05'}")

    if ccl_wins_sim and ccl_wins_recall and stat_significant:
        print(f"\n  → P3 支持 [確信度: 確信 — 統計的有意]")
    elif ccl_wins_sim and ccl_wins_recall:
        print(f"\n  → P3 支持 [確信度: 推定 — 統計的有意性は未確認]")
    elif ccl_wins_sim or ccl_wins_recall:
        print(f"\n  → P3 部分的支持 [確信度: 仮説のまま]")
    else:
        print(f"\n  → P3 不支持 — CCL embedding の優位性は確認できず")


# PURPOSE: 結果をマークダウンファイルに保存
def save_results(
    results: list[PairResult],
    recall: dict,
    stat_results: dict | None,
    output_path: Path,
):
    """結果を .md ファイルに保存。"""
    positives = [r for r in results if r.is_positive]
    negatives = [r for r in results if not r.is_positive]

    avg_text_pos = sum(r.text_similarity for r in positives) / len(positives)
    avg_ccl_pos = sum(r.ccl_similarity for r in positives) / len(positives)
    avg_text_neg = sum(r.text_similarity for r in negatives) / len(negatives) if negatives else 0
    avg_ccl_neg = sum(r.ccl_similarity for r in negatives) / len(negatives) if negatives else 0

    lines = [
        "# P3 検証結果: CCL embedding vs Text embedding",
        "",
        f"> 実験日: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> ベンチマーク: 正例 {len(positives)} ペア / 負例 {len(negatives)} ペア",
        "",
        "## ペアごとの結果",
        "",
        "| ID | 種別 | パターン | Text Sim | CCL Sim | Δ | CCL一致 |",
        "|:--|:--|:--|--:|--:|--:|:--|",
    ]

    for r in results:
        kind = "正例" if r.is_positive else "負例"
        delta = r.ccl_similarity - r.text_similarity
        match_str = "≡" if r.ccl_exact_match else ""
        lines.append(
            f"| {r.pair_id} | {kind} | {r.pattern} | {r.text_similarity:.3f} | {r.ccl_similarity:.3f} | {delta:+.3f} | {match_str} |"
        )

    lines.extend([
        "",
        "## 集計",
        "",
        f"| 指標 | Text | CCL | Δ |",
        f"|:--|--:|--:|--:|",
        f"| 正例平均類似度 | {avg_text_pos:.3f} | {avg_ccl_pos:.3f} | {avg_ccl_pos - avg_text_pos:+.3f} |",
        f"| 負例平均類似度 | {avg_text_neg:.3f} | {avg_ccl_neg:.3f} | {avg_ccl_neg - avg_text_neg:+.3f} |",
        f"| 分離度 (正-負) | {avg_text_pos - avg_text_neg:.3f} | {avg_ccl_pos - avg_ccl_neg:.3f} | {(avg_ccl_pos - avg_ccl_neg) - (avg_text_pos - avg_text_neg):+.3f} |",
        "",
        "## Recall@k",
        "",
        f"| k | Text | CCL | Δ |",
        f"|--:|--:|--:|--:|",
    ])

    for k in sorted(recall["text"].keys()):
        t = recall["text"][k]
        c = recall["ccl"][k]
        lines.append(f"| {k} | {t:.1%} | {c:.1%} | {c-t:+.1%} |")

    # 統計的検定
    if stat_results:
        lines.extend(["", "## 統計的検定", ""])

        # Wilcoxon
        wilcoxon = stat_results.get("wilcoxon", {})
        if wilcoxon.get("error"):
            lines.append(f"**Wilcoxon 符号順位検定:** ⚠️ {wilcoxon['error']}")
        else:
            p = wilcoxon.get("p_value", 1.0)
            sig = "有意 (p < 0.05)" if p < 0.05 else "非有意"
            lines.extend([
                "| 検定 | 統計量 | p値 | 判定 |",
                "|:--|--:|--:|:--|",
                f"| Wilcoxon 符号順位 | {wilcoxon.get('statistic', 'N/A')} | {p:.4f} | {sig} |",
            ])

        # AUC-ROC
        auc_text = stat_results.get("auc_text", {})
        auc_ccl = stat_results.get("auc_ccl", {})
        if auc_text and auc_ccl:
            t_auc = auc_text.get("auc", 0)
            c_auc = auc_ccl.get("auc", 0)
            t_ci = auc_text.get("ci_95", (0, 0))
            c_ci = auc_ccl.get("ci_95", (0, 0))
            lines.extend([
                "",
                "| 手法 | AUC | 95% CI |",
                "|:--|--:|:--|",
                f"| Text Embedding | {t_auc:.3f} | [{t_ci[0]:.3f}, {t_ci[1]:.3f}] |",
                f"| CCL Embedding | {c_auc:.3f} | [{c_ci[0]:.3f}, {c_ci[1]:.3f}] |",
            ])

        # Cohen's d
        cohens = stat_results.get("cohens_d", {})
        d_text = cohens.get("text", 0)
        d_ccl = cohens.get("ccl", 0)
        if d_text or d_ccl:
            def _d_label(d: float) -> str:
                ad = abs(d)
                if ad < 0.2: return "無視可能"
                if ad < 0.5: return "小"
                if ad < 0.8: return "中"
                return "大"
            lines.extend([
                "",
                "| 手法 | Cohen's d | 効果量 |",
                "|:--|--:|:--|",
                f"| Text Embedding | {d_text:.3f} | {_d_label(d_text)} |",
                f"| CCL Embedding | {d_ccl:.3f} | {_d_label(d_ccl)} |",
            ])

    lines.extend([
        "",
        "## CCL 構造式サンプル",
        "",
    ])

    for r in results[:5]:
        lines.extend([
            f"### {r.pair_id}: {r.pattern}",
            f"- CCL A: `{r.ccl_a}`",
            f"- CCL B: `{r.ccl_b}`",
            f"- 一致: {'完全一致' if r.ccl_exact_match else '不一致'}",
            "",
        ])

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="P3 検証: CCL embedding vs Text embedding"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="CCL 変換のみ (API 呼出なし)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="詳細出力")
    args = parser.parse_args()

    pairs = create_benchmark_pairs()
    print(f"📋 ベンチマーク: {len(pairs)} ペア "
          f"({sum(1 for p in pairs if not p.pair_id.startswith('N'))} 正例 / "
          f"{sum(1 for p in pairs if p.pair_id.startswith('N'))} 負例)")

    if args.dry_run:
        run_dry(pairs, verbose=args.verbose)
    else:
        run_experiment(pairs, verbose=args.verbose)


if __name__ == "__main__":
    main()
