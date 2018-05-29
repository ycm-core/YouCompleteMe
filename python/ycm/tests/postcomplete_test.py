# encoding: utf-8
#
# Copyright (C) 2015-2016 YouCompleteMe contributors
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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.tests.test_utils import MockVimModule
MockVimModule()

import contextlib
from mock import MagicMock, DEFAULT, patch
from nose.tools import eq_, ok_

from ycm import vimsupport
from ycmd.utils import ToBytes
from ycm.client.completion_request import ( CompletionRequest,
                                            _FilterToMatchingCompletions,
                                            _GetRequiredNamespaceImport )


def CompleteItemIs( word, abbr = None, menu = None,
                    info = None, kind = None, **kwargs ):
  item = {
    'word': ToBytes( word ),
    'abbr': ToBytes( abbr ),
    'menu': ToBytes( menu ),
    'info': ToBytes( info ),
    'kind': ToBytes( kind ),
  }
  item.update( **kwargs )
  return item


def GetVariableValue_CompleteItemIs( word, abbr = None, menu = None,
                                     info = None, kind = None, **kwargs ):
  def Result( variable ):
    if variable == 'v:completed_item':
      return CompleteItemIs( word, abbr, menu, info, kind, **kwargs )
    return DEFAULT
  return MagicMock( side_effect = Result )


def BuildCompletion( insertion_text = 'Test',
                     menu_text = None,
                     extra_menu_info = None,
                     detailed_info = None,
                     kind = None,
                     extra_data = None ):
  if extra_data is None:
    extra_data = {}

  return {
    'extra_data': extra_data,
    'insertion_text': insertion_text,
    'menu_text': menu_text,
    'extra_menu_info': extra_menu_info,
    'kind': kind,
    'detailed_info': detailed_info,
  }


def BuildCompletionNamespace( namespace = None,
                              insertion_text = 'Test',
                              menu_text = None,
                              extra_menu_info = None,
                              detailed_info = None,
                              kind = None ):
  return BuildCompletion( insertion_text = insertion_text,
                          menu_text = menu_text,
                          extra_menu_info = extra_menu_info,
                          detailed_info = detailed_info,
                          kind = kind,
                          extra_data = {
                            'required_namespace_import': namespace
                          } )


def BuildCompletionFixIt( fixits,
                          insertion_text = 'Test',
                          menu_text = None,
                          extra_menu_info = None,
                          detailed_info = None,
                          kind = None ):
  return BuildCompletion( insertion_text = insertion_text,
                          menu_text = menu_text,
                          extra_menu_info = extra_menu_info,
                          detailed_info = detailed_info,
                          kind = kind,
                          extra_data = {
                            'fixits': fixits,
                          } )


@contextlib.contextmanager
def _SetupForCsharpCompletionDone( completions ):
  with patch( 'ycm.vimsupport.InsertNamespace' ):
    with _SetUpCompleteDone( completions ) as request:
      yield request


@contextlib.contextmanager
def _SetUpCompleteDone( completions ):
  with patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Test' ):
    request = CompletionRequest( None )
    request.Done = MagicMock( return_value = True )
    request.RawResponse = MagicMock( return_value = {
      'completions': completions
    } )
    yield request


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'cs' ] )
def GetCompleteDoneHooks_ResultOnCsharp_test( *args ):
  request = CompletionRequest( None )
  result = list( request._GetCompleteDoneHooks() )
  eq_( result, [ request._OnCompleteDone_Csharp ] )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'java' ] )
def GetCompleteDoneHooks_ResultOnJava_test( *args ):
  request = CompletionRequest( None )
  result = list( request._GetCompleteDoneHooks() )
  eq_( result, [ request._OnCompleteDone_FixIt ] )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'typescript' ] )
def GetCompleteDoneHooks_ResultOnTypeScript_test( *args ):
  request = CompletionRequest( None )
  result = list( request._GetCompleteDoneHooks() )
  eq_( result, [ request._OnCompleteDone_FixIt ] )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
def GetCompleteDoneHooks_EmptyOnOtherFiletype_test( *args ):
  request = CompletionRequest( None )
  result = request._GetCompleteDoneHooks()
  eq_( len( list( result ) ), 0 )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
def OnCompleteDone_WithActionCallsIt_test( *args ):
  request = CompletionRequest( None )
  request.Done = MagicMock( return_value = True )
  action = MagicMock()
  request._complete_done_hooks[ 'ycmtest' ] = action
  request.OnCompleteDone()
  ok_( action.called )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
def OnCompleteDone_NoActionNoError_test( *args ):
  request = CompletionRequest( None )
  request.Done = MagicMock( return_value = True )
  request._OnCompleteDone_Csharp = MagicMock()
  request._OnCompleteDone_FixIt = MagicMock()
  request.OnCompleteDone()
  request._OnCompleteDone_Csharp.assert_not_called()
  request._OnCompleteDone_FixIt.assert_not_called()


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
def OnCompleteDone_NoActionIfNotDone_test( *args ):
  request = CompletionRequest( None )
  request.Done = MagicMock( return_value = False )
  action = MagicMock()
  request._complete_done_hooks[ 'ycmtest' ] = action
  request.OnCompleteDone()
  action.assert_not_called()


def FilterToCompletedCompletions_MatchIsReturned_test():
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = _FilterToMatchingCompletions( CompleteItemIs( 'Test' ), completions )
  eq_( list( result ), completions )


def FilterToCompletedCompletions_ShortTextDoesntRaise_test():
  completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
  result = _FilterToMatchingCompletions( CompleteItemIs( 'A' ), completions )
  eq_( list( result ), [] )


def FilterToCompletedCompletions_ExactMatchIsReturned_test():
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = _FilterToMatchingCompletions( CompleteItemIs( 'Test' ), completions )
  eq_( list( result ), completions )


def FilterToCompletedCompletions_NonMatchIsntReturned_test():
  completions = [ BuildCompletion( insertion_text = 'A' ) ]
  result = _FilterToMatchingCompletions( CompleteItemIs( '   Quote' ),
                                         completions )
  eq_( list( result ), [] )


def FilterToCompletedCompletions_Unicode_test():
  completions = [ BuildCompletion( insertion_text = '†es†' ) ]
  result = _FilterToMatchingCompletions( CompleteItemIs( '†es†' ),
                                         completions )
  eq_( list( result ), completions )


def GetRequiredNamespaceImport_ReturnNoneForNoExtraData_test():
  eq_( _GetRequiredNamespaceImport( {} ), None )


def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test():
  namespace = 'A_NAMESPACE'
  eq_( _GetRequiredNamespaceImport( BuildCompletionNamespace( namespace ) ),
       namespace )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Te' ) )
def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_test(
    *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    eq_( request._GetCompletionsUserMayHaveCompleted(), [] )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatches_test( *args ):
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletionNamespace( *info ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( request._GetCompletionsUserMayHaveCompleted(), completions )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatchesEvenIfPartial_test(): # noqa
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletionNamespace( *info ),
                  BuildCompletion( insertion_text = 'TestTest' ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( request._GetCompletionsUserMayHaveCompleted(), [ completions[ 0 ] ] )


def GetCompletionsUserMayHaveCompleted_DontReturnMatchIfNoExactMatchesAndPartial_test(): # noqa
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletion( insertion_text = info[ 0 ] ),
                  BuildCompletion( insertion_text = 'TestTest' ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( request._GetCompletionsUserMayHaveCompleted(), [] )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_test( *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    eq_( request._GetCompletionsUserMayHaveCompleted(), completions )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='0' ) )
def GetCompletionsUserMayHaveCompleted_UseUserData0_test( *args ):
  # Identical completions but we specify the first one via user_data.
  completions = [
    BuildCompletionNamespace( 'namespace1' ),
    BuildCompletionNamespace( 'namespace2' )
  ]

  with _SetupForCsharpCompletionDone( completions ) as request:
    eq_( request._GetCompletionsUserMayHaveCompleted(),
         [ BuildCompletionNamespace( 'namespace1' ) ] )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='1' ) )
def GetCompletionsUserMayHaveCompleted_UseUserData1_test( *args ):
  # Identical completions but we specify the second one via user_data.
  completions = [
    BuildCompletionNamespace( 'namespace1' ),
    BuildCompletionNamespace( 'namespace2' )
  ]

  with _SetupForCsharpCompletionDone( completions ) as request:
    eq_( request._GetCompletionsUserMayHaveCompleted(),
         [ BuildCompletionNamespace( 'namespace2' ) ] )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='' ) )
def GetCompletionsUserMayHaveCompleted_EmptyUserData_test( *args ):
  # Identical completions but none is selected.
  completions = [
    BuildCompletionNamespace( 'namespace1' ),
    BuildCompletionNamespace( 'namespace2' )
  ]

  with _SetupForCsharpCompletionDone( completions ) as request:
    eq_( request._GetCompletionsUserMayHaveCompleted(), [] )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def PostCompleteCsharp_EmptyDoesntInsertNamespace_test( *args ):
  with _SetupForCsharpCompletionDone( [] ) as request:
    request._OnCompleteDone_Csharp()
    ok_( not vimsupport.InsertNamespace.called )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace_test(
    *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    request._OnCompleteDone_Csharp()
    ok_( not vimsupport.InsertNamespace.called )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def PostCompleteCsharp_ValueDoesInsertNamespace_test( *args ):
  namespace = 'A_NAMESPACE'
  completions = [ BuildCompletionNamespace( namespace ) ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    request._OnCompleteDone_Csharp()
    vimsupport.InsertNamespace.assert_called_once_with( namespace )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.PresentDialog', return_value = 1 )
def PostCompleteCsharp_InsertSecondNamespaceIfSelected_test( *args ):
  namespace = 'A_NAMESPACE'
  namespace2 = 'ANOTHER_NAMESPACE'
  completions = [
    BuildCompletionNamespace( namespace ),
    BuildCompletionNamespace( namespace2 ),
  ]
  with _SetupForCsharpCompletionDone( completions ) as request:
    request._OnCompleteDone_Csharp()
    vimsupport.InsertNamespace.assert_called_once_with( namespace2 )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_NoFixIts_test( replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [] )
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_not_called()


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_EmptyFixIt_test( replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': [] } ] )
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_called_once_with( [], silent = True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_NoFixIt_test( replace_chunks, *args ):
  completions = [
    BuildCompletion()
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_not_called()


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_PickFirst_test( replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_called_once_with( 'one', silent = True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='0' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_PickFirstUserData_test( replace_chunks,
                                                         *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_called_once_with( 'one', silent = True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='1' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
def PostCompleteFixIt_ApplyFixIt_PickSecond_test( replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( completions ) as request:
    request._OnCompleteDone_FixIt()
    replace_chunks.assert_called_once_with( 'two', silent = True )
