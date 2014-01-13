# Copyright (C) 2011 Google Inc.
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

project( ycm_core_tests )
cmake_minimum_required( VERSION 2.8 )

# The gtest library triggers these warnings, so we turn them off; it's not up to
# us to fix gtest warnings, it's up to upstream.
if ( COMPILER_IS_CLANG )
  set( CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -Wno-long-long -Wno-variadic-macros -Wno-missing-field-initializers -Wno-unused-private-field" )
endif()

add_subdirectory( gmock )

include_directories(
  ${ycm_support_libs_SOURCE_DIR}
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

file( GLOB_RECURSE SOURCES *.h *.cpp )

# We don't want gmock sources in this target
file( GLOB_RECURSE to_remove gmock/*.h gmock/*.cpp CMakeFiles/*.cpp
  testdata/*.cpp testdata/*.h )

if( to_remove )
  list( REMOVE_ITEM SOURCES ${to_remove} )
endif()

if ( NOT USE_CLANG_COMPLETER )
  file( GLOB_RECURSE to_remove_clang ClangCompleter/*.h ClangCompleter/*.cpp )

  if( to_remove_clang )
    list( REMOVE_ITEM SOURCES ${to_remove_clang} )
  endif()
endif()

add_executable( ${PROJECT_NAME}
                ${SOURCES}
              )

target_link_libraries( ${PROJECT_NAME}
                       ${SERVER_LIB}
                       ${CLIENT_LIB}
                       gmock )


if ( NOT CMAKE_GENERATOR_IS_XCODE )
  # The test executable expects a "testdata" dir in its working directory. Why?
  # Because there's NO reliable, cross-platform way of getting the directory in
  # which the executable is located.
  add_custom_target( copy_testdata
                    COMMAND cmake -E copy_directory
                    ${CMAKE_CURRENT_SOURCE_DIR}/testdata
                    ${CMAKE_CURRENT_BINARY_DIR}/testdata )
else()
  add_custom_target( copy_testdata
                    COMMAND cmake -E copy_directory
                    ${CMAKE_CURRENT_SOURCE_DIR}/testdata
                    ${CMAKE_CURRENT_BINARY_DIR}/Debug/testdata
                    COMMAND cmake -E copy_directory
                    ${CMAKE_CURRENT_SOURCE_DIR}/testdata
                    ${CMAKE_CURRENT_BINARY_DIR}/Release/testdata )

endif()

add_dependencies( ${PROJECT_NAME} copy_testdata )
