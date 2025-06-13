"""
Use cases for PyTaskAI application layer.

This module contains all use cases that orchestrate domain services
and coordinate business operations for external adapters.
"""

from pytaskai.application.use_cases.ai_task_generation import AITaskGenerationUseCase
from pytaskai.application.use_cases.document_management import DocumentManagementUseCase
from pytaskai.application.use_cases.task_management import TaskManagementUseCase

__all__ = [
    "TaskManagementUseCase",
    "DocumentManagementUseCase",
    "AITaskGenerationUseCase",
]
