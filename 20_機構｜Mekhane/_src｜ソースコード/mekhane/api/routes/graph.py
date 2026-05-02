# PROOF: [L2/インフラ] <- mekhane/api/routes/graph.py
# PURPOSE: /api/graph/* — Hegemonikón 32実体グラフデータ
"""
Graph Routes — Trígōnon/Taxis データを JSON API で提供

GET /api/graph/nodes      — 24 動詞ノード
GET /api/graph/edges      — 21 X-series エッジ (15 binding rules + 6 identity)
GET /api/graph/full       — ノード + エッジ + メタデータ一括
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

# --- データ定義 ---

# PURPOSE: 6 Series (v4.1 では全族が Flow を持ち対等) の定義
SERIES = {
    "O": {"name": "Telos", "greek": "τέλος", "meaning": "目的", "type": "Flow",
           "tier": "Flow × Value", "color": "#00d4ff", "coordinates": ["Flow", "Value"]},
    "S": {"name": "Methodos", "greek": "μέθοδος", "meaning": "戦略", "type": "Flow",
           "tier": "Flow × Function", "color": "#10b981", "coordinates": ["Flow", "Function"]},
    "H": {"name": "Krisis", "greek": "κρίσις", "meaning": "コミットメント", "type": "Flow",
           "tier": "Flow × Precision", "color": "#ef4444", "coordinates": ["Flow", "Precision"]},
    "P": {"name": "Diástasis", "greek": "διάστασις", "meaning": "空間スケール", "type": "Flow",
           "tier": "Flow × Scale", "color": "#a855f7", "coordinates": ["Flow", "Scale"]},
    "K": {"name": "Orexis", "greek": "ὄρεξις", "meaning": "価値方向", "type": "Flow",
           "tier": "Flow × Valence", "color": "#f59e0b", "coordinates": ["Flow", "Valence"]},
    "A": {"name": "Chronos", "greek": "χρόνος", "meaning": "時間方向", "type": "Flow",
           "tier": "Flow × Temporality", "color": "#f97316", "coordinates": ["Flow", "Temporality"]},
}

# PURPOSE: 36 動詞 (Poiesis) — 6 Series × 6
THEOREMS: list[dict[str, Any]] = []
_THEOREM_NAMES = {
    # Telos 族
    "O1": ("Noēsis", "νόησις", "理解する"),
    "O2": ("Boulēsis", "βούλησις", "意志する"),
    "O3": ("Zētēsis", "ζήτησις", "探求する"),
    "O4": ("Energeia", "ἐνέργεια", "実行する"),
    "O5": ("Theōria", "θεωρία", "観照する"),
    "O6": ("Antilepsis", "ἀντίληψις", "検知する"),
    # Methodos 族
    "S1": ("Skepsis", "σκέψις", "発散する"),
    "S2": ("Synagōgē", "συναγωγή", "収束する"),
    "S3": ("Peira", "πεῖρα", "実験する"),
    "S4": ("Tekhnē", "τέχνη", "適用する"),
    "S5": ("Ereuna", "ἔρευνα", "探知する"),
    "S6": ("Anagnōsis", "ἀνάγνωσις", "参照する"),
    # Krisis 族
    "H1": ("Katalēpsis", "κατάληψις", "確定する"),
    "H2": ("Epochē", "ἐποχή", "留保する"),
    "H3": ("Proairesis", "προαίρεσις", "決断する"),
    "H4": ("Dokimasia", "δοκιμασία", "打診する"),
    "H5": ("Saphēneia", "σαφήνεια", "精読する"),
    "H6": ("Skiagraphia", "σκιαγραφία", "走査する"),
    # Diástasis 族
    "P1": ("Analysis", "ἀνάλυσις", "詳細分析する"),
    "P2": ("Synopsis", "σύνοψις", "俯瞰する"),
    "P3": ("Akribeia", "ἀκρίβεια", "精密操作する"),
    "P4": ("Architektonikē", "ἀρχιτεκτονική", "全体展開する"),
    "P5": ("Prosochē", "προσοχή", "注視する"),
    "P6": ("Perioptē", "περιωπή", "一覧する"),
    # Orexis 族
    "K1": ("Bebaiōsis", "βεβαίωσις", "肯定する"),
    "K2": ("Elenchos", "ἔλεγχος", "批判する"),
    "K3": ("Prokopē", "προκοπή", "推進する"),
    "K4": ("Diorthōsis", "διόρθωσις", "是正する"),
    "K5": ("Apodochē", "ἀποδοχή", "傾聴する"),
    "K6": ("Exetasis", "ἐξέτασις", "吟味する"),
    # Chronos 族
    "A1": ("Hypomnēsis", "ὑπόμνησις", "想起する"),
    "A2": ("Promētheia", "προμήθεια", "予見する"),
    "A3": ("Anatheōrēsis", "ἀναθεώρησις", "省みる"),
    "A4": ("Proparaskeuē", "προπαρασκευή", "仕掛ける"),
    "A5": ("Historiā", "ἱστορία", "回顧する"),
    "A6": ("Prognōsis", "πρόγνωσις", "予感する"),
}

# PURPOSE: 全要素の初期 3D 座標 (v4.1 — 6族等価の正六角形配置)
import math
_R = 6.0  # 半径
# 時計回りに 60度 ずつ配置 (0, -60, -120, -180, -240, -300)
_SERIES_POSITIONS = {
    "O": (0.0, _R, 0.0),                                                # トップ
    "S": (_R * math.cos(math.pi/6), _R * math.sin(math.pi/6), 0.0),     # 右上 (+30度)
    "H": (_R * math.cos(-math.pi/6), _R * math.sin(-math.pi/6), 0.0),   # 右下 (-30度)
    "P": (0.0, -_R, 0.0),                                               # ボトム (-90度)
    "K": (-_R * math.cos(-math.pi/6), _R * math.sin(-math.pi/6), 0.0),  # 左下 (-150度)
    "A": (-_R * math.cos(math.pi/6), _R * math.sin(math.pi/6), 0.0),    # 左上 (+150度)
}

# PURPOSE: 動詞ID → ワークフロースラッグの明示的マッピング (自動生成はUnicode・重複問題を起こす)
_WORKFLOW_SLUGS = {
    "O1": "/noe", "O2": "/bou", "O3": "/zet", "O4": "/ene", "O5": "/the", "O6": "/ant",
    "S1": "/ske", "S2": "/sag", "S3": "/pei", "S4": "/tek", "S5": "/ere", "S6": "/agn",
    "H1": "/kat", "H2": "/epo", "H3": "/pai", "H4": "/dok", "H5": "/sap", "H6": "/ski",
    "P1": "/lys", "P2": "/ops", "P3": "/akr", "P4": "/arc", "P5": "/prs", "P6": "/per",
    "K1": "/beb", "K2": "/ele", "K3": "/kop", "K4": "/dio", "K5": "/apo", "K6": "/exe",
    "A1": "/hyp", "A2": "/prm", "A3": "/ath", "A4": "/par", "A5": "/his", "A6": "/prg",
}

for series_id, series_info in SERIES.items():
    for i in range(1, 7):
        tid = f"{series_id}{i}"
        name, greek, meaning = _THEOREM_NAMES[tid]
        # 各動詞ノードは Series 中心からわずかにオフセット
        base_x, base_y, base_z = _SERIES_POSITIONS[series_id]
        offset_x = ((i - 1) % 2 - 0.5) * 1.0
        offset_y = ((i - 1) // 2 - 1.0) * 1.0
        THEOREMS.append({
            "id": tid,
            "series": series_id,
            "name": name,
            "greek": greek,
            "meaning": meaning,
            "workflow": _WORKFLOW_SLUGS[tid],
            "type": series_info["type"],
            "color": series_info["color"],
            "position": {"x": base_x + offset_x, "y": base_y + offset_y, "z": 0.0},
        })

# PURPOSE: X-series エッジ (v4.1: K₆ の 15結合規則 + 6中心点)
# フロントエンド描画用に、各族の「要素i」同士を結ぶ形 (4本×15ペア = 60エッジ) を生成する
_EDGE_DEFS = [
    # C(6,2) = 15 Pairs — (pair_id, src, tgt, naturality, meaning)
    ("X-OS", "O", "S", "structural", "Telos↔Methodos"),
    ("X-OH", "O", "H", "structural", "Telos↔Krisis"),
    ("X-OP", "O", "P", "structural", "Telos↔Diástasis"),
    ("X-OK", "O", "K", "experiential", "Telos↔Orexis"),
    ("X-OA", "O", "A", "reflective", "Telos↔Chronos"),
    ("X-SH", "S", "H", "structural", "Methodos↔Krisis"),
    ("X-SP", "S", "P", "structural", "Methodos↔Diástasis"),
    ("X-SK", "S", "K", "experiential", "Methodos↔Orexis"),
    ("X-SA", "S", "A", "reflective", "Methodos↔Chronos"),
    ("X-HP", "H", "P", "structural", "Krisis↔Diástasis"),
    ("X-HK", "H", "K", "experiential", "Krisis↔Orexis"),
    ("X-HA", "H", "A", "reflective", "Krisis↔Chronos"),
    ("X-PK", "P", "K", "experiential", "Diástasis↔Orexis"),
    ("X-PA", "P", "A", "reflective", "Diástasis↔Chronos"),
    ("X-KA", "K", "A", "reflective", "Orexis↔Chronos"),
]

EDGES: list[dict[str, Any]] = []
# 各結合規則について、対応する添字(1-6)同士を平行に結ぶ (6 × 15 = 90 エッジ)
for pair_id, src_s, tgt_s, nat, meaning in _EDGE_DEFS:
    for i in range(1, 7):
        EDGES.append({
            "id": f"{pair_id}-{i}",
            "pair": pair_id,
            "source": f"{src_s}{i}",
            "target": f"{tgt_s}{i}",
            "shared_coordinate": "Interaction",
            "naturality": nat,
            "meaning": meaning,
            "type": "bridge",
        })

# 36 恒等射 (各頂点内部の再帰的構造)
for series_id in SERIES:
    for i in range(1, 7):
        tid = f"{series_id}{i}"
        EDGES.append({
            "id": f"X-{series_id}{series_id}{i}",
            "pair": f"X-{series_id}{series_id}",
            "source": tid,
            "target": tid,
            "shared_coordinate": "identity",
            "naturality": "identity",
            "meaning": "恒等射",
            "type": "identity",
        })


# --- Pydantic Models ---

# PURPOSE: の統一的インターフェースを実現する
class GraphNode(BaseModel):
    id: str
    series: str
    name: str
    greek: str
    meaning: str
    workflow: str
    type: str = Field(description="Flow (v4.1: all tribes are Flow-based)")
    color: str
    position: dict[str, float]

# PURPOSE: の統一的インターフェースを実現する
class GraphEdge(BaseModel):
    id: str
    pair: str
    source: str
    target: str
    shared_coordinate: str
    naturality: str = Field(description="experiential, reflective, structural, or identity")
    meaning: str
    type: str = Field(description="anchor, bridge, or identity")

# PURPOSE: の統一的インターフェースを実現する
class GraphFullResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    meta: dict[str, Any]


# --- Router ---

router = APIRouter(prefix="/graph", tags=["graph"])


# PURPOSE: graph nodes を取得する
@router.get("/nodes", response_model=list[GraphNode])
async def get_graph_nodes() -> list[GraphNode]:
    """36 定理ノードを返す。"""
    return [GraphNode(**t) for t in THEOREMS]


# PURPOSE: graph edges を取得する
@router.get("/edges", response_model=list[GraphEdge])
async def get_graph_edges() -> list[GraphEdge]:
    """21 X-series エッジを返す (15 binding rules + 6 identity morphisms)。"""
    return [GraphEdge(**e) for e in EDGES]


# PURPOSE: graph full を取得する
@router.get("/full", response_model=GraphFullResponse)
async def get_graph_full() -> GraphFullResponse:
    """ノード + エッジ + メタデータを一括で返す。"""
    return GraphFullResponse(
        nodes=[GraphNode(**t) for t in THEOREMS],
        edges=[GraphEdge(**e) for e in EDGES],
        meta={
            "total_nodes": len(THEOREMS),
            "total_edges": len(EDGES),
            "series": SERIES,
            "structure": {
                "system": "48 Entities (v5.4)",
                "coordinates": 7,
                "poiesis_verbs": 36,
                "binding_rules": 15,
                "identity_morphisms": 6,
            },
            "topology": {
                "description": "6族は完全グラフ K₆ (正六角形) を形成し、Flow中心の等価な構造を持つ。",
                "vertices": {"O": "top", "S": "top-right", "H": "bottom-right", "P": "bottom", "K": "bottom-left", "A": "top-left"},
                "edges_between": "15 Pairs (K₆ complete graph)",
            },
            "naturality": {
                "experiential": "体感",
                "reflective": "反省",
                "structural": "構造",
            },
        },
    )
