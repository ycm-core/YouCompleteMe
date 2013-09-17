#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Stephen Sugden <me@stephensugden.com>
#                           Strahinja Val Markovic <val@markovic.io>
#                           Stanislav Golovanov <stgolovanov@gmail.com>
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

from ycm.completers.threaded_completer import ThreadedCompleter
from ycm import server_responses

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompletMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert( 0, join( abspath( dirname( __file__ ) ), 'jedi' ) )
try:
  import jedi
except ImportError:
  raise ImportError(
    'Error importing jedi. Make sure the jedi submodule has been checked out. '
    'In the YouCompleteMe folder, run "git submodule update --init --recursive"')
sys.path.pop( 0 )


class JediCompleter( ThreadedCompleter ):
  """
  A Completer that uses the Jedi completion engine.
  https://jedi.readthedocs.org/en/latest/
  """

  def __init__( self, user_options ):
    super( JediCompleter, self ).__init__( user_options )


  def SupportedFiletypes( self ):
    """ Just python """
    return [ 'python' ]


  def _GetJediScript( self, request_data ):
      filename = request_data[ 'filepath' ]
      contents = request_data[ 'file_data' ][ filename ][ 'contents' ]
      # Jedi expects lines to start at 1, not 0
      line = request_data[ 'line_num' ] + 1
      column = request_data[ 'column_num' ]
      print contents

      return jedi.Script( contents, line, column, filename )


  def ComputeCandidates( self, request_data ):
    script = self._GetJediScript( request_data )
    return [ server_responses.BuildCompletionData(
                str( completion.name ),
                str( completion.description ),
                str( completion.doc ) )
             for completion in script.completions() ]

  def DefinedSubcommands( self ):
    return [ "GoToDefinition",
             "GoToDeclaration",
             "GoToDefinitionElseDeclaration" ]


  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command = arguments[ 0 ]
    if command == 'GoToDefinition':
      return self._GoToDefinition( request_data )
    elif command == 'GoToDeclaration':
      return self._GoToDeclaration( request_data )
    elif command == 'GoToDefinitionElseDeclaration':
      return self._GoToDefinitionElseDeclaration( request_data )


  def _GoToDefinition( self, request_data ):
    definitions = self._GetDefinitionsList( request_data )
    if definitions:
      return self._BuildGoToResponse( definitions )
    else:
      raise RuntimeError( 'Can\'t jump to definition.' )


  def _GoToDeclaration( self, request_data ):
    definitions = self._GetDefinitionsList( request_data, declaration = True )
    if definitions:
      return self._BuildGoToResponse( definitions )
    else:
      raise RuntimeError( 'Can\'t jump to declaration.' )


  def _GoToDefinitionElseDeclaration( self, request_data ):
    definitions = self._GetDefinitionsList() or \
        self._GetDefinitionsList( request_data, declaration = True )
    if definitions:
      return self._BuildGoToResponse( definitions )
    else:
      raise RuntimeError( 'Can\'t jump to definition or declaration.' )


  def _GetDefinitionsList( self, request_data, declaration = False ):
    definitions = []
    script = self._GetJediScript( request_data )
    try:
      if declaration:
        definitions = script.goto_definitions()
      else:
        definitions = script.goto_assignments()
    except jedi.NotFoundError:
      raise RuntimeError(
                  'Cannot follow nothing. Put your cursor on a valid name.' )

    return definitions


  def _BuildGoToResponse( self, definition_list ):
    if len( definition_list ) == 1:
      definition = definition_list[ 0 ]
      if definition.in_builtin_module():
        if definition.is_keyword:
          raise RuntimeError(
                  'Cannot get the definition of Python keywords.' )
        else:
          raise RuntimeError( 'Builtin modules cannot be displayed.' )
      else:
        return server_responses.BuildGoToResponse( definition.module_path,
                                                   definition.line -1,
                                                   definition.column )
    else:
      # multiple definitions
      defs = []
      for definition in definition_list:
        if definition.in_builtin_module():
          defs.append( server_responses.BuildDescriptionOnlyGoToResponse(
                       'Builting ' + definition.description ) )
        else:
          defs.append(
            server_responses.BuildGoToResponse( definition.module_path,
                                                definition.line -1,
                                                definition.column,
                                                definition.description ) )
      return defs

