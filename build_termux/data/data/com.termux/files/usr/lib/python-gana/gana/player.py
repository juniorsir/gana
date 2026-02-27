import subprocess
import socket
import json
import time
import os
import sys
import threading
import urllib.request
from .config import config
from .cache import cache
from .utils import is_unwanted_media
from .database import db  # <--- Added Import Here
from .logger import log_playback, log_error
import shutil

class Player:
    def __init__(self):
        self.proc = None
        self.sock_path = str(config.socket_path)

        if not shutil.which("mpv"):
            print("\n\033[31m[FATAL ERROR]\033[0m mpv media player is not installed.")
            print("Please install it using: \033[36mpkg install mpv\033[0m (Termux) or \033[36msudo apt install mpv\033[0m (Linux)")
            sys.exit(1)

        self.queue = []
        self.current_index = -1
        self.repeat_mode = 0      
        self.tracker_locked = False

        self.play_lock = threading.Lock() 
        self.last_action_time = 0         
        self.sleep_time_remaining = 0     
        
        self.action_file = f"{os.environ.get('TMPDIR', '/tmp')}/gana_action"

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def set_sleep_timer(self, minutes):
        self.sleep_time_remaining = int(minutes * 60)
        if self.is_running():
            self.update_notification()

    def _download_thumbnail(self, video_id):
        if not video_id: return None
        thumb_path = f"{os.environ.get('TMPDIR', '/tmp')}/gana_thumb.jpg"
        url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as response, open(thumb_path, 'wb') as out_file:
                out_file.write(response.read())
            return thumb_path
        except: return None

    def update_notification(self):
        notif_bin = "/data/data/com.termux/files/usr/bin/termux-notification"
        if not os.path.exists(notif_bin): return
        
        if 0 <= self.current_index < len(self.queue):
            track = self.queue[self.current_index]
            title = track.get('title', 'Unknown')[:50]
            vid_id = track.get('id', '')
        else:
            return

        content = "Gana 🎧  |  👆 Tap: +15m Sleep"
        if self.sleep_time_remaining > 0:
            mins_left = int(self.sleep_time_remaining // 60)
            content = f"Gana 🎧  |  🌙 Sleep in {mins_left}m"

        script_path = os.path.abspath(sys.argv[0])

        # Get playback status
        status = self.get_status()
        is_paused = status.get("paused", False)

        # Use Material icon names
        icon = "pause" if is_paused else "music_note"
        cmd = [
            notif_bin,
            "--id", "gana_playing",
            "--title", title,
            "--content", content,
            "--priority", "max",
            "--ongoing", 
            "--icon", icon,
            "--alert-once", 
            "--type", "media",
            "--media-play", f"python {script_path} --cmd pause",
            "--media-pause", f"python {script_path} --cmd pause",
            "--media-next", f"python {script_path} --cmd next",
            "--media-previous", f"python {script_path} --cmd prev",
            "--action", f"python {script_path} --cmd timer_add"
        ]

        thumb_path = self._download_thumbnail(vid_id)
        if thumb_path and os.path.exists(thumb_path):
            cmd.extend(["--image-path", thumb_path])

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    def _monitor_loop(self):
        while True:
            time.sleep(0.5) 
            
            # 1. External Commands
            if os.path.exists(self.action_file):
                try:
                    with open(self.action_file, "r") as f:
                        action = f.read().strip()
                    os.remove(self.action_file)
                    
                    if action == "pause": self.toggle_pause()
                    elif action == "next": self.play_next()
                    elif action == "prev": self.play_prev()
                    elif action == "timer_add":
                        self.sleep_time_remaining += 15 * 60
                        self.update_notification()
                except: pass

            # 2. Sleep Timer
            if self.sleep_time_remaining > 0 and self.is_running():
                old_mins = int(self.sleep_time_remaining // 60)
                self.sleep_time_remaining -= 0.5 
                new_mins = int(self.sleep_time_remaining // 60)

                if self.sleep_time_remaining <= 0:
                    self.sleep_time_remaining = 0
                    self.stop()
                    self.queue = [] 
                    continue 

                if old_mins != new_mins:
                    self.update_notification()

            if not self.is_running() or not self.queue:
                continue

            status = self.get_status()
            is_idle = status.get('idle')
            pos = float(status.get('position') or 0)
            dur = float(status.get('duration') or 1)
            is_buf = status.get('buffering')
            
            # 3. Auto Next
            if is_idle is True and not is_buf:
                if time.time() - self.last_action_time > 2.0:
                    self.play_next()
                continue

            # 4. 50% Preference Tracker
            if dur > 10 and (pos / dur) > 0.50 and not self.tracker_locked:
                self.tracker_locked = True
                if 0 <= self.current_index < len(self.queue):
                    title = self.queue[self.current_index].get('title', '')
                    if not is_unwanted_media(title) and not config.settings.get('music_mode'):
                        config.settings['music_mode'] = True
                        config.save()

    def load_playlist(self, tracks, start_index=0):
        self.queue = tracks
        self.current_index = start_index
        self.play_current()

    def add_to_queue(self, track):
        self.queue.append(track)

    def play_next(self):
        if time.time() - self.last_action_time < 1.0: return
        self.last_action_time = time.time()

        if self.repeat_mode == 1: 
            self.play_current()
            return

        original_index = self.current_index
        while self.current_index < len(self.queue) - 1:
            self.current_index += 1
            next_track = self.queue[self.current_index]
            if config.settings.get('music_mode') and is_unwanted_media(next_track.get('title', '')):
                continue
            self.play_current()
            return

        if self.repeat_mode == 2: 
            self.current_index = 0
            self.play_current()
        else:
            self.current_index = original_index
            self.stop()

    def play_prev(self):
        if time.time() - self.last_action_time < 1.0: return
        self.last_action_time = time.time()

        while self.current_index > 0:
            self.current_index -= 1
            prev_track = self.queue[self.current_index]
            if config.settings.get('music_mode') and is_unwanted_media(prev_track.get('title', '')):
                continue
            self.play_current()
            return
        self.seek(0)

    def play_current(self):
        with self.play_lock:
            self.tracker_locked = False 
            self.last_action_time = time.time()

            if 0 <= self.current_index < len(self.queue):
                track = self.queue[self.current_index]
                self.stop() 
                
                try:
                    self.start_mpv(track['url'], track['title'])
                    
                    # --- TRIGGER PLAYBACK LOG ---
                    log_playback(track['title'], track['url'])
                    
                    threading.Thread(target=self._download_thumbnail, args=(track.get('id'),), daemon=True).start()
                    
                    def background_cache():
                        cache.download_background(track['url'], track['title'])
                    threading.Thread(target=background_cache, daemon=True).start()
                    
                    self.update_notification()
                    
                    from .database import db
                    db.save_session(self.queue, self.current_index, 0, self.repeat_mode)
                    
                except Exception as e:
                    # --- TRIGGER ERROR LOG ---
                    log_error(f"Failed to play {track['title']}: {str(e)}")

    def toggle_repeat(self):
        # 0=Sequence (➡), 1=Repeat One (🔂), 2=Repeat All (🔁)
        self.repeat_mode = (self.repeat_mode + 1) % 3
        # Save immediately so preference persists if app crashes
        db.save_session(self.queue, self.current_index, 0, self.repeat_mode)
        return self.repeat_mode


    def remove_from_queue(self, index):
        if 0 <= index < len(self.queue):
            del self.queue[index]
            if index < self.current_index:
                self.current_index -= 1

    def start_mpv(self, url, title):
        local_file = cache.find(title)
        if not local_file:
            from .utils import is_online
            if not is_online():
                from .logger import log_error
                log_error(f"Playback failed: No internet to stream '{title}'")
                return # Stop silently, the monitor thread will eventually trigger auto-next or quit
        play_target = local_file if local_file else url

        if os.path.exists(self.sock_path):
            try: os.remove(self.sock_path)
            except: pass

        cmd = ["mpv", "--no-terminal", "--force-window=no", f"--input-ipc-server={self.sock_path}", f"--title={title}", "--idle=yes"]
        if not local_file and config.settings.get('low_data'):
            cmd.append("--ytdl-format=worstvideo[height<=240]+bestaudio/worst")
        
        cmd.append(play_target)
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for _ in range(20):
            if os.path.exists(self.sock_path): break
            time.sleep(0.1)

    def send_cmd(self, command):
        if not os.path.exists(self.sock_path): return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.sock_path)
            payload = json.dumps({"command": command}) + "\n"
            client.send(payload.encode())
            response = client.recv(4096).decode()
            client.close()
            return json.loads(response.split('\n')[0])
        except: return None

    def get_status(self):
        try:
            pos = self.send_cmd(["get_property", "time-pos"])
            dur = self.send_cmd(["get_property", "duration"])
            paused = self.send_cmd(["get_property", "pause"])
            idle = self.send_cmd(["get_property", "idle-active"])
            buf = self.send_cmd(["get_property", "paused-for-cache"]) 
            
            p_val = pos.get("data") if pos else 0
            d_val = dur.get("data") if dur else 0
            
            is_buffering = (buf and buf.get("data") is True) or (d_val == 0 and not idle.get("data"))
            
            return {
                "position": p_val,
                "duration": d_val or 1,
                "paused": paused.get("data") if paused else False,
                "idle": idle.get("data") if idle else False,
                "buffering": is_buffering
            }
        except:
            return {"position": 0, "duration": 1, "paused": False, "idle": True, "buffering": True}

    def toggle_pause(self):
        self.send_cmd(["cycle", "pause"])
        time.sleep(0.1)  # small delay so mpv updates state
        self.update_notification()
    def seek(self, seconds): self.send_cmd(["seek", str(seconds), "relative"])
    
    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=1.0) 
            except subprocess.TimeoutExpired:
                self.proc.kill()            
            except Exception: pass
            self.proc = None
            
            notif_bin = "/data/data/com.termux/files/usr/bin/termux-notification"
            if os.path.exists(notif_bin):
                try: subprocess.run([notif_bin, "--id", "gana_playing", "--action", "cancel"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except: pass
            
    def is_running(self): 
        return self.proc and self.proc.poll() is None

player = Player()
