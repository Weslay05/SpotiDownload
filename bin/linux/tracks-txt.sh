#!/bin/bash
# Init
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PATH="$DIR/../../conda-debian/bin":$PATH
cd "$DIR/../.."

# Track.txt Path
read -p "Enter Music file.txt path (or leave for default) : " track_file
if [ -z "$track_file" ] ; then
    track_file="./assets/tracks.txt"
    echo "using $track_file"
fi
# Mode
read -p "Enter track fetch Mode, type whats in one of the 3 brackets (SongSearch(song), SpotifyURL(spotify), YoutubeURL(youtube)) : " mode

# Upgrade dependencies
pip install --upgrade -r "./requirements.txt"
echo -e "\n\n\n"

# Activate the conda environment
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate ./conda-debian

echo "Spotify Downloader Batch"

echo ""
echo "Tracks to Download : "
# Loop through each line in tracks.txt (strip Windows \r safely)
tr -d '\r' < $track_file | while IFS= read -r track; do
    echo "$track"
    #python main.py --$mode "$track"
done
echo ""

echo ""
echo "Starting to Process"
echo ""
echo ""

# Loop through each line in tracks.txt (strip Windows \r safely)
tr -d '\r' < "$track_file" | while IFS= read -r track; do
    python main.py --$mode "$track"
done

echo "done"
read -rp "Press any key to continue..." -n1
echo
