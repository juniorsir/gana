import time
import requests
import urllib.request

def is_online():
    """Ultra-fast check to see if we have internet."""
    try:
        # Use a reliable Google endpoint with a 1.5s timeout
        urllib.request.urlopen('https://www.google.com/generate_204', timeout=1.5)
        return True
    except:
        return False

def is_unwanted_media(title):
    """
    Smart Heuristic Filter:
    Analyzes a YouTube video title to determine if it's a movie/trailer/gameplay
    instead of a song.
    
    Returns:
        True if the media is UNWANTED (e.g., a movie trailer).
        False if the media is SAFE (e.g., a phonk track, song, or lofi mix).
    """
    if not title:
        return False

    title_lower = title.lower()
    
    # 1. WHITELIST (Overrides everything else)
    # If the title explicitly contains music-related terms, it's safe.
    safe_words = [
        'phonk', 'music', 'ost', 'soundtrack', 'mix', 'remix', 
        'song', 'audio', 'beat', 'lofi', 'instrumental', 'bass boosted',
        'lyric video', 'official video', 'album', 'ep', 'chill'
    ]
    for word in safe_words:
        if word in title_lower:
            return False

    # 2. BLACKLIST
    # Words commonly associated with non-music entertainment.
    unwanted_words = [
        'trailer', 'teaser', 'movie', 'full film', 'gameplay', 
        'walkthrough', 'cutscene', 'review', 'reaction', 'scene',
        'episode', 'season', 'hd cam', 'box office', 'ending explained',
        'let\'s play', 'playthrough', 'podcast', 'vlog'
    ]
    
    for word in unwanted_words:
        # We check for the word bounded by spaces or punctuation to avoid 
        # false positives (e.g., "scene" inside "obscene").
        # A simple `in` check is usually enough for these specific words.
        if word in title_lower:
            return True
            
    # Default to False (assume it's safe if we aren't sure)
    return False


def get_lyrics(artist, title):
    """
    Fetches lyrics from a public open API (lyrics.ovh).
    Useful for the Advanced Lyrics Mode.
    """
    try:
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get('lyrics', "Lyrics not found.")
    except requests.RequestException:
        return "Could not connect to lyrics service."
    
    return "Lyrics unavailable."


def check_internet_speed():
    """
    Simple network check using ping latency as a proxy for 'low-end' detection.
    Automatically triggers low-data mode if latency is very high.
    
    Returns: "fast", "slow", or "offline"
    """
    try:
        start = time.time()
        # Ping a highly available server with a strict timeout
        requests.get("https://www.google.com/generate_204", timeout=2)
        latency = time.time() - start
        
        # If latency is greater than 500ms, assume 3G/Edge/Slow connection
        if latency > 0.5:
            return "slow"
        return "fast"
    except requests.RequestException:
        return "offline"
