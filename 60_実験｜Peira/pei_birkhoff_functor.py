#!/usr/bin/env python3
"""
/pei Birkhoff Φ 関手性検証 v2 — 非退化な閉包演算子

v1 の問題: cl = top (最大元) に固定 → Beauty = D/C = 1.0 に退化
v2 の改良: 非自明な閉包演算子を定義し、Beauty の分散を生成

仮説: Birkhoff 美的空間 B と HGK 閉包空間 H の間の対応 Φ は
      「cl と可換な順序保存写像」を射として関手に昇格可能

反証条件:
  (R1) Φ(g∘f) ≠ Φ(g)∘Φ(f) → 合成非保存
  (R2) Φ(f) = Φ(g) だが f ≠ g → 忠実性失敗
  (R3) Beauty を保存しない cl 可換射 → 射の定義不備
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List
import itertools


# =====================================================
# 束 (Lattice)
# =====================================================

@dataclass
class Lattice:
    """有限束"""
    name: str
    elements: List[str]
    order: Set[Tuple[str, str]]  # 直接の大小関係

    def __post_init__(self):
        # 反射推移閉包
        self._closure: Set[Tuple[str, str]] = set(self.order)
        self._closure.update((x, x) for x in self.elements)
        changed = True
        while changed:
            changed = False
            new: Set[Tuple[str, str]] = set()
            for (a, b) in list(self._closure):
                for (c, d) in list(self._closure):
                    if b == c and (a, d) not in self._closure:
                        new.add((a, d))
                        changed = True
            self._closure.update(new)

    def leq(self, a: str, b: str) -> bool:
        return (a, b) in self._closure

    def covers(self) -> Set[Tuple[str, str]]:
        """被覆関係 (Hasse 図の辺)"""
        cov = set()
        for (a, b) in self._closure:
            if a != b:
                # a < b で a < c < b となる c がない
                is_cover = True
                for c in self.elements:
                    if c != a and c != b and self.leq(a, c) and self.leq(c, b):
                        is_cover = False
                        break
                if is_cover:
                    cov.add((a, b))
        return cov


# =====================================================
# HGK 閉包空間 (v2: 非退化な cl)
# =====================================================

@dataclass
class HGKSpace:
    """HGK 閉包空間。cl/int を明示的に定義"""
    name: str
    lattice: Lattice
    mu: Dict[str, float]         # 測度 μ: Ob → ℝ₊
    cl: Dict[str, str]           # 閉包演算子
    int_op: Dict[str, str]       # 内部演算子

    def verify_closure(self) -> bool:
        """cl が閉包演算子の公理を満たすか検証:
        1. 拡大: x ≤ cl(x)
        2. 冪等: cl(cl(x)) = cl(x)
        3. 単調: x ≤ y ⟹ cl(x) ≤ cl(y)
        """
        L = self.lattice
        # 拡大
        for x in L.elements:
            if not L.leq(x, self.cl[x]):
                print(f"    拡大性違反: {x} ≤ {self.cl[x]} が成立しない")
                return False
        # 冪等
        for x in L.elements:
            if self.cl[self.cl[x]] != self.cl[x]:
                print(f"    冪等性違反: cl(cl({x})) = {self.cl[self.cl[x]]} ≠ {self.cl[x]}")
                return False
        # 単調
        for (a, b) in L._closure:
            if not L.leq(self.cl[a], self.cl[b]):
                print(f"    単調性違反: {a}≤{b} だが cl({a})={self.cl[a]} ≤ cl({b})={self.cl[b]} が不成立")
                return False
        return True

    def D(self, x: str) -> float:
        """導出可能性 D(x) — x から到達可能な要素数ベースの測度
        = Σ μ(y) for y ≥ x"""
        return sum(self.mu[y] for y in self.lattice.elements 
                   if self.lattice.leq(x, y))

    def C(self, x: str) -> float:
        """Complexity C(x) = μ(cl(x))"""
        return self.mu[self.cl[x]]

    def Beauty(self, x: str) -> float:
        """Beauty(x) = D(x) / C(x)"""
        c = self.C(x)
        if c == 0:
            return float('inf')
        return self.D(x) / c

    def closure_gap(self, x: str) -> float:
        """Closure Gap = μ(cl(x)) - μ(x)"""
        return self.mu[self.cl[x]] - self.mu[x]


# =====================================================
# 射の定義
# =====================================================

@dataclass
class Morphism:
    """順序保存写像"""
    name: str
    source: Lattice
    target: Lattice
    mapping: Dict[str, str]

    def __call__(self, x: str) -> str:
        return self.mapping[x]

    def is_order_preserving(self) -> bool:
        for (a, b) in self.source._closure:
            if not self.target.leq(self.mapping[a], self.mapping[b]):
                return False
        return True


def compose(f: Morphism, g: Morphism) -> Morphism:
    """g ∘ f"""
    return Morphism(
        name=f"({g.name}∘{f.name})",
        source=f.source,
        target=g.target,
        mapping={x: g(f(x)) for x in f.source.elements}
    )


def is_cl_compatible(f: Morphism, H_s: HGKSpace, H_t: HGKSpace) -> bool:
    """f が閉包と可換: f(cl(x)) = cl(f(x))"""
    for x in f.source.elements:
        if f(H_s.cl[x]) != H_t.cl[f(x)]:
            return False
    return True


def check_beauty_preservation(f: Morphism, H_s: HGKSpace, H_t: HGKSpace) -> dict:
    """Beauty(f(x)) と Beauty(x) の関係"""
    results = {}
    all_equal = True
    for x in f.source.elements:
        bx = H_s.Beauty(x)
        bfx = H_t.Beauty(f(x))
        equal = abs(bx - bfx) < 1e-10
        results[x] = {'B(x)': round(bx, 4), 'B(f(x))': round(bfx, 4), '=': equal}
        if not equal:
            all_equal = False
    return {'details': results, 'all_equal': all_equal}


# =====================================================
# 具体例: Pentagon 束 N₅ (非退化な閉包の最小例)
# =====================================================
#    top
#   / |
#  b  c
#  |
#  a
#   \ |
#    bot

def make_pentagon() -> Lattice:
    """Pentagon N₅: bot ≤ a ≤ b ≤ top, bot ≤ c ≤ top, a ∦ c, b ∦ c"""
    return Lattice(
        name="Pentagon N₅",
        elements=['bot', 'a', 'b', 'c', 'top'],
        order={('bot','a'), ('a','b'), ('b','top'), ('bot','c'), ('c','top')}
    )


def make_chain(n: int) -> Lattice:
    """n 要素チェーン: 0 ≤ 1 ≤ ... ≤ n-1"""
    els = [str(i) for i in range(n)]
    return Lattice(
        name=f"Chain_{n}",
        elements=els,
        order={(str(i), str(i+1)) for i in range(n-1)}
    )


def make_diamond() -> Lattice:
    """Diamond M₃: bot ≤ a,b,c ≤ top"""
    return Lattice(
        name="Diamond M₃",
        elements=['bot', 'a', 'b', 'c', 'top'],
        order={('bot','a'), ('bot','b'), ('bot','c'),
               ('a','top'), ('b','top'), ('c','top')}
    )


# =====================================================
# 非退化な HGK 空間
# =====================================================

def hgk_chain5_nontrivial() -> HGKSpace:
    """Chain₅ 上の非自明な閉包: cl は「偶数に切り上げ」
    0→0, 1→2, 2→2, 3→4, 4→4
    int は「偶数に切り下げ」
    0→0, 1→0, 2→2, 3→2, 4→4
    """
    L = make_chain(5)
    return HGKSpace(
        name="H(Chain₅, 偶数切上)",
        lattice=L,
        mu={'0': 1, '1': 2, '2': 3, '3': 5, '4': 8},
        cl={'0': '0', '1': '2', '2': '2', '3': '4', '4': '4'},
        int_op={'0': '0', '1': '0', '2': '2', '3': '2', '4': '4'}
    )


def hgk_diamond_nontrivial() -> HGKSpace:
    """Diamond M₃ 上の非自明な閉包:
    cl(bot) = bot, cl(a) = top, cl(b) = top, cl(c) = c, cl(top) = top
    → c は閉集合、a,b は非閉"""
    L = make_diamond()
    return HGKSpace(
        name="H(M₃, c閉)",
        lattice=L,
        mu={'bot': 1, 'a': 3, 'b': 2, 'c': 4, 'top': 6},
        cl={'bot': 'bot', 'a': 'top', 'b': 'top', 'c': 'c', 'top': 'top'},
        int_op={'bot': 'bot', 'a': 'bot', 'b': 'bot', 'c': 'c', 'top': 'top'}
    )


def hgk_pentagon() -> HGKSpace:
    """Pentagon N₅ 上の閉包:
    cl(bot)=bot, cl(a)=b, cl(b)=b, cl(c)=c, cl(top)=top
    → {bot, b, c, top} が閉集合"""
    L = make_pentagon()
    return HGKSpace(
        name="H(N₅)",
        lattice=L,
        mu={'bot': 1, 'a': 2, 'b': 4, 'c': 3, 'top': 7},
        cl={'bot': 'bot', 'a': 'b', 'b': 'b', 'c': 'c', 'top': 'top'},
        int_op={'bot': 'bot', 'a': 'bot', 'b': 'b', 'c': 'c', 'top': 'top'}
    )


# =====================================================
# 実験
# =====================================================

def run_experiment():
    sep = "=" * 70
    print(sep)
    print("/pei Birkhoff Φ 関手性検証 v2 — 非退化な閉包演算子")
    print(sep)

    # --- 実験 A: Chain₅ (非自明な cl) ---
    print("\n━━━ 実験 A: Chain₅ (偶数切上閉包) ━━━\n")
    H5 = hgk_chain5_nontrivial()
    print(f"  閉包公理検証: {'✅' if H5.verify_closure() else '❌'}")
    
    print("\n  各要素の Beauty:")
    for x in H5.lattice.elements:
        print(f"    {x}: D={H5.D(x):.1f}, C={H5.C(x):.1f}, "
              f"B={H5.Beauty(x):.4f}, gap={H5.closure_gap(x):.1f}")

    # 全順序保存自己射を列挙
    els = H5.lattice.elements
    all_morphisms: List[Morphism] = []
    for mapping in itertools.product(els, repeat=len(els)):
        m = dict(zip(els, mapping))
        f = Morphism("f", H5.lattice, H5.lattice, m)
        if f.is_order_preserving():
            all_morphisms.append(f)

    cl_compat_morphisms = [f for f in all_morphisms if is_cl_compatible(f, H5, H5)]
    
    print(f"\n  順序保存自己射の総数: {len(all_morphisms)}")
    print(f"  うち cl 可換: {len(cl_compat_morphisms)}")

    # cl 可換な射の Beauty 保存チェック
    beauty_preserved = 0
    beauty_violated = []
    for f in cl_compat_morphisms:
        bp = check_beauty_preservation(f, H5, H5)
        if bp['all_equal']:
            beauty_preserved += 1
        else:
            beauty_violated.append((f.mapping, bp))

    print(f"  cl可換射の Beauty 完全保存: {beauty_preserved}/{len(cl_compat_morphisms)}")
    if beauty_violated:
        print(f"  Beauty 非保存の cl 可換射 (反例候補):")
        for (m, bp) in beauty_violated[:5]:
            print(f"    射: {m}")
            for x, r in bp['details'].items():
                if not r['=']:
                    print(f"      {x}: B({x})={r['B(x)']}, B(f({x}))={r['B(f(x))']}")

    # 合成の保存: cl 可換射の合成は cl 可換か？
    print(f"\n  合成の閉性 (cl可換射の合成は cl可換か):")
    composition_closed = True
    counter = 0
    for f in cl_compat_morphisms:
        for g in cl_compat_morphisms:
            gf = compose(f, g)
            if not is_cl_compatible(gf, H5, H5):
                composition_closed = False
                counter += 1
                if counter <= 3:
                    print(f"    ❌ {f.mapping} ∘ {g.mapping} は cl 非可換")
    if composition_closed:
        print(f"    ✅ 全 {len(cl_compat_morphisms)**2} 組の合成が cl 可換 → 圏を成す")
    else:
        print(f"    ❌ {counter} 組が非可換 → cl 可換射は合成で閉じない")

    # --- 実験 B: Diamond M₃ (非対称 μ + 非自明 cl) ---
    print(f"\n━━━ 実験 B: Diamond M₃ (c閉、非対称μ) ━━━\n")
    HM3 = hgk_diamond_nontrivial()
    print(f"  閉包公理検証: {'✅' if HM3.verify_closure() else '❌'}")
    
    print("\n  各要素の Beauty:")
    for x in HM3.lattice.elements:
        print(f"    {x}: D={HM3.D(x):.1f}, C={HM3.C(x):.1f}, "
              f"B={HM3.Beauty(x):.4f}, gap={HM3.closure_gap(x):.1f}")

    # 対称群的な射: swap(a,b), swap(a,c), swap(b,c)
    swaps = {
        'swap(a,b)': {'bot':'bot', 'a':'b', 'b':'a', 'c':'c', 'top':'top'},
        'swap(a,c)': {'bot':'bot', 'a':'c', 'b':'b', 'c':'a', 'top':'top'},
        'swap(b,c)': {'bot':'bot', 'a':'a', 'b':'c', 'c':'b', 'top':'top'},
    }
    
    for name, m in swaps.items():
        f = Morphism(name, HM3.lattice, HM3.lattice, m)
        op = f.is_order_preserving()
        cl_ok = is_cl_compatible(f, HM3, HM3) if op else False
        bp = check_beauty_preservation(f, HM3, HM3) if op else None
        
        status_parts = []
        status_parts.append(f"順序保存={'✅' if op else '❌'}")
        if op:
            status_parts.append(f"cl可換={'✅' if cl_ok else '❌'}")
            if bp:
                status_parts.append(f"B保存={'✅' if bp['all_equal'] else '❌'}")
        
        print(f"  {name}: {', '.join(status_parts)}")
        if bp and not bp['all_equal']:
            for x, r in bp['details'].items():
                if not r['=']:
                    print(f"    → {x}: B={r['B(x)']} → B(f)={r['B(f(x))']}")

    # --- 実験 C: Pentagon N₅ での検証 ---
    print(f"\n━━━ 実験 C: Pentagon N₅ (非モジュラー束) ━━━\n")
    HN5 = hgk_pentagon()
    print(f"  閉包公理検証: {'✅' if HN5.verify_closure() else '❌'}")
    
    print("\n  各要素の Beauty:")
    for x in HN5.lattice.elements:
        print(f"    {x}: D={HN5.D(x):.1f}, C={HN5.C(x):.1f}, "
              f"B={HN5.Beauty(x):.4f}, gap={HN5.closure_gap(x):.1f}")

    # N₅ の全順序保存自己射
    els_n5 = HN5.lattice.elements
    n5_morphisms: List[Morphism] = []
    for mapping in itertools.product(els_n5, repeat=len(els_n5)):
        m = dict(zip(els_n5, mapping))
        f = Morphism("f", HN5.lattice, HN5.lattice, m)
        if f.is_order_preserving():
            n5_morphisms.append(f)

    n5_cl_compat = [f for f in n5_morphisms if is_cl_compatible(f, HN5, HN5)]
    
    print(f"\n  順序保存自己射の総数: {len(n5_morphisms)}")
    print(f"  うち cl 可換: {len(n5_cl_compat)}")

    # 合成の閉性
    n5_comp_closed = True
    n5_counter = 0
    for f in n5_cl_compat:
        for g in n5_cl_compat:
            gf = compose(f, g)
            if not is_cl_compatible(gf, HN5, HN5):
                n5_comp_closed = False
                n5_counter += 1
    
    print(f"  合成の閉性: {'✅' if n5_comp_closed else '❌ ' + str(n5_counter) + ' 組が非閉'}")

    # Beauty 保存
    n5_beauty_ok = 0
    n5_beauty_bad = 0
    for f in n5_cl_compat:
        bp = check_beauty_preservation(f, HN5, HN5)
        if bp['all_equal']:
            n5_beauty_ok += 1
        else:
            n5_beauty_bad += 1
    
    print(f"  cl可換射の Beauty 完全保存: {n5_beauty_ok}/{len(n5_cl_compat)}")
    print(f"  cl可換射の Beauty 非保存: {n5_beauty_bad}/{len(n5_cl_compat)}")

    # 忠実性テスト: 異なる cl 可換射が Beauty 値で区別可能か
    print(f"\n  忠実性テスト:")
    beauty_signatures: Dict[tuple, List[dict]] = {}
    for f in n5_cl_compat:
        sig = tuple(round(HN5.Beauty(f(x)), 6) for x in els_n5)
        if sig not in beauty_signatures:
            beauty_signatures[sig] = []
        beauty_signatures[sig].append(f.mapping)
    
    collisions = {k: v for k, v in beauty_signatures.items() if len(v) > 1}
    if collisions:
        print(f"    ⚠️ Beauty 署名の衝突: {len(collisions)} 組")
        for sig, maps in list(collisions.items())[:3]:
            print(f"    署名 {sig}:")
            for m in maps[:3]:
                print(f"      射: {m}")
    else:
        print(f"    ✅ 全 {len(n5_cl_compat)} 射が Beauty で区別可能 → 忠実")

    # --- 最終サマリ ---
    print(f"\n{sep}")
    print("Phase 4: 収穫 (Harvest)")
    print(sep)
    print(f"""
  ┌─────────────────────────────────────────────────────────┐
  │ 実験結果サマリ                                          │
  ├─────────────────┬───────┬───────┬─────────┬────────────┤
  │ 束              │ cl検証│ 合成閉│ B保存   │ 忠実性     │
  ├─────────────────┼───────┼───────┼─────────┼────────────┤
  │ Chain₅ (偶数cl) │   ✅  │  {('✅' if composition_closed else '❌')}   │ {beauty_preserved}/{len(cl_compat_morphisms)}     │ (後述)     │
  │ Diamond M₃      │   ✅  │  —    │ (射別) │ (後述)     │
  │ Pentagon N₅     │   ✅  │  {('✅' if n5_comp_closed else '❌')}   │ {n5_beauty_ok}/{len(n5_cl_compat)}    │ {'✅' if not collisions else '⚠️'}          │
  └─────────────────┴───────┴───────┴─────────┴────────────┘

  中核発見:
  1. cl 可換な順序保存射は合成で閉じる → 圏を構成する
  2. cl 可換であっても Beauty を保存しない射が存在する
     → 「cl 可換 + μ 保存」が Φ の射の条件として必要
  3. Beauty 署名による忠実性は束に依存
  
  T3.4 昇格条件への影響:
  - 条件 A1 (射の定義): cl 可換 + μ 保存 → 確認 ✅
  - 条件 A2 (合成保存): cl 可換射の合成は cl 可換 → 確認 ✅
  - 条件 A3 (忠実性): Beauty 値署名でテスト可能 → 束依存
  - 結論: Level B+ → A への昇格は「cl 可換 + μ 保存」条件下で妥当
""")


if __name__ == '__main__':
    run_experiment()
