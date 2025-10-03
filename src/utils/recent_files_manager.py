"""Recent Files Manager for tracking and persisting recently used files."""

from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import os


class FileFieldType(Enum):
    """Types of file fields that can be tracked for quick selection."""
    DAY_OF_OPS = "day_of_ops_files"
    DAILY_ROUTES = "daily_routes_files"
    DAILY_SUMMARY = "daily_summary_files"
    ASSOCIATE_LIST = "associate_files"
    SCORECARD_PDF = "scorecard_files"


@dataclass
class RecentFileInfo:
    """Information about a recently used file."""
    path: str
    last_used: str
    file_size: Optional[int] = None
    exists: bool = True
    display_name: Optional[str] = None
    use_count: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecentFileInfo':
        """Create from dictionary."""
        return cls(**data)


class RecentFilesManager:
    """Manages recent files for each field type."""
    
    def __init__(self, config_dir: Path = None):
        """Initialize the recent files manager.
        
        Args:
            config_dir: Directory to store config file. Defaults to 'config'.
        """
        if config_dir is None:
            config_dir = Path("config")
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "recent_files.json"
        
        # Default settings
        self.max_files = 10
        self.auto_cleanup_days = 30
        self.show_relative_paths = True
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._data = self._load_data()
        
        # Cleanup on initialization
        self.cleanup_old_entries()
        self.cleanup_missing_files()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load recent files data from JSON file."""
        if not self.config_file.exists():
            # Return default structure
            return {
                FileFieldType.DAY_OF_OPS.value: [],
                FileFieldType.DAILY_ROUTES.value: [],
                FileFieldType.DAILY_SUMMARY.value: [],
                FileFieldType.ASSOCIATE_LIST.value: [],
                FileFieldType.SCORECARD_PDF.value: [],
                "settings": {
                    "max_recent_files": self.max_files,
                    "auto_cleanup_days": self.auto_cleanup_days,
                    "show_relative_paths": self.show_relative_paths
                }
            }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Apply settings
            if "settings" in data:
                self.max_files = data["settings"].get("max_recent_files", self.max_files)
                self.auto_cleanup_days = data["settings"].get("auto_cleanup_days", self.auto_cleanup_days)
                self.show_relative_paths = data["settings"].get("show_relative_paths", self.show_relative_paths)

            for field in FileFieldType:
                data.setdefault(field.value, [])
            
            return data
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load recent files: {e}")
            return self._load_data()  # Return default structure
    
    def _save_data(self):
        """Save recent files data to JSON file."""
        try:
            # Update settings
            self._data["settings"] = {
                "max_recent_files": self.max_files,
                "auto_cleanup_days": self.auto_cleanup_days,
                "show_relative_paths": self.show_relative_paths
            }
            
            # Write to temporary file first
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.config_file)
            
        except IOError as e:
            logger.error(f"Failed to save recent files: {e}")
    
    def add_recent_file(self, field_type: FileFieldType, file_path: str):
        """Add file to recent files list.
        
        Args:
            field_type: The type of file field.
            file_path: Path to the file to add.
        """
        file_path = str(Path(file_path).resolve())
        field_key = field_type.value
        
        # Get existing files
        recent_files = self._data.get(field_key, [])
        
        # Check if file already exists
        existing_index = None
        for i, file_info in enumerate(recent_files):
            if file_info["path"] == file_path:
                existing_index = i
                break
        
        # Create or update file info
        try:
            path_obj = Path(file_path)
            file_size = path_obj.stat().st_size if path_obj.exists() else None
            exists = path_obj.exists()
        except:
            file_size = None
            exists = False
        
        if existing_index is not None:
            # Update existing entry
            file_info = recent_files[existing_index]
            file_info["last_used"] = datetime.now().isoformat()
            file_info["use_count"] = file_info.get("use_count", 0) + 1
            file_info["file_size"] = file_size
            file_info["exists"] = exists
            # Move to front
            recent_files.pop(existing_index)
            recent_files.insert(0, file_info)
        else:
            # Add new entry
            new_file = RecentFileInfo(
                path=file_path,
                last_used=datetime.now().isoformat(),
                file_size=file_size,
                exists=exists,
                display_name=Path(file_path).name,
                use_count=1
            )
            recent_files.insert(0, new_file.to_dict())
        
        # Limit list size
        recent_files = recent_files[:self.max_files]
        
        # Update data
        self._data[field_key] = recent_files
        self._save_data()
        
        logger.debug(f"Added recent file: {file_path} to {field_type.name}")
    
    def get_recent_files(self, field_type: FileFieldType) -> List[RecentFileInfo]:
        """Get recent files for specific field type.
        
        Args:
            field_type: The type of file field.
            
        Returns:
            List of RecentFileInfo objects, sorted by recency/frequency.
        """
        field_key = field_type.value
        recent_files = self._data.get(field_key, [])
        
        # Convert to RecentFileInfo objects
        file_infos = []
        for file_data in recent_files:
            try:
                file_info = RecentFileInfo.from_dict(file_data)
                # Update existence status
                file_info.exists = Path(file_info.path).exists()
                file_infos.append(file_info)
            except Exception as e:
                logger.warning(f"Invalid recent file data: {e}")
        
        # Sort by smart algorithm (recency + frequency)
        def sort_key(info: RecentFileInfo) -> float:
            # Calculate recency score (0-1, higher is more recent)
            try:
                last_used = datetime.fromisoformat(info.last_used)
                days_ago = (datetime.now() - last_used).days
                recency_score = max(0, 1 - (days_ago / 30))  # Linear decay over 30 days
            except:
                recency_score = 0
            
            # Calculate frequency score (normalized)
            frequency_score = min(1.0, info.use_count / 10)  # Cap at 10 uses
            
            # Weighted combination (70% recency, 30% frequency)
            return -(0.7 * recency_score + 0.3 * frequency_score)
        
        file_infos.sort(key=sort_key)
        
        return file_infos
    
    def remove_recent_file(self, field_type: FileFieldType, file_path: str):
        """Remove specific file from recent files.
        
        Args:
            field_type: The type of file field.
            file_path: Path to the file to remove.
        """
        field_key = field_type.value
        recent_files = self._data.get(field_key, [])
        
        # Remove matching file
        self._data[field_key] = [
            f for f in recent_files 
            if f["path"] != str(Path(file_path).resolve())
        ]
        
        self._save_data()
        logger.debug(f"Removed recent file: {file_path} from {field_type.name}")
    
    def clear_recent_files(self, field_type: FileFieldType):
        """Clear all recent files for field type.
        
        Args:
            field_type: The type of file field.
        """
        field_key = field_type.value
        self._data[field_key] = []
        self._save_data()
        logger.info(f"Cleared recent files for {field_type.name}")
    
    def cleanup_missing_files(self):
        """Remove files that no longer exist from all lists."""
        removed_count = 0
        
        for field_type in FileFieldType:
            field_key = field_type.value
            recent_files = self._data.get(field_key, [])
            
            # Filter existing files
            existing_files = []
            for file_info in recent_files:
                if Path(file_info["path"]).exists():
                    existing_files.append(file_info)
                else:
                    removed_count += 1
            
            self._data[field_key] = existing_files
        
        if removed_count > 0:
            self._save_data()
            logger.info(f"Cleaned up {removed_count} missing files")
    
    def cleanup_old_entries(self):
        """Remove entries older than auto_cleanup_days."""
        if self.auto_cleanup_days <= 0:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.auto_cleanup_days)
        removed_count = 0
        
        for field_type in FileFieldType:
            field_key = field_type.value
            recent_files = self._data.get(field_key, [])
            
            # Filter recent files
            filtered_files = []
            for file_info in recent_files:
                try:
                    last_used = datetime.fromisoformat(file_info["last_used"])
                    if last_used > cutoff_date:
                        filtered_files.append(file_info)
                    else:
                        removed_count += 1
                except:
                    filtered_files.append(file_info)  # Keep if date parsing fails
            
            self._data[field_key] = filtered_files
        
        if removed_count > 0:
            self._save_data()
            logger.info(f"Cleaned up {removed_count} old entries")
    
    def get_display_path(self, file_path: str, max_length: int = 50) -> str:
        """Get intelligent display path for UI.
        
        Args:
            file_path: The file path to display.
            max_length: Maximum length for display.
            
        Returns:
            User-friendly display path.
        """
        if not self.show_relative_paths:
            return file_path
        
        path = Path(file_path)
        
        # Try to make relative to common directories
        base_dirs = [
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.home() / "Downloads",
            Path.home(),
            Path.cwd()
        ]
        
        for base in base_dirs:
            try:
                rel_path = path.relative_to(base)
                display = str(rel_path)
                
                # Add prefix for home directory
                if base == Path.home():
                    display = f"~/{rel_path}"
                elif base == Path.home() / "Documents":
                    display = f"~/Documents/{rel_path}"
                elif base == Path.home() / "Desktop":
                    display = f"~/Desktop/{rel_path}"
                elif base == Path.home() / "Downloads":
                    display = f"~/Downloads/{rel_path}"
                
                if len(display) <= max_length:
                    return display
                    
            except ValueError:
                continue
        
        # If path is too long, truncate intelligently
        if len(str(path)) > max_length:
            # Show parent directory and filename
            if path.parent.name:
                return f".../{path.parent.name}/{path.name}"
            else:
                return f".../{path.name}"
        
        return str(path)
    
    def update_settings(self, **kwargs):
        """Update manager settings.
        
        Args:
            max_files: Maximum number of recent files per type.
            auto_cleanup_days: Days before auto-cleanup.
            show_relative_paths: Whether to show relative paths.
        """
        if "max_files" in kwargs:
            self.max_files = kwargs["max_files"]
        if "auto_cleanup_days" in kwargs:
            self.auto_cleanup_days = kwargs["auto_cleanup_days"]
        if "show_relative_paths" in kwargs:
            self.show_relative_paths = kwargs["show_relative_paths"]
        
        self._save_data()