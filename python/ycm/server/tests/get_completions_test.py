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

from ..server_utils import SetUpPythonPath
SetUpPythonPath()
import time
import httplib
from .test_utils import ( Setup, BuildRequest, PathToTestFile,
                          ChangeSpecificOptions )
from webtest import TestApp, AppError
from nose.tools import eq_, with_setup
from hamcrest import ( assert_that, has_item, has_items, has_entry,
                       contains_inanyorder, empty )
from ..responses import ( BuildCompletionData, UnknownExtraConf,
                          NoExtraConfDetected )
from .. import handlers
import bottle

bottle.debug( True )


# TODO: Make the other tests use this helper too instead of BuildCompletionData
def CompletionEntryMatcher( insertion_text ):
  return has_entry( 'insertion_text', insertion_text )


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_Works_test():
  app = TestApp( handlers.app )
  event_data = BuildRequest( contents = 'foo foogoo ba',
                             event_name = 'FileReadyToParse' )

  app.post_json( '/event_notification', event_data )

  completion_data = BuildRequest( contents = 'oo foo foogoo ba',
                                  query = 'oo',
                                  column_num = 2 )

  eq_( [ BuildCompletionData( 'foo' ),
         BuildCompletionData( 'foogoo' ) ],
       app.post_json( '/completions', completion_data ).json )

def _CsCompleter_WaitForOmniSharpThenShutdown(app):
  # Wait until OmniSharp ready
  while True:
    result = app.post_json( '/run_completer_command',
                            BuildRequest( completer_target = 'filetype_default',
                                          command_arguments = ['ServerRunning'],
                                          filetype = 'cs' ) ).json
    if result:
      break
    time.sleep( 0.2 )

  # Stop it again
  app.post_json( '/run_completer_command',
                 BuildRequest( completer_target = 'filetype_default',
                               command_arguments = ['StopServer'],
                               filetype = 'cs' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_Works_test():
  app = TestApp( handlers.app )
  app.post_json( '/ignore_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  filepath = PathToTestFile( 'testy/Program.cs' )
  contents = open( filepath ).read()
  event_data = BuildRequest( filepath = filepath,
                             filetype = 'cs',
                             contents = contents,
                             event_name = 'FileReadyToParse' )

  app.post_json( '/event_notification', event_data )

  # We need to wait until the server has started up.
  while True:
    result = app.post_json( '/run_completer_command',
                            BuildRequest( completer_target = 'filetype_default',
                                          command_arguments = ['ServerReady'],
                                          filetype = 'cs' ) ).json
    if result:
      break
    time.sleep( 0.2 )

  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'cs',
                                  contents = contents,
                                  line_num = 8,
                                  column_num = 11,
                                  start_column = 11 )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_items( CompletionEntryMatcher( 'CursorLeft' ),
                                   CompletionEntryMatcher( 'CursorSize' ) ) )

  # We need to turn off the CS server so that it doesn't stick around
  app.post_json( '/run_completer_command',
                 BuildRequest( completer_target = 'filetype_default',
                               command_arguments = ['StopServer'],
                               filetype = 'cs' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_ReloadSolutionWorks_test():
  app = TestApp( handlers.app )
  app.post_json( '/ignore_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  filepath = PathToTestFile( 'testy/Program.cs' )
  contents = open( filepath ).read()
  event_data = BuildRequest( filepath = filepath,
                             filetype = 'cs',
                             contents = contents,
                             event_name = 'FileReadyToParse' )

  app.post_json( '/event_notification', event_data )

  # We need to wait until the server has started up.
  while True:
    result = app.post_json( '/run_completer_command',
                            BuildRequest( completer_target = 'filetype_default',
                                          command_arguments = ['ServerReady'],
                                          filetype = 'cs' ) ).json
    if result:
      break
    time.sleep( 0.2 )


  result = app.post_json( '/run_completer_command',
                          BuildRequest( completer_target = 'filetype_default',
                                        command_arguments = ['ReloadSolution'],
                                        filetype = 'cs' ) ).json

  eq_(result, True)

  # We need to turn off the CS server so that it doesn't stick around
  app.post_json( '/run_completer_command',
                 BuildRequest( completer_target = 'filetype_default',
                               command_arguments = ['StopServer'],
                               filetype = 'cs' ) )

def _CsCompleter_SolutionSelectCheck( app, sourcefile, reference_solution,
                                      extra_conf_store=None ):
  # reusable test: verify that the correct solution (reference_solution) is
  #   detected for a given source file (and optionally a given extra_conf)
  app.post_json( '/ignore_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  if extra_conf_store:
    app.post_json( '/load_extra_conf_file', { 'filepath': extra_conf_store } )
  contents = open( sourcefile ).read()
  event_data = BuildRequest( filepath = sourcefile,
                             filetype = 'cs',
                             contents = contents,
                             event_name = 'FileReadyToParse' )

  # Here the server should raise an exception if it can't start
  app.post_json( '/event_notification', event_data )
  # Assuming we have a successful launch
  result = app.post_json( '/run_completer_command',
                          BuildRequest( completer_target = 'filetype_default',
                                        command_arguments = ['SolutionFile'],
                                        filetype = 'cs' ) ).json
  # We don't want the server to linger around, stop it once start completed
  _CsCompleter_WaitForOmniSharpThenShutdown(app)
  # Now that cleanup is done, verify solution file
  eq_( reference_solution , result)

@with_setup( Setup )
def GetCompletions_CsCompleter_UsesSubfolderHint_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-named-like-folder/'
                                      'testy/Program.cs'),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-named-like-folder/'
                                      'testy.sln' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_UsesSuperfolderHint_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-named-like-folder/'
                                      'not-testy/Program.cs' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-named-like-folder/'
                                      'solution-named-like-folder.sln' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_ExtraConfStoreAbsolute_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-abs/'
                                      'testy/Program.cs' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'testy2.sln' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-abs/'
                                      '.ycm_extra_conf.py' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_ExtraConfStoreRelative_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-rel/'
                                      'testy/Program.cs' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-rel/'
                                      'testy2.sln' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-rel/'
                                      '.ycm_extra_conf.py' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_ExtraConfStoreHint_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-hint/'
                                      'testy/Program.cs' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-hint/'
                                      'testy1.sln' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-hint/'
                                      'testy/'
                                      '.ycm_extra_conf.py' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_ExtraConfStoreNonexisting_test():
  app = TestApp( handlers.app )
  _CsCompleter_SolutionSelectCheck( app,
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-bad/'
                                      'testy/Program.cs' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-bad/'
                                      'testy2.sln' ),
                                    PathToTestFile(
                                      'testy-multiple-solutions/'
                                      'solution-not-named-like-folder/'
                                      'extra-conf-bad/'
                                      'testy/'
                                      '.ycm_extra_conf.py' ) )

@with_setup( Setup )
def GetCompletions_CsCompleter_DoesntStartWithAmbiguousMultipleSolutions_test():
  app = TestApp( handlers.app )
  app.post_json( '/ignore_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )
  filepath = PathToTestFile( ('testy-multiple-solutions/'
                              'solution-not-named-like-folder/'
                              'testy/Program.cs') )
  contents = open( filepath ).read()
  event_data = BuildRequest( filepath = filepath,
                             filetype = 'cs',
                             contents = contents,
                             event_name = 'FileReadyToParse' )

  exception_caught = False
  try:
    app.post_json( '/event_notification', event_data )
  except AppError as e:
    if 'Autodetection of solution file failed' in str(e):
      exception_caught = True

  # the test passes if we caught an exception when trying to start it,
  # so raise one if it managed to start
  if not exception_caught:
    _CsCompleter_WaitForOmniSharpThenShutdown(app)

    raise Exception( ('The Omnisharp server started, despite us not being able '
                      'to find a suitable solution file to feed it. Did you '
                      'fiddle with the solution finding code in '
                      'cs_completer.py? Hopefully you\'ve enhanced it: you need'
                      'to update this test then :)') )

@with_setup( Setup )
def GetCompletions_ClangCompleter_WorksWithExplicitFlags_test():
  app = TestApp( handlers.app )
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
def GetCompletions_ClangCompleter_NoCompletionsWhenAutoTriggerOff_test():
  ChangeSpecificOptions( { 'auto_trigger': False } )
  app = TestApp( handlers.app )
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
  assert_that( results, empty() )


@with_setup( Setup )
def GetCompletions_ClangCompleter_UnknownExtraConfException_test():
  app = TestApp( handlers.app )
  filepath = PathToTestFile( 'basic.cpp' )
  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'cpp',
                                  contents = open( filepath ).read(),
                                  line_num = 10,
                                  column_num = 6,
                                  start_column = 6,
                                  force_semantic = True )

  response = app.post_json( '/completions',
                            completion_data,
                            expect_errors = True )

  eq_( response.status_code, httplib.INTERNAL_SERVER_ERROR )
  assert_that( response.json,
               has_entry( 'exception',
                          has_entry( 'TYPE', UnknownExtraConf.__name__ ) ) )

  app.post_json( '/ignore_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )

  response = app.post_json( '/completions',
                            completion_data,
                            expect_errors = True )

  eq_( response.status_code, httplib.INTERNAL_SERVER_ERROR )
  assert_that( response.json,
               has_entry( 'exception',
                          has_entry( 'TYPE', NoExtraConfDetected.__name__ ) ) )


@with_setup( Setup )
def GetCompletions_ClangCompleter_WorksWhenExtraConfExplicitlyAllowed_test():
  app = TestApp( handlers.app )
  app.post_json( '/load_extra_conf_file',
                 { 'filepath': PathToTestFile( '.ycm_extra_conf.py' ) } )

  filepath = PathToTestFile( 'basic.cpp' )
  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'cpp',
                                  contents = open( filepath ).read(),
                                  line_num = 10,
                                  column_num = 6,
                                  start_column = 6 )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_items( CompletionEntryMatcher( 'c' ),
                                   CompletionEntryMatcher( 'x' ),
                                   CompletionEntryMatcher( 'y' ) ) )


@with_setup( Setup )
def GetCompletions_ClangCompleter_ExceptionWhenNoFlagsFromExtraConf_test():
  app = TestApp( handlers.app )
  app.post_json( '/load_extra_conf_file',
                 { 'filepath': PathToTestFile(
                     'noflags/.ycm_extra_conf.py' ) } )

  filepath = PathToTestFile( 'noflags/basic.cpp' )
  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'cpp',
                                  contents = open( filepath ).read(),
                                  line_num = 10,
                                  column_num = 6,
                                  start_column = 6 )

  response = app.post_json( '/completions',
                            completion_data,
                            expect_errors = True )
  eq_( response.status_code, httplib.INTERNAL_SERVER_ERROR )
  assert_that( response.json,
               has_entry( 'exception',
                          has_entry( 'TYPE', RuntimeError.__name__ ) ) )


@with_setup( Setup )
def GetCompletions_ClangCompleter_ForceSemantic_OnlyFileteredCompletions_test():
  app = TestApp( handlers.app )
  contents = """
int main()
{
  int foobar;
  int floozar;
  int gooboo;
  int bleble;

  fooar
}
"""

  # 0-based line and column!
  completion_data = BuildRequest( filepath = '/foo.cpp',
                                  filetype = 'cpp',
                                  force_semantic = True,
                                  contents = contents,
                                  line_num = 8,
                                  column_num = 7,
                                  start_column = 7,
                                  query = 'fooar',
                                  compilation_flags = ['-x', 'c++'] )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results,
               contains_inanyorder( CompletionEntryMatcher( 'foobar' ),
                                    CompletionEntryMatcher( 'floozar' ) ) )


@with_setup( Setup )
def GetCompletions_ForceSemantic_Works_test():
  app = TestApp( handlers.app )

  completion_data = BuildRequest( filetype = 'python',
                                  force_semantic = True )

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_items( CompletionEntryMatcher( 'abs' ),
                                   CompletionEntryMatcher( 'open' ),
                                   CompletionEntryMatcher( 'bool' ) ) )


@with_setup( Setup )
def GetCompletions_ClangCompleter_ClientDataGivenToExtraConf_test():
  app = TestApp( handlers.app )
  app.post_json( '/load_extra_conf_file',
                 { 'filepath': PathToTestFile(
                                  'client_data/.ycm_extra_conf.py' ) } )

  filepath = PathToTestFile( 'client_data/main.cpp' )
  completion_data = BuildRequest( filepath = filepath,
                                  filetype = 'cpp',
                                  contents = open( filepath ).read(),
                                  line_num = 8,
                                  column_num = 6,
                                  start_column = 6,
                                  extra_conf_data = {
                                    'flags': ['-x', 'c++']
                                  })

  results = app.post_json( '/completions', completion_data ).json
  assert_that( results, has_item( CompletionEntryMatcher( 'x' ) ) )


@with_setup( Setup )
def GetCompletions_IdentifierCompleter_SyntaxKeywordsAdded_test():
  app = TestApp( handlers.app )
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
  app = TestApp( handlers.app )
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
def GetCompletions_UltiSnipsCompleter_UnusedWhenOffWithOption_test():
  ChangeSpecificOptions( { 'use_ultisnips_completer': False } )
  app = TestApp( handlers.app )

  event_data = BuildRequest(
    event_name = 'BufferVisit',
    ultisnips_snippets = [
        {'trigger': 'foo', 'description': 'bar'},
        {'trigger': 'zoo', 'description': 'goo'},
    ] )

  app.post_json( '/event_notification', event_data )

  completion_data = BuildRequest( contents = 'oo ',
                                  query = 'oo',
                                  column_num = 2 )

  eq_( [], app.post_json( '/completions', completion_data ).json )


