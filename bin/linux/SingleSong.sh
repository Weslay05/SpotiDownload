#!/usr/bin/env bash

# USAGE: script "path/to/python-env"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_ENV = $1

cd $DIR/../..
source PYTHON_ENV/bin/activate
pip install --upgrade -r "./requirements.txt"
echo ""
echo ""
echo ""

cmd="python main.py"

# Youtube Url
read -p "Enter Youtube_url (Optional): " youtube_url
[ -n "$youtube_url" ] && cmd="$cmd --youtube \"$youtube_url\"" # Add Command

# Spotify_url + File Name
read -p "Enter Spotify Url (Optional): " spotify_url
if [ -n "$spotify_url" ]; then
    cmd="$cmd --spotify \"$spotify_url\"" # Add Command
    read -p "Enter Song Name and Artist (Optional): " song
    cmd="$cmd --song \"$song\"" # Add Command
else
    read -p "Enter Song Name and Artist (Required): " song
    cmd="$cmd --song \"$song\"" # Add Command
fi

# Command
echo ""
echo "Run : $cmd"
echo ""

eval $cmd
nohup dolphin "./output" >/dev/null 2>&1 &

echo ""
read -p "Press Any Key to exit ..."
