#!/usr/bin/env bash

set -e

function command_exists {
  hash "$1" 2>/dev/null ;
}

function cmake_install {
  if [[ `uname -s` == "Darwin" ]]; then
    homebrew_cmake_install
  else
    linux_cmake_install
  fi
}

function homebrew_cmake_install {
  if command_exists brew; then
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
    lib_python="${python_prefix}/lib/lib${which_python}"
    if [ -f "${lib_python}.a" ]; then
      python_library+="${lib_python}.a"
    else
      python_library+="${lib_python}.dylib"
    fi
    python_include+="${python_prefix}/include/${which_python}"
  fi

  echo "${python_library} ${python_include}"
}

function num_cores {
  if command_exists nproc; then
   num_cpus=$(nproc)
  else
    num_cpus=1
    if [[ `uname -s` == "Linux" ]]; then
      num_cpus=$(grep -c ^processor /proc/cpuinfo)
    else
      # Works on Mac and FreeBSD
      num_cpus=$(sysctl -n hw.ncpu)
    fi
  fi
  echo $num_cpus
}


function install {
  ycm_dir=`pwd`
  build_dir=`mktemp -d -t ycm_build.XXXXXX`
  pushd $build_dir

  if [[ `uname -s` == "Darwin" ]]; then
    cmake -G "Unix Makefiles" $(python_finder) "$@" . $ycm_dir/cpp
  else
    cmake -G "Unix Makefiles" "$@" . $ycm_dir/cpp
  fi

  make -j $(num_cores) ycm_core
  popd
  rm -rf $build_dir
}

function testrun {
  ycm_dir=`pwd`
  build_dir=`mktemp -d -t ycm_build.XXXXXX`
  pushd $build_dir

  cmake -G "Unix Makefiles" "$@" . $ycm_dir/cpp
  make -j $(num_cores) ycm_core_tests
  cd ycm/tests
  LD_LIBRARY_PATH=$ycm_dir/python ./ycm_core_tests

  popd
  rm -rf $build_dir
}

function linux_cmake_install {
  echo "Please install CMake using your package manager and retry."
  exit 1
}

function usage {
  echo "Usage: $0 [--clang-completer [--system-libclang]]"
  exit 0
}

cmake_args=''
while [ -n "$1" ]; do
  case "$1" in
    --clang-completer)
      cmake_args="$cmake_args -DUSE_CLANG_COMPLETER=ON"
      shift
      ;;
    --system-libclang)
      cmake_args="$cmake_args -DUSE_SYSTEM_LIBCLANG=ON"
      shift
      ;;
    *)
      usage
      ;;
  esac
done

if [[ $cmake_args == *-DUSE_SYSTEM_LIBCLANG=ON* ]] && \
   [[ $cmake_args != *-DUSE_CLANG_COMPLETER=ON* ]]; then
  usage
fi

if ! command_exists cmake; then
  echo "CMake is required to build YouCompleteMe."
  cmake_install
fi

if [ -z "$YCM_TESTRUN" ]; then
  install $cmake_args $EXTRA_CMAKE_ARGS
else
  testrun $cmake_args $EXTRA_CMAKE_ARGS
fi

