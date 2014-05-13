#!/usr/bin/env python
#
# Copyright (C) 2013  Google Inc.
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

import sys
import os

def SetUpPythonPath():
  # We want to have the YouCompleteMe/python directory on the Python PATH
  # because all the code already assumes that it's there. This is a relic from
  # before the client/server architecture.
  # TODO: Fix things so that this is not needed anymore when we split ycmd into
  # a separate repository.
  sys.path.insert( 0, os.path.join(
                          os.path.dirname( os.path.abspath( __file__ ) ),
                          '../..' ) )

  from ycm import utils
  utils.AddThirdPartyFoldersToSysPath()
