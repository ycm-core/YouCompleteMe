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

project( indexer_tests )
cmake_minimum_required( VERSION 2.8 )

# The gtest library triggers these silly warnings, so we turn them off
if ( COMPILER_IS_CLANG )
  add_definitions( -Wno-long-long -Wno-variadic-macros )
endif()

add_subdirectory( gmock )

include_directories(
  ${indexer_SOURCE_DIR}
  )

include_directories(
  SYSTEM
  ${gtest_SOURCE_DIR}
  ${gtest_SOURCE_DIR}/include
  ${gmock_SOURCE_DIR}
  ${gmock_SOURCE_DIR}/include
  )

link_directories(
  ${Boost_LIBRARY_DIRS}
  ${PYTHON_LIBRARIES}
  )

file( GLOB SOURCES *.h *.cpp )

add_executable( ${PROJECT_NAME}
                ${SOURCES}
              )

target_link_libraries( ${PROJECT_NAME}
                       indexer
                       gmock_main
                     )

