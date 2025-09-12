import csv
import os

# --- CONFIG ---
CSV_FILE = "assets/Wide_Known_Songs.csv"   # exported from Exportify or Spotlistr
MUSIC_DIR = r"E:\Volume\pixels\Music\.newsongs\files" # root folder of your FLAC library
OUTPUT_M3U = "playlist.m3u"

# Column name from the CSV for song title (depends on export)
TITLE_COLUMN = "Track Name"  # Exportify usually uses this

# --- SCRIPT ---
def find_song_path(song_name, music_dir):
    """Search recursively for a file containing the song name (case-insensitive)."""
    song_lower = song_name.lower()
    for root, _, files in os.walk(music_dir):
        for f in files:
            if song_lower in f.lower():
                return os.path.join(root, f)
    return None


def main():
    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        song_names = [row[TITLE_COLUMN] for row in reader]

    found_paths = []
    missing = []

    for song in song_names:
        path = find_song_path(song, MUSIC_DIR)
        if path:
            found_paths.append(path)
        else:
            missing.append(song)

    with open(OUTPUT_M3U, "w", encoding="utf-8") as m3u:
        for p in found_paths:
            m3u.write(p + "\n")

    print(f"✅ Playlist written to {OUTPUT_M3U}")
    if missing:
        print("⚠️ Songs not found:")
        for m in missing:
            print(" -", m)


if __name__ == "__main__":
    main()
