import yt_dlp
import requests
import random
from collections import Counter
from .config import config
from .utils import is_unwanted_media
from .database import db
from .utils import is_unwanted_media, is_online
from .logger import log_error

class Searcher:
    def get_suggestions(self, query):
        if not query.strip(): return []
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
            return requests.get(url, timeout=2).json()[1][:10]
        except: return []

    def _clean_title(self, title):
        """Extracts core keywords from a song title"""
        bad_words = ['official', 'video', 'audio', 'lyrics', 'prod', 'feat', 'ft.', 'music', 'hd', 'hq', '4k']
        words = title.lower().replace('-', ' ').replace('|', ' ').replace('(', '').replace(')', '').split()
        return " ".join([w for w in words if w not in bad_words])

    def get_recommendations(self, current_track_title=None):
        """
        Generates recommendations based on:
        1. Current Playing Song (Context)
        2. Recent Search Queries (Intent)
        """
        # 1. Get Context
        recent_searches = db.get_recent_searches(limit=1)
        last_search = recent_searches[0] if recent_searches else ""
        
        query = ""
        
        # 2. Formulate Strategy
        if current_track_title:
            # STRATEGY A: "Contextual Mix"
            # Combine current song artist/vibe with what the user recently typed.
            # Ex: Playing "After Hours" + Search "Synthwave" -> "After Hours Synthwave Mix"
            cleaned_title = self._clean_title(current_track_title)
            
            if last_search and last_search not in cleaned_title:
                query = f"{cleaned_title} {last_search} mix"
            else:
                query = f"{cleaned_title} similar songs mix"
        
        elif last_search:
            # STRATEGY B: "Search Continuity"
            query = f"{last_search} recommended mix"
            
        else:
            # STRATEGY C: "History Aggregate" (Fallback)
            history = db.get_history()
            if not history: return []
            all_words = []
            for h in history:
                all_words.extend(self._clean_title(h[1]).split())
            if not all_words: return []
            most_common = Counter(all_words).most_common(1)[0][0]
            query = f"{most_common} mix"

        # 3. Fetch Results
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                raw_results = info.get('entries', [])
                
                # Filter & Shuffle
                valid = [r for r in raw_results if not is_unwanted_media(r.get('title', ''))]
                # Remove duplicates of current song
                if current_track_title:
                    valid = [r for r in valid if r.get('title') != current_track_title]
                
                random.shuffle(valid)
                return valid[:8]
        except:
            return []

    def search(self, query):
        if not is_online():
            log_error("Search failed: No internet connection.")
            return []

        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if "http" in query:
                    search_str = query
                else:
                    search_str = f"ytsearch15:{query}"
                info = ydl.extract_info(search_str, download=False)
                if 'entries' in info:
                    results = info.get('entries', [])
                else:
                    # It was a single valid video URL
                    results = [info]

                # Filter out broken links (yt-dlp returns None for broken entries)
                valid_results = [r for r in results if r is not None and r.get('id')]
                if config.settings.get('music_mode'):
                    filtered = [r for r in valid_results if not is_unwanted_media(r.get('title', ''))]
                    return filtered if filtered else valid_results
                    
                return valid_results
            except Exception as e:
                log_error(f"yt-dlp search error on query '{query}': {e}")
                return []
