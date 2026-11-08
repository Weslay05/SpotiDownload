#!/usr/bin/env bash

# USAGE: script "path/to/python-env"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_ENV = $1

cd $DIR/../..
source ${PYTHON_ENV}/bin/activate
pip install --upgrade -r "./requirements.txt"
echo ""
echo ""
echo ""

# Get Song
read -p "Enter Song in format (title - artist) | (Optional): " song_name

# Youtube Url
[ -n "$song_name" ] && read -p "Enter Youtube_url (Optional but more accurate): " youtube_url
[ -n "$song_name" ] || read -p "Enter Youtube_url (Required): " youtube_url

[ -n "$song_name" ] && cmd="python src/main.py --song \"$song_name\"" # Add Command
[ -n "$youtube_url" ] && cmd="python src/main.py --youtube \"$youtube_url\"" # Add Command

# Command
echo ""
echo "Running : $cmd"
echo ""

eval $cmd
nohup nautilus "./output" >/dev/null 2>&1 &

echo ""
read -p "Press Any Key to exit ..."
