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

import re
import vim
from threading import Thread, Event
from completers.completer import Completer
import vimsupport

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompleteMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert( 0, join( abspath( dirname( __file__ ) ), 'jedi' ) )
try:
  from jedi import Script
except ImportError:
  vimsupport.PostVimMessage(
    'Error importing jedi. Make sure the jedi submodule has been checked out. '
    'In the YouCompleteMe folder, run "git submodule update --init --recursive"')
sys.path.pop( 0 )


class JediCompleter( Completer ):
  """
  A Completer that uses the Jedi completion engine.
  https://jedi.readthedocs.org/en/latest/
  """

  def __init__( self ):
    super( JediCompleter, self ).__init__()
    self._query_ready = Event()
    self._candidates_ready = Event()
    self._candidates = None
    self._start_completion_thread()


  def _start_completion_thread( self ):
    self._completion_thread = Thread( target=self.SetCandidates )
    self._completion_thread.daemon = True
    self._completion_thread.start()


  def SupportedFiletypes( self ):
    """ Just python """
    return [ 'python' ]


  def CandidatesForQueryAsyncInner( self, unused_query ):
    self._candidates = None
    self._candidates_ready.clear()
    self._query_ready.set()


  def AsyncCandidateRequestReadyInner( self ):
    if self._completion_thread.is_alive():
      return WaitAndClear( self._candidates_ready, timeout=0.005 )
    else:
      self._start_completion_thread()
      return False


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates or []

  
  def OnCursorMovedInsertMode( self ):
    if DidInvokeCallable():
      _ExpandParams()


  def SetCandidates( self ):
    while True:
      try:
        WaitAndClear( self._query_ready )
        script = _GetJediScript()
        self._candidates = [ { 'word': str( completion.word ),
                               'menu': str( completion.description ),
                               'info': str( completion.doc ) }
                            for completion in script.complete() ]
      except:
        self._query_ready.clear()
        self._candidates = []
      self._candidates_ready.set()


CALLABLE_PATTERN = re.compile(r'.*\w\($')

def DidInvokeCallable():
  """
  Returns True if there is an identifier followed by an opening bracket,
  followed by the vim cursor. I.e. if it looks like `object.some_method(_`, and
  not some arithmetic expression. 
  """
  line, column = vimsupport.CurrentLineAndColumn()
  return CALLABLE_PATTERN.match( vim.current.buffer[ line ][ :column ] )


def GetUltiSnipsManager():
  try:
    from UltiSnips import UltiSnips_Manager as manager
    return manager
  except ImportError:
    return None
  

def WaitAndClear( event, timeout=None ):
  flag_is_set = event.wait( timeout )
  if flag_is_set:
    event.clear()
  return flag_is_set


def _GetJediScript():
  filename = vim.current.buffer.name
  line, column = vimsupport.CurrentLineAndColumn()
  # Jedi expects lines to start at 1, not 0
  line += 1
  contents = '\n'.join( vim.current.buffer )
  encoding = vim.eval( '&encoding' )
  return Script( contents, line, column, filename, encoding )


def _FormatSnippet( params ):
  params = [ '${{{}:{}}}'.format( index + 1, param )
             for index, param in enumerate( params ) ]
  return '{})$0'.format( ', '.join( params ) )


def _ExpandParams():
  manager = GetUltiSnipsManager()
  script = _GetJediScript()
  call_def = script.get_in_function_call()
  if call_def is None or not manager:
    # Either jedi can't look up the params, or UltiSnips is not found
    return

  params = [ param.get_code().strip() for param in call_def.params ]
  snippet = _FormatSnippet(params)
  manager.expand_anon(snippet)
