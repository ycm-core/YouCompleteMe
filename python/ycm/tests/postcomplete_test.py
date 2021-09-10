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

from ycm.tests.test_utils import MockVimModule
MockVimModule()

import contextlib
import json
from hamcrest import assert_that, contains_exactly, empty, equal_to, none
from unittest import TestCase
from unittest.mock import MagicMock, DEFAULT, patch

from ycm import vimsupport
from ycmd.utils import ToBytes
from ycm.client.completion_request import ( CompletionRequest,
                                            _FilterToMatchingCompletions,
                                            _GetRequiredNamespaceImport )
from ycm.client.omni_completion_request import OmniCompletionRequest


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
  completion = {
    'insertion_text': insertion_text
  }

  if extra_menu_info:
    completion[ 'extra_menu_info' ] = extra_menu_info
  if menu_text:
    completion[ 'menu_text' ] = menu_text
  if detailed_info:
    completion[ 'detailed_info' ] = detailed_info
  if kind:
    completion[ 'kind' ] = kind
  if extra_data:
    completion[ 'extra_data' ] = extra_data
  return completion


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
    request._RawResponse = MagicMock( return_value = {
      'completions': completions
    } )
    yield request


class PostcompleteTest( TestCase ):
  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
  def test_OnCompleteDone_DefaultFixIt( self, *args ):
    request = CompletionRequest( None )
    request.Done = MagicMock( return_value = True )
    request._OnCompleteDone_Csharp = MagicMock()
    request._OnCompleteDone_FixIt = MagicMock()
    request.OnCompleteDone()
    request._OnCompleteDone_Csharp.assert_not_called()
    request._OnCompleteDone_FixIt.assert_called_once_with()


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'cs' ] )
  def test_OnCompleteDone_CsharpFixIt( self, *args ):
    request = CompletionRequest( None )
    request.Done = MagicMock( return_value = True )
    request._OnCompleteDone_Csharp = MagicMock()
    request._OnCompleteDone_FixIt = MagicMock()
    request.OnCompleteDone()
    request._OnCompleteDone_Csharp.assert_called_once_with()
    request._OnCompleteDone_FixIt.assert_not_called()


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
  def test_OnCompleteDone_NoFixItIfNotDone( self, *args ):
    request = CompletionRequest( None )
    request.Done = MagicMock( return_value = False )
    request._OnCompleteDone_Csharp = MagicMock()
    request._OnCompleteDone_FixIt = MagicMock()
    request.OnCompleteDone()
    request._OnCompleteDone_Csharp.assert_not_called()
    request._OnCompleteDone_FixIt.assert_not_called()


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'ycmtest' ] )
  def test_OnCompleteDone_NoFixItForOmnifunc( self, *args ):
    request = OmniCompletionRequest( 'omnifunc', None )
    request.Done = MagicMock( return_value = True )
    request._OnCompleteDone_Csharp = MagicMock()
    request._OnCompleteDone_FixIt = MagicMock()
    request.OnCompleteDone()
    request._OnCompleteDone_Csharp.assert_not_called()
    request._OnCompleteDone_FixIt.assert_not_called()


  def test_FilterToCompletedCompletions_MatchIsReturned( self ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = _FilterToMatchingCompletions( CompleteItemIs( 'Test' ),
                                           completions )
    assert_that( list( result ), contains_exactly( {} ) )


  def test_FilterToCompletedCompletions_ShortTextDoesntRaise( self ):
    completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
    result = _FilterToMatchingCompletions( CompleteItemIs( 'A' ), completions )
    assert_that( list( result ), empty() )


  def test_FilterToCompletedCompletions_ExactMatchIsReturned( self ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = _FilterToMatchingCompletions( CompleteItemIs( 'Test' ),
                                           completions )
    assert_that( list( result ), contains_exactly( {} ) )


  def test_FilterToCompletedCompletions_NonMatchIsntReturned( self ):
    completions = [ BuildCompletion( insertion_text = 'A' ) ]
    result = _FilterToMatchingCompletions( CompleteItemIs( '   Quote' ),
                                           completions )
    assert_that( list( result ), empty() )


  def test_FilterToCompletedCompletions_Unicode( self ):
    completions = [ BuildCompletion( insertion_text = '†es†' ) ]
    result = _FilterToMatchingCompletions( CompleteItemIs( '†es†' ),
                                           completions )
    assert_that( list( result ), contains_exactly( {} ) )


  def test_GetRequiredNamespaceImport_ReturnNoneForNoExtraData( self ):
    assert_that( _GetRequiredNamespaceImport( {} ), none() )


  def test_GetRequiredNamespaceImport_ReturnNamespaceFromExtraData( self ):
    namespace = 'A_NAMESPACE'
    assert_that( _GetRequiredNamespaceImport(
                     BuildCompletionNamespace( namespace )[ 'extra_data' ] ),
                 equal_to( namespace ) )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Te' ) )
  def test_GetExtraDataUserMayHaveCompleted_ReturnEmptyIfPendingMatches(
      *args ):
    completions = [ BuildCompletionNamespace( None ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      assert_that( request._GetExtraDataUserMayHaveCompleted(), empty() )


  def test_GetExtraDataUserMayHaveCompleted_ReturnMatchIfExactMatches(
      self, *args ):
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletionNamespace( *info ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        assert_that( request._GetExtraDataUserMayHaveCompleted(),
                     contains_exactly( completions[ 0 ][ 'extra_data' ] ) )


  def test_GetExtraDataUserMayHaveCompleted_ReturnMatchIfExactMatchesEvenIfPartial( self ): # noqa
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletionNamespace( *info ),
                    BuildCompletion( insertion_text = 'TestTest' ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        assert_that( request._GetExtraDataUserMayHaveCompleted(),
                     contains_exactly( completions[ 0 ][ 'extra_data' ] ) )


  def test_GetExtraDataUserMayHaveCompleted_DontReturnMatchIfNoExactMatchesAndPartial( self ): # noqa
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletion( insertion_text = info[ 0 ] ),
                    BuildCompletion( insertion_text = 'TestTest' ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        assert_that( request._GetExtraDataUserMayHaveCompleted(), empty() )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def test_GetExtraDataUserMayHaveCompleted_ReturnMatchIfMatches( self, *args ):
    completions = [ BuildCompletionNamespace( None ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      assert_that( request._GetExtraDataUserMayHaveCompleted(),
                   contains_exactly( completions[ 0 ][ 'extra_data' ] ) )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs(
            'Test',
            user_data=json.dumps( {
              'required_namespace_import': 'namespace1' } ) ) )
  def test_GetExtraDataUserMayHaveCompleted_UseUserData0( self, *args ):
    # Identical completions but we specify the first one via user_data.
    completions = [
      BuildCompletionNamespace( 'namespace1' ),
      BuildCompletionNamespace( 'namespace2' )
    ]

    with _SetupForCsharpCompletionDone( completions ) as request:
      assert_that(
          request._GetExtraDataUserMayHaveCompleted(),
          contains_exactly(
            BuildCompletionNamespace( 'namespace1' )[ 'extra_data' ] ) )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs(
            'Test',
            user_data=json.dumps( {
              'required_namespace_import': 'namespace2' } ) ) )
  def test_GetExtraDataUserMayHaveCompleted_UseUserData1( self, *args ):
    # Identical completions but we specify the second one via user_data.
    completions = [
      BuildCompletionNamespace( 'namespace1' ),
      BuildCompletionNamespace( 'namespace2' )
    ]

    with _SetupForCsharpCompletionDone( completions ) as request:
      assert_that(
          request._GetExtraDataUserMayHaveCompleted(),
          contains_exactly(
            BuildCompletionNamespace( 'namespace2' )[ 'extra_data' ] ) )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test', user_data='' ) )
  def test_GetExtraDataUserMayHaveCompleted_EmptyUserData( self, *args ):
    # Identical completions but none is selected.
    completions = [
      BuildCompletionNamespace( 'namespace1' ),
      BuildCompletionNamespace( 'namespace2' )
    ]

    with _SetupForCsharpCompletionDone( completions ) as request:
      assert_that( request._GetExtraDataUserMayHaveCompleted(), empty() )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def test_PostCompleteCsharp_EmptyDoesntInsertNamespace( self, *args ):
    with _SetupForCsharpCompletionDone( [] ) as request:
      request._OnCompleteDone_Csharp()
      assert_that( not vimsupport.InsertNamespace.called )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def test_PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace(
      self, *args ):
    completions = [ BuildCompletionNamespace( None ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      request._OnCompleteDone_Csharp()
      assert_that( not vimsupport.InsertNamespace.called )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def test_PostCompleteCsharp_ValueDoesInsertNamespace( self, *args ):
    namespace = 'A_NAMESPACE'
    completions = [ BuildCompletionNamespace( namespace ) ]
    with _SetupForCsharpCompletionDone( completions ) as request:
      request._OnCompleteDone_Csharp()
      vimsupport.InsertNamespace.assert_called_once_with( namespace )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  @patch( 'ycm.vimsupport.PresentDialog', return_value = 1 )
  def test_PostCompleteCsharp_InsertSecondNamespaceIfSelected( self, *args ):
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
  def test_PostCompleteFixIt_ApplyFixIt_NoFixIts( self, replace_chunks, *args ):
    completions = [
      BuildCompletionFixIt( [] )
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_not_called()


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  @patch( 'ycm.vimsupport.ReplaceChunks' )
  def test_PostCompleteFixIt_ApplyFixIt_EmptyFixIt(
      self, replace_chunks, *args ):
    completions = [
      BuildCompletionFixIt( [ { 'chunks': [] } ] )
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_called_once_with( [], silent = True )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  @patch( 'ycm.vimsupport.ReplaceChunks' )
  def test_PostCompleteFixIt_ApplyFixIt_NoFixIt( self, replace_chunks, *args ):
    completions = [
      BuildCompletion()
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_not_called()


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  @patch( 'ycm.vimsupport.ReplaceChunks' )
  def test_PostCompleteFixIt_ApplyFixIt_PickFirst(
      self, replace_chunks, *args ):
    completions = [
      BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
      BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_called_once_with( 'one', silent = True )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs(
            'Test',
            user_data=json.dumps( { 'fixits': [ { 'chunks': 'one' } ] } ) ) )
  @patch( 'ycm.vimsupport.ReplaceChunks' )
  def test_PostCompleteFixIt_ApplyFixIt_PickFirstUserData( self,
                                                           replace_chunks,
                                                           *args ):
    completions = [
      BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
      BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_called_once_with( 'one', silent = True )


  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs(
            'Test',
            user_data=json.dumps( { 'fixits': [ { 'chunks': 'two' } ] } ) ) )
  @patch( 'ycm.vimsupport.ReplaceChunks' )
  def test_PostCompleteFixIt_ApplyFixIt_PickSecond(
      self, replace_chunks, *args ):
    completions = [
      BuildCompletionFixIt( [ { 'chunks': 'one' } ] ),
      BuildCompletionFixIt( [ { 'chunks': 'two' } ] ),
    ]
    with _SetUpCompleteDone( completions ) as request:
      request._OnCompleteDone_FixIt()
      replace_chunks.assert_called_once_with( 'two', silent = True )
