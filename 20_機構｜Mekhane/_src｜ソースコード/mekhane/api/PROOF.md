# PROOF.md — mekhane/api/

## 存在証明

- **Level**: L2/インフラ
- **Parent**: mekhane/
- **Axiom**: A0 → Hegemonikón の機能は外部から利用可能であるべき
- **Derivation**: A0 → 利用可能性 → REST API → FastAPI バックエンド

## PURPOSE

mekhane 配下の各モジュールを REST API として公開し、
Tauri v2 デスクトップアプリ (HGK App) および n8n (Sympatheia) から利用可能にする。

## REASON

「ツールは使われてこそ価値がある。見えないものは存在しないのと同じ」
（handoff_2026-02-08_1856 法則化 #1: 顔の法則）

## 構成

| ファイル | 役割 |
|:---|:---|
| `__init__.py` | パッケージ定義・定数 (`API_PREFIX = "/api"`) |
| `server.py` | FastAPI アプリ・CORS・27ルーター登録・uvicorn 起動 |

### routes/ — 27 ルーター (server.py `_register_routers()` に対応)

> 実際のURLパスは `API_PREFIX (/api)` + ルーター prefix で決まる。
> prefix なしのルーターは各エンドポイントにパスを直接定義。

#### 即時ロード (依存なし)

| ルート | prefix | 実 URL | server.py 登録 |
|:---|:---|:---|:---|
| `status.py` | `/status` | `/api/status/*` | L131 `prefix=API_PREFIX` |
| `fep.py` | `/fep` | `/api/fep/*` | L132 `prefix=API_PREFIX` |
| `postcheck.py` | `/postcheck` | `/api/postcheck/*` | L133 `prefix=API_PREFIX` |
| `dendron.py` | `/dendron` | `/api/dendron/*` | L134 `prefix=API_PREFIX` |
| `graph.py` | `/graph` | `/api/graph/*` | L135 `prefix=API_PREFIX` |

#### 遅延ロード (try/except — 依存あり)

| ルート | prefix | 実 URL | 依存 | server.py |
|:---|:---|:---|:---|:---|
| `gnosis.py` | `/gnosis` | `/api/gnosis/*` | FAISS index | L139 |
| `gnosis_narrator.py` | `/gnosis` | `/api/gnosis/*` | PKSEngine | L181 |
| `ccl.py` | *(なし)* | `/api/*` 直下 | Hermēneus | L147 |
| `sympatheia.py` | `/sympatheia` | `/api/sympatheia/*` | AttractorAdvisor | L155 |
| `cortex.py` | `/api/cortex` | `/api/cortex/*` | Gemini API | L166 (**prefix なし — 自前**) |
| `pks.py` | `/pks` | `/api/pks/*` | 埋込モデル | L173 |
| `link_graph.py` | `/link-graph` | `/api/link-graph/*` | FS IO | L189 |
| `sophia.py` | `/sophia` | `/api/sophia/*` | FS CRUD | L197 |
| `symploke.py` | `/symploke` | `/api/symploke/*` | ベクトル検索 | L205 |
| `synteleia.py` | `/synteleia` | `/api/synteleia/*` | — | L213 |
| `basanos.py` | `/basanos` | `/api/basanos/*` | SweepEngine | L221 |
| `timeline.py` | *(なし)* | `/api/*` 直下 | FS IO | L229 |
| `kalon.py` | *(なし)* | `/api/*` 直下 | FS IO | L237 |
| `gateway.py` | *(なし)* | `/api/*` 直下 | PolicyEnforcer | L245 |
| `hgk.py` | `/api/hgk` | `/api/hgk/*` | Gateway | L254 (**prefix なし — 自前**) |
| `digestor.py` | `/digestor` | `/api/digestor/*` | FS IO | L261 |
| `chat.py` | *(なし)* | `/api/*` 直下 | httpx SSE | L269 |
| `quota.py` | `/quota` | `/api/quota/*` | subprocess | L277 |
| `aristos.py` | `/aristos` | `/api/aristos/*` | FS IO | L285 |
| `sentinel.py` | `/sentinel` | `/api/sentinel/*` | FS IO | L293 |
| `epistemic.py` | `/epistemic` | `/api/epistemic/*` | YAML IO | L301 |
| `scheduler.py` | *(なし)* | `/api/*` 直下 | FS IO | L309 |
| `periskope.py` | `/periskope` | `/api/periskope/*` | async | L317 |
| `theorem.py` | *(なし)* | `/api/*` 直下 | FS IO | L325 |
| `wal.py` | *(なし)* | `/api/*` 直下 | FS IO | L333 |
| `devtools.py` | *(なし)* | `/api/*` 直下 | CortexClient | L341 |

### tests/

| ファイル | 役割 |
|:---|:---|
| `test_api.py` | TestClient テスト |

---

*更新: 2026-02-24 — server.py L123-345 `_register_routers()` と全ルートファイルの APIRouter 定義から検証*
