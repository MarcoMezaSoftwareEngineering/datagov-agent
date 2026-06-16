"""Cliente LLM (Ollama) con verificación de disponibilidad y degradación elegante.

Si Ollama no responde, `complete()` devuelve None y cada agente usa su lógica
determinista de respaldo. Así el sistema es demostrable y testeable sin modelos.
"""

from __future__ import annotations

from app.config import settings
from app.services.embeddings import ollama_available
from app.utils.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Envoltura ligera sobre ChatOllama con manejo de errores."""

    def __init__(self) -> None:
        self.model = settings.llm_model
        self.available = ollama_available()
        self._chat = None
        self._chat_json = None
        if self.available:
            try:
                self._chat = self._build()
                self._chat_json = self._build(json_mode=True)
                logger.info("LLM Ollama listo: %s", self.model)
            except Exception as exc:  # pragma: no cover - defensivo
                logger.warning("No se pudo inicializar ChatOllama (%s)", exc)
                self.available = False

    def _build(self, json_mode: bool = False):
        from langchain_ollama import ChatOllama

        kwargs = dict(
            model=self.model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )
        if json_mode:
            kwargs["format"] = "json"
        return ChatOllama(**kwargs)

    def complete(self, system: str, user: str, json_mode: bool = False) -> str | None:
        """Devuelve la respuesta del LLM o None si no está disponible / falla."""
        if not self.available:
            return None
        from langchain_core.messages import HumanMessage, SystemMessage

        chat = self._chat_json if json_mode else self._chat
        try:
            resp = chat.invoke([SystemMessage(content=system), HumanMessage(content=user)])
            return resp.content if hasattr(resp, "content") else str(resp)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("Fallo en la invocación del LLM (%s)", exc)
            return None


_CLIENT: LLMClient | None = None


def get_llm() -> LLMClient:
    """Devuelve un cliente LLM cacheado a nivel de proceso."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = LLMClient()
    return _CLIENT
