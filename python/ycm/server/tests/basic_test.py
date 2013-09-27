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
import bottle

bottle.debug( True )

# 'contents' should be just one line of text
def RequestDataForFileWithContents( filename, contents ):
  return {
    'filetypes': ['foo'],
    'filepath': filename,
    'line_value': contents,
    'file_data': {
      filename: {
        'contents': contents,
        'filetypes': ['foo']
      }
    }
  }


def Setup():
  ycmd.SetServerStateToDefaults()


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_Works_test():
  app = TestApp( ycmd.app )
  event_data = RequestDataForFileWithContents( '/foo/bar', 'foo foogoo ba' )
  event_data.update( {
    'event_name': 'FileReadyToParse',
  } )

  app.post_json( '/event_notification', event_data )

  completion_data = RequestDataForFileWithContents( '/foo/bar',
                                                    'oo foo foogoo ba' )
  completion_data.update( {
    'query': 'oo',
    'line_num': 0,
    'column_num': 2,
    'start_column': 0,
  } )

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'foogoo' ) ],
       app.post_json( '/get_completions', completion_data ).json )


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_SyntaxKeywordsAdded_test():
  app = TestApp( ycmd.app )
  event_data = RequestDataForFileWithContents( '/foo/bar', '' )
  event_data.update( {
    'event_name': 'FileReadyToParse',
    'syntax_keywords': ['foo', 'bar', 'zoo']
  } )

  app.post_json( '/event_notification', event_data )

  completion_data = RequestDataForFileWithContents( '/foo/bar',
                                                    'oo ' )
  completion_data.update( {
    'query': 'oo',
    'line_num': 0,
    'column_num': 2,
    'start_column': 0,
  } )

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'zoo' ) ],
       app.post_json( '/get_completions', completion_data ).json )


@with_setup( Setup )
def GetCompletions_UltiSnipsCompleter_Works_test():
  app = TestApp( ycmd.app )
  event_data = RequestDataForFileWithContents( '/foo/bar', '' )
  event_data.update( {
    'event_name': 'BufferVisit',
    'ultisnips_snippets': [
        {'trigger': 'foo', 'description': 'bar'},
        {'trigger': 'zoo', 'description': 'goo'},
    ]
  } )

  app.post_json( '/event_notification', event_data )

  completion_data = RequestDataForFileWithContents( '/foo/bar', 'oo ' )
  completion_data.update( {
    'query': 'oo',
    'line_num': 0,
    'column_num': 2,
    'start_column': 0,
  } )

  eq_( [ BuildCompletionData( 'foo', '<snip> bar' ),
         BuildCompletionData( 'zoo', '<snip> goo' ) ],
       app.post_json( '/get_completions', completion_data ).json )


@with_setup( Setup )
def RunCompleterCommand_GoTo_Jedi_ZeroBasedLineAndColumn_test():
  app = TestApp( ycmd.app )
  contents = """
def foo():
  pass

foo()
"""

  goto_data = {
    'completer_target': 'filetype_default',
    'command_arguments': ['GoToDefinition'],
    'line_num': 4,
    'column_num': 0,
    'filetypes': ['python'],
    'filepath': '/foo.py',
    'file_data': {
      '/foo.py': {
        'contents': contents,
        'filetypes': ['python']
      }
    }
  }

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

  filename = '/foo.cpp'
  goto_data = {
    'compilation_flags': ['-x', 'c++'],
    'completer_target': 'filetype_default',
    'command_arguments': ['GoToDefinition'],
    'line_num': 9,
    'column_num': 2,
    'filetypes': ['cpp'],
    'filepath': filename,
    'file_data': {
      filename: {
        'contents': contents,
        'filetypes': ['cpp']
      }
    }
  }

  # 0-based line and column!
  eq_( {
        'filepath': '/foo.cpp',
        'line_num': 1,
        'column_num': 7
      },
      app.post_json( '/run_completer_command', goto_data ).json )


@with_setup( Setup )
def FiletypeCompletionAvailable_Works_test():
  app = TestApp( ycmd.app )
  request_data = {
    'filetypes': ['cpp']
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

