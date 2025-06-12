"""BestPracticesService module

Responsabile della ricerca di best practice su un dato topic, estratta dal
monolitico ``AIService``.  Per ora si limita a delegare all'implementazione
privata mantenendo la compatibilit\xE0.
"""
from __future__ import annotations

from typing import List

from mcp_server.ai_service import AIService


class BestPracticesService:
    """Service orientato a raccomandazioni e best practices tecniche."""

    def __init__(self, ai_service: AIService):
        self._ai_service = ai_service

    async def get_best_practices(self, topic: str, context: str = "") -> List[str]:
        """Restituisce una lista di best practice per il topic indicato."""
        return await self._ai_service._get_best_practices(  # type: ignore[attr-defined]
            topic=topic,
            context=context,
        )

    def extract_topic(self, text: str) -> str:
        """Metodo di utilit\xE0 che espone ``_extract_topic`` di AIService."""
        return self._ai_service._extract_topic(text)  # type: ignore[attr-defined]


__all__ = ["BestPracticesService"]
