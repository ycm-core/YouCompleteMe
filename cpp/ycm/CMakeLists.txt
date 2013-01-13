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

project( ycm_core )

find_package( PythonLibs REQUIRED )

# This is a workaround for a CMake bug with include_directories(SYSTEM ...)
# on Mac OS X. Bug report: http://public.kitware.com/Bug/view.php?id=10837
set( CMAKE_INCLUDE_SYSTEM_FLAG_CXX "-isystem " )

# The SYSTEM flag makes sure that -isystem[header path] is passed to the
# compiler instead of the standard -I[header path]. Headers included with
# -isystem do not generate warnings (and they shouldn't; e.g. boost warnings are
# just noise for us since we won't be changing them).
include_directories(
  SYSTEM
  ${BoostParts_SOURCE_DIR}
  ${PYTHON_INCLUDE_DIRS}
  # We need CMAKE_SOURCE_DIR here instead of LLVM_SOURCE_DIR because the llvm
  # subdir may not have been included in the build
  "${CMAKE_SOURCE_DIR}/llvm/include"
  "${CMAKE_SOURCE_DIR}/llvm/tools/clang/include"
  )

file( GLOB_RECURSE SOURCES *.h *.cpp )

# The test sources are a part of a different target, so we remove them
# The CMakeFiles cpp file is picked up when the user creates an in-source build,
# and we don't want that.
file( GLOB_RECURSE to_remove tests/*.h tests/*.cpp CMakeFiles/*.cpp )

if( to_remove )
  list( REMOVE_ITEM SOURCES ${to_remove} )
endif()

if ( USE_CLANG_COMPLETER )
  include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    "${CMAKE_CURRENT_SOURCE_DIR}/ClangCompleter" )
  add_definitions( -DUSE_CLANG_COMPLETER )
else()
  file( GLOB_RECURSE to_remove_clang ClangCompleter/*.h ClangCompleter/*.cpp )

  if( to_remove_clang )
    list( REMOVE_ITEM SOURCES ${to_remove_clang} )
  endif()
endif()

#############################################################################

# One can use the system libclang.[so|dylib] like so:
#   cmake -DUSE_SYSTEM_LIBCLANG=1 [...]
# One can also explicitely pick the external libclang.[so|dylib] for use like so:
#   cmake -DEXTERNAL_LIBCLANG_PATH=/path/to/libclang.so [...]
# The final .so we build will then first look in the same dir in which it is
# located for libclang.so. This is provided by the rpath = $ORIGIN feature.
# Using an external libclang is an UNDOCUMENTED and UNSUPPORTED feature! I don't
# want to hear a single bug report about it! :) (I mean it)

if ( EXTERNAL_LIBCLANG_PATH OR USE_SYSTEM_LIBCLANG )
  if ( USE_SYSTEM_LIBCLANG )
    find_library( EXTERNAL_LIBCLANG_PATH clang )
  else()
    # For Macs, we do things differently; look further in this file.
    if ( NOT APPLE )
      # Setting this to true makes sure that libraries we build will have our rpath
      # set even without having to do "make install"
      set( CMAKE_BUILD_WITH_INSTALL_RPATH TRUE )
      set( CMAKE_INSTALL_RPATH "\$ORIGIN" )
    endif()
  endif()

  set( LIBCLANG_TARGET ${EXTERNAL_LIBCLANG_PATH} )
  message(
    "Using external libclang: ${EXTERNAL_LIBCLANG_PATH}" )
elseif( USE_CLANG_COMPLETER )
  set( LIBCLANG_TARGET libclang_static )
else()
  set( LIBCLANG_TARGET )
endif()

if ( EXTRA_RPATH )
  set( CMAKE_INSTALL_RPATH "${EXTRA_RPATH}:${CMAKE_INSTALL_RPATH}" )
endif()

#############################################################################

# Due to a bug/misconfiguration/stupidity, boost 1.52 and libc++ don't like each
# other much: a compilation error "Constexpr function never produces a constant
# expression" pops up when trying to compile anything that uses
# boost/chrono/duration.hpp (namely boost/thread for us). This is a workaround
# that prevents this from happening. Also present in cpp/BoostParts/CMakeLists.txt.
# See here for more details: https://svn.boost.org/trac/boost/ticket/7671
# TODO: remove this when it's fixed upstream (probably boost 1.53).
add_definitions( -DBOOST_THREAD_DONT_USE_CHRONO )

#############################################################################

add_library( ${PROJECT_NAME} SHARED
             ${SOURCES}
           )

target_link_libraries( ${PROJECT_NAME}
                       BoostParts
                       ${PYTHON_LIBRARIES}
                       ${LIBCLANG_TARGET}
                     )

#############################################################################

# Things are a bit different on Macs when using an external libclang.dylib; here
# we want to make sure we use @loader_path/libclang.dylib instead of
# @rpath/libclang.dylib in the final ycm_core.so. If we use the @rpath version,
# then it may load the system libclang which the user explicitely does not want
# (otherwise the user would specify USE_SYSTEM_LIBCLANG). With @loader_path, we
# make sure that only the libclang.dylib present in the same directory as our
# ycm_core.so is used.
if ( EXTERNAL_LIBCLANG_PATH AND APPLE )
  add_custom_command( TARGET ${PROJECT_NAME}
                      POST_BUILD
                      COMMAND install_name_tool
                      "-change"
                      "@rpath/libclang.dylib"
                      "@loader_path/libclang.dylib"
                      "$<TARGET_FILE:${PROJECT_NAME}>"
                      )
endif()


#############################################################################

# We don't want the "lib" prefix, it can screw up python when it tries to search
# for our module
set_target_properties( ${PROJECT_NAME} PROPERTIES PREFIX "")

# Even on macs, we want a .so extension instead of a .dylib which is what cmake
# would give us by default. Python won't recognize a .dylib as a module, but it
# will recognize a .so
if ( NOT WIN32 )
  set_target_properties( ${PROJECT_NAME} PROPERTIES SUFFIX ".so")
endif()

set_target_properties( ${PROJECT_NAME} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../../python )

#############################################################################

if( CMAKE_COMPILER_IS_GNUCXX OR COMPILER_IS_CLANG )
  # We want all warnings, and warnings should be treated as errors
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror" )
endif()

#############################################################################

# We want warnings if we accidentally use C++11 features
if ( COMPILER_IS_CLANG AND NOT CMAKE_GENERATOR_IS_XCODE )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wc++98-compat" )
endif()

#############################################################################

add_subdirectory( tests )
