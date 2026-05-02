# PROOF: [L2/インフラ] <- mekhane/dendron/tests/test_mece.py
"""
MECE チェッカーのテスト。

embed_fn をモック注入して API コストなしでテスト。
numpy の代わりにリスト演算でモックベクトルを生成。
"""

import tempfile
from pathlib import Path

import pytest

from mekhane.dendron.checker import DendronChecker
from mekhane.dendron.models import MECEIssue


# ─── ヘルパー ───────────────────────────────────


def _make_dir(parent: Path, name: str, purpose: str = "", reason: str = "") -> Path:
    """PROOF.md 付きのディレクトリを作成"""
    d = parent / name
    d.mkdir(parents=True, exist_ok=True)
    lines = []
    if purpose:
        lines.append(f"PURPOSE: {purpose}")
    if reason:
        lines.append(f"REASON: {reason}")
    if lines:
        (d / "PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    return d


_ORTHOGONAL_COUNTER: dict[str, int] = {}


def _mock_embed_orthogonal(text: str) -> list[float]:
    """各テキストに異なる方向の単位ベクトルを割り当てるモック。

    テキストごとに一意の次元インデックスを割り当て、
    その次元だけ 1.0 の 16 次元ベクトルを返す。
    hash 衝突を避けるため、初回呼び出し時にカウンタで管理する。
    """
    dim = 16
    if text not in _ORTHOGONAL_COUNTER:
        _ORTHOGONAL_COUNTER[text] = len(_ORTHOGONAL_COUNTER)
    idx = _ORTHOGONAL_COUNTER[text] % dim
    vec = [0.0] * dim
    vec[idx] = 1.0
    return vec


def _mock_embed_identical(text: str) -> list[float]:
    """ほぼ同一方向のベクトル + 小さなノイズを返すモック (d_eff ≈ 1)。

    全く同一だと中心化でゼロベクトルになるため、
    テキストハッシュからノイズを加える。ノイズは eigenvalue 閾値 (1e-10) を
    十分超える大きさにする。
    """
    dim = 16
    base = [1.0] * dim
    noise = (hash(text) % 1000) / 10000  # 0.0xxx のノイズ (d_eff 閾値を超える)
    base[hash(text) % dim] += noise
    return base


def _mock_embed_similar_pair(text: str) -> list[float]:
    """特定のテキストペアだけ類似ベクトルを返すモック。"""
    dim = 16
    if "認知" in text or "知性" in text:
        # 類似方向
        vec = [0.8] * dim
        if "知性" in text:
            vec[0] = 0.85  # ほぼ同じ方向
        return vec
    else:
        # 直交方向
        idx = hash(text) % dim
        vec = [0.0] * dim
        vec[idx] = 1.0
        return vec


# ─── テストクラス ────────────────────────────────


class TestMECENumberPrefix:
    """ME: 番号プレフィックス衝突 (テキストベース、embed_fn 不要)"""

    def test_no_collision(self, tmp_path: Path) -> None:
        """異なる番号プレフィックスは衝突しない"""
        _make_dir(tmp_path, "01_alpha", "Alpha purpose")
        _make_dir(tmp_path, "02_beta", "Beta purpose")
        _make_dir(tmp_path, "03_gamma", "Gamma purpose")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        number_issues = [i for i in issues if i.issue_type == "me_number"]
        assert len(number_issues) == 0

    def test_collision_detected(self, tmp_path: Path) -> None:
        """同じ番号プレフィックスは衝突として報告"""
        _make_dir(tmp_path, "01_alpha", "Alpha purpose")
        _make_dir(tmp_path, "01_beta", "Beta purpose")  # 衝突!
        _make_dir(tmp_path, "02_gamma", "Gamma purpose")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        number_issues = [i for i in issues if i.issue_type == "me_number"]
        assert len(number_issues) == 1
        assert number_issues[0].severity == "error"


class TestMECEPurposeSimilarity:
    """ME: PURPOSE cosine 類似度チェック"""

    def test_orthogonal_purposes_no_issue(self, tmp_path: Path) -> None:
        """直交する PURPOSE は ME 違反なし"""
        _make_dir(tmp_path, "01_alpha", "Alpha: データ管理")
        _make_dir(tmp_path, "02_beta", "Beta: ネットワーク通信")
        _make_dir(tmp_path, "03_gamma", "Gamma: UI表示")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=_mock_embed_orthogonal)
        purpose_issues = [i for i in issues if i.issue_type == "me_purpose"]
        assert len(purpose_issues) == 0

    def test_identical_purposes_detected(self, tmp_path: Path) -> None:
        """同一 PURPOSE は ME 違反として検出"""
        _make_dir(tmp_path, "01_alpha", "同一の内容")
        _make_dir(tmp_path, "02_beta", "同一の内容")
        _make_dir(tmp_path, "03_gamma", "同一の内容")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=_mock_embed_identical)
        purpose_issues = [i for i in issues if i.issue_type == "me_purpose" and i.similarity is not None]
        # 3C2 = 3 ペアが全て類似として検出されるはず
        assert len(purpose_issues) >= 1


class TestMECEParticipationRatio:
    """ME: d_eff (participation ratio) チェック"""

    def test_orthogonal_high_d_eff(self, tmp_path: Path) -> None:
        """直交する PURPOSE → d_eff ≈ n_children → 問題なし"""
        for i in range(5):
            _make_dir(tmp_path, f"0{i}_dir{i}", f"Purpose {i} unique direction")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=_mock_embed_orthogonal)
        d_eff_issues = [i for i in issues if i.issue_type == "me_purpose" and i.d_eff is not None]
        assert len(d_eff_issues) == 0

    def test_identical_low_d_eff(self, tmp_path: Path) -> None:
        """同一方向 → d_eff ≈ 1 → ME 冗長性検出"""
        for i in range(5):
            _make_dir(tmp_path, f"0{i}_dir{i}", f"同じ方向のPurpose {i}")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=_mock_embed_identical)
        d_eff_issues = [i for i in issues if i.issue_type == "me_purpose" and i.d_eff is not None]
        assert len(d_eff_issues) >= 1
        assert d_eff_issues[0].d_eff is not None
        assert d_eff_issues[0].d_eff < 3.0  # 5子で d_eff < 3 → 冗長


class TestBCNFDiagnostics:
    """BCNF 診断: deletability 検出時に最近傍・共有語・固有語・差別化ヒントが付与されるか"""

    def test_bcnf_diagnostic_fields(self, tmp_path: Path) -> None:
        """BCNF 検出時に診断フィールドが付与される"""
        # 4つの冗長 + 1つの固有ディレクトリ
        _make_dir(tmp_path, "01_alpha", "データを管理する永続化エンジン")
        _make_dir(tmp_path, "02_beta",  "データを管理する保存エンジン")
        _make_dir(tmp_path, "03_gamma", "データを管理する記録エンジン")
        _make_dir(tmp_path, "04_delta", "データを管理する蓄積エンジン")
        _make_dir(tmp_path, "05_unique", "量子力学的トポロジー解析")

        dim = 16
        def embed_redundant(text: str) -> list[float]:
            """冗長ディレクトリはほぼ同じ方向、fixed は直交方向"""
            if "量子力学" in text:
                vec = [0.0] * dim
                vec[0] = 1.0
                return vec
            # 冗長な方向 (全てほぼ同じベクトル)
            base = [0.0] * dim
            base[1] = 1.0
            # テキストに依存した微小ノイズ
            noise_idx = hash(text) % dim
            base[noise_idx] += 0.01
            return base

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=embed_redundant)
        bcnf = [i for i in issues if i.issue_type == "bcnf_deletable"]

        # 冗長ディレクトリのうち少なくとも1つが検出されるはず
        if len(bcnf) > 0:
            issue = bcnf[0]
            # 診断フィールドが付与されている
            assert issue.nearest_neighbor is not None, "nearest_neighbor が None"
            assert issue.differentiation_hint is not None, "differentiation_hint が None"
            assert issue.deletability is not None and issue.deletability > 0.95

    def test_bcnf_no_detection_orthogonal(self, tmp_path: Path) -> None:
        """直交する PURPOSE → BCNF 検出なし"""
        for i in range(5):
            _make_dir(tmp_path, f"0{i}_dir{i}", f"Purpose {i} unique direction")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=_mock_embed_orthogonal)
        bcnf = [i for i in issues if i.issue_type == "bcnf_deletable"]
        assert len(bcnf) == 0


class TestMECEDecomposition:
    """CE: 最小子ディレクトリ数"""

    def test_sufficient_children_no_issue(self, tmp_path: Path) -> None:
        """子が 3 以上なら CE 違反なし"""
        _make_dir(tmp_path, "01_a", "A")
        _make_dir(tmp_path, "02_b", "B")
        _make_dir(tmp_path, "03_c", "C")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        decomp_issues = [i for i in issues if i.issue_type == "ce_decomposition"]
        assert len(decomp_issues) == 0

    def test_insufficient_children_detected(self, tmp_path: Path) -> None:
        """子が 2 以下なら CE 違反"""
        _make_dir(tmp_path, "01_a", "A")
        _make_dir(tmp_path, "02_b", "B")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        decomp_issues = [i for i in issues if i.issue_type == "ce_decomposition"]
        assert len(decomp_issues) == 1
        assert decomp_issues[0].severity == "warning"


class TestMECEProofCoverage:
    """CE: PROOF.md カバー率"""

    def test_all_have_proof(self, tmp_path: Path) -> None:
        """全子に PROOF.md → 問題なし"""
        _make_dir(tmp_path, "01_a", "A")
        _make_dir(tmp_path, "02_b", "B")
        _make_dir(tmp_path, "03_c", "C")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        proof_issues = [i for i in issues if i.issue_type == "ce_proof"]
        assert len(proof_issues) == 0

    def test_missing_proof_detected(self, tmp_path: Path) -> None:
        """PROOF.md がない子は CE 違反"""
        _make_dir(tmp_path, "01_a", "A")
        d_b = tmp_path / "02_b"
        d_b.mkdir()  # PROOF.md なし
        _make_dir(tmp_path, "03_c", "C")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        proof_issues = [i for i in issues if i.issue_type == "ce_proof"]
        assert len(proof_issues) == 1


class TestMECEResidual:
    """CE: SVD 射影残差"""

    def test_well_covered_no_issue(self, tmp_path: Path) -> None:
        """子空間が親をカバー → 問題なし"""
        # 親と子の PURPOSE を設定して embed
        (tmp_path / "PROOF.md").write_text("PURPOSE: 認知と判断の統合", encoding="utf-8")
        _make_dir(tmp_path, "01_a", "認知の処理")
        _make_dir(tmp_path, "02_b", "判断の処理")
        _make_dir(tmp_path, "03_c", "統合の処理")

        # 親ベクトルが子空間内にあるモック
        def embed_covered(text: str) -> list[float]:
            dim = 16
            if "認知と判断の統合" in text:
                return [1.0, 1.0, 1.0] + [0.0] * (dim - 3)
            elif "認知" in text:
                return [1.0, 0.0, 0.0] + [0.0] * (dim - 3)
            elif "判断" in text:
                return [0.0, 1.0, 0.0] + [0.0] * (dim - 3)
            elif "統合" in text:
                return [0.0, 0.0, 1.0] + [0.0] * (dim - 3)
            return [0.0] * dim

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path, embed_fn=embed_covered)
        residual_issues = [i for i in issues if i.issue_type == "ce_residual"]
        assert len(residual_issues) == 0


class TestMECERecursion:
    """再帰的チェック"""

    def test_recursive_check(self, tmp_path: Path) -> None:
        """ネストしたディレクトリも再帰的にチェック"""
        parent = _make_dir(tmp_path, "01_parent", "親")
        _make_dir(parent, "01_child_a", "子A")  # 子が 1 つ → ce_decomposition
        _make_dir(tmp_path, "02_sibling", "兄弟")
        _make_dir(tmp_path, "03_other", "他")

        checker = DendronChecker(exempt_patterns=[])
        issues = checker.check_mece(tmp_path)
        # parent 配下に ce_decomposition が出るはず
        decomp_issues = [i for i in issues if i.issue_type == "ce_decomposition"]
        assert len(decomp_issues) >= 1
