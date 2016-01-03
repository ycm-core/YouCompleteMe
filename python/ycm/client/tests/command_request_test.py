#
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

from ycm.test_utils import MockVimModule
MockVimModule()

from mock import patch, call
from ycm.client.command_request import CommandRequest


class GoToResponse_QuickFix_test:
  """This class tests the generation of QuickFix lists for GoTo responses which
  return multiple locations, such as the Python completer and JavaScript
  completer. It mostly proves that we use 1-based indexing for the column
  number."""

  def setUp( self ):
    self._request = CommandRequest( [ 'GoToTest' ] )


  def tearDown( self ):
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


  @patch( 'vim.eval' )
  def _CheckGoToList( self, completer_response, expected_qf_list, vim_eval ):
    self._request._response = completer_response

    self._request.RunPostCommandActionsIfNeeded()

    vim_eval.assert_has_calls( [
      call( 'setqflist( {0} )'.format( repr( expected_qf_list ) ) ),
      call( 'youcompleteme#OpenGoToList()' ),
    ] )
