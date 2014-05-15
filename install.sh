#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$SCRIPT_DIR/third_party/ycmd/build.sh "$@"

# Remove old YCM libs if present so that YCM can start.
rm -f python/*ycm_core.* &> /dev/null
rm -f python/*ycm_client_support.* &> /dev/null
rm -f python/*clang*.* &> /dev/null
