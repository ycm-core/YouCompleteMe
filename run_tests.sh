#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function usage {
  echo "Usage: $0 [--skip-build]"
  exit 0
}

flake8 --select=F,C9 --max-complexity=10 "${SCRIPT_DIR}/python"
skip_build=false

for flag in $@; do
  case "$flag" in
    --skip-build)
      skip_build=true
      ;;
    *)
      usage
      ;;
  esac
done

if ! $skip_build; then
    "${SCRIPT_DIR}/third_party/ycmd/build.py"
fi

for directory in "${SCRIPT_DIR}"/third_party/*; do
  if [ -d "${directory}" ]; then
    export PYTHONPATH=${directory}:$PYTHONPATH
  fi
done


for directory in "${SCRIPT_DIR}"/third_party/ycmd/third_party/*; do
  if [ -d "${directory}" ]; then
    export PYTHONPATH=${directory}:$PYTHONPATH
  fi
done

nosetests -v "${SCRIPT_DIR}/python"
