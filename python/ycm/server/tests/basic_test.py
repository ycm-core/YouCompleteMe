#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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

from webtest import TestApp
from .. import ycmd
from ..responses import BuildCompletionData
from nose.tools import ok_, eq_, with_setup
from hamcrest import ( assert_that, has_items, has_entry, contains,
                       contains_string, has_entries )
import bottle

bottle.debug( True )

# TODO: Split this file into multiple files.

def BuildRequest( **kwargs ):
  filepath = kwargs[ 'filepath' ] if 'filepath' in kwargs else '/foo'
  contents = kwargs[ 'contents' ] if 'contents' in kwargs else ''
  filetype = kwargs[ 'filetype' ] if 'filetype' in kwargs else 'foo'

  request = {
    'query': '',
    'line_num': 0,
    'column_num': 0,
    'start_column': 0,
    'filetypes': [ filetype ],
    'filepath': filepath,
    'line_value': contents,
    'file_data': {
      filepath: {
        'contents': contents,
        'filetypes': [ filetype ]
      }
    }
  }

  for key, value in kwargs.iteritems():
    if key in [ 'contents', 'filetype', 'filepath' ]:
      continue
    request[ key ] = value

    if key == 'line_num':
      lines = contents.splitlines()
      if len( lines ) > 1:
        # NOTE: assumes 0-based line_num
        request[ 'line_value' ] = lines[ value ]

  return request


# TODO: Make the other tests use this helper too instead of BuildCompletionData
def CompletionEntryMatcher( insertion_text ):
  return has_entry( 'insertion_text', insertion_text )


def Setup():
  ycmd.SetServerStateToDefaults()


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_Works_test():
  app = TestApp( ycmd.app )
  event_data = BuildRequest( contents = 'foo foogoo ba',
                             event_name = 'FileReadyToParse' )

  app.post_json( '/event_notification', event_data )

  completion_data = BuildRequest( contents = 'oo foo foogoo ba',
                                  query = 'oo',
                                  column_num = 2 )

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'foogoo' ) ],
       app.post_json( '/completions', completion_data ).json )


@with_setup( Setup )
def GetCompletions_ClangCompleter_Works_test():
  app = TestApp( ycmd.app )
  contents = """
struct Foo {
  int x;
  int y;
  char c;
};

int main()
{
  Foo foo;
  foo.
}
"""

  # 0-based line and column!
  completion_data = BuildRequest( filepath = '/foo.cpp',
                                  filetype = 'cpp',
                                  contents = contents,
                                  line_num = 10,
                                  column_num = 6,
                                  start_column = 6,
                                  compilation_flags = ['-x', 'c++'] )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_items( CompletionEntryMatcher( 'c' ),
                                   CompletionEntryMatcher( 'x' ),
                                   CompletionEntryMatcher( 'y' ) ) )


@with_setup( Setup )
def GetCompletions_ForceSemantic_Works_test():
  app = TestApp( ycmd.app )

  completion_data = BuildRequest( filetype = 'python',
                                  force_semantic = True )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_items( CompletionEntryMatcher( 'abs' ),
                                   CompletionEntryMatcher( 'open' ),
                                   CompletionEntryMatcher( 'bool' ) ) )


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_SyntaxKeywordsAdded_test():
  app = TestApp( ycmd.app )
  event_data = BuildRequest( event_name = 'FileReadyToParse',
                             syntax_keywords = ['foo', 'bar', 'zoo'] )

  app.post_json( '/event_notification', event_data )

  completion_data = BuildRequest( contents =  'oo ',
                                  query = 'oo',
                                  column_num = 2 )

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'zoo' ) ],
       app.post_json( '/completions', completion_data ).json )


@with_setup( Setup )
def GetCompletions_UltiSnipsCompleter_Works_test():
  app = TestApp( ycmd.app )
  event_data = BuildRequest(
    event_name = 'BufferVisit',
    ultisnips_snippets = [
        {'trigger': 'foo', 'description': 'bar'},
        {'trigger': 'zoo', 'description': 'goo'},
    ] )

  app.post_json( '/event_notification', event_data )

  completion_data = BuildRequest( contents =  'oo ',
                                  query = 'oo',
                                  column_num = 2 )

  eq_( [ BuildCompletionData( 'foo', '<snip> bar' ),
         BuildCompletionData( 'zoo', '<snip> goo' ) ],
       app.post_json( '/completions', completion_data ).json )


@with_setup( Setup )
def RunCompleterCommand_GoTo_Jedi_ZeroBasedLineAndColumn_test():
  app = TestApp( ycmd.app )
  contents = """
def foo():
  pass

foo()
"""

  goto_data = BuildRequest( completer_target = 'filetype_default',
                            command_arguments = ['GoToDefinition'],
                            line_num = 4,
                            contents = contents,
                            filetype = 'python',
                            filepath = '/foo.py' )

  # 0-based line and column!
  eq_( {
         'filepath': '/foo.py',
         'line_num': 1,
         'column_num': 4
       },
       app.post_json( '/run_completer_command', goto_data ).json )


@with_setup( Setup )
def RunCompleterCommand_GoTo_Clang_ZeroBasedLineAndColumn_test():
  app = TestApp( ycmd.app )
  contents = """
struct Foo {
  int x;
  int y;
  char c;
};

int main()
{
  Foo foo;
  return 0;
}
"""

  goto_data = BuildRequest( completer_target = 'filetype_default',
                            command_arguments = ['GoToDefinition'],
                            compilation_flags = ['-x', 'c++'],
                            line_num = 9,
                            column_num = 2,
                            contents = contents,
                            filetype = 'cpp' )

  # 0-based line and column!
  eq_( {
        'filepath': '/foo',
        'line_num': 1,
        'column_num': 7
      },
      app.post_json( '/run_completer_command', goto_data ).json )


@with_setup( Setup )
def DefinedSubcommands_Works_test():
  app = TestApp( ycmd.app )
  subcommands_data = BuildRequest( completer_target = 'python' )

  eq_( [ 'GoToDefinition',
         'GoToDeclaration',
         'GoToDefinitionElseDeclaration' ],
       app.post_json( '/defined_subcommands', subcommands_data ).json )


@with_setup( Setup )
def DefinedSubcommands_WorksWhenNoExplicitCompleterTargetSpecified_test():
  app = TestApp( ycmd.app )
  subcommands_data = BuildRequest( filetype = 'python' )

  eq_( [ 'GoToDefinition',
         'GoToDeclaration',
         'GoToDefinitionElseDeclaration' ],
       app.post_json( '/defined_subcommands', subcommands_data ).json )


@with_setup( Setup )
def Diagnostics_ClangCompleter_ZeroBasedLineAndColumn_test():
  app = TestApp( ycmd.app )
  contents = """
struct Foo {
  int x  // semicolon missing here!
  int y;
  int c;
  int d;
};
"""

  event_data = BuildRequest( compilation_flags = ['-x', 'c++'],
                             event_name = 'FileReadyToParse',
                             contents = contents,
                             filetype = 'cpp' )

  results = app.post_json( '/event_notification', event_data ).json
  assert_that( results,
               contains(
                  has_entries( { 'text': contains_string( "expected ';'" ),
                                 'line_num': 2,
                                 'column_num': 7 } ) ) )


@with_setup( Setup )
def GetDetailedDiagnostic_ClangCompleter_Works_test():
  app = TestApp( ycmd.app )
  contents = """
struct Foo {
  int x  // semicolon missing here!
  int y;
  int c;
  int d;
};
"""

  diag_data = BuildRequest( compilation_flags = ['-x', 'c++'],
                            line_num = 2,
                            contents = contents,
                            filetype = 'cpp' )

  event_data = diag_data.copy()
  event_data.update( {
    'event_name': 'FileReadyToParse',
  } )

  app.post_json( '/event_notification', event_data )
  results = app.post_json( '/detailed_diagnostic', diag_data ).json
  assert_that( results,
               has_entry( 'message', contains_string( "expected ';'" ) ) )


@with_setup( Setup )
def FiletypeCompletionAvailable_Works_test():
  app = TestApp( ycmd.app )
  request_data = {
    'filetypes': ['python']
  }

  ok_( app.post_json( '/filetype_completion_available',
                      request_data ).json )


@with_setup( Setup )
def UserOptions_Works_test():
  app = TestApp( ycmd.app )
  options = app.get( '/user_options' ).json
  ok_( len( options ) )

  options[ 'foobar' ] = 'zoo'

  app.post_json( '/user_options', options )
  eq_( options, app.get( '/user_options' ).json )

