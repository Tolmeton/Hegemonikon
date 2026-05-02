from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: ファイル操作 API — Chat UI からのローカルファイルアクセス


import base64
import logging
import mimetypes
import tempfile
import uuid
import json
import asyncio
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])

_ALLOWED_ROOT = (Path.home() / "Sync" / "oikos").resolve()


def _safe_path(raw: str) -> Path:
    """Resolve path and ensure it's under ALLOWED_ROOT."""
    from urllib.parse import unquote
    raw = unquote(raw)  # URL decode first (%7E → ~)
    p = Path(raw).expanduser().resolve()
    if not str(p).startswith(str(_ALLOWED_ROOT)):
        logger.warning(f"Access denied: {p} (resolved) is outside {_ALLOWED_ROOT}")
        raise ValueError(f"Access denied: {p} is outside {_ALLOWED_ROOT}")
    return p


@router.get("/api/files/list")
async def files_list(path: str = "~/Sync/oikos"):
    """List directory contents."""
    try:
        p = _safe_path(path)
        if not p.is_dir():
            return JSONResponse({"error": f"Not a directory: {p}"}, status_code=400)
        entries = []
        for item in sorted(p.iterdir()):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime,
                })
            except (PermissionError, OSError):
                continue
        return {"path": str(p), "entries": entries}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/files/read")
async def files_read(path: str):
    """Read file contents. Returns text or base64 for binary files."""
    try:
        p = _safe_path(path)
        if not p.is_file():
            return JSONResponse({"error": f"Not a file: {p}"}, status_code=400)
        mime, _ = mimetypes.guess_type(str(p))
        is_text = mime and mime.startswith("text/") or p.suffix in (
            ".md", ".py", ".ts", ".js", ".css", ".html", ".json", ".yaml", ".yml",
            ".toml", ".cfg", ".ini", ".sh", ".bash", ".rs", ".go", ".rb", ".tsx",
            ".jsx", ".vue", ".svelte", ".sql", ".xml", ".csv", ".env", ".txt",
            ".prompt", ".gitignore", ".dockerignore", ".conf",
        )
        if is_text:
            content = p.read_text(errors="replace")
            return {"path": str(p), "content": content, "encoding": "text",
                    "mime": mime or "text/plain", "size": len(content)}
        else:
            raw = p.read_bytes()
            return {"path": str(p), "content": base64.b64encode(raw).decode(),
                    "encoding": "base64", "mime": mime or "application/octet-stream",
                    "size": len(raw)}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/files/upload")
async def files_upload(file: UploadFile = File(...)):
    """Upload a file. Saved to temp dir, returns path."""
    try:
        upload_dir = Path(tempfile.gettempdir()) / "hgk_uploads"
        upload_dir.mkdir(exist_ok=True)
        dest = upload_dir / f"{uuid.uuid4().hex[:8]}_{file.filename}"
        content = await file.read()
        dest.write_bytes(content)
        mime, _ = mimetypes.guess_type(file.filename or "")
        return {"path": str(dest), "filename": file.filename, "size": len(content), "mime": mime}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


from pydantic import BaseModel

class WriteRequest(BaseModel):
    path: str
    content: str
    encoding: str = "text"  # "text" or "base64"

@router.post("/api/files/write")
async def files_write(req: WriteRequest):
    """Write content to an existing or new file."""
    try:
        p = _safe_path(req.path)
        if p.exists() and not p.is_file():
            return JSONResponse({"error": f"Path exists but is not a file: {p}"}, status_code=400)
        
        if req.encoding == "base64":
            p.write_bytes(base64.b64decode(req.content))
        else:
            p.write_text(req.content, encoding="utf-8")
        
        return {"success": True, "path": str(p), "size": p.stat().st_size}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


class RenameRequest(BaseModel):
    path: str
    new_path: str

@router.post("/api/files/rename")
async def files_rename(req: RenameRequest):
    """Rename a file or directory."""
    try:
        p = _safe_path(req.path)
        if not p.exists():
            return JSONResponse({"error": f"Path does not exist: {p}"}, status_code=400)
        
        new_p = _safe_path(req.new_path)
        if new_p.exists():
            return JSONResponse({"error": f"Destination already exists: {new_p}"}, status_code=400)
        
        p.rename(new_p)
        return {"success": True, "path": str(new_p)}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


class DeleteRequest(BaseModel):
    path: str

@router.post("/api/files/delete")
async def files_delete(req: DeleteRequest):
    """Delete a file or directory."""
    try:
        p = _safe_path(req.path)
        if not p.exists():
            return JSONResponse({"error": f"Path does not exist: {p}"}, status_code=400)
            
        import shutil
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        
        return {"success": True, "path": str(p)}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


class SearchRequest(BaseModel):
    query: str
    path: str = "~/Sync/oikos"
    is_regex: bool = False
    match_case: bool = False

@router.post("/api/files/search")
async def files_search(req: SearchRequest):
    """Search for text in files using ripgrep."""
    try:
        p = _safe_path(req.path)
        import subprocess
        
        cmd = ["/usr/bin/rg", "--json", "--hidden", "--glob", "!.git/*"]
        if not req.match_case:
            cmd.append("-i")
        if not req.is_regex:
            cmd.append("-F")
        cmd.extend(["-e", req.query, str(p)])
        
        logger.info(f"Running search: {' '.join(cmd)}")
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)  # type: ignore
        
        # ripgrep returns 0 on match, 1 on no match, 2 on error
        if result.returncode == 2:
            return JSONResponse({"error": f"Search error: {result.stderr}"}, status_code=500)
        
        matches = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data["type"] == "match":
                    matches.append({
                        "file": data["data"]["path"]["text"],
                        "line": data["data"]["line_number"],
                        "content": data["data"]["lines"]["text"]
                    })
            except Exception:  # noqa: BLE001
                continue
                
        return {"matches": matches, "count": len(matches)}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Search failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

