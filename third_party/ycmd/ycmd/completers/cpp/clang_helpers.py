#!/usr/bin/env python
#
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


def PrepareClangFlags( flags, filename ):
  # When flags come from the compile_commands.json file, the first flag is
  # usually the path to the compiler that should be invoked. We want to strip
  # that.
  if flags and not flags[ 0 ].startswith( '-' ):
    return flags[ 1: ]
  return flags
