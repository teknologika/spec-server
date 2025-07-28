"""Configuration management for task formatting features."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TaskFormattingConfig:
    """Configuration settings for task formatting functionality."""

    # Core formatting settings
    auto_format_enabled: bool = True
    auto_requirements_linking: bool = True
    content_redistribution_enabled: bool = True

    # LLM validation settings
    llm_validation_enabled: bool = True
    llm_validation_confidence_threshold: float = 0.7
    allow_manual_override: bool = True
    max_validation_retries: int = 3

    # Content classification settings
    classification_confidence_threshold: float = 0.5
    keyword_matching_enabled: bool = True
    phrase_matching_enabled: bool = True

    # Requirements linking settings
    requirements_relevance_threshold: float = 0.2
    max_requirements_per_task: int = 3
    auto_add_tbd_placeholders: bool = True

    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    batch_processing_enabled: bool = True
    max_batch_size: int = 50

    # Error handling settings
    fail_on_formatting_errors: bool = False
    log_formatting_changes: bool = True
    log_level: str = "INFO"

    # Fallback settings
    fallback_to_original_on_error: bool = True
    preserve_original_backup: bool = True

    # Monitoring settings
    enable_metrics: bool = True
    metrics_collection_interval: int = 60  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "auto_format_enabled": self.auto_format_enabled,
            "auto_requirements_linking": self.auto_requirements_linking,
            "content_redistribution_enabled": self.content_redistribution_enabled,
            "llm_validation_enabled": self.llm_validation_enabled,
            "llm_validation_confidence_threshold": self.llm_validation_confidence_threshold,
            "allow_manual_override": self.allow_manual_override,
            "max_validation_retries": self.max_validation_retries,
            "classification_confidence_threshold": self.classification_confidence_threshold,
            "keyword_matching_enabled": self.keyword_matching_enabled,
            "phrase_matching_enabled": self.phrase_matching_enabled,
            "requirements_relevance_threshold": self.requirements_relevance_threshold,
            "max_requirements_per_task": self.max_requirements_per_task,
            "auto_add_tbd_placeholders": self.auto_add_tbd_placeholders,
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "batch_processing_enabled": self.batch_processing_enabled,
            "max_batch_size": self.max_batch_size,
            "fail_on_formatting_errors": self.fail_on_formatting_errors,
            "log_formatting_changes": self.log_formatting_changes,
            "log_level": self.log_level,
            "fallback_to_original_on_error": self.fallback_to_original_on_error,
            "preserve_original_backup": self.preserve_original_backup,
            "enable_metrics": self.enable_metrics,
            "metrics_collection_interval": self.metrics_collection_interval,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TaskFormattingConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)

    def validate(self) -> None:
        """Validate configuration values."""
        if not 0.0 <= self.llm_validation_confidence_threshold <= 1.0:
            raise ValueError("llm_validation_confidence_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.classification_confidence_threshold <= 1.0:
            raise ValueError("classification_confidence_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.requirements_relevance_threshold <= 1.0:
            raise ValueError("requirements_relevance_threshold must be between 0.0 and 1.0")

        if self.max_validation_retries < 0:
            raise ValueError("max_validation_retries must be non-negative")

        if self.max_requirements_per_task < 1:
            raise ValueError("max_requirements_per_task must be at least 1")

        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")

        if self.max_batch_size < 1:
            raise ValueError("max_batch_size must be at least 1")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("log_level must be a valid logging level")


class TaskFormattingConfigManager:
    """Manages task formatting configuration loading and saving."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_path = config_path or Path.cwd() / "task_formatting_config.json"
        self._config: Optional[TaskFormattingConfig] = None
        self._logger = logging.getLogger(__name__)

    def load_config(self) -> TaskFormattingConfig:
        """Load configuration from file or return default."""
        if self._config is not None:
            return self._config

        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_dict = json.load(f)
                self._config = TaskFormattingConfig.from_dict(config_dict)
                self._config.validate()
                self._logger.info(f"Loaded task formatting configuration from {self.config_path}")
            else:
                self._config = TaskFormattingConfig()
                self._logger.info("Using default task formatting configuration")

        except Exception as e:
            self._logger.error(f"Failed to load configuration: {e}")
            self._logger.info("Falling back to default configuration")
            self._config = TaskFormattingConfig()

        return self._config

    def save_config(self, config: TaskFormattingConfig) -> None:
        """Save configuration to file."""
        try:
            config.validate()

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)

            self._config = config
            self._logger.info(f"Saved task formatting configuration to {self.config_path}")

        except Exception as e:
            self._logger.error(f"Failed to save configuration: {e}")
            raise

    def update_config(self, **kwargs: Any) -> TaskFormattingConfig:
        """Update specific configuration values."""
        current_config = self.load_config()
        config_dict = current_config.to_dict()
        config_dict.update(kwargs)

        new_config = TaskFormattingConfig.from_dict(config_dict)
        self.save_config(new_config)

        return new_config

    def reset_to_defaults(self) -> TaskFormattingConfig:
        """Reset configuration to defaults."""
        default_config = TaskFormattingConfig()
        self.save_config(default_config)
        return default_config


# Global configuration manager instance
_config_manager: Optional[TaskFormattingConfigManager] = None


def get_config_manager(
    config_path: Optional[Path] = None,
) -> TaskFormattingConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = TaskFormattingConfigManager(config_path)
    return _config_manager


def get_config() -> TaskFormattingConfig:
    """Get the current task formatting configuration."""
    return get_config_manager().load_config()


def update_config(**kwargs: Any) -> TaskFormattingConfig:
    """Update task formatting configuration."""
    return get_config_manager().update_config(**kwargs)


# Configuration validation helpers
def validate_config_value(key: str, value: Any) -> bool:
    """Validate a single configuration value."""
    try:
        config = get_config()
        config_dict = config.to_dict()
        config_dict[key] = value

        test_config = TaskFormattingConfig.from_dict(config_dict)
        test_config.validate()
        return True

    except (ValueError, TypeError):
        return False


def get_config_schema() -> Dict[str, Dict[str, Any]]:
    """Get configuration schema for validation and documentation."""
    return {
        "auto_format_enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable automatic task formatting",
        },
        "auto_requirements_linking": {
            "type": "boolean",
            "default": True,
            "description": "Enable automatic linking of tasks to requirements",
        },
        "content_redistribution_enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable redistribution of content to appropriate documents",
        },
        "llm_validation_enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable LLM-based task completion validation",
        },
        "llm_validation_confidence_threshold": {
            "type": "float",
            "default": 0.7,
            "min": 0.0,
            "max": 1.0,
            "description": "Minimum confidence threshold for LLM validation",
        },
        "allow_manual_override": {
            "type": "boolean",
            "default": True,
            "description": "Allow manual override of LLM validation results",
        },
        "max_validation_retries": {
            "type": "integer",
            "default": 3,
            "min": 0,
            "description": "Maximum number of validation retries",
        },
        "classification_confidence_threshold": {
            "type": "float",
            "default": 0.5,
            "min": 0.0,
            "max": 1.0,
            "description": "Minimum confidence threshold for content classification",
        },
        "requirements_relevance_threshold": {
            "type": "float",
            "default": 0.2,
            "min": 0.0,
            "max": 1.0,
            "description": "Minimum relevance threshold for requirements linking",
        },
        "max_requirements_per_task": {
            "type": "integer",
            "default": 3,
            "min": 1,
            "description": "Maximum number of requirements to link per task",
        },
        "enable_caching": {
            "type": "boolean",
            "default": True,
            "description": "Enable caching for performance optimization",
        },
        "cache_ttl_seconds": {
            "type": "integer",
            "default": 300,
            "min": 0,
            "description": "Cache time-to-live in seconds",
        },
        "fail_on_formatting_errors": {
            "type": "boolean",
            "default": False,
            "description": "Fail operations when formatting errors occur",
        },
        "log_formatting_changes": {
            "type": "boolean",
            "default": True,
            "description": "Log formatting changes for debugging",
        },
        "fallback_to_original_on_error": {
            "type": "boolean",
            "default": True,
            "description": "Fallback to original content when formatting fails",
        },
    }
