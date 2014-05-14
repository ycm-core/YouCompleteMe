#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$SCRIPT_DIR/third_party/ycmd/build.sh "$@"

# Remove old YCM libs if present so that YCM can start.
rm python/*ycm_core.* &> /dev/null
rm python/*ycm_client_support.* &> /dev/null
rm python/*clang*.* &> /dev/null
