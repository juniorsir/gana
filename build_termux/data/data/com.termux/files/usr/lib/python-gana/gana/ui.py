import os
import sys
import time
import curses
import threading
import random
import math
from .config import config
from .utils import is_unwanted_media

class UI:
    def clear(self):
        os.system('clear')

    def spinner(self, stop_event):
        chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        i = 0
        while not stop_event.is_set():
            sys.stdout.write(f"\r \033[96m{chars[i % len(chars)]} SYSTEM PROCESSING...\033[0m")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * 40 + "\r")

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, 255, -1)   # White
        curses.init_pair(2, 242, -1)   # Dim Gray
        curses.init_pair(3, 0, 250)    # Selection
        curses.init_pair(4, 51, -1)    # Cyan
        curses.init_pair(5, 46, -1)    # Green
        curses.init_pair(6, 214, -1)   # Amber
        curses.init_pair(7, 196, -1)   # Red
        curses.init_pair(20, curses.COLOR_BLACK, curses.COLOR_CYAN) # Cursor
        
        # Red Background for Stop Animation
        curses.init_pair(99, 255, 196) 

        rainbow = [196, 202, 208, 214, 220, 226, 190, 154, 118, 82, 46, 47, 48, 49, 50, 51, 45, 39, 33, 27, 21, 57, 93, 129, 165, 201]
        for i, c in enumerate(rainbow): 
            curses.init_pair(10 + i, c, -1)

    # ---------------------------------------------------------
    # ANIMATIONS
    # ---------------------------------------------------------
    def _draw_stop_anim(self, stdscr):
        """Instant Red Flash & Shrink Animation"""
        h, w = stdscr.getmaxyx()
        msg = "🛑 SYSTEM HALTED"
        
        # 1. Flash Red
        try:
            stdscr.bkgd(' ', curses.color_pair(99)) # Red BG
            stdscr.addstr(h//2, max(0, (w-len(msg))//2), msg, curses.color_pair(99) | curses.A_REVERSE | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.1)
            
            # 2. Flash Black
            stdscr.bkgd(' ', curses.color_pair(1)) 
            stdscr.refresh()
            time.sleep(0.05)
            
            # 3. Collapse Effect (CRT Power off style)
            stdscr.bkgd(' ', curses.color_pair(2)) # Dim BG
            mid = h // 2
            for i in range(mid):
                # Clear from top and bottom moving inwards
                stdscr.move(i, 0); stdscr.clrtoeol()
                stdscr.move(h-1-i, 0); stdscr.clrtoeol()
                # Draw closing line
                stdscr.addstr(i, 0, "─" * w, curses.color_pair(7))
                stdscr.addstr(h-1-i, 0, "─" * w, curses.color_pair(7))
                stdscr.refresh()
                time.sleep(0.01) # Fast collapse
        except: pass

    def animate_shutdown(self):
        def _anim(stdscr):
            try:
                self._init_colors(); curses.curs_set(0); h, w = stdscr.getmaxyx()
                msg = "GANA SYSTEM SHUTDOWN"
                stdscr.addstr(h//2 - 2, max(0, (w-len(msg))//2), msg, curses.color_pair(7) | curses.A_BOLD)
                bar = min(50, w-10); sx = max(0, (w-bar)//2)
                for i in range(bar+1):
                    stdscr.addstr(h//2, sx, "█"*i, curses.color_pair(7))
                    stdscr.refresh(); time.sleep(0.015)
                for i in range(h):
                    stdscr.move(i, 0); stdscr.clrtoeol(); stdscr.refresh(); time.sleep(0.005)
            except: pass
        curses.wrapper(_anim)

    def animate_resume(self):
        def _anim(stdscr):
            try:
                self._init_colors(); curses.curs_set(0); h, w = stdscr.getmaxyx()
                msgs = ["RESTORING MEMORY...", "READYING AUDIO ENGINE...", "BYPASSING FIREWALLS...", "SESSION RESTORED."]
                for i, m in enumerate(msgs):
                    stdscr.addstr(h//2 - 2 + i, max(0, (w-len(m))//2), m, curses.color_pair(5))
                    stdscr.refresh(); time.sleep(0.2)
                time.sleep(0.3)
            except: pass
        curses.wrapper(_anim)

    # ---------------------------------------------------------
    # MAIN MENU
    # ---------------------------------------------------------
    def main_menu(self, player_obj, has_session=False):
        def _draw(stdscr):
            curses.curs_set(0); stdscr.timeout(100); self._init_colors(); sel_idx = 0
            while True:
                stdscr.erase(); h, w = stdscr.getmaxyx()
                opts = [
                    {"id": "search", "label": "Search Database"},
                    {"id": "history", "label": "Playback History"},
                    {"id": "timer", "label": "Sleep Timer"},
                    {"id": "low_data", "label": "Low Data Mode"},
                    {"id": "music_mode", "label": "Smart Music Mode"},
                    {"id": "quit", "label": "Shutdown System"}
                ]
                if has_session and not player_obj.is_running():
                    opts.insert(0, {"id": "resume", "label": "▶ RESUME LAST SESSION"})
                if sel_idx >= len(opts): sel_idx = len(opts)-1

                try:
                    stdscr.addstr(1, 2, "GANA PLAYER ", curses.color_pair(4) | curses.A_BOLD)
                    if w > 20: stdscr.addstr(1, 14, "│ SYSTEM DASHBOARD", curses.color_pair(2))
                    stdscr.addstr(2, 2, "─" * max(0, w-4), curses.color_pair(2))
                    
                    for i, o in enumerate(opts):
                        if 4+i >= h-1: break
                        st = ""
                        if o['id']=='low_data': st = "[ON]" if config.settings.get('low_data') else "[OFF]"
                        elif o['id']=='music_mode': st = "[ON]" if config.settings.get('music_mode') else "[OFF]"
                        elif o['id']=='timer' and player_obj.sleep_time_remaining > 0:
                            st = f"[{int(player_obj.sleep_time_remaining//60)}m]"
                        
                        line = f" {o['label']}".ljust(25) + f" {st}".ljust(max(0, w-4))
                        attr = curses.color_pair(3) if i==sel_idx else (curses.color_pair(6) if o['id']=='resume' else curses.color_pair(1))
                        stdscr.addstr(4+i, 2, line[:max(0, w-3)], attr)

                    if player_obj.is_running() and player_obj.queue and h > 10:
                        t = player_obj.queue[player_obj.current_index]
                        stdscr.addstr(h-4, 2, "─"*max(0, w-4), curses.color_pair(2))
                        stdscr.addstr(h-3, 2, "▶ PLAYING: ", curses.color_pair(5)|curses.A_BOLD)
                        stdscr.addstr(t.get('title','?')[:max(0, w-20)], curses.color_pair(1))
                        stdscr.addstr(h-2, 2, "[P] Player   [X] Stop", curses.color_pair(2))
                except: pass
                stdscr.refresh()
                k = stdscr.getch()
                if k == curses.KEY_UP and sel_idx > 0: sel_idx -= 1
                elif k == curses.KEY_DOWN and sel_idx < len(opts)-1: sel_idx += 1
                elif k == ord('\n'): return opts[sel_idx]['id']
                elif k == ord('q'): return 'quit'
                elif k == ord('p') and player_obj.is_running(): return 'player'
                elif k == ord('x') and player_obj.is_running(): return 'stop'
        return curses.wrapper(_draw)

    # ---------------------------------------------------------
    # PLAYER SCREEN (With Instant Stop Animation)
    # ---------------------------------------------------------
    def player_screen(self, player_obj):
        def _control(stdscr):
            self._init_colors()
            curses.curs_set(0)
            stdscr.timeout(50)

            stars = [[random.uniform(-1, 1), random.uniform(-0.5, 0.5), random.uniform(0.2, 2.0)] for _ in range(50)]
            frame, vis_state = 0, [0] * 250
            spinner_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
            
            show_recs, recommendations, rec_sel_idx = False, [], 0

            def fetch_recs():
                nonlocal recommendations
                from .search import Searcher
                s = Searcher()
                cur_title = player_obj.queue[player_obj.current_index].get('title') if player_obj.queue else None
                r = s.get_recommendations(current_track_title=cur_title)
                recommendations = r[:4] if r else []

            # --- MAIN LOOP ---
            try:
                while True:
                    frame += 1
                    if not player_obj.is_running() and not player_obj.queue: break
                    stdscr.erase(); h, w = stdscr.getmaxyx()
                    
                    status = player_obj.get_status()
                    pos, dur = float(status.get('position') or 0), float(status.get('duration') or 1)
                    is_paused, is_buf = status.get('paused'), status.get('buffering')

                    # 1. STARS
                    spd = 0.002 if is_paused else 0.04
                    for s in stars:
                        s[2] -= spd
                        if s[2] <= 0.1: s[0], s[1], s[2] = random.uniform(-1, 1), random.uniform(-0.5, 0.5), 2.0
                        sx, sy = int(w//2 + (s[0]/s[2])*80), int(h//2 + (s[1]/s[2])*40)
                        if 0 <= sx < w-1 and 0 <= sy < h-8:
                            try:
                                if s[2] < 0.6: char, col = "O", curses.color_pair(1) | curses.A_BOLD
                                elif s[2] < 1.2: char, col = "*", curses.color_pair(1)
                                else: char, col = ".", curses.color_pair(2)
                                stdscr.addstr(sy, sx, char, col)
                            except: pass

                    # 2. HUD RECS
                    if show_recs:
                        if not recommendations:
                            try: stdscr.addstr(h//2, max(0, (w-20)//2), "SCANNING AI...", curses.color_pair(4)|curses.A_BOLD)
                            except: pass
                        else:
                            hh, card_w = h//2, min(35, w//2 - 4)
                            pos_map = [(2, hh-4), (2, hh+1), (w-card_w-2, hh-4), (w-card_w-2, hh+1)]
                            for i, r in enumerate(recommendations):
                                if i >= 4: break
                                rx, ry = pos_map[i]
                                sel = (i == rec_sel_idx)
                                col = curses.color_pair(6)|curses.A_BOLD if sel else curses.color_pair(2)
                                brd = "█" if sel else "│"
                                try:
                                    stdscr.addstr(ry, rx, f"{brd} {r['title'][:card_w-3]}", col)
                                    stdscr.addstr(ry+1, rx, f"{brd} ────────", col)
                                except: pass

                    try:
                        # 3. TITLE & VISUALIZER
                        if not show_recs:
                            t = player_obj.queue[player_obj.current_index].get('title', '?')
                            stdscr.addstr(1, 0, t[:w-2].center(w-1), curses.color_pair(4)|curses.A_BOLD)
                            
                            bw = max(5, w-10); sx = (w-bw)//2; yv = h-6
                            chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
                            for i in range(bw):
                                if sx+i >= w-1: break
                                if not is_paused: vis_state[i] = max(0, min(7, vis_state[i] + random.randint(-1, 1)))
                                else: vis_state[i] = 0
                                
                                wv = math.sin((frame*0.3) + (i*0.3))
                                ci = max(10, min(35, 10 + int(((wv+1)/2)*25)))
                                stdscr.addstr(yv, sx+i, chars[vis_state[i]], curses.color_pair(ci))

                        # 4. PROGRESS
                        yb = h-5; bw = max(5, w-10); sx = (w-bw)//2
                        fill = int((pos/dur)*bw) if dur>0 else 0
                        stdscr.addstr(yb, sx, "─"*bw, curses.color_pair(2))
                        stdscr.addstr(yb, sx, "━"*min(fill, bw), curses.color_pair(4)|curses.A_BOLD)
                        
                        # Status
                        cs, ts = f"{int(pos//60):02}:{int(pos%60):02}", f"{int(dur//60):02}:{int(dur%60):02}"
                        stdscr.addstr(yb+1, sx, cs, curses.color_pair(1))
                        if sx+bw-5 < w: stdscr.addstr(yb+1, sx+bw-5, ts, curses.color_pair(1))

                        spin = spinner_frames[frame % len(spinner_frames)]
                        msg = "⏸" if is_paused else (spin if is_buf else "▶")
                        stdscr.addstr(h-3, max(0, (w-len(msg))//2), msg, curses.color_pair(6 if (is_paused or is_buf) else 4))

                        if show_recs: hlp = "[ARROWS] Nav  [ENTER] Play Next  [A] Queue  [S] Close"
                        else: hlp = "[SPACE] Pause  [S] Recs  [←/→] Seek  [N/P] Skip  [V] Queue  [B] Back"
                        if h>2: stdscr.addstr(h-2, max(0, (w-len(hlp))//2), hlp[:w-1], curses.color_pair(2))

                    except: pass
                    stdscr.refresh()

                    # INPUT
                    key = stdscr.getch()
                    if show_recs:
                        if key in [ord('s'), ord('S'), 27]: show_recs = False
                        elif key == curses.KEY_UP: rec_sel_idx = 0 if rec_sel_idx==1 else (2 if rec_sel_idx==3 else rec_sel_idx)
                        elif key == curses.KEY_DOWN: rec_sel_idx = 1 if rec_sel_idx==0 else (3 if rec_sel_idx==2 else rec_sel_idx)
                        elif key == curses.KEY_LEFT and rec_sel_idx >= 2: rec_sel_idx -= 2
                        elif key == curses.KEY_RIGHT and rec_sel_idx < 2: rec_sel_idx += 2
                        elif key in [ord('\n'), ord('a'), ord('A')]:
                            if 0 <= rec_sel_idx < len(recommendations):
                                if key == ord('\n'):
                                    player_obj.queue.insert(player_obj.current_index+1, recommendations[rec_sel_idx])
                                    show_recs = False
                                else:
                                    player_obj.add_to_queue(recommendations[rec_sel_idx])
                    else:
                        if key in [ord('s'), ord('S')]:
                            show_recs = True
                            if not recommendations: threading.Thread(target=fetch_recs, daemon=True).start()
                        elif key == ord(' '): player_obj.toggle_pause()
                        elif key == curses.KEY_RIGHT: player_obj.seek(10)
                        elif key == curses.KEY_LEFT: player_obj.seek(-10)
                        elif key in [ord('n'), ord('N')]: player_obj.play_next()
                        elif key in [ord('p'), ord('P')]: player_obj.play_prev()
                        elif key in [ord('r'), ord('R')]: player_obj.toggle_repeat()
                        elif key in [ord('v'), ord('V')]:
                            new = self.queue_screen(player_obj)
                            if new is not None: player_obj.current_index = new; player_obj.play_current()
                        elif key in [ord('b'), ord('B')]: break
                        elif key in [ord('q'), ord('Q')]: 
                            # Manually trigger the exit sequence logic to show animation
                            raise KeyboardInterrupt 
            
            except KeyboardInterrupt:
                # 1. SHOW ANIMATION FIRST
                self._draw_stop_anim(stdscr)
                # 2. THEN STOP PLAYER
                player_obj.stop()
                player_obj.queue = []
                return

        return curses.wrapper(_control)

    # ---------------------------------------------------------
    # OTHER SCREENS
    # ---------------------------------------------------------
    def live_search(self, searcher):
        def _draw(stdscr):
            self._init_colors(); curses.curs_set(1); stdscr.timeout(100)
            from .database import db
            recent = db.get_recent_searches(limit=8)
            q, suggs, sel = "", recent.copy(), -1
            def fetch(txt): 
                nonlocal suggs, sel
                if txt.strip(): suggs = searcher.get_suggestions(txt)
                else: suggs = recent.copy()
                sel = -1
            while True:
                stdscr.erase(); h, w = stdscr.getmaxyx()
                try:
                    stdscr.addstr(0, 0, " GANA :: LIVE SEARCH ".ljust(w-1), curses.color_pair(4)|curses.A_BOLD)
                    stdscr.addstr(1, 0, "─"*max(0, w-1), curses.color_pair(2))
                    disp = (suggs[sel] if 0 <= sel < len(suggs) else q)[:max(0, w-15)]
                    stdscr.addstr(3, 2, "QUERY >> ", curses.color_pair(6)|curses.A_BOLD)
                    stdscr.addstr(3, 11, disp, curses.color_pair(1)|curses.A_BOLD)
                    sub = "Live Suggestions:" if q.strip() else "Recent Searches:"
                    stdscr.addstr(5, 4, sub, curses.color_pair(2))
                    for i, s in enumerate(suggs):
                        if 7+i >= h-3: break
                        is_sel = (i == sel)
                        pre = ">> " if is_sel else "   "
                        att = curses.color_pair(3) if is_sel else curses.color_pair(1)
                        stdscr.addstr(7+i, 2, f"{pre}{s}".ljust(max(0, w-5))[:max(0, w-5)], att)
                    hlp = "[↑/↓] Browse   [ENTER] Search   [ESC] Cancel"
                    stdscr.addstr(h-2, 0, "─"*max(0, w-1), curses.color_pair(2))
                    stdscr.addstr(h-1, max(0, (w-len(hlp))//2), hlp[:w-1], curses.color_pair(2))
                except: pass
                stdscr.refresh(); k = stdscr.getch()
                if k == -1: continue
                if k in [10, 13]: 
                    try: curses.curs_set(0)
                    except: pass
                    return (suggs[sel] if 0<=sel<len(suggs) else q)
                elif k == 27: 
                    try: curses.curs_set(0)
                    except: pass
                    return None
                elif k in [curses.KEY_BACKSPACE, 127, 8]:
                    q = q[:-1]; threading.Thread(target=fetch, args=(q,), daemon=True).start()
                elif k == curses.KEY_UP: sel = max(-1, sel-1)
                elif k == curses.KEY_DOWN: sel = min(len(suggs)-1, sel+1)
                else:
                    try: 
                        if chr(k).isprintable(): q+=chr(k); threading.Thread(target=fetch, args=(q,), daemon=True).start()
                    except: pass
        return curses.wrapper(_draw)

    def menu_selector(self, items, is_history=False):
        def _draw(stdscr):
            self._init_colors(); curses.curs_set(0)
            row, sel, local = 0, set(), items
            while True:
                stdscr.erase(); h, w = stdscr.getmaxyx(); tot = len(local)
                try:
                    stdscr.addstr(0, 0, f" FOUND [{tot}] ".ljust(w-1), curses.color_pair(4)|curses.A_BOLD)
                    sub = (" [SPC] Sel  [ENT] Play  [Q] Back" + ("  [D] Del" if is_history else "  [A] All"))[:w-1]
                    stdscr.addstr(1, 0, sub, curses.color_pair(2))
                    if tot == 0: stdscr.addstr(3, 2, "Empty."); stdscr.refresh(); time.sleep(0.5); return None, None
                    disp = h-4; start = max(0, row-disp+1)
                    for i in range(disp):
                        idx = start+i
                        if idx >= tot: break
                        cur, chk = (idx==row), (idx in sel)
                        ln = f"{'>>' if cur else '  '} {'[+]' if chk else '[ ]'} {local[idx]['title']}"[:max(0, w-2)]
                        att = curses.color_pair(3) if cur else (curses.color_pair(5) if chk else curses.color_pair(1))
                        stdscr.addstr(i+3, 0, ln.ljust(w-1), att)
                except: pass
                stdscr.refresh(); k = stdscr.getch()
                if k == curses.KEY_UP and row > 0: row -= 1
                elif k == curses.KEY_DOWN and row < tot-1: row += 1
                elif k == ord(' '): 
                    if row in sel: sel.remove(row)
                    else: sel.add(row)
                    row = min(tot-1, row+1)
                elif k == ord('a') and not is_history: sel = set(range(tot)) if len(sel) != tot else set()
                elif k == ord('d') and is_history:
                    from .database import db; db.delete_history(local[row]['id']); del local[row]; sel.clear()
                    if row >= len(local) and row > 0: row -= 1
                elif k == ord('\n'):
                    if sel: return [local[i] for i in sorted(list(sel))], 0
                    return local, row
                elif k == ord('q'): return None, None
        return curses.wrapper(_draw)

    def queue_screen(self, player_obj):
        def _q(stdscr):
            self._init_colors(); curses.curs_set(0); sel = player_obj.current_index
            while True:
                stdscr.erase(); h, w = stdscr.getmaxyx()
                ico = ["➡ SEQ", "🔂 ONE", "🔁 ALL"][player_obj.repeat_mode]
                try:
                    stdscr.addstr(0, 0, f" QUEUE [{len(player_obj.queue)}] ".ljust(w-1), curses.color_pair(4)|curses.A_BOLD)
                    stdscr.addstr(0, max(0, w-len(ico)-2), ico, curses.color_pair(6)|curses.A_BOLD)
                    stdscr.addstr(1, 0, " [ENT] Jump  [D] Del  [R] Loop  [Q] Back", curses.color_pair(2))
                    disp = h-4; start = max(0, sel-disp+1)
                    for i in range(disp):
                        idx = start+i
                        if idx >= len(player_obj.queue): break
                        t = player_obj.queue[idx]['title'][:max(0, w-6)]
                        cur, play = (idx==sel), (idx==player_obj.current_index)
                        pre = " ▶ " if play else (" > " if cur else "   ")
                        att = curses.color_pair(5)|curses.A_BOLD if play else (curses.color_pair(20) if cur else curses.color_pair(1))
                        stdscr.addstr(i+3, 0, f"{pre}{idx+1}. {t}".ljust(max(0, w-1)), att)
                except: pass
                stdscr.refresh(); k = stdscr.getch()
                if k == curses.KEY_UP and sel > 0: sel -= 1
                elif k == curses.KEY_DOWN and sel < len(player_obj.queue)-1: sel += 1
                elif k in [ord('d'), ord('D')]: 
                    if len(player_obj.queue) > 0: player_obj.remove_from_queue(sel); sel = max(0, sel-1)
                elif k in [ord('r'), ord('R')]: player_obj.toggle_repeat()
                elif k == ord('\n'): return sel
                elif k == ord('q'): return None
        return curses.wrapper(_q)

ui = UI()
