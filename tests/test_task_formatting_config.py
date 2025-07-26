"""Tests for task formatting configuration system."""

import tempfile
from pathlib import Path

import pytest

from src.spec_server.task_formatting_config import TaskFormattingConfig, TaskFormattingConfigManager, get_config, get_config_schema, update_config, validate_config_value


class TestTaskFormattingConfig:
    """Test TaskFormattingConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TaskFormattingConfig()

        assert config.auto_format_enabled is True
        assert config.auto_requirements_linking is True
        assert config.content_redistribution_enabled is True
        assert config.llm_validation_enabled is True
        assert config.llm_validation_confidence_threshold == 0.7
        assert config.classification_confidence_threshold == 0.5
        assert config.requirements_relevance_threshold == 0.2
        assert config.max_requirements_per_task == 3
        assert config.enable_caching is True
        assert config.fail_on_formatting_errors is False
        assert config.fallback_to_original_on_error is True

    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = TaskFormattingConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "auto_format_enabled" in config_dict
        assert "llm_validation_confidence_threshold" in config_dict
        assert config_dict["auto_format_enabled"] is True
        assert config_dict["llm_validation_confidence_threshold"] == 0.7

    def test_config_from_dict(self):
        """Test configuration deserialization from dictionary."""
        config_dict = {
            "auto_format_enabled": False,
            "llm_validation_confidence_threshold": 0.8,
            "max_requirements_per_task": 5,
        }

        config = TaskFormattingConfig.from_dict(config_dict)

        assert config.auto_format_enabled is False
        assert config.llm_validation_confidence_threshold == 0.8
        assert config.max_requirements_per_task == 5
        # Other values should be defaults
        assert config.auto_requirements_linking is True

    def test_config_validation_valid(self):
        """Test configuration validation with valid values."""
        config = TaskFormattingConfig()
        config.validate()  # Should not raise

    def test_config_validation_invalid_confidence(self):
        """Test configuration validation with invalid confidence values."""
        config = TaskFormattingConfig()
        config.llm_validation_confidence_threshold = 1.5

        with pytest.raises(ValueError, match="llm_validation_confidence_threshold"):
            config.validate()

    def test_config_validation_invalid_threshold(self):
        """Test configuration validation with invalid threshold values."""
        config = TaskFormattingConfig()
        config.classification_confidence_threshold = -0.1

        with pytest.raises(ValueError, match="classification_confidence_threshold"):
            config.validate()

    def test_config_validation_invalid_retries(self):
        """Test configuration validation with invalid retry values."""
        config = TaskFormattingConfig()
        config.max_validation_retries = -1

        with pytest.raises(ValueError, match="max_validation_retries"):
            config.validate()

    def test_config_validation_invalid_log_level(self):
        """Test configuration validation with invalid log level."""
        config = TaskFormattingConfig()
        config.log_level = "INVALID"

        with pytest.raises(ValueError, match="log_level"):
            config.validate()


class TestTaskFormattingConfigManager:
    """Test TaskFormattingConfigManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "test_config.json"

    def test_load_default_config(self):
        """Test loading default configuration when no file exists."""
        manager = TaskFormattingConfigManager(self.config_path)
        config = manager.load_config()

        assert isinstance(config, TaskFormattingConfig)
        assert config.auto_format_enabled is True

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        manager = TaskFormattingConfigManager(self.config_path)

        # Create custom config
        config = TaskFormattingConfig()
        config.auto_format_enabled = False
        config.llm_validation_confidence_threshold = 0.8

        # Save config
        manager.save_config(config)
        assert self.config_path.exists()

        # Load config
        loaded_config = manager.load_config()
        assert loaded_config.auto_format_enabled is False
        assert loaded_config.llm_validation_confidence_threshold == 0.8

    def test_update_config(self):
        """Test updating specific configuration values."""
        manager = TaskFormattingConfigManager(self.config_path)

        # Update specific values
        updated_config = manager.update_config(auto_format_enabled=False, max_requirements_per_task=5)

        assert updated_config.auto_format_enabled is False
        assert updated_config.max_requirements_per_task == 5
        # Other values should remain default
        assert updated_config.auto_requirements_linking is True

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        manager = TaskFormattingConfigManager(self.config_path)

        # First update config
        manager.update_config(auto_format_enabled=False)

        # Then reset
        reset_config = manager.reset_to_defaults()

        assert reset_config.auto_format_enabled is True

    def test_load_invalid_config_file(self):
        """Test loading invalid configuration file."""
        # Create invalid JSON file
        with open(self.config_path, "w") as f:
            f.write("invalid json content")

        manager = TaskFormattingConfigManager(self.config_path)
        config = manager.load_config()

        # Should fallback to default config
        assert isinstance(config, TaskFormattingConfig)
        assert config.auto_format_enabled is True

    def test_save_invalid_config(self):
        """Test saving invalid configuration."""
        manager = TaskFormattingConfigManager(self.config_path)

        config = TaskFormattingConfig()
        config.llm_validation_confidence_threshold = 2.0  # Invalid

        with pytest.raises(ValueError):
            manager.save_config(config)


class TestConfigurationHelpers:
    """Test configuration helper functions."""

    def test_validate_config_value_valid(self):
        """Test validating valid configuration values."""
        assert validate_config_value("auto_format_enabled", True) is True
        assert validate_config_value("llm_validation_confidence_threshold", 0.8) is True
        assert validate_config_value("max_requirements_per_task", 5) is True

    def test_validate_config_value_invalid(self):
        """Test validating invalid configuration values."""
        assert validate_config_value("llm_validation_confidence_threshold", 1.5) is False
        assert validate_config_value("max_validation_retries", -1) is False
        assert validate_config_value("log_level", "INVALID") is False

    def test_get_config_schema(self):
        """Test getting configuration schema."""
        schema = get_config_schema()

        assert isinstance(schema, dict)
        assert "auto_format_enabled" in schema
        assert "llm_validation_confidence_threshold" in schema

        # Check schema structure
        auto_format_schema = schema["auto_format_enabled"]
        assert auto_format_schema["type"] == "boolean"
        assert auto_format_schema["default"] is True
        assert "description" in auto_format_schema

        confidence_schema = schema["llm_validation_confidence_threshold"]
        assert confidence_schema["type"] == "float"
        assert confidence_schema["min"] == 0.0
        assert confidence_schema["max"] == 1.0

    def test_global_config_functions(self):
        """Test global configuration functions."""
        # Test get_config
        config = get_config()
        assert isinstance(config, TaskFormattingConfig)

        # Test update_config
        updated_config = update_config(auto_format_enabled=False)
        assert updated_config.auto_format_enabled is False

        # Verify the change persists
        config_again = get_config()
        assert config_again.auto_format_enabled is False
