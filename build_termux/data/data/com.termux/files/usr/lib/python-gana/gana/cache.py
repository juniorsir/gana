import os
import subprocess
import time
from pathlib import Path
from .config import config

class Cache:
    def __init__(self):
        self.cache_dir = config.cache_path
        # Maximum number of songs to keep offline
        self.limit = 5 

    def get_path(self, title):
        """Generates a safe filesystem path for a track title"""
        # Remove weird characters to make it a valid filename
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        # Fallback if title becomes empty
        if not safe_title:
            safe_title = f"track_{int(time.time())}"
            
        return self.cache_dir / f"{safe_title}.mp3"

    def find(self, title):
        """Checks if a song exists in cache. Returns path or None."""
        path = self.get_path(title)
        if path.exists():
            # 'Touch' the file to update its timestamp
            # This ensures frequently played songs aren't deleted by cleanup
            path.touch()
            return str(path)
        return None

    def download_background(self, url, title):
        """
        Downloads a track using yt-dlp. 
        Returns the path if successful, None otherwise.
        """
        target_path = self.get_path(title)
        
        # If already exists, just return it
        if target_path.exists():
            target_path.touch()
            return str(target_path)

        # Clean up old files before downloading new one
        self.cleanup()

        # yt-dlp command to extract audio
        cmd = [
            "yt-dlp",
            "-x",                      # Extract audio
            "--audio-format", "mp3",   # Convert to mp3
            "--audio-quality", "96K",  # Low bitrate for speed/storage
            "-o", str(target_path),    # Output path
            "--quiet",                 # No terminal output
            "--no-warnings",
            url
        ]

        try:
            subprocess.run(cmd, check=True)
            return str(target_path)
        except Exception as e:
            # If download fails, return None (Caller should stream instead)
            return None

    def cleanup(self):
        """Deletes oldest files if cache exceeds limit"""
        try:
            # List all mp3s
            files = list(self.cache_dir.glob("*.mp3"))
            
            # Sort by modification time (Oldest first)
            files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove files until we are under the limit
            while len(files) >= self.limit:
                oldest_file = files.pop(0)
                os.remove(oldest_file)
        except Exception:
            pass

    def clear_all(self):
        """Manually clear the entire cache"""
        for f in self.cache_dir.glob("*.mp3"):
            try:
                os.remove(f)
            except:
                pass

cache = Cache()
