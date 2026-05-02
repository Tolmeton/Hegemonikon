# F2 セッション自動分類 — Fisher 情報行列による軸の演繹的導出

> **確信度**: [仮説] 45%。理論的枠組みは既存体系と整合するが、実験未実施。
> **由来**: 2026-03-14 F2 設計セッション (AMBITION.md F2 要件)
> **依存**: linkage_hyphe.md §7, axiom_hierarchy.md §Euporía 感度理論, Possati PDE PoC

---

## §1. 核心思想

> 「意味空間に溶かした上で結晶化させて、場における相対的な座標軸を演繹的に求めたい」
> — Creator, 2026-03-14

FEP が VFE 汎関数の数学的構造から 7 座標を固有分解で導出したように (axiom_hierarchy.md §Euporía 感度理論)、
F2 は **全セッションの embedding 場の情報幾何から分類軸を演繹的に導出** する。

### FEP → 6座標 との構造的同型

| FEP 体系 | F2 分類 |
|:---------|:--------|
| VFE 汎関数 F[q] | セッション embedding 場 |
| Fisher 情報行列 G_ij = E[∂_i log p · ∂_j log p] | 場の情報幾何的構造 |
| 固有ベクトル = 7座標 (Flow, Value, ...) | 固有ベクトル = 分類軸 (自動発見) |
| 固有値 λ = Euporía 感度 | 固有値 λ = 軸の重要度 |
| d 値 = 仮定の数 = 1/λ (sloppy) | 断崖 gap = 軸数 k の自然決定 |
| Helmholtz Γ⊣Q | 場⊣結晶 (linkage_hyphe.md §7) |

**意義**: F2 が成功すれば、FEP → 6座標の演繹構造が「認知理論の構成」だけでなく
「情報空間の自動構造発見」にも普遍的に適用できることを実証する。

---

## §2. アルゴリズム — 3段階パイプライン

### Stage 1: 溶解 (Dissolve) — 既存

```
全セッション text → HypheField.dissolve()
→ NucleatorChunker でチャンク化
→ Gemini embedding (3072次元)
→ LanceDB (GnosisIndex) に格納
```

📖 既存実装: `hyphe_field.py`, `hyphe_pipeline.py`

### Stage 2: 情報幾何構造の解析 — **NEW**

```python
# PURPOSE: embedding 場の Fisher 情報行列を構築し固有分解

def extract_field_axes(embeddings: np.ndarray, k: int = 10) -> FieldAxes:
    """場から分類軸を演繹的に導出する。

    1. 3072次元 embedding を直接使用 (PCA なし — 情報損失を回避)
    2. KSG estimator で条件付き相互情報量 → Fisher 情報行列の近似
    3. 固有分解 → 固有ベクトル (軸) + 固有値 (重要度)
    4. Sloppy spectrum の gap 検出 → 軸数 k の自然決定

    Note: 3072次元での直接計算。Gemini embedding 料金は
    無料枠 + クレジットでカバー。情報損失を避けるため PCA は使用しない。
    """

    # Step 1: Fisher 情報行列の構築
    # Possati (2025) の MB density approach:
    #   G_ij ≈ E[∂_i ρ_MB · ∂_j ρ_MB]
    # ρ_MB = 1 - I(I;E|B) / (I(I;E) + ε)
    # 3072次元で直接計算 (ANN で近傍探索を高速化)
    G = compute_fisher_matrix(embeddings, k=k)

    # Step 2: 固有分解
    # 3072×3072 行列の完全固有分解は重いため、
    # 上位 k_max 個のみ計算 (scipy.sparse.linalg.eigsh)
    from scipy.sparse.linalg import eigsh
    k_max = min(50, embeddings.shape[0] - 1)  # 最大50軸
    eigenvalues, eigenvectors = eigsh(G, k=k_max, which='LM')
    # 降順にソート
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Step 3: Sloppy spectrum gap 検出
    # log(λ_i) - log(λ_{i+1}) の最大 gap で k を決定
    log_λ = np.log10(eigenvalues + 1e-10)
    gaps = np.diff(log_λ)
    k_axes = np.argmax(np.abs(gaps)) + 1  # gap の直前までが有意な軸

    return FieldAxes(
        eigenvectors=eigenvectors[:, :k_axes],
        eigenvalues=eigenvalues[:k_axes],
        k=k_axes,
    )
```

### Fisher 情報行列の構築

```python
def compute_fisher_matrix(X: np.ndarray, k: int = 10) -> np.ndarray:
    """KSG k-NN を使い Fisher 情報行列を近似する。

    Possati (2025): ρ_MB(x) = 1 - I(I;E|B) / (I(I;E) + ε)

    Fisher 行列の (i,j) 成分:
      G_ij = Σ_x (∂ρ/∂x_i)(∂ρ/∂x_j) · w(x)

    ここで ∂ρ/∂x_i は ρ_MB のi方向勾配 (近傍微分で近似)。
    """
    n, d = X.shape
    tree = cKDTree(X)
    G = np.zeros((d, d))

    for i in range(n):
        dists, indices = tree.query(X[i], k=k+1)
        neighbors = indices[1:]

        # ρ_MB の勾配を近傍微分で近似
        grad_rho = np.zeros(d)
        rho_i = compute_rho_point(X, i, tree, k)

        for j_idx in neighbors:
            rho_j = compute_rho_point(X, j_idx, tree, k)
            delta = X[j_idx] - X[i]
            dist = np.linalg.norm(delta) + 1e-8
            grad_rho += (rho_j - rho_i) * delta / (dist ** 2)

        grad_rho /= k

        # Fisher 行列への寄与: 外積
        G += np.outer(grad_rho, grad_rho)

    G /= n
    return G
```

### Stage 3: 分類 + タグ演繹 — **NEW**

```python
def classify_session(
    session_chunks: list[dict],
    field_axes: FieldAxes,
) -> ClassificationResult:
    """セッションを場の固有軸に射影して分類する。

    1. セッション centroid を計算
    2. 固有軸空間に射影 → k 次元座標
    3. 座標空間でクラスタリング (HDBSCAN)
    4. クラスタ → タグの演繹的導出
    """
    embeddings = np.array([c["embedding"] for c in session_chunks])
    centroid = embeddings.mean(axis=0)  # セッション代表ベクトル

    # 固有軸への直接射影 (3072次元 → k次元)
    coords = centroid @ field_axes.eigenvectors  # k 次元座標

    return ClassificationResult(
        coords=coords.flatten(),
        eigenvalues=field_axes.eigenvalues,
        k=field_axes.k,
    )
```

---

## §3. クラスタリング — 動的 PJ 発見

### 冷起動 (Phase 1: データ < 50 セッション)

- Boulēsis 12 PJ の既存ドキュメントを dissolve → PJ centroid を seed
- 新セッションは最近傍 PJ centroid に割り当て
- 距離閾値を超えたら「未分類クラスタ」に → 候補 PJ として蓄積
- **Nucleator の prior** として機能 (linkage_hyphe.md §8)

### 定常状態 (Phase 2: データ >= 50 セッション)

- 定期的に (毎週 or 50 セッション蓄積ごとに) Fisher 固有分解を再実行
- HDBSCAN (密度ベース、クラスタ数を自動決定) で動的クラスタリング
- クラスタの centroid と既存 PJ seed の cosine 類似度でラベル付与:
  - 類似度 > 0.7 → 既存 PJ 名を継承
  - 類似度 < 0.7 → 新 PJ として Creator に提案
- **Sloppy spectrum の gap が変化** → 軸構造の進化を検出可能

### タグの演繹的導出

タグは座標値から **決定論的に** 導出される:

```
座標値 = [c₁, c₂, ..., c_k]  (k 個の固有軸上の値)
固有値 = [λ₁, λ₂, ..., λ_k]  (各軸の重要度)

タグ生成規則:
  1. 最近傍クラスタのラベル → "PJ:{name}"
  2. 各軸 i で |c_i| > 1σ の方向 → "Axis{i}:{±}"
  3. 軸のラベル自体が場のデータから事後的に命名される
     (最高/最低のセッションの内容を LLM が1語で要約)
```

**定型性**: タグの文法は固定 (`PJ:`, `Axis:`)。タグの語彙は座標系から決定。
**自由性**: 軸の数・方向・ラベルは場のデータによって動的に変化。
**演繹性**: 座標値→タグの変換は決定論的。LLM は軸ラベルの命名にのみ使用。

---

## §4. FEP → 6座標 の普遍性テスト

F2 は **Euporía 感度理論の実証実験** を兼ねる。

### 仮説

> F2 の Fisher 固有分解で発見される軸は、HGK の 7 座標と相関する。
> 特に sloppy spectrum の層構造 (d=0,1,2,3) が embedding 場にも現れる。

### 検証方法

1. **固有値の sloppy spectrum**: log₁₀(λ) が均等分布するか
2. **固有ベクトルと HGK 座標の内積**: 上位固有ベクトルが HGK 座標の特定の意味方向と整列するか
3. **層構造の再現**: d=0 (最 stiff), d=1 (中), d=2-3 (sloppy) が現れるか
4. **予測の検証**: d が小さい軸の分類精度 > d が大きい軸の分類精度

### 期待される結果

| シナリオ | 固有スペクトル | 意味 |
|:---------|:--------------|:-----|
| **理想** | 7座標と高相関 + sloppy 層構造 | FEP 座標の普遍性を実証 |
| **部分的** | 一部座標と相関 + 追加軸を発見 | FEP 座標は部分的に普遍 + ドメイン固有軸の存在 |
| **独立** | 7座標と無相関 + 独自の sloppy 構造 | FEP 座標は理論固有。情報空間は別の自然基底を持つ |

**[仮説]** シナリオ「部分的」が最も確率が高い (45%)。
理由: embedding 空間は言語モデルの事前学習で構成されており、
FEP の認知座標とは異なるバイアスを持つ。しかし HGK セッション群は
FEP 的な認知活動の記録であるため、部分的な相関は期待できる。

---

## §5. 既存資産との統合

### 依存

| モジュール | 利用方法 |
|:-----------|:---------|
| `hyphe_field.py` | dissolve(), recall(), update_density() — 場への溶解 |
| `hyphe_pipeline.py` | auto_dissolve() — セッション進行中の自動溶解 |
| `chunker_nucleator.py` | NucleatorChunker — チャンク化 |
| `rom_distiller.py` | classify_content() — Depth 軸の supplementary input |
| `phantazein_store.py` | session_classifications テーブル — 分類結果の永続化 |
| `phantazein_mcp_server.py` | phantazein_classify ツール — MCP 経由のアクセス |
| `notes.ts` | Classify ボタン (L163) — UI |

### 新規モジュール

| ファイル | 目的 |
|:---------|:-----|
| `mekhane/symploke/field_classifier.py` | FieldClassifier 本体 — Fisher 固有分解 + 分類 |
| `mekhane/symploke/field_axes.py` | FieldAxes — 固有軸の計算・キャッシュ |
| `mekhane/anamnesis/fisher_field.py` | Fisher 情報行列の構築 (KSG estimator) |

### DB スキーマ

```sql
-- 分類結果
CREATE TABLE IF NOT EXISTS session_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    coords TEXT DEFAULT '[]',       -- JSON: k 次元座標値
    cluster_id INTEGER,             -- HDBSCAN クラスタ ID
    cluster_label TEXT DEFAULT '',  -- ラベル名 (PJ:xxx)
    tags TEXT DEFAULT '[]',         -- 演繹されたタグ (JSON 配列)
    centroid BLOB,                  -- セッション centroid (3072次元)
    classified_at TEXT NOT NULL,
    classifier_version TEXT DEFAULT 'v1'
);

-- 場の固有軸 (定期更新, 3072次元ベース)
CREATE TABLE IF NOT EXISTS field_axes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    k INTEGER NOT NULL,               -- 有効軸数
    eigenvalues TEXT NOT NULL,         -- JSON: λ 配列
    eigenvectors BLOB NOT NULL,        -- pickled numpy array (3072 × k)
    spectrum_gap REAL,                 -- 最大 gap の位置
    computed_at TEXT NOT NULL,
    total_sessions INTEGER,
    sloppy_ratio REAL                  -- log₁₀(λ_max/λ_min)
);
```

---

## §6. 実装順序

| Phase | 内容 | 期間 |
|:------|:-----|:-----|
| P1 | `fisher_field.py` — KSG estimator + Fisher 行列構築 | 2-3日 |
| P2 | `field_axes.py` — 固有分解 + sloppy gap 検出 | 1-2日 |
| P3 | `field_classifier.py` — 分類 + HDBSCAN + タグ演繹 | 2日 |
| P4 | Possati PDE PoC との統合テスト (既存実験活用) | 1日 |
| P5 | DB スキーマ + phantazein_store 拡張 | 1日 |
| P6 | MCP ツール + /bye 自動トリガー | 1日 |
| P7 | notes.ts UI 接続 | 1日 |
| **E1** | **FEP 普遍性テスト** — 固有ベクトル vs HGK 7座標の相関分析 | 1-2日 |

---

## §7. linkage_hyphe.md との対応

| linkage_hyphe.md | F2 分類 |
|:-----------------|:--------|
| §2 η の MB: 4認知操作 | 分類 = η_a (行為: セッションの座標を決定) |
| §3.3 ρ_MB 密度場 | Fisher 行列の ∂ρ/∂x で構築 |
| §3.4 τ 臨界密度 | HDBSCAN の min_cluster_size ≈ τ |
| §5 DP-1 〜 DP-6 | 6設計原則を分類アルゴリズムに反映 |
| §7 場⊣結晶原理 | 溶解→Fisher→固有軸→結晶 |
| §8 Nucleator | 冷起動の Boulēsis seed = prior |
| §8.4 多スケール Nucleator | τ 多スケールで入れ子 MB = 階層的クラスタ |

---

*F2 Auto Classification Design v3.0 — 2026-03-14*
