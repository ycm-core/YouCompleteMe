#!/usr/bin/env python
#
# Copyright (C) 2015 YouCompleteMe contributors.
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
import sys
import vim
import functools
from ycmd import utils

DIR_OF_CURRENT_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )

WIN_PYTHON_PATH = os.path.join( sys.exec_prefix, 'python.exe' )


def Memoize( obj ):
  cache = obj.cache = {}

  @functools.wraps( obj )
  def memoizer( *args, **kwargs ):
    key = str( args ) + str( kwargs )
    if key not in cache:
      cache[ key ] = obj( *args, **kwargs )
    return cache[ key ]
  return memoizer


@Memoize
def PathToPythonInterpreter():
  python_interpreter = vim.eval( 'g:ycm_path_to_python_interpreter' )

  if python_interpreter:
    if not CheckPythonVersion( python_interpreter ):
      raise RuntimeError( "Path in 'g:ycm_path_to_python_interpreter' option "
                          "does not point to a valid Python 2.6 or 2.7." )

    return python_interpreter

  # On UNIX platforms, we use sys.executable as the Python interpreter path.
  # We cannot use sys.executable on Windows because for unknown reasons, it
  # returns the Vim executable. Instead, we use sys.exec_prefix to deduce the
  # interpreter path.
  python_interpreter = ( WIN_PYTHON_PATH if utils.OnWindows() else
                         sys.executable )

  if not CheckPythonVersion( python_interpreter ):
    raise RuntimeError( "Cannot find Python 2.6 or 2.7. You can set its path "
                        "using the 'g:ycm_path_to_python_interpreter' "
                        "option." )

  return python_interpreter


def CheckPythonVersion( python_interpreter ):
  """Check if given path is the Python interpreter version 2.6 or 2.7."""
  command = [ python_interpreter,
              '-c',
              "import sys;"
              "major, minor = sys.version_info[ :2 ];"
              "sys.exit( major != 2 or minor < 6)" ]

  return utils.SafePopen( command ).wait() == 0


def PathToServerScript():
  return os.path.join( DIR_OF_CURRENT_SCRIPT, '..', '..', 'third_party',
                       'ycmd', 'ycmd' )


def PathToCheckCoreVersion():
  return os.path.join( DIR_OF_CURRENT_SCRIPT, '..', '..', 'third_party',
                       'ycmd', 'check_core_version.py' )
