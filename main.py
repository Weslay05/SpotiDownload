import logging
import os
import json
import re
import argparse
import subprocess
import requests
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


# Spotify API Key
CLIENT_ID = "client-id"
CLIENT_SECRET = "client-secret"


# Configure logging
logging.basicConfig(
    filename="assets/spotify_youtube.log",     # log file name
    filemode="a",
    encoding="utf-8",
    level=logging.INFO,                 # log level: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Spotify Client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)


def sanitize_filename(song_artists):
    # Split song and artist
    if ' - ' in song_artists:
        song_name, artists = song_artists.split(' - ', 1)
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
    return f'{song_name} - {artists}'

def download_audio(file, url):
    """Download audio from YouTube video URL."""
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': file,
        'noplaylist': True,
        'quiet': False,  # Show progress during download
    }   
    # download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        logging.debug("Downloaded %s", url)

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

def get_youtube_link(search: str, track_url, tolerance, max_results):
    # Variables
    track = sp.track(track_url)
    length_ms = track["duration_ms"]
    target_seconds = length_ms // 1000
    
    
    # search function
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"{query_type}{max_results}:{search_for}", download=False)
                return info.get("entries", []) if info else []
            except Exception as e:
                logging.error("Error in %s: %s", query_type, str(e))
                return []
            
            
    # # --- 1. Try YouTube Music ---
    # for entry in do_search("https://music.youtube.com/search?q=", search):
    #     if entry.get("duration") is None:
    #         continue
    #     yt_duration = entry["duration"]
    #     if abs(yt_duration - target_seconds) <= tolerance:
    #         return entry["webpage_url"]  # good match
    # logging.warning(
    #     "YouTube Music failed, falling back to Youtube Search results for %s",
    #     search
    # )
    
    #  --- 2. Fallback to YouTube Search---
    for entry in do_search("ytsearch", search):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.warning(
        "Youtube Search failed, falling back to YouTube Topic Search for %s",
        search
    )
    
    #  --- 3. Fallback to YouTube Topic Video---
    for entry in do_search("ytsearch", f"{search} topic"):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.warning(
        "Youtube Topic Search failed, falling back to Youtube Lyrics Video for %s",
        search
    )
    
    #  --- 4. Fallback to Youtube Lyrics Video---
    for entry in do_search("ytsearch", f"{search} AND lyrics"):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance:
            logging.debug("returning good youtube url")
            return entry["webpage_url"]
    logging.critical(
        "Youtube Lyrics Video not found, falling back to first best result for %s",
        search
    )
    
    # --- 5. As a last resort, return the first YouTube result ---
    youtube_entries = do_search("ytsearch", search)
    if youtube_entries:
        return youtube_entries[0]["webpage_url"]
    
    # --- Error ---
    logging.critical("no yt url found")
    return None

def get_spotify_track_url(song_artists):
    query = song_artists
    results = sp.search(q=query, type='track', limit=1)
    items = results['tracks']['items']
    if items:
        track = items[0]
        return track['external_urls']['spotify']  # URL of the track
    else:
        logging.warning("could not get spotify track url")
        return None
    
def get_spotify_name_artits(url):
    track = sp.track(url)
    name = track['name']          # Track name
    artists = ", ".join([a['name'] for a in track['artists']])  # Artist(s)
    return f"{name} - {artists}"

def fetch_metadata(track_url):
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
    cover_data = requests.get(data["cover_url"]).content
    with open(cover_path, "wb") as f:
        f.write(cover_data)
        logging.debug("wrote cover.jpg")
        
    genre_str = ", ".join(data["genres"])
    
    cmd = [
        "ffmpeg", 
        "-n", # always not overwrite
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


if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Spotify ↔ YouTube helper")
    parser.add_argument("--song", default="", help="Search for ...")
    parser.add_argument("--spotify", default="", help="Spotify track URL")
    parser.add_argument("--youtube", default="", help="YouTube video URL")
    args = parser.parse_args()
    
    
    # Main Variables
    logging.info("Starting to download a new Track with given data")
    if not args.song and not args.spotify:
        logging.info('Using in-script values')
        song = ""
        spotify = ""
        youtube = ""
    else:
        logging.info('Using given Arguments')
        song = args.song
        spotify = args.spotify
        youtube = args.youtube
    # Secondary Variables
    tolerance_sec = 2
    max_results_ytsearch = 10
    input_file = "output/tmp_downloaded.wav"
    tmp_file = "output/tmp_normalized.wav"
    tmp_cover = "output/tmp_cover_data.jpg"
    
    
    # Look if something is missing
    if not song and not spotify :
        print('No Song name or Spotify URL')
    else:
        if not song:
            file_name = get_spotify_name_artits(spotify)
            logging.info("No Song name given, generated one is (%s)", file_name)
            print(f'auto-generated file name is : "{file_name}"')
        if not spotify:
            # Spotify URL
            spotify_url = get_spotify_track_url(song)
            logging.info("No spotify url given, generated one is (%s)", spotify_url)
            print(f'auto-generated spotify url is : "{spotify_url}"')
            # File Name
            file_name = get_spotify_name_artits(spotify_url)
            print(f'auto-generated file name is : "{file_name}"')
    # Correct File Name
    formatted_name = sanitize_filename(file_name)
    final_file = f"output/{formatted_name}.flac"
    if os.path.exists(final_file):
        print("file already exists")
        logging.info(
            "File (%s) already exists, not overwriting it but program will go on because why not",
            final_file
        )
    if not youtube:
        youtube_url = get_youtube_link(
            formatted_name, spotify_url, tolerance_sec, max_results_ytsearch
        )
        logging.info("no youtube url given, generated one is (%s)", youtube_url)
        print(f'auto-generated youtube url is : "{youtube_url}"')
        

    # Download Audio
    download_audio(input_file, youtube_url)
    # Analyse Audio
    measured = analyze_audio(input_file)
    # Normalize Audio
    normalize_audio(input_file, tmp_file, measured)
    # Get Metadata
    metadata = fetch_metadata(spotify_url)
    # Apply Metadata
    embed_metadata(tmp_file, final_file, tmp_cover, metadata)
    # Delete Temp Files
    os.remove(tmp_file)
    os.remove(input_file)
    os.remove(tmp_cover)
    logging.debug("removing temp files")


    print(f"✅ Done! Final file saved as {final_file}")
    logging.info("Done! Final file saved as (%s)\n", final_file)
