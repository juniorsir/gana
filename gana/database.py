import sqlite3
import json
from .config import config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # History & Session
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history 
            (id TEXT PRIMARY KEY, title TEXT, url TEXT, pos INTEGER, ts DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS session 
            (key TEXT PRIMARY KEY, value TEXT)''')
            
        # --- NEW: SEARCH LOGS ---
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS searches 
            (query TEXT PRIMARY KEY, ts DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            
        self.conn.commit()

    def add_history(self, vid, title, url):
        self.cursor.execute("INSERT OR REPLACE INTO history (id, title, url, pos) VALUES (?, ?, ?, 0)", (vid, title, url))
        self.conn.commit()

    def delete_history(self, vid):
        self.cursor.execute("DELETE FROM history WHERE id = ?", (vid,))
        self.conn.commit()

    def get_history(self):
        return self.cursor.execute("SELECT id, title, url FROM history ORDER BY ts DESC LIMIT 50").fetchall()

    # --- NEW METHODS ---
    def add_search(self, query):
        """Log a search query to context memory"""
        self.cursor.execute("INSERT OR REPLACE INTO searches (query) VALUES (?)", (query.lower().strip(),))
        self.conn.commit()

    def get_recent_searches(self, limit=3):
        """Get last few things user looked for"""
        res = self.cursor.execute("SELECT query FROM searches ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        return [r[0] for r in res]

    # --- SESSION MANAGEMENT ---
    def save_session(self, queue, index, position=0, repeat_mode=0):
        try:
            q_data = json.dumps(queue)
            self.cursor.execute("INSERT OR REPLACE INTO session (key, value) VALUES (?, ?)", ("queue", q_data))
            self.cursor.execute("INSERT OR REPLACE INTO session (key, value) VALUES (?, ?)", ("index", str(index)))
            self.cursor.execute("INSERT OR REPLACE INTO session (key, value) VALUES (?, ?)", ("position", str(position)))
            self.cursor.execute("INSERT OR REPLACE INTO session (key, value) VALUES (?, ?)", ("repeat", str(repeat_mode)))
            self.conn.commit()
        except: pass

    def load_session(self):
        try:
            q = self.cursor.execute("SELECT value FROM session WHERE key='queue'").fetchone()
            i = self.cursor.execute("SELECT value FROM session WHERE key='index'").fetchone()
            p = self.cursor.execute("SELECT value FROM session WHERE key='position'").fetchone()
            r = self.cursor.execute("SELECT value FROM session WHERE key='repeat'").fetchone()
            if q and i:
                return json.loads(q[0]), int(i[0]), float(p[0] if p else 0), int(r[0] if r else 0)
        except: pass
        return [], -1, 0, 0

db = Database()
