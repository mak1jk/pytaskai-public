"""
PyTaskAI CLI Application using Click framework.

This module implements the main CLI interface following the Adapter pattern,
adapting the application use cases to command-line commands while ensuring
zero duplication with the MCP adapter by reusing the same application layer.
"""

import asyncio
import sys
from functools import wraps
from typing import Optional

import click

from pytaskai.adapters.cli.commands.task_commands import task_commands
from pytaskai.adapters.cli.config import CLIConfig
from pytaskai.adapters.cli.dependency_injection import (
    CLIContainer,
    create_cli_container,
)


class CLIContext:
    """
    CLI context object for passing shared state between commands.

    This follows the Context pattern to provide shared configuration
    and dependency injection container across all CLI commands.
    """

    def __init__(self, container: CLIContainer, config: CLIConfig) -> None:
        """
        Initialize CLI context with container and configuration.

        Args:
            container: CLI dependency injection container
            config: CLI configuration
        """
        self.container = container
        self.config = config


def async_command(func):
    """
    Decorator to make Click commands work with async functions.

    This decorator wraps async command functions to run them in the
    event loop, enabling async use case execution in CLI commands.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group()
@click.option(
    "--database-path",
    "-d",
    help="Path to the database file",
    envvar="PYTASKAI_DATABASE_PATH",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["table", "json", "plain"]),
    default="table",
    help="Output format for results",
    envvar="PYTASKAI_OUTPUT_FORMAT",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
    envvar="PYTASKAI_VERBOSE",
)
@click.option(
    "--config-file",
    "-c",
    help="Path to configuration file",
    envvar="PYTASKAI_CONFIG_FILE",
)
@click.pass_context
def cli(
    ctx: click.Context,
    database_path: Optional[str],
    output_format: str,
    verbose: bool,
    config_file: Optional[str],
) -> None:
    """
    PyTaskAI - AI-powered task management system.

    A command-line interface for managing tasks with AI assistance.
    Supports task creation, updates, listing, and AI-powered features.

    Examples:
        pytaskai list --status Todo
        pytaskai add "Complete documentation" --priority High
        pytaskai update task123 --status "In Progress"
        pytaskai generate task123 --max-subtasks 5
    """
    try:
        # Load configuration
        config = CLIConfig.load(
            config_file=config_file,
            database_path=database_path,
            output_format=output_format,
            verbose=verbose,
        )

        # Create dependency injection container
        container = create_cli_container(database_path=config.database_path)

        # Store context for commands
        ctx.obj = CLIContext(container=container, config=config)

        if verbose:
            click.echo(
                f"PyTaskAI CLI initialized with database: {config.database_path}"
            )

    except Exception as e:
        click.echo(f"Error initializing CLI: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def version(cli_ctx: CLIContext) -> None:
    """Show PyTaskAI version information."""
    click.echo("PyTaskAI CLI v0.1.0")
    click.echo("AI-powered task management system")


@cli.command()
@click.pass_obj
def status(cli_ctx: CLIContext) -> None:
    """Show system status and service availability."""
    try:
        service_status = cli_ctx.container.get_service_status()

        click.echo("PyTaskAI System Status:")
        click.echo("=" * 40)

        for service, available in service_status.items():
            status_icon = "✅" if available else "❌"
            click.echo(
                f"{status_icon} {service.title()}: {'Available' if available else 'Unavailable'}"
            )

        # Database information
        if service_status.get("database", False):
            click.echo(f"\nDatabase: {cli_ctx.config.database_path}")

        # Configuration information
        click.echo(f"Output Format: {cli_ctx.config.output_format}")
        click.echo(f"Verbose Mode: {cli_ctx.config.verbose}")

    except Exception as e:
        click.echo(f"Error checking status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
@async_command
async def init(cli_ctx: CLIContext) -> None:
    """Initialize PyTaskAI database and configuration."""
    try:
        # Initialize database schema
        cli_ctx.container.initialize_database()

        click.echo("✅ Database initialized successfully")
        click.echo(f"📁 Database location: {cli_ctx.config.database_path}")

        # Check if AI services are available
        if cli_ctx.container.application_container.has_ai_services():
            click.echo("🤖 AI services configured and available")
        else:
            click.echo("⚠️  AI services not configured (optional)")
            click.echo(
                "   Set OPENAI_API_KEY environment variable to enable AI features"
            )

    except Exception as e:
        click.echo(f"Error during initialization: {e}", err=True)
        sys.exit(1)


# Register task command groups
cli.add_command(task_commands, name="task")


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
