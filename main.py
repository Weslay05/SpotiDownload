import json
import subprocess
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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

def fetch_metadata(track_url, client_id, client_secret):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret
    ))
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
    return metadata

def embed_metadata(wav_file, output_file, metadata):
    cover_data = requests.get(metadata["cover_url"]).content
    with open("files/cover_data.jpg", "wb") as f:
        f.write(cover_data)
        
    genre_str = ", ".join(metadata["genres"])
    
    cmd = [
        "ffmpeg", "-i", wav_file, "-i", "files/cover_data.jpg",
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
    subprocess.run(cmd)

if __name__ == "__main__":
    # Main Variables
    input_file = "files/someaudio.abc"
    spotify_url = "https://open.spotify.com/track/abcdef1234567"
    final_file = "files/output.flac"
    # Secondary Variables
    tmp_file = "files/tmp_normalized.wav"

    # Spotify API Key
    CLIENT_ID = "CLIENT_ID"
    CLIENT_SECRET = "CLIENT_SECRET"

    measured = analyze_audio(input_file)
    
    normalize_audio(input_file, tmp_file, measured)

    metadata = fetch_metadata(spotify_url, CLIENT_ID, CLIENT_SECRET)

    embed_metadata(tmp_file, final_file, metadata)

    print(f"✅ Done! Final file saved as {final_file}")
