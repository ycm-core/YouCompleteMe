#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Stephen Sugden <me@stephensugden.com>
#                           Strahinja Val Markovic <val@markovic.io>
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

import vim
from completers.threaded_completer import ThreadedCompleter
import vimsupport

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompletMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert( 0, join( abspath( dirname( __file__ ) ), 'jedi' ) )
try:
  from jedi import Script
except ImportError:
  vimsupport.PostVimMessage(
    'Error importing jedi. Make sure the jedi submodule has been checked out. '
    'In the YouCompleteMe folder, run "git submodule update --init --recursive"')
sys.path.pop( 0 )


class JediCompleter( ThreadedCompleter ):
  """
  A Completer that uses the Jedi completion engine.
  https://jedi.readthedocs.org/en/latest/
  """

  def __init__( self ):
    super( JediCompleter, self ).__init__()


  def SupportedFiletypes( self ):
    """ Just python """
    return [ 'python' ]


  def ComputeCandidates( self, unused_query, unused_start_column ):
    filename = vim.current.buffer.name
    line, column = vimsupport.CurrentLineAndColumn()
    # Jedi expects lines to start at 1, not 0
    line += 1
    contents = '\n'.join( vim.current.buffer )
    script = Script( contents, line, column, filename )

    return [ { 'word': str( completion.word ),
               'menu': str( completion.description ),
               'info': str( completion.doc ) }
             for completion in script.complete() ]


