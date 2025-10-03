"""Logging service for application-wide logging."""

from typing import Optional, Any
from pathlib import Path
from datetime import datetime
import sys
from loguru import logger
from logging.handlers import RotatingFileHandler
import logging

from src.core.base_service import BaseService


class LoggingService(BaseService):
    """Service for centralized logging management.
    
    Provides structured logging with multiple outputs,
    log rotation, and filtering capabilities.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the logging service.
        
        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        
        # Configuration
        self.log_level = self.get_config("log_level", "INFO")
        self.log_file = Path(self.get_config("log_file", "logs/resource_allocation.log"))
        self.max_file_size = self.get_config("max_log_file_size", 10 * 1024 * 1024)  # 10MB
        self.backup_count = self.get_config("log_backup_count", 5)
        self.log_format = self.get_config(
            "log_format",
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        self.json_logs = self.get_config("json_logs", False)
        
        # Log handlers
        self.handlers = []
        
        # Configure loguru
        self._configure_loguru()
    
    def initialize(self) -> None:
        """Initialize the logging service."""
        logger.info("Initializing Logging Service")
        
        # Create log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Add handlers
        self._add_file_handler()
        self._add_console_handler()
        
        if self.json_logs:
            self._add_json_handler()
        
        logger.info(f"Logging initialized: level={self.log_level}, file={self.log_file}")
        self._initialized = True
    
    def validate(self) -> bool:
        """Validate the service configuration.
        
        Returns:
            True if configuration is valid.
        """
        valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            logger.error(f"Invalid log level: {self.log_level}")
            return False
        
        return True
    
    def cleanup(self) -> None:
        """Clean up logging resources."""
        # Remove all added handlers
        for handler_id in self.handlers:
            try:
                logger.remove(handler_id)
            except:
                pass
        
        super().cleanup()
    
    def _configure_loguru(self):
        """Configure loguru logger."""
        # Remove default handler
        logger.remove()
        
        # Set activation levels
        logger.enable("src")
    
    def _add_file_handler(self):
        """Add file handler with rotation."""
        handler_id = logger.add(
            self.log_file,
            rotation=self.max_file_size,
            retention=self.backup_count,
            level=self.log_level,
            format=self.log_format,
            backtrace=True,
            diagnose=True,
            enqueue=True  # Thread-safe
        )
        self.handlers.append(handler_id)
    
    def _add_console_handler(self):
        """Add console handler."""
        handler_id = logger.add(
            sys.stderr,
            level=self.log_level,
            format=self.log_format,
            colorize=True
        )
        self.handlers.append(handler_id)
    
    def _add_json_handler(self):
        """Add JSON file handler."""
        json_file = self.log_file.with_suffix(".json")
        
        def json_format(record):
            """Format log record as JSON."""
            return {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "function": record["function"],
                "line": record["line"],
                "message": record["message"],
                "extra": record.get("extra", {})
            }
        
        handler_id = logger.add(
            json_file,
            rotation=self.max_file_size,
            retention=self.backup_count,
            level=self.log_level,
            format=json_format,
            serialize=True,
            enqueue=True
        )
        self.handlers.append(handler_id)
    
    def set_level(self, level: str):
        """Set logging level.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        self.log_level = level.upper()
        
        # Update existing handlers
        for handler_id in self.handlers:
            logger.remove(handler_id)
        
        self.handlers = []
        self._add_file_handler()
        self._add_console_handler()
        
        if self.json_logs:
            self._add_json_handler()
        
        logger.info(f"Log level changed to: {self.log_level}")
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message.
        
        Args:
            level: Log level.
            message: Log message.
            **kwargs: Additional context.
        """
        level = level.upper()
        
        if kwargs:
            logger.bind(**kwargs).log(level, message)
        else:
            logger.log(level, message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self.log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self.log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self.log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self.log("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback.
        
        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        if kwargs:
            logger.bind(**kwargs).exception(message)
        else:
            logger.exception(message)
    
    def add_context(self, **kwargs) -> logger:
        """Add context to logger.
        
        Args:
            **kwargs: Context variables.
        
        Returns:
            Contextualized logger.
        """
        return logger.bind(**kwargs)
    
    def create_logger(self, name: str) -> logger:
        """Create a named logger.
        
        Args:
            name: Logger name.
        
        Returns:
            Named logger instance.
        """
        return logger.bind(logger_name=name)
    
    def get_log_file_path(self) -> Path:
        """Get current log file path.
        
        Returns:
            Log file path.
        """
        return self.log_file
    
    def get_recent_logs(self, lines: int = 100, level: Optional[str] = None) -> list[str]:
        """Get recent log entries.
        
        Args:
            lines: Number of lines to retrieve.
            level: Filter by log level.
        
        Returns:
            List of log entries.
        """
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file) as f:
                all_lines = f.readlines()
            
            # Get last N lines
            recent = all_lines[-lines:] if lines < len(all_lines) else all_lines
            
            # Filter by level if specified
            if level:
                level = level.upper()
                filtered = []
                for line in recent:
                    if f"| {level}" in line or f"|{level}" in line:
                        filtered.append(line)
                return filtered
            
            return recent
            
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            return []
    
    def clear_logs(self) -> bool:
        """Clear log files.
        
        Returns:
            True if cleared successfully.
        """
        try:
            # Clear main log file
            if self.log_file.exists():
                self.log_file.unlink()
            
            # Clear JSON log if exists
            json_file = self.log_file.with_suffix(".json")
            if json_file.exists():
                json_file.unlink()
            
            # Clear rotated logs
            for backup in self.log_file.parent.glob(f"{self.log_file.stem}*.log*"):
                backup.unlink()
            
            logger.info("Log files cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear logs: {e}")
            return False
    
    def archive_logs(self, archive_path: Optional[Path] = None) -> bool:
        """Archive current logs.
        
        Args:
            archive_path: Path for archive.
        
        Returns:
            True if archived successfully.
        """
        try:
            import zipfile
            
            archive_path = archive_path or Path(f"logs_archive_{datetime.now():%Y%m%d_%H%M%S}.zip")
            
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add main log
                if self.log_file.exists():
                    zf.write(self.log_file, self.log_file.name)
                
                # Add JSON log
                json_file = self.log_file.with_suffix(".json")
                if json_file.exists():
                    zf.write(json_file, json_file.name)
                
                # Add rotated logs
                for backup in self.log_file.parent.glob(f"{self.log_file.stem}*.log*"):
                    zf.write(backup, backup.name)
            
            logger.info(f"Logs archived to: {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive logs: {e}")
            return False