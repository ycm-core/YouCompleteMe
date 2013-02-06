#!/usr/bin/env bash

set -e

function cmake_install {
  if [[ `uname -s` == "Darwin" ]]; then
    homebrew_cmake_install
  else
    linux_cmake_install
  fi
}

function homebrew_cmake_install {
  if [[ `which brew &> /dev/null` ]]; then
    brew install cmake
  else
    echo "Go get homebrew, lazy! And retry."
    exit 1
  fi
}

function install {
  ycm_dir=`pwd`
  build_dir=`mktemp -d -t ycm_build`
  pushd $build_dir
  cmake $ycm_dir/cpp
  make ycm_core
  popd
}

function linux_cmake_install {
  echo "Please install 'cmake' using your package manager and retry."
  exit 1
}

if [[ ! -z `which cmake &> /dev/null` ]]; then
  cmake_install
fi
install
