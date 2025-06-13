"""
OpenAI service implementation for PyTaskAI infrastructure layer.

This module implements the AI service interfaces using OpenAI API,
following the Adapter pattern to integrate OpenAI with the application layer.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pytaskai.application.dto.task_dto import TaskCreateDTO
from pytaskai.application.interfaces.ai_service import (
    AIResearchService,
    AIServiceError,
    AITaskGenerationService,
)
from pytaskai.infrastructure.config.ai_config import AIConfig
from pytaskai.infrastructure.external.openai_client import OpenAIClient, OpenAIError
from pytaskai.infrastructure.external.prompt_templates import (
    PromptContext,
    PromptTemplateFactory,
    PromptType,
    create_prompt_context,
)

# Configure logging
logger = logging.getLogger(__name__)


class OpenAITaskGenerationService(AITaskGenerationService):
    """
    OpenAI implementation of AI task generation service.

    This service uses OpenAI API to generate tasks, subtasks, and provide
    task analysis using carefully crafted prompts and robust error handling.
    """

    def __init__(self, openai_client: OpenAIClient, config: AIConfig) -> None:
        """
        Initialize OpenAI task generation service.

        Args:
            openai_client: Configured OpenAI client
            config: AI configuration
        """
        self._client = openai_client
        self._config = config
        self._template_factory = PromptTemplateFactory()

    async def generate_tasks_from_prd(
        self, prd_content: str, project: str, max_tasks: int = 20
    ) -> List[TaskCreateDTO]:
        """
        Generate tasks from a Product Requirements Document using OpenAI.

        Args:
            prd_content: The PRD content to parse
            project: Project name for generated tasks
            max_tasks: Maximum number of tasks to generate

        Returns:
            List of TaskCreateDTO objects representing generated tasks
        """
        try:
            logger.info(f"Generating tasks from PRD for project '{project}'")

            # Create specialized prompt for PRD parsing
            system_prompt = self._build_prd_parsing_system_prompt()
            user_prompt = self._build_prd_parsing_user_prompt(
                prd_content, project, max_tasks
            )

            # Use research model for complex PRD analysis
            model = self._config.get_optimal_model_for_task("analysis", "high")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.7,
                max_tokens=self._config.max_tokens,
            )

            # Parse JSON response into TaskCreateDTO objects
            tasks = self._parse_tasks_response(response.content, project)

            logger.info(f"Generated {len(tasks)} tasks from PRD")
            return tasks[:max_tasks]  # Ensure we don't exceed limit

        except OpenAIError as e:
            logger.error(f"OpenAI error in PRD task generation: {e}")
            raise AIServiceError(f"Failed to generate tasks from PRD: {e}", "OpenAI")

        except Exception as e:
            logger.error(f"Unexpected error in PRD task generation: {e}")
            raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    async def generate_subtasks(
        self, parent_task_description: str, project: str, max_subtasks: int = 10
    ) -> List[TaskCreateDTO]:
        """
        Generate subtasks for a complex task using OpenAI.

        Args:
            parent_task_description: Description of the parent task
            project: Project name for generated subtasks
            max_subtasks: Maximum number of subtasks to generate

        Returns:
            List of TaskCreateDTO objects representing subtasks
        """
        try:
            logger.info(
                f"Generating {max_subtasks} subtasks for: {parent_task_description[:50]}..."
            )

            # Use task breakdown template
            template = self._template_factory.create_template(PromptType.TASK_BREAKDOWN)
            context = create_prompt_context(
                user_input=parent_task_description,
                project_context=project,
                max_items=max_subtasks,
            )

            system_prompt, user_prompt = template.generate_prompt_pair(context)

            # Use appropriate model based on complexity
            model = self._config.get_optimal_model_for_task("breakdown", "medium")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.8,  # Slightly higher for creativity
            )

            # Parse subtasks from response
            subtasks = self._parse_subtasks_response(response.content, project)

            logger.info(f"Generated {len(subtasks)} subtasks")
            return subtasks[:max_subtasks]

        except OpenAIError as e:
            logger.error(f"OpenAI error in subtask generation: {e}")
            raise AIServiceError(f"Failed to generate subtasks: {e}", "OpenAI")

        except Exception as e:
            logger.error(f"Unexpected error in subtask generation: {e}")
            raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    async def suggest_task_priority(
        self,
        task_title: str,
        task_description: Optional[str] = None,
        project_context: Optional[str] = None,
        use_fallback: bool = True,
    ) -> str:
        """
        Suggest priority for a task using OpenAI analysis.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task
            project_context: Optional context about the project

        Returns:
            Suggested priority (Low, Medium, High, Critical)
        """
        try:
            logger.info(f"Suggesting priority for task: {task_title}")

            system_prompt = self._build_priority_analysis_system_prompt()
            user_prompt = self._build_priority_analysis_user_prompt(
                task_title, task_description, project_context
            )

            # Use fast model for simple priority analysis
            model = self._config.get_optimal_model_for_task("analysis", "low")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.3,  # Lower temperature for consistent results
                max_tokens=50,  # Short response
            )

            # Extract priority from response
            priority = self._extract_priority_from_response(response.content)

            logger.info(f"Suggested priority '{priority}' for task: {task_title}")
            return priority

        except OpenAIError as e:
            logger.error(f"OpenAI error in priority suggestion: {e}")
            if use_fallback:
                # Return safe default rather than failing
                logger.warning("Falling back to Medium priority")
                return "Medium"
            else:
                # Re-raise exception for graceful degradation handling
                raise

        except Exception as e:
            logger.error(f"Unexpected error in priority suggestion: {e}")
            if use_fallback:
                return "Medium"
            else:
                raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    async def estimate_task_size(
        self,
        task_title: str,
        task_description: Optional[str] = None,
        use_fallback: bool = True,
    ) -> str:
        """
        Estimate the size/complexity of a task using OpenAI.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task

        Returns:
            Estimated size (Small, Medium, Large, Extra Large)
        """
        try:
            logger.info(f"Estimating size for task: {task_title}")

            system_prompt = self._build_size_estimation_system_prompt()
            user_prompt = self._build_size_estimation_user_prompt(
                task_title, task_description
            )

            # Use fast model for size estimation
            model = self._config.get_optimal_model_for_task("analysis", "low")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.3,
                max_tokens=50,
            )

            # Extract size from response
            size = self._extract_size_from_response(response.content)

            logger.info(f"Estimated size '{size}' for task: {task_title}")
            return size

        except OpenAIError as e:
            logger.error(f"OpenAI error in size estimation: {e}")
            if use_fallback:
                return "Medium"
            else:
                raise

        except Exception as e:
            logger.error(f"Unexpected error in size estimation: {e}")
            if use_fallback:
                return "Medium"
            else:
                raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    def _build_prd_parsing_system_prompt(self) -> str:
        """Build system prompt for PRD parsing."""
        return """
You are an expert project manager and technical analyst. Your role is to analyze Product Requirements Documents (PRDs) and break them down into actionable development tasks.

Guidelines for PRD analysis:
1. Identify core features and functionality
2. Break down complex features into implementable tasks
3. Consider technical implementation aspects
4. Include testing, documentation, and deployment tasks
5. Prioritize tasks based on dependencies and business value
6. Estimate relative complexity

Response format:
Provide a JSON array of task objects with these fields:
- title: Clear, actionable task title
- description: Detailed task description
- task_type: One of [Task, Feature, Bug, Enhancement, Research, Documentation]
- priority: One of [Low, Medium, High, Critical]
- size: One of [XS, S, M, L, XL]
- tags: Array of relevant tags

Ensure tasks are specific, measurable, and implementable.
"""

    def _build_prd_parsing_user_prompt(
        self, prd_content: str, project: str, max_tasks: int
    ) -> str:
        """Build user prompt for PRD parsing."""
        return f"""
Analyze this PRD and generate {max_tasks} actionable development tasks for project "{project}":

{prd_content}

Generate comprehensive tasks covering:
- Core feature implementation
- Testing and quality assurance
- Documentation and user guides
- Technical infrastructure
- Integration and deployment

Provide exactly {max_tasks} tasks in JSON format.
"""

    def _build_priority_analysis_system_prompt(self) -> str:
        """Build system prompt for priority analysis."""
        return """
You are a project prioritization expert. Analyze tasks and suggest appropriate priorities based on:

- Business impact and value
- Technical urgency and dependencies
- Risk and complexity factors
- User experience impact

Priority levels:
- Critical: Blocking issues, security vulnerabilities, production failures
- High: Important features, significant improvements, dependency tasks
- Medium: Standard features, enhancements, nice-to-have improvements
- Low: Minor improvements, cleanup tasks, future considerations

Respond with only the priority level: Critical, High, Medium, or Low.
"""

    def _build_priority_analysis_user_prompt(
        self, title: str, description: Optional[str], context: Optional[str]
    ) -> str:
        """Build user prompt for priority analysis."""
        prompt_parts = [f"Task: {title}"]

        if description:
            prompt_parts.append(f"Description: {description}")

        if context:
            prompt_parts.append(f"Project context: {context}")

        prompt_parts.append("\nSuggest priority level:")

        return "\n".join(prompt_parts)

    def _build_size_estimation_system_prompt(self) -> str:
        """Build system prompt for size estimation."""
        return """
You are a technical estimation expert. Analyze tasks and estimate their complexity/size based on:

- Technical complexity and scope
- Time and effort required
- Dependencies and unknowns
- Testing and documentation needs

Size categories:
- XS: Simple tasks, 1-2 hours, minimal complexity
- S: Small tasks, half day, straightforward implementation
- M: Medium tasks, 1-2 days, moderate complexity
- L: Large tasks, 3-5 days, significant complexity
- XL: Extra large tasks, 1+ weeks, major features or complex changes

Respond with only the size: XS, S, M, L, or XL.
"""

    def _build_size_estimation_user_prompt(
        self, title: str, description: Optional[str]
    ) -> str:
        """Build user prompt for size estimation."""
        prompt_parts = [f"Task: {title}"]

        if description:
            prompt_parts.append(f"Description: {description}")

        prompt_parts.append("\nEstimate size:")

        return "\n".join(prompt_parts)

    def _parse_tasks_response(
        self, response_content: str, project: str
    ) -> List[TaskCreateDTO]:
        """
        Parse OpenAI response into TaskCreateDTO objects.

        Args:
            response_content: Raw response from OpenAI
            project: Project name for tasks

        Returns:
            List of parsed TaskCreateDTO objects
        """
        try:
            # Try to extract JSON from response
            json_start = response_content.find("[")
            json_end = response_content.rfind("]") + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")

            json_content = response_content[json_start:json_end]
            tasks_data = json.loads(json_content)

            tasks = []
            for task_data in tasks_data:
                if isinstance(task_data, dict):
                    # Map OpenAI response to TaskCreateDTO
                    task = TaskCreateDTO(
                        title=task_data.get("title", "Untitled Task"),
                        description=task_data.get("description"),
                        project=project,
                        task_type=task_data.get("task_type", "Task"),
                        status="Todo",
                        priority=task_data.get("priority", "Medium"),
                        size=task_data.get("size"),
                        tags=task_data.get("tags", []),
                    )
                    tasks.append(task)

            return tasks

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse tasks response: {e}")
            # Return fallback task if parsing fails
            return [
                TaskCreateDTO(
                    title="Review AI Generated Tasks",
                    description=f"Review and manually create tasks from AI response: {response_content[:200]}...",
                    project=project,
                    task_type="Task",
                    status="Todo",
                    priority="Medium",
                )
            ]

    def _parse_subtasks_response(
        self, response_content: str, project: str
    ) -> List[TaskCreateDTO]:
        """
        Parse OpenAI subtask response into TaskCreateDTO objects.

        Args:
            response_content: Raw response from OpenAI
            project: Project name for subtasks

        Returns:
            List of parsed TaskCreateDTO objects
        """
        # Reuse the same parsing logic as tasks
        return self._parse_tasks_response(response_content, project)

    def _extract_priority_from_response(self, response_content: str) -> str:
        """
        Extract priority from OpenAI response.

        Args:
            response_content: Raw response content

        Returns:
            Priority level string
        """
        content = response_content.strip().upper()

        if "CRITICAL" in content:
            return "Critical"
        elif "HIGH" in content:
            return "High"
        elif "LOW" in content:
            return "Low"
        else:
            return "Medium"

    def _extract_size_from_response(self, response_content: str) -> str:
        """
        Extract size from OpenAI response.

        Args:
            response_content: Raw response content

        Returns:
            Size string
        """
        content = response_content.strip().upper()

        if "XL" in content:
            return "XL"
        elif "L" in content and "XL" not in content:
            return "L"
        elif "XS" in content:
            return "XS"
        elif "S" in content and "XS" not in content:
            return "S"
        else:
            return "M"


class OpenAIResearchService(AIResearchService):
    """
    OpenAI implementation of AI research service.

    This service uses OpenAI to provide research and contextual analysis,
    though it's currently limited to the model's training data.
    """

    def __init__(self, openai_client: OpenAIClient, config: AIConfig) -> None:
        """
        Initialize OpenAI research service.

        Args:
            openai_client: Configured OpenAI client
            config: AI configuration
        """
        self._client = openai_client
        self._config = config

    async def research_task_context(
        self, task_title: str, task_description: Optional[str] = None
    ) -> str:
        """
        Research additional context for a task using OpenAI knowledge.

        Args:
            task_title: Title of the task
            task_description: Optional description of the task

        Returns:
            Research findings and contextual information
        """
        try:
            logger.info(f"Researching context for task: {task_title}")

            system_prompt = self._build_research_system_prompt()
            user_prompt = self._build_research_user_prompt(task_title, task_description)

            # Use research model for comprehensive analysis
            model = self._config.get_optimal_model_for_task("research", "medium")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.7,
            )

            logger.info(f"Generated research context for task: {task_title}")
            return response.content

        except OpenAIError as e:
            logger.error(f"OpenAI error in task research: {e}")
            raise AIServiceError(f"Failed to research task context: {e}", "OpenAI")

        except Exception as e:
            logger.error(f"Unexpected error in task research: {e}")
            raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    async def suggest_related_tasks(
        self, completed_task_title: str, project: str
    ) -> List[TaskCreateDTO]:
        """
        Suggest follow-up tasks based on a completed task.

        Args:
            completed_task_title: Title of the completed task
            project: Project name for suggested tasks

        Returns:
            List of suggested follow-up tasks
        """
        try:
            logger.info(f"Suggesting related tasks for: {completed_task_title}")

            system_prompt = self._build_related_tasks_system_prompt()
            user_prompt = self._build_related_tasks_user_prompt(
                completed_task_title, project
            )

            model = self._config.get_optimal_model_for_task("suggestions", "medium")

            response = await self._client.generate_completion_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=0.8,  # Higher creativity for suggestions
            )

            # Parse suggestions into tasks
            tasks = self._parse_tasks_response(response.content, project)

            logger.info(f"Generated {len(tasks)} related task suggestions")
            return tasks

        except OpenAIError as e:
            logger.error(f"OpenAI error in related task suggestions: {e}")
            raise AIServiceError(f"Failed to suggest related tasks: {e}", "OpenAI")

        except Exception as e:
            logger.error(f"Unexpected error in related task suggestions: {e}")
            raise AIServiceError(f"Unexpected error: {e}", "OpenAI")

    def _build_research_system_prompt(self) -> str:
        """Build system prompt for task research."""
        return """
You are a research analyst and domain expert. Provide comprehensive context and background information for development tasks.

Provide research covering:
1. Technical background and concepts
2. Best practices and standards
3. Common challenges and pitfalls
4. Relevant tools and technologies
5. Implementation considerations
6. Testing and validation approaches

Keep research practical and actionable for developers.
"""

    def _build_research_user_prompt(
        self, title: str, description: Optional[str]
    ) -> str:
        """Build user prompt for task research."""
        prompt_parts = [
            f"Research context and background for this development task:",
            f"\nTask: {title}",
        ]

        if description:
            prompt_parts.append(f"Description: {description}")

        prompt_parts.extend(
            [
                "\nProvide:",
                "- Technical background and key concepts",
                "- Best practices and implementation guidance",
                "- Common challenges and solutions",
                "- Relevant tools and technologies",
                "- Testing and validation considerations",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_related_tasks_system_prompt(self) -> str:
        """Build system prompt for related task suggestions."""
        return """
You are a project management expert. When a task is completed, suggest logical follow-up tasks and next steps.

Consider:
1. Natural progression and next steps
2. Testing and validation tasks
3. Documentation and communication needs
4. Integration and deployment considerations
5. Maintenance and monitoring tasks
6. User feedback and iteration opportunities

Response format:
Provide a JSON array of follow-up task objects with:
- title: Clear task title
- description: Detailed description
- task_type: Type of follow-up task
- priority: Suggested priority
- reasoning: Why this task is relevant
"""

    def _build_related_tasks_user_prompt(
        self, completed_task: str, project: str
    ) -> str:
        """Build user prompt for related task suggestions."""
        return f"""
A task has been completed in project "{project}":

Completed Task: {completed_task}

Suggest 3-5 logical follow-up tasks that should be considered next. Include testing, documentation, integration, and maintenance tasks as appropriate.

Provide suggestions in JSON format.
"""

    def _parse_tasks_response(
        self, response_content: str, project: str
    ) -> List[TaskCreateDTO]:
        """
        Parse OpenAI response into TaskCreateDTO objects.

        This reuses the same parsing logic from the task generation service.
        """
        # Import here to avoid circular imports
        from pytaskai.infrastructure.external.openai_service import (
            OpenAITaskGenerationService,
        )

        # Create a temporary instance just for parsing
        temp_service = OpenAITaskGenerationService(self._client, self._config)
        return temp_service._parse_tasks_response(response_content, project)


def create_openai_services(
    config: AIConfig,
) -> tuple[OpenAITaskGenerationService, OpenAIResearchService]:
    """
    Factory function to create OpenAI AI services.

    Args:
        config: AI configuration

    Returns:
        Tuple of (task_generation_service, research_service)

    Raises:
        AIServiceError: If OpenAI is not properly configured
    """
    if not config.has_openai_access():
        raise AIServiceError("OpenAI API key not configured", "OpenAI")

    from pytaskai.infrastructure.external.openai_client import create_openai_client

    client = create_openai_client(config)

    task_generation_service = OpenAITaskGenerationService(client, config)
    research_service = OpenAIResearchService(client, config)

    return task_generation_service, research_service
