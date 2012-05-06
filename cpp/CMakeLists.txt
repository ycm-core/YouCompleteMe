# Copyright (C) 2011  Strahinja Markovic  <strahinja.markovic@gmail.com>
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

project( indexer )
cmake_minimum_required( VERSION 2.8 )

# This is needed so that on macs, the library is built in both 32 bit and 64 bit
# versions. Without this python might refuse to load the module, depending on
# how python was built.
# On Mac, boost needs to be compiled universal as well. For brew, that's
# "brew install boost --universal"
set( CMAKE_OSX_ARCHITECTURES "i386;x86_64" )

# Force release build, speed is of the essence
if( NOT CMAKE_BUILD_TYPE )
  set( CMAKE_BUILD_TYPE RELEASE )
endif()

find_package( Boost COMPONENTS
                system
                thread
                python
              REQUIRED)

find_package( PythonLibs REQUIRED )

include_directories(
  ${Boost_INCLUDE_DIRS}
  ${PYTHON_INCLUDE_DIRS}
  )

link_directories(
  ${Boost_LIBRARY_DIRS}
  ${PYTHON_LIBRARIES}
  )

file( GLOB_RECURSE SOURCES *.h *.cpp )

# The test sources are a part of a different target, so we remove them
# The CMakeFiles cpp file is picked up when the user creates an in-source build,
# and we don't want that.
file( GLOB_RECURSE to_remove tests/*.h tests/*.cpp CMakeFiles/*.cpp )
if( to_remove )
  list( REMOVE_ITEM SOURCES ${to_remove} )
endif()

add_library( ${PROJECT_NAME} SHARED
             ${SOURCES}
           )

target_link_libraries( ${PROJECT_NAME}
                       ${Boost_LIBRARIES}
                       ${PYTHON_LIBRARIES}
                       # gtest
                     )

set_target_properties( ${PROJECT_NAME} PROPERTIES PREFIX "")

# Even on macs, we want a .so extension instead of a .dylib which is what cmake
# would give us by default. Python won't recognize a .dylib as a module, but it
# will recognize a .so
if ( NOT WIN32 )
  set_target_properties( ${PROJECT_NAME} PROPERTIES SUFFIX ".so")
endif()

set_target_properties( ${PROJECT_NAME} PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/../python)

if ( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" )
  set( COMPILER_IS_CLANG true )
endif()

if( CMAKE_COMPILER_IS_GNUCXX OR COMPILER_IS_CLANG )
  # We want all warnings, and warnings should be treated as errors
	# TODO: -Wextra?
  add_definitions( -Wall -Werror )
endif()

add_subdirectory( tests )
