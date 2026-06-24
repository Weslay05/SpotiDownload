#!/usr/bin/env bash

# USAGE: script "path/to/python-env"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_ENV = $1

cd $DIR/../..
source PYTHON_ENV/bin/activate
pip install --upgrade -r "./requirements.txt"

cmd="python playlist.py"

read -p "Enter CSV File Path : " csv
[ -n "$csv" ] && cmd="$cmd --csv \"$csv\"" # Add Command

read -p "Enter Music Search Dir : " music
[ -n "$music Search Dir" ] && cmd="$cmd --music \"$music\"" # Add Command

# Command
echo ""
echo "Run : $cmd"
echo ""

eval $cmd
