import sys
import logging
import colorlog
import os
import io
import json
import re
import argparse
import subprocess
from pathlib import Path

from PIL import Image
import requests
from yt_dlp import YoutubeDL
import musicbrainzngs

# Initialize the client with a descriptive user-agent string
musicbrainzngs.set_useragent("SongDownloader", "2.0", "contact@example.com")

# Configure logging
if not Path("assets/song_downloader.log").exists():
    Path("assets").mkdir(exist_ok=True)
    Path("assets/song_downloader.log").write_text("", "UTF-8")
    
logger = logging.getLogger()
logging.basicConfig(
    filename="assets/song_downloader.log",     # log file name
    filemode="a",
    encoding="utf-8",
    level=logging.INFO,                 # log level: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# beautiful horses color to logging
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',  # Red text on a white background
    },
    secondary_log_colors={},
    style='%'
)
handler = colorlog.StreamHandler() # Output to Terminal too
handler.setFormatter(formatter)
logger.addHandler(handler) # add handler for color format


logging.getLogger("musicbrainzngs").setLevel(logging.WARNING)
def get_metadata_musicbrainz(title: str, artist: str):
    # Search for the recording
    result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=1) # artistname
    
    if not result['recording-list']:
        return None
        
    track = result['recording-list'][0]
    
    # Process systematic variables
    GENRES = [
        g["name"]
        for g in track.get("genre-list", [])
        if "name" in g
    ]
    if not GENRES:
        GENRES = [
            t["name"]
            for t in track.get("tag-list", [])
            if "name" in t
        ]
    metadata = {
        "title": track.get("title"),
        "artist": track.get("artist-credit", [{}])[0].get("artist", {}).get("name"),
        "duration_ms": int(track.get("length", 0)),  # Duration in milliseconds
        "release_id": track.get("release-list", [{}])[0].get("id"),
        "album": track.get("release-list", [{}])[0].get("title"),
        "date": track.get("release-list", [{}])[0].get("date"),
        "genres": GENRES
    }
    # Fetch cover art URL if a release ID exists
    if metadata["release_id"]:
        metadata["cover_url"] = f"https://coverartarchive.org/release/{metadata['release_id']}/front" # TODO: Natively download Image
    else:
        metadata["cover_url"] = 'https://None'
        logging.critical(
            "No Song Cover found using '%s' return: '%s'",
            metadata['release_id'],
            metadata["cover_url"]
        )
        
    return metadata

def sanitize_filename(song_artists: str):
    # Split song and artist
    if ' - ' in song_artists:
        song_name, artists = song_artists.rsplit(' - ', 1)
    else:
        # If no ' - ', treat the whole string as song name
        song_name = song_artists
        artists = "Unknown Artist"
    # Remove invalid characters
    song_name = re.sub(r'[<>:"/\\|?*]', '', song_name)
    artists = re.sub(r'[<>:"/\\|?*]', '', artists)
    # trim to a maximum length
    max_length_artists = 100
    max_length_song = 50
    if len(song_name) > max_length_song:
        song_name = song_name[:max_length_song].rstrip()
    if len(artists) > max_length_artists:
        artists = artists[:max_length_artists].rstrip()
    logging.debug("%s - %s", song_name, song_artists)
    #return f'{song_name} - {artists}'
    song_title_artists = {
        "title": song_name,
        "artist": artists
    }
    return song_title_artists

def download_audio(file, url):
    """Download audio from YouTube video URL."""
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': file,
        'noplaylist': True,
        'quiet': False,  # Show progress during download
    }   
    # download
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        logging.debug("Downloaded '%s'", url)

def analyze_audio(file):
    cmd = [
        "ffmpeg", "-i", file,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=14:print_format=json",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, check=False, text=True)
    output = result.stderr
    json_start = output.find("{")
    json_end = output.rfind("}") + 1
    logging.debug("Analysed audio and return loudnorm input values")
    return json.loads(output[json_start:json_end])

def normalize_audio(file, decoy_file, measure_value):
    filter_settings = (
        f"loudnorm=I=-14:TP=-1.5:LRA=14:"
        f"measured_I={measure_value['input_i']}:"
        f"measured_TP={measure_value['input_tp']}:"
        f"measured_LRA={measure_value['input_lra']}:"
        f"measured_thresh={measure_value['input_thresh']}:"
        f"offset={measure_value['target_offset']}:"
        f"linear=true:print_format=summary"
    )
    cmd = ["ffmpeg", "-i", file, "-af", filter_settings, decoy_file]
    subprocess.run(cmd, check=False)
    logging.debug("Applying Norm")

def get_metadata_ytdlp(url: str):
    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
    data = {
        "video_url": info_dict.get("url", None),
        "video_id": info_dict.get("id", None),
        "video_title": info_dict.get('title', None)
    }
    return data

def get_youtube_link(search: str, tolerance_sec: int, max_results: int, metadata: dict): # TODO: Cache Youtube_Search Query
    # Variables
    length_ms = metadata["duration_ms"]
    target_seconds = length_ms // 1000

    def do_search(query_type, search_for):
        ydl_opts = {
            # "match_filter": lambda info_dict: (
            #     None
            #     if (
            #         # only accept Topic uploads
            #         "Topic" in info_dict.get("uploader", "")
            #         # duration between 3:30 and 4:10
            #         and 210 <= info_dict.get("duration", 0) <= 250
            #     )
            #     else "Skipped: not Topic or wrong duration"
            # ),
            # 'cookies': cookies,
            'quiet': True,
            'skip_download': True,
            'noplaylist': True,
            'default_search': query_type
        }
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"{query_type}{max_results}:{search_for}", download=False)
                return info.get("entries", []) if info else []
            except Exception as e:
                logging.error("Error in %s: %s", query_type, str(e))
                return []
            
    # TODO: Youtube Music Search
    # # --- 1. Try YouTube Music ---
    # for entry in do_search("https://music.youtube.com/search?q=", search):
    #     if entry.get("duration") is None:
    #         continue
    #     yt_duration = entry["duration"]
    #     if abs(yt_duration - target_seconds) <= tolerance_sec:
    #         return entry["webpage_url"]  # good match
    # logging.warning(
    #     "YouTube Music failed, falling back to Youtube Search results for '%s'",
    #     search
    # )
    
    #  --- 2. Fallback to YouTube Search---
    for entry in do_search("ytsearch", search):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance_sec:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.warning(
        "Youtube Search failed, falling back to YouTube Topic Search for '%s'",
        search
    )
    
    #  --- 3. Fallback to YouTube Topic Video---
    for entry in do_search("ytsearch", f"{search} topic"):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance_sec:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.warning(
        "Youtube Topic Search failed, falling back to Youtube Lyrics Video for '%s'",
        search
    )
    
    #  --- 4. Fallback to Youtube Lyrics Video---
    for entry in do_search("ytsearch", f"{search} AND lyrics"):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance_sec:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.critical(
        "Youtube Lyrics Video not found, falling back to first best result for '%s'",
        search
    )
    
    # --- 5. As a last resort, return the first YouTube result ---
    youtube_entries = do_search("ytsearch", search)
    if youtube_entries:
        return youtube_entries[0]["webpage_url"]
    
    # --- Error ---
    logging.warning("No youtube_url found for: (%s)", search)
    return None

def get_metadata_spotify(track_url):
    track = sp.track(track_url)
    
    # Get artist details
    artist_id = track["artists"][0]["id"]
    artist_data = sp.artist(artist_id)
    
    json_metadata = {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "date": track["album"]["release_date"][:4],
        "cover_url": track["album"]["images"][0]["url"],
        "genres": artist_data.get("genres", [])
    }
    logging.debug("return metadata")
    return json_metadata

def embed_metadata(wav_file, output_file, cover_path, data):
    if data["cover_url"] == "https://None":
        cover_data = ""
        img = Image.new("RGB", (1, 1), (255, 255, 255))
        img.save(cover_path, "JPEG")
        logging.critical("No Real Cover, using decoy jpg")
    else:
        cover_data = requests.get(data["cover_url"]).content
        try:
            img = Image.open(io.BytesIO(cover_data)).convert("RGB")
            with open(cover_path, "wb") as f:
                f.write(cover_data)
            # TODO: Make JPG lighter than native
            # img.save(cover_path, format="JPEG", quality=70)
            logging.debug("wrote cover.jpg natively")
        except Exception as e:
            logging.critical("Invalid Cover Data: %s", str(e))
            img = Image.new("RGB", (1, 1), (255, 255, 255))
            img.save(cover_path, "JPEG")
            logging.critical("Created decoy JPG just to download and go on")
        
        
    genre_str = ", ".join(data["genres"])
    
    CODEC: str = output_file.rsplit(".", 1)[-1]
    if CODEC == "opus":
        cmd = [ # TODO: Natively support libopus
            "ffmpeg",
            "-i", wav_file,
            "-map", "0:a", 
            "-metadata", f"title={data['title']}",
            "-metadata", f"artist={data['artist']}",
            "-metadata", f"album={data['album']}",
            "-metadata", f"date={data['date']}",
            "-metadata", f"genre={genre_str}",
            "-metadata", cover_path,
            "-c:a", "libopus", "-b:a", "128k",
            output_file
        ]
    else:
        cmd = [
            "ffmpeg", 
            "-i", wav_file, # input file
            "-i", cover_path, #cover
            "-map", "0", "-map", "1",
            #"-acodec", "flac",
            #"-compression_level", "8",
            "-metadata", f"title={data['title']}",
            "-metadata", f"artist={data['artist']}",
            "-metadata", f"album={data['album']}",
            "-metadata", f"date={data['date']}",
            "-metadata", f"genre={genre_str}",
            "-disposition:v", "attached_pic",
            output_file
        ]
    logging.debug("embedding metadata")
    subprocess.run(cmd, check=False)
    logging.debug("embedding metadata done")

def compress_audio(file: dict, output_path: str):
    if os.path.exists(file["path"]):
        if os.path.exists(output_path):
            logging.info("Overwriting: '%s'", output_path)
            os.remove(output_path)
    else:
        logging.error("'%s' doesn't exist: skipping compression", file["path"])
        return 1
    cmd = [
        "ffmpeg",
        "-i", file["path"],
        "-c:a", file["codec"], "-b:a", file["bitrate"],
        output_path
    ]
    subprocess.run(cmd, check=False)
    return 0

def check_filepaths(file_path: str, compression_arg: bool):
    if os.path.exists(file_path):
        if compression_arg is True:
            logging.info("File '%s' already exists & compression activated: skipping to compression", file_path)
            return 2
        logging.info("File '%s' already exists & compression deactivated: closing\n", file_path)
        return 1
    else:
        return 0

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Spotify ↔ YouTube helper")
    parser.add_argument("--song", default="", help="Search for ...")
    parser.add_argument("--youtube", default="", help="YouTube video URL")
    # TODO: Custom cover
    # TODO: Explicit Mode / Custom Filename
    args = parser.parse_args()

    # Main Variables
    logging.info("Starting to download a new Track with given data")
    if not args.song and not args.youtube:
        logging.debug('Using in-script values')
        song = ""
        youtube = ""
    else:
        logging.debug('Using given Arguments')
        song = args.song
        youtube = args.youtube

    # Secondary Variables
    tolerance_sec = 2
    max_results_ytsearch = 10
    input_file = "output/tmp_downloaded.wav"
    tmp_file = "output/tmp_normalized.wav"
    tmp_cover = "output/tmp_cover_data.jpg"
    COMPRESSION_OPT_PATH = "output/compressed (ohio-impressed)"

    if os.path.exists(input_file):
        os.remove(input_file)
        logging.warning("Overwriting tmp_downloaded file")
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
        logging.warning("Overwriting tmp_normalized file")
    if os.path.exists(tmp_cover):
        os.remove(tmp_cover)
        logging.warning("Overwriting tmp_cover_data file")

    # Look if something is missing
    if not song and not youtube :
        logging.error("No Song name or Youtube URL\n")
        sys.exit(1)
    else:
        if song and youtube:
            logging.info(
                "... Processing: '%s' (%s) ---",
                song,
                youtube
            )
            song_data = sanitize_filename(song)
            METADATA = get_metadata_musicbrainz(song_data['title'], song_data['artist'])
            filename_data = sanitize_filename(f"{METADATA['title']} - {METADATA['artist']}")
            opt_filename: str = f"{filename_data['title']} - {filename_data['artist']}"
            logging.info("Song name is: (%s)", song)
            logging.info("Youtube_URL is: (%s)", youtube)
        if not song:
            logging.info("... Processing: (%s)", youtube)
            # TODO: Derive song from youtube url
            logging.info("No Song name given, generated one is: (%s)", song)
        if not youtube:
            logging.info("... Processing: '%s'", song)
            song_data = sanitize_filename(song)
            METADATA = get_metadata_musicbrainz(song_data['title'], song_data['artist'])
            filename_data = sanitize_filename(f"{METADATA['title']} - {METADATA['artist']}")
            opt_filename: str = f"{filename_data['title']} - {filename_data['artist']}"

    # Correct File Name
    Path("output").mkdir(exist_ok=True)
    final_file = {
        "path": f"output/{opt_filename}.flac",
        "compress": True,
        "codec": "libopus",
        "container": "opus",
        "bitrate": "128k"
    }
    FILE_COMPRESSED = f"{COMPRESSION_OPT_PATH}/{opt_filename}.{final_file["container"]}"

    match check_filepaths(final_file["path"], final_file["compress"]):
        case 1: # All files already there
            sys.exit(0)
        case 2: # Skipping to compression
            pass
        case 0: # No initial file there, downloading audio
            if not youtube: # Fetch Youtube URL
                # QUERY = f"{METADATA['title']} - {METADATA['artist']}"
                QUERY = opt_filename
                youtube = get_youtube_link(QUERY, tolerance_sec, max_results_ytsearch, METADATA)
                if youtube is None:
                    # Fallback to user Input
                    USER_INPUT = f"{song_data['title']} - {song_data['artist']}"

                    # Redefining/Revalidating Things
                    QUERY = USER_INPUT
                    final_file["path"] = f"output/{USER_INPUT}.flac"
                    FILE_COMPRESSED = f"{COMPRESSION_OPT_PATH}/{USER_INPUT}.{final_file["container"]}"

                    # Running loop again
                    match check_filepaths(final_file["path"], final_file["compress"]):
                        case 1: # All files already there
                            sys.exit(0)
                        case 2: # Skipping to compression
                            pass
                        case 0: # No initial file there, downloading audio
                            logging.critical("Fetching Youtube_URL failed, falling back to user input query: '%s'", QUERY)
                            youtube = get_youtube_link(QUERY, tolerance_sec, max_results_ytsearch, METADATA)
                            if youtube is None:
                                logging.error("Fetching Youtube_URL failed for all Queries\n")
                                sys.exit(1)
                logging.info("No Youtube_URL given, generated one is: (%s)", youtube)

            download_audio(input_file, youtube)

            measured = analyze_audio(input_file)
            normalize_audio(input_file, tmp_file, measured)

            embed_metadata(tmp_file, final_file["path"], tmp_cover, METADATA)

            # Delete Temp Files
            logging.debug("removing temp files")
            os.remove(tmp_file)
            os.remove(input_file)
            os.remove(tmp_cover)

    # Compress Audio
    if check_filepaths(final_file["path"], final_file["compress"]) == 0:
        logging.error("`%s` was never written\n", final_file["path"])
        sys.exit(1)
    else:
        Path(COMPRESSION_OPT_PATH).mkdir(exist_ok=True)
        compress_audio(final_file, FILE_COMPRESSED)
        # os.remove(final_file["path"]) # Delete large file
        logging.info("✅ Compressed: '%s'", FILE_COMPRESSED)

    logging.info("✅ Downloaded: '%s'\n", final_file["path"])
    sys.exit(0)
