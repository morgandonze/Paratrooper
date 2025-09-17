"""
Configuration management for the PARA + Daily Task Management System.
"""

import json
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class for the task management system."""
    
    def __init__(self, task_file: Path, icon_set: str = "default", editor: str = "nvim"):
        self.task_file = task_file
        self.icon_set = icon_set
        self.editor = editor
        self.icon_sets = {
            "default": {"complete": "✓", "progress": "~", "incomplete": "○"},
            "dots": {"complete": "●", "progress": "◐", "incomplete": "○"},
            "check": {"complete": "☑", "progress": "☐", "incomplete": "☐"},
            "simple": {"complete": "x", "progress": "~", "incomplete": " "}
        }
        
        # Validate icon set
        if self.icon_set not in self.icon_sets:
            print(f"Warning: Unknown icon set '{self.icon_set}', using default")
            self.icon_set = "default"
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = Path.home() / ".paratrooper" / "config.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls(
                    task_file=Path(data['task_file']),
                    icon_set=data.get('icon_set', 'default'),
                    editor=data.get('editor', 'nvim')
                )
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading config: {e}")
                print("Creating default configuration...")
        
        # Create default config
        default_task_file = Path.home() / "tasks.md"
        config = cls(default_task_file)
        config.save(config_path)
        return config
    
    def save(self, config_path: Path):
        """Save configuration to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'task_file': str(self.task_file),
            'icon_set': self.icon_set,
            'editor': self.editor
        }
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def create_default_config(cls, config_path: Path, config: 'Config'):
        """Create a default configuration file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'task_file': str(config.task_file),
            'icon_set': config.icon_set,
            'editor': config.editor
        }
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
