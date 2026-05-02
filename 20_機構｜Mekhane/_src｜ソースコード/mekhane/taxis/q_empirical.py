from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/taxis/q_empirical.py
# PURPOSE: Q-series Empirical Grounding Pipeline — tape データから Q̂ を推定し Bootstrap CI で検証する
"""
Q-series Empirical Grounding Pipeline

理論値 Q₀ (from_theory) を実セッション tape データと突き合わせる。
tape JSONL → WF→座標マッピング → 遷移行列集計 → Q̂ 推定 → Residual Bootstrap CI
→ 理論値との乖離検定。

使い方:
    from mekhane.taxis.q_empirical import QEmpiricalPipeline
    p = QEmpiricalPipeline()
    result = p.run(bootstrap_n=2000)
    print(result.summary())

導出チェーン:
  tape (JSONL) → COMPLETE エントリ抽出
    → WF名パース → 座標マッピング (24動詞 → 6族 → 6座標)
      → 連続遷移ペア → 遷移行列 T̂
        → Q̂ = (P̂ - P̂ᵀ)/2
          → Residual Bootstrap (B=2000) → 15辺 × (Q̂, CI_low, CI_high)
            → Q₀ vs Q̂ 乖離検定
"""


import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from mekhane.taxis.q_series import (
    COORDINATES,
    COORD_INDEX,
    QMatrix,
)


# ---------------------------------------------------------------------------
# 定数: WF → 座標マッピング
# ---------------------------------------------------------------------------

# PURPOSE: 24動詞 → 6族 → 6座標。体系から演繹的に定まる。
VERB_TO_COORD: dict[str, str] = {
    # Telos (目的) = Flow × Value
    "noe": "Value",
    "bou": "Value",
    "zet": "Value",
    "ene": "Value",
    # Methodos (方法) = Flow × Function
    "ske": "Function",
    "sag": "Function",
    "pei": "Function",
    "tek": "Function",
    # Krisis (判断) = Flow × Precision
    "kat": "Precision",
    "epo": "Precision",
    "pai": "Precision",
    "dok": "Precision",
    # Diástasis (拡張) = Flow × Scale
    "lys": "Scale",
    "ops": "Scale",
    "akr": "Scale",
    "arc": "Scale",
    # Orexis (欲求) = Flow × Valence
    "beb": "Valence",
    "ele": "Valence",
    "kop": "Valence",
    "dio": "Valence",
    # Chronos (時間) = Flow × Temporality
    "hyp": "Temporality",
    "prm": "Temporality",
    "ath": "Temporality",
    "par": "Temporality",
    # S極 (Afferent, v5.0+)
    "the": "Value",
    "ant": "Value",
    "ere": "Function",
    "agn": "Function",
    "sap": "Precision",
    "ski": "Precision",
    "prs": "Scale",
    "per": "Scale",
    "apo": "Valence",
    "exe": "Valence",
    "his": "Temporality",
    "prg": "Temporality",
}

# PURPOSE: τ層 WF → 座標マッピング。
# /bye, /boot は時間の境界を切る行為 → Temporality。
# その他は除外 (座標的に曖昧 or マクロ展開後に分析すべき)。
TAU_TO_COORD: dict[str, str] = {
    "bye": "Temporality",
    "boot": "Temporality",
    "rom": "Temporality",  # 記憶の焼付 = 時間的保存
    "hon": "Valence",  # 本気 = 肯定方向の駆動
    "u": "Valence",  # 意見 = 主観的価値判断
    "eat": "Value",  # 消化 = 内部化
    "fit": "Precision",  # 適合検証 = 精度確認
    "vet": "Precision",  # 監査 = 精度確認
    "dendron": "Precision",  # 存在証明 = 精度確認
    "basanos": "Precision",  # 静的解析 = 精度確認
}

# PURPOSE: CCL マクロ → 主要座標のマッピング。
# マクロは複数 WF を含むが、tape にはマクロ名のみ記録されるため
# 主要座標で近似する。
MACRO_TO_COORD: dict[str, str] = {
    "plan": "Value",  # 段取り → 目的設定
    "fix": "Valence",  # 直す → 是正
    "build": "Function",  # 組む → 方法
    "chew": "Value",  # 噛む → 理解の内部化
    "dig": "Precision",  # 掘る → 精密分析
    "exp": "Function",  # 鍛える → 実験
    "vet": "Precision",  # 確かめる → 精度
    "learn": "Temporality",  # 刻む → 時間的学習
    "next": "Temporality",  # 次 → 未来志向
    "rest": "Temporality",  # 休む → 時間的停止
    "wake": "Temporality",  # 起きる → 時間的再開
    "ready": "Scale",  # 見渡す → 俯瞰
    "read": "Value",  # 読む → 認識
    "search": "Function",  # 検索 → 探索
    "nous": "Value",  # 問う → 認識
    "ero": "Value",  # ソクラテス的探求 → 認識
    "query": "Function",  # 問う(検索) → 探索
    "helm": "Value",  # 舵 → 目的
    "noe": "Value",  # 見通す → 認識
    "design": "Function",  # デザイン → 方法
    "syn": "Scale",  # 監る → 俯瞰
    "proof": "Precision",  # 裁く → 精度
    "rpr": "Function",  # 回す (RPR) → 方法
    "kyc": "Precision",  # 回す (KYC) → 精度
    "tak": "Precision",  # 捌く → 精度
    "weave": "Temporality",  # 時を編む → 時間
    "xrev": "Precision",  # 渡す → 精度
    "gap": "Precision",  # ギャップ → 精度 (不確実性)
    "denoise": "Function",  # 逆拡散 → 方法
    "prd": "Value",  # PRD → 目的定義
    "desktop": "Function",  # デスクトップ操作 → 方法
}

# PURPOSE: WF 名パース用の正規表現
_WF_PATTERN = re.compile(
    r"^[/@]?"  # 先頭の / または @
    r"([a-z]+)"  # WF 名本体
    r"[-+]?"  # 修飾子
)


# ---------------------------------------------------------------------------
# WF 名パース
# ---------------------------------------------------------------------------

def parse_wf_to_coord(wf_name: str) -> Optional[str]:
    """WF 名を座標に変換する。

    Args:
        wf_name: "/noe+", "@plan", "/bye" 等

    Returns:
        座標名 ("Value", "Function", ...) or None (マッピング不可)
    """
    if not wf_name:
        return None

    # 複雑な CCL 式 (演算子含む) → 先頭の WF のみ抽出
    # 例: "/noe+>>/ele+" → "noe"
    # 例: "(/noe >> /ele) >> /ene" → "noe"
    wf = wf_name.strip()

    # 括弧・演算子を含む複合 CCL → 先頭のみ
    if any(op in wf for op in (">>", "~", "*", "|", "_", "{")):
        # 先頭の /verb を抽出
        m = re.search(r"[/@]([a-z]+)", wf)
        if m:
            verb = m.group(1)
        else:
            return None
    else:
        # 単純な WF 名
        m = _WF_PATTERN.match(wf)
        if not m:
            return None
        verb = m.group(1)

    # CCL マクロ (@plan 等) は ccl- 接頭辞なしで記録されることがある
    # @plan → "plan", /ccl-plan → "ccl" (→ panic)
    if wf.startswith("@"):
        # @マクロ → MACRO_TO_COORD
        if verb in MACRO_TO_COORD:
            return MACRO_TO_COORD[verb]
        # ccl- 接頭辞付き
        if verb.startswith("ccl"):
            macro_name = wf.lstrip("@").replace("ccl-", "").rstrip("+-")
            return MACRO_TO_COORD.get(macro_name)
        return None

    # /ccl-xxx → マクロ
    if verb == "ccl" or wf.startswith("/ccl-"):
        macro_name = wf.lstrip("/").replace("ccl-", "").rstrip("+-")
        return MACRO_TO_COORD.get(macro_name)

    # 24動詞 → 座標
    if verb in VERB_TO_COORD:
        return VERB_TO_COORD[verb]

    # τ層
    if verb in TAU_TO_COORD:
        return TAU_TO_COORD[verb]

    return None


# ---------------------------------------------------------------------------
# tape ローダー
# ---------------------------------------------------------------------------

# PURPOSE: デフォルトの tape ディレクトリ
# パス: mekhane/taxis/q_empirical.py
#   parents[0]=taxis, [1]=mekhane, [2]=_src|ソースコード, [3]=20_機構|Mekhane, [4]=HGK ルート
_DEFAULT_TAPE_DIR = (
    Path(__file__).resolve().parents[4]
    / "30_記憶｜Mneme"
    / "01_記録｜Records"
    / "g_実行痕跡｜traces"
)


@dataclass
class TapeEntry:
    """tape JSONL の COMPLETE エントリ。"""

    ts: str
    wf: str
    coord: Optional[str]  # マッピング後の座標名
    workflow_name: str = ""
    confidence: float = 0.0
    source: str = ""
    tape_file: str = ""  # 所属 tape ファイル (セッション境界)


def load_tape_entries(
    tape_dir: Optional[Path] = None,
) -> list[TapeEntry]:
    """tape ディレクトリから COMPLETE エントリを読み込み、座標にマッピングする。

    Args:
        tape_dir: tape JSONL のディレクトリ。None ならデフォルト。

    Returns:
        TapeEntry のリスト (タイムスタンプ昇順)
    """
    if tape_dir is None:
        tape_dir = _DEFAULT_TAPE_DIR

    entries: list[TapeEntry] = []
    for f in sorted(tape_dir.glob("tape_*.jsonl")):
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if raw.get("step") != "COMPLETE":
                        continue

                    wf = raw.get("wf", "")
                    coord = parse_wf_to_coord(wf)

                    entries.append(TapeEntry(
                        ts=raw.get("ts", ""),
                        wf=wf,
                        coord=coord,
                        workflow_name=raw.get("workflow_name", ""),
                        confidence=raw.get("confidence", 0.0),
                        source=raw.get("source", ""),
                        tape_file=f.name,
                    ))
        except OSError:
            continue

    # タイムスタンプ昇順ソート
    entries.sort(key=lambda e: e.ts)
    return entries


# ---------------------------------------------------------------------------
# 遷移行列の構築
# ---------------------------------------------------------------------------

def build_transition_matrix(
    entries: list[TapeEntry],
) -> tuple[np.ndarray, int, int]:
    """連続 COMPLETE エントリの座標ペアから遷移行列を構築する。

    同一 tape ファイル内でのみ遷移を数える (セッション境界を跨がない)。
    同一座標間の遷移 (e.g., Value→Value) はカウントしない。

    Args:
        entries: TapeEntry のリスト

    Returns:
        (T, n_transitions, n_unmapped)
        T: 6×6 遷移カウント行列
        n_transitions: 有効な遷移の総数
        n_unmapped: 座標マッピング不可で除外されたエントリ数
    """
    n = len(COORDINATES)
    T = np.zeros((n, n), dtype=int)
    n_transitions = 0
    n_unmapped = 0

    # tape ファイルごとにグループ化
    by_file: dict[str, list[TapeEntry]] = {}
    for e in entries:
        by_file.setdefault(e.tape_file, []).append(e)

    for _file, file_entries in by_file.items():
        prev_coord: Optional[str] = None
        for e in file_entries:
            if e.coord is None:
                n_unmapped += 1
                prev_coord = None  # マッピング不可 → 遷移チェーンを切断
                continue

            if prev_coord is not None and prev_coord != e.coord:
                i = COORD_INDEX[prev_coord]
                j = COORD_INDEX[e.coord]
                T[i, j] += 1
                n_transitions += 1

            prev_coord = e.coord

    return T, n_transitions, n_unmapped


# ---------------------------------------------------------------------------
# Residual Bootstrap
# ---------------------------------------------------------------------------

@dataclass
class BootstrapEdgeResult:
    """1辺の Bootstrap 結果。"""

    edge_id: int
    coord_i: str
    coord_j: str
    q_hat: float  # 点推定
    ci_low: float  # CI 下限
    ci_high: float  # CI 上限
    q_theory: float  # 理論値 Q₀
    in_ci: bool  # Q₀ が CI に含まれるか
    n_transitions_ij: int  # i→j の遷移数
    n_transitions_ji: int  # j→i の遷移数


@dataclass
class BootstrapResult:
    """Bootstrap 全体の結果。"""

    edges: list[BootstrapEdgeResult]
    n_total_transitions: int
    n_unmapped: int
    n_tape_files: int
    n_complete_entries: int
    bootstrap_n: int
    alpha: float

    # Bootstrap サンプルの Q 行列群 (Schur 分解用に保持)
    _q_samples: np.ndarray = field(default_factory=lambda: np.array([]), repr=False)

    @property
    def n_divergent(self) -> int:
        """理論値が CI に含まれない辺の数。"""
        return sum(1 for e in self.edges if not e.in_ci)

    @property
    def divergent_edges(self) -> list[BootstrapEdgeResult]:
        """理論値が CI に含まれない辺。"""
        return [e for e in self.edges if not e.in_ci]

    def summary(self) -> str:
        """結果のサマリーを Markdown テーブルで返す。"""
        lines = [
            "# Q-series Empirical Grounding Report",
            "",
            f"- tape ファイル数: {self.n_tape_files}",
            f"- COMPLETE エントリ数: {self.n_complete_entries}",
            f"- 有効遷移数: {self.n_total_transitions}",
            f"- マッピング不可: {self.n_unmapped}",
            f"- Bootstrap B={self.bootstrap_n}, α={self.alpha}",
            f"- **乖離辺数: {self.n_divergent}/15**",
            "",
            "| Q# | 辺 | Q̂ | CI({:.0f}%)| Q₀ | 乖離 | n_ij | n_ji |".format(
                (1 - self.alpha) * 100
            ),
            "|:---|:---|:---|:-------|:---|:-----|:-----|:-----|",
        ]
        for e in sorted(self.edges, key=lambda x: x.edge_id):
            flag = "❌" if not e.in_ci else "✅"
            lines.append(
                f"| Q{e.edge_id} | {e.coord_i[:3]}→{e.coord_j[:3]} "
                f"| {e.q_hat:+.3f} "
                f"| [{e.ci_low:+.3f}, {e.ci_high:+.3f}] "
                f"| {e.q_theory:+.3f} "
                f"| {flag} "
                f"| {e.n_transitions_ij} | {e.n_transitions_ji} |"
            )
        return "\n".join(lines)


def residual_bootstrap(
    T: np.ndarray,
    q_theory: QMatrix,
    bootstrap_n: int = 2000,
    alpha: float = 0.05,
    rng: Optional[np.random.Generator] = None,
) -> BootstrapResult:
    """Residual Bootstrap で Q̂ の信頼区間を計算する。

    手順:
    1. 観測遷移行列 T̂ から Q̂ を計算
    2. 対称成分 S = (P + Pᵀ)/2 を基準モデルとする
    3. 残差 R = P - S (非対称=循環成分)
    4. B 回リサンプリング:
       a. R の各行を行単位でリサンプリング → R*
       b. P* = S + R*
       c. Q̂* = (P* - P*ᵀ)/2
    5. 15辺の (Q̂, CI_low, CI_high) を返す

    Args:
        T: 6×6 遷移カウント行列
        q_theory: 理論値 QMatrix (Q₀)
        bootstrap_n: リサンプリング回数 (デフォルト 2000)
        alpha: 有意水準 (デフォルト 0.05 → 95% CI)
        rng: 乱数生成器 (再現性用)

    Returns:
        BootstrapResult
    """
    if rng is None:
        rng = np.random.default_rng()

    n = len(COORDINATES)

    # 行正規化 → 遷移確率 P̂
    row_sums = T.sum(axis=1, keepdims=True).astype(float)
    row_sums[row_sums == 0] = 1  # ゼロ除算防止
    P = T.astype(float) / row_sums

    # 点推定 Q̂
    Q_hat = (P - P.T) / 2

    # 対称成分 (基準モデル)
    S = (P + P.T) / 2

    # 残差
    R = P - S  # = Q̂ (反対称成分そのもの)

    # 有効な行の特定 (遷移がある行のみリサンプリング)
    active_rows = T.sum(axis=1) > 0

    # Bootstrap サンプリング
    q_samples = np.zeros((bootstrap_n, n, n))
    for b in range(bootstrap_n):
        R_star = np.zeros_like(R)
        for i in range(n):
            if not active_rows[i]:
                continue
            # 行 i の残差をリサンプリング
            # 残差の列インデックスをリサンプリング
            indices = rng.choice(n, size=n, replace=True)
            R_star[i, :] = R[i, indices]

        # P* = S + R*
        P_star = S + R_star
        # 非負制約 + 行正規化
        P_star = np.maximum(P_star, 0)
        rs = P_star.sum(axis=1, keepdims=True)
        rs[rs == 0] = 1
        P_star = P_star / rs

        # Q̂*
        q_samples[b] = (P_star - P_star.T) / 2

    # CI 計算
    q_lower = np.percentile(q_samples, 100 * alpha / 2, axis=0)
    q_upper = np.percentile(q_samples, 100 * (1 - alpha / 2), axis=0)

    # 理論値の行列
    Q0 = q_theory.matrix

    # 結果構築
    edge_results = []
    edge_id = 1
    for i in range(n):
        for j in range(i + 1, n):
            in_ci = q_lower[i, j] <= Q0[i, j] <= q_upper[i, j]
            edge_results.append(BootstrapEdgeResult(
                edge_id=edge_id,
                coord_i=COORDINATES[i],
                coord_j=COORDINATES[j],
                q_hat=float(Q_hat[i, j]),
                ci_low=float(q_lower[i, j]),
                ci_high=float(q_upper[i, j]),
                q_theory=float(Q0[i, j]),
                in_ci=in_ci,
                n_transitions_ij=int(T[i, j]),
                n_transitions_ji=int(T[j, i]),
            ))
            edge_id += 1

    return BootstrapResult(
        edges=edge_results,
        n_total_transitions=int(T.sum()),
        n_unmapped=0,  # 呼び出し側で設定
        n_tape_files=0,  # 呼び出し側で設定
        n_complete_entries=0,  # 呼び出し側で設定
        bootstrap_n=bootstrap_n,
        alpha=alpha,
        _q_samples=q_samples,
    )


# ---------------------------------------------------------------------------
# Schur 周波数の経験的推定
# ---------------------------------------------------------------------------

def empirical_schur(result: BootstrapResult) -> dict:
    """Bootstrap サンプルから Schur 周波数の分布を推定する。

    各 Q̂* に Schur 分解を適用し、3回転面 (ω₁, ω₂, ω₃) の分布を計算。

    Args:
        result: BootstrapResult (q_samples を含む)

    Returns:
        dict with:
          - frequencies_mean: [ω₁, ω₂, ω₃] の平均
          - frequencies_ci: [(low, high), ...] の CI
          - frequencies_theory: 理論値の Schur 周波数
    """
    from scipy.linalg import schur

    q_samples = result._q_samples
    if q_samples.size == 0:
        return {"error": "Bootstrap サンプルが空"}

    B = q_samples.shape[0]
    all_freqs = []

    for b in range(B):
        Q = q_samples[b]
        try:
            T_schur, _ = schur(Q, output="complex")
            eigenvalues = np.diag(T_schur)
            imag_parts = np.sort(np.abs(eigenvalues.imag))[::-1]
            freqs = []
            seen: set[float] = set()
            for val in imag_parts:
                rounded = round(val, 10)
                if rounded > 0 and rounded not in seen:
                    freqs.append(rounded)
                    seen.add(rounded)
                if len(freqs) == 3:
                    break
            while len(freqs) < 3:
                freqs.append(0.0)
            all_freqs.append(sorted(freqs, reverse=True))
        except Exception:  # noqa: BLE001
            continue

    if not all_freqs:
        return {"error": "Schur 分解に成功したサンプルなし"}

    freqs_array = np.array(all_freqs)
    alpha = result.alpha

    # 理論値の Schur 周波数
    q_theory = QMatrix.from_theory()
    theory_schur = q_theory.schur_decomposition()

    return {
        "frequencies_mean": freqs_array.mean(axis=0).tolist(),
        "frequencies_std": freqs_array.std(axis=0).tolist(),
        "frequencies_ci": [
            (
                float(np.percentile(freqs_array[:, k], 100 * alpha / 2)),
                float(np.percentile(freqs_array[:, k], 100 * (1 - alpha / 2))),
            )
            for k in range(3)
        ],
        "frequencies_theory": theory_schur["frequencies"],
        "n_successful_decompositions": len(all_freqs),
        "n_total_samples": B,
    }


# ---------------------------------------------------------------------------
# パイプライン
# ---------------------------------------------------------------------------

@dataclass
class QEmpiricalPipeline:
    """Q-series Empirical Grounding Pipeline。

    tape JSONL → 遷移行列 → Q̂ + Bootstrap CI → 理論値乖離検定。
    """

    tape_dir: Optional[Path] = None

    def run(
        self,
        bootstrap_n: int = 2000,
        alpha: float = 0.05,
        seed: Optional[int] = None,
    ) -> BootstrapResult:
        """パイプラインを実行する。

        Args:
            bootstrap_n: Bootstrap リサンプリング回数 (デフォルト 2000)
            alpha: 有意水準 (デフォルト 0.05 → 95% CI)
            seed: 乱数シード (再現性用)

        Returns:
            BootstrapResult
        """
        rng = np.random.default_rng(seed)

        # 1. tape ロード
        entries = load_tape_entries(self.tape_dir)

        # 2. 遷移行列構築
        T, n_transitions, n_unmapped = build_transition_matrix(entries)

        # 3. 理論値
        q_theory = QMatrix.from_theory()

        # 4. Bootstrap
        result = residual_bootstrap(
            T=T,
            q_theory=q_theory,
            bootstrap_n=bootstrap_n,
            alpha=alpha,
            rng=rng,
        )

        # メタ情報を設定
        result.n_unmapped = n_unmapped
        result.n_tape_files = len(set(e.tape_file for e in entries))
        result.n_complete_entries = len(entries)

        return result

    def run_with_schur(
        self,
        bootstrap_n: int = 2000,
        alpha: float = 0.05,
        seed: Optional[int] = None,
    ) -> tuple[BootstrapResult, dict]:
        """パイプライン + Schur 周波数の経験的推定。

        Returns:
            (BootstrapResult, schur_dict)
        """
        result = self.run(bootstrap_n=bootstrap_n, alpha=alpha, seed=seed)
        schur_result = empirical_schur(result)
        return result, schur_result
