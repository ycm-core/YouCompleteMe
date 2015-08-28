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

from mock import MagicMock
from nose.tools import eq_
from hamcrest import assert_that, empty
from ycm import vimsupport
from ycm.youcompleteme import YouCompleteMe

def HasPostCompletionAction_TrueOnCsharp_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "cs" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  eq_( True, ycm_state.HasPostCompletionAction() )


def HasPostCompletionAction_FalseOnOtherFiletype_test():
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "txt" ] )
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  eq_( False, ycm_state.HasPostCompletionAction() )


def GetRequiredNamespaceImport_ReturnEmptyForNoExtraData_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( "", ycm_state.GetRequiredNamespaceImport( {} ) )


def GetRequiredNamespaceImport_ReturnNamespaceFromExtraData_test():
  namespace = "A_NAMESPACE"
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )

  eq_( namespace, ycm_state.GetRequiredNamespaceImport(
    _BuildCompletion( namespace )
  ))


def FilterMatchingCompletions_MatchIsReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Test" )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state.FilterMatchingCompletions( completions )

  eq_( list( result ), completions )


def FilterMatchingCompletions_ShortTextDoesntRaise_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "X" )
  completions = [ _BuildCompletion( "A" ) ]

  ycm_state.FilterMatchingCompletions( completions )


def FilterMatchingCompletions_ExactMatchIsReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "Test" )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state.FilterMatchingCompletions( completions )

  eq_( list( result ), completions )


def FilterMatchingCompletions_NonMatchIsntReturned_test():
  ycm_state = YouCompleteMe( MagicMock( spec_set = dict ) )
  vimsupport.TextBeforeCursor = MagicMock( return_value = "   Quote" )
  completions = [ _BuildCompletion( "A" ) ]

  result = ycm_state.FilterMatchingCompletions( completions )

  assert_that( list( result ), empty() )


def PostComplete_EmptyDoesntInsertNamespace_test():
  ycm_state = _SetupForCompletionDone( [] )

  ycm_state.OnCompleteDone()

  assert not vimsupport.InsertNamespace.called

def PostComplete_ExistingWithoutNamespaceDoesntInsertNamespace_test():
  completions = [ _BuildCompletion( None ) ]
  ycm_state = _SetupForCompletionDone( completions )

  ycm_state.OnCompleteDone()

  assert not vimsupport.InsertNamespace.called


def PostComplete_ValueDoesInsertNamespace_test():
  namespace = "A_NAMESPACE"
  completions = [ _BuildCompletion( namespace ) ]
  ycm_state = _SetupForCompletionDone( completions )

  ycm_state.OnCompleteDone()

  vimsupport.InsertNamespace.assert_called_once_with( namespace )

def PostComplete_InsertSecondNamespaceIfSelected_test():
  namespace = "A_NAMESPACE"
  namespace2 = "ANOTHER_NAMESPACE"
  completions = [
    _BuildCompletion( namespace ),
    _BuildCompletion( namespace2 ),
  ]
  ycm_state = _SetupForCompletionDone( completions )
  vimsupport.PresentDialog = MagicMock( return_value = 1 )

  ycm_state.OnCompleteDone()

  vimsupport.InsertNamespace.assert_called_once_with( namespace2 )


def _SetupForCompletionDone( completions ):
  vimsupport.CurrentFiletypes = MagicMock( return_value = [ "cs" ] )
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
