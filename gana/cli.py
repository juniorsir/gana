#!/usr/bin/env python3
import sys
import os
import argparse

# -----------------------------------------------------------------
# 1. FAST IPC COMMAND HANDLER
# -----------------------------------------------------------------
if len(sys.argv) == 3 and sys.argv[1] == '--cmd':
    action = sys.argv[2]
    try:
        with open(f"{os.environ.get('TMPDIR', '/tmp')}/gana_action", "w") as f:
            f.write(action)
    except: pass
    sys.exit(0)

# -----------------------------------------------------------------
# 2. APP IMPORTS
# -----------------------------------------------------------------
import threading
import time
import subprocess
from gana.ui import ui
from gana.search import Searcher
from gana.player import player
from gana.database import db
from gana.config import config
from gana.logger import log_error
import traceback
from gana.utils import is_online

CYAN = "\033[38;5;51m"
GREEN = "\033[38;5;46m"
YELLOW = "\033[38;5;226m"
PURPLE = "\033[38;5;201m"
RESET = "\033[0m"
BOLD = "\033[1m"
# -----------------------------------------------------------------
# 3. BACKGROUND LISTENER
def start_media_button_listener():
    termux_api_path = "/data/data/com.termux/files/usr/bin/termux-media-player"
    if not os.path.exists(termux_api_path): return

    # --- NEW: SAFETY CHECK FOR Termux:API APK ---
    # If the APK isn't installed, this command will hang forever.
    # We use python's subprocess timeout to catch it.
    try:
        subprocess.run(["termux-battery-status"], timeout=1.0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        # The APK is missing! Silently abort the listener so the app doesn't freeze.
        return
    except: pass

    def listener_loop():
        try:
            subprocess.run(["termux-media-player", "play", "system/media/audio/ui/click.ogg"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass
        
        while True:
            try:
                result = subprocess.run([termux_api_path, "info"], capture_output=True, text=True)
                output = result.stdout.lower()
                if player.is_running():
                    if "play" in output or "pause" in output: player.toggle_pause()
                    elif "next" in output: player.play_next()
                    elif "previous" in output: player.play_prev()
            except: pass
            time.sleep(0.5)

    threading.Thread(target=listener_loop, daemon=True).start()

# -----------------------------------------------------------------
# 4. CORE APPLICATION LOGIC
# -----------------------------------------------------------------
def resume_session():
    queue, idx, pos, rpt = db.load_session()
    if queue and idx >= 0:
        ui.animate_resume()
        player.repeat_mode = rpt
        player.load_playlist(queue, start_index=idx)
        if pos > 0: player.seek(int(pos))
        ui.player_screen(player)
    else:
        print(f"\n{YELLOW}No saved session found to resume.{RESET}")
        time.sleep(1)

def handle_search(initial_query=None):
    if not is_online():
        ui.clear()
        print(f"\n{YELLOW}OFFLINE: Please connect to the internet to search.{RESET}")
        time.sleep(2)
        return
    searcher = Searcher()
    if initial_query:
        query = initial_query
        db.add_search(query)
    else:
        query = ui.live_search(searcher)
        if not query or not query.strip(): return
        db.add_search(query)

    ui.clear()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=ui.spinner, args=(stop_event,))
    spinner_thread.start()

    results = searcher.search(query)
    stop_event.set()
    spinner_thread.join()

    if not results:
        print(f"\n{YELLOW}No results found for '{query}'.{RESET}")
        time.sleep(1.5)
        return

    playlist, start_index = ui.menu_selector(results)
    if playlist:
        player.load_playlist(playlist, start_index=start_index)
        track = playlist[start_index]
        db.add_history(track['id'], track['title'], track['url'])
        ui.player_screen(player)

def handle_direct_play(query_or_url):
    if not is_online():
        print(f"\n{YELLOW}OFFLINE: Cannot fetch media data without an internet connection.{RESET}")
        time.sleep(2)
        return
    searcher = Searcher()
    ui.clear()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=ui.spinner, args=(stop_event,))
    spinner_thread.start()

    results = searcher.search(query_or_url)
    stop_event.set()
    spinner_thread.join()

    if not results:
        print(f"\n{YELLOW}Could not load media: {query_or_url}{RESET}")
        return

    track = results[0]
    db.add_history(track['id'], track['title'], track['url'])
    db.add_search(query_or_url)
    
    player.load_playlist([track], start_index=0)
    ui.player_screen(player)

def show_history():
    raw_hist = db.get_history()
    if not raw_hist:
        print(f"\n{YELLOW}History is empty.{RESET}")
        time.sleep(1)
        return

    formatted_list = [{'id': h[0], 'title': h[1], 'url': h[2], 'duration': 'HIST'} for h in raw_hist]
    playlist, start_index = ui.menu_selector(formatted_list, is_history=True)
    if playlist:
        player.load_playlist(playlist, start_index=start_index)
        ui.player_screen(player)

def set_timer():
    ui.clear()
    print(f"\n{CYAN}--- SLEEP TIMER ---{RESET}")
    print(f"Current: {int(player.sleep_time_remaining // 60)}m left")
    print("Minutes until stop (0 to disable):")
    try:
        val = input(f"{GREEN}>> {RESET}").strip()
        if not val: return
        mins = float(val)
        player.set_sleep_timer(mins)
        if mins == 0: print(f"{YELLOW}Timer cleared.{RESET}")
        else: print(f"{GREEN}Timer set to {mins}m.{RESET}")
        time.sleep(1)
    except: pass

# -----------------------------------------------------------------
# 5. USER GUIDE (PRINTED ON `gana help`)
# -----------------------------------------------------------------
def print_help_guide():
    ui.clear()
    
    # 1. Pulsing Logo Animation
    logo = [
        "  ██████╗  █████╗ ███╗   ██╗ █████╗ ",
        " ██╔════╝ ██╔══██╗████╗  ██║██╔══██╗",
        " ██║  ███╗███████║██╔██╗ ██║███████║",
        " ██║   ██║██╔══██║██║╚██╗██║██╔══██║",
        " ╚██████╔╝██║  ██║██║ ╚████║██║  ██║",
        "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
    ]
    
    # Quick pulse effect before settling on Cyan
    for color in [PURPLE, GREEN, YELLOW, CYAN]:
        ui.clear()
        print(f"{color}{BOLD}")
        for line in logo:
            print(line)
        time.sleep(0.15)
        
    print(f"{PURPLE} ─────────────────────────────────────{RESET}")
    print(f"{GREEN}   The Ultimate Hacker Music Player{RESET}")
    print(f"{PURPLE} ─────────────────────────────────────{RESET}\n")
    time.sleep(0.3)

    # 2. Typewriter Effect Helper
    def type_text(text, speed=0.01):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(speed)
        print() # New line at the end

    type_text(f"{CYAN}{BOLD}📖 GANA USER GUIDE:{RESET}", 0.03)
    type_text("GANA is installed globally. Launch it from anywhere!\n", 0.01)
    time.sleep(0.2)

    # 3. Staggered Commands Section
    print(f"{YELLOW}COMMANDS:{RESET}")
    commands = [
        f"  {GREEN}gana{RESET}                     Launch the Interactive Dashboard",
        f"  {GREEN}gana play \"lofi\"{RESET}         Instantly play the first result",
        f"  {GREEN}gana play <URL>{RESET}          Play a direct YouTube link",
        f"  {GREEN}gana search \"phonk\"{RESET}      Skip directly to the search UI",
        f"  {GREEN}gana resume{RESET}              Instantly resume your last session",
        f"  {GREEN}gana history{RESET}             View your playback history\n"
    ]
    for cmd in commands:
        type_text(cmd, 0.005) # Super fast typing
    time.sleep(0.2)

    # 4. Staggered Hotkeys Section
    print(f"{YELLOW}UI HOTKEYS (While Playing):{RESET}")
    hotkeys = [
        f"  {CYAN}[SPACE]{RESET}        Pause / Resume music",
        f"  {CYAN}[ ← / → ]{RESET}      Seek backward / forward 10 seconds",
        f"  {CYAN}[ N / P ]{RESET}      Skip to Next / Previous song",
        f"  {CYAN}[ S ]{RESET}          Open {PURPLE}✨ AI Recommendations HUD{RESET}",
        f"  {CYAN}[ V ]{RESET}          View Queue & Loop settings",
        f"  {CYAN}[ B ]{RESET}          Background Mode (Return to menu while playing)",
        f"  {CYAN}[ Q ]{RESET}          Stop music and quit\n"
    ]
    for hk in hotkeys:
        type_text(hk, 0.005)
    time.sleep(0.2)

    # 5. Pro Tips Section
    print(f"{YELLOW}PRO TIPS:{RESET}")
    tips = [
        f"  1. {BOLD}Offline Mode:{RESET} Songs you play are automatically cached. Turn off",
        f"     your internet, go to History, and play them offline!",
        f"  2. {BOLD}Lock Screen:{RESET} Use your Bluetooth earbuds or swipe down your",
        f"     notification bar to control music while the app is in the background.\n"
    ]
    for tip in tips:
        type_text(tip, 0.01)
    
    time.sleep(0.5)
    type_text(f"{GREEN}Type '{BOLD}gana{RESET}{GREEN}' to start listening! 🎧{RESET}", 0.05)
# -----------------------------------------------------------------
# 5. MAIN MENU LOOP
# -----------------------------------------------------------------
def main_loop():
    while True:
        has_session = False
        try:
            q, i, p, r = db.load_session()
            if q and len(q) > 0: has_session = True
        except: pass

        action = ui.main_menu(player, has_session=has_session)

        if action == 'search': handle_search()
        elif action == 'history': show_history()
        elif action == 'resume': resume_session()
        elif action == 'timer': set_timer()
        elif action == 'player': ui.player_screen(player)
        elif action == 'low_data':
            config.settings['low_data'] = not config.settings['low_data']
            config.save()
        elif action == 'music_mode':
            config.settings['music_mode'] = not config.settings.get('music_mode', False)
            config.save()
        elif action == 'stop':
            player.stop()
            player.queue = []
            player.set_sleep_timer(0)
        elif action == 'quit':
            if player.queue:
                status = player.get_status()
                pos = status.get('position', 0)
                db.save_session(player.queue, player.current_index, pos, player.repeat_mode)
            player.stop()
            ui.animate_shutdown()
            sys.exit()

def main():
    parser = argparse.ArgumentParser(description="GANA: Hacker-style CLI Music Player")
    parser.add_argument("command", nargs="?", choices=["search", "play", "history", "resume", "help"], help="Direct command to execute")
    parser.add_argument("query", nargs="*", help="Query string or URL for the command")
    parser.add_argument("--low-data", action="store_true", help="Force low data mode for this session")
    parser.add_argument("--music-mode", action="store_true", help="Force smart music mode for this session")
    
    args = parser.parse_args()

    try:
        start_media_button_listener()
        if args.command == "help" or "--help" in sys.argv or "-h" in sys.argv:
            print_help_guide()
            sys.exit(0)

        if args.low_data: config.settings['low_data'] = True
        if args.music_mode: config.settings['music_mode'] = True

        if args.command == "search":
            query_str = " ".join(args.query)
            handle_search(initial_query=query_str)
            main_loop()
        elif args.command == "play":
            query_str = " ".join(args.query)
            if not query_str:
                print(f"{YELLOW}Error: Please provide a search term or URL to play.{RESET}")
                sys.exit(1)
            handle_direct_play(query_str)
            main_loop()
        elif args.command == "history":
            show_history()
            main_loop()
        elif args.command == "resume":
            resume_session()
            main_loop()
        else:
            main_loop()

    except KeyboardInterrupt:
        player.stop()
        try: curses.endwin()
        except: pass
        print("\nForce Quit.")
        sys.exit()
    except Exception as e:
        # --- LOG FATAL CRASHES ---
        player.stop()
        try: curses.endwin()
        except: pass
        error_details = traceback.format_exc()
        log_error(f"FATAL APP CRASH:\n{error_details}")
        player.stop()
        print("Please report this issue.")
        print(f"\n{YELLOW}The app encountered a critical error and had to shut down.{RESET}")
        print(f"Please check {CYAN}~/.gana/logs/error.log{RESET} for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
