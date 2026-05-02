# CCL-PL ランタイム — トランスパイルされたコードが依存するヘルパー関数
"""
CCL-PL Runtime

CCL → Python トランスパイラが生成するコードが依存する
ランタイムヘルパー関数群。

各関数は CCL 演算子の操作的意味論を Python で実装する。
"""

import asyncio
import itertools
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union


# =============================================================================
# 融合 / 展開 (代数的演算子)
# =============================================================================

def merge(*args: Any, weights: Optional[List[float]] = None) -> Dict[str, Any]:
    """融合 (*) — 精度加重された統合
    
    CCL: A * B
    圏論: Catamorphism (fold) — F-代数的消費 (α: F(A) → A)
    
    辞書ならマージ、数値なら加重平均、リストなら結合。
    """
    if not args:
        return {}
    
    # 全て辞書の場合 → マージ
    if all(isinstance(a, dict) for a in args):
        result = {}
        for d in args:
            result.update(d)
        return result
    
    # 全て数値の場合 → 加重平均
    if all(isinstance(a, (int, float)) for a in args):
        if weights:
            total_w = sum(weights)
            return sum(a * w for a, w in zip(args, weights)) / total_w
        return sum(args) / len(args)
    
    # リストの場合 → 結合
    if all(isinstance(a, list) for a in args):
        result = []
        for lst in args:
            result.extend(lst)
        return result
    
    # フォールバック → タプル
    return args


def product(*args: Any) -> List[Tuple]:
    """展開 (%) — 全次元の組み合わせを保持
    
    CCL: A % B
    圏論: Anamorphism (unfold) — F-余代数的生成 (β: A → F(A))
    """
    if not args:
        return []
    
    # 各引数をイテラブルに変換
    iterables = []
    for a in args:
        if isinstance(a, (list, tuple, set)):
            iterables.append(a)
        elif isinstance(a, dict):
            iterables.append(list(a.items()))
        else:
            iterables.append([a])
    
    return list(itertools.product(*iterables))


# =============================================================================
# 振動 / 収束 / 発散 (プロセス演算子)
# =============================================================================

def oscillate(fn_a: Callable, fn_b: Callable, 
              max_iter: int = 5, 
              state: Any = None) -> Generator:
    """振動 (~) — 二者間の対話的往復
    
    CCL: A ~ B
    圏論: 余代数的展開 (Q 成分)
    
    fn_a と fn_b を交互に呼び、各ステップの結果を yield する。
    """
    current = state
    for i in range(max_iter):
        current = fn_a(current)
        yield ("a", i, current)
        current = fn_b(current)
        yield ("b", i, current)


def converge(fn_a: Callable, fn_b: Callable,
             max_iter: int = 5,
             threshold: float = 0.01,
             state: Any = None) -> Any:
    """収束振動 (~*) — 不動点への収束
    
    CCL: A ~* B
    圏論: terminal coalgebra (最大不動点)
    
    fn_a と fn_b を交互に呼び、結果が安定したら停止。
    """
    current = state
    prev = None
    
    for i in range(max_iter):
        current = fn_a(current)
        current = fn_b(current)
        
        # 収束判定
        if prev is not None:
            try:
                if isinstance(current, (int, float)) and isinstance(prev, (int, float)):
                    if abs(current - prev) < threshold:
                        return current
                elif current == prev:
                    return current
            except (TypeError, ValueError):
                pass
        
        prev = current
    
    return current


def diverge(fn_a: Callable, fn_b: Callable,
            max_iter: int = 5,
            state: Any = None) -> List[Any]:
    """発散振動 (~!) — 可能性空間の拡大
    
    CCL: A ~! B
    圏論: initial algebra (最小不動点)
    
    fn_a と fn_b を交互に呼び、全ての中間結果を収集。
    """
    results = []
    current = state
    
    for i in range(max_iter):
        current = fn_a(current)
        results.append(current)
        current = fn_b(current)
        results.append(current)
    
    return results


def meta(fn: Callable) -> Callable:
    """メタ (^) — 関手的適用 (ネスト構造)
    
    CCL: A^
    圏論: 関手の適用 F(−)
    
    リスト・辞書等の各要素に fn を適用する = MB の入れ子構造。
    Creator の洞察: ^ はネスト = Markov Blanket の入れ子構造そのもの。
    
    meta(fn)(items) → [fn(item) for item in items]
    meta(fn)(dict)  → {k: fn(v) for k, v in dict.items()}
    meta(fn)(x)     → fn(x)  (非コレクション)
    """
    def apply(items: Any = None, **kwargs) -> Any:
        if items is None:
            return fn(**kwargs)
        if isinstance(items, list):
            return [fn(item, **kwargs) for item in items]
        if isinstance(items, dict):
            return {k: fn(v, **kwargs) for k, v in items.items()}
        if isinstance(items, tuple):
            return tuple(fn(item, **kwargs) for item in items)
        # 非コレクション → 直接適用
        return fn(items, **kwargs)
    return apply


# =============================================================================
# パイプライン
# =============================================================================

def pipe(*fns: Callable) -> Callable:
    """パイプライン (|>) — 関数合成
    
    CCL: A |> B |> C
    圏論: 射の合成 g ∘ f
    
    pipe(f, g, h)(x) = h(g(f(x)))
    """
    def composed(x: Any = None) -> Any:
        result = x
        for fn in fns:
            if result is None:
                result = fn()
            else:
                result = fn(result)
        return result
    return composed


async def parallel(*fns: Callable) -> List[Any]:
    """並列実行 (||) — 同時実行
    
    CCL: A || B || C
    圏論: 直積 A × B × C
    """
    async def _wrap(fn):
        if asyncio.iscoroutinefunction(fn):
            return await fn()
        return fn()
    
    return await asyncio.gather(*[_wrap(fn) for fn in fns])


# =============================================================================
# タグ付きブロック
# =============================================================================

def validate(result: Any, predicate: Optional[Callable] = None) -> Any:
    """検証 (V:) — 結果の検証
    
    CCL: V:{body}
    
    predicate があれば検証し、失敗なら ValueError。
    なければ結果をそのまま返す。
    """
    if predicate is not None:
        if not predicate(result):
            raise ValueError(f"検証失敗: {result}")
    return result


def cycle(fn: Callable, n: int = 1, state: Any = None) -> Any:
    """サイクル (C:) — N回反復実行
    
    CCL: C:{body}
    """
    current = state
    for _ in range(n):
        current = fn(current)
    return current


def memo(result: Any, key: str = "default", store: Optional[Dict] = None) -> Any:
    """記憶 (M:) — 結果の永続化
    
    CCL: M:{body}
    """
    if store is not None:
        store[key] = result
    return result


# =============================================================================
# 双対生成 (\ 演算子) — CCL-PL のユニーク機能
# =============================================================================

# 双対レジストリ: 関数名 → 双対関数のマッピング (対称的)
_dual_registry: Dict[str, Callable] = {}

# 随伴レジストリ: 左随伴名 → 右随伴名 のマッピング (方向付き)
# F ⊣ G ならば _adjunction_registry["F"] = "G"
# right_adjoint("F") → "G", left_adjoint("G") → "F"
_adjunction_registry: Dict[str, str] = {}

# 演算子の双対マップ (CCL operators.md 準拠)
OPERATOR_DUALS = {
    "merge": "product",     # * ↔ %
    "product": "merge",     # % ↔ *
    "converge": "diverge",  # ~* ↔ ~!
    "diverge": "converge",  # ~! ↔ ~*
}


def register_dual(fn_a: Union[Callable, str], fn_b: Union[Callable, str]) -> None:
    """2つの関数/名前を双対 (随伴対) として登録する
    
    Callable 引数:
        register_dual(encode, decode) → fn.__name__ で登録
    文字列引数 (トランスパイラ生成コード用):
        register_dual("noe", "zet") → 文字列をそのままキーに
    
    CCL: /noe || /zet → register_dual("noe", "zet")
    圏論: F ⊣ G (随伴対)
    """
    name_a = fn_a if isinstance(fn_a, str) else fn_a.__name__
    name_b = fn_b if isinstance(fn_b, str) else fn_b.__name__
    
    # 双対レジストリ (対称): 双方向で登録
    if callable(fn_a) and callable(fn_b):
        _dual_registry[name_a] = fn_b
        _dual_registry[name_b] = fn_a
    else:
        # 文字列の場合はプレースホルダーとして名前のみ記録
        # (実関数は後で bind される想定)
        _dual_registry[name_a] = name_b  # type: ignore[assignment]
        _dual_registry[name_b] = name_a  # type: ignore[assignment]
    
    # 随伴レジストリ (方向付き): F ⊣ G = F が左、G が右
    _adjunction_registry[name_a] = name_b


def dual_of(partner: Callable) -> Callable:
    """デコレータ: 双対関数を登録する
    
    使用例:
        def encode(data):
            return base64.b64encode(data)
        
        @dual_of(encode)
        def decode(data):
            return base64.b64decode(data)
        
        # 以降、dual("encode") → decode が利用可能
        # CCL では \\encode と書くだけで decode を呼べる
    """
    def decorator(fn: Callable) -> Callable:
        register_dual(partner, fn)
        return fn
    return decorator


def dual(fn_or_name: Union[Callable, str]) -> Callable:
    """関数の双対を取得する
    
    CCL: \\A → A の双対関数
    圏論: f に対する f* (随伴、逆射、引き戻し)
    
    検索順:
    1. ユーザ登録された双対 (register_dual / @dual_of)
    2. 組み込み演算子の双対 (OPERATOR_DUALS)
    3. 見つからない場合は DualNotFoundError を送出
    """
    name = fn_or_name if isinstance(fn_or_name, str) else fn_or_name.__name__
    
    # 1. ユーザ登録
    if name in _dual_registry:
        return _dual_registry[name]
    
    # 2. 組み込み演算子
    if name in OPERATOR_DUALS:
        dual_name = OPERATOR_DUALS[name]
        # グローバルから関数を取得
        import sys
        this_module = sys.modules[__name__]
        return getattr(this_module, dual_name)
    
    raise DualNotFoundError(name)


class DualNotFoundError(Exception):
    """双対が登録されていない場合のエラー"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"'{name}' の双対が見つかりません。"
            f"register_dual() または @dual_of() で登録してください。"
        )


class AdjointNotFoundError(Exception):
    """随伴が登録されていない場合のエラー"""
    def __init__(self, name: str, direction: str):
        self.name = name
        self.direction = direction
        super().__init__(
            f"'{name}' の{direction}随伴が見つかりません。"
            f"register_dual() で随伴対を登録してください。"
        )


def right_adjoint(name: str) -> Union[str, Callable]:
    """右随伴を取得する
    
    CCL: F|> → G (F の右随伴)
    圏論: F ⊣ G のとき、F から G を取得
    
    register_dual("noe", "zet") 後:
        right_adjoint("noe") → "zet"
    """
    if name in _adjunction_registry:
        right_name = _adjunction_registry[name]
        # 実関数が _dual_registry にあればそちらを返す
        if right_name in _dual_registry and callable(_dual_registry[right_name]):
            return _dual_registry[right_name]
        return right_name
    raise AdjointNotFoundError(name, "右")


def left_adjoint(name: str) -> Union[str, Callable]:
    """左随伴を取得する
    
    CCL: G<| → F (G の左随伴)
    圏論: F ⊣ G のとき、G から F を取得
    
    register_dual("noe", "zet") 後:
        left_adjoint("zet") → "noe"
    """
    # _adjunction_registry の逆引き: value が name であるキーを探す
    for left_name, right_name in _adjunction_registry.items():
        if right_name == name:
            # 実関数が _dual_registry にあればそちらを返す
            if left_name in _dual_registry and callable(_dual_registry[left_name]):
                return _dual_registry[left_name]
            return left_name
    raise AdjointNotFoundError(name, "左")


def invert_pipeline(*fns: Callable) -> Callable:
    """パイプラインを逆転する
    
    CCL: \\(A >> B >> C) = \\C >> \\B >> \\A
    
    各関数の双対を取得し、逆順に合成する。
    パイプライン全体の「逆変換」を一発で生成。
    
    使用例:
        encode_pipeline = pipe(compress, base64_encode, encrypt)
        decode_pipeline = invert_pipeline(compress, base64_encode, encrypt)
        # → pipe(dual(encrypt), dual(base64_encode), dual(compress))
    """
    dual_fns = [dual(fn) for fn in reversed(fns)]
    return pipe(*dual_fns)


def with_dual(fn: Callable, dual_fn: Callable) -> Callable:
    """関数に双対を付与して返す (インライン登録)
    
    使用例:
        encode = with_dual(
            lambda data: base64.b64encode(data),
            lambda data: base64.b64decode(data)
        )
        # dual("encode") で逆変換が取得可能
    """
    register_dual(fn, dual_fn)
    return fn


# =============================================================================
# 逆射 / Pullback (<< 演算子) — 目標から逆算する
# =============================================================================

def backward(goal: Any, *fns: Callable) -> Any:
    """逆射 (<<) — 目標から逆算して入力を推定する
    
    CCL: goal << A << B << C
    圏論: pullback / 引き戻し
    
    各関数の双対 (dual()) を逆順に適用して入力を推定する。
    
    使用例:
        # encode → compress → encrypt のパイプラインの逆射
        # 暗号文 << encrypt << compress << encode
        # = decode(decompress(decrypt(暗号文)))
        
        original = backward(encrypted_data, encrypt, compress, encode)
    """
    current = goal
    for fn in fns:
        dual_fn = dual(fn)
        current = dual_fn(current)
    return current


def backward_search(goal: Any, fn: Callable, 
                    candidates: Optional[List[Any]] = None,
                    predicate: Optional[Callable] = None) -> Optional[Any]:
    """逆像探索 — 双対が存在しない場合のフォールバック
    
    CCL: goal << fn (双対未登録時)
    
    候補リストから fn(x) == goal を満たす x を探す。
    双対が登録されていない場合の「力技」解法。
    
    predicate: カスタム一致判定 (デフォルトは等価比較)
    """
    if candidates is None:
        return None
    
    match_fn = predicate or (lambda result, target: result == target)
    
    for candidate in candidates:
        try:
            result = fn(candidate)
            if match_fn(result, goal):
                return candidate
        except Exception:
            continue
    
    return None


# =============================================================================
# Morphism 演算子 — 構造的変換 (射層)
# =============================================================================
# トランスパイラ (_visit_Morphism) が生成するコードが呼び出す関数群。
# 全関数が (source, target) -> result の統一シグネチャ。
# operators.md §2 の意味論に基づく操作的セマンティクス。

def morphism_forward(source: Any, target: Any) -> Any:
    """順射 (>>) — 構造的変換。source を target の構造に変換する

    CCL: A >> B
    圏論: 射 f: A → B (pushforward)
    FEP: 信念伝播 (belief propagation)

    操作:
    - callable(target): target(source) — target が変換関数
    - dict × dict: source を target のキーでフィルタし射影
    - list × list: source の各要素を target の構造に合わせる
    - その他: (source, target) タプルを返す
    """
    # target が callable なら変換関数として適用
    if callable(target):
        return target(source)

    # 辞書 → 辞書: target のキー構造に source を射影
    if isinstance(source, dict) and isinstance(target, dict):
        result = {}
        for key in target:
            if key in source:
                result[key] = source[key]
            else:
                result[key] = target[key]  # target のデフォルト値を保持
        return result

    # リスト → リスト: source を target の長さに合わせる
    if isinstance(source, list) and isinstance(target, list):
        target_len = len(target)
        if len(source) >= target_len:
            return source[:target_len]
        return source + [None] * (target_len - len(source))

    # フォールバック: 変換ペア
    return {"source": source, "target": target, "direction": "forward"}


def morphism_reverse(source: Any, target: Any) -> Any:
    """逆射 (<<) — ゴールから逆算。target を得るために source に何が必要か

    CCL: A << B
    圏論: 射 f*: B → A (pullback)
    FEP: posterior からの逆推論

    操作:
    - callable(source): source(target) — source が逆変換関数
    - dict × dict: target を source のキーでフィルタ (逆方向の射影)
    - その他: 逆算ペアを返す

    Note: backward() は dual を使うパイプライン逆射。こちらは Morphism ノードの直接実行用。
    """
    # source が callable なら逆変換関数として適用
    if callable(source):
        return source(target)

    # 辞書 → 辞書: source のキー構造で target をフィルタ (forward の逆)
    if isinstance(source, dict) and isinstance(target, dict):
        result = {}
        for key in source:
            if key in target:
                result[key] = target[key]
            else:
                result[key] = source[key]  # source のデフォルト値
        return result

    # フォールバック
    return {"source": source, "target": target, "direction": "reverse"}


def morphism_lax(source: Any, target: Any) -> Any:
    """射的融合 (>*) — source が target の視点で変容する

    CCL: A >* B
    圏論: Lax Actegory ⊳ (forward channel + 融合)
    FEP: 予測 (forward) × 精度加重融合

    操作:
    - dict × dict: source を target の精度で加重マージ (source 優先、target で変容)
    - callable(target): merge(source, target(source)) — target の変換で source を変容
    - 数値 × 数値: source × target (射的な積)
    """
    # dict × dict: source に target の視点を融合 (source 優先)
    if isinstance(source, dict) and isinstance(target, dict):
        result = dict(source)
        for key, val in target.items():
            if key in result:
                # 両方に存在するキー → 値を融合 (source 優先で target の影響を受ける)
                src_val = result[key]
                if isinstance(src_val, (int, float)) and isinstance(val, (int, float)):
                    result[key] = src_val * 0.7 + val * 0.3  # source 優先
                elif isinstance(src_val, str) and isinstance(val, str):
                    result[key] = f"{src_val} [via {val}]"
                # 型不一致は source 値を保持
            else:
                result[key] = val  # target のみのキーを追加
        return result

    # callable(target): target の変換で source を変容
    if callable(target):
        transformed = target(source)
        return merge(source, transformed) if isinstance(source, dict) and isinstance(transformed, dict) else transformed

    # 数値 × 数値: 射的な積
    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        return source * target

    return {"source": source, "target": target, "direction": "lax"}


def morphism_oplax(source: Any, target: Any) -> Any:
    """逆射融合 (<*) — target の視点を source に吸収して変容 (>* の双対)

    CCL: A <* B
    圏論: Oplax functor (backward channel + 融合)
    FEP: 推論更新 (backward) × 精度加重融合

    操作:
    - dict × dict: target の構造を source に吸収 (target 優先、source で受容)
    - callable(source): source(target) の結果と target をマージ
    - 数値 × 数値: target × source (逆方向の射的積)

    >* との違い: >* は source が能動的に投射、<* は source が受動的に吸収。
    """
    # dict × dict: target の視点を source に吸収 (target 優先 — >* と逆)
    if isinstance(source, dict) and isinstance(target, dict):
        result = dict(source)
        for key, val in target.items():
            if key in result:
                src_val = result[key]
                if isinstance(src_val, (int, float)) and isinstance(val, (int, float)):
                    result[key] = src_val * 0.3 + val * 0.7  # target 優先 (>* の逆)
                elif isinstance(src_val, str) and isinstance(val, str):
                    result[key] = f"{val} [absorbed by {src_val}]"
            else:
                result[key] = val
        return result

    # callable(source): source が target を処理
    if callable(source):
        absorbed = source(target)
        return merge(target, absorbed) if isinstance(target, dict) and isinstance(absorbed, dict) else absorbed

    # 数値 × 数値
    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        return target * source

    return {"source": source, "target": target, "direction": "oplax"}


def morphism_directed_fuse(source: Any, target: Any) -> Any:
    """方向付き融合 (*>) — source と target を融合し、結果を target 方向に投射

    CCL: A *> B
    圏論: colimit(A, B) → C (融合) + 射 (方向)
    FEP: posterior → goal への方向付け

    操作:
    - dict × dict: まず merge(source, target) で融合 → target のキーでフィルタ
    - callable(target): merge の結果を target に通す
    - 数値 × 数値: 加重平均 → target 方向にスケール

    &> との違い: &> はデータを通過させる (同一性保存)。
    *> はデータを融合してから流す (同一性破壊)。
    """
    # dict × dict: 融合 → target 方向に射影
    if isinstance(source, dict) and isinstance(target, dict):
        # 融合 (merge)
        fused = dict(source)
        fused.update(target)
        # target のキーでフィルタ (方向付け)
        directed = {key: fused[key] for key in target if key in fused}
        return directed

    # callable(target): 融合結果を target 関数に通す
    if callable(target):
        if isinstance(source, dict):
            return target(source)
        return target(source)

    # 数値 × 数値: 融合 (平均) して target 方向にスケール
    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        fused = (source + target) / 2
        # target 方向 = target の符号に合わせる
        if target != 0:
            return fused * (abs(target) / target)
        return fused

    return {"source": source, "target": target, "direction": "directed_fuse"}


def morphism_pushforward(source: Any, target: Any) -> Any:
    """射的展開 (>%) — source を target の全次元にテンソル展開

    CCL: A >% B
    圏論: Pushforward tensor (方向付き外積)
    FEP: 予測分布の全次元展開

    操作:
    - dict × dict: source の各値 × target の各キー (方向付き product)
    - list × list: source の各要素を target の各要素と組み合わせる
    - 数値 × 数値: source × target (スカラー積)

    % との違い: % は無方向 (対称的展開)。>% は source → target 方向 (非対称)。
    source が target の空間に展開する。
    """
    # dict × dict: 方向付きテンソル展開
    if isinstance(source, dict) and isinstance(target, dict):
        result = {}
        for t_key in target:
            result[t_key] = {}
            for s_key, s_val in source.items():
                result[t_key][s_key] = (s_val, target[t_key])
        return result

    # list × list: 方向付き直積 (source の各要素を target の全要素に展開)
    if isinstance(source, (list, tuple)) and isinstance(target, (list, tuple)):
        result = []
        for s_item in source:
            row = [(s_item, t_item) for t_item in target]
            result.append(row)
        return result

    # 数値 × 数値: スカラー積 (方向付き)
    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        return source * target

    return {"source": source, "target": target, "direction": "pushforward"}


# =============================================================================
# ユーティリティ
# =============================================================================

def detail_level(base_level: int, modifier: str) -> int:
    """CCL 修飾子から detail_level を計算
    
    + = 3 (深化/L3), 無印 = 2 (標準/L2), - = 1 (縮約/L1)
    """
    levels = {"+": 3, "": 2, "-": 1, "^": 4, "!": 5}
    return levels.get(modifier, base_level)


# =============================================================================
# エクスポート
# =============================================================================

__all__ = [
    "merge", "product",
    "oscillate", "converge", "diverge",
    "pipe", "parallel", "backward",
    "validate", "cycle", "memo",
    "detail_level",
    # 双対生成
    "dual", "dual_of", "register_dual", "invert_pipeline",
    "with_dual", "DualNotFoundError", "OPERATOR_DUALS",
    # 随伴演算子 (v7.6)
    "right_adjoint", "left_adjoint", "AdjointNotFoundError",
    # Morphism 演算子 (射層)
    "morphism_forward", "morphism_reverse",
    "morphism_lax", "morphism_oplax",
    "morphism_directed_fuse", "morphism_pushforward",
]
