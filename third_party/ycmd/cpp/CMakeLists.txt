# Copyright (C) 2011, 2012  Google Inc.
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

# Disable CMake legacy mode for Cygwin, since the build doesn't depend on
# WIN32 being set for Cygwin, and this property being unset causes a
# warning in Cygwin.
# Remove when CMake >= 2.8.4 is required, since that implicitly sets this
set( CMAKE_LEGACY_CYGWIN_WIN32 0 )

project( YouCompleteMe )

option( UNIVERSAL "Build universal mac binary" OFF )

if ( CMAKE_GENERATOR STREQUAL Xcode )
  set( CMAKE_GENERATOR_IS_XCODE true )
endif()

if ( ${CMAKE_SYSTEM_NAME} MATCHES "FreeBSD" )
  set( SYSTEM_IS_FREEBSD true )
endif()

if ( ${CMAKE_SYSTEM_NAME} MATCHES "SunOS" )
  set( SYSTEM_IS_SUNOS true )
endif()

# Check if platform is 64 bit
if( CMAKE_SIZEOF_VOID_P EQUAL 4 )
  set( 64_BIT_PLATFORM 0 )
else()
  set( 64_BIT_PLATFORM 1 )
endif()

#############################################################################

# Turning on this flag tells cmake to emit a compile_commands.json file.
# This file can be used to load compilation flags into YCM. See here for more
# details: http://clang.llvm.org/docs/JSONCompilationDatabase.html
set( CMAKE_EXPORT_COMPILE_COMMANDS 1 )

#############################################################################

# This is needed so that on macs, the library is built in both 32 bit and 64 bit
# versions. Without this python might refuse to load the module, depending on
# how python was built.
# On Mac, boost needs to be compiled universal as well, if used instead of the
# included BoostParts lib. For brew, that's
# "brew install boost --universal"
# If the user chose to use the system libclang.dylib (or the libclang.dylib
# binary downloaded from llvm.org) on a mac, then we don't specify universal
# binary building since the system libclang on macs is not  universal (and thus
# linking would fail with universal).
if ( UNIVERSAL AND NOT USE_SYSTEM_LIBCLANG )
  set( CMAKE_OSX_ARCHITECTURES "i386;x86_64" )
endif()

#############################################################################

if ( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" )
  set( COMPILER_IS_CLANG true )

  # Linux machines don't necessarily have libc++ installed alongside clang,
  # but HAS_LIBCXX11 doesn't always trigger for machines that DO have libc++. We
  # know that at least all the Mac OS versions we support that use Clang have
  # libc++, so we're safe there. On FreeBSD 9 libc++ is an optional build
  # toggle. On FreeBSD 10 it is the default.
  if ( HAS_LIBCXX11 OR APPLE OR SYSTEM_IS_FREEBSD )
    set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++" )
  endif()

  # Ninja will by default prevent Clang from outputting diagnostics in color, so
  # we force color output
  if ( CMAKE_GENERATOR STREQUAL "Ninja" )
    set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fcolor-diagnostics" )
  endif()
endif()

#############################################################################

# Force release build by default, speed is of the essence
if ( NOT CMAKE_BUILD_TYPE )
  set( CMAKE_BUILD_TYPE Release )
endif()

#############################################################################

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
  set( CMAKE_XCODE_ATTRIBUTE_CLANG_CXX_LANGUAGE_STANDARD "c++11" )
  set( CMAKE_XCODE_ATTRIBUTE_CLANG_CXX_LIBRARY "libc++" )
endif()

#############################################################################

# For MSVC enable UNICODE and compilation on multiple processors
if ( MSVC )
  add_definitions( /DUNICODE /D_UNICODE /Zc:wchar_t-  )
	set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP" )
endif()

# Solves the conflict in names of hypot in python sources and boost::python
if ( MINGW )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -include cmath")
endif()

# Due to a bug/misconfiguration/stupidity, boost 1.52 and libc++ don't like each
# other much: a compilation error "Constexpr function never produces a constant
# expression" pops up when trying to compile anything that uses
# boost/chrono/duration.hpp (namely boost/thread for us). This is a workaround
# that prevents this from happening. Also present in cpp/BoostParts/CMakeLists.txt.
# See here for more details: https://svn.boost.org/trac/boost/ticket/7671
# TODO: remove this when it's fixed upstream (probably boost 1.53).
add_definitions( -DBOOST_THREAD_DONT_USE_CHRONO )

if( MSVC OR CYGWIN )
  # BOOST_ALL_NO_LIB turns off MSVC library autolinking
  add_definitions( -DBOOST_ALL_NO_LIB )
endif()

if( WIN32 OR CYGWIN )
  # BOOST_PYTHON_SOURCE makes boost use the correct __declspec
  add_definitions( -DBOOST_PYTHON_SOURCE -DBOOST_THREAD_USE_LIB )
  if ( 64_BIT_PLATFORM )
    # Enables python compilation for 64-bit Windows
    add_definitions( -DMS_WIN64 )
  endif()
endif()

#############################################################################

# When used with Clang, adding the -std=c++0x flag to CMAKE_CXX_FLAGS will cause
# the compiler to output a warning during linking:
#  clang: warning: argument unused during compilation: '-std=c++0x'
# This is caused by cmake passing this flag to the linking stage which it
# shouldn't do. It's ignored so it does no harm, but the warning is annoying.
#
# Putting the flag in add_definitions() works around the issue, even though it
# shouldn't in theory go there.
if ( CPP11_AVAILABLE )
  message( "Your C++ compiler supports C++11, compiling in that mode." )

  # Cygwin needs its hand held a bit; see issue #473
  if ( CYGWIN AND CMAKE_COMPILER_IS_GNUCXX )
    add_definitions( -std=gnu++0x )
  else()
    add_definitions( -std=c++0x )
  endif()
else()
  message(
    "Your C++ compiler does NOT support C++11, compiling in C++03 mode." )
endif()

add_subdirectory( BoostParts )
add_subdirectory( ycm )
