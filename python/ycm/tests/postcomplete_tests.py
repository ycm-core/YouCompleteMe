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

from mock import MagicMock
from nose.tools import eq_
from hamcrest import assert_that, empty
from ycm import vimsupport
from ycm.youcompleteme import YouCompleteMe

def GetCompleteDoneHooks_ResultOnCsharp_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "cs" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  result = ycm_state.GetCompleteDoneHooks()
  eq_( 1, len( list( result ) ) )


def GetCompleteDoneHooks_EmptyOnOtherFiletype_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "txt" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  result = ycm_state.GetCompleteDoneHooks()
  eq_( 0, len( list( result ) ) )


def OnCompleteDone_WithActionCallsIt_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "txt" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  action = MagicMock()
  ycm_state._complete_done_hooks[ "txt" ] = action
  ycm_state.OnCompleteDone()

  assert action.called


def OnCompleteDone_NoActionNoError_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "txt" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  ycm_state.OnCompleteDone()


def FilterToCompletionsMatchingOnCursor_MatchIsReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Test" )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state.FilterToCompletionsMatchingOnCursor( completions )

  eq_( list( result ), completions )


def FilterToCompletionsMatchingOnCursor_ShortTextDoesntRaise_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "X" )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state.FilterToCompletionsMatchingOnCursor( completions )


def FilterToCompletionsMatchingOnCursor_ExactMatchIsReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "Test" )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state.FilterToCompletionsMatchingOnCursor( completions )

  eq_( list( result ), completions )


def FilterToCompletionsMatchingOnCursor_NonMatchIsntReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Quote" )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state.FilterToCompletionsMatchingOnCursor( completions )

  assert_that( list( result ), empty() )


def HasCompletionsThatCouldMatchOnCursorWithMoreText_MatchIsReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Te" )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state.HasCompletionsThatCouldMatchOnCursorWithMoreText( completions )

  eq_( result, True )


def HasCompletionsThatCouldMatchOnCursorWithMoreText_ShortTextDoesntRaise_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "X" )
  completions = [ _BuildCompletion( "AAA" ) ]

  ycm_state.HasCompletionsThatCouldMatchOnCursorWithMoreText( completions )


def HasCompletionsThatCouldMatchOnCursorWithMoreText_ExactMatchIsntReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "Test" )
  completions = [ _BuildCompletion( "Test" ) ]

  result = ycm_state.HasCompletionsThatCouldMatchOnCursorWithMoreText( completions )

  eq_( result, False )


def HasCompletionsThatCouldMatchOnCursorWithMoreText_NonMatchIsntReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Quote" )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state.HasCompletionsThatCouldMatchOnCursorWithMoreText( completions )

  eq_( result, False )


def GetRequiredNamespaceImport_ReturnNoneForNoExtraData_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( None, ycm_state.GetRequiredNamespaceImport( {} ) )


def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test():
  namespace = "A_NAMESPACE"
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( namespace, ycm_state.GetRequiredNamespaceImport(
    _BuildCompletion( namespace )
  ))


def GetMatchingCompletionsOnCursor_ReturnEmptyIfNotDone_test():
  ycm_state = _SetupForCsharpCompletionDone( [] )
  ycm_state._latest_completion_request.Done = MagicMock( return_value = False )

  eq_( [], ycm_state.GetMatchingCompletionsOnCursor() )
  

def GetMatchingCompletionsOnCursor_ReturnEmptyIfPendingMatches_test():
  completions = [ _BuildCompletion( None ) ]
  ycm_state = _SetupForCsharpCompletionDone( completions )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Te" )

  eq_( [], ycm_state.GetMatchingCompletionsOnCursor() )


def GetMatchingCompletionsOnCursor_ReturnMatchIfMatches_test():
  completions = [ _BuildCompletion( None ) ]
  ycm_state = _SetupForCsharpCompletionDone( completions )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Test" )

  eq_( completions, ycm_state.GetMatchingCompletionsOnCursor() )


def PostCompleteCsharp_EmptyDoesntInsertNamespace_test():
  ycm_state = _SetupForCsharpCompletionDone( [] )

  ycm_state.OnCompleteDone_Csharp()

  assert not vimsupport.InsertNamespace.called


def PostCompleteCsharp_ExistingWithoutNamespaceDoesntInsertNamespace_test():
  completions = [ _BuildCompletion( None ) ]
  ycm_state = _SetupForCsharpCompletionDone( completions )

  ycm_state.OnCompleteDone_Csharp()

  assert not vimsupport.InsertNamespace.called


def PostCompleteCsharp_ValueDoesInsertNamespace_test():
  namespace = "A_NAMESPACE"
  completions = [ _BuildCompletion( namespace ) ]
  ycm_state = _SetupForCsharpCompletionDone( completions )

  ycm_state.OnCompleteDone_Csharp()

  vimsupport.InsertNamespace.assert_called_once_with( namespace )

def PostCompleteCsharp_InsertSecondNamespaceIfSelected_test():
  namespace = "A_NAMESPACE"
  namespace2 = "ANOTHER_NAMESPACE"
  completions = [
    _BuildCompletion( namespace ),
    _BuildCompletion( namespace2 ),
  ]
  ycm_state = _SetupForCsharpCompletionDone( completions )
  vimsupport.PresentDialog = MagicMock( return_value = 1 )

  ycm_state.OnCompleteDone_Csharp()

  vimsupport.InsertNamespace.assert_called_once_with( namespace2 )


def _SetupForCsharpCompletionDone( completions ):
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  request = MagicMock();
  request.Done = MagicMock( return_value = True )
  request.RawResponse = MagicMock( return_value = completions )
  ycm_state._latest_completion_request = request
  vimsupport.InsertNamespace = MagicMock()
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Test" )
  return ycm_state


def _BuildCompletion( namespace ):
  return {
    'extra_data': { 'required_namespace_import' : namespace },
    'insertion_text': 'Test'
  }
