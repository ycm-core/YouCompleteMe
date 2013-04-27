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

set( Python_ADDITIONAL_VERSIONS 2.7 2.6 2.5 )
find_package( PythonLibs 2.5 REQUIRED )

if ( NOT PYTHONLIBS_VERSION_STRING VERSION_LESS "3.0.0" )
  message( FATAL_ERROR
    "CMake found python3 libs instead of python2 libs. YCM works only with "
    "python2.\n" )
endif()

option( USE_CLANG_COMPLETER "Use Clang semantic completer for C/C++/ObjC" OFF )
option( PATH_TO_LLVM_ROOT "Path to the root of a LLVM+Clang binary distribution" )
option( USE_SYSTEM_LIBCLANG "Set to ON to use the system libclang library" OFF )
option( EXTERNAL_LIBCLANG_PATH "Path libclang library to use" )

if ( USE_CLANG_COMPLETER AND NOT USE_SYSTEM_LIBCLANG AND NOT PATH_TO_LLVM_ROOT )
  message( "Downloading Clang 3.2" )

  set( CLANG_URL "http://llvm.org/releases/3.2" )

  if ( APPLE )
    set( CLANG_DIRNAME "clang+llvm-3.2-x86_64-apple-darwin11" )
    set( CLANG_MD5 "fbdca3b4e8cdaa2352f2aeb038a16532" )
  else()
    if ( 64_BIT_PLATFORM )
      set( CLANG_DIRNAME "clang+llvm-3.2-x86_64-linux-ubuntu-12.04" )
      set( CLANG_MD5 "81821e339d7300afb76aca8edab2cf4f" )
    else()
      set( CLANG_DIRNAME "clang+llvm-3.2-x86-linux-ubuntu-12.04" )
      set( CLANG_MD5 "cea2d01b3206e92a8df7b079935c070b" )
    endif()
  endif()

  set( CLANG_FILENAME "${CLANG_DIRNAME}.tar.gz" )

  file(
    DOWNLOAD "${CLANG_URL}/${CLANG_FILENAME}" "./${CLANG_FILENAME}"
    SHOW_PROGRESS EXPECTED_MD5 "${CLANG_MD5}"
  )

  execute_process( COMMAND tar -xzf ${CLANG_FILENAME} )

  # And set PATH_TO_LLVM_ROOT
  set( PATH_TO_LLVM_ROOT "${CMAKE_CURRENT_BINARY_DIR}/../${CLANG_DIRNAME}" )
endif()

if ( PATH_TO_LLVM_ROOT OR USE_SYSTEM_LIBCLANG OR EXTERNAL_LIBCLANG_PATH )
  set( USE_CLANG_COMPLETER TRUE )
endif()

if ( USE_CLANG_COMPLETER AND
     NOT PATH_TO_LLVM_ROOT AND
     NOT USE_SYSTEM_LIBCLANG AND
     NOT EXTERNAL_LIBCLANG_PATH )
  message( FATAL_ERROR
    "You have not specified which libclang to use. You have several options:\n"
    " 1. Set PATH_TO_LLVM_ROOT to a path to the root of a LLVM+Clang binary "
    "distribution. You can download such a binary distro from llvm.org. This "
    "is the recommended approach.\n"
    " 2. Set USE_SYSTEM_LIBCLANG to ON; this makes YCM search for the system "
    "version of libclang.\n"
    " 3. Set EXTERNAL_LIBCLANG_PATH to a path to whatever "
    "libclang.[so|dylib|dll] you wish to use.\n"
    "You HAVE to pick one option. See the docs for more information.")
endif()

if ( USE_CLANG_COMPLETER )
  message( "Using libclang to provide semantic completion for C/C++/ObjC" )
else()
  message( "NOT using libclang, no semantic completion for C/C++/ObjC will be "
           "available" )
endif()

if ( PATH_TO_LLVM_ROOT )
  set( CLANG_INCLUDES_DIR "${PATH_TO_LLVM_ROOT}/include" )
else()
  set( CLANG_INCLUDES_DIR "${CMAKE_SOURCE_DIR}/llvm/include" )
endif()

if ( NOT IS_ABSOLUTE "${CLANG_INCLUDES_DIR}" )
  get_filename_component(CLANG_INCLUDES_DIR
    "${CMAKE_BINARY_DIR}/${CLANG_INCLUDES_DIR}" ABSOLUTE)
endif()

if ( NOT EXTERNAL_LIBCLANG_PATH AND PATH_TO_LLVM_ROOT )
  # Need TEMP because find_library does not work with an option variable
  find_library( TEMP clang
                PATHS ${PATH_TO_LLVM_ROOT}/lib
                NO_DEFAULT_PATH )
  set( EXTERNAL_LIBCLANG_PATH ${TEMP} )
endif()

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
  ${CLANG_INCLUDES_DIR}
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

if ( EXTERNAL_LIBCLANG_PATH OR USE_SYSTEM_LIBCLANG )
  if ( USE_SYSTEM_LIBCLANG )
    if ( APPLE )
      set( ENV_LIB_PATHS ENV DYLD_LIBRARY_PATH )
    elseif ( UNIX )
      set( ENV_LIB_PATHS ENV LD_LIBRARY_PATH )
    elseif ( WIN32 )
      set( ENV_LIB_PATHS ENV PATH )
    else ()
      set( ENV_LIB_PATHS "" )
    endif()
    # Need TEMP because find_library does not work with an option variable
    find_library( TEMP clang
                  PATHS
                  ${ENV_LIB_PATHS}
                  /usr/lib
                  /usr/lib/llvm )
    set( EXTERNAL_LIBCLANG_PATH ${TEMP} )
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
else()
  set( LIBCLANG_TARGET )
endif()

if ( EXTRA_RPATH )
  set( CMAKE_INSTALL_RPATH "${EXTRA_RPATH}:${CMAKE_INSTALL_RPATH}" )
endif()

# Needed on Linux machines, but not on Macs
if ( UNIX AND NOT APPLE )
  set( EXTRA_LIBS rt )
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

if( MSVC OR CYGWIN )
  # BOOST_PYTHON_SOURCE makes boost use the correct __declspec and
  # BOOST_ALL_NO_LIB turns off MSVC library autolinking
  add_definitions( -DBOOST_PYTHON_SOURCE -DBOOST_ALL_NO_LIB )
endif()
#############################################################################

add_library( ${PROJECT_NAME} SHARED
             ${SOURCES}
           )

target_link_libraries( ${PROJECT_NAME}
                       BoostParts
                       ${PYTHON_LIBRARIES}
                       ${LIBCLANG_TARGET}
                       ${EXTRA_LIBS}
                     )

if ( LIBCLANG_TARGET )
  add_custom_command(
    TARGET ${PROJECT_NAME}
    POST_BUILD
    COMMAND cp "${LIBCLANG_TARGET}" "$<TARGET_FILE_DIR:${PROJECT_NAME}>"
  )
endif()

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

if ( WIN32 OR CYGWIN )
  # This is the extension for compiled Python modules on Windows
  set_target_properties( ${PROJECT_NAME} PROPERTIES SUFFIX ".pyd")
else()
  # Even on macs, we want a .so extension instead of a .dylib which is what
  # cmake would give us by default. Python won't recognize a .dylib as a module,
  # but it will recognize a .so
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
# We can't use this warning on FreeBSD because std headers on that OS are dumb.
# See here: https://github.com/Valloric/YouCompleteMe/issues/260
if ( COMPILER_IS_CLANG AND NOT CMAKE_GENERATOR_IS_XCODE AND NOT
     SYSTEM_IS_FREEBSD )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wc++98-compat" )
endif()

#############################################################################

add_subdirectory( tests )
