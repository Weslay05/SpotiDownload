from yt_dlp import YoutubeDL
import time
import random
import sys
import math
from fuzzywuzzy import fuzz
import re

def remove_words(input_string, word_blacklist) -> str:
    """
    Removes all words from input_string that are in word_blacklist (case-insensitive).
    
    Args:
        input_string (str): The original string
        word_blacklist (list): List of words to remove
        
    Returns:
        str: String with blacklist words removed
    """
    # Create a pattern that matches any of the blacklist words case-insensitively
    escaped_words = [re.escape(word) for word in word_blacklist]
    pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
    
    # Replace matches with empty string, case-insensitive
    result = re.sub(pattern, '', input_string, flags=re.IGNORECASE)
    
    # Clean up extra spaces left behind
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result

class Youtube:
    """Gets Data from youtube i guess"""

    def __init__(self,
                 logger: object,
                 max_retries: int = 5,
                 retry_wait_seconds: list[float] = [0.54, 1.0, 2.0, 3.0, 4.0],
                 wait_error_seconds: float = 0.6
                 ) -> None:
        """Handles Youtube requests"""
        self.logging: object = logger
        self.max_retries: int = max_retries
        self.wait: list[float] = retry_wait_seconds
        self.error: float = wait_error_seconds

    def download_audio(self, file_path: str, url: str):
        """Download audio from YouTube video URL."""
        logging = self.logging
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': file_path,
            'noplaylist': True,
            'quiet': False,  # Show progress during download
        }

        error = self.error
        with YoutubeDL(ydl_opts) as ydl:
            for x in range(self.max_retries):
                if x+1 >= self.max_retries:
                    logging.critical("Couldn't download (%s)", url)
                    sys.exit(1)
                try:
                    ydl.download([url])
                    break
                except Exception as e:
                        # : Catch max tries
                    logging.debug("ERROR while downloading: %s", str(e))
                    logging.info("Couldn't download (%s) / try(%s/%s): timeout(%ss to %ss)...",
                            url, x+1, self.max_retries, max(0, self.wait[x]-error), self.wait[x]+error)
                    time.sleep( random.uniform(max(0, self.wait[x]-error),self.wait[x]+error) ) # sleep for wait time with error
        logging.debug("Downloaded '%s'", url)

    def get_metadata_ytdlp(self, url: str) -> dict[str, int | None ]:
        """Downloads Youtube Metadata"""
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            blacklist: list[str] = [ " - topic", " lyrics", " topic" ]
            data = {
                "title": f"{remove_words(info_dict.get("title", ""), blacklist)}",
                "artist": f'{remove_words(info_dict.get("track_artist") or info_dict.get("uploader"), blacklist)}',
                "duration_sec": int( info_dict.get("duration", 0) ),
                "url": f"{info_dict.get("webpage_url", "")}",
                "thumbnail": f"{info_dict.get("thumbnail", "")}",
            }
        return data

    def youtube_search(self, song_title: str, song_artist: str = "", song_duration_ms: int = 3000, tolerance_sec: int = 2, does_case_matter: bool = False):
        """Gets Youtube URL Song title and artist"""
        #title = song_title.lstrip(" - ", 0)
        
        # Variables
        log = self.logging

        def soft_score(entry, trg_title:str, trg_artist: str = "", trg_duration_ms: int = 3000) -> float:
            """Scores softer, ensure good instead of perfect but rare results"""
            score: float = 0.0
            entry_tmp = {
                "title": f'{entry.get("title", "")}',
                "duration_ms": int(entry.get("duration", 0) * 1000),
                "artist": f'{entry.get("track_artist") or entry.get("uploader")}',
                "views": int(entry.get("view_count", 0))
            }

            # Title & Artist Score
            if does_case_matter:
                score += fuzz.ratio(entry_tmp["title"], trg_title)/100 *20 # : Title Matching
                score += fuzz.ratio(entry_tmp["artist"], trg_artist)/100 *28 # : Artist Matching
            else:
                score += fuzz.ratio(entry_tmp["title"].lower(), trg_title.lower())/100 *20 # : Title Matching
                score += fuzz.ratio(entry_tmp["artist"].lower(), trg_artist.lower())/100 *28 # : Artist Matching

            # View Score (logarithmic)
            score += max(0, 3*math.log2( math.log10(entry_tmp["views"]) /1000 +1 ) ) # : 1 for >200, 3 for 1K / 6 for 10k / 9 for 100K / 12 for 1 Million

            # Duration Score
            if trg_duration_ms > 5*1000:
                score += max(0, -math.pow( abs(entry_tmp["duration_ms"]-trg_duration_ms) /1000, 2) +15 ) # Duration Matching

            return score

        def url_query(query):
            ydl_opts = {
                # 'cookies': cookies,
                #'extractflat': True,
                'quiet': True,
                'skip_download': True,
                'noplaylist': True#,
                #'max-downloads': max_downloads
            }
            with YoutubeDL(ydl_opts) as ydl:
                tries: list[int] = [ 1, 2, 3 ] # TODO: Maybe another try version
                for x in range(len(tries)):
                    if x+1 >= len(tries):
                        log.warning("Search Failed fully for: (%s)", query)
                        return []
                    try:
                        info = ydl.extract_info(f"{query}", download=False)
                        return info.get("entries", []) if info else []
                    except Exception as e:
                        log.debug("Temp Search failed for (%s) : %s\n...retry(%s/%s)",
                                  query, str(e), x, len(tries))
                        time.sleep(tries[x])

        highest_matching: int = 5

        queries: list[str] = [
                                 #f"https://music.youtube.com/search?q=:{song_title} - {song_artist}" # Youtube Music
                                 f"ytsearch{highest_matching}:{song_title} - {song_artist}", # YT Search
                                 f"ytsearch{highest_matching}:{song_title} - {song_artist} topic",
                                 f"ytsearch{highest_matching}:{song_title} - {song_artist} AND lyrics"
                                 ]

        blacklist: list[str] = [ " - topic", " lyrics", " topic" ]

        # Save songs with scores
        saved_songs: list = []
        for query in queries:
            for entry in url_query(query):
                score = soft_score(entry=entry, trg_title=song_title, trg_artist=song_artist, trg_duration_ms=song_duration_ms)
                song = {
                    "score": score,
                    "title": f"{remove_words(entry.get("title", ""), blacklist)}",
                    "artist": f'{remove_words(entry.get("track_artist") or entry.get("uploader"), blacklist)}',
                    "album": entry.get("album"),
                    "duration_ms": int( entry.get("duration", 0) * 1000 ),
                    "url": f"{entry.get("webpage_url", "")}",
                    "thumbnail": f"{entry.get("thumbnail", "")}",
                    "views": int( entry.get("view_count", 0) )
                }
                if isinstance(song, list):
                    saved_songs.extend(song)
                elif isinstance(song, dict):
                    saved_songs.append(song)
                else:
                    log.warning("somethings missing out: %s", song)

        sorted_songs = sorted(saved_songs, key=lambda x: x["score"], reverse=True) # Sort Songs by score

        return sorted_songs
