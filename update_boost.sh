#!/usr/bin/env bash

# This script is used to update cpp/BoostParts to the latest boost version
# Give it the full path to the boost_1_XX_X folder

# Exit if error
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/boost_1_XX_X"
  exit 0
fi

pushd $1

./bootstrap.sh
./b2 tools/bcp

boost_part_dir=`mktemp -d -t boost_parts.XXXXXX`

dist/bin/bcp boost/utility.hpp boost/python.hpp boost/bind.hpp boost/lambda/lambda.hpp boost/exception/all.hpp boost/tuple/tuple_io.hpp boost/tuple/tuple_comparison.hpp boost/regex.hpp boost/foreach.hpp boost/smart_ptr.hpp boost/algorithm/string_regex.hpp boost/thread.hpp boost/unordered_map.hpp boost/unordered_set.hpp boost/format.hpp boost/ptr_container/ptr_container.hpp boost/filesystem.hpp boost/filesystem/fstream.hpp boost/utility.hpp boost/algorithm/cxx11/any_of.hpp atomic lockfree assign $boost_part_dir

pushd $boost_part_dir

# DON'T exit if error
set +e

find libs \( -name assign -o -name mpi -o -name config -o -name lockfree \) -exec rm -rf '{}' \;
find libs \( -name doc -o -name test -o -name examples -o -name build \) -exec rm -rf '{}' \;
find libs -not \( -name "*.hpp" -o -name "*.cpp" -o -name "*.ipp" -o -name "*.inl" \) -type f -delete

# Exit if error
set -e

popd
popd

rm -rf cpp/BoostParts/libs
rm -rf cpp/BoostParts/boost

cp -R $boost_part_dir/libs cpp/BoostParts/libs
cp -R $boost_part_dir/boost cpp/BoostParts/boost

rm -rf $boost_part_dir
