#!/usr/bin/env python
#
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

import os

# Given an iterable object that produces strings (flags for Clang), removes the
# '-c' and '-o' options that Clang does not like to see when it's producing
# completions for a file.
def PrepareClangFlags( flags, filename ):
  new_flags = []
  skip = True
  for flag in flags:
    if skip:
      skip = False
      continue

    if flag == '-c':
      skip = True;
      continue

    if flag == '-o':
      skip = True;
      continue

    if flag == filename or os.path.realpath(flag) == filename:
      continue

    new_flags.append( flag )
  return new_flags
