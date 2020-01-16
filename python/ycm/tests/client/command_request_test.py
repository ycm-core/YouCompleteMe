# Copyright (C) 2016 YouCompleteMe Contributors
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

from ycm.tests.test_utils import ExtendedMock, MockVimModule
MockVimModule()

import json
import pytest
from hamcrest import assert_that
from unittest.mock import patch, call
from ycm.client.command_request import CommandRequest


def GoToTest( command, response ):
  with patch( 'ycm.vimsupport.JumpToLocation' ) as jump_to_location:
    request = CommandRequest( [ command ] )
    request._response = response
    request.RunPostCommandActionsIfNeeded( 'rightbelow' )
    jump_to_location.assert_called_with(
        response[ 'filepath' ],
        response[ 'line_num' ],
        response[ 'column_num' ],
        'rightbelow',
        'same-buffer' )


def GoToListTest( command, response ):
  # Note: the detail of these called are tested by
  # GoToResponse_QuickFix_test, so here we just check that the right call is
  # made
  with patch( 'ycm.vimsupport.SetQuickFixList' ) as set_qf_list:
    with patch( 'ycm.vimsupport.OpenQuickFixList' ) as open_qf_list:
      request = CommandRequest( [ command ] )
      request._response = response
      request.RunPostCommandActionsIfNeeded( 'tab' )
      assert_that( set_qf_list.called )
      assert_that( open_qf_list.called )


BASIC_GOTO = {
  'filepath': 'test',
  'line_num': 10,
  'column_num': 100,
}


BASIC_FIXIT = {
  'fixits': [ {
    'resolve': False,
    'chunks': [ {
      'dummy chunk contents': True
    } ]
  } ]
}
BASIC_FIXIT_CHUNKS = BASIC_FIXIT[ 'fixits' ][ 0 ][ 'chunks' ]

MULTI_FIXIT = {
  'fixits': [ {
    'text': 'first',
    'resolve': False,
    'chunks': [ {
      'dummy chunk contents': True
    } ]
  }, {
    'text': 'second',
    'resolve': False,
    'chunks': [ {
      'dummy chunk contents': False
    } ]
  } ]
}
MULTI_FIXIT_FIRST_CHUNKS = MULTI_FIXIT[ 'fixits' ][ 0 ][ 'chunks' ]
MULTI_FIXIT_SECOND_CHUNKS = MULTI_FIXIT[ 'fixits' ][ 1 ][ 'chunks' ]


class GoToResponse_QuickFix_test:
  """This class tests the generation of QuickFix lists for GoTo responses which
  return multiple locations, such as the Python completer and JavaScript
  completer. It mostly proves that we use 1-based indexing for the column
  number."""

  def setup_method( self ):
    self._request = CommandRequest( [ 'GoToTest' ] )


  def teardown_method( self ):
    self._request = None


  def GoTo_EmptyList_test( self ):
    self._CheckGoToList( [], [] )


  def GoTo_SingleItem_List_test( self ):
    self._CheckGoToList( [ {
      'filepath':     'dummy_file',
      'line_num':     10,
      'column_num':   1,
      'description': 'this is some text',
    } ], [ {
      'filename':    'dummy_file',
      'text':        'this is some text',
      'lnum':        10,
      'col':         1
    } ] )


  def GoTo_MultiItem_List_test( self ):
    self._CheckGoToList( [ {
      'filepath':     'dummy_file',
      'line_num':     10,
      'column_num':   1,
      'description': 'this is some other text',
    }, {
      'filepath':     'dummy_file2',
      'line_num':     1,
      'column_num':   21,
      'description': 'this is some text',
    } ], [ {
      'filename':    'dummy_file',
      'text':        'this is some other text',
      'lnum':        10,
      'col':         1
    }, {
      'filename':    'dummy_file2',
      'text':        'this is some text',
      'lnum':        1,
      'col':         21
    } ] )


  @patch( 'ycm.vimsupport.VariableExists', return_value = True )
  @patch( 'ycm.vimsupport.SetFittingHeightForCurrentWindow' )
  @patch( 'vim.command', new_callable = ExtendedMock )
  @patch( 'vim.eval', new_callable = ExtendedMock )
  def _CheckGoToList( self,
                      completer_response,
                      expected_qf_list,
                      vim_eval,
                      vim_command,
                      set_fitting_height,
                      variable_exists ):
    self._request._response = completer_response

    self._request.RunPostCommandActionsIfNeeded( 'aboveleft' )

    vim_eval.assert_has_exact_calls( [
      call( 'setqflist( {0} )'.format( json.dumps( expected_qf_list ) ) )
    ] )
    vim_command.assert_has_exact_calls( [
      call( 'botright copen' ),
      call( 'augroup ycmquickfix' ),
      call( 'autocmd! * <buffer>' ),
      call( 'autocmd WinLeave <buffer> '
            'if bufnr( "%" ) == expand( "<abuf>" ) | q | endif '
            '| autocmd! ycmquickfix' ),
      call( 'augroup END' ),
      call( 'doautocmd User YcmQuickFixOpened' )
    ] )
    set_fitting_height.assert_called_once_with()


class Response_Detection_test:

  @pytest.mark.parametrize( 'command,response', [
        [ 'AnythingYouLike',        True ],
        [ 'GoToEvenWorks',          10 ],
        [ 'FixItWorks',             'String!' ],
        [ 'and8434fd andy garbag!', 10.3 ],
  ] )
  def BasicResponse_test( self, command, response ):
    def _BasicResponseTest( command, response ):
      with patch( 'vim.command' ) as vim_command:
        request = CommandRequest( [ command ] )
        request._response = response
        request.RunPostCommandActionsIfNeeded( 'belowright' )
        vim_command.assert_called_with( "echo '{0}'".format( response ) )

    _BasicResponseTest( command, response )

  @pytest.mark.parametrize( 'command', [ 'FixIt',
                                         'Refactor',
                                         'GoToHell',
                                         'any_old_garbade!!!21' ] )
  def FixIt_Response_Empty_test( self, command ):
    # Ensures we recognise and handle fixit responses which indicate that there
    # are no fixits available
    def EmptyFixItTest( command ):
      with patch( 'ycm.vimsupport.ReplaceChunks' ) as replace_chunks:
        with patch( 'ycm.vimsupport.PostVimMessage' ) as post_vim_message:
          request = CommandRequest( [ command ] )
          request._response = {
            'fixits': []
          }
          request.RunPostCommandActionsIfNeeded( 'botright' )

          post_vim_message.assert_called_with(
            'No fixits found for current line', warning = False )
          replace_chunks.assert_not_called()

    EmptyFixItTest( command )



  @pytest.mark.parametrize( 'command,response,chunks,selection,silent', [
      [ 'AnythingYouLike',
        BASIC_FIXIT,  BASIC_FIXIT_CHUNKS,        0, False ],
      [ 'GoToEvenWorks',
        BASIC_FIXIT,  BASIC_FIXIT_CHUNKS,        0, False ],
      [ 'FixItWorks',
        BASIC_FIXIT,  BASIC_FIXIT_CHUNKS,        0, False ],
      [ 'and8434fd andy garbag!',
        BASIC_FIXIT,  BASIC_FIXIT_CHUNKS,        0, False ],
      [ 'Format',
        BASIC_FIXIT,  BASIC_FIXIT_CHUNKS,        0, True ],
      [ 'select from multiple 1',
        MULTI_FIXIT,  MULTI_FIXIT_FIRST_CHUNKS,  0, False ],
      [ 'select from multiple 2',
        MULTI_FIXIT,  MULTI_FIXIT_SECOND_CHUNKS, 1, False ],
    ] )
  def FixIt_Response_test( self, command, response, chunks, selection, silent ):
    # Ensures we recognise and handle fixit responses with some dummy chunk data
    def FixItTest( command, response, chunks, selection, silent ):
      with patch( 'ycm.vimsupport.ReplaceChunks' ) as replace_chunks:
        with patch( 'ycm.vimsupport.PostVimMessage' ) as post_vim_message:
          with patch( 'ycm.vimsupport.SelectFromList',
                      return_value = selection ):
            request = CommandRequest( [ command ] )
            request._response = response
            request.RunPostCommandActionsIfNeeded( 'leftabove' )

            replace_chunks.assert_called_with( chunks, silent = silent )
            post_vim_message.assert_not_called()


    FixItTest( command, response, chunks, selection, silent )


  @pytest.mark.parametrize( 'command,message', [
      [ '___________', 'This is a message' ],
      [ '',            'this is also a message' ],
      [ 'GetType',     'std::string' ],
    ] )
  def Message_Response_test( self, command, message ):
    # Ensures we correctly recognise and handle responses with a message to show
    # to the user

    def MessageTest( command, message ):
      with patch( 'ycm.vimsupport.PostVimMessage' ) as post_vim_message:
        request = CommandRequest( [ command ] )
        request._response = { 'message': message }
        request.RunPostCommandActionsIfNeeded( 'rightbelow' )
        post_vim_message.assert_called_with( message, warning = False )

    MessageTest( command, message )


  @pytest.mark.parametrize( 'command,info', [
      [ '___________', 'This is a message' ],
      [ '',            'this is also a message' ],
      [ 'GetDoc',      'std::string\netc\netc' ],
    ] )
  def Detailed_Info_test( self, command, info ):
    # Ensures we correctly detect and handle detailed_info responses which are
    # used to display information in the preview window

    def DetailedInfoTest( command, info ):
      with patch( 'ycm.vimsupport.WriteToPreviewWindow' ) as write_to_preview:
        request = CommandRequest( [ command ] )
        request._response = { 'detailed_info': info }
        request.RunPostCommandActionsIfNeeded( 'topleft' )
        write_to_preview.assert_called_with( info )

    DetailedInfoTest( command, info )


  @pytest.mark.parametrize( 'test,command,response', [
      [ GoToTest,     'AnythingYouLike', BASIC_GOTO ],
      [ GoToTest,     'GoTo',            BASIC_GOTO ],
      [ GoToTest,     'FindAThing',      BASIC_GOTO ],
      [ GoToTest,     'FixItGoto',       BASIC_GOTO ],
      [ GoToListTest, 'AnythingYouLike', [ BASIC_GOTO ] ],
      [ GoToListTest, 'GoTo',            [] ],
      [ GoToListTest, 'FixItGoto',       [ BASIC_GOTO, BASIC_GOTO ] ],
    ] )
  def GoTo_Single_test( self, test, command, response ):
    test( command, response )
