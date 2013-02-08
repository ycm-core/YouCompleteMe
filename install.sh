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
    echo "Homebrew was not found installed in your system."
    echo "Go to http://mxcl.github.com/homebrew/ and follow the instructions."
    echo "Or install CMake somehow and retry."
    exit 1
  fi
}

function install {
  ycm_dir=`pwd`
  build_dir=`mktemp -d -t ycm_build.XXXX`
  pushd $build_dir
  cmake -G "Unix Makefiles" $1 . $ycm_dir/cpp
  make ycm_core
  popd
}

function linux_cmake_install {
  echo "Please install CMake using your package manager and retry."
  exit 1
}

function usage {
  echo "Usage: $0 [--clang-completer]"
  exit 0
}

if [[ $# -gt 1 ]]; then
  usage
fi

case "$1" in
  --clang-completer)
    cmake_args='-DUSE_CLANG_COMPLETER=ON'
    ;;
  '')
    cmake_args=''
    ;;
  *)
    usage
    ;;
esac

if [[ ! -z `which cmake &> /dev/null` ]]; then
  echo "CMake is required to build YouCompleteMe."
  cmake_install
fi
install $cmake_args
