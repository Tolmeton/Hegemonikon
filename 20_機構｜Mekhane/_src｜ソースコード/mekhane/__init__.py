# PROOF: [L2/インフラ] <- mekhane/__init__.py A0→mekhane実装層が必要→__init__ が担う
"""Hegemonikón Mechanism Layer (Mēkhanē)"""

# Sub-layers — lazy loaded to avoid heavy dependency chains
# poiema.flow imports sentence-transformers/torch which takes ~60s
# Use: from mekhane import poiema  (triggers lazy load when accessed)
def __getattr__(name):
    if name == "poiema":
        from . import poiema as _poiema
        return _poiema
    raise AttributeError(f"module 'mekhane' has no attribute {name!r}")
