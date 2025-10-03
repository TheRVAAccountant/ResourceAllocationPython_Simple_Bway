"""Unified configuration service to consolidate all config sources.

This service provides a single source of truth for configuration by:
1. Loading from environment variables (.env)
2. Loading from JSON config files (config/settings.json)
3. Allowing runtime overrides via GUI
4. Providing clear priority: Runtime > JSON > Environment > Defaults
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

from src.core.base_service import BaseService


class UnifiedConfigurationService(BaseService):
    """Centralized configuration management service.
    
    Configuration Priority (highest to lowest):
    1. Runtime overrides (set via GUI or code)
    2. JSON config file (config/settings.json)
    3. Environment variables (.env)
    4. Default values (hardcoded)
    """
    
    # Default configuration values
    DEFAULTS = {
        # Excel Configuration
        "excel_visible": False,
        "excel_display_alerts": False,
        "use_xlwings": True,
        
        # Allocation Rules
        "max_vehicles_per_driver": 3,
        "min_vehicles_per_driver": 1,
        "priority_weight_factor": 1.5,
        "allocation_threshold": 0.8,
        
        # Duplicate Validation
        "strict_duplicate_validation": False,
        "max_assignments_per_vehicle": 1,
        
        # Email Settings
        "email_enabled": False,
        "email_host": "smtp.gmail.com",
        "email_port": 587,
        "email_use_tls": True,
        
        # File Paths
        "default_input_dir": "inputs",
        "default_output_dir": "outputs",
        "template_path": None,
        
        # History Settings
        "max_history_entries": 100,
        "history_retention_days": 90,
        
        # GUI Settings
        "theme": "dark",
        "company_name": "Resource Allocation System",
        "window_width": 1400,
        "window_height": 1000,
        
        # Logging
        "log_level": "INFO",
        "log_retention_days": 7,
        
        # Performance
        "enable_caching": True,
        "cache_ttl_seconds": 3600,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the unified configuration service.
        
        Args:
            config_file: Path to JSON config file (default: config/settings.json)
        """
        super().__init__()
        
        self.config_file = config_file or "config/settings.json"
        self.env_config: Dict[str, Any] = {}
        self.json_config: Dict[str, Any] = {}
        self.runtime_config: Dict[str, Any] = {}
        
    def initialize(self) -> None:
        """Initialize configuration by loading from all sources."""
        logger.info("Initializing UnifiedConfigurationService")
        
        # Load environment variables
        self._load_env_config()
        
        # Load JSON config file
        self._load_json_config()
        
        self._initialized = True
        logger.info("Configuration loaded successfully")
        
    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        # Load .env file
        load_dotenv()
        
        # Map environment variables to config keys
        env_mappings = {
            "EXCEL_VISIBLE": ("excel_visible", lambda x: x.lower() == "true"),
            "EXCEL_DISPLAY_ALERTS": ("excel_display_alerts", lambda x: x.lower() == "true"),
            "USE_XLWINGS": ("use_xlwings", lambda x: x.lower() == "true"),
            "MAX_VEHICLES_PER_DRIVER": ("max_vehicles_per_driver", int),
            "MIN_VEHICLES_PER_DRIVER": ("min_vehicles_per_driver", int),
            "PRIORITY_WEIGHT_FACTOR": ("priority_weight_factor", float),
            "ALLOCATION_THRESHOLD": ("allocation_threshold", float),
            "STRICT_DUPLICATE_VALIDATION": ("strict_duplicate_validation", lambda x: x.lower() == "true"),
            "EMAIL_ENABLED": ("email_enabled", lambda x: x.lower() == "true"),
            "EMAIL_HOST": ("email_host", str),
            "EMAIL_PORT": ("email_port", int),
            "EMAIL_USERNAME": ("email_username", str),
            "EMAIL_PASSWORD": ("email_password", str),
            "LOG_LEVEL": ("log_level", str),
            "THEME": ("theme", str),
            "COMPANY_NAME": ("company_name", str),
        }
        
        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    self.env_config[config_key] = converter(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert {env_var}={value}: {e}")
        
        logger.debug(f"Loaded {len(self.env_config)} settings from environment")
    
    def _load_json_config(self) -> None:
        """Load configuration from JSON file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return
        
        try:
            with open(config_path, 'r') as f:
                self.json_config = json.load(f)
            
            logger.debug(f"Loaded {len(self.json_config)} settings from {self.config_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with priority resolution.
        
        Priority: Runtime > JSON > Environment > Defaults > default parameter
        
        Args:
            key: Configuration key
            default: Default value if key not found anywhere
        
        Returns:
            Configuration value
        """
        # Check runtime overrides first
        if key in self.runtime_config:
            return self.runtime_config[key]
        
        # Check JSON config
        if key in self.json_config:
            return self.json_config[key]
        
        # Check environment config
        if key in self.env_config:
            return self.env_config[key]
        
        # Check defaults
        if key in self.DEFAULTS:
            return self.DEFAULTS[key]
        
        # Return provided default
        return default
    
    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """Set configuration value at runtime.
        
        Args:
            key: Configuration key
            value: Configuration value
            persist: If True, save to JSON config file
        """
        self.runtime_config[key] = value
        logger.debug(f"Set runtime config: {key}={value}")
        
        if persist:
            self.json_config[key] = value
            self._save_json_config()
    
    def _save_json_config(self) -> None:
        """Save current JSON config to file."""
        config_path = Path(self.config_file)
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.json_config, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values with priority resolution.
        
        Returns:
            Dictionary of all configuration values
        """
        # Start with defaults
        config = self.DEFAULTS.copy()
        
        # Override with environment
        config.update(self.env_config)
        
        # Override with JSON
        config.update(self.json_config)
        
        # Override with runtime
        config.update(self.runtime_config)
        
        return config
    
    def reset_to_defaults(self, persist: bool = False) -> None:
        """Reset all configuration to default values.
        
        Args:
            persist: If True, save defaults to JSON config file
        """
        self.runtime_config.clear()
        
        if persist:
            self.json_config = self.DEFAULTS.copy()
            self._save_json_config()
        
        logger.info("Configuration reset to defaults")
    
    def export_config(self, file_path: str) -> None:
        """Export current configuration to a file.
        
        Args:
            file_path: Path to export file
        """
        config = self.get_all()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Exported configuration to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            raise
    
    def import_config(self, file_path: str, persist: bool = False) -> None:
        """Import configuration from a file.
        
        Args:
            file_path: Path to import file
            persist: If True, save imported config to JSON file
        """
        try:
            with open(file_path, 'r') as f:
                imported_config = json.load(f)
            
            # Update runtime config
            self.runtime_config.update(imported_config)
            
            if persist:
                self.json_config.update(imported_config)
                self._save_json_config()
            
            logger.info(f"Imported configuration from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            raise
    
    def get_config_source(self, key: str) -> str:
        """Get the source of a configuration value.
        
        Args:
            key: Configuration key
        
        Returns:
            Source name: "runtime", "json", "env", "default", or "not_found"
        """
        if key in self.runtime_config:
            return "runtime"
        elif key in self.json_config:
            return "json"
        elif key in self.env_config:
            return "env"
        elif key in self.DEFAULTS:
            return "default"
        else:
            return "not_found"
    
    def validate(self) -> bool:
        """Validate configuration values.
        
        Returns:
            True if configuration is valid
        """
        config = self.get_all()
        
        # Validate numeric ranges
        if not 0 <= config.get("allocation_threshold", 0) <= 1:
            logger.error("allocation_threshold must be between 0 and 1")
            return False
        
        if config.get("max_vehicles_per_driver", 0) < config.get("min_vehicles_per_driver", 0):
            logger.error("max_vehicles_per_driver must be >= min_vehicles_per_driver")
            return False
        
        if config.get("email_port", 0) <= 0:
            logger.error("email_port must be positive")
            return False
        
        # Validate paths exist if specified
        template_path = config.get("template_path")
        if template_path and not Path(template_path).exists():
            logger.warning(f"Template path does not exist: {template_path}")
        
        return True
    
    def cleanup(self) -> None:
        """Clean up configuration service."""
        # Optionally save runtime config to JSON
        if self.runtime_config:
            logger.debug("Runtime config not persisted (use persist=True to save)")
        
        super().cleanup()


# Global configuration instance (singleton pattern)
_config_instance: Optional[UnifiedConfigurationService] = None


def get_config() -> UnifiedConfigurationService:
    """Get the global configuration instance.
    
    Returns:
        UnifiedConfigurationService instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = UnifiedConfigurationService()
        _config_instance.initialize()
    
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config_instance
    _config_instance = None
