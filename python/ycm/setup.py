# Copyright (C) 2016 YouCompleteMe contributors
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
import paths


def SetUpSystemPaths():
  sys.path.insert( 0, os.path.join( paths.DIR_OF_YCMD ) )

  from ycmd import server_utils as su
  su.AddNearestThirdPartyFoldersToSysPath( paths.DIR_OF_CURRENT_SCRIPT )
  # We need to import ycmd's third_party folders as well since we import and
  # use ycmd code in the client.
  su.AddNearestThirdPartyFoldersToSysPath( su.__file__ )


def SetUpYCM():
  import base
  from ycmd import user_options_store, utils
  from youcompleteme import YouCompleteMe

  base.LoadJsonDefaultsIntoVim()

  user_options_store.SetAll( base.BuildServerConf() )

  popen_args = [ paths.PathToPythonInterpreter(),
                 paths.PathToCheckCoreVersion() ]

  if utils.SafePopen( popen_args ).wait() == 2:
    raise RuntimeError( 'YCM support libs too old, PLEASE RECOMPILE.' )

  return YouCompleteMe( user_options_store.GetAll() )
