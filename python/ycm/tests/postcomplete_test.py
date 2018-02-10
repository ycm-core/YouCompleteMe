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
from hamcrest import assert_that, empty
from mock import MagicMock, DEFAULT, patch
from nose.tools import eq_, ok_

from ycm import vimsupport
from ycm.tests import YouCompleteMeInstance
from ycmd.utils import ToBytes

from ycm.youcompleteme import _CompleteDoneHook_CSharp
from ycm.youcompleteme import _CompleteDoneHook_Java


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
def _SetupForCsharpCompletionDone( ycm, completions ):
  with patch( 'ycm.vimsupport.InsertNamespace' ):
    with _SetUpCompleteDone( ycm, completions ):
      yield


@contextlib.contextmanager
def _SetUpCompleteDone( ycm, completions ):
  with patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Test' ):
    request = MagicMock()
    request.Done = MagicMock( return_value = True )
    request.RawResponse = MagicMock( return_value = {
      'completions': completions
    } )
    ycm._latest_completion_request = request
    yield


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'cs' ] )
@YouCompleteMeInstance()
def GetCompleteDoneHooks_ResultOnCsharp_test( ycm, *args ):
  result = list( ycm.GetCompleteDoneHooks() )
  eq_( [ _CompleteDoneHook_CSharp ], result )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'java' ] )
@YouCompleteMeInstance()
def GetCompleteDoneHooks_ResultOnJava_test( ycm, *args ):
  result = list( ycm.GetCompleteDoneHooks() )
  eq_( [ _CompleteDoneHook_Java ], result )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
@YouCompleteMeInstance()
def GetCompleteDoneHooks_EmptyOnOtherFiletype_test( ycm, *args ):
  result = ycm.GetCompleteDoneHooks()
  eq_( 0, len( list( result ) ) )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
@YouCompleteMeInstance()
def OnCompleteDone_WithActionCallsIt_test( ycm, *args ):
  action = MagicMock()
  ycm._complete_done_hooks[ 'ycmtest' ] = action
  ycm.OnCompleteDone()
  ok_( action.called )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
@YouCompleteMeInstance()
def OnCompleteDone_NoActionNoError_test( ycm, *args ):
  with patch.object( ycm, '_OnCompleteDone_Csharp' ) as csharp:
    with patch.object( ycm, '_OnCompleteDone_Java' ) as java:
      ycm.OnCompleteDone()
      csharp.assert_not_called()
      java.assert_not_called()


@YouCompleteMeInstance()
def FilterToCompletedCompletions_MatchIsReturned_test( ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = ycm._FilterToMatchingCompletions( CompleteItemIs( 'Test' ),
                                             completions,
                                             False )
  eq_( list( result ), completions )


@YouCompleteMeInstance()
def FilterToCompletedCompletions_ShortTextDoesntRaise_test( ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
  ycm._FilterToMatchingCompletions( CompleteItemIs( 'A' ),
                                    completions,
                                    False )


@YouCompleteMeInstance()
def FilterToCompletedCompletions_ExactMatchIsReturned_test( ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = ycm._FilterToMatchingCompletions( CompleteItemIs( 'Test' ),
                                             completions,
                                             False )
  eq_( list( result ), completions )


@YouCompleteMeInstance()
def FilterToCompletedCompletions_NonMatchIsntReturned_test( ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'A' ) ]
  result = ycm._FilterToMatchingCompletions( CompleteItemIs( '   Quote' ),
                                             completions,
                                             False )
  assert_that( list( result ), empty() )


@YouCompleteMeInstance()
def FilterToCompletedCompletions_Unicode_test( ycm, *args ):
  completions = [ BuildCompletion( insertion_text = '†es†' ) ]
  result = ycm._FilterToMatchingCompletions( CompleteItemIs( '†es†' ),
                                             completions,
                                             False )
  eq_( list( result ), completions )


@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
@YouCompleteMeInstance()
def HasCompletionsThatCouldBeCompletedWithMoreText_MatchIsReturned_test(
    ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = ycm._HasCompletionsThatCouldBeCompletedWithMoreText(
    CompleteItemIs( 'Te' ),
    completions )
  eq_( result, True )


@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
@YouCompleteMeInstance()
def HasCompletionsThatCouldBeCompletedWithMoreText_ShortTextDoesntRaise_test(
    ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
  ycm._HasCompletionsThatCouldBeCompletedWithMoreText( CompleteItemIs( 'X' ),
                                                       completions )


@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
@YouCompleteMeInstance()
def HasCompletionsThatCouldBeCompletedWithMoreText_ExactMatchIsntReturned_test(
    ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'Test' ) ]
  result = ycm._HasCompletionsThatCouldBeCompletedWithMoreText(
    CompleteItemIs( 'Test' ),
    completions )
  eq_( result, False )


@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
@YouCompleteMeInstance()
def HasCompletionsThatCouldBeCompletedWithMoreText_NonMatchIsntReturned_test(
    ycm, *args ):
  completions = [ BuildCompletion( insertion_text = "A" ) ]
  result = ycm._HasCompletionsThatCouldBeCompletedWithMoreText(
    CompleteItemIs( '   Quote' ),
    completions )
  eq_( result, False )


@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Uniç' )
@YouCompleteMeInstance()
def HasCompletionsThatCouldBeCompletedWithMoreText_Unicode_test(
    ycm, *args ):
  completions = [ BuildCompletion( insertion_text = 'Uniçø∂¢' ) ]
  result = ycm._HasCompletionsThatCouldBeCompletedWithMoreText(
    CompleteItemIs( 'Uniç' ),
    completions )
  eq_( result, True )


@YouCompleteMeInstance()
def GetRequiredNamespaceImport_ReturnNoneForNoExtraData_test( ycm ):
  eq_( None, ycm._GetRequiredNamespaceImport( {} ) )


@YouCompleteMeInstance()
def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test( ycm ):
  namespace = 'A_NAMESPACE'
  eq_( namespace, ycm._GetRequiredNamespaceImport(
    BuildCompletionNamespace( namespace )
  ) )


@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfNotDone_test( ycm ):
  with _SetupForCsharpCompletionDone( ycm, [] ):
    ycm._latest_completion_request.Done = MagicMock( return_value = False )
    eq_( [], ycm.GetCompletionsUserMayHaveCompleted() )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Te' ) )
@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_test(
    ycm, *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    eq_( [], ycm.GetCompletionsUserMayHaveCompleted() )


@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatches_test(
    ycm, *args ):
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletionNamespace( *info ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( completions, ycm.GetCompletionsUserMayHaveCompleted() )


@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatchesEvenIfPartial_test( # noqa
    ycm, *args ):
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletionNamespace( *info ),
                  BuildCompletion( insertion_text = 'TestTest' ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( [ completions[ 0 ] ], ycm.GetCompletionsUserMayHaveCompleted() )


@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_DontReturnMatchIfNoExactMatchesAndPartial_test( # noqa
    ycm, *args ):
  info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
  completions = [ BuildCompletion( insertion_text = info[ 0 ] ),
                  BuildCompletion( insertion_text = 'TestTest' ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    with patch( 'ycm.vimsupport.GetVariableValue',
                GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
      eq_( [], ycm.GetCompletionsUserMayHaveCompleted() )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_test( ycm, *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    eq_( completions, ycm.GetCompletionsUserMayHaveCompleted() )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='0' ) )
@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_UseUserData0_test( ycm, *args ):
  # identical completions but we specify the first one via user_data
  completions = [
    BuildCompletionNamespace( 'namespace1' ),
    BuildCompletionNamespace( 'namespace2' )
  ]

  with _SetupForCsharpCompletionDone( ycm, completions ):
    eq_( [ BuildCompletionNamespace( 'namespace1' ) ],
         ycm.GetCompletionsUserMayHaveCompleted() )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='1' ) )
@YouCompleteMeInstance()
def GetCompletionsUserMayHaveCompleted_UseUserData1_test( ycm, *args ):
  # identical completions but we specify the second one via user_data
  completions = [
    BuildCompletionNamespace( 'namespace1' ),
    BuildCompletionNamespace( 'namespace2' )
  ]

  with _SetupForCsharpCompletionDone( ycm, completions ):
    eq_( [ BuildCompletionNamespace( 'namespace2' ) ],
         ycm.GetCompletionsUserMayHaveCompleted() )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@YouCompleteMeInstance()
def PostCompleteCsharp_EmptyDoesntInsertNamespace_test( ycm, *args ):
  with _SetupForCsharpCompletionDone( ycm, [] ):
    ycm._OnCompleteDone_Csharp()
    ok_( not vimsupport.InsertNamespace.called )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@YouCompleteMeInstance()
def PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace_test(
    ycm, *args ):
  completions = [ BuildCompletionNamespace( None ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    ycm._OnCompleteDone_Csharp()
    ok_( not vimsupport.InsertNamespace.called )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@YouCompleteMeInstance()
def PostCompleteCsharp_ValueDoesInsertNamespace_test( ycm, *args ):
  namespace = 'A_NAMESPACE'
  completions = [ BuildCompletionNamespace( namespace ) ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    ycm._OnCompleteDone_Csharp()
    vimsupport.InsertNamespace.assert_called_once_with( namespace )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.PresentDialog', return_value = 1 )
@YouCompleteMeInstance()
def PostCompleteCsharp_InsertSecondNamespaceIfSelected_test( ycm, *args ):
  namespace = 'A_NAMESPACE'
  namespace2 = 'ANOTHER_NAMESPACE'
  completions = [
    BuildCompletionNamespace( namespace ),
    BuildCompletionNamespace( namespace2 ),
  ]
  with _SetupForCsharpCompletionDone( ycm, completions ):
    ycm._OnCompleteDone_Csharp()
    vimsupport.InsertNamespace.assert_called_once_with( namespace2 )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_NoFixIts_test( ycm, replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [] )
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_not_called()


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_EmptyFixIt_test( ycm, replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': [] } ] )
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_called_once_with( [], silent=True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_NoFixIt_test( ycm, replace_chunks, *args ):
  completions = [
    BuildCompletion( )
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_not_called()


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_PickFirst_test( ycm, replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_called_once_with( 'one', silent=True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='0' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_PickFirstUserData_test( ycm,
                                                        replace_chunks,
                                                        *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_called_once_with( 'one', silent=True )


@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test', user_data='1' ) )
@patch( 'ycm.vimsupport.ReplaceChunks' )
@YouCompleteMeInstance()
def PostCompleteJava_ApplyFixIt_PickSecond_test( ycm, replace_chunks, *args ):
  completions = [
    BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
    BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
  ]
  with _SetUpCompleteDone( ycm, completions ):
    ycm._OnCompleteDone_Java()
    replace_chunks.assert_called_once_with( 'two', silent=True )
