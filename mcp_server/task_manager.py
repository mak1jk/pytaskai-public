"""
PyTaskAI - MCP Task Management Tools

FastMCP tools for task management operations including list, create, update, and manage tasks.
Integrates with Claude Code for seamless task workflow management.
"""

from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
from fastmcp import FastMCP

from .utils import (
    load_tasks,
    save_tasks,
    validate_tasks_file,
    get_tasks_statistics,
    ensure_directories_exist,
    get_reports_directory,  # PyTaskAI: Added for standardized report paths
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("PyTaskAI MCP Server")


def _list_tasks_internal(
    project_root: str,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    include_subtasks: bool = True,
    include_stats: bool = False,
) -> Dict[str, Any]:
    """Internal function for listing tasks (without MCP decorator)"""
    try:
        logger.info(f"Loading tasks from project: {project_root}")

        # Ensure directory structure exists
        ensure_directories_exist(project_root)

        # Load tasks using database manager
        from .database import get_db_manager

        db_manager = get_db_manager(project_root)
        tasks = db_manager.get_all_tasks(include_subtasks=include_subtasks)

        if not tasks:
            return {
                "tasks": [],
                "total_count": 0,
                "message": "No tasks found in database",
                "project_root": project_root,
            }

        # Apply status filter
        if status_filter:
            tasks = [task for task in tasks if task.get("status") == status_filter]

        # Apply priority filter
        if priority_filter:
            tasks = [task for task in tasks if task.get("priority") == priority_filter]

        # Apply type filter
        if type_filter:
            tasks = [task for task in tasks if task.get("type", "task") == type_filter]

        # Filter subtasks if requested
        if not include_subtasks:
            # Make a copy to avoid modifying original data
            tasks = [dict(task) for task in tasks]
            for task in tasks:
                if "subtasks" in task:
                    del task["subtasks"]

        result = {
            "tasks": tasks,
            "total_count": len(tasks),
            "filters_applied": {
                "status": status_filter,
                "priority": priority_filter,
                "type": type_filter,
                "include_subtasks": include_subtasks,
            },
            "project_root": project_root,
        }

        # Add stats if requested
        if include_stats:
            try:
                stats = get_tasks_statistics(tasks)
                result["statistics"] = stats
            except Exception as e:
                logger.warning(f"Failed to get task statistics: {e}")
                result["statistics"] = {}

        logger.info(f"Successfully loaded {len(tasks)} tasks")
        return result

    except Exception as e:
        logger.error(f"Error loading tasks: {str(e)}")
        return {
            "error": f"Failed to load tasks: {str(e)}",
            "tasks": [],
            "total_count": 0,
            "project_root": project_root,
        }


@mcp.tool()
def list_tasks_tool(
    project_root: str,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    include_subtasks: bool = True,
    include_stats: bool = False,
) -> Dict[str, Any]:
    """
    Lista tutti i task del progetto con filtri opzionali.

    Args:
        project_root: Path assoluto alla directory del progetto
        status_filter: Filtra per status (pending, in-progress, done, cancelled)
        priority_filter: Filtra per priorità (highest, high, medium, low, lowest)
        type_filter: Filtra per tipo (task, bug, feature, enhancement, research, documentation)
        include_subtasks: Includi i subtask nella risposta
        include_stats: Includi statistiche del progetto

    Returns:
        Dict contenente lista task e metadati
    """
    return _list_tasks_internal(
        project_root=project_root,
        status_filter=status_filter,
        priority_filter=priority_filter,
        type_filter=type_filter,
        include_subtasks=include_subtasks,
        include_stats=include_stats,
    )


@mcp.tool()
def get_task_tool(
    project_root: str, task_id: Union[int, str], include_subtasks: bool = True
) -> Dict[str, Any]:
    """
    Ottieni un task specifico per ID.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task da recuperare
        include_subtasks: Includi i subtask nella risposta

    Returns:
        Dict contenente il task richiesto
    """
    try:
        logger.info(f"Getting task {task_id} from project: {project_root}")

        # Ensure directory structure exists
        ensure_directories_exist(project_root)

        # Load tasks using database manager (consistent with _list_tasks_internal)
        from .database import get_db_manager

        db_manager = get_db_manager(project_root)
        tasks = db_manager.get_all_tasks(include_subtasks=include_subtasks)

        if not tasks:
            return {
                "error": "No tasks found in database",
                "task": None,
                "project_root": project_root,
            }

        task_id = int(task_id)

        # Find the task
        task = None
        for t in tasks:
            if isinstance(t, dict) and t.get("id") == task_id:
                task = t.copy()
                break

        if not task:
            return {
                "error": f"Task with ID {task_id} not found",
                "task": None,
                "project_root": project_root,
            }

        # Filter subtasks if requested
        if not include_subtasks and "subtasks" in task:
            del task["subtasks"]

        logger.info(f"Successfully retrieved task {task_id}")
        return {"task": task, "task_id": task_id, "project_root": project_root}

    except Exception as e:
        import traceback

        full_traceback = traceback.format_exc()
        logger.error(f"Error getting task {task_id}: {str(e)}")
        logger.error(f"Full traceback: {full_traceback}")

        error_msg = (
            f"Failed to get task {task_id}: {str(e)}\nTraceback: {full_traceback}"
        )

        return {
            "error": error_msg,
            "task": None,
            "project_root": project_root,
        }


@mcp.tool()
def get_next_task_tool(
    project_root: str, exclude_dependencies: bool = False
) -> Dict[str, Any]:
    """
    Trova il prossimo task da eseguire basato su dipendenze e priorità.

    Args:
        project_root: Path assoluto alla directory del progetto
        exclude_dependencies: Ignora le dipendenze nella selezione

    Returns:
        Dict contenente il prossimo task consigliato
    """
    try:
        logger.info(f"Finding next task for project: {project_root}")

        # Load tasks using database manager (consistent with _list_tasks_internal)
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=False)
        
        if not tasks_dict:
            return {
                "error": "No tasks file found",
                "next_task": None,
                "project_root": project_root,
            }

        # Convert dict format to Task objects for compatibility
        from shared.models import Task
        tasks = []
        for task_dict in tasks_dict:
            if isinstance(task_dict, dict):
                # Convert to Task object
                task = Task(**task_dict)
                tasks.append(task)
            else:
                tasks.append(task_dict)

        # Find pending tasks
        pending_tasks = [t for t in tasks if t.status == "pending"]

        if not pending_tasks:
            return {
                "message": "No pending tasks found",
                "next_task": None,
                "completed_tasks": len([t for t in tasks if t.status == "done"]),
                "project_root": project_root,
            }

        # If ignoring dependencies, just return highest priority pending task
        if exclude_dependencies:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            pending_tasks.sort(
                key=lambda x: (
                    priority_order.get(x.priority or "medium", 2),
                    x.id or 0,
                ),
                reverse=True,
            )
            next_task = pending_tasks[0]
        else:
            # Find tasks with no unfulfilled dependencies
            done_task_ids = {t.id for t in tasks if t.status == "done"}

            available_tasks = []
            for task in pending_tasks:
                dependencies = task.dependencies or []
                if not dependencies or all(
                    dep_id in done_task_ids for dep_id in dependencies
                ):
                    available_tasks.append(task)

            if not available_tasks:
                return {
                    "message": "No tasks available (pending tasks have unfulfilled dependencies)",
                    "next_task": None,
                    "pending_with_dependencies": len(pending_tasks),
                    "project_root": project_root,
                }

            # Sort by priority and ID
            priority_order = {"high": 3, "medium": 2, "low": 1}
            available_tasks.sort(
                key=lambda x: (
                    priority_order.get(x.priority or "medium", 2),
                    x.id or 0,
                ),
                reverse=True,
            )
            next_task = available_tasks[0]

        logger.info(f"Next task selected: {next_task.id} - {next_task.title}")

        # Convert Task object to dict for JSON serialization
        next_task_dict = (
            next_task.dict()
            if hasattr(next_task, "dict")
            else {
                "id": next_task.id,
                "title": next_task.title,
                "description": next_task.description,
                "status": next_task.status,
                "priority": next_task.priority,
                "type": next_task.type,
            }
        )

        return {
            "next_task": next_task_dict,
            "available_tasks_count": len(pending_tasks),
            "recommendation": f"Task {next_task.id}: {next_task.title}",
            "project_root": project_root,
        }

    except Exception as e:
        logger.error(f"Error finding next task: {str(e)}")
        return {
            "error": f"Failed to find next task: {str(e)}",
            "next_task": None,
            "project_root": project_root,
        }


@mcp.tool()
def validate_tasks_tool(project_root: str) -> Dict[str, Any]:
    """
    Valida la struttura e integrità del file tasks.json.

    Args:
        project_root: Path assoluto alla directory del progetto

    Returns:
        Dict contenente risultati della validazione
    """
    try:
        logger.info(f"Validating tasks file for project: {project_root}")

        # Validate database structure and content
        # Since we're using SQLite now, we validate the database instead of JSON
        is_valid = True
        errors = []
        warnings = []
        
        # Check if database exists and is accessible
        from .database import get_db_manager
        db_manager = get_db_manager(project_root)
        
        try:
            # Try to query the database
            db_manager.get_all_tasks(include_subtasks=False)
        except Exception as e:
            is_valid = False
            errors.append(f"Database validation failed: {str(e)}")

        # Load tasks for statistics
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        stats = get_tasks_statistics(tasks_dict) if tasks_dict else {}

        result = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "statistics": stats,
            "project_root": project_root,
        }

        if is_valid:
            logger.info("Tasks file validation passed")
        else:
            logger.warning(f"Tasks file validation failed: {errors}")

        return result

    except Exception as e:
        logger.error(f"Error validating tasks: {str(e)}")
        return {
            "is_valid": False,
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": [],
            "statistics": {},
            "project_root": project_root,
        }


@mcp.tool()
def init_claude_support_tool(
    project_root: str, include_windsurfrules: bool = True
) -> Dict[str, Any]:
    """
    Inizializza il supporto Claude Code per il progetto.

    Args:
        project_root: Path assoluto alla directory del progetto
        include_windsurfrules: Se generare anche .windsurfrules

    Returns:
        Dict contenente risultati dell'operazione
    """
    try:
        from .claude_code_setup import init_claude_support

        logger.info(
            f"Initializing Claude Code support via MCP tool for: {project_root}"
        )

        result = init_claude_support(
            mcp_instance=mcp,
            project_root=project_root,
            include_windsurfrules=include_windsurfrules,
        )

        return result

    except Exception as e:
        logger.error(f"Error in init_claude_support_tool: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to initialize Claude Code support: {str(e)}",
            "created_files": [],
            "project_root": project_root,
        }


@mcp.tool()
async def parse_prd_tool(
    project_root: str,
    prd_content: str,
    target_tasks_count: int = 10,
    use_research: bool = False,
    use_lts_deps: bool = True,
    overwrite_existing: bool = False,
) -> Dict[str, Any]:
    """
    Parsa un PRD e genera automaticamente task usando l'AI Service.

    Args:
        project_root: Path assoluto alla directory del progetto
        prd_content: Contenuto del PRD da parsare
        target_tasks_count: Numero target di task da generare
        use_research: Se utilizzare funzionalità di ricerca per generazione task
        use_lts_deps: Se preferire versioni LTS delle dipendenze
        overwrite_existing: Se sovrascrivere task esistenti

    Returns:
        Dict contenente risultati dell'operazione e task generati
    """
    try:
        logger.info(f"Parsing PRD for project: {project_root}")

        # Ensure directory structure exists
        ensure_directories_exist(project_root)

        # Check if tasks already exist - use database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        existing_tasks_dict = db_manager.get_all_tasks(include_subtasks=False)
        existing_tasks = existing_tasks_dict if existing_tasks_dict else []

        if existing_tasks and not overwrite_existing:
            return {
                "error": "Tasks file already exists. Use overwrite_existing=True to replace",
                "existing_tasks_count": len(existing_tasks),
                "generated_tasks": [],
                "project_root": project_root,
            }

        # Initialize AI Service
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Prepare prompt for task generation from PRD
        generation_prompt = f"""
Analizza il seguente PRD e genera {target_tasks_count} task di sviluppo ben strutturati.

CONTENUTO PRD:
{prd_content}

ISTRUZIONI:
1. Identifica le funzionalità principali dal PRD
2. Crea task atomici ma significativi
3. Considera dipendenze logiche tra task
4. Includi dettagli implementativi sufficienti
5. Fornisci strategie di test appropriate
6. Stima complessità e ore di lavoro

FORMATO RICHIESTO:
Genera una lista di task JSON, ognuno con:
- title: Titolo chiaro e specifico
- description: Descrizione dettagliata del task
- details: Dettagli implementativi specifici
- test_strategy: Strategia di testing
- priority: high/medium/low
- estimated_hours: Stima ore di lavoro
- complexity_score: 1-10
- dependencies: Array di ID task dipendenti (se applicabile)

Rispondi SOLO con JSON valido contenente array di task.
        """

        # Generate tasks using AI
        logger.info("Generating tasks from PRD using AI Service")
        generation_result = await ai_service.generate_task_with_ai(
            user_prompt=generation_prompt,
            use_research=use_research,
            use_lts_deps=use_lts_deps,
            project_context=f"PRD parsing for {target_tasks_count} tasks",
        )

        # Extract tasks from AI response
        if "error" in generation_result:
            return {
                "error": f"AI generation failed: {generation_result['error']}",
                "generated_tasks": [],
                "project_root": project_root,
            }

        # Parse the generated content
        ai_content = generation_result.get("content", "")
        try:
            # Try to extract JSON from AI response
            import json
            import re

            # Look for JSON array in the response
            json_match = re.search(r"\[.*\]", ai_content, re.DOTALL)
            if json_match:
                generated_tasks_raw = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire content as JSON
                generated_tasks_raw = json.loads(ai_content)

            # Ensure it's a list
            if not isinstance(generated_tasks_raw, list):
                generated_tasks_raw = [generated_tasks_raw]

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "error": f"Failed to parse AI response: {str(e)}",
                "ai_response": (
                    ai_content[:500] + "..." if len(ai_content) > 500 else ai_content
                ),
                "generated_tasks": [],
                "project_root": project_root,
            }

        # Process and format tasks
        generated_tasks = []
        for i, task_data in enumerate(generated_tasks_raw[:target_tasks_count], 1):
            task = {
                "id": i,
                "title": task_data.get("title", f"Generated Task {i}"),
                "description": task_data.get("description", ""),
                "details": task_data.get("details", ""),
                "status": "pending",
                "priority": task_data.get("priority", "medium"),
                "dependencies": task_data.get("dependencies", []),
                "test_strategy": task_data.get("test_strategy", ""),
                "estimated_hours": task_data.get("estimated_hours", 0.0),
                "complexity_score": task_data.get("complexity_score", 5),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            generated_tasks.append(task)

        # Prepare tasks data structure
        tasks_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "source": "PRD parsing via AI",
            "metadata": {
                "target_tasks_count": target_tasks_count,
                "use_research": use_research,
                "use_lts_deps": use_lts_deps,
                "ai_model_used": generation_result.get("model_used", "unknown"),
                "generation_time": generation_result.get("generation_time", 0),
            },
            "tasks": generated_tasks,
        }

        # Save tasks to file
        try:
            save_tasks(project_root, tasks_data)
            logger.info(f"Successfully saved {len(generated_tasks)} generated tasks")
        except Exception as save_error:
            logger.error(f"Failed to save tasks: {save_error}")
            return {
                "error": f"Failed to save tasks: {str(save_error)}",
                "generated_tasks": generated_tasks,
                "project_root": project_root,
            }

        result = {
            "success": True,
            "message": f"Successfully generated {len(generated_tasks)} tasks from PRD",
            "generated_tasks": generated_tasks,
            "generated_tasks_count": len(generated_tasks),
            "overwritten_existing": len(existing_tasks) if overwrite_existing else 0,
            "ai_metadata": {
                "research_used": use_research,
                "lts_deps_used": use_lts_deps,
                "model_used": generation_result.get("model_used", "unknown"),
                "generation_time": generation_result.get("generation_time", 0),
            },
            "project_root": project_root,
        }

        logger.info(
            f"PRD parsing completed successfully: {len(generated_tasks)} tasks generated"
        )
        return result

    except Exception as e:
        logger.error(f"Error parsing PRD: {str(e)}")
        return {
            "error": f"Failed to parse PRD: {str(e)}",
            "generated_tasks": [],
            "project_root": project_root,
        }


@mcp.tool()
def get_cache_metrics_tool(
    project_root: str, include_detailed_stats: bool = True
) -> Dict[str, Any]:
    """
    Ottieni metriche di performance cache e rate limiting dell'AI Service.

    Args:
        project_root: Path assoluto alla directory del progetto
        include_detailed_stats: Includi statistiche dettagliate per tipo di cache

    Returns:
        Dict contenente metriche complete di cache e rate limiting
    """
    try:
        logger.info(f"Getting cache metrics for project: {project_root}")

        # Initialize AI Service to get cache manager
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Get base metrics
        metrics = ai_service.get_cache_metrics()

        # Add detailed stats if requested
        if include_detailed_stats:
            try:
                detailed_stats = ai_service.cache_manager.get_cache_stats_by_type()
                metrics["detailed_cache_stats"] = detailed_stats
            except Exception as e:
                logger.warning(f"Failed to get detailed cache stats: {e}")
                metrics["detailed_cache_stats"] = {"error": f"Failed to get detailed stats: {str(e)}"}

        # Add timestamp and project info
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["project_root"] = project_root

        # Add summary insights
        cache_metrics = metrics.get("cache", {})
        hit_rate = cache_metrics.get("hit_rate", 0)
        total_saved_cost = cache_metrics.get("total_saved_cost", 0)

        insights = []
        if hit_rate > 80:
            insights.append("Excellent cache performance - high hit rate")
        elif hit_rate > 50:
            insights.append("Good cache performance - moderate hit rate")
        elif hit_rate > 20:
            insights.append("Fair cache performance - consider optimizing")
        else:
            insights.append("Low cache performance - review caching strategy")

        if total_saved_cost > 1.0:
            insights.append(f"Significant cost savings: ${total_saved_cost:.2f}")
        elif total_saved_cost > 0.1:
            insights.append(f"Moderate cost savings: ${total_saved_cost:.2f}")

        metrics["insights"] = insights

        logger.info(f"Cache metrics retrieved successfully - hit rate: {hit_rate:.1f}%")
        return {"success": True, "metrics": metrics, "project_root": project_root}

    except Exception as e:
        logger.error(f"Error getting cache metrics: {str(e)}")
        return {
            "error": f"Failed to get cache metrics: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def clear_cache_tool(
    project_root: str, cache_type: Optional[str] = None, confirm: bool = False
) -> Dict[str, Any]:
    """
    Pulisci la cache AI per ottimizzare le performance.

    Args:
        project_root: Path assoluto alla directory del progetto
        cache_type: Tipo di cache da pulire (lts_research, best_practices, task_generation, general) o None per tutto
        confirm: Conferma operazione di pulizia

    Returns:
        Dict contenente risultati dell'operazione di pulizia
    """
    try:
        logger.info(
            f"Cache clear requested for project: {project_root}, type: {cache_type}"
        )

        if not confirm:
            return {
                "error": "Cache clear requires confirmation. Set confirm=True to proceed.",
                "project_root": project_root,
            }

        # Initialize AI Service to get cache manager
        from .ai_service import AIService
        from .cache_manager import CacheType

        ai_service = AIService(project_root=project_root)

        # Map string to CacheType enum
        cache_type_enum = None
        if cache_type:
            cache_type_map = {
                "lts_research": CacheType.LTS_RESEARCH,
                "best_practices": CacheType.BEST_PRACTICES,
                "task_generation": CacheType.TASK_GENERATION,
                "general": CacheType.GENERAL,
            }

            if cache_type not in cache_type_map:
                return {
                    "error": f"Invalid cache type: {cache_type}. Valid types: {list(cache_type_map.keys())}",
                    "project_root": project_root,
                }

            cache_type_enum = cache_type_map[cache_type]

        # Get metrics before clearing
        before_metrics = ai_service.get_cache_metrics()
        before_size = before_metrics.get("cache", {}).get("cache_size", 0)

        # Clear cache
        cleared_count = ai_service.cache_manager.clear_cache(cache_type_enum)

        # Get metrics after clearing
        after_metrics = ai_service.get_cache_metrics()
        after_size = after_metrics.get("cache", {}).get("cache_size", 0)

        result = {
            "success": True,
            "message": f"Successfully cleared {cleared_count} cache entries",
            "cache_type_cleared": cache_type or "all",
            "entries_cleared": cleared_count,
            "cache_size_before": before_size,
            "cache_size_after": after_size,
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
        }

        logger.info(f"Cache cleared successfully: {cleared_count} entries removed")
        return result

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {
            "error": f"Failed to clear cache: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def check_rate_limits_tool(
    project_root: str, provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Controlla lo stato dei rate limits e fornisce istruzioni per la configurazione.

    Args:
        project_root: Path assoluto alla directory del progetto
        provider: Provider specifico da controllare (openai, anthropic, perplexity, etc.) o None per tutti

    Returns:
        Dict contenente stato rate limits e istruzioni configurazione
    """
    try:
        logger.info(
            f"Checking rate limits for project: {project_root}, provider: {provider}"
        )

        # Initialize AI Service to get cache manager
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Get current metrics
        metrics = ai_service.get_cache_metrics()
        rate_limits = metrics.get("rate_limits", {})

        if not rate_limits:
            return {
                "message": "No rate limit data available yet. Make some AI calls first.",
                "rate_limits": {},
                "project_root": project_root,
            }

        # Filter by provider if specified
        if provider:
            rate_limits = {
                k: v for k, v in rate_limits.items() if v["provider"] == provider
            }

            if not rate_limits:
                return {
                    "error": f"No rate limit data found for provider: {provider}",
                    "available_providers": list(
                        set(
                            v["provider"]
                            for v in metrics.get("rate_limits", {}).values()
                        )
                    ),
                    "project_root": project_root,
                }

        # Check each rate limit and get messages
        status_messages = []
        configuration_tips = []
        warnings = []

        for rate_key, rate_info in rate_limits.items():
            provider_name = rate_info["provider"]
            model_name = rate_info["model"]

            # Get user-friendly message
            rate_msg = ai_service.cache_manager.get_rate_limit_message(
                provider_name, model_name
            )
            if rate_msg:
                if "Rate limit reached" in rate_msg:
                    warnings.append(rate_msg)
                else:
                    status_messages.append(rate_msg)

            # Add configuration tips
            usage_pct = rate_info.get("usage_percentage", 0)
            if usage_pct > 50:  # Show tips for providers with >50% usage
                daily_var = f"PYTASKAI_{provider_name.upper()}_DAILY_LIMIT"
                minute_var = f"PYTASKAI_{provider_name.upper()}_MINUTE_LIMIT"
                current_daily = rate_info.get("daily_limit", 1000)
                current_minute = rate_info.get("minute_limit", 60)

                config_tip = {
                    "provider": provider_name,
                    "model": model_name,
                    "current_usage": f"{rate_info.get('calls_count', 0)}/{current_daily} calls ({usage_pct:.1f}%)",
                    "recommended_config": [
                        f"export {daily_var}={current_daily * 2}  # Double daily limit",
                        f"export {minute_var}={current_minute * 2}  # Double minute limit",
                    ],
                    "alternative_models": self._get_alternative_models(provider_name),
                }
                configuration_tips.append(config_tip)

        # Prepare result
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "rate_limits_summary": rate_limits,
            "status_messages": status_messages,
            "warnings": warnings,
            "configuration_tips": configuration_tips,
            "project_root": project_root,
        }

        # Add overall recommendations
        recommendations = []
        if warnings:
            recommendations.append(
                "🚨 URGENT: Some providers have reached rate limits. Configure higher limits immediately."
            )
        elif status_messages:
            recommendations.append(
                "⚠️  Some providers are approaching limits. Consider increasing limits proactively."
            )
        else:
            recommendations.append("✅ All rate limits are healthy.")

        # Add general configuration guide
        recommendations.append(
            "💡 To modify rate limits, set environment variables and restart the application."
        )
        recommendations.append(
            "📖 See MCP_CONFIGURATION.md for complete configuration guide."
        )

        result["recommendations"] = recommendations

        logger.info(
            f"Rate limits checked: {len(rate_limits)} providers, {len(warnings)} warnings"
        )
        return result

    except Exception as e:
        logger.error(f"Error checking rate limits: {str(e)}")
        return {
            "error": f"Failed to check rate limits: {str(e)}",
            "project_root": project_root,
        }


def _get_alternative_models(provider: str) -> List[str]:
    """Get alternative models for a provider to suggest for rate limiting."""
    alternatives = {
        "openai": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"],
        "anthropic": [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ],
        "perplexity": [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
        ],
        "google": ["gemini-1.5-flash", "gemini-1.5-pro"],
        "xai": ["grok-beta"],
    }
    return alternatives.get(provider, [])


@mcp.tool()
def get_usage_stats_tool(
    project_root: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[str] = None,
    operation_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ottieni statistiche dettagliate di utilizzo AI con breakdown per provider e operazioni.

    Args:
        project_root: Path assoluto alla directory del progetto
        start_date: Data inizio filtro (ISO format: YYYY-MM-DD)
        end_date: Data fine filtro (ISO format: YYYY-MM-DD)
        provider: Provider specifico da analizzare (openai, anthropic, etc.)
        operation_type: Tipo operazione (lts_research, best_practices, task_generation, etc.)

    Returns:
        Dict contenente statistiche complete di utilizzo
    """
    try:
        logger.info(f"Getting usage stats for project: {project_root}")

        # Initialize AI Service to get usage tracker
        from .ai_service import AIService
        from dataclasses import asdict

        ai_service = AIService(project_root=project_root)

        # Parse dates if provided
        kwargs = {}
        if start_date:
            kwargs["start_date"] = datetime.fromisoformat(start_date)
        if end_date:
            kwargs["end_date"] = datetime.fromisoformat(end_date)
        if provider:
            kwargs["provider"] = provider
        if operation_type:
            from .usage_tracker import OperationType

            try:
                kwargs["operation_type"] = OperationType(operation_type)
            except ValueError:
                return {
                    "error": f"Invalid operation type: {operation_type}. Valid types: {[ot.value for ot in OperationType]}",
                    "project_root": project_root,
                }

        # Get statistics
        stats = ai_service.get_usage_stats(**kwargs)

        # Add efficiency metrics
        efficiency_metrics = ai_service.usage_tracker.get_efficiency_metrics()

        # Get budget status
        budget_status = ai_service.get_budget_status()

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "provider": provider,
                "operation_type": operation_type,
            },
            "usage_stats": asdict(stats),
            "efficiency_metrics": efficiency_metrics,
            "budget_status": budget_status,
            "project_root": project_root,
        }

        # Add insights
        insights = []

        if stats.total_cost > 0:
            insights.append(f"💰 Total cost: ${stats.total_cost:.4f}")
            if stats.estimated_monthly_cost > 0:
                insights.append(
                    f"📊 Estimated monthly: ${stats.estimated_monthly_cost:.2f}"
                )

        if stats.cache_hit_rate > 0:
            insights.append(f"🎯 Cache hit rate: {stats.cache_hit_rate:.1f}%")

        if stats.most_used_model:
            insights.append(f"🔧 Most used model: {stats.most_used_model}")

        if stats.most_expensive_operation:
            insights.append(
                f"💸 Most expensive operation: {stats.most_expensive_operation}"
            )

        # Budget insights
        if budget_status["daily"]["status"] != "ok":
            insights.append(f"⚠️ Daily budget: {budget_status['daily']['status']}")

        if budget_status["monthly"]["status"] != "ok":
            insights.append(f"⚠️ Monthly budget: {budget_status['monthly']['status']}")

        result["insights"] = insights

        logger.info(
            f"Usage stats retrieved: {stats.total_calls} calls, ${stats.total_cost:.4f}"
        )
        return result

    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        return {
            "error": f"Failed to get usage stats: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def check_budget_status_tool(project_root: str) -> Dict[str, Any]:
    """
    Controlla stato budget AI e fornisce raccomandazioni per ottimizzazione costi.

    Args:
        project_root: Path assoluto alla directory del progetto

    Returns:
        Dict contenente stato budget e raccomandazioni
    """
    try:
        logger.info(f"Checking budget status for project: {project_root}")

        # Initialize AI Service to get usage tracker
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Get budget status
        budget_status = ai_service.get_budget_status()

        # Get efficiency metrics for additional insights
        efficiency_metrics = ai_service.usage_tracker.get_efficiency_metrics()

        # Get top models by cost
        top_models = ai_service.usage_tracker.get_top_models_by_cost(5)

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "budget_status": budget_status,
            "efficiency_metrics": efficiency_metrics,
            "top_models_by_cost": top_models,
            "project_root": project_root,
        }

        # Add quick summary
        daily = budget_status["daily"]
        monthly = budget_status["monthly"]

        summary = []
        summary.append(
            f"💰 Daily: ${daily['spent']:.4f} / ${daily['budget']:.2f} ({daily['usage_percentage']:.1f}%)"
        )
        summary.append(
            f"📅 Monthly: ${monthly['spent']:.4f} / ${monthly['budget']:.2f} ({monthly['usage_percentage']:.1f}%)"
        )

        if efficiency_metrics.get("cache_hit_rate", 0) > 0:
            summary.append(
                f"🎯 Cache hit rate: {efficiency_metrics['cache_hit_rate']:.1f}%"
            )

        if top_models:
            most_expensive = top_models[0]
            summary.append(
                f"💸 Most expensive: {most_expensive[0]} (${most_expensive[1]:.4f})"
            )

        result["summary"] = summary

        logger.info(
            f"Budget status checked: daily {daily['status']}, monthly {monthly['status']}"
        )
        return result

    except Exception as e:
        logger.error(f"Error checking budget status: {str(e)}")
        return {
            "error": f"Failed to check budget status: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def set_task_status_tool(
    project_root: str,
    task_id: Union[int, str],
    new_status: str,
    subtask_id: Optional[Union[int, str]] = None,
    update_timestamp: bool = True,
) -> Dict[str, Any]:
    """
    Aggiorna lo stato di un task o subtask specifico.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task da aggiornare
        new_status: Nuovo stato (pending, in-progress, done, cancelled, review, deferred)
        subtask_id: ID del subtask da aggiornare (opzionale, per aggiornare un subtask)
        update_timestamp: Se aggiornare automaticamente il timestamp updated_at

    Returns:
        Dict contenente risultato dell'operazione
    """
    try:
        logger.info(
            f"Setting task status for project: {project_root}, task_id: {task_id}, status: {new_status}"
        )

        # Validate status
        valid_statuses = [
            "pending",
            "in-progress",
            "done",
            "cancelled",
            "review",
            "deferred",
        ]
        if new_status not in valid_statuses:
            return {
                "error": f"Invalid status: {new_status}. Valid statuses: {valid_statuses}",
                "task_id": task_id,
                "project_root": project_root,
            }

        # Get database manager
        from .database import get_db_manager

        db_manager = get_db_manager(project_root)
        task_id = int(task_id)

        # Get the target task
        target_task = db_manager.get_task_by_id(task_id)
        if not target_task:
            return {
                "error": f"Task with ID {task_id} not found",
                "task_id": task_id,
                "project_root": project_root,
            }

        # Prepare update information
        old_status = None
        update_target = "task"

        # Handle subtask update
        if subtask_id is not None:
            subtask_id = int(subtask_id)

            # Find the subtask to update
            subtask_found = False
            for subtask in target_task.get("subtasks", []):
                if subtask.get("id") == subtask_id:
                    old_status = subtask.get("status")
                    subtask_found = True
                    update_target = f"subtask {subtask_id}"
                    break

            if not subtask_found:
                return {
                    "error": f"Subtask with ID {subtask_id} not found in task {task_id}",
                    "task_id": task_id,
                    "subtask_id": subtask_id,
                    "project_root": project_root,
                }

            # Update subtask using database manager
            update_data = {"status": new_status}
            if update_timestamp:
                update_data["updated_at"] = datetime.now()

            updated_task = db_manager.update_subtask(task_id, subtask_id, update_data)
            if not updated_task:
                return {
                    "error": f"Failed to update subtask {subtask_id}",
                    "task_id": task_id,
                    "subtask_id": subtask_id,
                    "project_root": project_root,
                }

        else:
            # Update main task
            old_status = target_task.get("status")

            update_data = {"status": new_status}
            if update_timestamp:
                update_data["updated_at"] = datetime.now()

            updated_task = db_manager.update_task(task_id, update_data)
            if not updated_task:
                return {
                    "error": f"Failed to update task {task_id}",
                    "task_id": task_id,
                    "project_root": project_root,
                }

        logger.info(
            f"Successfully updated {update_target} status from '{old_status}' to '{new_status}'"
        )

        # Prepare success response
        result = {
            "success": True,
            "message": f"Successfully updated {update_target} status from '{old_status}' to '{new_status}'",
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": datetime.now().isoformat(),
            "project_root": project_root,
        }

        if subtask_id is not None:
            result["subtask_id"] = subtask_id

        # Add task context to response
        task_context = {
            "title": target_task.get("title"),
            "description": target_task.get("description"),
            "priority": target_task.get("priority"),
        }
        result["task_context"] = task_context

        # Add status progression insights
        status_progression = []
        if old_status == "pending" and new_status == "in-progress":
            status_progression.append("✅ Task started - work in progress")
        elif old_status == "in-progress" and new_status == "done":
            status_progression.append("🎉 Task completed successfully")
        elif old_status in ["pending", "in-progress"] and new_status == "review":
            status_progression.append("🔍 Task ready for review")
        elif new_status == "cancelled":
            status_progression.append("❌ Task cancelled")
        elif new_status == "deferred":
            status_progression.append("⏰ Task deferred for later")

        if status_progression:
            result["status_progression"] = status_progression

        logger.info(f"Task status update completed: {task_id} -> {new_status}")
        return result

    except ValueError as ve:
        logger.error(f"Value error in set_task_status: {str(ve)}")
        return {
            "error": f"Invalid input: {str(ve)}",
            "task_id": task_id,
            "project_root": project_root,
        }
    except Exception as e:
        logger.error(f"Error setting task status: {str(e)}")
        return {
            "error": f"Failed to set task status: {str(e)}",
            "task_id": task_id,
            "project_root": project_root,
        }


@mcp.tool()
async def add_task_tool(
    project_root: str,
    prompt: str,
    use_research: bool = False,
    use_lts_deps: bool = True,
    priority: str = "medium",
    target_task_id: Optional[int] = None,
    dependencies: Optional[str] = None,
    task_type: str = "task",
    severity: Optional[str] = None,
    steps_to_reproduce: Optional[str] = None,
    expected_result: Optional[str] = None,
    actual_result: Optional[str] = None,
    environment: Optional[str] = None,
    target_test_coverage: Optional[float] = None,
    related_tests: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Aggiunge un nuovo task principale utilizzando AI (LiteLLM) con supporto ricerca e best practices.

    Supporta sia task generici che bug tracking con campi specifici per debugging.

    Args:
        project_root: Path assoluto alla directory del progetto
        prompt: Descrizione del task da creare
        use_research: Se utilizzare ricerca attiva per LTS e best practices
        use_lts_deps: Se preferire versioni LTS delle dipendenze
        priority: Priorità del task (high, medium, low)
        target_task_id: ID specifico da assegnare al task (opzionale)
        dependencies: Lista dipendenze come stringa comma-separated (es: "1,2,3")
        task_type: Tipo di task (task, bug, feature, enhancement, research, documentation)
        severity: Severità del bug (critical, high, medium, low) - solo per bugs
        steps_to_reproduce: Passi per riprodurre il bug - solo per bugs
        expected_result: Comportamento atteso - solo per bugs
        actual_result: Comportamento osservato - solo per bugs
        environment: Ambiente dove si verifica il bug - solo per bugs
        target_test_coverage: Copertura test target (0-100%) - opzionale
        related_tests: Lista test correlati come stringa comma-separated

    Returns:
        Dict contenente il task creato e metadati dell'operazione
    """
    try:
        # Validate project_root parameter
        if not project_root or project_root == "":
            project_root = "."

        # Ensure project_root is absolute and valid
        import os

        if not os.path.isabs(project_root):
            project_root = os.path.abspath(project_root)

        logger.info(f"Creating new task for project: {project_root}")
        logger.info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        logger.info(
            f"Research: {use_research}, LTS: {use_lts_deps}, Priority: {priority}"
        )

        # Validazione parametri
        valid_priorities = ["highest", "high", "medium", "low", "lowest"]
        if priority not in valid_priorities:
            return {
                "error": f"Invalid priority: {priority}. Valid priorities: {valid_priorities}",
                "project_root": project_root,
            }

        valid_task_types = [
            "task",
            "bug",
            "feature",
            "enhancement",
            "research",
            "documentation",
        ]
        if task_type not in valid_task_types:
            return {
                "error": f"Invalid task_type: {task_type}. Valid types: {valid_task_types}",
                "project_root": project_root,
            }

        # Validate bug-specific fields
        if task_type == "bug":
            if severity:
                valid_severities = ["critical", "high", "medium", "low"]
                if severity not in valid_severities:
                    return {
                        "error": f"Invalid severity: {severity}. Valid severities: {valid_severities}",
                        "project_root": project_root,
                    }

        # Validate test coverage
        if target_test_coverage is not None:
            if not (0 <= target_test_coverage <= 100):
                return {
                    "error": f"Invalid target_test_coverage: {target_test_coverage}. Must be between 0 and 100",
                    "project_root": project_root,
                }

        # Load existing tasks to determine next ID - use database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        existing_tasks_dict = db_manager.get_all_tasks(include_subtasks=False)
        
        if existing_tasks_dict:
            existing_tasks = existing_tasks_dict
            data = {
                "version": "1.0",
                "tasks": existing_tasks,
                "metadata": {
                    "generator": "PyTaskAI",
                    "last_updated": datetime.now().isoformat(),
                    "total_tasks": len(existing_tasks),
                },
            }
        else:
            # Initialize empty tasks structure
            existing_tasks = []
            data = {
                "version": "1.0",
                "tasks": [],
                "metadata": {
                    "generator": "PyTaskAI",
                    "created_at": datetime.now().isoformat(),
                },
            }

        # Determine next task ID
        if target_task_id:
            # Check if target ID already exists
            if any(t.get("id") == target_task_id for t in existing_tasks):
                return {
                    "error": f"Task ID {target_task_id} already exists",
                    "project_root": project_root,
                }
            next_id = target_task_id
        else:
            # Auto-assign next available ID
            max_id = max([t.get("id", 0) for t in existing_tasks], default=0)
            next_id = max_id + 1

        # Parse dependencies
        parsed_dependencies = []
        if dependencies:
            try:
                dep_ids = [
                    int(dep.strip()) for dep in dependencies.split(",") if dep.strip()
                ]

                # Validate that all dependencies exist
                existing_ids = {t.get("id") for t in existing_tasks}
                invalid_deps = [
                    dep_id for dep_id in dep_ids if dep_id not in existing_ids
                ]

                if invalid_deps:
                    return {
                        "error": f"Invalid dependency IDs: {invalid_deps}. These tasks do not exist.",
                        "existing_task_ids": list(existing_ids),
                        "project_root": project_root,
                    }

                parsed_dependencies = dep_ids

            except ValueError as e:
                return {
                    "error": f"Invalid dependencies format: {dependencies}. Use comma-separated numbers (e.g., '1,2,3')",
                    "project_root": project_root,
                }

        # Parse related tests
        parsed_related_tests = []
        if related_tests:
            parsed_related_tests = [
                test.strip() for test in related_tests.split(",") if test.strip()
            ]

        # Extract information for research if enabled
        mentioned_technologies = []
        topic_for_best_practices = ""

        if use_research:
            # Simple extraction logic - in a real implementation this could be more sophisticated
            # Extract technology mentions (common patterns)
            import re

            tech_patterns = [
                r"\b(React|Vue|Angular|Svelte|Next\.js|Nuxt|Gatsby)\b",
                r"\b(Node\.js|Express|Fastify|Koa|Deno|Bun)\b",
                r"\b(Python|FastAPI|Django|Flask|Tornado)\b",
                r"\b(TypeScript|JavaScript|Go|Rust|Java|C\#)\b",
                r"\b(Docker|Kubernetes|AWS|GCP|Azure)\b",
                r"\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite)\b",
                r"\b(Git|GitHub|GitLab|CI/CD|Jenkins)\b",
            ]

            for pattern in tech_patterns:
                matches = re.findall(pattern, prompt, re.IGNORECASE)
                mentioned_technologies.extend([match.lower() for match in matches])

            # Remove duplicates
            mentioned_technologies = list(set(mentioned_technologies))

            # Extract topic for best practices (first sentence or key phrase)
            sentences = prompt.split(".")
            if sentences:
                topic_for_best_practices = sentences[0].strip()

            logger.info(f"Extracted technologies: {mentioned_technologies}")
            logger.info(f"Best practices topic: {topic_for_best_practices}")

        # Initialize AI Service
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Generate task using AI
        logger.info("Generating task with AI Service")

        generation_result = await ai_service.generate_task_with_ai(
            user_prompt=prompt,
            use_research=use_research,
            use_lts_deps=use_lts_deps,
            mentioned_technologies=mentioned_technologies,
            topic_for_best_practices=topic_for_best_practices,
            project_context=f"Adding task to project with {len(existing_tasks)} existing tasks",
        )

        # Check for AI generation errors
        if "error" in generation_result:
            return {
                "error": f"AI task generation failed: {generation_result['error']}",
                "generation_details": generation_result,
                "project_root": project_root,
            }

        # Extract generated content
        ai_content = generation_result.get("content", "")
        if not ai_content:
            return {
                "error": "AI generated empty content",
                "generation_result": generation_result,
                "project_root": project_root,
            }

        # Parse AI generated task data
        try:
            # Try to extract JSON from AI response
            import json
            import re

            # Look for JSON object in the response
            json_match = re.search(r"\{.*\}", ai_content, re.DOTALL)
            if json_match:
                task_data = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire content as JSON
                task_data = json.loads(ai_content)

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")

            # Fallback: create task from prompt
            task_data = {
                "title": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "description": prompt,
                "details": "Task created from user prompt. AI parsing failed.",
                "test_strategy": "Manual testing required.",
                "estimated_hours": 2.0,
                "complexity_score": 5,
            }

        # Create new task with proper structure
        new_task = {
            "id": next_id,
            "title": task_data.get(
                "title", prompt[:50] + "..." if len(prompt) > 50 else prompt
            ),
            "description": task_data.get("description", prompt),
            "details": task_data.get("details", ""),
            "status": "pending",
            "priority": priority,
            "type": task_type,
            "dependencies": parsed_dependencies,
            "test_strategy": task_data.get("test_strategy", ""),
            "estimated_hours": task_data.get("estimated_hours", 0.0),
            "complexity_score": task_data.get("complexity_score", 5),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "subtasks": [],
            "attachments": [],
            "related_tests": parsed_related_tests,
        }

        # Add bug-specific fields if it's a bug
        if task_type == "bug":
            new_task.update(
                {
                    "severity": severity,
                    "steps_to_reproduce": steps_to_reproduce,
                    "expected_result": expected_result,
                    "actual_result": actual_result,
                    "environment": environment,
                }
            )

        # Add test coverage fields if specified
        if target_test_coverage is not None:
            new_task["target_test_coverage"] = target_test_coverage

        # Add AI generation metadata
        if "model_used" in generation_result:
            new_task["ai_metadata"] = {
                "model_used": generation_result["model_used"],
                "research_used": use_research,
                "lts_deps_used": use_lts_deps,
                "mentioned_technologies": mentioned_technologies,
                "generation_time": generation_result.get("generation_time", 0),
                "generation_cost": generation_result.get("cost", 0),
            }

        # Add task to data structure
        data["tasks"].append(new_task)
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        data["metadata"]["total_tasks"] = len(data["tasks"])

        # Save updated tasks
        try:
            # Convert dict tasks to Task objects for save_tasks function
            task_objects = []
            for task_dict in data["tasks"]:
                # Add missing fields with defaults if needed
                if "subtasks" not in task_dict:
                    task_dict["subtasks"] = []
                # Create Task object - this will handle validation
                from shared.models import Task

                task_obj = Task(**task_dict)
                task_objects.append(task_obj)

            save_tasks(task_objects, project_root)
            logger.info(f"Successfully created task {next_id}: {new_task['title']}")
        except Exception as save_error:
            logger.error(f"Failed to save new task: {save_error}")
            return {
                "error": f"Failed to save new task: {str(save_error)}",
                "generated_task": new_task,
                "project_root": project_root,
            }

        # Prepare success response
        result = {
            "success": True,
            "message": f"Successfully created task {next_id}: {new_task['title']}",
            "task": new_task,
            "task_id": next_id,
            "ai_generation": {
                "research_used": use_research,
                "lts_deps_used": use_lts_deps,
                "model_used": generation_result.get("model_used", "unknown"),
                "generation_time": generation_result.get("generation_time", 0),
                "cost": generation_result.get("cost", 0),
            },
            "project_stats": {
                "total_tasks": len(data["tasks"]),
                "new_task_position": next_id,
            },
            "project_root": project_root,
        }

        # Add research insights if used
        if use_research and mentioned_technologies:
            result["research_insights"] = {
                "technologies_found": mentioned_technologies,
                "best_practices_topic": topic_for_best_practices,
            }

        logger.info(f"Task creation completed successfully: ID {next_id}")
        return result

    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "error": f"Failed to create task: {str(e)}",
            "prompt": prompt,
            "project_root": project_root,
        }


@mcp.tool()
def update_task_test_coverage_tool(
    project_root: str,
    task_id: int,
    achieved_coverage: Optional[float] = None,
    test_report_url: Optional[str] = None,
    test_results_summary: Optional[str] = None,
    tests_passed: Optional[bool] = None,
    total_tests: Optional[int] = None,
    failed_tests: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Aggiorna i dati di copertura test per un task specifico.

    Questo tool dovrebbe essere usato dall'agente di coding dopo aver eseguito i test,
    per riportare i risultati e aggiornare lo stato del task.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task da aggiornare
        achieved_coverage: Percentuale di copertura raggiunta (0-100)
        test_report_url: URL o path al report di copertura
        test_results_summary: Riassunto testuale dei risultati dei test
        tests_passed: Se tutti i test sono passati
        total_tests: Numero totale di test eseguiti
        failed_tests: Numero di test falliti

    Returns:
        Dict contenente conferma dell'aggiornamento e stato del task
    """
    try:
        logger.info(f"Updating test coverage for task {task_id}")

        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {
                "error": "No tasks file found",
                "project_root": project_root,
            }

        tasks = [
            task.model_dump() if hasattr(task, "model_dump") else task for task in data
        ]
        task = None
        task_index = None

        for i, t in enumerate(tasks):
            if t.get("id") == task_id:
                task = t
                task_index = i
                break

        if not task:
            return {
                "error": f"Task {task_id} not found",
                "project_root": project_root,
            }

        # Update test coverage fields
        now = datetime.now().isoformat()
        updated_fields = []

        if achieved_coverage is not None:
            if not (0 <= achieved_coverage <= 100):
                return {
                    "error": f"Invalid achieved_coverage: {achieved_coverage}. Must be between 0 and 100",
                    "project_root": project_root,
                }
            task["achieved_test_coverage"] = achieved_coverage
            updated_fields.append("achieved_test_coverage")

        if test_report_url is not None:
            task["test_report_url"] = test_report_url
            updated_fields.append("test_report_url")

        if test_results_summary is not None:
            if "test_metadata" not in task:
                task["test_metadata"] = {}
            task["test_metadata"]["results_summary"] = test_results_summary
            updated_fields.append("test_results_summary")

        if tests_passed is not None:
            if "test_metadata" not in task:
                task["test_metadata"] = {}
            task["test_metadata"]["tests_passed"] = tests_passed
            updated_fields.append("tests_passed")

        if total_tests is not None:
            if "test_metadata" not in task:
                task["test_metadata"] = {}
            task["test_metadata"]["total_tests"] = total_tests
            updated_fields.append("total_tests")

        if failed_tests is not None:
            if "test_metadata" not in task:
                task["test_metadata"] = {}
            task["test_metadata"]["failed_tests"] = failed_tests
            updated_fields.append("failed_tests")

        # Update timestamp
        task["updated_at"] = now

        # Check if target coverage is met
        target_coverage = task.get("target_test_coverage")
        coverage_status = "not_measured"

        if achieved_coverage is not None:
            if target_coverage is not None:
                if achieved_coverage >= target_coverage:
                    coverage_status = "target_met"
                else:
                    coverage_status = "target_not_met"
            else:
                coverage_status = "measured"

        # Save updated tasks
        from shared.models import Task

        updated_tasks = []
        for t in tasks:
            try:
                updated_tasks.append(Task(**t))
            except Exception as e:
                logger.warning(
                    f"Failed to convert task {t.get('id')} to Task object: {e}"
                )
                updated_tasks.append(t)

        success = save_tasks(project_root, updated_tasks)

        if not success:
            return {
                "error": "Failed to save updated task",
                "project_root": project_root,
            }

        logger.info(f"Successfully updated test coverage for task {task_id}")

        return {
            "success": True,
            "message": f"Successfully updated test coverage for task {task_id}",
            "task_id": task_id,
            "updated_fields": updated_fields,
            "coverage_status": coverage_status,
            "achieved_coverage": achieved_coverage,
            "target_coverage": target_coverage,
            "timestamp": now,
            "project_root": project_root,
        }

    except Exception as e:
        logger.error(f"Error updating test coverage: {str(e)}")
        return {
            "error": f"Failed to update test coverage: {str(e)}",
            "task_id": task_id,
            "project_root": project_root,
        }


@mcp.tool()
async def report_bug_tool(
    project_root: str,
    title: str,
    description: str,
    severity: str = "medium",
    priority: str = "high",
    steps_to_reproduce: Optional[str] = None,
    expected_result: Optional[str] = None,
    actual_result: Optional[str] = None,
    environment: Optional[str] = None,
    related_task_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Strumento dedicato per la segnalazione rapida di bug.

    Semplifica il processo di creazione di bug report con campi pre-configurati
    e validazione specifica per bug tracking.

    Args:
        project_root: Path assoluto alla directory del progetto
        title: Titolo breve del bug
        description: Descrizione dettagliata del problema
        severity: Gravità del bug (critical, high, medium, low)
        priority: Priorità (highest, high, medium, low, lowest)
        steps_to_reproduce: Passi per riprodurre il bug
        expected_result: Comportamento atteso
        actual_result: Comportamento osservato
        environment: Ambiente dove si verifica il bug
        related_task_id: ID del task correlato (opzionale)

    Returns:
        Dict contenente il bug report creato e metadati
    """
    try:
        logger.info(f"Creating bug report: {title[:50]}...")

        # Validate severity
        valid_severities = ["critical", "high", "medium", "low"]
        if severity not in valid_severities:
            return {
                "error": f"Invalid severity: {severity}. Valid severities: {valid_severities}",
                "project_root": project_root,
            }

        # Validate priority
        valid_priorities = ["highest", "high", "medium", "low", "lowest"]
        if priority not in valid_priorities:
            return {
                "error": f"Invalid priority: {priority}. Valid priorities: {valid_priorities}",
                "project_root": project_root,
            }

        # Enhanced description for bug reports
        enhanced_description = description

        if steps_to_reproduce:
            enhanced_description += f"\n\n**Steps to Reproduce:**\n{steps_to_reproduce}"

        if expected_result:
            enhanced_description += f"\n\n**Expected Result:**\n{expected_result}"

        if actual_result:
            enhanced_description += f"\n\n**Actual Result:**\n{actual_result}"

        if environment:
            enhanced_description += f"\n\n**Environment:**\n{environment}"

        if related_task_id:
            enhanced_description += f"\n\n**Related Task:** #{related_task_id}"

        # Set dependencies if related task provided
        dependencies = [related_task_id] if related_task_id else []
        dependencies_str = str(related_task_id) if related_task_id else None

        # Create bug using add_task_tool
        result = await add_task_tool(
            project_root=project_root,
            prompt=enhanced_description,
            task_type="bug",
            severity=severity,
            priority=priority,
            steps_to_reproduce=steps_to_reproduce,
            expected_result=expected_result,
            actual_result=actual_result,
            environment=environment,
            dependencies=dependencies_str,
            use_research=False,  # Bug reports typically don't need research
        )

        if result.get("error"):
            return {
                "error": f"Failed to create bug report: {result['error']}",
                "project_root": project_root,
            }

        # Enhance response with bug-specific information
        bug_id = result.get("task_id")
        bug_data = result.get("task", {})

        # Add bug report metadata
        bug_report_info = {
            "bug_id": bug_id,
            "bug_type": "bug",
            "severity": severity,
            "priority": priority,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "has_reproduction_steps": bool(steps_to_reproduce),
            "has_environment_info": bool(environment),
            "is_related_to_task": bool(related_task_id),
        }

        # Generate bug tracking recommendations
        recommendations = []

        if severity in ["critical", "high"]:
            recommendations.append("High severity bug - consider immediate attention")

        if not steps_to_reproduce:
            recommendations.append(
                "Consider adding reproduction steps for faster debugging"
            )

        if not environment:
            recommendations.append("Add environment details to help with debugging")

        if not expected_result or not actual_result:
            recommendations.append(
                "Clarify expected vs actual behavior for better understanding"
            )

        logger.info(f"Bug report created successfully: #{bug_id}")

        return {
            "success": True,
            "message": f"Bug report created successfully: #{bug_id}",
            "bug_report": bug_report_info,
            "recommendations": recommendations,
            "task": bug_data,
            "project_root": project_root,
        }

    except Exception as e:
        logger.error(f"Error creating bug report: {str(e)}")
        return {
            "error": f"Failed to create bug report: {str(e)}",
            "title": title,
            "project_root": project_root,
        }


@mcp.tool()
def get_bug_statistics_tool(
    project_root: str, include_resolved: bool = False, group_by: str = "severity"
) -> Dict[str, Any]:
    """
    Ottieni statistiche sui bug del progetto.

    Args:
        project_root: Path assoluto alla directory del progetto
        include_resolved: Include bug risolti nelle statistiche
        group_by: Raggruppa per (severity, priority, status, environment)

    Returns:
        Dict contenente statistiche dettagliate sui bug
    """
    try:
        logger.info(f"Generating bug statistics for project: {project_root}")

        # Load all tasks
        result = list_tasks_tool(
            project_root=project_root, type_filter="bug", include_subtasks=False
        )

        if result.get("error"):
            return {
                "error": f"Failed to load bugs: {result['error']}",
                "project_root": project_root,
            }

        bugs = result.get("tasks", [])

        # Filter out resolved bugs if requested
        if not include_resolved:
            bugs = [bug for bug in bugs if bug.get("status") != "done"]

        # Calculate statistics
        total_bugs = len(bugs)

        # Group by requested field
        grouped_stats = {}
        valid_group_fields = ["severity", "priority", "status", "environment"]

        if group_by not in valid_group_fields:
            group_by = "severity"

        for bug in bugs:
            group_value = bug.get(group_by, "unknown")
            if group_value not in grouped_stats:
                grouped_stats[group_value] = {"count": 0, "percentage": 0, "bugs": []}
            grouped_stats[group_value]["count"] += 1
            grouped_stats[group_value]["bugs"].append(
                {
                    "id": bug.get("id"),
                    "title": bug.get("title"),
                    "status": bug.get("status"),
                    "severity": bug.get("severity"),
                    "created_at": bug.get("created_at"),
                }
            )

        # Calculate percentages
        for group_value, stats in grouped_stats.items():
            stats["percentage"] = (stats["count"] / max(total_bugs, 1)) * 100

        # Calculate severity distribution (always include this)
        severity_distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }

        for bug in bugs:
            severity = bug.get("severity", "unknown")
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

        # Calculate status distribution
        status_distribution = {}
        for bug in bugs:
            status = bug.get("status", "unknown")
            status_distribution[status] = status_distribution.get(status, 0) + 1

        # Find oldest unresolved bugs
        unresolved_bugs = [
            bug for bug in bugs if bug.get("status") not in ["done", "cancelled"]
        ]
        oldest_bugs = sorted(unresolved_bugs, key=lambda x: x.get("created_at", ""))[:5]

        # Calculate metrics
        critical_high_count = severity_distribution.get(
            "critical", 0
        ) + severity_distribution.get("high", 0)
        resolution_rate = 0
        if include_resolved:
            all_bugs_result = list_tasks_tool(
                project_root=project_root, type_filter="bug"
            )
            all_bugs = all_bugs_result.get("tasks", [])
            resolved_bugs = len([b for b in all_bugs if b.get("status") == "done"])
            resolution_rate = (resolved_bugs / max(len(all_bugs), 1)) * 100

        logger.info(f"Bug statistics generated: {total_bugs} bugs analyzed")

        return {
            "success": True,
            "statistics": {
                "total_bugs": total_bugs,
                "critical_high_count": critical_high_count,
                "resolution_rate": resolution_rate,
                "grouped_by": group_by,
                "grouped_stats": grouped_stats,
                "severity_distribution": severity_distribution,
                "status_distribution": status_distribution,
                "oldest_unresolved": oldest_bugs,
            },
            "metadata": {
                "include_resolved": include_resolved,
                "generated_at": datetime.now().isoformat(),
                "project_root": project_root,
            },
        }

    except Exception as e:
        logger.error(f"Error generating bug statistics: {str(e)}")
        return {
            "error": f"Failed to generate bug statistics: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
async def expand_task_tool(
    project_root: str,
    task_id: Union[int, str],
    use_research: bool = False,
    use_lts_deps: bool = True,
    target_subtasks_count: int = 5,
    additional_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Espande un task esistente in subtask utilizzando AI (LiteLLM) con supporto ricerca e best practices.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task da espandere in subtask
        use_research: Se utilizzare ricerca attiva per LTS e best practices
        use_lts_deps: Se preferire versioni LTS delle dipendenze
        target_subtasks_count: Numero target di subtask da generare (default: 5)
        additional_context: Contesto aggiuntivo per la generazione subtask

    Returns:
        Dict contenente i subtask generati e metadati dell'operazione
    """
    try:
        logger.info(f"Expanding task {task_id} for project: {project_root}")
        logger.info(
            f"Research: {use_research}, LTS: {use_lts_deps}, Target count: {target_subtasks_count}"
        )

        # Load existing tasks
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {
                "error": "No tasks file found",
                "task_id": task_id,
                "project_root": project_root,
            }

        tasks = data  # data is already a list of task dictionaries
        task_id = int(task_id)

        # Find the target task
        target_task = None
        task_index = None

        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                target_task = task
                task_index = i
                break

        if not target_task:
            return {
                "error": f"Task with ID {task_id} not found",
                "task_id": task_id,
                "project_root": project_root,
            }

        # Check if task already has subtasks
        existing_subtasks = target_task.get("subtasks", [])
        if existing_subtasks:
            logger.warning(
                f"Task {task_id} already has {len(existing_subtasks)} subtasks"
            )

        # Prepare task content for AI generation
        task_content = {
            "title": target_task.get("title", ""),
            "description": target_task.get("description", ""),
            "details": target_task.get("details", ""),
            "test_strategy": target_task.get("test_strategy", ""),
            "priority": target_task.get("priority", "medium"),
            "complexity_score": target_task.get("complexity_score", 5),
            "estimated_hours": target_task.get("estimated_hours", 0),
        }

        # Extract information for research if enabled
        mentioned_technologies = []
        topic_for_best_practices = ""

        if use_research:
            # Extract technology mentions from task content
            import re

            # Combine all task text for analysis
            full_text = f"{task_content['title']} {task_content['description']} {task_content['details']}"
            if additional_context:
                full_text += f" {additional_context}"

            tech_patterns = [
                r"\b(React|Vue|Angular|Svelte|Next\.js|Nuxt|Gatsby)\b",
                r"\b(Node\.js|Express|Fastify|Koa|Deno|Bun)\b",
                r"\b(Python|FastAPI|Django|Flask|Tornado)\b",
                r"\b(TypeScript|JavaScript|Go|Rust|Java|C\#)\b",
                r"\b(Docker|Kubernetes|AWS|GCP|Azure)\b",
                r"\b(PostgreSQL|MySQL|MongoDB|Redis|SQLite)\b",
                r"\b(Git|GitHub|GitLab|CI/CD|Jenkins)\b",
            ]

            for pattern in tech_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                mentioned_technologies.extend([match.lower() for match in matches])

            # Remove duplicates
            mentioned_technologies = list(set(mentioned_technologies))

            # Extract topic for best practices
            topic_for_best_practices = task_content["title"]

            logger.info(f"Extracted technologies: {mentioned_technologies}")
            logger.info(f"Best practices topic: {topic_for_best_practices}")

        # Initialize AI Service
        from .ai_service import AIService

        ai_service = AIService(project_root=project_root)

        # Generate subtasks using AI
        logger.info("Generating subtasks with AI Service")
        # Check if method exists, if not create a wrapper
        if hasattr(ai_service, "generate_subtasks_with_ai"):
            generation_result = await ai_service.generate_subtasks_with_ai(
                task_content=task_content,
                target_subtasks_count=target_subtasks_count,
                use_research=use_research,
                use_lts_deps=use_lts_deps,
                mentioned_technologies=mentioned_technologies,
                topic_for_best_practices=topic_for_best_practices,
                additional_context=additional_context,
            )
        else:
            # Fallback: use generate_task_with_ai with modified prompt
            subtask_prompt = f"""
Espandi il seguente task in {target_subtasks_count} subtask dettagliati e actionable:

TASK DA ESPANDERE:
Titolo: {task_content['title']}
Descrizione: {task_content['description']}
Dettagli: {task_content['details']}
Test Strategy: {task_content['test_strategy']}
Priorità: {task_content['priority']}
Complessità: {task_content['complexity_score']}/10

{f"CONTESTO AGGIUNTIVO: {additional_context}" if additional_context else ""}

ISTRUZIONI:
1. Crea {target_subtasks_count} subtask che coprano completamente l'implementazione del task principale
2. Ogni subtask deve essere atomic e implementabile indipendentemente
3. Ordina i subtask in sequenza logica di implementazione
4. Includi dettagli implementativi specifici per ogni subtask
5. Considera le dipendenze tra subtask

FORMATO RICHIESTO:
Genera un array JSON di subtask, ognuno con:
- title: Titolo chiaro e specifico del subtask
- description: Descrizione dettagliata di cosa implementare
- details: Dettagli implementativi step-by-step
- test_strategy: Come testare questo specifico subtask
- estimated_hours: Stima ore di lavoro (decimal)
- complexity_score: Complessità 1-10
- dependencies: Array di ID subtask dipendenti (se applicabile)

Rispondi SOLO con JSON valido contenente array di subtask.
            """

            generation_result = await ai_service.generate_task_with_ai(
                user_prompt=subtask_prompt,
                use_research=use_research,
                use_lts_deps=use_lts_deps,
                mentioned_technologies=mentioned_technologies,
                topic_for_best_practices=topic_for_best_practices,
                project_context=f"Expanding task {task_id} into {target_subtasks_count} subtasks",
            )

        # Check for AI generation errors
        if "error" in generation_result:
            return {
                "error": f"AI subtask generation failed: {generation_result['error']}",
                "generation_details": generation_result,
                "task_id": task_id,
                "project_root": project_root,
            }

        # Extract generated content
        ai_content = generation_result.get("content", "")
        if not ai_content:
            return {
                "error": "AI generated empty content for subtasks",
                "generation_result": generation_result,
                "task_id": task_id,
                "project_root": project_root,
            }

        # Parse AI generated subtasks data
        try:
            # Try to extract JSON from AI response
            import json
            import re

            # Look for JSON array in the response
            json_match = re.search(r"\[.*\]", ai_content, re.DOTALL)
            if json_match:
                subtasks_data = json.loads(json_match.group())
            else:
                # Try to find JSON object and wrap in array
                json_match = re.search(r"\{.*\}", ai_content, re.DOTALL)
                if json_match:
                    single_subtask = json.loads(json_match.group())
                    subtasks_data = [single_subtask]
                else:
                    # Fallback: try to parse entire content as JSON
                    subtasks_data = json.loads(ai_content)

            # Ensure it's a list
            if not isinstance(subtasks_data, list):
                subtasks_data = [subtasks_data]

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")

            # Fallback: create basic subtasks from task breakdown
            subtasks_data = [
                {
                    "title": f"Implementazione {task_content['title']} - Parte {i+1}",
                    "description": f"Subtask generato automaticamente per {task_content['title']}",
                    "details": "Dettagli da definire. AI parsing fallito.",
                    "test_strategy": "Test da definire manualmente.",
                    "estimated_hours": 1.0,
                    "complexity_score": 3,
                }
                for i in range(min(target_subtasks_count, 3))
            ]

        # Process and format subtasks
        generated_subtasks = []
        for i, subtask_data in enumerate(subtasks_data[:target_subtasks_count]):
            subtask_id = len(existing_subtasks) + i + 1

            subtask = {
                "id": subtask_id,
                "title": subtask_data.get("title", f"Subtask {subtask_id}"),
                "description": subtask_data.get("description", ""),
                "details": subtask_data.get("details", ""),
                "status": "pending",
                "test_strategy": subtask_data.get("test_strategy", ""),
                "estimated_hours": subtask_data.get("estimated_hours", 0.0),
                "complexity_score": subtask_data.get("complexity_score", 3),
                "dependencies": subtask_data.get("dependencies", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            generated_subtasks.append(subtask)

        # Add subtasks to parent task
        if "subtasks" not in target_task:
            target_task["subtasks"] = []

        target_task["subtasks"].extend(generated_subtasks)
        target_task["updated_at"] = datetime.now().isoformat()

        # Update task metadata if not present
        if "ai_expansion_metadata" not in target_task:
            target_task["ai_expansion_metadata"] = []

        expansion_metadata = {
            "expansion_date": datetime.now().isoformat(),
            "subtasks_generated": len(generated_subtasks),
            "model_used": generation_result.get("model_used", "unknown"),
            "research_used": use_research,
            "lts_deps_used": use_lts_deps,
            "mentioned_technologies": mentioned_technologies,
            "generation_time": generation_result.get("generation_time", 0),
            "generation_cost": generation_result.get("cost", 0),
        }
        target_task["ai_expansion_metadata"].append(expansion_metadata)

        # Save updated tasks
        try:
            save_tasks(project_root, data)
            logger.info(
                f"Successfully expanded task {task_id} with {len(generated_subtasks)} subtasks"
            )
        except Exception as save_error:
            logger.error(f"Failed to save expanded task: {save_error}")
            return {
                "error": f"Failed to save expanded task: {str(save_error)}",
                "generated_subtasks": generated_subtasks,
                "task_id": task_id,
                "project_root": project_root,
            }

        # Prepare success response
        result = {
            "success": True,
            "message": f"Successfully expanded task {task_id} with {len(generated_subtasks)} subtasks",
            "task_id": task_id,
            "task_title": target_task.get("title", "Unknown"),
            "generated_subtasks": generated_subtasks,
            "subtasks_count": len(generated_subtasks),
            "total_subtasks": len(target_task["subtasks"]),
            "ai_generation": {
                "research_used": use_research,
                "lts_deps_used": use_lts_deps,
                "model_used": generation_result.get("model_used", "unknown"),
                "generation_time": generation_result.get("generation_time", 0),
                "cost": generation_result.get("cost", 0),
            },
            "project_root": project_root,
        }

        # Add research insights if used
        if use_research and mentioned_technologies:
            result["research_insights"] = {
                "technologies_found": mentioned_technologies,
                "best_practices_topic": topic_for_best_practices,
            }

        logger.info(
            f"Task expansion completed successfully: {len(generated_subtasks)} subtasks added to task {task_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Error expanding task {task_id}: {str(e)}")
        return {
            "error": f"Failed to expand task: {str(e)}",
            "task_id": task_id,
            "project_root": project_root,
        }


@mcp.tool()
def next_task_tool(
    project_root: str,
    status_filter: Optional[str] = "pending",
    priority_order: Optional[str] = "high,medium,low",
    include_blocked: bool = False,
) -> Dict[str, Any]:
    """
    Suggerisce il prossimo task da affrontare basandosi su dipendenze, priorità e stato.

    Args:
        project_root: Path assoluto alla directory del progetto
        status_filter: Stato dei task da considerare (default: "pending")
        priority_order: Ordine di priorità (default: "high,medium,low")
        include_blocked: Se includere task con dipendenze non completate

    Returns:
        Dict contenente il task suggerito e le informazioni di selezione
    """
    try:
        logger.info(f"Finding next task for project: {project_root}")

        # Load tasks data
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {"error": "No tasks file found", "project_root": project_root}

        tasks = data  # data is already a list of task dictionaries
        if not tasks:
            return {"error": "No tasks available", "project_root": project_root}

        # Parse priority order
        priority_levels = [p.strip() for p in priority_order.split(",")]
        priority_weight = {level: idx for idx, level in enumerate(priority_levels)}

        # Filter tasks by status
        filtered_tasks = []
        for task in tasks:
            if task.get("status", "pending") == status_filter:
                filtered_tasks.append(task)

        if not filtered_tasks:
            return {
                "message": f"No tasks found with status '{status_filter}'",
                "total_tasks": len(tasks),
                "project_root": project_root,
            }

        # Check dependencies and find available tasks
        available_tasks = []
        blocked_tasks = []

        for task in filtered_tasks:
            task_id = task.get("id")
            dependencies = task.get("dependencies", [])

            # Check if all dependencies are completed
            if dependencies:
                deps_completed = True
                pending_deps = []

                for dep_id in dependencies:
                    dep_task = next((t for t in tasks if t.get("id") == dep_id), None)
                    if not dep_task or dep_task.get("status") != "done":
                        deps_completed = False
                        pending_deps.append(dep_id)

                if deps_completed:
                    available_tasks.append(task)
                else:
                    blocked_tasks.append(
                        {"task": task, "pending_dependencies": pending_deps}
                    )
            else:
                # No dependencies - task is available
                available_tasks.append(task)

        # If no available tasks and include_blocked is False
        if not available_tasks and not include_blocked:
            return {
                "message": "No tasks available (all have unmet dependencies)",
                "blocked_count": len(blocked_tasks),
                "blocked_tasks": [
                    {
                        "id": bt["task"]["id"],
                        "title": bt["task"]["title"],
                        "pending_deps": bt["pending_dependencies"],
                    }
                    for bt in blocked_tasks
                ],
                "suggestion": "Consider completing dependency tasks first or set include_blocked=True",
                "project_root": project_root,
            }

        # Choose tasks to rank (available first, then blocked if requested)
        tasks_to_rank = available_tasks[:]
        if include_blocked and blocked_tasks:
            tasks_to_rank.extend([bt["task"] for bt in blocked_tasks])

        # Sort by priority and ID
        def task_sort_key(task):
            priority = task.get("priority", "medium")
            priority_score = priority_weight.get(
                priority, 999
            )  # Unknown priorities go last
            task_id = task.get("id", 999999)
            return (priority_score, task_id)

        sorted_tasks = sorted(tasks_to_rank, key=task_sort_key)

        if not sorted_tasks:
            return {"error": "No suitable tasks found", "project_root": project_root}

        # Select the next task
        next_task = sorted_tasks[0]
        task_id = next_task.get("id")

        # Check if this task is blocked
        is_blocked = task_id in [bt["task"]["id"] for bt in blocked_tasks]
        pending_deps = []
        if is_blocked:
            blocked_info = next(
                (bt for bt in blocked_tasks if bt["task"]["id"] == task_id), None
            )
            if blocked_info:
                pending_deps = blocked_info["pending_dependencies"]

        # Build result
        result = {
            "next_task": {
                "id": next_task.get("id"),
                "title": next_task.get("title"),
                "description": next_task.get("description"),
                "priority": next_task.get("priority", "medium"),
                "status": next_task.get("status"),
                "dependencies": next_task.get("dependencies", []),
                "details": next_task.get("details", ""),
                "test_strategy": next_task.get("testStrategy", ""),
            },
            "selection_info": {
                "total_tasks": len(tasks),
                "filtered_tasks": len(filtered_tasks),
                "available_tasks": len(available_tasks),
                "blocked_tasks": len(blocked_tasks),
                "is_blocked": is_blocked,
                "pending_dependencies": pending_deps,
            },
            "recommendations": [],
            "project_root": project_root,
        }

        # Add recommendations
        if is_blocked:
            result["recommendations"].append(
                f"Task {task_id} has pending dependencies: {pending_deps}. Consider completing these first."
            )

        if len(available_tasks) > 1:
            result["recommendations"].append(
                f"You have {len(available_tasks)} tasks available. This was selected based on priority and ID order."
            )

        if blocked_tasks and not include_blocked:
            result["recommendations"].append(
                f"{len(blocked_tasks)} tasks are blocked by dependencies. Use include_blocked=True to consider them."
            )

        logger.info(f"Next task selected: {task_id} - {next_task.get('title')}")
        return result

    except Exception as e:
        logger.error(f"Error finding next task: {str(e)}")
        return {
            "error": f"Failed to find next task: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def analyze_complexity_tool(
    project_root: str,
    task_ids: Optional[str] = None,
    use_research: bool = False,
    complexity_threshold: int = 7,
    save_report: bool = True,
    report_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analizza la complessità dei task usando AI (LiteLLM) per valutazioni accurate.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_ids: ID dei task da analizzare (comma-separated), se None analizza tutti i pending
        use_research: Se usare ricerca per context aggiuntivo
        complexity_threshold: Soglia per segnalare task complessi (1-10)
        save_report: Se salvare il report di complessità
        report_path: Path custom per il report (default: .pytaskai/reports/complexity_report.json)

    Returns:
        Dict contenente analisi di complessità e raccomandazioni
    """
    try:
        logger.info(f"Analyzing task complexity for project: {project_root}")

        # Load tasks data
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {"error": "No tasks file found", "project_root": project_root}

        tasks = data  # data is already a list of task dictionaries
        if not tasks:
            return {
                "error": "No tasks available for analysis",
                "project_root": project_root,
            }

        # Determine which tasks to analyze
        target_tasks = []
        if task_ids:
            # Analyze specific tasks
            task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
            target_tasks = [t for t in tasks if t.get("id") in task_id_list]

            if len(target_tasks) != len(task_id_list):
                found_ids = [t.get("id") for t in target_tasks]
                missing_ids = [tid for tid in task_id_list if tid not in found_ids]
                return {
                    "error": f"Some task IDs not found: {missing_ids}",
                    "found_tasks": found_ids,
                    "project_root": project_root,
                }
        else:
            # Analyze all pending tasks
            target_tasks = [t for t in tasks if t.get("status", "pending") == "pending"]

        if not target_tasks:
            return {"message": "No tasks to analyze", "project_root": project_root}

        # Initialize AI service
        from .ai_service import ai_service_instance

        if not ai_service_instance:
            return {"error": "AI service not available", "project_root": project_root}

        # Analyze each task
        complexity_results = []
        total_analysis_time = 0
        total_analysis_cost = 0

        for task in target_tasks:
            task_id = task.get("id")
            task_title = task.get("title", "")
            task_description = task.get("description", "")
            task_details = task.get("details", "")
            task_dependencies = task.get("dependencies", [])

            logger.info(f"Analyzing complexity for task {task_id}: {task_title}")

            # Build analysis prompt
            analysis_prompt = f"""
Analizza la complessità del seguente task di sviluppo software e fornisci una valutazione strutturata.

## Task da analizzare:
**ID**: {task_id}
**Titolo**: {task_title}
**Descrizione**: {task_description}
**Dettagli**: {task_details}
**Dipendenze**: {task_dependencies}

## Criteri di valutazione (scala 1-10):
1. **Complessità tecnica**: Difficoltà dell'implementazione
2. **Scope**: Ampiezza del lavoro richiesto  
3. **Dipendenze**: Impatto delle dipendenze esterne/interne
4. **Risk level**: Rischi potenziali e incertezze
5. **Time estimate**: Stima temporale realistica

## Output richiesto (JSON):
```json
{{
    "task_id": {task_id},
    "complexity_score": <numero 1-10>,
    "technical_complexity": <numero 1-10>,
    "scope_complexity": <numero 1-10>,
    "dependency_complexity": <numero 1-10>,
    "risk_level": <numero 1-10>,
    "estimated_hours": <numero>,
    "reasoning": "Spiegazione dettagliata della valutazione",
    "recommendations": [
        "Lista di raccomandazioni specifiche"
    ],
    "potential_blockers": [
        "Possibili ostacoli da considerare"
    ],
    "suggested_subtasks": [
        "Suggerimenti per divisione in subtask"
    ]
}}
```

Fornisci SOLO il JSON senza testo aggiuntivo.
"""

            try:
                # Get AI analysis
                start_time = time.time()

                if use_research:
                    # Use research context
                    analysis_response = ai_service_instance.generate_task_with_ai(
                        prompt=analysis_prompt,
                        project_context=f"Task complexity analysis for: {task_title}",
                        use_research=True,
                        research_query=f"software development complexity analysis {task_title} best practices",
                    )
                else:
                    # Direct analysis
                    analysis_response = ai_service_instance.generate_task_with_ai(
                        prompt=analysis_prompt,
                        project_context=f"Task complexity analysis for: {task_title}",
                        use_research=False,
                    )

                analysis_time = time.time() - start_time
                total_analysis_time += analysis_time

                # Track costs if available
                if (
                    hasattr(analysis_response, "usage_cost")
                    and analysis_response.usage_cost
                ):
                    total_analysis_cost += analysis_response.usage_cost

                # Parse JSON response
                analysis_content = (
                    analysis_response.content
                    if hasattr(analysis_response, "content")
                    else str(analysis_response)
                )

                # Try multiple JSON parsing strategies
                complexity_data = None
                json_patterns = [
                    r"```json\s*(\{.*?\})\s*```",
                    r"```\s*(\{.*?\})\s*```",
                    r"(\{.*?\})",
                ]

                for pattern in json_patterns:
                    matches = re.findall(
                        pattern, analysis_content, re.DOTALL | re.IGNORECASE
                    )
                    if matches:
                        try:
                            complexity_data = json.loads(matches[0].strip())
                            break
                        except json.JSONDecodeError:
                            continue

                # Fallback: create basic analysis
                if not complexity_data:
                    logger.warning(
                        f"Failed to parse AI response for task {task_id}, using fallback"
                    )

                    # Simple heuristic-based complexity estimation
                    estimated_complexity = 5  # Default medium

                    # Adjust based on task characteristics
                    if len(task_dependencies) > 3:
                        estimated_complexity += 1
                    if len(task_details) > 200:
                        estimated_complexity += 1
                    if "AI" in task_title or "LiteLLM" in task_title:
                        estimated_complexity += 1
                    if "test" in task_title.lower():
                        estimated_complexity -= 1

                    estimated_complexity = max(1, min(10, estimated_complexity))

                    complexity_data = {
                        "task_id": task_id,
                        "complexity_score": estimated_complexity,
                        "technical_complexity": estimated_complexity,
                        "scope_complexity": estimated_complexity - 1,
                        "dependency_complexity": min(len(task_dependencies), 10),
                        "risk_level": estimated_complexity,
                        "estimated_hours": estimated_complexity * 2,
                        "reasoning": f"Automatic analysis based on task characteristics. Dependencies: {len(task_dependencies)}, Details length: {len(task_details)}",
                        "recommendations": [
                            "Consider breaking down into smaller subtasks if complexity > 7"
                        ],
                        "potential_blockers": ["Review dependencies before starting"],
                        "suggested_subtasks": ["Planning", "Implementation", "Testing"],
                    }

                # Add metadata
                complexity_data["analysis_metadata"] = {
                    "analyzed_at": datetime.now().isoformat(),
                    "analysis_time": analysis_time,
                    "use_research": use_research,
                    "model_used": getattr(
                        ai_service_instance, "current_model", "unknown"
                    ),
                    "ai_generated": (
                        complexity_data.get("complexity_score") != estimated_complexity
                        if "estimated_complexity" in locals()
                        else True
                    ),
                }

                complexity_results.append(complexity_data)
                logger.info(
                    f"Task {task_id} complexity: {complexity_data.get('complexity_score', 'unknown')}/10"
                )

            except Exception as e:
                logger.error(f"Error analyzing task {task_id}: {str(e)}")
                # Add error entry
                complexity_results.append(
                    {
                        "task_id": task_id,
                        "error": f"Analysis failed: {str(e)}",
                        "analysis_metadata": {
                            "analyzed_at": datetime.now().isoformat(),
                            "analysis_time": 0,
                            "use_research": use_research,
                        },
                    }
                )

        # Build summary report
        successful_analyses = [r for r in complexity_results if "error" not in r]
        failed_analyses = [r for r in complexity_results if "error" in r]

        if successful_analyses:
            complexity_scores = [
                r.get("complexity_score", 0) for r in successful_analyses
            ]
            avg_complexity = sum(complexity_scores) / len(complexity_scores)
            max_complexity = max(complexity_scores)
            min_complexity = min(complexity_scores)

            # Identify high complexity tasks
            high_complexity_tasks = [
                r
                for r in successful_analyses
                if r.get("complexity_score", 0) >= complexity_threshold
            ]
        else:
            avg_complexity = max_complexity = min_complexity = 0
            high_complexity_tasks = []

        # Build final report
        report = {
            "analysis_summary": {
                "total_tasks_analyzed": len(target_tasks),
                "successful_analyses": len(successful_analyses),
                "failed_analyses": len(failed_analyses),
                "average_complexity": round(avg_complexity, 2),
                "max_complexity": max_complexity,
                "min_complexity": min_complexity,
                "high_complexity_count": len(high_complexity_tasks),
                "complexity_threshold": complexity_threshold,
            },
            "task_analyses": complexity_results,
            "high_complexity_tasks": high_complexity_tasks,
            "recommendations": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project_root": project_root,
                "analysis_settings": {
                    "use_research": use_research,
                    "complexity_threshold": complexity_threshold,
                    "task_ids_filter": task_ids,
                },
                "performance": {
                    "total_analysis_time": round(total_analysis_time, 2),
                    "total_analysis_cost": round(total_analysis_cost, 4),
                    "average_time_per_task": (
                        round(total_analysis_time / len(target_tasks), 2)
                        if target_tasks
                        else 0
                    ),
                },
            },
        }

        # Add recommendations
        if high_complexity_tasks:
            report["recommendations"].append(
                f"Consider expanding {len(high_complexity_tasks)} high-complexity tasks into subtasks"
            )

        if avg_complexity > 6:
            report["recommendations"].append(
                "Average complexity is high - consider reviewing project scope and timelines"
            )

        if failed_analyses:
            report["recommendations"].append(
                f"Re-run analysis for {len(failed_analyses)} failed task(s) with different settings"
            )

        # Save report if requested
        if save_report:
            try:
                # Determine report path
                if not report_path:
                    reports_dir = get_reports_directory(
                        project_root
                    )  # PyTaskAI: Use standardized path
                    reports_dir.mkdir(parents=True, exist_ok=True)
                    report_path = reports_dir / "complexity_report.json"
                else:
                    report_path = Path(project_root) / report_path
                    report_path.parent.mkdir(parents=True, exist_ok=True)

                # Save report
                with open(report_path, "w") as f:
                    json.dump(report, f, indent=2)

                report["saved_report_path"] = str(report_path)
                logger.info(f"Complexity report saved to: {report_path}")

            except Exception as e:
                logger.error(f"Failed to save complexity report: {str(e)}")
                report["save_error"] = f"Failed to save report: {str(e)}"

        logger.info(
            f"Complexity analysis completed: {len(successful_analyses)}/{len(target_tasks)} tasks analyzed"
        )
        return report

    except Exception as e:
        logger.error(f"Error in complexity analysis: {str(e)}")
        return {
            "error": f"Failed to analyze complexity: {str(e)}",
            "project_root": project_root,
        }


@mcp.tool()
def update_subtask_tool(
    project_root: str,
    task_id: Union[int, str],
    subtask_id: Union[int, str],
    update_prompt: str,
    use_research: bool = False,
    preserve_existing: bool = True,
    update_fields: Optional[str] = "details,title,description",
) -> Dict[str, Any]:
    """
    Aggiorna un subtask specifico usando AI (LiteLLM) per raffinare i dettagli.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task padre
        subtask_id: ID del subtask da aggiornare
        update_prompt: Prompt con le modifiche/raffinamenti richiesti
        use_research: Se usare ricerca per context aggiuntivo
        preserve_existing: Se preservare informazioni esistenti non modificate
        update_fields: Campi da aggiornare (comma-separated: title,description,details,test_strategy)

    Returns:
        Dict contenente risultato dell'aggiornamento
    """
    try:
        logger.info(
            f"Updating subtask {subtask_id} of task {task_id} in project: {project_root}"
        )

        # Load tasks data
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {"error": "No tasks file found", "project_root": project_root}

        tasks = data  # data is already a list of task dictionaries
        task_id = int(task_id)
        subtask_id = int(subtask_id)

        # Find parent task
        parent_task = None
        for task in tasks:
            if task.get("id") == task_id:
                parent_task = task
                break

        if not parent_task:
            return {
                "error": f"Parent task {task_id} not found",
                "task_id": task_id,
                "project_root": project_root,
            }

        # Find subtask
        subtasks = parent_task.get("subtasks", [])
        target_subtask = None
        subtask_index = None

        for i, subtask in enumerate(subtasks):
            if subtask.get("id") == subtask_id:
                target_subtask = subtask
                subtask_index = i
                break

        if not target_subtask:
            return {
                "error": f"Subtask {subtask_id} not found in task {task_id}",
                "task_id": task_id,
                "subtask_id": subtask_id,
                "available_subtasks": [s.get("id") for s in subtasks],
                "project_root": project_root,
            }

        # Initialize AI service
        from .ai_service import ai_service_instance

        if not ai_service_instance:
            return {"error": "AI service not available", "project_root": project_root}

        # Parse update fields
        fields_to_update = [f.strip() for f in update_fields.split(",")]
        valid_fields = ["title", "description", "details", "test_strategy"]
        fields_to_update = [f for f in fields_to_update if f in valid_fields]

        if not fields_to_update:
            return {
                "error": f"No valid fields to update. Valid fields: {valid_fields}",
                "project_root": project_root,
            }

        # Get current subtask content
        current_title = target_subtask.get("title", "")
        current_description = target_subtask.get("description", "")
        current_details = target_subtask.get("details", "")
        current_test_strategy = target_subtask.get("test_strategy", "")
        current_status = target_subtask.get("status", "pending")
        current_dependencies = target_subtask.get("dependencies", [])

        # Build context about parent task
        parent_context = f"""
## Parent Task Context:
**Task ID**: {task_id}
**Title**: {parent_task.get('title', '')}
**Description**: {parent_task.get('description', '')}
**Details**: {parent_task.get('details', '')}
**Priority**: {parent_task.get('priority', 'medium')}
"""

        # Build refinement prompt
        refinement_prompt = f"""
Sei un esperto di project management e sviluppo software. Devi raffinare un subtask specifico basandoti sul prompt di aggiornamento fornito.

{parent_context}

## Subtask Attuale da Raffinare:
**Subtask ID**: {subtask_id}
**Titolo**: {current_title}
**Descrizione**: {current_description}
**Dettagli**: {current_details}
**Strategia Test**: {current_test_strategy}
**Status**: {current_status}
**Dipendenze**: {current_dependencies}

## Richiesta di Aggiornamento:
{update_prompt}

## Campi da Aggiornare:
{', '.join(fields_to_update)}

## Istruzioni:
1. Raffinare SOLO i campi specificati nei "Campi da Aggiornare"
2. {"Preservare informazioni esistenti utili e integrarle con i nuovi dettagli" if preserve_existing else "Sostituire completamente il contenuto esistente"}
3. Mantenere coerenza con il parent task e il contesto generale
4. Fornire dettagli tecnici specifici e actionable
5. Assicurarsi che la strategia di test sia realistica e completa

## Output richiesto (JSON):
```json
{{
    "title": "Titolo raffinato del subtask",
    "description": "Descrizione chiara e concisa",
    "details": "Dettagli tecnici specifici con step implementativi",
    "test_strategy": "Strategia di testing dettagliata e specifica",
    "reasoning": "Spiegazione delle modifiche apportate",
    "improvements_made": [
        "Lista delle migliorie specifiche applicate"
    ]
}}
```

Includi SOLO i campi che sono nei "Campi da Aggiornare". Fornisci SOLO il JSON senza testo aggiuntivo.
"""

        try:
            # Get AI refinement
            start_time = time.time()

            if use_research:
                # Use research context for more informed updates
                research_query = f"software development subtask refinement {current_title} best practices implementation"
                refinement_response = ai_service_instance.generate_task_with_ai(
                    prompt=refinement_prompt,
                    project_context=f"Subtask refinement for: {current_title}",
                    use_research=True,
                    research_query=research_query,
                )
            else:
                # Direct refinement
                refinement_response = ai_service_instance.generate_task_with_ai(
                    prompt=refinement_prompt,
                    project_context=f"Subtask refinement for: {current_title}",
                    use_research=False,
                )

            refinement_time = time.time() - start_time

            # Track costs if available
            refinement_cost = 0
            if (
                hasattr(refinement_response, "usage_cost")
                and refinement_response.usage_cost
            ):
                refinement_cost = refinement_response.usage_cost

            # Parse JSON response
            refinement_content = (
                refinement_response.content
                if hasattr(refinement_response, "content")
                else str(refinement_response)
            )

            # Try multiple JSON parsing strategies
            refinement_data = None
            json_patterns = [
                r"```json\s*(\{.*?\})\s*```",
                r"```\s*(\{.*?\})\s*```",
                r"(\{.*?\})",
            ]

            for pattern in json_patterns:
                matches = re.findall(
                    pattern, refinement_content, re.DOTALL | re.IGNORECASE
                )
                if matches:
                    try:
                        refinement_data = json.loads(matches[0].strip())
                        break
                    except json.JSONDecodeError:
                        continue

            # Fallback: create enhanced version using simple rules
            if not refinement_data:
                logger.warning(
                    f"Failed to parse AI response for subtask {subtask_id}, using enhanced fallback"
                )

                # Enhanced fallback based on update prompt
                refinement_data = {}

                if "title" in fields_to_update:
                    enhanced_title = current_title
                    if update_prompt and len(update_prompt) > 10:
                        # Try to extract action words and enhance title
                        if "implement" in update_prompt.lower():
                            enhanced_title = f"Implementazione: {current_title}"
                        elif "test" in update_prompt.lower():
                            enhanced_title = f"Testing: {current_title}"
                        elif "refactor" in update_prompt.lower():
                            enhanced_title = f"Refactoring: {current_title}"
                    refinement_data["title"] = enhanced_title

                if "description" in fields_to_update:
                    enhanced_desc = current_description
                    if preserve_existing and current_description:
                        enhanced_desc = f"{current_description}\n\nAggiornamento: {update_prompt[:100]}..."
                    else:
                        enhanced_desc = f"Subtask raffinato: {update_prompt[:200]}..."
                    refinement_data["description"] = enhanced_desc

                if "details" in fields_to_update:
                    enhanced_details = current_details
                    if preserve_existing and current_details:
                        enhanced_details = (
                            f"{current_details}\n\n## Aggiornamenti:\n{update_prompt}"
                        )
                    else:
                        enhanced_details = f"Dettagli implementativi:\n1. {update_prompt}\n2. Implementare logica base\n3. Testare funzionalità"
                    refinement_data["details"] = enhanced_details

                if "test_strategy" in fields_to_update:
                    enhanced_test = current_test_strategy
                    if not enhanced_test or not preserve_existing:
                        enhanced_test = "1. Unit test per funzionalità core\n2. Test di integrazione\n3. Validazione manuale"
                    refinement_data["test_strategy"] = enhanced_test

                refinement_data["reasoning"] = (
                    f"Fallback enhancement based on update prompt: {update_prompt[:100]}..."
                )
                refinement_data["improvements_made"] = [
                    "Enhanced based on update request",
                    "Preserved existing information",
                ]

            # Update subtask with refined content
            updated_subtask = target_subtask.copy()
            changes_made = []

            for field in fields_to_update:
                if field in refinement_data:
                    old_value = updated_subtask.get(field, "")
                    new_value = refinement_data[field]

                    if old_value != new_value:
                        updated_subtask[field] = new_value
                        changes_made.append(f"{field}: updated")
                    else:
                        changes_made.append(f"{field}: no change")

            # Add update metadata
            updated_subtask["updated_at"] = datetime.now().isoformat()
            if "ai_update_history" not in updated_subtask:
                updated_subtask["ai_update_history"] = []

            update_metadata = {
                "updated_at": datetime.now().isoformat(),
                "update_prompt": update_prompt,
                "fields_updated": fields_to_update,
                "use_research": use_research,
                "preserve_existing": preserve_existing,
                "refinement_time": refinement_time,
                "refinement_cost": refinement_cost,
                "model_used": getattr(ai_service_instance, "current_model", "unknown"),
                "changes_made": changes_made,
                "reasoning": refinement_data.get("reasoning", "AI refinement applied"),
                "improvements": refinement_data.get("improvements_made", []),
            }

            updated_subtask["ai_update_history"].append(update_metadata)

            # Update subtasks list
            subtasks[subtask_index] = updated_subtask
            parent_task["subtasks"] = subtasks

            # Save updated tasks
            success = save_tasks(project_root, data)
            if not success:
                return {
                    "error": "Failed to save updated subtask",
                    "task_id": task_id,
                    "subtask_id": subtask_id,
                    "project_root": project_root,
                }

            # Build result
            result = {
                "success": True,
                "task_id": task_id,
                "subtask_id": subtask_id,
                "updated_subtask": updated_subtask,
                "update_summary": {
                    "fields_updated": fields_to_update,
                    "changes_made": changes_made,
                    "use_research": use_research,
                    "preserve_existing": preserve_existing,
                    "reasoning": refinement_data.get("reasoning", ""),
                    "improvements": refinement_data.get("improvements_made", []),
                },
                "performance": {
                    "refinement_time": round(refinement_time, 2),
                    "refinement_cost": round(refinement_cost, 4),
                },
                "project_root": project_root,
            }

            logger.info(
                f"Subtask {subtask_id} updated successfully with {len(changes_made)} changes"
            )
            return result

        except Exception as e:
            logger.error(
                f"Error during AI refinement for subtask {subtask_id}: {str(e)}"
            )
            return {
                "error": f"AI refinement failed: {str(e)}",
                "task_id": task_id,
                "subtask_id": subtask_id,
                "project_root": project_root,
            }

    except Exception as e:
        logger.error(f"Error updating subtask {subtask_id}: {str(e)}")
        return {
            "error": f"Failed to update subtask: {str(e)}",
            "task_id": task_id,
            "subtask_id": subtask_id,
            "project_root": project_root,
        }


@mcp.tool()
def add_dependency_tool(
    project_root: str,
    task_id: Union[int, str],
    dependency_id: Union[int, str],
    validate_circular: bool = True,
) -> Dict[str, Any]:
    """
    Aggiunge una dipendenza a un task specifico.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task che dipende da un altro
        dependency_id: ID del task da cui dipende
        validate_circular: Se validare dipendenze circolari (raccomandato)

    Returns:
        Dict contenente risultato dell'operazione
    """
    try:
        logger.info(
            f"Adding dependency for project: {project_root}, task {task_id} depends on {dependency_id}"
        )

        # Load tasks data
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {
                "error": "No tasks file found",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        tasks = data  # data is already a list of task dictionaries
        task_id = int(task_id)
        dependency_id = int(dependency_id)

        # Validate that both tasks exist
        task_exists = any(t.get("id") == task_id for t in tasks)
        dependency_exists = any(t.get("id") == dependency_id for t in tasks)

        if not task_exists:
            return {
                "error": f"Task with ID {task_id} not found",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        if not dependency_exists:
            return {
                "error": f"Dependency task with ID {dependency_id} not found",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        # Find the target task
        target_task = None
        for task in tasks:
            if task.get("id") == task_id:
                target_task = task
                break

        # Ensure dependencies array exists
        if "dependencies" not in target_task:
            target_task["dependencies"] = []

        # Check if dependency already exists
        if dependency_id in target_task["dependencies"]:
            return {
                "error": f"Task {task_id} already depends on task {dependency_id}",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "existing_dependencies": target_task["dependencies"],
                "project_root": project_root,
            }

        # Check for circular dependencies if validation enabled
        if validate_circular:

            def has_circular_dependency(current_id, target_id, visited=None):
                if visited is None:
                    visited = set()

                if current_id in visited:
                    return True

                visited.add(current_id)

                current_task = next(
                    (t for t in tasks if t.get("id") == current_id), None
                )
                if not current_task:
                    return False

                for dep_id in current_task.get("dependencies", []):
                    if dep_id == target_id or has_circular_dependency(
                        dep_id, target_id, visited.copy()
                    ):
                        return True

                return False

            if has_circular_dependency(dependency_id, task_id):
                return {
                    "error": f"Adding dependency would create circular dependency: task {dependency_id} already depends on task {task_id}",
                    "task_id": task_id,
                    "dependency_id": dependency_id,
                    "project_root": project_root,
                }

        # Add the dependency
        target_task["dependencies"].append(dependency_id)
        target_task["updated_at"] = datetime.now().isoformat()

        # Save updated tasks
        try:
            save_tasks(project_root, data)
            logger.info(
                f"Successfully added dependency: task {task_id} now depends on task {dependency_id}"
            )
        except Exception as save_error:
            logger.error(f"Failed to save tasks: {save_error}")
            return {
                "error": f"Failed to save dependency update: {str(save_error)}",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        # Get task titles for context
        task_title = target_task.get("title", f"Task {task_id}")
        dependency_task = next((t for t in tasks if t.get("id") == dependency_id), {})
        dependency_title = dependency_task.get("title", f"Task {dependency_id}")

        result = {
            "success": True,
            "message": f"Successfully added dependency: '{task_title}' now depends on '{dependency_title}'",
            "task_id": task_id,
            "task_title": task_title,
            "dependency_id": dependency_id,
            "dependency_title": dependency_title,
            "updated_dependencies": target_task["dependencies"],
            "updated_at": target_task["updated_at"],
            "project_root": project_root,
        }

        logger.info(f"Dependency added successfully: {task_id} -> {dependency_id}")
        return result

    except ValueError as ve:
        logger.error(f"Value error in add_dependency: {str(ve)}")
        return {
            "error": f"Invalid input: {str(ve)}",
            "task_id": task_id,
            "dependency_id": dependency_id,
            "project_root": project_root,
        }
    except Exception as e:
        logger.error(f"Error adding dependency: {str(e)}")
        return {
            "error": f"Failed to add dependency: {str(e)}",
            "task_id": task_id,
            "dependency_id": dependency_id,
            "project_root": project_root,
        }


@mcp.tool()
def remove_dependency_tool(
    project_root: str, task_id: Union[int, str], dependency_id: Union[int, str]
) -> Dict[str, Any]:
    """
    Rimuove una dipendenza da un task specifico.

    Args:
        project_root: Path assoluto alla directory del progetto
        task_id: ID del task da cui rimuovere la dipendenza
        dependency_id: ID del task da rimuovere dalle dipendenze

    Returns:
        Dict contenente risultato dell'operazione
    """
    try:
        logger.info(
            f"Removing dependency for project: {project_root}, task {task_id} no longer depends on {dependency_id}"
        )

        # Load tasks data
        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks_dict = db_manager.get_all_tasks(include_subtasks=True)
        
        data = {"tasks": tasks_dict, "subtasks": []} if tasks_dict else None
        if not data:
            return {
                "error": "No tasks file found",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        tasks = data  # data is already a list of task dictionaries
        task_id = int(task_id)
        dependency_id = int(dependency_id)

        # Find the target task
        target_task = None
        for task in tasks:
            if task.get("id") == task_id:
                target_task = task
                break

        if not target_task:
            return {
                "error": f"Task with ID {task_id} not found",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        # Check if task has dependencies
        dependencies = target_task.get("dependencies", [])
        if not dependencies:
            return {
                "error": f"Task {task_id} has no dependencies to remove",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        # Check if dependency exists
        if dependency_id not in dependencies:
            return {
                "error": f"Task {task_id} does not depend on task {dependency_id}",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "existing_dependencies": dependencies,
                "project_root": project_root,
            }

        # Remove the dependency
        dependencies.remove(dependency_id)
        target_task["dependencies"] = dependencies
        target_task["updated_at"] = datetime.now().isoformat()

        # Save updated tasks
        try:
            save_tasks(project_root, data)
            logger.info(
                f"Successfully removed dependency: task {task_id} no longer depends on task {dependency_id}"
            )
        except Exception as save_error:
            logger.error(f"Failed to save tasks: {save_error}")
            return {
                "error": f"Failed to save dependency removal: {str(save_error)}",
                "task_id": task_id,
                "dependency_id": dependency_id,
                "project_root": project_root,
            }

        # Get task titles for context
        task_title = target_task.get("title", f"Task {task_id}")
        dependency_task = next((t for t in tasks if t.get("id") == dependency_id), {})
        dependency_title = dependency_task.get("title", f"Task {dependency_id}")

        result = {
            "success": True,
            "message": f"Successfully removed dependency: '{task_title}' no longer depends on '{dependency_title}'",
            "task_id": task_id,
            "task_title": task_title,
            "dependency_id": dependency_id,
            "dependency_title": dependency_title,
            "remaining_dependencies": dependencies,
            "updated_at": target_task["updated_at"],
            "project_root": project_root,
        }

        logger.info(f"Dependency removed successfully: {task_id} -/-> {dependency_id}")
        return result

    except ValueError as ve:
        logger.error(f"Value error in remove_dependency: {str(ve)}")
        return {
            "error": f"Invalid input: {str(ve)}",
            "task_id": task_id,
            "dependency_id": dependency_id,
            "project_root": project_root,
        }
    except Exception as e:
        logger.error(f"Error removing dependency: {str(e)}")
        return {
            "error": f"Failed to remove dependency: {str(e)}",
            "task_id": task_id,
            "dependency_id": dependency_id,
            "project_root": project_root,
        }


@mcp.tool()
def validate_dependencies_tool(
    project_root: str, fix_issues: bool = False
) -> Dict[str, Any]:
    """
    Valida l'integrità delle dipendenze tra task e identifica problemi.

    Args:
        project_root: Path assoluto alla directory del progetto
        fix_issues: Se correggere automaticamente i problemi trovati

    Returns:
        Dict contenente risultati della validazione e problemi trovati
    """
    try:
        logger.info(
            f"Validating dependencies for project: {project_root}, fix_issues: {fix_issues}"
        )

        # Load tasks using database manager
        from .database import get_db_manager
        
        db_manager = get_db_manager(project_root)
        tasks = db_manager.get_all_tasks(include_subtasks=True)
        
        if not tasks:
            return {"error": "No tasks found in database", "project_root": project_root}

        # Debug: Log task structure
        logger.info(f"Tasks loaded: {len(tasks)} tasks")
        if tasks:
            logger.info(f"First task type: {type(tasks[0])}")
            logger.info(f"First task: {tasks[0]}")

        # Validate that tasks is a list and each item is a dict
        if not isinstance(tasks, list):
            return {
                "error": f"Tasks data is not a list: {type(tasks)}",
                "project_root": project_root,
            }
        
        task_ids = {t.get("id") for t in tasks}

        # Validation results
        validation_results = {
            "is_valid": True,
            "issues_found": [],
            "warnings": [],
            "fixes_applied": [],
            "statistics": {
                "total_tasks": len(tasks),
                "tasks_with_dependencies": 0,
                "total_dependencies": 0,
                "orphaned_dependencies": 0,
                "circular_dependencies": 0,
            },
        }

        # Track changes for potential fixes
        fixes_made = False

        # Check each task's dependencies
        for task in tasks:
            task_id = task.get("id")
            dependencies = task.get("dependencies", [])

            if dependencies:
                validation_results["statistics"]["tasks_with_dependencies"] += 1
                validation_results["statistics"]["total_dependencies"] += len(
                    dependencies
                )

            # Check for orphaned dependencies (references to non-existent tasks)
            orphaned_deps = []
            for dep_id in dependencies:
                if dep_id not in task_ids:
                    orphaned_deps.append(dep_id)
                    validation_results["statistics"]["orphaned_dependencies"] += 1
                    validation_results["is_valid"] = False

                    issue = {
                        "type": "orphaned_dependency",
                        "task_id": task_id,
                        "task_title": task.get("title", f"Task {task_id}"),
                        "orphaned_dependency_id": dep_id,
                        "description": f"Task {task_id} depends on non-existent task {dep_id}",
                    }
                    validation_results["issues_found"].append(issue)

            # Fix orphaned dependencies if requested
            if fix_issues and orphaned_deps:
                original_deps = dependencies.copy()
                new_deps = [dep for dep in dependencies if dep in task_ids]
                task["dependencies"] = new_deps
                task["updated_at"] = datetime.now().isoformat()
                fixes_made = True

                fix_record = {
                    "type": "removed_orphaned_dependencies",
                    "task_id": task_id,
                    "removed_dependencies": orphaned_deps,
                    "original_dependencies": original_deps,
                    "new_dependencies": new_deps,
                }
                validation_results["fixes_applied"].append(fix_record)

        # Check for circular dependencies
        def find_circular_dependencies():
            circular_deps = []

            def has_path(start_id, end_id, visited=None):
                if visited is None:
                    visited = set()

                if start_id == end_id and visited:
                    return True

                if start_id in visited:
                    return False

                visited.add(start_id)

                start_task = next((t for t in tasks if t.get("id") == start_id), None)
                if not start_task:
                    return False

                for dep_id in start_task.get("dependencies", []):
                    if dep_id in task_ids and has_path(dep_id, end_id, visited.copy()):
                        return True

                return False

            for task in tasks:
                task_id = task.get("id")
                for dep_id in task.get("dependencies", []):
                    if dep_id in task_ids and has_path(dep_id, task_id):
                        circular_deps.append((task_id, dep_id))
                        validation_results["statistics"]["circular_dependencies"] += 1
                        validation_results["is_valid"] = False

                        issue = {
                            "type": "circular_dependency",
                            "task_id": task_id,
                            "task_title": task.get("title", f"Task {task_id}"),
                            "dependency_id": dep_id,
                            "description": f"Circular dependency detected: task {task_id} ↔ task {dep_id}",
                        }
                        validation_results["issues_found"].append(issue)

            return circular_deps

        circular_deps = find_circular_dependencies()

        # Add warnings for potential issues
        high_dependency_tasks = [t for t in tasks if len(t.get("dependencies", [])) > 5]

        for task in high_dependency_tasks:
            warning = {
                "type": "high_dependency_count",
                "task_id": task.get("id"),
                "task_title": task.get("title", f"Task {task.get('id')}"),
                "dependency_count": len(task.get("dependencies", [])),
                "description": f"Task has {len(task.get('dependencies', []))} dependencies (consider breaking down)",
            }
            validation_results["warnings"].append(warning)

        # Note: Auto-fixes are disabled for dependencies validation 
        # as it requires careful manual review of task relationships
        if fixes_made:
            logger.info(
                f"Would have applied {len(validation_results['fixes_applied'])} dependency fixes (auto-fix disabled)"
            )

        # Prepare final result
        result = {
            "success": True,
            "validation_results": validation_results,
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
        }

        # Add summary
        issues_count = len(validation_results["issues_found"])
        warnings_count = len(validation_results["warnings"])
        fixes_count = len(validation_results["fixes_applied"])

        if validation_results["is_valid"]:
            result["summary"] = (
                f"✅ Dependencies validation passed. {warnings_count} warnings found."
            )
        else:
            result["summary"] = (
                f"❌ Dependencies validation failed. {issues_count} issues found."
            )
            if fix_issues:
                result["summary"] += f" {fixes_count} fixes applied."

        logger.info(
            f"Dependencies validation completed: valid={validation_results['is_valid']}, issues={issues_count}, fixes={fixes_count}"
        )
        return result

    except Exception as e:
        import traceback
        logger.error(f"Error validating dependencies: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "error": f"Failed to validate dependencies: {str(e)}",
            "traceback": traceback.format_exc(),
            "project_root": project_root,
        }


@mcp.tool()
def get_system_diagnostics_tool(project_root: str) -> Dict[str, Any]:
    """
    Ottieni diagnostics completi del sistema PyTaskAI per debugging.
    
    Args:
        project_root: Path assoluto alla directory del progetto
        
    Returns:
        Dict contenente versione, ambiente, database status e configurazione
    """
    try:
        import sys
        import platform
        import os
        import sqlite3
        from pathlib import Path
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
            "system_info": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "python_executable": sys.executable,
                "working_directory": os.getcwd(),
            },
            "pytaskai_info": {
                "mcp_server_version": None,
                "package_location": None,
                "installed_version": None,
            },
            "database_info": {
                "db_path": None,
                "db_exists": False,
                "db_size": None,
                "tasks_count": 0,
                "sqlite_version": sqlite3.sqlite_version,
            },
            "environment_vars": {
                "pythonpath": os.environ.get("PYTHONPATH", "Not set"),
                "openai_api_key_set": bool(os.environ.get("OPENAI_API_KEY")),
                "anthropic_api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
            }
        }
        
        # Get PyTaskAI version info
        try:
            from mcp_server import __version__
            diagnostics["pytaskai_info"]["mcp_server_version"] = __version__
        except ImportError:
            diagnostics["pytaskai_info"]["mcp_server_version"] = "Could not import"
            
        try:
            import mcp_server
            diagnostics["pytaskai_info"]["package_location"] = str(Path(mcp_server.__file__).parent)
        except:
            diagnostics["pytaskai_info"]["package_location"] = "Could not determine"
            
        try:
            import pytaskai
            diagnostics["pytaskai_info"]["installed_version"] = getattr(pytaskai, "__version__", "No version attr")
        except ImportError:
            try:
                import pkg_resources
                diagnostics["pytaskai_info"]["installed_version"] = pkg_resources.get_distribution("pytaskai").version
            except:
                diagnostics["pytaskai_info"]["installed_version"] = "Could not determine"
        
        # Database diagnostics
        try:
            from .database import get_db_manager
            db_manager = get_db_manager(project_root)
            db_path = Path(project_root) / ".pytaskai" / "tasks.db"
            
            diagnostics["database_info"]["db_path"] = str(db_path)
            diagnostics["database_info"]["db_exists"] = db_path.exists()
            
            if db_path.exists():
                diagnostics["database_info"]["db_size"] = db_path.stat().st_size
                tasks = db_manager.get_all_tasks()
                diagnostics["database_info"]["tasks_count"] = len(tasks) if tasks else 0
        except Exception as e:
            diagnostics["database_info"]["error"] = str(e)
            
        # Module import paths
        diagnostics["import_paths"] = {
            "sys_path": sys.path[:5],  # First 5 paths for brevity
            "mcp_server_path": None,
            "shared_path": None,
        }
        
        try:
            import mcp_server
            diagnostics["import_paths"]["mcp_server_path"] = mcp_server.__file__
        except:
            pass
            
        try:
            import shared
            diagnostics["import_paths"]["shared_path"] = shared.__file__
        except:
            pass
        
        return diagnostics
        
    except Exception as e:
        import traceback
        return {
            "error": f"Failed to get system diagnostics: {str(e)}",
            "traceback": traceback.format_exc(),
            "project_root": project_root,
        }


@mcp.tool()
def hot_reload_modules_tool(project_root: str, clear_cache: bool = False) -> Dict[str, Any]:
    """
    Ricarica i moduli MCP server senza riavviare il processo (hot reload).
    
    Args:
        project_root: Path assoluto alla directory del progetto
        clear_cache: Se pulire anche la cache dei moduli prima del reload
        
    Returns:
        Dict contenente risultati del hot reload
    """
    try:
        logger.info(f"Hot reload requested for project: {project_root}")
        
        from .hot_reload import get_reloader, clear_module_cache
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
            "operations": []
        }
        
        # Clear module cache if requested
        if clear_cache:
            cache_result = clear_module_cache("mcp_server")
            results["operations"].append({
                "operation": "clear_cache",
                "result": cache_result
            })
        
        # Perform hot reload
        reloader = get_reloader()
        reload_result = reloader.reload_modules()
        results["operations"].append({
            "operation": "hot_reload",
            "result": reload_result
        })
        
        # Add summary
        if reload_result["status"] == "completed":
            results["status"] = "success"
            results["summary"] = f"Successfully reloaded {reload_result['summary']['successfully_reloaded']} modules"
            if reload_result["summary"]["failed"] > 0:
                results["summary"] += f", {reload_result['summary']['failed']} failed"
        else:
            results["status"] = "partial_success"
            results["summary"] = "Hot reload completed with some issues"
        
        logger.info(f"Hot reload completed: {results['summary']}")
        return results
        
    except Exception as e:
        import traceback
        error_msg = f"Hot reload failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": error_msg,
            "traceback": traceback.format_exc(),
            "project_root": project_root,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def restart_mcp_server_tool(project_root: str, confirm: bool = False, graceful: bool = True) -> Dict[str, Any]:
    """
    Riavvia il server MCP (solo per sviluppo).
    
    Args:
        project_root: Path assoluto alla directory del progetto
        confirm: Conferma per procedere con il riavvio
        graceful: Se effettuare un riavvio graceful o forzato
        
    Returns:
        Dict contenente risultato dell'operazione di riavvio
    """
    try:
        logger.info(f"MCP server restart requested for project: {project_root}")
        
        if not confirm:
            return {
                "status": "confirmation_required",
                "message": "⚠️ Set confirm=True to proceed with server restart",
                "note": "This will terminate the current MCP server process",
                "project_root": project_root,
                "timestamp": datetime.now().isoformat()
            }
        
        from .hot_reload import restart_server_process
        
        # Log restart attempt
        logger.warning(f"🔄 Initiating MCP server restart (graceful={graceful})")
        
        # Perform restart
        restart_result = restart_server_process(graceful=graceful)
        
        return {
            "status": "restart_initiated",
            "restart_result": restart_result,
            "message": "🔄 MCP server restart signal sent. Client may need to reconnect.",
            "project_root": project_root,
            "timestamp": datetime.now().isoformat(),
            "warning": "Client applications may lose connection and need to restart"
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Failed to restart MCP server: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "traceback": traceback.format_exc(),
            "project_root": project_root,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def get_module_status_tool(project_root: str) -> Dict[str, Any]:
    """
    Ottieni informazioni sui moduli caricati e stato del server.
    
    Args:
        project_root: Path assoluto alla directory del progetto
        
    Returns:
        Dict contenente informazioni sui moduli e stato server
    """
    try:
        logger.info(f"Module status requested for project: {project_root}")
        
        from .hot_reload import get_reloader
        import sys
        import os
        from pathlib import Path
        
        reloader = get_reloader()
        module_info = reloader.get_module_info()
        
        # Add server process info
        server_info = {
            "process_id": os.getpid(),
            "working_directory": os.getcwd(),
            "python_executable": sys.executable,
            "python_version": sys.version,
            "total_loaded_modules": len(sys.modules),
            "project_root": project_root
        }
        
        # Add PyTaskAI version info
        version_info = {}
        try:
            from mcp_server import __version__ as mcp_version
            version_info["mcp_server_version"] = mcp_version
        except:
            version_info["mcp_server_version"] = "Unknown"
        
        try:
            import pytaskai
            version_info["pytaskai_version"] = getattr(pytaskai, "__version__", "Unknown")
        except ImportError:
            version_info["pytaskai_version"] = "Not installed as package"
        
        # Check database status
        db_status = {}
        try:
            db_path = Path(project_root) / ".pytaskai" / "tasks.db"
            db_status["database_path"] = str(db_path)
            db_status["database_exists"] = db_path.exists()
            if db_path.exists():
                db_status["database_size"] = db_path.stat().st_size
        except Exception as e:
            db_status["error"] = str(e)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "server_info": server_info,
            "version_info": version_info,
            "database_status": db_status,
            "module_info": module_info,
            "project_root": project_root
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Failed to get module status: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "traceback": traceback.format_exc(),
            "project_root": project_root,
            "timestamp": datetime.now().isoformat()
        }


# Export the MCP server for use in main application
__all__ = [
    "mcp",
    "list_tasks_tool",
    "get_task_tool",
    "get_next_task_tool",
    "validate_tasks_tool",
    "init_claude_support_tool",
    "parse_prd_tool",
    "get_cache_metrics_tool",
    "clear_cache_tool",
    "check_rate_limits_tool",
    "get_usage_stats_tool",
    "check_budget_status_tool",
    "set_task_status_tool",
    "add_task_tool",
    "update_task_test_coverage_tool",
    "report_bug_tool",
    "get_bug_statistics_tool",
    "expand_task_tool",
    "add_dependency_tool",
    "remove_dependency_tool",
    "validate_dependencies_tool",
    "get_system_diagnostics_tool",
    "hot_reload_modules_tool",
    "restart_mcp_server_tool", 
    "get_module_status_tool",
]
