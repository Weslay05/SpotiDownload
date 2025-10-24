#! /usr/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#source $HOME/miniconda3/etc/profile.d/conda.sh
#conda activate $DIR/../../conda-debian
export PATH="$DIR/../../conda-debian/bin":$PATH
cd $DIR/../..
pip install --upgrade -r "./requirements.txt"
echo ""
echo ""
echo ""

cmd="python playlist.py"

read -p "Enter CSV File Path : " youtube_url
[ -n "$csv" ] && cmd="$cmd --csv \"$csv\"" # Add Command

read -p "Enter Music Search Dir (Optional): " Music Search Dir
[ -n "$Music Search Dir" ] && cmd="$cmd --music \"$Music Search Dir\"" # Add Command

# Command
echo ""
echo "Run : $cmd"
echo ""

eval $cmd

echo ""
read -p "Press Any Key to exit ..."