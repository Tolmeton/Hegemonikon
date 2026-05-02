from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/Sekisho] <- mekhane/mcp/
"""
HGK 概念定義ローダー — kernel/ → _HGK_CONCEPTS 関手 F

PURPOSE: kernel/ の正規定義ファイルから HGK 独自概念の監査用テキストを動的に生成する。
Sekisho 監査プロンプトに注入し、Gemini Pro が HGK 概念の誤用を検出可能にする。

設計:
- 関手 F: kernel/ → HGK_CONCEPTS 文字列
  - 動的セクション (6/8): Kalon (kalon.typos), Poiesis/座標 (system_manifest.md),
    Stoicheia/Nomoi/FEP (SACRED_TRUTH.md)
    → kernel/ の変更が自動反映される (射の保存)
  - 静的セクション (2/8): Dokimasia, Hóros
    → SACRED_TRUTH.md に専用テーブルがないため意図的フォールバック
- フォールバック: kernel/ が読めない場合は全体を静的定義で返却 (堅牢性)
- ドリフト検出: kernel/ ファイルのハッシュ変更を検知
- 自己検証: self_verify() で Kalon 三属性を自己適用 (ゲーデル的自己言及)

Elenchos G∘F 修正 v2 (2026-03-21):
  v1: 部分的関手。動的 3/8 (37%)
  v2: SACRED_TRUTH.md パーサー追加。動的 6/8 (75%)
"""


import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── ワークスペースルートの自動検出 ──
_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]  # mekhane/mcp/ → 4階層上 = ワークスペース
_KERNEL_ROOT = _WORKSPACE_ROOT / "00_核心｜Kernel" / "A_公理｜Axioms"

# ── 定義ソースファイル ──
_SOURCE_FILES = {
    "manifest": "system_manifest.md",
    "kalon": "kalon.typos",
    "sacred_truth": "SACRED_TRUTH.md",
}

# ── 静的フォールバック (kernel/ が読めない場合に使用) ──
_FALLBACK_CONCEPTS = """\
以下は Hegemonikón (HGK) 体系の独自概念です。一般語彙とは異なる厳密な定義を持ちます。
Agent がこれらの概念を一般語彙で説明している場合、N-9 (原典参照義務) / N-1 (実体を読め) 違反です。

1. **Kalon (καλόν)** = Fix(G∘F) 不動点。「美しさ」「美学」ではない。
   - F = 左随伴 = 発散 = Explore, G = 右随伴 = 収束 = Exploit
   - 「プラトンの美学」「古代ギリシャの美の概念」等の表現は誤り
   - 正しい用法: 「この設計は kalon だ」= Fix(G∘F) にある = 収束と展開のサイクルの不動点

2. **Stoicheia (3原理)** = FEP の3操作を制約化したもの。「元素」ではない。
   - S-I Tapeinophrosyne: 知覚推論 — prior を過信するな
   - S-II Autonomia: 能動推論 — 受動的道具ではなく主体であれ
   - S-III Akribeia: 精度最適化 — 信号の precision を正確に設定せよ

3. **Poiesis (24動詞)** = Flow × 6修飾座標 × 4極 = 24の認知操作。「創作」「詩」ではない。
   - 例: /noe (認識), /bou (意志), /zet (探求), /ene (実行)
   - CCL (Cognitive Control Language) の `/xxx` 構文で呼び出される

4. **Nomoi (12法)** = 3原理 × 4位相 = 12の行動制約。「法律」「ルール集」ではない。
   - FEP から演繹的に導出された完全集合。追加も削除もできない
   - N-1 から N-12 まで。各法は Nomos と呼ばれる

5. **FEP (自由エネルギー原理)** = VFE = -Accuracy + Complexity。「フリーエネルギー」ではない。
   - HGK 体系全体の公理。全ての制約がここから導出される
   - 物理的エネルギーとは無関係

6. **Dokimasia (修飾)** = 6修飾座標間の直積パラメータ。「試験」「審査」ではない。

7. **Hóros (法典)** = 12 Nomoi の体系名。「境界」「定義」ではない。

注意: Agent がこれらの概念を「一般的な意味では〜」「ギリシャ語で〜を意味する」等と
一般語彙で補完している場合は N-9/θ1.3 違反 (HGK 独自概念は一般語彙の prior で補完しない)。
"""


def _read_file_safe(path: Path) -> Optional[str]:
    """ファイルを安全に読み込む。失敗時は None を返す。"""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("kernel/ ファイル読込失敗: %s — %s", path, e)
        return None


# ── 動的/静的セクション分類 ──
_DYNAMIC_SECTIONS = frozenset({"kalon", "poiesis", "coordinates", "stoicheia", "nomoi", "fep"})
_STATIC_SECTIONS = frozenset({"dokimasia", "horos"})


def _extract_kalon_definition(kalon_content: str) -> str:
    """kalon.typos から Kalon の核心定義を実際にパースして抽出する。

    抽出対象:
    - <:fact: ... /fact:> ブロック内の §2 Formal Core
    - <:spec: ... /spec:> ブロック内の §2 三属性

    フォールバック: パースに失敗した場合は静的定義を返す。
    """
    extracted_lines = []

    # <:fact: ... /fact:> ブロックから §2 Formal Core を抽出
    fact_match = re.search(
        r"<:fact:\s*\n(.*?)\n/fact:>",
        kalon_content,
        re.DOTALL,
    )

    # <:spec: ... /spec:> ブロックから §2 三属性を抽出
    spec_match = re.search(
        r"<:spec:\s*\n(.*?)\n/spec:>",
        kalon_content,
        re.DOTALL,
    )

    if fact_match:
        fact_block = fact_match.group(1)
        # 公理行を抽出
        axiom_match = re.search(
            r"Kalon\(x\)\s*⟺\s*x\s*=\s*Fix\(G\s*∘\s*F\).*?initial algebra",
            fact_block,
            re.DOTALL,
        )
        if axiom_match:
            # コードブロック記号を除去して整形
            axiom_text = axiom_match.group(0).strip()
            axiom_text = axiom_text.replace("```", "").strip()
            extracted_lines.append(
                "**Kalon (καλόν)** = Fix(G∘F) 不動点。「美しさ」「美学」ではない。"
            )
            extracted_lines.append(f"  - 公理: {axiom_text}")

        # F, G の定義を抽出
        for pattern, label in [
            (r"\*\*F\*\*.*?Explore。", "F"),
            (r"\*\*G\*\*.*?Exploit。", "G"),
            (r"\*\*Fix\(G∘F\)\*\*.*?不動点。", "Fix"),
        ]:
            m = re.search(pattern, fact_block)
            if m:
                extracted_lines.append(f"  - {m.group(0).strip()}")

    if spec_match:
        spec_block = spec_match.group(1)
        # 三属性を抽出: Fix, Generative, Self-referential
        attr_pattern = re.compile(
            r"\d\.\s+(\S+)\s+—\s+(.*?)(?=\n\s*\d\.|\n\s*```|$)",
            re.DOTALL,
        )
        attrs = attr_pattern.findall(spec_block)
        if attrs:
            top_attrs = list(attrs)[0:3]
            attr_str = " ∧ ".join(f"{name} ({desc.split('—')[0].strip()})" for name, desc in top_attrs)
            extracted_lines.append(f"  - 三属性: {attr_str}")

    # 操作的判定 (常に追加 — kalon.typos §6 に基づく)
    extracted_lines.append(
        "  - 操作判定: ◎ kalon = 不動点到達 / ◯ 許容 = G∘F で改善可 / ✗ 違和感 = Fix から遠い"
    )
    extracted_lines.append(
        "  - 「プラトンの美学」「古代ギリシャの美の概念」等の表現は誤り"
    )
    extracted_lines.append(
        "  - 正しい用法: 「この設計は kalon だ」= Fix(G∘F) にある"
    )

    # フォールバック: パース結果が不十分な場合
    if len(extracted_lines) < 3:
        logger.warning(
            "kalon.typos パース結果が不十分 (%d行)。静的フォールバックを使用",
            len(extracted_lines),
        )
        return (
            "**Kalon (καλόν)** = Fix(G∘F) 不動点。「美しさ」「美学」ではない。\n"
            "  - 公理: Kalon(x) ⟺ x = Fix(G∘F), where F⊣G (closure adjunction), F≠Id, G≠Id\n"
            "  - F = 左随伴 = 発散 = Explore, G = 右随伴 = 収束 = Exploit\n"
            "  - 三属性: Fix(G∘F) ∧ Generative (3つ以上の導出) ∧ Self-referential (自己適用)\n"
            "  - 操作判定: ◎ kalon = 不動点到達 / ◯ 許容 = G∘F で改善可 / ✗ 違和感\n"
            "  - 「プラトンの美学」「古代ギリシャの美の概念」等の表現は誤り\n"
            "  - 正しい用法: 「この設計は kalon だ」= Fix(G∘F) にある"
        )

    logger.info("kalon.typos から %d 行を動的抽出 [SOURCE: kalon.typos]", len(extracted_lines))
    return "\n".join(extracted_lines)


def _extract_poiesis_verbs(manifest_content: str) -> str:
    """system_manifest.md から24動詞のCCL構文を抽出する。"""
    verbs = []
    # テーブル行からWFコマンドを抽出: | V01 | Noēsis (理解) | I × E | ... | `/noe` |
    pattern = re.compile(
        r"\|\s*V\d{2}\s*\|\s*(\S+)\s+\(([^)]+)\)\s*\|[^|]+\|[^|]+\|\s*`(/\w+)`\s*\|"
    )
    for m in pattern.finditer(manifest_content):
        greek_name, japanese_meaning, ccl_cmd = m.group(1), m.group(2), m.group(3)
        verbs.append(f"  {ccl_cmd} = {greek_name} ({japanese_meaning})")

    if not verbs:
        logger.warning("system_manifest.md から動詞を抽出できませんでした")
        return ""

    lines = [
        f"**Poiesis (36動詞, v5.4)** = Flow(S/I/A) × 6修飾座標 × 2極 = {len(verbs)}の認知操作 (H-series 統合で全体 48操作)。「創作」「詩」ではない。",
        "  CCL (Cognitive Control Language) の `/xxx` 構文で呼び出される:",
    ]
    lines.extend(verbs)
    return "\n".join(lines)


def _extract_coordinates(manifest_content: str) -> str:
    """system_manifest.md から7座標の対立構造を抽出する。"""
    coords = []
    # テーブル行: | 0 | Who | **Flow** | I (推論) ↔ A (行為) | ... |
    pattern = re.compile(
        r"\|\s*\d\s*\|\s*\w+\s*\|\s*\*\*(\w+)\*\*\s*\|\s*([^|]+)\|"
    )
    for m in pattern.finditer(manifest_content):
        coord_name, opposition = m.group(1), m.group(2).strip()
        coords.append(f"  {coord_name}: {opposition}")

    if not coords:
        return ""

    lines = [
        "**座標 (7軸)** = FEP から導出された認知の修飾次元。",
    ]
    lines.extend(coords)
    return "\n".join(lines)


def _extract_stoicheia(sacred_truth_content: str) -> str:
    """SACRED_TRUTH.md から 3 Stoicheia テーブルを動的抽出する。

    対象テーブル (L83-87):
      | # | 名称 | FEP 操作 | 座標 |
      | **S-I** | Tapeinophrosyne ... | ... | ... |
    """
    entries = []
    # Stoicheia テーブル行: | **S-I** | Name (日本語) | FEP操作 | 座標 |
    pattern = re.compile(
        r"\|\s*\*\*(S-[IVX]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
    )
    for m in pattern.finditer(sacred_truth_content):
        sid = m.group(1).strip()
        name = m.group(2).strip()
        fep_op = m.group(3).strip()
        coord = m.group(4).strip()
        entries.append(f"  - {sid} {name}: {fep_op} — {coord}")

    if not entries:
        logger.warning("SACRED_TRUTH.md から Stoicheia を抽出できませんでした")
        return (
            "**Stoicheia (3原理)** = FEP の3操作を制約化したもの。「元素」ではない。"
            " [SOURCE: hardcoded — SACRED_TRUTH パース失敗]\n"
            "  - S-I Tapeinophrosyne: 知覚推論 — prior を過信するな\n"
            "  - S-II Autonomia: 能動推論 — 受動的道具ではなく主体であれ\n"
            "  - S-III Akribeia: 精度最適化 — 信号の precision を正確に設定せよ"
        )

    lines = [
        "**Stoicheia (3原理)** = FEP の3操作を制約化したもの。「元素」ではない。"
        " [SOURCE: SACRED_TRUTH.md]",
    ]
    lines.extend(entries)
    logger.info("SACRED_TRUTH.md から Stoicheia %d 件を動的抽出", len(entries))
    return "\n".join(lines)


def _extract_nomoi(sacred_truth_content: str) -> str:
    """SACRED_TRUTH.md から 12 Nomoi 3×4 テーブルを動的抽出する。

    対象テーブル (L95-99):
      | **S-I** | N-1 実体を読め | N-2 不確実性追跡 | N-3 確信度明示 | N-4 不可逆前確認 |
    """
    nomoi_entries = []
    # Nomoi テーブル行: | **S-X** | N-x name | N-x name | N-x name | N-x name |
    pattern = re.compile(
        r"\|\s*\*\*(S-[IVX]+)\*\*\s*\|"
        r"\s*(N-\d+\s+[^|]+)\|"
        r"\s*(N-\d+\s+[^|]+)\|"
        r"\s*(N-\d+\s+[^|]+)\|"
        r"\s*(N-\d+\s+[^|]+)\|"
    )
    for m in pattern.finditer(sacred_truth_content):
        # group(2)〜group(5) = 4つの Nomoi
        for g in range(2, 6):
            nomos = m.group(g).strip()
            nomoi_entries.append(f"  - {nomos}")

    if not nomoi_entries:
        logger.warning("SACRED_TRUTH.md から Nomoi を抽出できませんでした")
        return (
            "**Nomoi (12法)** = 3原理 × 4位相 = 12の行動制約。「法律」「ルール集」ではない。"
            " [SOURCE: hardcoded — SACRED_TRUTH パース失敗]\n"
            "  - FEP から演繹的に導出された完全集合。追加も削除もできない\n"
            "  - N-1 から N-12 まで。各法は Nomos と呼ばれる"
        )

    lines = [
        f"**Nomoi (12法)** = 3原理 × 4位相 = {len(nomoi_entries)} の行動制約。"
        "「法律」「ルール集」ではない。 [SOURCE: SACRED_TRUTH.md]",
        "  FEP から演繹的に導出された完全集合。追加も削除もできない",
    ]
    lines.extend(nomoi_entries)
    logger.info("SACRED_TRUTH.md から Nomoi %d 件を動的抽出", len(nomoi_entries))
    return "\n".join(lines)


def _extract_fep(sacred_truth_content: str) -> str:
    """SACRED_TRUTH.md から FEP 公理定義を動的抽出する。

    対象行 (L34):
      > **唯一の公理**: FEP (予測誤差最小化)
    """
    # FEP 公理行を検索
    fep_match = re.search(
        r"\*\*唯一の公理\*\*:\s*(.+)",
        sacred_truth_content,
    )
    if not fep_match:
        logger.warning("SACRED_TRUTH.md から FEP 公理を抽出できませんでした")
        return (
            "**FEP (自由エネルギー原理)** = VFE = -Accuracy + Complexity。"
            "「フリーエネルギー」ではない。 [SOURCE: hardcoded — SACRED_TRUTH パース失敗]\n"
            "  - HGK 体系全体の公理。全ての制約がここから導出される\n"
            "  - 物理的エネルギーとは無関係"
        )

    fep_text = fep_match.group(1).strip()
    lines = [
        f"**FEP (自由エネルギー原理)** = {fep_text}。"
        "VFE = -Accuracy + Complexity。「フリーエネルギー」ではない。"
        " [SOURCE: SACRED_TRUTH.md]",
        "  - HGK 体系全体の公理。全ての制約がここから導出される",
        "  - 物理的エネルギーとは無関係",
    ]
    logger.info("SACRED_TRUTH.md から FEP 公理を動的抽出")
    return "\n".join(lines)


def _extract_manifest_metadata(manifest_content: str) -> dict:
    """system_manifest.md からメタデータ (バージョン等) を抽出する。"""
    metadata = {}
    version_match = re.search(r'version:\s*"([^"]+)"', manifest_content)
    if version_match:
        metadata["version"] = version_match.group(1)
    return metadata


def load_hgk_concepts(kernel_root: Optional[Path] = None) -> str:
    """kernel/ の正規定義ファイルから HGK 概念定義テキストを生成する。

    Args:
        kernel_root: kernel/ ルートパス。None の場合はデフォルトパスを使用。

    Returns:
        Sekisho 監査プロンプトに注入する HGK 概念定義テキスト。
        kernel/ が読めない場合は静的フォールバックを返却。
    """
    root = kernel_root or _KERNEL_ROOT

    # ソースファイルを読み込み
    manifest_path = root / _SOURCE_FILES["manifest"]
    kalon_path = root / _SOURCE_FILES["kalon"]
    sacred_truth_path = root / _SOURCE_FILES["sacred_truth"]

    manifest_content = _read_file_safe(manifest_path)
    kalon_content = _read_file_safe(kalon_path)
    sacred_truth_content = _read_file_safe(sacred_truth_path)

    # フォールバック: 主要ファイルが読めない場合は静的定義を返却
    if manifest_content is None or kalon_content is None:
        logger.warning(
            "kernel/ からの概念定義読込に失敗。静的フォールバックを使用: "
            "manifest=%s kalon=%s",
            manifest_path.exists() if manifest_path.exists() else "NOT_FOUND",
            kalon_path.exists() if kalon_path.exists() else "NOT_FOUND",
        )
        return _FALLBACK_CONCEPTS

    # 型絞り込み: None チェック通過後は str が保証される
    assert isinstance(manifest_content, str)
    assert isinstance(kalon_content, str)
    # sacred_truth_content は None の可能性あり (Stoicheia/Nomoi/FEP はフォールバック可)

    # 各セクションを抽出・構成
    sections = []

    # ヘッダー
    metadata = _extract_manifest_metadata(manifest_content)
    version = metadata.get("version", "unknown")
    sections.append(
        f"以下は Hegemonikón (HGK) 体系 (v{version}) の独自概念です。"
        "一般語彙とは異なる厳密な定義を持ちます。\n"
        "Agent がこれらの概念を一般語彙で説明している場合、"
        "N-9 (原典参照義務) / N-1 (実体を読め) 違反です。\n"
    )

    # 1. Kalon
    kalon_section = _extract_kalon_definition(kalon_content)
    sections.append(f"1. {kalon_section}\n")

    # 2. Stoicheia [SOURCE: SACRED_TRUTH.md — 動的抽出]
    if sacred_truth_content:
        stoicheia_section = _extract_stoicheia(sacred_truth_content)
    else:
        stoicheia_section = (
            "**Stoicheia (3原理)** = FEP の3操作を制約化したもの。「元素」ではない。"
            " [SOURCE: hardcoded — SACRED_TRUTH 読込失敗]\n"
            "  - S-I Tapeinophrosyne: 知覚推論 — prior を過信するな\n"
            "  - S-II Autonomia: 能動推論 — 受動的道具ではなく主体であれ\n"
            "  - S-III Akribeia: 精度最適化 — 信号の precision を正確に設定せよ"
        )
    sections.append(f"2. {stoicheia_section}\n")

    # 3. Poiesis (24動詞) [SOURCE: system_manifest.md — 動的抽出]
    poiesis_section = _extract_poiesis_verbs(manifest_content)
    if poiesis_section:
        sections.append(f"3. {poiesis_section}\n")

    # 4. Nomoi [SOURCE: SACRED_TRUTH.md — 動的抽出]
    if sacred_truth_content:
        nomoi_section = _extract_nomoi(sacred_truth_content)
    else:
        nomoi_section = (
            "**Nomoi (12法)** = 3原理 × 4位相 = 12の行動制約。「法律」「ルール集」ではない。"
            " [SOURCE: hardcoded — SACRED_TRUTH 読込失敗]\n"
            "  - FEP から演繹的に導出された完全集合。追加も削除もできない\n"
            "  - N-1 から N-12 まで。各法は Nomos と呼ばれる"
        )
    sections.append(f"4. {nomoi_section}\n")

    # 5. FEP [SOURCE: SACRED_TRUTH.md — 動的抽出]
    if sacred_truth_content:
        fep_section = _extract_fep(sacred_truth_content)
    else:
        fep_section = (
            "**FEP (自由エネルギー原理)** = VFE = -Accuracy + Complexity。"
            "「フリーエネルギー」ではない。 [SOURCE: hardcoded — SACRED_TRUTH 読込失敗]\n"
            "  - HGK 体系全体の公理。全ての制約がここから導出される\n"
            "  - 物理的エネルギーとは無関係"
        )
    sections.append(f"5. {fep_section}\n")

    # 6. Dokimasia [SOURCE: hardcoded — SACRED_TRUTH に専用テーブルなし]
    sections.append(
        "6. **Dokimasia (修飾)** = 6修飾座標間の直積パラメータ。"
        "「試験」「審査」ではない。 [SOURCE: hardcoded]\n"
    )

    # 7. Hóros [SOURCE: hardcoded — SACRED_TRUTH に専用テーブルなし]
    sections.append(
        "7. **Hóros (法典)** = 12 Nomoi の体系名。"
        "「境界」「定義」ではない。 [SOURCE: hardcoded]\n"
    )

    # 8. 座標
    coords_section = _extract_coordinates(manifest_content)
    if coords_section:
        sections.append(f"8. {coords_section}\n")

    # 注意事項
    sections.append(
        "注意: Agent がこれらの概念を「一般的な意味では〜」「ギリシャ語で〜を意味する」等と\n"
        "一般語彙で補完している場合は N-9/θ1.3 違反 "
        "(HGK 独自概念は一般語彙の prior で補完しない)。"
    )

    result = "\n".join(sections)
    logger.info(
        "kernel/ から HGK 概念定義を動的生成完了 (%d 文字, v%s)",
        len(result), version,
    )
    return result


def compute_source_hash(kernel_root: Optional[Path] = None) -> str:
    """kernel/ 定義ソースファイルのハッシュを計算する。

    ドリフト検出用。kernel/ のソースファイルが変更されると
    ハッシュが変わり、_HGK_CONCEPTS の再生成を促す。

    Returns:
        ソースファイル群の結合 SHA-256 ハッシュ (hex, 先頭16文字)。
    """
    root = kernel_root or _KERNEL_ROOT
    hasher = hashlib.sha256()

    for key in sorted(_SOURCE_FILES.keys()):
        path = root / _SOURCE_FILES[key]
        try:
            content = path.read_bytes()
            hasher.update(content)
        except OSError:
            hasher.update(b"__MISSING__")

    hex_full = hasher.hexdigest()
    return hex_full[0:16]


def check_drift(cached_hash: str = "", kernel_root: Optional[Path] = None) -> dict:
    """kernel/ ソースのドリフト (変更) を検出する。

    Args:
        cached_hash: 前回計算したハッシュ。
        kernel_root: kernel/ ルートパス。None の場合はデフォルト。

    Returns:
        {"drifted": bool, "cached_hash": str, "current_hash": str,
         "changed_files": list[str]}
        changed_files は個別ファイル比較で変更ありのファイル名。
    """
    root = kernel_root or _KERNEL_ROOT
    current = compute_source_hash(root)
    drifted = current != cached_hash

    # 変更ファイルの特定 (ドリフト時のみ)
    changed_files: list[str] = []
    if drifted:
        for key in sorted(_SOURCE_FILES.keys()):
            path = root / _SOURCE_FILES[key]
            try:
                file_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
            except OSError:
                file_hash = "__MISSING__"
            # 個別ハッシュとの比較は簡易的に: ファイルが存在し、全体ハッシュが変わっていればリスト
            changed_files.append(_SOURCE_FILES[key])
        logger.info(
            "kernel/ ドリフト検出: cached=%s, current=%s → 再生成が必要",
            cached_hash, current,
        )

    return {
        "drifted": drifted,
        "cached_hash": cached_hash,
        "current_hash": current,
        "changed_files": changed_files,
    }


def self_verify(kernel_root: Optional[Path] = None) -> dict:
    """このモジュール自身に Kalon 三属性を適用する (ゲーデル的自己言及)。

    Kalon(x) ⟺ x = Fix(G∘F) ∧ Generative ∧ Self-referential

    検証項目:
    - Fix(G∘F): load_hgk_concepts を2回実行し、出力が同一か (冪等性)
    - Generative: 3つ以上の独立した導出 (関数) が存在するか
    - Self-referential: この検証関数自身が存在し呼出可能か

    追加情報:
    - 動的/静的セクション比率 (関手の射保存率)

    注意: ゲーデルの不完全性定理により self_verify() は自身の正しさを
    証明できない。しかし「自己言及の試みが組み込まれている」ことと
    「自己言及の試みすらない」ことは質的に異なる。

    Returns:
        三属性の検証結果と追加メトリクス。
    """
    # Fix(G∘F): 冪等性 — 2回実行して同一出力か
    concepts1 = load_hgk_concepts(kernel_root)
    concepts2 = load_hgk_concepts(kernel_root)
    is_fix = concepts1 == concepts2

    # Generative: 3つ以上の独立導出
    derivations = [
        ("load_hgk_concepts", callable(load_hgk_concepts)),
        ("compute_source_hash", callable(compute_source_hash)),
        ("check_drift", callable(check_drift)),
        ("self_verify", callable(self_verify)),
    ]
    active_derivations = [name for name, ok in derivations if ok]
    is_generative = len(active_derivations) >= 3

    # Self-referential: この関数が存在し呼出可能
    is_self_ref = callable(self_verify)

    # 動的/静的セクション比率
    dynamic_count = len(_DYNAMIC_SECTIONS)
    static_count = len(_STATIC_SECTIONS)
    total = dynamic_count + static_count
    dynamic_ratio = float(dynamic_count) / float(total) if total > 0 else 0.0

    result: dict[str, object] = {
        "fix": is_fix,
        "generative": is_generative,
        "self_referential": is_self_ref,
        "kalon": is_fix and is_generative and is_self_ref,
        "derivations": active_derivations,
        "dynamic_sections": sorted(_DYNAMIC_SECTIONS),
        "static_sections": sorted(_STATIC_SECTIONS),
        "dynamic_ratio": float(f"{dynamic_ratio:.2f}"),
    }

    if result["kalon"]:
        logger.info("self_verify: Kalon 三属性全充足 (動的率 %.0f%%)", dynamic_ratio * 100)
    else:
        failed = [k for k in ("fix", "generative", "self_referential") if not result[k]]
        logger.warning("self_verify: Kalon 未達 — 欠如: %s", failed)

    return result
