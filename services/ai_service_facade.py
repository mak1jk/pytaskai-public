"""AIServiceFacade module

Orchestrates the newly extracted domain services (Research, Task Generation,
Best Practices) offrendo un punto di accesso unico e mantenendo retro
compatibilit\xE0 nei confronti del vecchio ``AIService`` dove necessario.
"""
from __future__ import annotations

from typing import List, Dict, Any

from mcp_server.ai_service import AIService

from .research_service import ResearchService
from .task_generation_service import TaskGenerationService
from .best_practices_service import BestPracticesService


class AIServiceFacade:
    """Facciata che coordina i servizi estratti da **AIService**.

    Parametri
    ---------
    project_root: str | None
        Radice del progetto per risolvere dipendenze interne (cache manager,
        usage tracker, ecc.).
    config: dict | None
        Configurazione opzionale passata al vecchio ``AIService`` per mantenere
        parit\xE0 di funzionalit\xE0.
    """

    def __init__(self, project_root: str | None = None, config: Dict[str, Any] | None = None):
        self._legacy_ai_service = AIService(project_root=project_root, config=config)
        # Instantiate extracted services
        self.research = ResearchService(self._legacy_ai_service)
        self.task_generation = TaskGenerationService(self._legacy_ai_service)
        self.best_practices = BestPracticesService(self._legacy_ai_service)

    # ---------------------------------------------------------------------
    # Facade helper methods
    # ---------------------------------------------------------------------

    async def get_lts_versions(self, technologies: List[str]) -> Dict[str, str]:
        """Shortcut verso ``ResearchService.get_lts_versions``."""
        return await self.research.get_lts_versions(technologies)

    async def generate_subtasks(
        self,
        parent_task_id: int,
        title: str,
        description: str,
        task_type: str,
        priority: str,
        target_count: int = 5,
        additional_context: str = "",
    ) -> List[Dict[str, Any]]:
        """Shortcut verso ``TaskGenerationService.generate_subtasks``."""
        return await self.task_generation.generate_subtasks(
            parent_task_id=parent_task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            target_count=target_count,
            additional_context=additional_context,
        )

    async def get_best_practices(self, topic: str, context: str = "") -> List[str]:
        """Shortcut verso ``BestPracticesService.get_best_practices``."""
        return await self.best_practices.get_best_practices(topic, context)

    # ------------------------------------------------------------------
    # Backward-compatibility shims (methods still used elsewhere)
    # ------------------------------------------------------------------

    async def generate_task_with_ai(self, *args, **kwargs):  # noqa: D401,E501
        """Forward to legacy ``AIService.generate_task_with_ai``.

        This method is retained to avoid large-scale refactors where the old
        ``AIService`` interface is still expected (e.g. within MCP tools).
        All positional/keyword arguments are passed through untouched.
        """

        return await self._legacy_ai_service.generate_task_with_ai(*args, **kwargs)

    # Retro compatibilit\xE0: esponiamo accesso diretto all'istanza legacy se
    # qualcun altro codice necessita di metodi non ancora rifattorizzati.
    @property
    def legacy(self) -> AIService:
        return self._legacy_ai_service

    # ------------------------------------------------------------------
    # Generic fallback for legacy methods/attributes
    # ------------------------------------------------------------------

    def __getattr__(self, item):  # noqa: D401
        """Delegate unknown attributes to the legacy ``AIService`` instance."""

        return getattr(self._legacy_ai_service, item)


__all__ = [
    "AIServiceFacade",
]
