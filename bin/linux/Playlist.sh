#! /usr/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#source $HOME/miniconda3/etc/profile.d/conda.sh
#conda activate $DIR/../../conda-debian
export PATH="$DIR/../../conda-debian/bin":$PATH
cd $DIR/../..

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
