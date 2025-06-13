"""
CLI Configuration management for PyTaskAI.

This module handles configuration loading from environment variables,
configuration files, and command-line arguments, following the
Configuration pattern for centralized configuration management.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CLIConfig:
    """Configuration for CLI adapter operations."""

    database_path: str
    output_format: str = "table"
    verbose: bool = False
    config_file: Optional[str] = None

    @classmethod
    def load(
        cls,
        config_file: Optional[str] = None,
        database_path: Optional[str] = None,
        output_format: str = "table",
        verbose: bool = False,
    ) -> "CLIConfig":
        """
        Load configuration from multiple sources with precedence.

        Configuration precedence (highest to lowest):
        1. Command-line arguments
        2. Environment variables
        3. Configuration file
        4. Default values

        Args:
            config_file: Path to JSON configuration file
            database_path: Database file path override
            output_format: Output format preference
            verbose: Verbose logging flag

        Returns:
            Loaded CLIConfig instance
        """
        # Load from config file if provided
        file_config = {}
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                raise ValueError(f"Invalid configuration file {config_file}: {e}")

        # Build final configuration with precedence
        final_database_path = (
            database_path  # CLI argument (highest precedence)
            or os.getenv("PYTASKAI_DATABASE_PATH")  # Environment variable
            or file_config.get("database_path")  # Config file
            or cls._get_default_database_path()  # Default value
        )

        final_output_format = (
            output_format
            if output_format != "table"
            else None  # CLI argument (if changed)
            or os.getenv("PYTASKAI_OUTPUT_FORMAT")  # Environment variable
            or file_config.get("output_format")  # Config file
            or "table"  # Default value
        )

        final_verbose = (
            verbose  # CLI argument
            or os.getenv("PYTASKAI_VERBOSE", "").lower()
            in ("true", "1", "yes")  # Environment
            or file_config.get("verbose", False)  # Config file
        )

        return cls(
            database_path=final_database_path,
            output_format=final_output_format,
            verbose=final_verbose,
            config_file=config_file,
        )

    @classmethod
    def _get_default_database_path(cls) -> str:
        """Get default database path in user's PyTaskAI directory."""
        home_dir = Path.home()
        pytaskai_dir = home_dir / ".pytaskai"
        pytaskai_dir.mkdir(exist_ok=True)
        return str(pytaskai_dir / "tasks.db")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary for serialization."""
        return {
            "database_path": self.database_path,
            "output_format": self.output_format,
            "verbose": self.verbose,
        }

    def save(self, config_file: str) -> None:
        """
        Save current configuration to file.

        Args:
            config_file: Path to configuration file to create/update
        """
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate output format
        valid_formats = ["table", "json", "plain"]
        if self.output_format not in valid_formats:
            raise ValueError(
                f"Invalid output format '{self.output_format}'. "
                f"Must be one of: {', '.join(valid_formats)}"
            )

        # Validate database path directory exists or can be created
        db_path = Path(self.database_path)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot create database directory: {e}")

    @property
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.verbose

    @property
    def database_dir(self) -> str:
        """Get database directory path."""
        return str(Path(self.database_path).parent)

    def get_display_config(self) -> dict:
        """Get configuration suitable for display (no sensitive data)."""
        return {
            "Database Path": self.database_path,
            "Output Format": self.output_format,
            "Verbose Mode": "Enabled" if self.verbose else "Disabled",
            "Config File": self.config_file or "None",
        }


def create_default_config_file(config_path: str) -> None:
    """
    Create a default configuration file with common settings.

    Args:
        config_path: Path where to create the configuration file
    """
    default_config = CLIConfig(
        database_path=CLIConfig._get_default_database_path(),
        output_format="table",
        verbose=False,
    )

    default_config.save(config_path)


def load_or_create_config(config_path: Optional[str] = None) -> CLIConfig:
    """
    Load configuration or create default if none exists.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Loaded or default CLIConfig instance
    """
    if config_path and not os.path.exists(config_path):
        create_default_config_file(config_path)

    return CLIConfig.load(config_file=config_path)
