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
    # This check is for for CYGWIN
    elif [ -f "${lib_python}.dll.a" ]; then
      python_library+="${lib_python}.dll.a"
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

  make -j $(num_cores) ycm_support_libs
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
  echo "Usage: $0 [--clang-completer [--system-libclang]] [--omnisharp-completer]"
  exit 0
}

function check_third_party_libs {
  libs_present=true
  for folder in third_party/*; do
    num_files_in_folder=$(find $folder -maxdepth 1 -mindepth 1 | wc -l)
    if [[ $num_files_in_folder -eq 0 ]]; then
      libs_present=false
    fi
  done

  if ! $libs_present; then
    echo "Some folders in ./third_party are empty; you probably forgot to run:"
    printf "\n\tgit submodule update --init --recursive\n\n"
    exit 1
  fi
}

cmake_args=""
omnisharp_completer=false
for flag in $@; do
  case "$flag" in
    --clang-completer)
      cmake_args="-DUSE_CLANG_COMPLETER=ON"
      ;;
    --system-libclang)
      cmake_args="$cmake_args -DUSE_SYSTEM_LIBCLANG=ON"
      ;;
    --omnisharp-completer)
      omnisharp_completer=true
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

check_third_party_libs

if ! command_exists cmake; then
  echo "CMake is required to build YouCompleteMe."
  cmake_install
fi

if [ -z "$YCM_TESTRUN" ]; then
  install $cmake_args $EXTRA_CMAKE_ARGS
else
  testrun $cmake_args $EXTRA_CMAKE_ARGS
fi

if $omnisharp_completer; then
  buildcommand="msbuild"
  if ! command_exists msbuild; then
    buildcommand="msbuild.exe"
    if ! command_exists msbuild.exe; then
      buildcommand="xbuild"
      if ! command_exists xbuild; then
        echo "msbuild or xbuild is required to build Omnisharp"
        exit 1
      fi
    fi
  fi

  ycm_dir=`pwd`
  build_dir=$ycm_dir"/python/ycm/completers/cs/OmniSharpServer"

  cd $build_dir
  $buildcommand
  cd $ycm_dir
fi
