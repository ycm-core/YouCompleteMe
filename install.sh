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

function python_finder {
  python_library="-DPYTHON_LIBRARY="
  python_include="-DPYTHON_INCLUDE_DIR="

  # The CMake 'FindPythonLibs' Module does not work properly.
  # So we are forced to do its job for it.
  python_prefix=$(python-config --prefix | sed 's/^[ \t]*//')
  if [ -f "${python_prefix}/Python" ]; then
    python_library+="${python_prefix}/Python"
    python_include+="${python_prefix}/Headers"
  else
    which_python=$(python -c 'import sys;print(sys.version)' | sed 's/^[ \t]*//')
    which_python="python${which_python:0:3}"
    lib_python="${python_prefix}/lib/libpython${which_python}"
    if [ -f "${lib_python}.a" ]; then
      python_library+="${lib_python}.a"
    else
      python_library+="${lib_python}.dylib"
    fi
    python_include+="${python_prefix}/include/${which_python}"
  fi

  echo "${python_library} ${python_include}"
}

function install {
  ycm_dir=`pwd`
  build_dir=`mktemp -d -t ycm_build.XXXX`
  pushd $build_dir
  cmake -G "Unix Makefiles" $(python_finder) $1 . $ycm_dir/cpp
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
