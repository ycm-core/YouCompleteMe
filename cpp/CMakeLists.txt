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

cmake_minimum_required( VERSION 2.8 )
project( YouCompleteMe )

# This is needed so that on macs, the library is built in both 32 bit and 64 bit
# versions. Without this python might refuse to load the module, depending on
# how python was built.
# On Mac, boost needs to be compiled universal as well, if used instead of the
# included BoostParts lib. For brew, that's
# "brew install boost --universal"
set( CMAKE_OSX_ARCHITECTURES "i386;x86_64" )

if ( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" )
  set( COMPILER_IS_CLANG true )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++" )
endif()

# Force release build by default, speed is of the essence
if ( NOT CMAKE_BUILD_TYPE )
  set( CMAKE_BUILD_TYPE Release )
endif()

# Determining the presence of C++11 support in the compiler
set( CPP11_AVAILABLE false )
if ( CMAKE_COMPILER_IS_GNUCXX )
  execute_process(
    COMMAND ${CMAKE_CXX_COMPILER} -dumpversion OUTPUT_VARIABLE GCC_VERSION)
  if ( GCC_VERSION VERSION_GREATER 4.6 OR GCC_VERSION VERSION_EQUAL 4.6 )
    set( CPP11_AVAILABLE true )
  endif()
elseif( COMPILER_IS_CLANG )
  set( CPP11_AVAILABLE true )
endif()

# When used with Clang, adding the -std=c++0x flag to CMAKE_CXX_FLAGS will cause
# the compiler to output a warning during linking:
#  clang: warning: argument unused during compilation: '-std=c++0x'
# This is caused by cmake passing this flag to the linking stage which it
# shouldn't do. It's ignored so it does no harm, but the warning is annoying and
# there's no way around the problem (the flag is correctly used during the
# compilation stage). We could use add_definitions(-std=c++0x), but this will
# break the llvm build since the flag will then be used when compiling C code
# too. Sadly there's no way around the warning.
if ( CPP11_AVAILABLE )
  message( "Your C++ compiler supports C++11, compiling in that mode." )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x" )
else()
  message(
    "Your C++ compiler does NOT support C++11, compiling in C++03 mode." )
endif()

add_subdirectory( llvm )
add_subdirectory( BoostParts )
add_subdirectory( ycm )
