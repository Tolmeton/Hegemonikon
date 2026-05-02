import sys
import os
import pickle
import numpy as np

# Adjust path to import hermeneus
sys.path.insert(0, os.path.abspath('20_機構｜Mekhane/_src｜ソースコード'))

from hermeneus.src.parser import CCLParser
from hermeneus.src.forgetfulness_score import extract_coordinates, extract_implicit_coordinates, _count_verb_coverage, COORDINATES, ImplicitScoreResult, ScoreResult, diagnose

def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    array = np.array(array, dtype=np.float64)
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 1e-9  # prevent division by zero
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return (np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array))

def fast_score_ccl_implicit(ccl_str: str, parser: CCLParser) -> ImplicitScoreResult:
    ast = parser.parse(ccl_str)

    explicit_coords = frozenset(extract_coordinates(ast))
    explicit_missing = frozenset(COORDINATES - explicit_coords)
    s_explicit = len(explicit_missing) / len(COORDINATES)
    diag = diagnose(ast)

    explicit_result = ScoreResult(
        score=s_explicit,
        present_coordinates=explicit_coords,
        missing_coordinates=explicit_missing,
        diagnoses=tuple(diag),
        total_coordinates=len(COORDINATES),
        expression=ccl_str,
    )

    implicit_coords = frozenset(extract_implicit_coordinates(ast))
    all_coords = explicit_coords | implicit_coords
    missing_implicit = frozenset(COORDINATES - all_coords)
    s_implicit = len(missing_implicit) / len(COORDINATES)

    verb_coverage = _count_verb_coverage(ast)

    return ImplicitScoreResult(
        explicit=explicit_result,
        implicit_coordinates=implicit_coords,
        all_coordinates=all_coords,
        s_implicit=s_implicit,
        missing_implicit=missing_implicit,
        verb_coverage=verb_coverage,
    )

def main():
    pkl_path = "30_記憶｜Mneme/02_索引｜Index/code.pkl"
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
        
    metadata = data.get('metadata', {})
    print(f"Loaded {len(metadata)} functions from code.pkl")
    
    parser = CCLParser()
    
    coords_list = sorted(list(COORDINATES))
    s_matrix = []  
    s_implicit_scores = []
    
    valid_count = 0
    error_count = 0
    
    # Supress warnings
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    for k, v in metadata.items():
        ccl_expr = v.get('ccl_expr')
        if not ccl_expr:
            continue
        try:
            res = fast_score_ccl_implicit(ccl_expr, parser)
            missing = res.missing_implicit
            row = [1.0 if c in missing else 0.0 for c in coords_list]
            s_matrix.append(row)
            s_implicit_scores.append(res.s_implicit)
            valid_count += 1
        except Exception:
            # 擬似 CCL 構文によるパースエラー時は暗黙座標 0 のため 1.0 (完全忘却) とする
            row = [1.0 for _ in coords_list]
            s_matrix.append(row)
            s_implicit_scores.append(1.0)
            error_count += 1
            valid_count += 1
            
    print(f"\nProcessed {valid_count} functions (parsed {valid_count - error_count}, fallback {error_count})")
    
    s_matrix = np.array(s_matrix)
    p_k = np.mean(s_matrix, axis=0)
    
    print("\n--- 座標別忘却率 (p_k: 1に近いほどよく忘却されている) ---")
    for c, p in zip(coords_list, p_k):
        print(f"  {c}: {p:.4f}")
        
    gini_p = gini(p_k)
    var_p = np.var(p_k)
    
    print(f"\n--- 分布構造測度 ---")
    print(f"Mean(S_implicit): {np.mean(s_implicit_scores):.4f}")
    print(f"Var(p_k): {var_p:.4f}")
    print(f"Gini(p_k) [Ξ_discrete]: {gini_p:.4f}")
    
    features_path = "30_記憶｜Mneme/02_索引｜Index/code_ccl_features.pkl"
    with open(features_path, 'rb') as f:
        feat_data = pickle.load(f)
        
    vecs = np.array(feat_data['vectors'])
    means = np.mean(vecs, axis=0)
    stds = np.std(vecs, axis=0)
    cvs = stds / (means + 1e-9)
    # 49次元すべてで CV の Gini を取るか、それとも特定の次元か？
    # 課題通り全体の特徴量 CV のジニ係数を計算して比較
    cv_gini = gini(cvs)
    
    print(f"\n--- 比較対象 ---")
    print(f"CV Gini [Ξ_search]: {cv_gini:.4f}")
    print(f"Difference (Ξ_discrete - Ξ_search): {gini_p - cv_gini:.4f}")

if __name__ == '__main__':
    main()
