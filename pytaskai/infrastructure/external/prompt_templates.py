"""
AI prompt templates for PyTaskAI infrastructure layer.

This module provides reusable prompt templates for different AI operations,
following the Template Method pattern to ensure consistency and maintainability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from pytaskai.application.dto.task_dto import TaskCreateDTO, TaskResponseDTO


class PromptType(Enum):
    """Types of AI prompts supported by the system."""

    TASK_BREAKDOWN = "task_breakdown"
    TASK_SUGGESTIONS = "task_suggestions"
    TEMPLATE_GENERATION = "template_generation"
    TASK_ANALYSIS = "task_analysis"
    PROJECT_PLANNING = "project_planning"


@dataclass
class PromptContext:
    """Context information for AI prompt generation."""

    user_input: str
    task_context: Optional[TaskResponseDTO] = None
    project_context: Optional[str] = None
    existing_tasks: Optional[List[TaskResponseDTO]] = None
    breakdown_approach: str = "functional"
    max_items: int = 5
    additional_context: Optional[Dict[str, Any]] = None


class PromptTemplate(ABC):
    """
    Abstract base class for AI prompt templates.

    This class follows the Template Method pattern, defining the
    structure for generating prompts while allowing subclasses
    to customize specific parts.
    """

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this template type."""
        pass

    @abstractmethod
    def build_user_prompt(self, context: PromptContext) -> str:
        """Build the user prompt from context."""
        pass

    def generate_prompt_pair(self, context: PromptContext) -> tuple[str, str]:
        """
        Generate system and user prompt pair.

        Args:
            context: Context for prompt generation

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = self.get_system_prompt()
        user_prompt = self.build_user_prompt(context)

        return system_prompt, user_prompt


class TaskBreakdownTemplate(PromptTemplate):
    """
    Template for breaking down complex tasks into subtasks.

    This template helps AI generate meaningful subtasks that follow
    good task management practices.
    """

    def get_system_prompt(self) -> str:
        return """
You are an expert project manager and task breakdown specialist. Your role is to analyze complex tasks and break them down into clear, actionable subtasks.

Guidelines for task breakdown:
1. Each subtask should be specific and actionable
2. Subtasks should be roughly equal in complexity when possible
3. Dependencies between subtasks should be minimal
4. Each subtask should have a clear definition of done
5. Use descriptive titles that clearly indicate the work required
6. Consider different breakdown approaches: functional, temporal, by component, by skill

Response format:
- Provide a JSON array of subtask objects
- Each object should have: title, description, estimated_size, priority
- Include a brief explanation of your breakdown approach
- Limit to the requested number of subtasks
"""

    def build_user_prompt(self, context: PromptContext) -> str:
        prompt_parts = [
            f"Please break down this task into {context.max_items} subtasks:",
            f"\nTask: {context.user_input}",
        ]

        if context.task_context:
            prompt_parts.extend(
                [
                    f"\nCurrent task context:",
                    f"- Description: {context.task_context.description or 'No description'}",
                    f"- Priority: {context.task_context.priority or 'Medium'}",
                    f"- Project: {context.task_context.project or 'Default'}",
                ]
            )

        if context.project_context:
            prompt_parts.append(f"\nProject context: {context.project_context}")

        if context.existing_tasks:
            task_titles = [task.title for task in context.existing_tasks[:5]]
            prompt_parts.append(f"\nExisting related tasks: {', '.join(task_titles)}")

        prompt_parts.extend(
            [
                f"\nBreakdown approach: {context.breakdown_approach}",
                f"\nPlease provide {context.max_items} well-structured subtasks.",
            ]
        )

        return "\n".join(prompt_parts)


class TaskSuggestionsTemplate(PromptTemplate):
    """
    Template for generating task suggestions based on context.

    This template helps users discover related tasks or next steps
    they might not have considered.
    """

    def get_system_prompt(self) -> str:
        return """
You are an intelligent task management assistant. Your role is to suggest relevant tasks based on user input and project context.

Guidelines for task suggestions:
1. Suggest tasks that are relevant to the user's current work
2. Consider different task types: implementation, testing, documentation, research
3. Think about dependencies and logical task sequences
4. Suggest tasks of varying complexity and time investment
5. Consider maintenance and follow-up tasks
6. Be creative but practical

Response format:
- Provide a JSON array of suggested task objects
- Each object should have: title, description, task_type, priority, estimated_size
- Include reasoning for each suggestion
- Prioritize suggestions by relevance and importance
"""

    def build_user_prompt(self, context: PromptContext) -> str:
        prompt_parts = [
            f"Based on this input, suggest {context.max_items} relevant tasks:",
            f"\nUser input: {context.user_input}",
        ]

        if context.project_context:
            prompt_parts.append(f"\nProject context: {context.project_context}")

        if context.existing_tasks:
            task_list = "\n".join(
                [
                    f"- {task.title} [{task.status}]"
                    for task in context.existing_tasks[:10]
                ]
            )
            prompt_parts.append(f"\nExisting tasks:\n{task_list}")

        prompt_parts.extend(
            [
                f"\nPlease suggest {context.max_items} relevant and useful tasks.",
                "Consider implementation, testing, documentation, and maintenance tasks.",
            ]
        )

        return "\n".join(prompt_parts)


class TemplateGenerationTemplate(PromptTemplate):
    """
    Template for generating task templates based on patterns.

    This template creates reusable task templates for common
    project patterns and workflows.
    """

    def get_system_prompt(self) -> str:
        return """
You are a workflow optimization expert. Your role is to create reusable task templates based on common project patterns and user requirements.

Guidelines for template generation:
1. Identify the core workflow or pattern
2. Create generic, reusable task templates
3. Include placeholder variables for customization
4. Consider standard phases: planning, implementation, testing, deployment, review
5. Include quality gates and checkpoints
6. Make templates adaptable to different project sizes

Response format:
- Provide a JSON object with template metadata and tasks
- Include: name, description, category, tasks array
- Each task should have: title, description, task_type, dependencies
- Use placeholder variables like {{project_name}}, {{feature_name}}
- Include usage instructions
"""

    def build_user_prompt(self, context: PromptContext) -> str:
        prompt_parts = [
            "Create a reusable task template based on this pattern:",
            f"\nPattern/Workflow: {context.user_input}",
        ]

        if context.project_context:
            prompt_parts.append(f"\nProject type: {context.project_context}")

        if context.existing_tasks:
            prompt_parts.append("\nExample tasks to consider:")
            for task in context.existing_tasks[:5]:
                prompt_parts.append(
                    f"- {task.title}: {task.description or 'No description'}"
                )

        prompt_parts.extend(
            [
                "\nCreate a comprehensive template that can be reused for similar workflows.",
                "Include standard phases and quality checkpoints.",
                "Use placeholder variables for customization.",
            ]
        )

        return "\n".join(prompt_parts)


class TaskAnalysisTemplate(PromptTemplate):
    """
    Template for analyzing existing tasks and providing insights.

    This template helps users understand task complexity,
    dependencies, and potential issues.
    """

    def get_system_prompt(self) -> str:
        return """
You are a project analysis expert. Your role is to analyze tasks and provide insights about complexity, risks, dependencies, and optimization opportunities.

Guidelines for task analysis:
1. Assess task complexity and effort estimation
2. Identify potential risks and blockers
3. Suggest optimizations and improvements
4. Analyze dependencies and sequencing
5. Consider resource requirements
6. Identify missing or unclear requirements

Response format:
- Provide a JSON object with analysis results
- Include: complexity_score, risk_factors, dependencies, recommendations
- Give specific, actionable advice
- Highlight critical issues that need attention
"""

    def build_user_prompt(self, context: PromptContext) -> str:
        prompt_parts = [
            "Please analyze this task and provide insights:",
            f"\nTask: {context.user_input}",
        ]

        if context.task_context:
            prompt_parts.extend(
                [
                    "\nTask details:",
                    f"- Description: {context.task_context.description or 'No description'}",
                    f"- Status: {context.task_context.status}",
                    f"- Priority: {context.task_context.priority or 'Medium'}",
                    f"- Size: {context.task_context.size or 'Unknown'}",
                ]
            )

        if context.existing_tasks:
            prompt_parts.append("\nRelated tasks in project:")
            for task in context.existing_tasks[:5]:
                prompt_parts.append(f"- {task.title} [{task.status}]")

        prompt_parts.extend(
            [
                "\nProvide analysis covering:",
                "- Complexity assessment",
                "- Risk factors and potential blockers",
                "- Dependencies and sequencing",
                "- Recommendations for improvement",
            ]
        )

        return "\n".join(prompt_parts)


class PromptTemplateFactory:
    """
    Factory for creating appropriate prompt templates.

    This factory follows the Factory pattern to create the right
    template type based on the requested AI operation.
    """

    _templates = {
        PromptType.TASK_BREAKDOWN: TaskBreakdownTemplate,
        PromptType.TASK_SUGGESTIONS: TaskSuggestionsTemplate,
        PromptType.TEMPLATE_GENERATION: TemplateGenerationTemplate,
        PromptType.TASK_ANALYSIS: TaskAnalysisTemplate,
    }

    @classmethod
    def create_template(cls, prompt_type: PromptType) -> PromptTemplate:
        """
        Create a prompt template of the specified type.

        Args:
            prompt_type: Type of prompt template to create

        Returns:
            Appropriate PromptTemplate instance

        Raises:
            ValueError: If prompt type is not supported
        """
        if prompt_type not in cls._templates:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")

        template_class = cls._templates[prompt_type]
        return template_class()

    @classmethod
    def get_supported_types(cls) -> List[PromptType]:
        """
        Get list of supported prompt types.

        Returns:
            List of supported PromptType values
        """
        return list(cls._templates.keys())


def create_prompt_context(
    user_input: str,
    task_context: Optional[TaskResponseDTO] = None,
    project_context: Optional[str] = None,
    existing_tasks: Optional[List[TaskResponseDTO]] = None,
    **kwargs,
) -> PromptContext:
    """
    Factory function to create prompt context.

    Args:
        user_input: User's input text
        task_context: Optional current task context
        project_context: Optional project information
        existing_tasks: Optional list of related tasks
        **kwargs: Additional context parameters

    Returns:
        Configured PromptContext instance
    """
    return PromptContext(
        user_input=user_input,
        task_context=task_context,
        project_context=project_context,
        existing_tasks=existing_tasks,
        **kwargs,
    )
