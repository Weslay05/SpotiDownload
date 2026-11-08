import os
import random
import sys
import logging
import colorlog
import io
import json
import time
import re
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pathlib import Path
import string
import subprocess
import requests
from PIL import Image

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

load_dotenv()
# Initialize the client with a descriptive user-agent string
OUTPUT_DIR = os.getenv('OUTPUT_DIRECTORY')

BITRATE = os.getenv('OUTPUT_BITRATE') # kbp/s
MAX_DOWNLOAD_TRIES = os.getenv('MAX_DOWNLOAD_TRIES')
MAX_YOUTUBE_RESULTS = os.getenv('MAX_YOUTUBE_RESULTS')

METADATA_FROM = os.getenv('METADATA_FROM')
AUDIO_CONTAINER = os.getenv('AUDIO_CONTAINER')

LOUDNESS_LUFS = os.getenv('LOUDNESS_LUFS')
LOUDNESS_PEAK_DBFS = os.getenv('LOUDNESS_PEAK_DBFS')
LOUDNESS_RANGE_LRA = os.getenv('LOUDNESS_RANGE_LRA')

from handler.metadata import Metadata
from handler.download import Youtube
from handler.ffmpeg import FFMPEG

metadata = Metadata(logger=logging)
yt = Youtube(logger=logging, max_download_retries=int(MAX_DOWNLOAD_TRIES), max_results_ytsearch=int(MAX_YOUTUBE_RESULTS))
audio = FFMPEG(logger=logging, output_loudness_lufs=LOUDNESS_LUFS, loudness_peak_dbfs=LOUDNESS_PEAK_DBFS, loudness_range_lra=LOUDNESS_RANGE_LRA)

def get_cover(output_path:str, cover_url:str):
    MAX_COVER_SIZE = 1024
    if data["cover_url"] == "https://None":
        cover_data = ""
        img = Image.new("RGB", (1, 1), (255, 255, 255))
        img.save(cover_path, "JPEG")
        logging.critical("No Real Cover, using decoy jpg")
    else:
        cover_data = requests.get(data["cover_url"]).content
        try:
            img = Image.open(io.BytesIO(cover_data)).convert("RGB")
            #with open(cover_path, "wb") as f:
            #    f.write(cover_data)
            img.thumbnail((MAX_COVER_SIZE, MAX_COVER_SIZE))
            img.save(cover_path, format="JPEG", quality=80)
            logging.debug("wrote cover.jpg natively")
        except Exception as e:
            logging.debug("cover data: %s", str(e))
            logging.warning("Invalid Cover Data falling back secondary cover")
            cover_data = requests.get(data["cover_url_fallback"]).content
            try: # TODO: Add another API as fallback instead of other url
                img = Image.open(io.BytesIO(cover_data)).convert("RGB")
                #with open(cover_path, "wb") as f:
                #    f.write(cover_data)
                img.thumbnail((MAX_COVER_SIZE, MAX_COVER_SIZE))
                img.save(cover_path, format="JPEG", quality=80)
                logging.debug("wrote cover.jpg natively though had to use fallback")
            except Exception as e2:
                logging.debug("cover data: %s", str(e2))
                logging.critical("Invalid Cover Data Creating decoy JPG to download and go on")
                img = Image.new("RGB", (1, 1), (255, 255, 255))
                img.save(cover_path, "JPEG")
                logging.debug("wrote cover.jpg using decoy file")
    genre_str = ", ".join(data["genres"])

def embed_metadata(input_wav_file:str, output_file:str, title:str, artist:str, album:str, cover_path:str, date:str, bitrate:int=128):
    file_name, CODEC = output_file.rsplit(".", 1)
    if CODEC == "opus" or CODEC == "libopus":
        cmd = [
            "opusenc",
            "--bitrate", bitrate, "--vbr",
            "--title", f"{title}",
            "--artist", f"{artist}",
            "--album", f"{album}",
            "--date", f"{date}",
            #"--genre", f"{genre_str}",
            "--picture", f"3||Front Cover||{cover_path}",
            input_wav_file, f"{file_name}.{CODEC}"
        ]
    else:
        if CODEC == "flac":
            pass
        else:
            logging.warning("Codec not tested: falling back to ffmpeg auto conversion.")
        cmd = [
            "ffmpeg", 
            "-i", input_wav_file, "-i", cover_path,
            "-map", "0:a", "-map", "1:v",
            "-id3v2_version", "3",
            "-metadata:s:v", 'title="Album cover"',
            "-metadata:s:v", 'comment="Cover (Front)"',
            "-metadata:s:v:0", 'description="Front Cover"',
            "-metadata", f"{title}",
            "-metadata", f"{artist}",
            "-metadata", f"{album}",
            "-metadata", f"{date}",
            #"-metadata", f"genre={genre_str}",
            "-disposition:v", "attached_pic",
            f"{file_name}.{CODEC}"
        ]
    logging.debug("embedding metadata")
    subprocess.run(cmd, check=False)
    logging.debug("embedding metadata done")

def check_filepaths(file_path: str):
    if os.path.exists(file_path):
        return 1
    else:
        return 0

def sanitize_filename(input_string: str):
    # Split song and artist
    #if ' - ' in song_artists:
    #    song_name, artists = song_artists.rsplit(' - ', 1)
    #else:
    #    # If no ' - ', treat the whole string as song name
    #    song_name = song_artists
    #    artists = "Unknown Artist"
    # Remove invalid characters
    output = re.sub(r'[<>:"/\\|?*]', '', input_string)
    #artists = re.sub(r'[<>:"/\\|?*]', '', artists)
    # trim to a maximum length
    #max_length_artists = 100
    max_length_song = 100
    if len(output) > max_length_song:
        output = output[:max_length_song].rstrip()
    #if len(artists) > max_length_artists:
    #    artists = artists[:max_length_artists].rstrip()
    logging.debug("sanitized (%s) to (%s)", input_string, output)
    #return f'{song_name} - {artists}'
    #song_title_artists = {
    #    "title": song_name,
    #    "artist": artists
    #}
    return output

def random_alphanumeric(length: int) -> str:
    """Return a random string of the given length with characters a‑z, A‑Z, 0‑9."""
    pool = string.ascii_letters + string.digits  # 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(pool) for _ in range(length))

def download_cover(url: str, output_path):
    #img = Image.new("RGB", (1, 1), (255, 255, 255))
    #img.save(output_path, "JPEG")
    #logging.critical("No Real Cover, using decoy jpg")
    max_cover_size = 1024 # In pixels
    cover_data = requests.get(url).content
    img = Image.open(io.BytesIO(cover_data)).convert("RGB")
    img.thumbnail((max_cover_size, max_cover_size))
    img.save(output_path, format="JPEG", quality=80)
    logging.debug("wrote cover.jpg natively")

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Spotify ↔ YouTube helper")
    parser.add_argument("--song", default="", help="Search for ...")
    parser.add_argument("--youtube", default="", help="YouTube video URL")
    parser.add_argument("--cover", default="", help="Cover URL")
    args = parser.parse_args()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    # Create Lock file
    RAND_STRING_LENGTH: int = 5
    RAND_STRING = f"{random_alphanumeric(length=RAND_STRING_LENGTH)}"
    LOCK_FILE = ""
    # Check for Already Existing lock file
    tmp_retries = 100+1
    good: int = 0
    for x in range(tmp_retries):
        if check_filepaths(LOCK_FILE) == 0 and good == 2:
            break
        elif check_filepaths(LOCK_FILE):
            good = 2
        else:
            RAND_STRING = f"{random_alphanumeric(length=RAND_STRING_LENGTH)}"
            LOCK_FILE = f"{OUTPUT_DIR}/{RAND_STRING}.lock"
    with open(LOCK_FILE, 'a') as f:
        f.write("Downloading song...")

    # Variables
    tmp_song_path = f"{OUTPUT_DIR}/downloaded_{RAND_STRING}.wav"
    tmp_norm_path = f"{OUTPUT_DIR}/normalized_{RAND_STRING}.wav"
    tmp_cover_path = f"{OUTPUT_DIR}/cover_{RAND_STRING}.jpg"
    METADATA_FROM = "youtube" # TODO: False not Implemented

    logging.info("--- Starting to download a new Track with given data:\n")

    if not args.song and not args.youtube:
        logging.error('‼️ No arguments given')
        sys.exit(0)
    else:
        logging.debug('Using given Arguments')
        song = args.song
        youtube = args.youtube

    song: dict = {}
    final_output: str = ""
    if METADATA_FROM == "youtube" and args.youtube:
        # Download Sonng
        song = yt.youtube_download_metadata(url=f"{args.youtube}") # Get Metadata & Download Cover
        logging.info("Got Song: (%s)", f"{song["title"]} - {song["artist"]}")
    elif METADATA_FROM == "youtube" and args.song:
        title, artist = args.song.rsplit(" - ", 1)
        artist = artist.split(", ", 1)[0]
        song = yt.youtube_search(song_title=f"{title}", song_artist=f"{artist}")[0]
        logging.info("Got Song: (%s)", f"{song["title"]} - {song["artist"]}")
        logging.info("Song Data: scored(%s) / url(%s)", song["score"], song["url"])
    else:
        logger.error("‼️ Got No useful input")
    if args.cover:
        pass

    final_output = f"{OUTPUT_DIR}/{ sanitize_filename( input_string= f"{song["title"]} - {song["artist"]}.{AUDIO_CONTAINER}" ) }"
    if check_filepaths(final_output):
        logger.info("✅ Song Already Exists: Skipping")
        os.remove(LOCK_FILE)
        sys.exit()

    # Download -> Normalize -> Embed Metadata -> Final output song
    
    if yt.download_audio(file_path=tmp_song_path, url=f"{song["url"]}") == 1:
        logging.CRITICAL("‼️ Couldn't download song.. exiting ‼️")
        os.remove(tmp_song_path)
        os.remove(LOCK_FILE)
        sys.exit(1)
        
    analyze_result = audio.analyze_audio(file=tmp_song_path)
    audio.normalize_audio(input_file=tmp_song_path, output_file=tmp_norm_path, analysis_results=analyze_result)
    download_cover(url=song["thumbnail"], output_path=tmp_cover_path)
    try:
        embed_metadata(input_wav_file=tmp_norm_path,
                   output_file=final_output,
                   cover_path=tmp_cover_path,
                   date=song["date"],
                   title=song["title"],
                   artist=song["artist"],
                   album=song["album"], bitrate=BITRATE)
    except:
      print('‼️ An exception occurred')


    os.remove(tmp_cover_path)
    os.remove(tmp_norm_path)
    os.remove(tmp_song_path)
    os.remove(LOCK_FILE)
    if song["score"] < 25.0:
        logging.warning("✅‼️ SCORE UNDER 25 PLEASE CHECK / Downloaded: '%s'\n", final_output)
    else:
        logging.info("✅ Downloaded: '%s'", final_output)
