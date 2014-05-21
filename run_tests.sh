#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$SCRIPT_DIR/third_party/ycmd/build.sh

flake8 --select=F,C9 --max-complexity=10 $SCRIPT_DIR/python

for directory in $SCRIPT_DIR/third_party/*; do
  if [ -d "${directory}" ]; then
    export PYTHONPATH=${directory}:$PYTHONPATH
  fi
done


for directory in $SCRIPT_DIR/third_party/ycmd/third_party/*; do
  if [ -d "${directory}" ]; then
    export PYTHONPATH=${directory}:$PYTHONPATH
  fi
done

nosetests -v $SCRIPT_DIR/python
