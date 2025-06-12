"""ResearchService module

Provides research-related functionality such as fetching LTS versions or web
best-practice references.  In the first refactor iteration it delegates to the
existing AIService private helpers, so behaviour is preserved while moving
responsibilities out of the monolithic class.
"""
from __future__ import annotations

from typing import List, Dict, Any

from mcp_server.ai_service import AIService


class ResearchService:
    """Isolated service responsible for research-centric AI operations."""

    def __init__(self, ai_service: AIService):
        self._ai_service = ai_service

    async def get_lts_versions(self, technologies: List[str]) -> Dict[str, str]:
        """Return LTS versions for a list of technologies.

        This implementation simply delegates to the original ``AIService``
        helper to keep behaviour unchanged.
        """
        # Delegate – note: protected access acceptable during migration
        return await self._ai_service._get_lts_versions(technologies)  # type: ignore[attr-defined]

    # Future: additional research helpers (best practices, summaries, …)


__all__ = ["ResearchService"]
