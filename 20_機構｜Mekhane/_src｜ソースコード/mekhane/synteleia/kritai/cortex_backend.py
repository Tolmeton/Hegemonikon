# PROOF: [L2/品質] <- mekhane/synteleia/kritai/cortex_backend.py A0→品質保証→Cortex直接LLMバックエンド
# PURPOSE: Cortex (Gemini API 直接呼出) バックエンド — IDE/LS 非依存
"""
CortexBackend — Direct Gemini API Bridge for Synteleia

OchemaBackend が Antigravity Language Server に依存するのに対し、
CortexBackend は Gemini API を直接呼び出す。
CI/CD や IDE 外での監査実行に使用。

デフォルトは Gemini 3.1 Pro。429/503 エラー時は Flash に自動フォールバック。

Usage:
    backend = CortexBackend()                       # gemini-3.1-pro-preview (default)
    backend = CortexBackend(model=FLASH)            # Flash を明示指定
    response = backend.query(prompt, context)
"""

import json
import logging
import os
from typing import Optional

from .semantic_agent import LLMBackend
from mekhane.ochema.model_defaults import PRO, FLASH

logger = logging.getLogger(__name__)


# PURPOSE: Cortex (Gemini API 直接呼出) バックエンド
class CortexBackend(LLMBackend):
    """Gemini API 直接呼出バックエンド。

    IDE (Language Server) に依存せず、GEMINI_API_KEY で直接認証する。
    CI/CD パイプラインやスタンドアロン実行で利用可能。

    デフォルトモデル: Gemini 3.1 Pro (最高品質)
    フォールバック: Gemini 3 Flash (429/503 時に自動降格)

    Available models:
        - gemini-3.1-pro-preview (default, highest quality)
        - gemini-3-flash-preview (fallback, cost-optimal)
    """

    # PURPOSE: 初期化
    def __init__(
        self,
        model: str = PRO,
        fallback_model: str = FLASH,
        timeout: float = 60.0,
        label: str = "",
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.label = label or model
        self._available: Optional[bool] = None

    # PURPOSE: Gemini API にクエリを送信 (Pro → Flash フォールバック)
    def query(self, prompt: str, context: str) -> str:
        """Gemini API 直接呼出でクエリを実行。

        Pro モデルで試行し、429 (CAPACITY_EXHAUSTED) / 503 (ServiceUnavailable)
        の場合は Flash にフォールバックする。
        """
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return json.dumps({
                "issues": [],
                "summary": "GEMINI_API_KEY not set",
                "confidence": 0.0,
            })

        genai.configure(api_key=api_key)
        combined = f"{prompt}\n\n---\n\n## 監査対象\n\n{context}"
        gen_config = genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2000,
        )

        # Pro で試行
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(combined, generation_config=gen_config)
            return response.text or "{}"
        except Exception as e:  # noqa: BLE001
            err_str = str(e).lower()
            # 429 CAPACITY_EXHAUSTED / 503 ServiceUnavailable → Flash にフォールバック
            if "429" in err_str or "503" in err_str or "capacity" in err_str or "unavailable" in err_str:
                logger.warning(
                    "Synteleia CortexBackend: %s unavailable (%s), falling back to %s",
                    self.model, type(e).__name__, self.fallback_model,
                )
                try:
                    fallback = genai.GenerativeModel(self.fallback_model)
                    response = fallback.generate_content(combined, generation_config=gen_config)
                    return response.text or "{}"
                except Exception as fallback_err:  # noqa: BLE001
                    logger.error("Synteleia CortexBackend: fallback also failed: %s", fallback_err)
                    return json.dumps({
                        "issues": [],
                        "summary": f"Both {self.model} and {self.fallback_model} failed",
                        "confidence": 0.0,
                    })
            else:
                # それ以外のエラーはそのまま raise
                raise

    # PURPOSE: バックエンドが利用可能か
    def is_available(self) -> bool:
        """GEMINI_API_KEY が設定されているかチェック。"""
        if self._available is None:
            self._available = bool(os.environ.get("GEMINI_API_KEY"))
        return self._available

    # PURPOSE: 文字列表現
    def __repr__(self) -> str:
        return f"CortexBackend(model={self.model!r}, fallback={self.fallback_model!r}, label={self.label!r})"
