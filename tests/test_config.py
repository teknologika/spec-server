"""
Tests for the configuration management system.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from spec_server.config import (
    ConfigManager,
    ServerConfig,
    create_example_config,
    get_config,
    reload_config,
)


class TestServerConfig:
    """Test cases for ServerConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ServerConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.transport == "stdio"
        assert config.specs_dir == "specs"
        assert config.max_specs == 1000
        assert config.max_document_size == 1_000_000
        assert config.auto_backup is True
        assert config.backup_dir == "backups"
        assert config.strict_validation is True
        assert config.allow_dangerous_paths is False
        assert config.log_level == "INFO"
        assert config.log_file is None
        assert config.cache_enabled is True
        assert config.cache_size == 100

    def test_custom_config(self):
        """Test creating config with custom values."""
        config = ServerConfig(
            host="0.0.0.0",
            port=9000,
            transport="sse",
            specs_dir="custom_specs",
            log_level="DEBUG",
        )

        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.transport == "sse"
        assert config.specs_dir == "custom_specs"
        assert config.log_level == "DEBUG"

    def test_invalid_transport(self):
        """Test validation of invalid transport."""
        with pytest.raises(ValueError, match="Transport must be"):
            ServerConfig(transport="invalid")

    def test_invalid_port(self):
        """Test validation of invalid port."""
        with pytest.raises(ValueError, match="Port must be between"):
            ServerConfig(port=0)

        with pytest.raises(ValueError, match="Port must be between"):
            ServerConfig(port=70000)

    def test_invalid_log_level(self):
        """Test validation of invalid log level."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            ServerConfig(log_level="INVALID")

    def test_log_level_case_insensitive(self):
        """Test that log level validation is case insensitive."""
        config = ServerConfig(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_invalid_directory(self):
        """Test validation of invalid directory paths."""
        with pytest.raises(ValueError, match="Directory path must be"):
            ServerConfig(specs_dir="")

        # Pydantic V2 raises ValidationError for type mismatches
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ServerConfig(backup_dir=None)

    def test_invalid_positive_integers(self):
        """Test validation of positive integer fields."""
        with pytest.raises(ValueError, match="Value must be positive"):
            ServerConfig(max_specs=0)

        with pytest.raises(ValueError, match="Value must be positive"):
            ServerConfig(max_document_size=-1)

        with pytest.raises(ValueError, match="Value must be positive"):
            ServerConfig(cache_size=0)


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init_without_config_file(self):
        """Test initializing ConfigManager without config file."""
        manager = ConfigManager()
        assert manager.config_file is None
        assert manager._config is None

    def test_init_with_config_file(self):
        """Test initializing ConfigManager with config file."""
        config_path = Path("test-config.json")
        manager = ConfigManager(config_path)
        assert manager.config_file == config_path

    def test_load_config_defaults(self):
        """Test loading config with defaults only."""
        manager = ConfigManager()

        # Mock file and env loading to return empty
        with patch.object(manager, "_load_from_file", return_value={}):
            with patch.object(manager, "_load_from_env", return_value={}):
                config = manager.load_config()

        assert isinstance(config, ServerConfig)
        assert config.host == "127.0.0.1"  # Default value

    def test_load_config_from_file(self):
        """Test loading config from file."""
        file_config = {"host": "0.0.0.0", "port": 9000, "transport": "sse"}

        manager = ConfigManager()

        with patch.object(manager, "_load_from_file", return_value=file_config):
            with patch.object(manager, "_load_from_env", return_value={}):
                config = manager.load_config()

        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.transport == "sse"

    def test_load_config_from_env_override(self):
        """Test that environment variables override file config."""
        file_config = {"host": "0.0.0.0", "port": 9000}
        env_config = {"host": "192.168.1.1", "transport": "sse"}

        manager = ConfigManager()

        with patch.object(manager, "_load_from_file", return_value=file_config):
            with patch.object(manager, "_load_from_env", return_value=env_config):
                config = manager.load_config()

        assert config.host == "192.168.1.1"  # From env (overrides file)
        assert config.port == 9000  # From file
        assert config.transport == "sse"  # From env

    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "SPEC_SERVER_HOST": "test-host",
            "SPEC_SERVER_PORT": "3000",
            "SPEC_SERVER_TRANSPORT": "sse",
            "SPEC_SERVER_SPECS_DIR": "test-specs",
            "SPEC_SERVER_AUTO_BACKUP": "false",
            "SPEC_SERVER_LOG_LEVEL": "debug",
            "SPEC_SERVER_CACHE_SIZE": "50",
        }

        manager = ConfigManager()

        with patch.dict(os.environ, env_vars):
            config_data = manager._load_from_env()

        assert config_data["host"] == "test-host"
        assert config_data["port"] == 3000
        assert config_data["transport"] == "sse"
        assert config_data["specs_dir"] == "test-specs"
        assert config_data["auto_backup"] is False
        assert config_data["log_level"] == "debug"
        assert config_data["cache_size"] == 50

    def test_parse_bool(self):
        """Test boolean parsing from strings."""
        assert ConfigManager._parse_bool("true") is True
        assert ConfigManager._parse_bool("True") is True
        assert ConfigManager._parse_bool("1") is True
        assert ConfigManager._parse_bool("yes") is True
        assert ConfigManager._parse_bool("on") is True

        assert ConfigManager._parse_bool("false") is False
        assert ConfigManager._parse_bool("False") is False
        assert ConfigManager._parse_bool("0") is False
        assert ConfigManager._parse_bool("no") is False
        assert ConfigManager._parse_bool("off") is False
        assert ConfigManager._parse_bool("") is False

    def test_load_from_file_valid_json(self):
        """Test loading from valid JSON file."""
        config_data = {"host": "test-host", "port": 3000}
        json_content = json.dumps(config_data)

        manager = ConfigManager()

        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch.object(
                manager, "_find_config_file", return_value=Path("test.json")
            ):
                result = manager._load_from_file()

        assert result == config_data

    def test_load_from_file_invalid_json(self):
        """Test loading from invalid JSON file."""
        invalid_json = "{ invalid json }"

        manager = ConfigManager()

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch.object(
                manager, "_find_config_file", return_value=Path("test.json")
            ):
                result = manager._load_from_file()

        assert result == {}  # Should return empty dict on error

    def test_load_from_file_not_found(self):
        """Test loading when config file is not found."""
        manager = ConfigManager()

        with patch.object(manager, "_find_config_file", return_value=None):
            result = manager._load_from_file()

        assert result == {}

    def test_find_config_file_explicit(self):
        """Test finding explicitly specified config file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            manager = ConfigManager(tmp_path)
            found_file = manager._find_config_file()
            assert found_file == tmp_path
        finally:
            tmp_path.unlink()

    def test_find_config_file_explicit_not_found(self):
        """Test finding explicitly specified config file that doesn't exist."""
        non_existent = Path("non-existent-config.json")
        manager = ConfigManager(non_existent)

        found_file = manager._find_config_file()
        assert found_file is None

    def test_save_config(self):
        """Test saving configuration to file."""
        config = ServerConfig(host="test-host", port=3000)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            manager = ConfigManager()
            manager.save_config(config, tmp_path)

            # Verify file was written correctly
            with open(tmp_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["host"] == "test-host"
            assert saved_data["port"] == 3000
        finally:
            tmp_path.unlink()

    def test_get_config_loads_if_needed(self):
        """Test that get_config loads config if not already loaded."""
        manager = ConfigManager()
        assert manager._config is None

        with patch.object(manager, "load_config") as mock_load:
            mock_config = ServerConfig()
            mock_load.return_value = mock_config

            result = manager.get_config()

            mock_load.assert_called_once()
            assert result == mock_config

    def test_get_config_returns_cached(self):
        """Test that get_config returns cached config if available."""
        manager = ConfigManager()
        cached_config = ServerConfig(host="cached-host")
        manager._config = cached_config

        with patch.object(manager, "load_config") as mock_load:
            result = manager.get_config()

            mock_load.assert_not_called()
            assert result == cached_config

    def test_reload_config(self):
        """Test reloading configuration."""
        manager = ConfigManager()
        old_config = ServerConfig(host="old-host")
        manager._config = old_config

        with patch.object(manager, "load_config") as mock_load:
            new_config = ServerConfig(host="new-host")
            mock_load.return_value = new_config

            result = manager.reload_config()

            mock_load.assert_called_once()
            assert result == new_config
            assert manager._config == new_config


class TestConfigFunctions:
    """Test cases for module-level configuration functions."""

    def test_create_example_config(self):
        """Test creating example configuration."""
        example = create_example_config()

        # Should be valid JSON
        data = json.loads(example)

        # Should contain comments and config data
        assert "_comments" in data
        assert "host" in data
        assert "port" in data

        # Comments should explain the fields
        assert "host" in data["_comments"]
        assert "Transport protocol" in data["_comments"]["transport"]

    @patch("spec_server.config.config_manager")
    def test_get_config(self, mock_manager):
        """Test global get_config function."""
        mock_config = ServerConfig()
        mock_manager.get_config.return_value = mock_config

        result = get_config()

        mock_manager.get_config.assert_called_once()
        assert result == mock_config

    @patch("spec_server.config.config_manager")
    def test_reload_config(self, mock_manager):
        """Test global reload_config function."""
        mock_config = ServerConfig()
        mock_manager.reload_config.return_value = mock_config

        result = reload_config()

        mock_manager.reload_config.assert_called_once()
        assert result == mock_config


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_full_config_loading_cycle(self):
        """Test complete configuration loading cycle."""
        # Create temporary config file
        config_data = {
            "host": "integration-host",
            "port": 4000,
            "transport": "sse",
            "specs_dir": "integration-specs",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(config_data, tmp)
            tmp_path = Path(tmp.name)

        try:
            # Set some environment variables
            env_vars = {
                "SPEC_SERVER_PORT": "5000",  # Should override file
                "SPEC_SERVER_LOG_LEVEL": "DEBUG",  # Should add to config
            }

            with patch.dict(os.environ, env_vars):
                manager = ConfigManager(tmp_path)
                config = manager.load_config()

            # Verify configuration
            assert config.host == "integration-host"  # From file
            assert config.port == 5000  # From env (overrides file)
            assert config.transport == "sse"  # From file
            assert config.specs_dir == "integration-specs"  # From file
            assert config.log_level == "DEBUG"  # From env

        finally:
            tmp_path.unlink()
