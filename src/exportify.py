import argparse
import csv
import platform

# --- CONFIG ---
OUTPUT = "assets/tracks.txt"

# Column name from the CSV for song title (depends on export)
TITLE_COLUMN = "Track Name"  # Exportify usually uses this
ARTIST_COLUMN = "Artist Name(s)" # And this

if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="m3u file generator")
    parser.add_argument("--csv", default="", help="CSV file Path")
    args = parser.parse_args()
    
    # Check if everything is there
    if not args.csv:
        print("Non existing csv file path")
    
    # Set Args
    if platform.system() == 'Windows':
        csv_file = fr"{args.csv}"
        music_dir = fr"{args.music}"  # Search for Songs in ...
    elif platform.system() == 'Linux':
        csv_file = f"{args.csv}"
    print("Using : ", csv_file)
    
    
    with open(csv_file, newline='', encoding="utf-8") as csvfile:
        reader = list(csv.DictReader(csvfile))
        song_names = [row[TITLE_COLUMN] for row in reader]
        artist = [row[ARTIST_COLUMN] for row in reader]

    songs = []
    missing = []

    for song, artist in zip(song_names, artist):
        songs.append(f"{song} - {artist}")

    with open(OUTPUT, "w", encoding="utf-8") as file:
        for song in songs:
            file.write(song + "\n")

    print(f"✅ Playlist written to {OUTPUT}")
    if missing:
        print("⚠️ Songs not found:")
        for song, artist in missing:
            print(f"{song} - {artist}")
