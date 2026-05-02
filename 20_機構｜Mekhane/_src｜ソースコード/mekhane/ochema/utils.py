from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→Ochema Utilities
# PURPOSE: Ochema モジュール内で共通利用されるユーティリティ関数群

def fuzzy_suggest(name: str, candidates: list[str], max_distance: int = 2) -> str | None:
    """Return closest candidate within Levenshtein distance, or None.

    Uses a simple DP approach — no external deps. O(n*m) per candidate.
    """
    def _lev(a: str, b: str) -> int:
        if len(a) < len(b):
            a, b = b, a
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (0 if ca == cb else 1)))
            prev = curr
        return prev[-1]

    best, best_d = None, max_distance + 1
    for c in candidates:
        d = _lev(name, c)
        if d < best_d:
            best, best_d = c, d
    return best if best_d <= max_distance else None
