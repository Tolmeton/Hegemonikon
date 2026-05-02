# PROOF: [L1/機能] <- mekhane/ochema/account_router.py A0→マルチアカウント→パイプライン別アカウント分離
# PURPOSE: パイプライン（用途）別にアカウントを割り当て、quota 競合を防ぐ
"""Account Router — Pipeline-based account allocation.

Maps pipelines (use cases) to specific TokenVault accounts,
preventing quota contention between different subsystems.

Usage:
    from mekhane.ochema.account_router import get_account_for

    account = get_account_for("periskope")  # → "rairaixoxoxo" or "hraiki"
    client = CortexClient(account=account)
"""

from __future__ import annotations
import itertools

# Pipeline → Account mapping
# Each pipeline gets dedicated accounts to prevent quota contention
PIPELINE_ACCOUNTS: dict[str, list[str]] = {
    "ide":       ["default"],                        # Antigravity IDE fixed
    "mcp":       ["movement", "Tolmeton"],          # MCP batch (round-robin)
    "hermeneus": ["movement", "Tolmeton"],          # L3 phased execution (round-robin)
    "periskope": ["movement", "Tolmeton", "rairaixoxoxo", "hraiki"],           # Parallel search
    "chat":      ["movement", "Tolmeton"],           # Chat conversations
    "cursor":    ["Tolmeton", "movement", "makaron", "rairaixoxoxo", "hraiki", "nous"],  # Cursor OpenAI bridge (6acct)
    "claude":    ["rairaixoxoxo"],                     # DEPRECATED (v9.1): REST偽陽性。LS経由使用
    "batch":     ["movement", "Tolmeton", "rairaixoxoxo", "hraiki"],  # Batch processing
    "reserve":   ["nous"],                             # Reserve / independent
}

# Round-robin iterators per pipeline
_iterators: dict[str, itertools.cycle] = {}


# PURPOSE: [L2-auto] get_account_for の関数定義
def get_account_for(pipeline: str) -> str:
    """Get the next account for a given pipeline via round-robin.

    Args:
        pipeline: Pipeline name (e.g. "mcp", "periskope", "ide")

    Returns:
        Account name from TokenVault

    Examples:
        >>> get_account_for("ide")
        'default'
        >>> get_account_for("periskope")  # alternates between rairaixoxoxo and hraiki
        'rairaixoxoxo'
    """
    accounts = PIPELINE_ACCOUNTS.get(pipeline)
    if not accounts:
        # Unknown pipeline: use auto (all accounts)
        return "auto"

    if len(accounts) == 1:
        return accounts[0]

    # Round-robin within pipeline
    if pipeline not in _iterators:
        _iterators[pipeline] = itertools.cycle(accounts)
    return next(_iterators[pipeline])


# PURPOSE: [L2-auto] get_pipeline_map の関数定義
def get_pipeline_map() -> dict[str, list[str]]:
    """Get the full pipeline-to-accounts mapping (for dashboard display)."""
    return dict(PIPELINE_ACCOUNTS)


# PURPOSE: [L2-auto] reset_iterators の関数定義
def reset_iterators() -> None:
    """Reset all round-robin iterators (for testing)."""
    _iterators.clear()
