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
    filename="spotify_youtube.log",     # log file name
    filemode="a",
    encoding="utf-8",
    level=logging.INFO,                 # log level: DEBUG, INFO, WARNING, ERROR
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
    
    # Optionally trim to a maximum length
    max_length_artists = 100
    max_length_song = 50
    if len(song_name) > max_length_song:
        song_name = song_name[:max_length_song].rstrip()
    if len(artists) > max_length_artists:
        artists = artists[:max_length_artists].rstrip()
    
    logging.debug(f'{song_name} - {artists}')
    return f'{song_name} - {artists}'

def download_audio(file_name, youtube_url):
    cmd = f"yt-dlp -f 251 {youtube_url} -o {file_name}"
    subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    logging.debug(f"finished downloading ({file_name})")

def analyze_audio(input_file):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=14:print_format=json",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    output = result.stderr
    json_start = output.find("{")
    json_end = output.rfind("}") + 1
    logging.debug(f'Analysed audio and return loudnorm input values')
    return json.loads(output[json_start:json_end])

def normalize_audio(input_file, tmp_file, measured):
    filter_settings = (
        f"loudnorm=I=-14:TP=-1.5:LRA=14:"
        f"measured_I={measured['input_i']}:"
        f"measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:"
        f"measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:"
        f"linear=true:print_format=summary"
    )
    cmd = ["ffmpeg", "-i", input_file, "-af", filter_settings, tmp_file]
    subprocess.run(cmd)
    logging.debug(f'Applying Norm')

def get_youtube_link(search: str, track_url, tolerance, max_results=1):
    track = sp.track(track_url)
    length_ms = track["duration_ms"]
    
    def do_search(query_type):
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"{query_type}{max_results}:{search}"
            info = ydl.extract_info(search_query, download=False)
            return info.get("entries", []) if info else []
    
    target_seconds = length_ms // 1000

    # # --- 1. Try YouTube Music ---
    # for entry in do_search("ytsearch"):
    #     if entry.get("duration") is None:
    #         continue
    #     yt_duration = entry["duration"]
    #     if abs(yt_duration - target_seconds) <= tolerance:
    #         return entry["webpage_url"]  # good match
     
    #  --- 2. Fallback to YouTube ---
    # logging.warning(f'Couldnt find ({search}) in ytmusic search trying normal youtube next')
    for entry in do_search("ytsearch"):
        if entry.get("duration") is None:
            continue
        yt_duration = entry["duration"]
        if abs(yt_duration - target_seconds) <= tolerance:
            logging.debug(f'returning good youtube url')
            return entry["webpage_url"]
    
    # --- 3. As a last resort, return the first YouTube result ---
    logging.error(f'Couldnt find ({search}) trying first best search result')
    youtube_entries = do_search("ytsearch")
    if youtube_entries:
        logging.warning(f'returning fallback youtube url')
        return youtube_entries[0]["webpage_url"]
    
    logging.critical(f'no yt url found')
    return None

def get_spotify_track_url(song_artists):
    query = song_artists
    results = sp.search(q=query, type='track', limit=1)
    items = results['tracks']['items']
    if items:
        track = items[0]
        return track['external_urls']['spotify']  # URL of the track
    else:
        logging.warning(f'could not get spotify track url')
        return None
    
def get_spotify_name_artits(spotify_url):
    track = sp.track(spotify_url)
    name = track['name']          # Track name
    artists = ", ".join([a['name'] for a in track['artists']])  # Artist(s)
    return f"{name} - {artists}"

def fetch_metadata(track_url):
    track = sp.track(track_url)
    
    # Get artist details
    artist_id = track["artists"][0]["id"]
    artist_data = sp.artist(artist_id)
    
    metadata = {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "date": track["album"]["release_date"][:4],
        "cover_url": track["album"]["images"][0]["url"],
        "genres": artist_data.get("genres", [])
    }
    logging.debug(f'return metadata')
    return metadata

def embed_metadata(wav_file, output_file, metadata):
    cover_data = requests.get(metadata["cover_url"]).content
    with open("files/tmp_cover_data.jpg", "wb") as f:
        f.write(cover_data)
        logging.debug(f'wrote cover.jpg')
        
    genre_str = ", ".join(metadata["genres"])
    
    cmd = [
        "ffmpeg", "-i", wav_file, "-i", "files/tmp_cover_data.jpg",
        "-map", "0", "-map", "1",
        #"-acodec", "flac",
        #"-compression_level", "8",
        "-metadata", f"title={metadata['title']}",
        "-metadata", f"artist={metadata['artist']}",
        "-metadata", f"album={metadata['album']}",
        "-metadata", f"date={metadata['date']}",
        "-metadata", f"genre={genre_str}",
        "-disposition:v", "attached_pic",
        output_file
    ]
    logging.debug(f'embedding metadata')
    subprocess.run(cmd)
    logging.debug(f'embedding metadata done')

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Spotify ↔ YouTube helper")
    parser.add_argument("--file_name", default="", help="Optional file name")
    parser.add_argument("--spotify_url", default="", help="Spotify track URL")
    parser.add_argument("--youtube_url", default="", help="YouTube video URL")
    args = parser.parse_args()
    
    # Main Variables
    logging.info(f'Starting to download a new Track with given data')
    if not args.file_name and not args.spotify_url:
        logging.info('Using in-script values')
        file_name = "song - artists"
        spotify_url = "https://open.spotify.com/track/abcdefghi1234567"
        youtube_url = "https://music.youtube.com/watch?v=abcdefghi1234567"
    else:
        logging.info('Using given Arguments')
        file_name = args.file_name
        spotify_url = args.spotify_url
        youtube_url = args.youtube_url
    
    # Secondary Variables
    tolerance_sec = 1
    input_file = "files/tmp_downloaded.webm"
    tmp_file = "files/tmp_normalized.wav"
    # Look if something is missing
    if not file_name and not spotify_url :
        print('No Song name or Spotify URL')
    else:
        if not file_name:
            file_name = get_spotify_name_artits(spotify_url)
            logging.info(f'found no file name, generated one is ({file_name})')
            print(f'auto-generated file name is : "{file_name}"')
        if not spotify_url:
            spotify_url = get_spotify_track_url(file_name)
            logging.info(f'found no spotify url, generated one is ({spotify_url})')
            print(f'auto-generated spotify url is : "{spotify_url}"')
            
    # Correct File Name
    formatted_name = sanitize_filename(file_name)
    final_file = f"files/{formatted_name}.flac"
    if not youtube_url:
        youtube_url = get_youtube_link(formatted_name, spotify_url, tolerance_sec, max_results=1)
        logging.info(f'found no youtube url, generated one is ({youtube_url})')
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
    embed_metadata(tmp_file, final_file, metadata)
    
    # Delete Temp Files
    os.remove(tmp_file)
    os.remove(input_file)
    os.remove("files/tmp_cover_data.jpg")
    logging.debug(f'removing temp files')

    print(f"✅ Done! Final file saved as {final_file}")
    logging.info(f"Done! Final file saved as {final_file}\n")
