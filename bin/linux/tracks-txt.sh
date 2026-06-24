#!/usr/bin/env bash

# USAGE: script "path/to/python-env"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_ENV = $1

cd $DIR/../..
source PYTHON_ENV/bin/activate
pip install --upgrade -r "./requirements.txt"

xargs -I {} command_name arguments {} < input.txt