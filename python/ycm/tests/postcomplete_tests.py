# encoding: utf-8
#
# Copyright (C) 2015 YouCompleteMe contributors
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
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycm.test_utils import MockVimModule
MockVimModule()

import contextlib
from hamcrest import assert_that, empty
from mock import MagicMock, DEFAULT, patch
from nose.tools import eq_, ok_

from ycm import vimsupport
from ycm.tests.server_test import Server_test
from ycmd.utils import ToBytes


def GetVariableValue_CompleteItemIs( word, abbr = None, menu = None,
                                     info = None, kind = None ):
  def Result( variable ):
    if variable == 'v:completed_item':
      return {
        'word': ToBytes( word ),
        'abbr': ToBytes( abbr ),
        'menu': ToBytes( menu ),
        'info': ToBytes( info ),
        'kind': ToBytes( kind ),
      }
    return DEFAULT
  return MagicMock( side_effect = Result )


def BuildCompletion( namespace = None, insertion_text = 'Test',
                     menu_text = None, extra_menu_info = None,
                     detailed_info = None, kind = None ):
  return {
    'extra_data': { 'required_namespace_import': namespace },
    'insertion_text': insertion_text,
    'menu_text': menu_text,
    'extra_menu_info': extra_menu_info,
    'kind': kind,
    'detailed_info': detailed_info,
  }


class PostComplete_test( Server_test ):

  @contextlib.contextmanager
  def _SetupForCsharpCompletionDone( self, completions ):
    with patch( 'ycm.vimsupport.InsertNamespace' ):
      with patch( 'ycm.vimsupport.TextBeforeCursor',
                  return_value = '   Test' ):
        request = MagicMock()
        request.Done = MagicMock( return_value = True )
        request.RawResponse = MagicMock( return_value = completions )
        self._server_state._latest_completion_request = request
        yield


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'cs' ] )
  def GetCompleteDoneHooks_ResultOnCsharp_test( self, *args ):
    result = self._server_state.GetCompleteDoneHooks()
    eq_( 1, len( list( result ) ) )


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'txt' ] )
  def GetCompleteDoneHooks_EmptyOnOtherFiletype_test( self, *args ):
    result = self._server_state.GetCompleteDoneHooks()
    eq_( 0, len( list( result ) ) )


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'txt' ] )
  def OnCompleteDone_WithActionCallsIt_test( self, *args ):
    action = MagicMock()
    self._server_state._complete_done_hooks[ 'txt' ] = action
    self._server_state.OnCompleteDone()

    ok_( action.called )


  @patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ 'txt' ] )
  def OnCompleteDone_NoActionNoError_test( self, *args ):
    self._server_state.OnCompleteDone()


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def FilterToCompletedCompletions_NewVim_MatchIsReturned_test( self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    eq_( list( result ), completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'A' ) )
  def FilterToCompletedCompletions_NewVim_ShortTextDoesntRaise_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
    self._server_state._FilterToMatchingCompletions( completions, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def FilterToCompletedCompletions_NewVim_ExactMatchIsReturned_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    eq_( list( result ), completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( '   Quote' ) )
  def FilterToCompletedCompletions_NewVim_NonMatchIsntReturned_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'A' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    assert_that( list( result ), empty() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( '†es†' ) )
  def FilterToCompletedCompletions_NewVim_Unicode_test( self, *args ):
    completions = [ BuildCompletion( insertion_text = '†es†' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    eq_( list( result ), completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Test' )
  def FilterToCompletedCompletions_OldVim_MatchIsReturned_test( self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    eq_( list( result ), completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'X' )
  def FilterToCompletedCompletions_OldVim_ShortTextDoesntRaise_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
    self._server_state._FilterToMatchingCompletions( completions, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Test' )
  def FilterToCompletedCompletions_OldVim_ExactMatchIsReturned_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    eq_( list( result ), completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def FilterToCompletedCompletions_OldVim_NonMatchIsntReturned_test( self,
                                                                     *args ):
    completions = [ BuildCompletion( insertion_text = 'A' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    assert_that( list( result ), empty() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Uniçø∂¢' )
  def FilterToCompletedCompletions_OldVim_Unicode_test( self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Uniçø∂¢' ) ]
    result = self._server_state._FilterToMatchingCompletions( completions,
                                                              False )
    assert_that( list( result ), empty() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Te' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_MatchIsReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, True )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'X' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_ShortTextDoesntRaise_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = "AAA" ) ]
    self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                               completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Test' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_ExactMatchIsntReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_NonMatchIsntReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'A' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Uniç' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_Unicode_test(
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Uniçø∂¢' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, True )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Te' ) )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_MatchIsReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, True )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'X' ) )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_ShortTextDoesntRaise_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'AAA' ) ]
    self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_ExactMatchIsntReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = 'Test' ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( '   Quote' ) )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_NonMatchIsntReturned_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( insertion_text = "A" ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, False )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Uniç' ) )
  @patch( 'ycm.vimsupport.TextBeforeCursor', return_value = 'Uniç' )
  def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_Unicode_test(
    self, *args ):
    completions = [ BuildCompletion( insertion_text = "Uniçø∂¢" ) ]
    result = self._server_state._HasCompletionsThatCouldBeCompletedWithMoreText(
                                                                completions )
    eq_( result, True )


  def GetRequiredNamespaceImport_ReturnNoneForNoExtraData_test( self ):
    eq_( None, self._server_state._GetRequiredNamespaceImport( {} ) )


  def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test( self ):
    namespace = 'A_NAMESPACE'
    eq_( namespace, self._server_state._GetRequiredNamespaceImport(
      BuildCompletion( namespace )
    ) )


  def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfNotDone_test( self ):
    with self._SetupForCsharpCompletionDone( [] ):
      self._server_state._latest_completion_request.Done = MagicMock(
        return_value = False )
      eq_( [], self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Te' ) )
  def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_NewVim_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( None ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      eq_( [], self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_OldVim_test( # noqa
    self, *args ):
    completions = [ BuildCompletion( None ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      with patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Te' ):
        eq_( [], self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatches_NewVim_test(
    self, *args ):
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletion( *info ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( completions,
             self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatchesEvenIfPartial_NewVim_test( # noqa
    self, *args ):
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletion( *info ),
                    BuildCompletion( insertion_text = 'TestTest' ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( [ completions[ 0 ] ],
               self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  def GetCompletionsUserMayHaveCompleted_DontReturnMatchIfNontExactMatchesAndPartial_NewVim_test( # noqa
    self, *args ):
    info = [ 'NS', 'Test', 'Abbr', 'Menu', 'Info', 'Kind' ]
    completions = [ BuildCompletion( insertion_text = info[ 0 ] ),
                    BuildCompletion( insertion_text = 'TestTest' ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( [], self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
  @patch( 'ycm.vimsupport.GetVariableValue',
          GetVariableValue_CompleteItemIs( 'Test' ) )
  def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_NewVim_test(
    self, *args ):
    completions = [ BuildCompletion( None ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      eq_( completions,
           self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_OldVim_test(
    self, *args ):
    completions = [ BuildCompletion( None ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      eq_( completions,
           self._server_state.GetCompletionsUserMayHaveCompleted() )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  def PostCompleteCsharp_EmptyDoesntInsertNamespace_test( self, *args ):
    with self._SetupForCsharpCompletionDone( [] ):
      self._server_state._OnCompleteDone_Csharp()
      ok_( not vimsupport.InsertNamespace.called )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  def PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace_test(
    self, *args ):
    completions = [ BuildCompletion( None ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      self._server_state._OnCompleteDone_Csharp()
      ok_( not vimsupport.InsertNamespace.called )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  def PostCompleteCsharp_ValueDoesInsertNamespace_test( self, *args ):
    namespace = 'A_NAMESPACE'
    completions = [ BuildCompletion( namespace ) ]
    with self._SetupForCsharpCompletionDone( completions ):
      self._server_state._OnCompleteDone_Csharp()
      vimsupport.InsertNamespace.assert_called_once_with( namespace )


  @patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
  @patch( 'ycm.vimsupport.PresentDialog', return_value = 1 )
  def PostCompleteCsharp_InsertSecondNamespaceIfSelected_test( self, *args ):
    namespace = 'A_NAMESPACE'
    namespace2 = 'ANOTHER_NAMESPACE'
    completions = [
      BuildCompletion( namespace ),
      BuildCompletion( namespace2 ),
    ]
    with self._SetupForCsharpCompletionDone( completions ):
      self._server_state._OnCompleteDone_Csharp()
      vimsupport.InsertNamespace.assert_called_once_with( namespace2 )
