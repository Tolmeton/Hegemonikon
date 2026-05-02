from __future__ import annotations

from pathlib import Path

import mekhane.paths as hgk_paths
from mekhane.symploke import phantazein_indexer
from mekhane.symploke.phantazein_store import PhantazeinStore, get_store, reset_store


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_full_sync_scans_recursive_handoffs_and_records_sync_state(
    tmp_path: Path,
    monkeypatch,
):
    reset_store()
    db_path = tmp_path / "state" / "phantazein.db"
    store = PhantazeinStore(db_path=db_path)

    brain_dir = tmp_path / "brain"
    handoff_dir = tmp_path / "handoff"
    rom_dir = tmp_path / "rom"
    brain_dir.mkdir(parents=True, exist_ok=True)
    rom_dir.mkdir(parents=True, exist_ok=True)

    _write(
        handoff_dir / "2026-04" / "handoff_2026-04-17_0900_alpha.md",
        "# Alpha\n\n*Session: 123e4567-e89b-12d3-a456-426614174000*",
    )
    _write(
        handoff_dir / "2026-04" / "handoff_2026-04-17_1000_beta.md",
        "# Beta\n\n*Session: 123e4567-e89b-12d3-a456-426614174001*",
    )
    _write(
        rom_dir / "rom_2026-04-17_pinakas.md",
        "Pinakas ROM summary",
    )

    monkeypatch.setattr(phantazein_indexer, "_get_brain_dir", lambda: brain_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_handoff_dir", lambda: handoff_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_rom_dir", lambda: rom_dir)

    result = phantazein_indexer.full_sync(store=store)

    assert result["handoffs"] == 2
    assert result["roms"] == 1
    assert store.get_config_value("last_full_sync_at") is not None
    assert store.get_config_value("source_counts_json")["handoffs"] == 2
    assert store.get_db_health()["status"] == "ok"
    store.close()


def test_rebuild_phantazein_db_archives_existing_db_and_updates_sync_state(
    tmp_path: Path,
    monkeypatch,
):
    reset_store()
    db_path = tmp_path / "state" / "phantazein.db"
    existing_store = get_store(db_path=db_path)
    existing_store.register_session(context="stale")

    brain_dir = tmp_path / "brain"
    handoff_dir = tmp_path / "handoff"
    rom_dir = tmp_path / "rom"
    brain_dir.mkdir(parents=True, exist_ok=True)
    rom_dir.mkdir(parents=True, exist_ok=True)

    _write(
        handoff_dir / "2026-04" / "handoff_2026-04-17_1100_gamma.md",
        "# Gamma\n\n*Session: 123e4567-e89b-12d3-a456-426614174002*",
    )
    _write(
        rom_dir / "rom_2026-04-17_gamma.md",
        "Gamma ROM summary",
    )

    monkeypatch.setattr(phantazein_indexer, "_get_brain_dir", lambda: brain_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_handoff_dir", lambda: handoff_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_rom_dir", lambda: rom_dir)

    result = phantazein_indexer.rebuild_phantazein_db(db_path=db_path)

    archived_db_path = Path(result["archived_db_path"])
    assert archived_db_path.exists()
    assert db_path.exists()
    assert result["handoffs"] == 1
    assert result["roms"] == 1
    assert result["db_health"]["status"] == "ok"

    rebuilt_store = get_store(db_path=db_path)
    sync_state = rebuilt_store.get_sync_state()
    assert sync_state["last_rebuild_at"] is not None
    assert sync_state["source_counts_json"]["handoffs"] == 1

    reset_store()


def test_full_sync_restores_project_links_for_reporter(
    tmp_path: Path,
    monkeypatch,
):
    reset_store()
    db_path = tmp_path / "state" / "phantazein.db"
    store = PhantazeinStore(db_path=db_path)

    brain_dir = tmp_path / "brain"
    handoff_dir = tmp_path / "handoff"
    rom_dir = tmp_path / "rom"
    boulesis_dir = tmp_path / "boulesis"
    constraints_dir = tmp_path / "constraints"
    mekhane_dir = tmp_path / "mekhane"
    mneme_dir = tmp_path / "mneme"
    peira_dir = tmp_path / "peira"
    poiema_dir = tmp_path / "poiema"
    external_dir = tmp_path / "external"
    brain_dir.mkdir(parents=True, exist_ok=True)
    rom_dir.mkdir(parents=True, exist_ok=True)
    boulesis_dir.mkdir(parents=True, exist_ok=True)
    constraints_dir.mkdir(parents=True, exist_ok=True)
    mekhane_dir.mkdir(parents=True, exist_ok=True)
    mneme_dir.mkdir(parents=True, exist_ok=True)
    peira_dir.mkdir(parents=True, exist_ok=True)
    poiema_dir.mkdir(parents=True, exist_ok=True)
    external_dir.mkdir(parents=True, exist_ok=True)

    session_id = "123e4567-e89b-12d3-a456-426614174099"
    _write(
        brain_dir / session_id / "task.md",
        "# Pinakas bootstrap\n\nproject link test",
    )
    _write(
        handoff_dir / "2026-04" / "handoff_2026-04-17_0900_pinakas.md",
        "# Pinakas 設計の handoff\n\n*Session: 123e4567-e89b-12d3-a456-426614174099*",
    )
    (boulesis_dir / "01_Pinakas｜Pinakas").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(phantazein_indexer, "_get_brain_dir", lambda: brain_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_handoff_dir", lambda: handoff_dir)
    monkeypatch.setattr(phantazein_indexer, "_get_rom_dir", lambda: rom_dir)
    monkeypatch.setattr(hgk_paths, "BOULESIS_DIR", boulesis_dir)
    monkeypatch.setattr(hgk_paths, "CONSTRAINTS_DIR", constraints_dir)
    monkeypatch.setattr(hgk_paths, "MEKHANE_DIR", mekhane_dir)
    monkeypatch.setattr(hgk_paths, "MNEME_DIR", mneme_dir)
    monkeypatch.setattr(hgk_paths, "PEIRA_DIR", peira_dir)
    monkeypatch.setattr(hgk_paths, "POIEMA_DIR", poiema_dir)
    monkeypatch.setattr(hgk_paths, "EXTERNAL_DIR", external_dir)

    result = phantazein_indexer.full_sync(store=store)
    cross_ref = store.get_session_cross_ref(limit=5)
    handoff = store.get_handoff_by_filename("handoff_2026-04-17_0900_pinakas.md")

    assert result["projects"] >= 1
    assert result["matched_projects"] == 1
    assert handoff is not None
    assert handoff["project_id"] == "boulesis/01_Pinakas｜Pinakas"
    assert cross_ref[0]["projects"] == [
        {
            "project_id": "boulesis/01_Pinakas｜Pinakas",
            "name": "01_Pinakas｜Pinakas",
        }
    ]

    store.close()


def test_match_handoffs_to_projects_links_compound_internal_projects(tmp_path: Path):
    reset_store()
    db_path = tmp_path / "state" / "phantazein.db"
    store = PhantazeinStore(db_path=db_path)

    store.upsert_project("workspace/mneme", "30_記憶｜Mneme")
    store.upsert_project("mekhane/09_編組｜Symploke", "09_編組｜Symploke")
    store.upsert_ide_session("sess-1", title="Compound project")
    store.upsert_handoff(
        filename="handoff_compound.md",
        title="compound normalization",
        session_id="sess-1",
        project_name="Mneme / Symploke",
    )

    matched = phantazein_indexer._match_handoffs_to_projects(store)
    handoff = store.get_handoff_by_filename("handoff_compound.md")
    links = store._conn.execute(
        "SELECT session_id, project_id FROM session_projects ORDER BY project_id"
    ).fetchall()

    assert matched == 1
    assert handoff is not None
    assert handoff["project_id"] == "mekhane/09_編組｜Symploke"
    assert [tuple(row) for row in links] == [
        ("sess-1", "mekhane/09_編組｜Symploke"),
        ("sess-1", "workspace/mneme"),
    ]

    store.close()


def test_match_handoffs_to_projects_normalizes_freeform_fallback(tmp_path: Path):
    reset_store()
    db_path = tmp_path / "state" / "phantazein.db"
    store = PhantazeinStore(db_path=db_path)

    store.upsert_ide_session("sess-1", title="Freeform project")
    store.upsert_handoff(
        filename="handoff_freeform.md",
        title="freeform normalization",
        session_id="sess-1",
        project_name="Motherbrain",
    )

    matched = phantazein_indexer._match_handoffs_to_projects(store)
    handoff = store.get_handoff_by_filename("handoff_freeform.md")
    project = store._conn.execute(
        "SELECT project_id, name FROM projects WHERE project_id = ?",
        ("freeform/motherbrain",),
    ).fetchone()

    assert matched == 1
    assert handoff is not None
    assert handoff["project_id"] == "freeform/motherbrain"
    assert tuple(project) == ("freeform/motherbrain", "Motherbrain")

    store.close()
