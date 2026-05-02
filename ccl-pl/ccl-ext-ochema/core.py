from typing import Optional
from mekhane.ochema.service import OchemaService

def ask_ochema(message: str, model: str = "claude-sonnet", timeout: float = 120.0) -> str:
    """OchemaService.ask への Pythonブリッジ
    
    Claude 指定時には Gemini への自動フォールバックが働く。
    エラーは捕捉せず送出させ、CCL側で構造的に扱えるようにする。
    """
    svc = OchemaService.get()
    resp = svc.ask(message, model=model, timeout=timeout)
    return resp.text

def chat_ochema(message: str, cascade_id: str = "", model: str = "claude-sonnet") -> str:
    """OchemaService.chat への Pythonブリッジ"""
    svc = OchemaService.get()
    resp = svc.chat(message, model=model, cascade_id=cascade_id)
    return resp.text
