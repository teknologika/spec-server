"""
Configuration management for spec-server.

This module provides configuration loading from environment variables
and optional JSON configuration files with validation and defaults.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Server configuration settings."""
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, description="Port to listen on")
    transport: str = Field(default="stdio", description="Transport protocol (stdio or sse)")
    
    # Spec storage settings
    specs_dir: str = Field(default="specs", description="Directory for storing specifications")
    max_specs: int = Field(default=1000, description="Maximum number of specifications")
    
    # Document settings
    max_document_size: int = Field(default=1_000_000, description="Maximum document size in bytes")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_dir: str = Field(default="backups", description="Directory for backups")
    
    # Validation settings
    strict_validation: bool = Field(default=True, description="Enable strict input validation")
    allow_dangerous_paths: bool = Field(default=False, description="Allow potentially dangerous file paths")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path (None for console only)")
    
    # Performance settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_size: int = Field(default=100, description="Maximum cache size")
    
    @field_validator('transport')
    @classmethod
    def validate_transport(cls, v):
        """Validate transport protocol."""
        if v not in ['stdio', 'sse']:
            raise ValueError("Transport must be 'stdio' or 'sse'")
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('specs_dir', 'backup_dir')
    @classmethod
    def validate_directories(cls, v):
        """Validate directory paths."""
        if not v or not isinstance(v, str):
            raise ValueError("Directory path must be a non-empty string")
        return v
    
    @field_validator('max_specs', 'max_document_size', 'cache_size')
    @classmethod
    def validate_positive_integers(cls, v):
        """Validate positive integer values."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class ConfigManager:
    """Configuration manager for spec-server."""
    
    # Environment variable prefix
    ENV_PREFIX = "SPEC_SERVER_"
    
    # Default configuration file paths
    DEFAULT_CONFIG_PATHS = [
        "spec-server.json",
        "config/spec-server.json",
        os.path.expanduser("~/.spec-server.json"),
        "/etc/spec-server.json"
    ]
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self._config: Optional[ServerConfig] = None
    
    def load_config(self) -> ServerConfig:
        """
        Load configuration from environment variables and config file.
        
        Returns:
            ServerConfig instance with loaded configuration
        """
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_data = {}
        
        # Load from configuration file if available
        file_config = self._load_from_file()
        if file_config:
            config_data.update(file_config)
        
        # Override with environment variables
        env_config = self._load_from_env()
        config_data.update(env_config)
        
        # Create and validate configuration
        self._config = ServerConfig(**config_data)
        return self._config
    
    def _load_from_file(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dictionary with configuration data
        """
        config_file = self._find_config_file()
        if not config_file:
            return {}
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Configuration file must contain a JSON object")
            
            return data
        
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            # Log warning but don't fail - fall back to defaults and env vars
            logger.warning(f"Could not load configuration file {config_file}: {e}")
            return {}
    
    def _find_config_file(self) -> Optional[Path]:
        """
        Find configuration file to use.
        
        Returns:
            Path to configuration file or None if not found
        """
        # Use explicitly specified file if provided
        if self.config_file:
            if self.config_file.exists():
                return self.config_file
            else:
                logger.warning(f"Specified config file {self.config_file} not found")
                return None
        
        # Search default locations
        for path_str in self.DEFAULT_CONFIG_PATHS:
            path = Path(path_str)
            if path.exists() and path.is_file():
                return path
        
        return None
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dictionary with configuration data from environment
        """
        config = {}
        
        # Map environment variables to config keys
        env_mappings = {
            f"{self.ENV_PREFIX}HOST": "host",
            f"{self.ENV_PREFIX}PORT": ("port", int),
            f"{self.ENV_PREFIX}TRANSPORT": "transport",
            f"{self.ENV_PREFIX}SPECS_DIR": "specs_dir",
            f"{self.ENV_PREFIX}MAX_SPECS": ("max_specs", int),
            f"{self.ENV_PREFIX}MAX_DOCUMENT_SIZE": ("max_document_size", int),
            f"{self.ENV_PREFIX}AUTO_BACKUP": ("auto_backup", self._parse_bool),
            f"{self.ENV_PREFIX}BACKUP_DIR": "backup_dir",
            f"{self.ENV_PREFIX}STRICT_VALIDATION": ("strict_validation", self._parse_bool),
            f"{self.ENV_PREFIX}ALLOW_DANGEROUS_PATHS": ("allow_dangerous_paths", self._parse_bool),
            f"{self.ENV_PREFIX}LOG_LEVEL": "log_level",
            f"{self.ENV_PREFIX}LOG_FILE": "log_file",
            f"{self.ENV_PREFIX}CACHE_ENABLED": ("cache_enabled", self._parse_bool),
            f"{self.ENV_PREFIX}CACHE_SIZE": ("cache_size", int),
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(config_key, tuple):
                    key, converter = config_key
                    try:
                        config[key] = converter(value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_var}: {value} ({e})")
                else:
                    config[config_key] = value
        
        return config
    
    @staticmethod
    def _parse_bool(value: str) -> bool:
        """
        Parse boolean value from string.
        
        Args:
            value: String value to parse
            
        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        return bool(value)
    
    def save_config(self, config: ServerConfig, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration to save
            file_path: Optional path to save to (defaults to current config file)
        """
        if file_path:
            target_file = Path(file_path)
        elif self.config_file:
            target_file = self.config_file
        else:
            target_file = Path("spec-server.json")
        
        # Create directory if it doesn't exist
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dictionary
        config_dict = config.model_dump()
        
        # Write to file with pretty formatting
        with open(target_file, 'w') as f:
            json.dump(config_dict, f, indent=2, sort_keys=True)
    
    def get_config(self) -> ServerConfig:
        """
        Get current configuration, loading if necessary.
        
        Returns:
            Current ServerConfig instance
        """
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> ServerConfig:
        """
        Reload configuration from sources.
        
        Returns:
            Reloaded ServerConfig instance
        """
        self._config = None
        config = self.load_config()
        self._config = config
        return config


def create_example_config() -> str:
    """
    Create an example configuration file content.
    
    Returns:
        JSON string with example configuration
    """
    example_config = ServerConfig()
    config_dict = example_config.model_dump()
    
    # Add comments as a separate structure (JSON doesn't support comments)
    example_with_comments = {
        "_comments": {
            "host": "Host to bind to for SSE transport",
            "port": "Port to listen on for SSE transport",
            "transport": "Transport protocol: 'stdio' or 'sse'",
            "specs_dir": "Directory where specifications are stored",
            "max_specs": "Maximum number of specifications allowed",
            "max_document_size": "Maximum size of a single document in bytes",
            "auto_backup": "Whether to automatically backup specifications",
            "backup_dir": "Directory for storing backups",
            "strict_validation": "Enable strict input validation",
            "allow_dangerous_paths": "Allow potentially dangerous file paths (not recommended)",
            "log_level": "Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            "log_file": "Path to log file (null for console only)",
            "cache_enabled": "Enable caching for better performance",
            "cache_size": "Maximum number of items in cache"
        },
        **config_dict
    }
    
    return json.dumps(example_with_comments, indent=2, sort_keys=True)


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> ServerConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Current ServerConfig instance
    """
    return config_manager.get_config()


def reload_config() -> ServerConfig:
    """
    Reload the global configuration.
    
    Returns:
        Reloaded ServerConfig instance
    """
    return config_manager.reload_config()