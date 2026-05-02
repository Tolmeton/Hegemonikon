# PROOF: [L2/品質] <- mekhane/synteleia/kritai/ochema_backend.py A0→品質保証→Ochēma経由LLMバックエンド
# PURPOSE: Ochēma (OchemaService) 経由の LLM バックエンド
"""
OchemaBackend — Cortex API Bridge for Synteleia

OchemaService を使い、Cortex API 経由で LLM を Synteleia 監査に利用する。
Strategy Pattern: LLMBackend の具象実装。

Usage:
    backend = OchemaBackend(model="gemini-3-flash-preview")
    response = backend.query(prompt, context)
"""

from typing import Optional

from .semantic_agent import LLMBackend


# PURPOSE: Ochēma (OchemaService) 経由の LLM バックエンド
class OchemaBackend(LLMBackend):
    """Ochēma (OchemaService) 経由の LLM バックエンド。

    Cortex API 経由で利用可能な LLM にクエリを送信する。
    """

    # PURPOSE: [L2-auto] 初期化: init__
    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        timeout: float = 60.0,
        label: str = "",
    ):
        self.model = model
        self.timeout = timeout
        self.label = label or model
        self._svc = None
        self._available: Optional[bool] = None

    # PURPOSE: LLM にクエリを送信
    def query(self, prompt: str, context: str) -> str:
        """Ochēma 経由で LLM にクエリを送信し、テキスト応答を返す。"""
        svc = self._get_service()
        combined = f"{prompt}\n\n---\n\n## 監査対象\n\n{context}"

        response = svc.ask(
            message=combined,
            model=self.model,
            timeout=self.timeout,
        )

        return response.text

    # PURPOSE: バックエンドが利用可能か
    def is_available(self) -> bool:
        """Cortex API が接続可能かチェック。"""
        if self._available is None:
            try:
                svc = self._get_service()
                self._available = svc.cortex_available
            except Exception:  # noqa: BLE001
                self._available = False
        return self._available

    # PURPOSE: OchemaService のシングルトン取得
    def _get_service(self):
        """OchemaService をシングルトンで取得。"""
        if self._svc is None:
            from mekhane.ochema.service import OchemaService
            self._svc = OchemaService.get()
        return self._svc

    # PURPOSE: [L2-auto] 文字列表現: repr__
    def __repr__(self) -> str:
        return f"OchemaBackend(model={self.model!r}, label={self.label!r})"
