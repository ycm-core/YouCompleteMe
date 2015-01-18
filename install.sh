#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

build_file=$SCRIPT_DIR/third_party/ycmd/build.py

if [[ ! -f "$build_file" ]]; then
  echo "File $build_file doesn't exist; you probably forgot to run:"
  printf "\n\tgit submodule update --init --recursive\n\n"
  exit 1
fi

PYTHON2=python
command -v python2 >/dev/null && PYTHON2=python2
$PYTHON2 "$build_file" "$@"

# Remove old YCM libs if present so that YCM can start.
rm -f python/*ycm_core.* &> /dev/null
rm -f python/*ycm_client_support.* &> /dev/null
rm -f python/*clang*.* &> /dev/null
