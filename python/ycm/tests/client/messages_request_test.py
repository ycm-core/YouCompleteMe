# Copyright (C) 2017 YouCompleteMe Contributors
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

import json
from ycm.tests.test_utils import MockVimModule
MockVimModule()

from hamcrest import assert_that, equal_to
from unittest import TestCase
from unittest.mock import patch, call, MagicMock

from ycm.client.messages_request import _HandlePollResponse, MessagesPoll
from ycm.tests.test_utils import ExtendedMock, MockVimBuffers, VimBuffer


class MessagesRequestTest( TestCase ):
  def test_HandlePollResponse_NoMessages( self ):
    assert_that( _HandlePollResponse( True, None ), equal_to( True ) )

    # Other non-False responses mean the same thing
    assert_that( _HandlePollResponse( '', None ), equal_to( True ) )
    assert_that( _HandlePollResponse( 1, None ), equal_to( True ) )
    assert_that( _HandlePollResponse( {}, None ), equal_to( True ) )


  def test_HandlePollResponse_PollingNotSupported( self ):
    assert_that( _HandlePollResponse( False, None ), equal_to( False ) )

    # 0 is not False
    assert_that( _HandlePollResponse( 0, None ), equal_to( True ) )


  @patch( 'ycm.client.messages_request.PostVimMessage',
          new_callable = ExtendedMock )
  def test_HandlePollResponse_SingleMessage( self, post_vim_message ):
    assert_that( _HandlePollResponse( [ { 'message': 'this is a message' } ] ,
                                      None ),
                 equal_to( True ) )

    post_vim_message.assert_has_exact_calls( [
      call( 'this is a message', warning=False, truncate=True )
    ] )


  @patch( 'ycm.client.messages_request.PostVimMessage',
          new_callable = ExtendedMock )
  def test_HandlePollResponse_MultipleMessages( self, post_vim_message ):
    assert_that( _HandlePollResponse( [ { 'message': 'this is a message' },
                                        { 'message': 'this is another one' } ] ,
                                      None ),
                 equal_to( True ) )

    post_vim_message.assert_has_exact_calls( [
      call( 'this is a message', warning=False, truncate=True ),
      call( 'this is another one', warning=False, truncate=True )
    ] )


  def test_HandlePollResponse_SingleDiagnostic( self ):
    diagnostics_handler = ExtendedMock()
    messages = [
      { 'filepath': 'foo', 'diagnostics': [ 'PLACEHOLDER' ] },
    ]
    assert_that( _HandlePollResponse( messages, diagnostics_handler ),
                 equal_to( True ) )
    diagnostics_handler.UpdateWithNewDiagnosticsForFile.assert_has_exact_calls(
      [
        call( 'foo', [ 'PLACEHOLDER' ] )
      ] )


  def test_HandlePollResponse_MultipleDiagnostics( self ):
    diagnostics_handler = ExtendedMock()
    messages = [
      { 'filepath': 'foo', 'diagnostics': [ 'PLACEHOLDER1' ] },
      { 'filepath': 'bar', 'diagnostics': [ 'PLACEHOLDER2' ] },
      { 'filepath': 'baz', 'diagnostics': [ 'PLACEHOLDER3' ] },
      { 'filepath': 'foo', 'diagnostics': [ 'PLACEHOLDER4' ] },
    ]
    assert_that( _HandlePollResponse( messages, diagnostics_handler ),
                 equal_to( True ) )
    diagnostics_handler.UpdateWithNewDiagnosticsForFile.assert_has_exact_calls(
      [
        call( 'foo', [ 'PLACEHOLDER1' ] ),
        call( 'bar', [ 'PLACEHOLDER2' ] ),
        call( 'baz', [ 'PLACEHOLDER3' ] ),
        call( 'foo', [ 'PLACEHOLDER4' ] )
      ] )


  @patch( 'ycm.client.messages_request.PostVimMessage',
          new_callable = ExtendedMock )
  def test_HandlePollResponse_MultipleMessagesAndDiagnostics(
      self, post_vim_message ):
    diagnostics_handler = ExtendedMock()
    messages = [
      { 'filepath': 'foo', 'diagnostics': [ 'PLACEHOLDER1' ] },
      { 'message': 'On the first day of Christmas, my VimScript gave to me' },
      { 'filepath': 'bar', 'diagnostics': [ 'PLACEHOLDER2' ] },
      { 'message': 'A test file in a Command-T' },
      { 'filepath': 'baz', 'diagnostics': [ 'PLACEHOLDER3' ] },
      { 'message': 'On the second day of Christmas, my VimScript gave to me' },
      { 'filepath': 'foo', 'diagnostics': [ 'PLACEHOLDER4' ] },
      { 'message': 'Two popup menus, and a test file in a Command-T' },
    ]
    assert_that( _HandlePollResponse( messages, diagnostics_handler ),
                 equal_to( True ) )
    diagnostics_handler.UpdateWithNewDiagnosticsForFile.assert_has_exact_calls(
      [
        call( 'foo', [ 'PLACEHOLDER1' ] ),
        call( 'bar', [ 'PLACEHOLDER2' ] ),
        call( 'baz', [ 'PLACEHOLDER3' ] ),
        call( 'foo', [ 'PLACEHOLDER4' ] )
      ] )

    post_vim_message.assert_has_exact_calls( [
      call( 'On the first day of Christmas, my VimScript gave to me',
            warning=False,
            truncate=True ),
      call( 'A test file in a Command-T', warning=False, truncate=True ),
      call( 'On the second day of Christmas, my VimScript gave to me',
            warning=False,
            truncate=True ),
      call( 'Two popup menus, and a test file in a Command-T',
            warning=False,
            truncate=True ),
    ] )


  def test_Poll_FirstCall_StartsRequest( self ):
    test_buffer = VimBuffer( 'test_buffer', number = 1, contents = [ '' ] )

    with MockVimBuffers( [ test_buffer ], [ test_buffer ] ):
      poller = MessagesPoll( test_buffer )

      # Mock the async request method to avoid actual HTTP call
      mock_future = MagicMock()
      with patch.object( poller, 'PostDataToHandlerAsync',
                        return_value = mock_future ) as mock_post:
        # First poll should start request
        result = poller.Poll( None )

        assert_that( result, equal_to( True ) )
        mock_post.assert_called_once()


  def test_Poll_FutureNotDone_ReturnsTrue( self ):
    test_buffer = VimBuffer( 'test_buffer', number = 1, contents = [ '' ] )

    with MockVimBuffers( [ test_buffer ], [ test_buffer ] ):
      poller = MessagesPoll( test_buffer )

      # Mock future that is not done
      mock_future = MagicMock()
      mock_future.done.return_value = False
      poller._response_future = mock_future

      # Should return True without extracting result
      result = poller.Poll( None )

      assert_that( result, equal_to( True ) )
      mock_future.result.assert_not_called()


  def test_Poll_FutureReady_ExtractsResponseNonBlocking( self ):
    test_buffer = VimBuffer( 'test_buffer', number = 1, contents = [ '' ] )

    with MockVimBuffers( [ test_buffer ], [ test_buffer ] ):
      poller = MessagesPoll( test_buffer )

      # Mock completed future with response
      mock_response = MagicMock()
      mock_response.read.return_value = json.dumps(
          [ { 'message': 'test' } ] ).encode()
      mock_response.close = MagicMock()

      mock_future = MagicMock()
      mock_future.done.return_value = True
      mock_future.result.return_value = mock_response
      poller._response_future = mock_future

      # Mock diagnostics handler
      mock_handler = MagicMock()

      # Should extract result with timeout=0 (non-blocking)
      with patch( 'ycm.client.messages_request.PostVimMessage' ):
        result = poller.Poll( mock_handler )

      # Verify non-blocking extraction
      mock_future.result.assert_called_once_with( timeout = 0 )
      mock_response.read.assert_called_once()
      mock_response.close.assert_called_once()
      assert_that( result, equal_to( True ) )


  def test_Poll_FutureException_ReturnsFalse( self ):
    test_buffer = VimBuffer( 'test_buffer', number = 1, contents = [ '' ] )

    with MockVimBuffers( [ test_buffer ], [ test_buffer ] ):
      poller = MessagesPoll( test_buffer )

      # Mock future that raises exception
      mock_future = MagicMock()
      mock_future.done.return_value = True
      mock_future.result.side_effect = Exception( 'Connection error' )
      poller._response_future = mock_future

      # Should catch exception and return False
      result = poller.Poll( None )

      assert_that( result, equal_to( False ) )


  def test_Poll_DoesNotCallHandleFuture( self ):
    """Verify that Poll() does NOT call HandleFuture() to avoid blocking."""
    test_buffer = VimBuffer( 'test_buffer', number = 1, contents = [ '' ] )

    with MockVimBuffers( [ test_buffer ], [ test_buffer ] ):
      poller = MessagesPoll( test_buffer )

      # Mock completed future
      mock_response = MagicMock()
      mock_response.read.return_value = json.dumps( True ).encode()
      mock_response.close = MagicMock()

      mock_future = MagicMock()
      mock_future.done.return_value = True
      mock_future.result.return_value = mock_response
      poller._response_future = mock_future

      # Spy on HandleFuture to ensure it's NOT called
      with patch.object( poller, 'HandleFuture' ) as mock_handle_future:
        # Poll should not call HandleFuture
        poller.Poll( None )

        mock_handle_future.assert_not_called()
