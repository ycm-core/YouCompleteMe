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

project( indexer )

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
  )

file( GLOB_RECURSE SOURCES *.h *.cpp )

# The test sources are a part of a different target, so we remove them
# The CMakeFiles cpp file is picked up when the user creates an in-source build,
# and we don't want that.
file( GLOB_RECURSE to_remove tests/*.h tests/*.cpp CMakeFiles/*.cpp )

if( to_remove )
  list( REMOVE_ITEM SOURCES ${to_remove} )
endif()

#############################################################################

add_library( ${PROJECT_NAME} SHARED
             ${SOURCES}
           )

target_link_libraries( ${PROJECT_NAME}
                       BoostParts
                       ${PYTHON_LIBRARIES}
                     )

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
  add_definitions( -Wall -Wextra -Werror )
endif()

#############################################################################

add_subdirectory( tests )
