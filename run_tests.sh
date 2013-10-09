#!/usr/bin/env bash

set -e

function usage {
  echo "Usage: $0 [--no-clang-completer]"
  exit 0
}

flake8 --select=F,C9 --max-complexity=10 python

use_clang_completer=true
for flag in $@; do
  case "$flag" in
    --no-clang-completer)
      use_clang_completer=false
      ;;
    *)
      usage
      ;;
  esac
done

if [ -n "$USE_CLANG_COMPLETER" ]; then
  use_clang_completer=$USE_CLANG_COMPLETER
fi

if $use_clang_completer; then
  extra_cmake_args="-DUSE_CLANG_COMPLETER=ON -DUSE_DEV_FLAGS=ON"
else
  extra_cmake_args="-DUSE_DEV_FLAGS=ON"
fi

EXTRA_CMAKE_ARGS=$extra_cmake_args YCM_TESTRUN=1 ./install.sh --omnisharp-completer

for directory in third_party/*; do
  if [ -d "${directory}" ]; then
    export PYTHONPATH=$PWD/${directory}:$PYTHONPATH
  fi
done

if $use_clang_completer; then
  nosetests -v python
else
  nosetests -v --exclude=".*Clang.*" python
fi
