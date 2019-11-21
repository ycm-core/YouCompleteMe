#!/bin/sh

echo "WARNING: this script is deprecated. Use the install.py script instead." 1>&2


SCRIPT_DIR=$(dirname $0 || exit $?)

python3 "$SCRIPT_DIR/install.py" "$@" || exit $?
