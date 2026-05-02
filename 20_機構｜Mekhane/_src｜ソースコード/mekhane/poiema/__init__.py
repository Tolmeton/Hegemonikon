# PROOF: [L2/インフラ] <- mekhane/poiema/__init__.py O4→創造機能が必要
# Hegemonikón poiēma (ποίημα) Layer
# Products built using Hegemonikón design principles
"""
Poiema — 構造化出力の生成エンジン

統合 facade: flow/ の全モジュールを re-export し、
パッケージレベルの便利関数 (generate, mask_pii) を提供する。

Usage::

    from mekhane.poiema import generate, mask_pii, MetronResolver

    # テキスト処理パイプライン
    result = generate("入力テキスト", metron_level=60)

    # PII マスキング
    masked, mapping = mask_pii("氏名: 田中太郎")
"""
# --- Lazy imports to avoid loading torch/sentence-transformers at import time ---
# flow/ は sentence-transformers → torch を引き込み、notepc で ~60s かかる
# アクセス時まで遅延させることで、テスト実行や他モジュール利用時に影響しない

_FLOW_EXPORTS = {
    "MetronResolver",
    "EpocheShield",
    "EpocheScanner",
    "EnergeiaCoreResolver",
    "DoxaCache",
    "NoesisClient",
}

_flow_module = None

def _load_flow():
    global _flow_module
    if _flow_module is None:
        from . import flow as _fm
        _flow_module = _fm
    return _flow_module

def __getattr__(name):
    if name in _FLOW_EXPORTS:
        mod = _load_flow()
        return getattr(mod, name)
    raise AttributeError(f"module 'mekhane.poiema' has no attribute {name!r}")

__all__ = [
    # flow/ re-exports (lazy loaded)
    "MetronResolver",
    "EpocheShield",
    "EpocheScanner",
    "EnergeiaCoreResolver",
    "DoxaCache",
    "NoesisClient",
    # convenience functions
    "generate",
    "mask_pii",
    "generate_incremental",
]


# PURPOSE: テキスト処理パイプラインの統合エントリポイント
def generate(
    text: str,
    metron_level: int = 60,
    privacy_mode: bool = True,
    settings: dict | None = None,
) -> dict:
    """
    テキスト処理パイプラインの統合エントリポイント。

    EnergeiaCoreResolver のラッパーとして、
    Metron (尺度) → Epochē (PII保護) → Noēsis (AI生成) → Epochē (復元)
    の全処理を同期的に実行する。

    Args:
        text: 入力テキスト
        metron_level: 処理レベル (0-100)。
            0=LIGHT, 30=MEDIUM, 60=RICH, 100=DEEP
        privacy_mode: PII マスキングの有効化 (default: True)
        settings: カスタム設定辞書 (optional)

    Returns:
        dict: {"result": str, "metron_level": int, "model_used": str, ...}
              失敗時: {"error": str, "message": str}
    """
    cfg = settings or {}
    cfg.setdefault("PRIVACY_MODE", privacy_mode)

    flow = _load_flow()
    core = flow.EnergeiaCoreResolver(settings=cfg)
    return core.process_sync(text, metron_level=metron_level)


# PURPOSE: PII マスキングの convenience wrapper
def mask_pii(text: str) -> tuple[str, dict[str, str]]:
    """
    PII マスキングの convenience wrapper。

    EpocheShield を使用してテキスト内の個人情報を検出・マスクする。

    Args:
        text: マスク対象テキスト

    Returns:
        (masked_text, pii_mapping):
            masked_text: マスク後のテキスト
            pii_mapping: {placeholder: original_value} の辞書
    """
    flow = _load_flow()
    shield = flow.EpocheShield()
    return shield.mask(text)


# PURPOSE: セクション別漸進出力 (D3 馴化 — MiroFish B2.4 パターン)
def generate_incremental(
    sections: list[dict],
    output_dir: str | None = None,
    metron_level: int = 60,
    privacy_mode: bool = True,
    settings: dict | None = None,
) -> dict:
    """セクション別に生成結果をファイルに漸進保存する。
    
    長い生成物をセクション単位で処理し、各セクション完了時に
    ファイルに保存する。中断からの復帰時に完了セクションをスキップできる。
    
    Args:
        sections: セクション定義のリスト。各要素は
            {"id": str, "title": str, "prompt": str} の辞書。
        output_dir: 出力ディレクトリのパス (省略時は一時ディレクトリ)
        metron_level: 処理レベル (0-100)
        privacy_mode: PII マスキング有効化
        settings: カスタム設定辞書 (内部でコピーされるため、呼出元の dict は変更されない)
    
    Returns:
        dict: {
            "sections": [{
                "id": str, "title": str, "path": str,
                "success": bool, "skipped": bool
            }],
            "completed": int,
            "total": int,
            "output_dir": str,
        }
    
    Note:
        output_dir=None 時は一時ディレクトリを作成する。
        呼出元が不要時に shutil.rmtree(output_dir) で削除する責任を持つ。
    """
    import json as _json
    from pathlib import Path as _Path
    
    if output_dir is None:
        import tempfile
        output_dir = tempfile.mkdtemp(prefix="poiema_")
    
    out_path = _Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 進捗管理ファイル
    progress_file = out_path / "_progress.json"
    completed_ids: set[str] = set()
    if progress_file.exists():
        try:
            data = _json.loads(progress_file.read_text(encoding="utf-8"))
            completed_ids = set(data.get("completed_ids", []))
        except Exception:  # noqa: BLE001
            pass
    
    results: list[dict] = []
    
    for idx, section in enumerate(sections):
        # idx ベースで一意 ID 生成 (「id」キー未指定時のフォールバック)
        sec_id = section.get("id", f"section_{idx}")
        # E2: パストラバーサル防御 — sec_id にパス区切り文字が含まれる場合を遮断
        sec_id = sec_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        title = section.get("title", sec_id)
        prompt = section.get("prompt", "")
        
        # F4: 空プロンプトは LLM 呼出を回避
        if not prompt or not prompt.strip():
            results.append({
                "id": sec_id, "title": title,
                "path": "", "success": False, "skipped": False,
                "error": "空のプロンプト",
            })
            continue
        
        # スキップ: 既に完了
        sec_path = out_path / f"{sec_id}.md"
        if sec_id in completed_ids and sec_path.exists():
            results.append({
                "id": sec_id, "title": title,
                "path": str(sec_path), "success": True, "skipped": True,
            })
            continue
        
        # 生成 (F7: settings のコピーを渡して呼出元 dict の副作用を遮断)
        try:
            result = generate(
                prompt, metron_level=metron_level,
                privacy_mode=privacy_mode,
                settings=dict(settings) if settings else None,
            )
            content = result.get("result", "")
            success = "error" not in result
        except Exception as e:  # noqa: BLE001
            content = f"生成エラー: {e}"
            success = False
        
        # F2: 成功時のみファイル保存 (失敗時のゴミファイル防止)
        if success:
            sec_path.write_text(
                f"# {title}\n\n{content}\n",
                encoding="utf-8",
            )
            # F3: 成功時のみ進捗更新 (不要 I/O 排除)
            completed_ids.add(sec_id)
            progress_file.write_text(
                _json.dumps({"completed_ids": list(completed_ids)}, ensure_ascii=False),
                encoding="utf-8",
            )
        
        results.append({
            "id": sec_id, "title": title,
            "path": str(sec_path) if success else "",
            "success": success, "skipped": False,
        })
    
    return {
        "sections": results,
        "completed": sum(1 for r in results if r["success"]),
        "total": len(sections),
        "output_dir": str(out_path),
    }
