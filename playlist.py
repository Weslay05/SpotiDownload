import argparse
import csv
import os
import platform

# --- CONFIG ---
OUTPUT_M3U = "assets/playlist.m3u"

# Column name from the CSV for song title (depends on export)
TITLE_COLUMN = "Track Name"  # Exportify usually uses this
ARTIST_COLUMN = "Artist Name(s)" # And this

def find_song_path(song_name, music_dir):
    """Search recursively for a file containing the song name (case-insensitive)."""
    song_lower = song_name.lower()
    for root, _, files in os.walk(music_dir):
        for f in files:
            if song_lower in f.lower():
                return os.path.join(root, f)
    return None

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="m3u file generator")
    parser.add_argument("--csv", default="", help="CSV file Path")
    parser.add_argument("--music", default="", help="Music Search Folder")
    args = parser.parse_args()
    
    # Check if everything is there
    if not args.csv:
        print("Non existing csv file path")
    if not args.music:
        print("Non existing music file path")
    
    # Set Args
    if platform.system() == 'Windows':
        csv_file = fr"{args.csv}"
        music_dir = fr"{args.music}"  # Search for Songs in ...
    elif platform.system() == 'Linux':
        csv_file = f"{args.csv}"
        music_dir = f"{args.music}"  # Search for Songs in ...
    print("Using : ", csv_file)
    print("Searching for Music in : ", music_dir)
    
    
    with open(csv_file, newline='', encoding="utf-8") as csvfile:
        reader = list(csv.DictReader(csvfile))
        song_names = [row[TITLE_COLUMN] for row in reader]
        artist = [row[ARTIST_COLUMN] for row in reader]

    found_paths = []
    missing = []

    for song, artist in zip(song_names, artist):
        path = find_song_path(song, music_dir)
        if path:
            found_paths.append(path)
        else:
            missing.append((song, artist))

    with open(OUTPUT_M3U, "w", encoding="utf-8") as m3u:
        for p in found_paths:
            m3u.write(p + "\n")

    print(f"✅ Playlist written to {OUTPUT_M3U}")
    if missing:
        print("⚠️ Songs not found:")
        for song, artist in missing:
            print(f"{song} - {artist}")
