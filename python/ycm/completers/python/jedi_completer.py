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

import vim
from ycm.completers.threaded_completer import ThreadedCompleter
from ycm import vimsupport

import sys
from os.path import join, abspath, dirname

# We need to add the jedi package to sys.path, but it's important that we clean
# up after ourselves, because ycm.YouCompletMe.GetFiletypeCompleterForFiletype
# removes sys.path[0] after importing completers.python.hook
sys.path.insert( 0, join( abspath( dirname( __file__ ) ), 'jedi' ) )
try:
  import jedi
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


  def _GetJediScript( self ):
    contents = '\n'.join( vim.current.buffer )
    line, column = vimsupport.CurrentLineAndColumn()
    # Jedi expects lines to start at 1, not 0
    line += 1
    filename = vim.current.buffer.name

    return jedi.Script( contents, line, column, filename )


  def ComputeCandidates( self, unused_query, unused_start_column ):
    script = self._GetJediScript()

    return [ { 'word': str( completion.word ),
               'menu': str( completion.description ),
               'info': str( completion.doc ) }
             for completion in script.complete() ]


  def DefinedSubcommands( self ):
    return [ "GoToDefinition",
             "GoToDeclaration",
             "GoToDefinitionElseDeclaration" ]


  def OnUserCommand( self, arguments ):
    if not arguments:
      self.EchoUserCommandsHelpMessage()
      return

    command = arguments[ 0 ]
    if command == 'GoToDefinition':
      self._GoToDefinition()
    elif command == 'GoToDeclaration':
      self._GoToDeclaration()
    elif command == 'GoToDefinitionElseDeclaration':
      self._GoToDefinitionElseDeclaration()


  def _GoToDefinition( self ):
    definitions = self._GetDefinitionsList()
    if definitions:
      self._JumpToLocation( definitions )
    else:
      vimsupport.PostVimMessage( 'Can\'t jump to definition.' )


  def _GoToDeclaration( self ):
    definitions = self._GetDefinitionsList( declaration = True )
    if definitions:
      self._JumpToLocation( definitions )
    else:
      vimsupport.PostVimMessage( 'Can\'t jump to declaration.' )


  def _GoToDefinitionElseDeclaration( self ):
    definitions = self._GetDefinitionsList() or \
        self._GetDefinitionsList( declaration = True )
    if definitions:
      self._JumpToLocation( definitions )
    else:
      vimsupport.PostVimMessage( 'Can\'t jump to definition or declaration.' )


  def _GetDefinitionsList( self, declaration = False ):
    definitions = []
    script = self._GetJediScript()
    try:
      if declaration:
        definitions = script.goto_definitions()
      else:
        definitions = script.goto_assignments()
    except jedi.NotFoundError:
      vimsupport.PostVimMessage(
                  "Cannot follow nothing. Put your cursor on a valid name." )
    except Exception as e:
      vimsupport.PostVimMessage(
                  "Caught exception, aborting. Full error: " + str( e ) )

    return definitions


  def _JumpToLocation( self, definition_list ):
    if len( definition_list ) == 1:
      definition = definition_list[ 0 ]
      if definition.in_builtin_module():
        if definition.is_keyword:
          vimsupport.PostVimMessage(
                  "Cannot get the definition of Python keywords." )
        else:
          vimsupport.PostVimMessage( "Builtin modules cannot be displayed." )
      else:
        vimsupport.JumpToLocation( definition.module_path,
                                   definition.line_nr,
                                   definition.column + 1 )
    else:
      # multiple definitions
      defs = []
      for definition in definition_list:
        if definition.in_builtin_module():
          defs.append( {'text': 'Builtin ' + \
                       definition.description.encode( 'utf-8' ) } )
        else:
          defs.append( {'filename': definition.module_path.encode( 'utf-8' ),
                        'lnum': definition.line_nr,
                        'col': definition.column + 1,
                        'text': definition.description.encode( 'utf-8' ) } )

      vim.eval( 'setqflist( %s )' % repr( defs ) )
      vim.eval( 'youcompleteme#OpenGoToList()' )
