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

python playlist.py