"""Configuration management service."""

from typing import Optional, Any, Union
from pathlib import Path
import json
import yaml
import os
from dotenv import load_dotenv
from loguru import logger

from src.core.base_service import BaseService


class ConfigurationService(BaseService):
    """Service for managing application configuration.
    
    Handles configuration from multiple sources including
    files, environment variables, and runtime updates.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration service.
        
        Args:
            config_file: Path to configuration file.
        """
        super().__init__()
        
        self.config_file = config_file
        self.config_dir = Path("config")
        self.env_prefix = "RA_"  # Resource Allocation prefix
        
        # Configuration sources in priority order
        self.sources = {
            "defaults": {},
            "file": {},
            "env": {},
            "runtime": {}
        }
        
        # Load configuration
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()
    
    def initialize(self) -> None:
        """Initialize the configuration service."""
        logger.info("Initializing Configuration Service")
        
        # Create config directory if needed
        self.config_dir.mkdir(exist_ok=True)
        
        # Validate configuration
        if self.validate():
            logger.info("Configuration loaded successfully")
        else:
            logger.warning("Configuration validation failed")
        
        self._initialized = True
    
    def validate(self) -> bool:
        """Validate the configuration.
        
        Returns:
            True if configuration is valid.
        """
        # Check required settings
        required = [
            "max_vehicles_per_driver",
            "min_vehicles_per_driver"
        ]
        
        for key in required:
            if not self.get(key):
                logger.error(f"Required configuration missing: {key}")
                return False
        
        # Validate ranges
        max_vehicles = self.get("max_vehicles_per_driver", 0)
        min_vehicles = self.get("min_vehicles_per_driver", 0)
        
        if max_vehicles < min_vehicles:
            logger.error("Max vehicles per driver less than minimum")
            return False
        
        return True
    
    def _load_defaults(self):
        """Load default configuration."""
        self.sources["defaults"] = {
            # Application settings
            "app_name": "Resource Management System",
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO",
            
            # Allocation settings
            "max_vehicles_per_driver": 3,
            "min_vehicles_per_driver": 1,
            "priority_weight_factor": 1.5,
            "allocation_threshold": 0.8,
            "enable_optimization": True,
            "enable_validation": True,
            
            # Excel settings
            "use_xlwings": False,
            "excel_visible": False,
            "display_alerts": False,
            "template_path": "",
            "apply_borders": True,
            "border_style": "thick",
            "section_border_style": "thick",
            "internal_border_style": "thin",
            "header_border_style": "medium",
            
            # Email settings
            "email_enabled": False,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "email_username": "",
            "email_password": "",
            "from_email": "noreply@resourceallocation.com",
            "from_name": "Resource Management System",
            "default_recipients": [],
            
            # Cache settings
            "cache_enabled": True,
            "cache_ttl": 3600,
            "max_memory_cache_size": 1000,
            "cache_directory": ".cache",
            
            # Performance settings
            "max_workers": 4,
            "batch_size": 100,
            "timeout": 300,
            
            # File paths
            "log_file": "logs/resource_allocation.log",
            "data_directory": "data",
            "output_directory": "outputs",
            "backup_directory": "backups"
        }
    
    def _load_from_file(self):
        """Load configuration from file."""
        if self.config_file:
            config_path = Path(self.config_file)
        else:
            # Look for config files in order of preference
            config_candidates = [
                self.config_dir / "settings.json",
                self.config_dir / "settings.yaml",
                self.config_dir / "config.json",
                self.config_dir / "config.yaml",
                Path("settings.json"),
                Path("config.json")
            ]
            
            config_path = None
            for candidate in config_candidates:
                if candidate.exists():
                    config_path = candidate
                    break
        
        if config_path and config_path.exists():
            try:
                with open(config_path) as f:
                    if config_path.suffix == ".json":
                        self.sources["file"] = json.load(f)
                    elif config_path.suffix in [".yaml", ".yml"]:
                        self.sources["file"] = yaml.safe_load(f)
                    else:
                        logger.warning(f"Unknown config file type: {config_path}")
                
                logger.info(f"Configuration loaded from: {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Load .env file if exists
        load_dotenv()
        
        # Map environment variables to config keys
        env_mapping = {
            "RA_DEBUG": ("debug", lambda x: x.lower() == "true"),
            "RA_LOG_LEVEL": ("log_level", str),
            "RA_MAX_VEHICLES": ("max_vehicles_per_driver", int),
            "RA_MIN_VEHICLES": ("min_vehicles_per_driver", int),
            "RA_EXCEL_VISIBLE": ("excel_visible", lambda x: x.lower() == "true"),
            "RA_EMAIL_ENABLED": ("email_enabled", lambda x: x.lower() == "true"),
            "RA_SMTP_HOST": ("smtp_host", str),
            "RA_SMTP_PORT": ("smtp_port", int),
            "RA_EMAIL_USERNAME": ("email_username", str),
            "RA_EMAIL_PASSWORD": ("email_password", str),
            "RA_CACHE_ENABLED": ("cache_enabled", lambda x: x.lower() == "true"),
            "RA_CACHE_TTL": ("cache_ttl", int),
            "RA_MAX_WORKERS": ("max_workers", int)
        }
        
        for env_key, (config_key, converter) in env_mapping.items():
            env_value = os.environ.get(env_key)
            if env_value:
                try:
                    self.sources["env"][config_key] = converter(env_value)
                    logger.debug(f"Loaded from env: {config_key}")
                except Exception as e:
                    logger.error(f"Failed to parse env var {env_key}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation).
            default: Default value if not found.
        
        Returns:
            Configuration value or default.
        """
        # Check sources in priority order
        for source in ["runtime", "env", "file", "defaults"]:
            value = self._get_nested(self.sources[source], key)
            if value is not None:
                return value
        
        return default
    
    def set(self, key: str, value: Any, persist: bool = False):
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation).
            value: Configuration value.
            persist: Whether to save to file.
        """
        self._set_nested(self.sources["runtime"], key, value)
        logger.debug(f"Configuration set: {key} = {value}")
        
        if persist:
            self.save()
    
    def _get_nested(self, data: dict, key: str) -> Any:
        """Get nested value using dot notation.
        
        Args:
            data: Dictionary to search.
            key: Dot-separated key.
        
        Returns:
            Value or None.
        """
        keys = key.split(".")
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _set_nested(self, data: dict, key: str, value: Any):
        """Set nested value using dot notation.
        
        Args:
            data: Dictionary to update.
            key: Dot-separated key.
            value: Value to set.
        """
        keys = key.split(".")
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_section(self, section: str) -> dict[str, Any]:
        """Get configuration section.
        
        Args:
            section: Section name.
        
        Returns:
            Section dictionary.
        """
        result = {}
        
        # Merge from all sources
        for source in ["defaults", "file", "env", "runtime"]:
            section_data = self.sources[source].get(section, {})
            if isinstance(section_data, dict):
                result.update(section_data)
        
        return result
    
    def save(self, file_path: Optional[str] = None):
        """Save configuration to file.
        
        Args:
            file_path: Path to save file.
        """
        save_path = file_path or self.config_dir / "settings.json"
        
        # Merge all sources
        merged = {}
        for source in ["defaults", "file", "env", "runtime"]:
            self._deep_merge(merged, self.sources[source])
        
        try:
            with open(save_path, "w") as f:
                json.dump(merged, f, indent=2)
            logger.info(f"Configuration saved to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _deep_merge(self, target: dict, source: dict):
        """Deep merge source into target.
        
        Args:
            target: Target dictionary.
            source: Source dictionary.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def reload(self):
        """Reload configuration from files."""
        logger.info("Reloading configuration")
        self.sources["file"] = {}
        self.sources["env"] = {}
        self._load_from_file()
        self._load_from_env()
    
    def export(self, format: str = "json") -> str:
        """Export configuration as string.
        
        Args:
            format: Export format (json or yaml).
        
        Returns:
            Configuration string.
        """
        # Merge all sources
        merged = {}
        for source in ["defaults", "file", "env", "runtime"]:
            self._deep_merge(merged, self.sources[source])
        
        if format == "json":
            return json.dumps(merged, indent=2)
        elif format == "yaml":
            return yaml.dump(merged, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.
        
        Returns:
            Merged configuration dictionary.
        """
        merged = {}
        for source in ["defaults", "file", "env", "runtime"]:
            self._deep_merge(merged, self.sources[source])
        return merged