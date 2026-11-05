from yt_dlp import YoutubeDL
import time
import random
import sys
import math
from fuzzywuzzy import fuzz

class Youtube:
    """Gets Data from youtube i guess"""

    def __init__(self,
                 logger: object,
                 max_retries: int = 4,
                 retry_wait_seconds: list[float] = [0.54, 1.0, 3.0, 5.0, 10.0, 20.0, 30.0],
                 wait_error_seconds: float = 0.54
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

        wait_times: int = 0
        error = self.error
        retry_available = True
        downloaded = False
        while retry_available:
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    retry_available = False
                    downloaded = True
                except Exception as e:
                        # : Variables
                    retry_available = True
                    downloaded = False

                        # : Catch max tries
                    logging.debug("ERROR while downloading: %s", str(e))
                    if wait_times >= self.max_retries:
                        downloaded = False
                        retry_available = False
                    else:
                        wait = self.wait[wait_times]
                        logging.info("Couldn't download (%s), trying again / try(%s/%s) timeout(%ss -+%ss)...",
                                url, wait_times+1, self.max_retries, wait, self.error)
                        time.sleep(random.uniform(wait-error, wait+error))

                    wait_times += 1

        if downloaded:
            logging.debug("Downloaded '%s'", url)
        else:
            logging.critical("Couldn't download (%s)", url)
            sys.exit(1)

    def get_metadata_ytdlp(self, url: str) -> dict[str, str]:
        """Downloads Youtube Metadata"""
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
        data = {
            #"video_url": info_dict.get("url", None),
            #"video_id": info_dict.get("id", None),
            "video_title": info_dict.get('title', None),
            "thumbnail_url": info_dict.get("thumbnail"),
            "artist": info_dict.get("track_artist") or info_dict.get("uploader"),
            #"genre": info_dict.get("track_genre") or info_dict.get("genre") or "Unknown"
        }
        return data

    def get_youtube_link(self, search_query: str, metadata: dict[str, int], tolerance_sec: int = 2):
        """Gets Youtube URL by Query"""
        # Variables
        log = self.logging
        length_ms = metadata["duration_ms"]
        target_seconds = length_ms // 1000

        def soft_score(entry, trg_title:str, trg_artist: str = "", trg_duration_ms: int = 3000) -> float:
            """Scores softer, ensure good instead of perfect but rare results"""
            score: float = 0.0
            entry_tmp = {
                "title": f'{entry.get("title", "").lower()}',
                "duration_ms": int(entry.get("duration", 0) * 1000),
                "artist": f'{entry.get("uploader", "").lower()}',
                "views": int(entry.get("view_count", 0))
            }

            # Title & Artist Score
            score += fuzz.ratio(entry_tmp["title"], trg_title) *25 # : Title Matching
            score += fuzz.ratio(entry_tmp["artist"], trg_title) *20 # : Artist Matching 100%=16, 10%=1.6 points

            # View Score (logarithmic) (0.0 from 1 view to 10 points for 1 million views)
            score += math.log2(math.log10(entry_tmp["views"]) /1000 +1)

            # Duration Score
            if trg_duration_ms > 5*1000:
                score += -math.pow( abs(entry_tmp["duration_ms"]-trg_duration_ms) /1000, 2) +15 # Duration Matching

            return score


        def url_query(query):
            ydl_opts = {
                # 'cookies': cookies,
                'quiet': True,
                'skip_download': True,
                'noplaylist': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(f"{query}", download=False)
                    return info.get("entries", []) if info else []
                except Exception as e:
                    log.debug("Search failed for (%s): %s", query, str(e))
                    return []

        saved_songs: list = []
        highest_score: float = 0

        search_for: list[str] = [ 
                                 f"https://music.youtube.com/search?q=:{search_query}" # Youtube Music
                                 f"ytsearch:5:{search_query}", # YT Search
                                 f"ytsearch:5:{search_query} topic",
                                 f"ytsearch:10:{search_query} AND lyrics",
                                 f"ytsearch:1:{search_query}"
                                 ]

        for query in search_for:
            for entry in url_query(query):
                tmp_score = soft_score(entry=entry,
                                       trg_title=metadata["title"],
                                       trg_artist=metadata["artist"],
                                       trg_duration_ms=metadata["duration_ms"])
                song = {
                    "score": f"{tmp_score}",
                    "title": f"{entry.get("title", "")}",
                    "artist": f'{entry.get("uploader", "").lower()}',
                    "duration_ms": int( entry.get("duration", 0) * 1000 ),
                    "views": int( entry.get("view_count", 0) )
                }
                if tmp_score >= highest_score:
                    saved_songs.insert(0, song)
                else:
                    for x in saved_songs:
                        if tmp_score >= saved_songs[x]:
                            saved_songs.insert(0, song)
                            break;

        return saved_songs
