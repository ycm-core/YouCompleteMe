# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

# The interesting parts of Boost have been extracted using
# the BCP tool:
#   http://www.boost.org/doc/libs/1_52_0/tools/bcp/doc/html/index.html
#
# bcp call: bcp boost/utility.hpp boost/python.hpp boost/bind.hpp boost/lambda/lambda.hpp boost/exception/all.hpp boost/tuple/tuple_io.hpp boost/tuple/tuple_comparison.hpp boost/regex.hpp boost/foreach.hpp boost/smart_ptr.hpp boost/algorithm/string_regex.hpp boost/thread.hpp boost/unordered_map.hpp boost/unordered_set.hpp boost/format.hpp boost/ptr_container/ptr_container.hpp boost/filesystem.hpp boost/filesystem/fstream.hpp boost/utility.hpp ../BoostParts

# WARNING: When doing this from fresh boost sources, note that in the file
# /boost/config/user.hpp the BOOST_ALL_NO_LIB define has been uncommented.
# Otherwise, we will get linker errors on MSVC because of boost auto-linking. If
# you don't care about Windows then feel free to use the raw boost version of
# /boost/config/user.hpp

cmake_minimum_required( VERSION 2.8 )

project( BoostParts )

set( Python_ADDITIONAL_VERSIONS 2.7 2.6 2.5 )
find_package( PythonLibs 2.5 REQUIRED )

if ( NOT PYTHONLIBS_VERSION_STRING VERSION_LESS "3.0.0" )
  message( FATAL_ERROR
    "CMake found python3 libs instead of python2 libs. YCM works only with "
    "python2.\n" )
endif()

file( GLOB_RECURSE SOURCES *.cpp )

# We need to remove all the thread cpp files and then add them on a per-platform
# basis
file( GLOB_RECURSE to_remove libs/thread/*.cpp libs/detail/*.cpp )

if( to_remove )
  list( REMOVE_ITEM SOURCES ${to_remove} )
endif()

set( COMMON_SOURCES
    libs/thread/src/future.cpp
    )

set( WIN_SOURCES
    libs/thread/src/win32/thread.cpp
    libs/thread/src/win32/timeconv.inl
    libs/thread/src/win32/tss_dll.cpp
    libs/thread/src/win32/tss_pe.cpp
    )

set( UNIX_SOURCES
    libs/thread/src/pthread/once.cpp
    libs/thread/src/pthread/thread.cpp
    libs/thread/src/pthread/timeconv.inl
    )

list( APPEND SOURCES ${COMMON_SOURCES} )

if ( WIN32 )
    list( APPEND SOURCES ${WIN_SOURCES} )
else()
    list( APPEND SOURCES ${UNIX_SOURCES} )
endif()

#############################################################################

if( MSVC )
  # BOOST_PYTHON_SOURCE makes boost use the correct __declspec and
  # BOOST_ALL_NO_LIB turns off MSVC library autolinking
  add_definitions( -DBOOST_PYTHON_SOURCE -DBOOST_ALL_NO_LIB )
endif()

#############################################################################

include_directories(
  SYSTEM
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${PYTHON_INCLUDE_DIRS}
  )

add_library( BoostParts ${SOURCES} )

#############################################################################

if( CMAKE_COMPILER_IS_GNUCXX OR COMPILER_IS_CLANG )
  # No warnings. We just use Boost as is so warnings coming from it are just
  # noise.
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w")
endif()

#############################################################################

# Linking fails without this
if( NOT WIN32 AND CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64" )
  set_target_properties( BoostParts PROPERTIES COMPILE_FLAGS "-fPIC")
endif()

#############################################################################

# Special compiler and linker flags for MSVC
if( MSVC )
    add_definitions( /DUNICODE /D_UNICODE /Zc:wchar_t-  )
    set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP" )
    set( CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /Oi /GL" )
    set_target_properties( ${PROJECT_NAME} PROPERTIES STATIC_LIBRARY_FLAGS "/LTCG" )
endif()
