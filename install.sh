#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

$SCRIPT_DIR/third_party/ycmd/build.sh "$@"
