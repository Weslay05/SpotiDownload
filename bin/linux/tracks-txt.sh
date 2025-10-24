#!/bin/bash
# Init
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PATH="$DIR/../../conda-debian/bin":$PATH
cd "$DIR/../.."

# Mode
read -p "Enter track fetch Mode, type whats in one of the 3 brackets (SongSearch(song), SpotifyURL(spotify), YoutubeURL(youtube)) : " mode
# Validate input
if [ "$mode" = "song" ] || [ "$mode" = "spotify" ] || [ "$mode" = "youtube" ]; then
    echo "Mode set to: $mode"
else
    echo "Invalid mode, using default mode : SongSearch"
    mode="song"
fi

# Upgrade dependencies
pip install --upgrade -r "./requirements.txt"
echo -e "\n\n\n"

# Activate the conda environment
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate ./conda-debian

echo "Spotify Downloader Batch"

# Loop through each line in tracks.txt (strip Windows \r safely)
tr -d '\r' < "assets/tracks.txt" | while IFS= read -r track; do
    echo "Processing: $track"
    python main.py --$mode "$track"
done

echo "done"
read -rp "Press any key to continue..." -n1
echo
