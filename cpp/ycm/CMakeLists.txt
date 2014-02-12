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

project( ycm_support_libs )
set( CLIENT_LIB "ycm_client_support" )
set( SERVER_LIB "ycm_core" )

set( Python_ADDITIONAL_VERSIONS 2.7 2.6 )
find_package( PythonLibs 2.6 REQUIRED )

if ( NOT PYTHONLIBS_VERSION_STRING VERSION_LESS "3.0.0" )
  message( FATAL_ERROR
    "CMake found python3 libs instead of python2 libs. YCM works only with "
    "python2.\n" )
endif()

option( USE_DEV_FLAGS "Use compilation flags meant for YCM developers" OFF )
option( USE_CLANG_COMPLETER "Use Clang semantic completer for C/C++/ObjC" OFF )
option( USE_SYSTEM_LIBCLANG "Set to ON to use the system libclang library" OFF )
set( PATH_TO_LLVM_ROOT "" CACHE PATH "Path to the root of a LLVM+Clang binary distribution" )
set( EXTERNAL_LIBCLANG_PATH "" CACHE PATH "Path to the libclang library to use" )

if ( USE_CLANG_COMPLETER AND
     NOT USE_SYSTEM_LIBCLANG AND
     NOT PATH_TO_LLVM_ROOT AND
     NOT EXTERNAL_LIBCLANG_PATH )
  message( "Downloading Clang 3.4" )

  set( CLANG_URL "http://llvm.org/releases/3.4" )

  if ( APPLE )
    set( CLANG_DIRNAME "clang+llvm-3.4-x86_64-apple-darwin10.9" )
    set( CLANG_MD5 "4f43ea0e87090ae5e7bec12373ca4927" )
    set( CLANG_FILENAME "${CLANG_DIRNAME}.tar.gz" )
  else()
    if ( 64_BIT_PLATFORM )
      set( CLANG_DIRNAME "clang+llvm-3.4-x86_64-unknown-ubuntu12.04" )
      set( CLANG_MD5 "6077459d20a7ff412eefc6ce3b9f5c85" )
      set( CLANG_FILENAME "${CLANG_DIRNAME}.tar.xz" )
    else()
      message( "No pre-built Clang 3.4 binaries for 32 bit linux, "
               "downloading Clang 3.3" )
      set( CLANG_URL "http://llvm.org/releases/3.3" )
      set( CLANG_DIRNAME "clang+llvm-3.3-i386-debian6" )
      set( CLANG_MD5 "415d033b60659433d4631df894673802" )
      set( CLANG_FILENAME "${CLANG_DIRNAME}.tar.bz2" )
    endif()
  endif()

  file(
    DOWNLOAD "${CLANG_URL}/${CLANG_FILENAME}" "./${CLANG_FILENAME}"
    SHOW_PROGRESS EXPECTED_MD5 "${CLANG_MD5}"
  )

  if ( CLANG_FILENAME MATCHES ".+bz2" )
    execute_process( COMMAND tar -xjf ${CLANG_FILENAME} )
  elseif( CLANG_FILENAME MATCHES ".+xz" )
    execute_process( COMMAND tar -xJf ${CLANG_FILENAME} )
  else()
    execute_process( COMMAND tar -xzf ${CLANG_FILENAME} )
  endif()

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
  if ( MINGW )
    set( LIBCLANG_SEARCH_PATH "${PATH_TO_LLVM_ROOT}/bin" )
  else()
    set( LIBCLANG_SEARCH_PATH "${PATH_TO_LLVM_ROOT}/lib" )
  endif()

  # Need TEMP because find_library does not work with an option variable
  find_library( TEMP NAMES clang libclang
                PATHS ${LIBCLANG_SEARCH_PATH}
                NO_DEFAULT_PATH )
  set( EXTERNAL_LIBCLANG_PATH ${TEMP} )
endif()

# This is a workaround for a CMake bug with include_directories(SYSTEM ...)
# on Mac OS X. Bug report: http://public.kitware.com/Bug/view.php?id=10837
if ( APPLE )
  set( CMAKE_INCLUDE_SYSTEM_FLAG_CXX "-isystem " )
endif()

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

file( GLOB_RECURSE SERVER_SOURCES *.h *.cpp )

# The test sources are a part of a different target, so we remove them
# The CMakeFiles cpp file is picked up when the user creates an in-source build,
# and we don't want that. We also remove client-specific code
file( GLOB_RECURSE to_remove tests/*.h tests/*.cpp CMakeFiles/*.cpp *client* )

if( to_remove )
  list( REMOVE_ITEM SERVER_SOURCES ${to_remove} )
endif()

if ( USE_CLANG_COMPLETER )
  include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    "${CMAKE_CURRENT_SOURCE_DIR}/ClangCompleter" )
  add_definitions( -DUSE_CLANG_COMPLETER )
else()
  file( GLOB_RECURSE to_remove_clang ClangCompleter/*.h ClangCompleter/*.cpp )

  if( to_remove_clang )
    list( REMOVE_ITEM SERVER_SOURCES ${to_remove_clang} )
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
    # On Debian-based systems, llvm installs into /usr/lib/llvm-x.y.
    file( GLOB SYS_LLVM_PATHS "/usr/lib/llvm*/lib" )
    # Need TEMP because find_library does not work with an option variable
    find_library( TEMP clang
                  PATHS
                  ${ENV_LIB_PATHS}
                  /usr/lib
                  /usr/lib/llvm
                  ${SYS_LLVM_PATHS}
                  /Library/Developer/CommandLineTools/usr/lib,
                  /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib )
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

# We don't actually need all of the files this picks up, just the ones needed by
# PythonSupport.cpp. But this is easier to maintain and dead code elemination
# will remove unused code.
file( GLOB CLIENT_SOURCES *.h *.cpp )
file( GLOB SERVER_SPECIFIC *ycm_core* )

if( SERVER_SPECIFIC )
  list( REMOVE_ITEM CLIENT_SOURCES ${SERVER_SPECIFIC} )
endif()

add_library( ${CLIENT_LIB} SHARED
             ${CLIENT_SOURCES}
           )

target_link_libraries( ${CLIENT_LIB}
                       BoostParts
                       ${PYTHON_LIBRARIES}
                       ${EXTRA_LIBS}
                     )

#############################################################################

add_library( ${SERVER_LIB} SHARED
             ${SERVER_SOURCES}
           )

target_link_libraries( ${SERVER_LIB}
                       BoostParts
                       ${PYTHON_LIBRARIES}
                       ${LIBCLANG_TARGET}
                       ${EXTRA_LIBS}
                     )

if( LIBCLANG_TARGET )
  if( NOT WIN32 )
    add_custom_command(
      TARGET ${SERVER_LIB}
      POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy "${LIBCLANG_TARGET}" "$<TARGET_FILE_DIR:${SERVER_LIB}>"
    )
  else()
    add_custom_command(
      TARGET ${SERVER_LIB}
      POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy "${PATH_TO_LLVM_ROOT}/bin/libclang.dll" "$<TARGET_FILE_DIR:${SERVER_LIB}>")
  endif()
endif()

#############################################################################

# Convenience target that builds both support libs.
add_custom_target( ${PROJECT_NAME}
                   DEPENDS ${CLIENT_LIB} ${SERVER_LIB} )


#############################################################################

# Things are a bit different on Macs when using an external libclang.dylib; here
# we want to make sure we use @loader_path/libclang.dylib instead of
# @rpath/libclang.dylib in the final ycm_core.so. If we use the
# @rpath version, then it may load the system libclang which the user
# explicitely does not want (otherwise the user would specify
# USE_SYSTEM_LIBCLANG). With @loader_path, we make sure that only the
# libclang.dylib present in the same directory as our ycm_core.so
# is used.
if ( EXTERNAL_LIBCLANG_PATH AND APPLE )
  add_custom_command( TARGET ${SERVER_LIB}
                      POST_BUILD
                      COMMAND install_name_tool
                      "-change"
                      "@rpath/libclang.dylib"
                      "@loader_path/libclang.dylib"
                      "$<TARGET_FILE:${SERVER_LIB}>"
                    )
endif()


#############################################################################

# We don't want the "lib" prefix, it can screw up python when it tries to search
# for our module
set_target_properties( ${CLIENT_LIB} PROPERTIES PREFIX "")
set_target_properties( ${SERVER_LIB} PROPERTIES PREFIX "")

if ( WIN32 OR CYGWIN )
  # DLL platforms put dlls in the RUNTIME_OUTPUT_DIRECTORY
  set_target_properties( ${CLIENT_LIB} PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../../python )
  set_target_properties( ${SERVER_LIB} PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../../python )

  if ( WIN32 )
    # This is the extension for compiled Python modules on Windows
    set_target_properties( ${CLIENT_LIB} PROPERTIES SUFFIX ".pyd")
    set_target_properties( ${SERVER_LIB} PROPERTIES SUFFIX ".pyd")
  elseif ( CYGWIN )
    # This is the extension for compiled Python modules in Cygwin
    set_target_properties( ${CLIENT_LIB} PROPERTIES SUFFIX ".dll")
    set_target_properties( ${SERVER_LIB} PROPERTIES SUFFIX ".dll")
  endif()
else()
  # Even on macs, we want a .so extension instead of a .dylib which is what
  # cmake would give us by default. Python won't recognize a .dylib as a module,
  # but it will recognize a .so
  set_target_properties( ${CLIENT_LIB} PROPERTIES SUFFIX ".so")
  set_target_properties( ${SERVER_LIB} PROPERTIES SUFFIX ".so")
endif()

set_target_properties( ${CLIENT_LIB} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../../python )
set_target_properties( ${SERVER_LIB} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../../python )

#############################################################################


# For some reason, Xcode is too dumb to understand the -isystem flag and thus
# borks on warnings in Boost.
if ( USE_DEV_FLAGS AND ( CMAKE_COMPILER_IS_GNUCXX OR COMPILER_IS_CLANG ) AND
     NOT CMAKE_GENERATOR_IS_XCODE )
  # We want all warnings, and warnings should be treated as errors
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror" )
endif()

#############################################################################

# We want warnings if we accidentally use C++11 features
# We can't use this warning on FreeBSD because std headers on that OS are dumb.
# See here: https://github.com/Valloric/YouCompleteMe/issues/260
if ( USE_DEV_FLAGS AND COMPILER_IS_CLANG AND NOT CMAKE_GENERATOR_IS_XCODE AND
     NOT SYSTEM_IS_FREEBSD )
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wc++98-compat" )
endif()

#############################################################################

if( SYSTEM_IS_SUNOS )
  # SunOS needs this setting for thread support
  set( CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthreads" )
endif()

add_subdirectory( tests )
