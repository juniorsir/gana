import os
import json
import tempfile
from pathlib import Path

class Config:
    def __init__(self):
        # Base directory for app data
        self.home = Path.home() / ".gana"
        self.home.mkdir(exist_ok=True)
        
        # File paths
        self.config_path = self.home / "config.json"
        self.db_path = self.home / "data.db"
        
        # Cache directory
        self.cache_path = self.home / "cache"
        self.cache_path.mkdir(exist_ok=True)

        self.log_path = self.home / "logs"
        self.log_path.mkdir(exist_ok=True)

        # MPV IPC Socket Path
        self.socket_path = Path(tempfile.gettempdir()) / "gana_mpv.sock"
        
        # Default Settings
        self.settings = {
            "low_data": False,
            "audio_only": True,
            "resolution": "480p",
            "music_mode": False
        }
        self.load()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.settings.update(json.load(f))
            except json.JSONDecodeError:
                pass 

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

config = Config()
