"""TaskGenerationService module

Encapsula la logica di generazione task/subtask finora contenuta dentro
``AIService``.  In questa prima iterazione esponiamo un metodo principale che
si appoggia ai metodi protetti esistenti mantenendo compatibilit\xE0.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from mcp_server.ai_service import AIService


class TaskGenerationService:
    """Service dedicato alla generazione di task e subtasks mediante AI."""

    def __init__(self, ai_service: AIService):
        self._ai_service = ai_service

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
        """Genera subtasks delegando alla vecchia implementazione."""
        return await self._ai_service._generate_subtasks(  # type: ignore[attr-defined]
            parent_task_id=parent_task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            target_count=target_count,
            additional_context=additional_context,
        )

    # TODO: estrarre anche generate_task_with_ai (task principale) in step successivi


__all__ = ["TaskGenerationService"]
