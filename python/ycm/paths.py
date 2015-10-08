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
import vim
import functools
from ycmd import utils

DIR_OF_CURRENT_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )

WIN_PYTHON27_PATH = 'C:\python27\python.exe'
WIN_PYTHON26_PATH = 'C:\python26\python.exe'


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
  user_path_to_python = vim.eval( 'g:ycm_path_to_python_interpreter' )

  if user_path_to_python:
    return user_path_to_python

  # We check for 'python2' before 'python' because some OS's (I'm looking at
  # you Arch Linux) have made the... interesting decision to point
  # /usr/bin/python to python3.
  python_names = [ 'python2', 'python' ]

  path_to_python = utils.PathToFirstExistingExecutable( python_names )
  if path_to_python:
    return path_to_python

  # On Windows, Python may not be on the PATH at all, so we check some common
  # install locations.
  if utils.OnWindows():
    if os.path.exists( WIN_PYTHON27_PATH ):
      return WIN_PYTHON27_PATH
    elif os.path.exists( WIN_PYTHON26_PATH ):
      return WIN_PYTHON26_PATH

  raise RuntimeError( 'Python 2.7/2.6 not installed!' )


def PathToServerScript():
  return os.path.join( DIR_OF_CURRENT_SCRIPT, '..', '..', 'third_party',
                       'ycmd', 'ycmd' )


def PathToCheckCoreVersion():
  return os.path.join( DIR_OF_CURRENT_SCRIPT, '..', '..', 'third_party',
                       'ycmd', 'check_core_version.py' )
