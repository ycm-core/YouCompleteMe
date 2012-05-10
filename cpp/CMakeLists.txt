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

if ( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" )
  set( COMPILER_IS_CLANG true )
endif()

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

add_subdirectory( BoostParts )
add_subdirectory( ycm )
