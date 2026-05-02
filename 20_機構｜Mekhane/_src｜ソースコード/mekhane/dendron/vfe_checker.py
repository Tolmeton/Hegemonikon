# PROOF: [L2/FEP] <- mekhane/dendron/vfe_checker.py
# REASON: [auto] 初回実装 (2026-04-03)
# PURPOSE: Dendron VFE スコアリングロジックの定義と AST 解析による Surprise (乖離度) の算出

import ast
import math
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import subprocess

from mekhane.dendron.checker import DendronChecker
from mekhane.fep.basis import helmholtz_score
from mekhane.dendron.models import ProofStatus

# REASON: [auto] 関数 get_git_root の実装が必要だったため
def get_git_root() -> Path:
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(root)
    except Exception:
        return Path.cwd()

# REASON: [auto] クラス DendronVFEChecker の実装が必要だったため
class DendronVFEChecker:
# REASON: [auto] クラスの初期化処理が必要だったため
    def __init__(self, root: Optional[Path] = None):
        self.root = root or get_git_root()
        # validate_parents=False にして、親ディレクトリの存在チェック等による INVALID を回避する
        self.checker = DendronChecker(root=self.root, validate_parents=False)

# REASON: [auto] 関数 compute_vfe の実装が必要だったため
    def compute_vfe(self, file_path: Path) -> Dict[str, Any]:
        """
        Capacity-bounded Asymmetric VFE Model に基づき VFE を算出する。
        - Prior Precision (π): PROOF.md や # PURPOSE から得られる目的の明確さ
        - Observation Entropy (H_obs): ASTノード数の対数による複雑さの指標
        - Capacity (H_capacity): π に比例して許容されるエントロピーの上限
        - Prediction Error (PE): 許容量を超過したエントロピー (max(0, H_obs - H_capacity))
        - Γ (Gradient): PE^2 (リファクタリング・単純化への圧力)
        - Q (Solenoidal): (1 - π) * W (意味を探索しドキュメント化する圧力)
        - VFE = Γ + Q
        """
        file_proof = self.checker.check_file_proof(file_path)
        
        # 1. Prior Precision (π)
        # PROOF が明確であるほど、より多くの複雑さを「意図されたもの」として許容できる
        if file_proof.status == ProofStatus.OK:
            precision_pi = 1.0
        elif file_proof.status == ProofStatus.ORPHAN:
            precision_pi = 0.8
        elif file_proof.status == ProofStatus.WEAK:
            precision_pi = 0.5
        elif file_proof.status == ProofStatus.MISSING and file_proof.has_reason:
            precision_pi = 0.4
        else:
            precision_pi = 0.1  # PURPOSEなし、または INVALID (一様分布に近く、複雑さを許容しない)
            
        # 2. Observation Entropy (H_obs)
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception:
            return {"error": "parse_failed"}

        # ASTの全ノード数を取得し、構造の情報量 (Shannon Entropy の近似) を底2の対数で計算
        total_nodes = len(list(ast.walk(tree)))
        h_obs = math.log2(total_nodes + 1) if total_nodes > 0 else 0.0
        
        # 3. Capacity-bounded Prediction Error
        # H_base: 完璧な PROOF (π=1.0) が与えられたときに許容される最大エントロピー
        # ノード数 約1023 (log2(1024) = 10) 程度をひとつのモジュールの適正上限と仮定
        h_base = 10.0
        h_capacity = h_base * precision_pi
        
        # 予測誤差: 許容量を超過した複雑さのみをペナルティとする (非対称・ReLU的)
        # コードが単純である (H_obs < H_capacity) ことは「優れた圧縮」でありエラーではない
        prediction_error = max(0.0, h_obs - h_capacity)
        
        # 4. Helmholtz Decomposition (Γ ⊣ Q)
        # Γ (Gradient): 予測誤差の二乗。コードを削れ、リファクタリングせよという最適化圧力
        gamma = prediction_error ** 2
        
        # Q (Solenoidal): 目的の不明確さ (1 - π) に起因する探索圧力。
        # 複雑さに依存せず、PROOFが欠如していること自体へのペナルティ (ドキュメントを書けという圧力)
        w_orphan = 5.0  # 探索圧力のベースウェイト
        q = (1.0 - precision_pi) * w_orphan
        
        # VFE = Γ + Q
        vfe = gamma + q
        
        hs = helmholtz_score(gamma, q)

        return {
            "path": str(file_path.name),
            "proof_status": file_proof.status.name,
            "proof_reason": file_proof.reason,
            "prior_precision": precision_pi,
            "observation_entropy": round(h_obs, 2),
            "prediction_error": round(prediction_error, 2),
            "vfe_score": round(vfe, 2),
            "helmholtz_score": round(hs.score, 2)
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).resolve()
        checker = DendronVFEChecker()
        res = checker.compute_vfe(path)
        print(res)
