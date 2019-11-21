#!/bin/sh

echo "WARNING: this script is deprecated. Use the install.py script instead." 1>&2


SCRIPT_DIR=$(dirname $0 || exit $?)

command_exists() {
  command -v "$1" >/dev/null 2>&1 ;
}

PYTHON_BINARY=python

$PYTHON_BINARY "$SCRIPT_DIR/install.py" "$@" || exit $?
