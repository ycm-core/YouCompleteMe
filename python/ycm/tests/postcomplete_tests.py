#!/usr/bin/env python
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

from ycm.test_utils import MockVimModule
MockVimModule()

from mock import ( MagicMock, DEFAULT, patch )
from nose.tools import eq_
from hamcrest import assert_that, empty
from ycm import vimsupport
from ycm.youcompleteme import YouCompleteMe

import contextlib

def GetVariableValue_CompleteItemIs( word, abbr = None, menu = None,
                                     info = None, kind = None ):
  def Result( variable ):
    if variable == 'v:completed_item':
      return {
        'word': word,
        'abbr': abbr,
        'menu': menu,
        'info': info,
        'kind': kind,
      }
    else:
      return DEFAULT
  return MagicMock( side_effect = Result )


@contextlib.contextmanager
def _SetupForCsharpCompletionDone( completions ):
  with patch( 'ycm.vimsupport.InsertNamespace' ):
    with patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Test' ):
      ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
      request = MagicMock();
      request.Done = MagicMock( return_value = True )
      request.RawResponse = MagicMock( return_value = completions )
      ycm_state._latest_completion_request = request
      yield ycm_state


def _BuildCompletion( namespace = None, insertion_text = 'Test',
                      menu_text = None, extra_menu_info = None,
                      detailed_info = None, kind = None ):
  return {
    'extra_data': { 'required_namespace_import' : namespace },
    'insertion_text': insertion_text,
    'menu_text': menu_text,
    'extra_menu_info': extra_menu_info,
    'kind': kind,
    'detailed_info': detailed_info,
  }


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ "cs" ] )
def GetCompleteDoneHooks_ResultOnCsharp_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  result = ycm_state.GetCompleteDoneHooks()
  eq_( 1, len( list( result ) ) )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ "txt" ] )
def GetCompleteDoneHooks_EmptyOnOtherFiletype_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  result = ycm_state.GetCompleteDoneHooks()
  eq_( 0, len( list( result ) ) )


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ "txt" ] )
def OnCompleteDone_WithActionCallsIt_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  action = MagicMock()
  ycm_state._complete_done_hooks[ "txt" ] = action
  ycm_state.OnCompleteDone()

  assert action.called


@patch( 'ycm.vimsupport.CurrentFiletypes', return_value = [ "txt" ] )
def OnCompleteDone_NoActionNoError_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  ycm_state.OnCompleteDone()


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def FilterToCompletedCompletions_NewVim_MatchIsReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  eq_( list( result ), completions )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'A' ) )
def FilterToCompletedCompletions_NewVim_ShortTextDoesntRaise_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state._FilterToMatchingCompletions( completions, False )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( 'Test' ) )
def FilterToCompletedCompletions_NewVim_ExactMatchIsReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  eq_( list( result ), completions )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( '   Quote' ) )
def FilterToCompletedCompletions_NewVim_NonMatchIsntReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  assert_that( list( result ), empty() )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Test" )
def FilterToCompletedCompletions_OldVim_MatchIsReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  eq_( list( result ), completions )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "X" )
def FilterToCompletedCompletions_OldVim_ShortTextDoesntRaise_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state._FilterToMatchingCompletions( completions, False )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "Test" )
def FilterToCompletedCompletions_OldVim_ExactMatchIsReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  eq_( list( result ), completions )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Quote" )
def FilterToCompletedCompletions_OldVim_NonMatchIsntReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state._FilterToMatchingCompletions( completions, False )

  assert_that( list( result ), empty() )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Te" )
def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_MatchIsReturned_test(
    *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, True )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "X" )
def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_ShortTextDoesntRaise_test( *args ) :
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "Test" )
def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_ExactMatchIsntReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, False )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Quote" )
def HasCompletionsThatCouldBeCompletedWithMoreText_OldVim_NonMatchIsntReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, False )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( "Te") )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Quote" )
def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_MatchIsReturned_test(
    *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, True )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( "X") )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = "   Quote" )
def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_ShortTextDoesntRaise_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( "Test" ) )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_ExactMatchIsntReturned_test(
    *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, False )


@patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True )
@patch( 'ycm.vimsupport.GetVariableValue',
        GetVariableValue_CompleteItemIs( "   Quote" ) )
@patch( 'ycm.vimsupport.TextBeforeCursor', return_value = '   Quote' )
def HasCompletionsThatCouldBeCompletedWithMoreText_NewVim_NonMatchIsntReturned_test( *args ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state._HasCompletionsThatCouldBeCompletedWithMoreText( completions )

  eq_( result, False )


def GetRequiredNamespaceImport_ReturnNoneForNoExtraData_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( None, ycm_state._GetRequiredNamespaceImport( {} ) )


def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test():
  namespace = "A_NAMESPACE"
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( namespace, ycm_state._GetRequiredNamespaceImport(
    _BuildCompletion( namespace )
  ))


def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfNotDone_test():
  with _SetupForCsharpCompletionDone( [] ) as ycm_state:
    ycm_state._latest_completion_request.Done = MagicMock( return_value = False )

    eq_( [], ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_NewVim_test():
  completions = [ _BuildCompletion( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( 'Te' ) ):
        eq_( [], ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnEmptyIfPendingMatches_OldVim_test(
    *args ):
  completions = [ _BuildCompletion( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( 'Te' ) ):
        eq_( [], ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatches_NewVim_test(
    *args ):
  info = [ "NS","Test", "Abbr", "Menu", "Info", "Kind" ]
  completions = [ _BuildCompletion( *info ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( completions, ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfExactMatchesEvenIfPartial_NewVim_test( *args ):
  info = [ "NS", "Test", "Abbr", "Menu", "Info", "Kind" ]
  completions = [ _BuildCompletion( *info ),
                  _BuildCompletion( insertion_text = "TestTest" ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( [ completions[ 0 ] ],
             ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_DontReturnMatchIfNontExactMatchesAndPartial_NewVim_test():
  info = [ "NS", "Test", "Abbr", "Menu", "Info", "Kind" ]
  completions = [ _BuildCompletion( insertion_text = info[ 0 ] ),
                  _BuildCompletion( insertion_text = "TestTest" ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( *info[ 1: ] ) ):
        eq_( [], ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_NewVim_test( *args ):
  completions = [ _BuildCompletion( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = True ):
      with patch( 'ycm.vimsupport.GetVariableValue',
                  GetVariableValue_CompleteItemIs( "Test" ) ):
        eq_( completions, ycm_state.GetCompletionsUserMayHaveCompleted() )


def GetCompletionsUserMayHaveCompleted_ReturnMatchIfMatches_OldVim_test( *args ):
  completions = [ _BuildCompletion( None ) ]
  ycm_state = _SetupForCsharpCompletionDone( completions )
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False ):
      eq_( completions, ycm_state.GetCompletionsUserMayHaveCompleted() )


def PostCompleteCsharp_EmptyDoesntInsertNamespace_test( *args ):
  with _SetupForCsharpCompletionDone( [] ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False ):
      ycm_state._OnCompleteDone_Csharp()

    assert not vimsupport.InsertNamespace.called


def PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace_test( *args
    ):
  completions = [ _BuildCompletion( None ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False ):
      ycm_state._OnCompleteDone_Csharp()

    assert not vimsupport.InsertNamespace.called


def PostCompleteCsharp_ValueDoesInsertNamespace_test( *args ):
  namespace = "A_NAMESPACE"
  completions = [ _BuildCompletion( namespace ) ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False ):
      ycm_state._OnCompleteDone_Csharp()

      vimsupport.InsertNamespace.assert_called_once_with( namespace )

def PostCompleteCsharp_InsertSecondNamespaceIfSelected_test( *args ):
  namespace = "A_NAMESPACE"
  namespace2 = "ANOTHER_NAMESPACE"
  completions = [
    _BuildCompletion( namespace ),
    _BuildCompletion( namespace2 ),
  ]
  with _SetupForCsharpCompletionDone( completions ) as ycm_state:
    with patch( 'ycm.vimsupport.VimVersionAtLeast', return_value = False ):
      with patch( 'ycm.vimsupport.PresentDialog', return_value = 1 ):
        ycm_state._OnCompleteDone_Csharp()

        vimsupport.InsertNamespace.assert_called_once_with( namespace2 )
