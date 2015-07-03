#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

build_file=$SCRIPT_DIR/third_party/ycmd/build.py

if [[ ! -f "$build_file" ]]; then
  echo "File $build_file doesn't exist; installing modules"
  git submodule update --init --recursive
  if [[ ! -f "$build_file" ]]; then
    echo "Hmmm, still not here after installing modules. Sorry, I don't know how to proceed"
    exit 1
  fi
fi

command_exists() {
  command -v "$1" >/dev/null 2>&1 ;
}

PYTHON_BINARY=python
if command_exists python2; then
  PYTHON_BINARY=python2
fi

$PYTHON_BINARY "$build_file" "$@"

# Remove old YCM libs if present so that YCM can start.
rm -f python/*ycm_core.* &> /dev/null
rm -f python/*ycm_client_support.* &> /dev/null
rm -f python/*clang*.* &> /dev/null
