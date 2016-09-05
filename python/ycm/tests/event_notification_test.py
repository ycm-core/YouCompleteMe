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

from ycm.test_utils import MockVimModule, ExtendedMock
MockVimModule()

import contextlib
import os

from ycm.tests.server_test import Server_test
from ycmd.responses import ( BuildDiagnosticData, Diagnostic, Location, Range,
                             UnknownExtraConf, ServerError )

from mock import call, MagicMock, patch
from nose.tools import eq_, ok_


def PresentDialog_Confirm_Call( message ):
  """Return a mock.call object for a call to vimsupport.PresentDialog, as called
  why vimsupport.Confirm with the supplied confirmation message"""
  return call( message, [ 'Ok', 'Cancel' ] )


def PlaceSign_Call( sign_id, line_num, buffer_num, is_error ):
  sign_name = 'YcmError' if is_error else 'YcmWarning'
  return call( 'sign place {0} line={1} name={2} buffer={3}'
                  .format( sign_id, line_num, sign_name, buffer_num ) )


def UnplaceSign_Call( sign_id, buffer_num ):
  return call( 'try | exec "sign unplace {0} buffer={1}" |'
               ' catch /E158/ | endtry'.format( sign_id, buffer_num ) )


@contextlib.contextmanager
def MockArbitraryBuffer( filetype, native_available = True ):
  """Used via the with statement, set up mocked versions of the vim module such
  that a single buffer is open with an arbitrary name and arbirary contents. Its
  filetype is set to the supplied filetype"""
  with patch( 'vim.current' ) as vim_current:
    def VimEval( value ):
      """Local mock of the vim.eval() function, used to ensure we get the
      correct behvaiour"""

      if value == '&omnifunc':
        # The omnicompleter is not required here
        return ''

      if value == 'getbufvar(0, "&mod")':
        # Ensure that we actually send the even to the server
        return 1

      if value == 'getbufvar(0, "&ft")' or value == '&filetype':
        return filetype

      if value.startswith( 'bufnr(' ):
        return 0

      if value.startswith( 'bufwinnr(' ):
        return 0

      raise ValueError( 'Unexpected evaluation' )

    # Arbitrary, but valid, cursor position
    vim_current.window.cursor = ( 1, 2 )

    # Arbitrary, but valid, single buffer open
    current_buffer = MagicMock()
    current_buffer.number = 0
    current_buffer.filename = os.path.realpath( 'TEST_BUFFER' )
    current_buffer.name = 'TEST_BUFFER'
    current_buffer.window = 0

    # The rest just mock up the Vim module so that our single arbitrary buffer
    # makes sense to vimsupport module.
    with patch( 'vim.buffers', [ current_buffer ] ):
      with patch( 'vim.current.buffer', current_buffer ):
        with patch( 'vim.eval', side_effect=VimEval ):
          yield


@contextlib.contextmanager
def MockEventNotification( response_method, native_filetype_completer = True ):
  """Mock out the EventNotification client request object, replacing the
  Response handler's JsonFromFuture with the supplied |response_method|.
  Additionally mock out YouCompleteMe's FiletypeCompleterExistsForFiletype
  method to return the supplied |native_filetype_completer| parameter, rather
  than querying the server"""

  # We don't want the event to actually be sent to the server, just have it
  # return success
  with patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync',
              return_value = MagicMock( return_value=True ) ):

    # We set up a fake a Response (as called by EventNotification.Response)
    # which calls the supplied callback method. Generally this callback just
    # raises an apropriate exception, otherwise it would have to return a mock
    # future object.
    #
    # Note: JsonFromFuture is actually part of ycm.client.base_request, but we
    # must patch where an object is looked up, not where it is defined.
    # See https://docs.python.org/dev/library/unittest.mock.html#where-to-patch
    # for details.
    with patch( 'ycm.client.event_notification.JsonFromFuture',
                side_effect = response_method ):

      # Filetype available information comes from the server, so rather than
      # relying on that request, we mock out the check. The caller decides if
      # filetype completion is available
      with patch(
        'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = native_filetype_completer ):

        yield


class EventNotification_test( Server_test ):

  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def FileReadyToParse_NonDiagnostic_Error_test( self, post_vim_message ):
    # This test validates the behaviour of YouCompleteMe.HandleFileParseRequest
    # in combination with YouCompleteMe.OnFileReadyToParse when the completer
    # raises an exception handling FileReadyToParse event notification
    ERROR_TEXT = 'Some completer response text'

    def ErrorResponse( *args ):
      raise ServerError( ERROR_TEXT )

    with MockArbitraryBuffer( 'javascript' ):
      with MockEventNotification( ErrorResponse ):
        self._server_state.OnFileReadyToParse()
        assert self._server_state.FileParseRequestReady()
        self._server_state.HandleFileParseRequest()

        # The first call raises a warning
        post_vim_message.assert_has_exact_calls( [
          call( ERROR_TEXT, truncate = False )
        ] )

        # Subsequent calls don't re-raise the warning
        self._server_state.HandleFileParseRequest()
        post_vim_message.assert_has_exact_calls( [
          call( ERROR_TEXT, truncate = False )
        ] )

        # But it does if a subsequent event raises again
        self._server_state.OnFileReadyToParse()
        assert self._server_state.FileParseRequestReady()
        self._server_state.HandleFileParseRequest()
        post_vim_message.assert_has_exact_calls( [
          call( ERROR_TEXT, truncate = False ),
          call( ERROR_TEXT, truncate = False )
        ] )


  @patch( 'vim.command' )
  def FileReadyToParse_NonDiagnostic_Error_NonNative_test( self, vim_command ):
    with MockArbitraryBuffer( 'javascript' ):
      with MockEventNotification( None, False ):
        self._server_state.OnFileReadyToParse()
        self._server_state.HandleFileParseRequest()
        vim_command.assert_not_called()


  @patch( 'ycm.client.event_notification._LoadExtraConfFile',
          new_callable = ExtendedMock )
  @patch( 'ycm.client.event_notification._IgnoreExtraConfFile',
          new_callable = ExtendedMock )
  def FileReadyToParse_NonDiagnostic_ConfirmExtraConf_test(
      self,
      ignore_extra_conf,
      load_extra_conf,
      *args ):

    # This test validates the behaviour of YouCompleteMe.HandleFileParseRequest
    # in combination with YouCompleteMe.OnFileReadyToParse when the completer
    # raises the (special) UnknownExtraConf exception

    FILE_NAME = 'a_file'
    MESSAGE = ( 'Found ' + FILE_NAME + '. Load? \n\n(Question can be '
                'turned off with options, see YCM docs)' )

    def UnknownExtraConfResponse( *args ):
      raise UnknownExtraConf( FILE_NAME )

    with MockArbitraryBuffer( 'javascript' ):
      with MockEventNotification( UnknownExtraConfResponse ):

        # When the user accepts the extra conf, we load it
        with patch( 'ycm.vimsupport.PresentDialog',
                    return_value = 0,
                    new_callable = ExtendedMock ) as present_dialog:
          self._server_state.OnFileReadyToParse()
          assert self._server_state.FileParseRequestReady()
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          load_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
          ] )

          # Subsequent calls don't re-raise the warning
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE )
          ] )
          load_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
          ] )

          # But it does if a subsequent event raises again
          self._server_state.OnFileReadyToParse()
          assert self._server_state.FileParseRequestReady()
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          load_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
            call( FILE_NAME ),
          ] )

        # When the user rejects the extra conf, we reject it
        with patch( 'ycm.vimsupport.PresentDialog',
                    return_value = 1,
                    new_callable = ExtendedMock ) as present_dialog:
          self._server_state.OnFileReadyToParse()
          assert self._server_state.FileParseRequestReady()
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          ignore_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
          ] )

          # Subsequent calls don't re-raise the warning
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE )
          ] )
          ignore_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
          ] )

          # But it does if a subsequent event raises again
          self._server_state.OnFileReadyToParse()
          assert self._server_state.FileParseRequestReady()
          self._server_state.HandleFileParseRequest()

          present_dialog.assert_has_exact_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          ignore_extra_conf.assert_has_exact_calls( [
            call( FILE_NAME ),
            call( FILE_NAME ),
          ] )


  def FileReadyToParse_Diagnostic_Error_Native_test( self ):
    self._Check_FileReadyToParse_Diagnostic_Error()
    self._Check_FileReadyToParse_Diagnostic_Warning()
    self._Check_FileReadyToParse_Diagnostic_Clean()


  @patch( 'vim.command' )
  def _Check_FileReadyToParse_Diagnostic_Error( self, vim_command ):
    # Tests Vim sign placement and error/warning count python API
    # when one error is returned.
    def DiagnosticResponse( *args ):
      start = Location( 1, 2, 'TEST_BUFFER' )
      end = Location( 1, 4, 'TEST_BUFFER' )
      extent = Range( start, end )
      diagnostic = Diagnostic( [], start, extent, 'expected ;', 'ERROR' )
      return [ BuildDiagnosticData( diagnostic ) ]

    with MockArbitraryBuffer( 'cpp' ):
      with MockEventNotification( DiagnosticResponse ):
        self._server_state.OnFileReadyToParse()
        ok_( self._server_state.FileParseRequestReady() )
        self._server_state.HandleFileParseRequest()
        vim_command.assert_has_calls( [
          PlaceSign_Call( 1, 1, 0, True )
        ] )
        eq_( self._server_state.GetErrorCount(), 1 )
        eq_( self._server_state.GetWarningCount(), 0 )

        # Consequent calls to HandleFileParseRequest shouldn't mess with
        # existing diagnostics, when there is no new parse request.
        vim_command.reset_mock()
        ok_( not self._server_state.FileParseRequestReady() )
        self._server_state.HandleFileParseRequest()
        vim_command.assert_not_called()
        eq_( self._server_state.GetErrorCount(), 1 )
        eq_( self._server_state.GetWarningCount(), 0 )


  @patch( 'vim.command' )
  def _Check_FileReadyToParse_Diagnostic_Warning( self, vim_command ):
    # Tests Vim sign placement/unplacement and error/warning count python API
    # when one warning is returned.
    # Should be called after _Check_FileReadyToParse_Diagnostic_Error
    def DiagnosticResponse( *args ):
      start = Location( 2, 2, 'TEST_BUFFER' )
      end = Location( 2, 4, 'TEST_BUFFER' )
      extent = Range( start, end )
      diagnostic = Diagnostic( [], start, extent, 'cast', 'WARNING' )
      return [ BuildDiagnosticData( diagnostic ) ]

    with MockArbitraryBuffer( 'cpp' ):
      with MockEventNotification( DiagnosticResponse ):
        self._server_state.OnFileReadyToParse()
        ok_( self._server_state.FileParseRequestReady() )
        self._server_state.HandleFileParseRequest()
        vim_command.assert_has_calls( [
          PlaceSign_Call( 2, 2, 0, False ),
          UnplaceSign_Call( 1, 0 )
        ] )
        eq_( self._server_state.GetErrorCount(), 0 )
        eq_( self._server_state.GetWarningCount(), 1 )

        # Consequent calls to HandleFileParseRequest shouldn't mess with
        # existing diagnostics, when there is no new parse request.
        vim_command.reset_mock()
        ok_( not self._server_state.FileParseRequestReady() )
        self._server_state.HandleFileParseRequest()
        vim_command.assert_not_called()
        eq_( self._server_state.GetErrorCount(), 0 )
        eq_( self._server_state.GetWarningCount(), 1 )


  @patch( 'vim.command' )
  def _Check_FileReadyToParse_Diagnostic_Clean( self, vim_command ):
    # Tests Vim sign unplacement and error/warning count python API
    # when there are no errors/warnings left.
    # Should be called after _Check_FileReadyToParse_Diagnostic_Warning
    with MockArbitraryBuffer( 'cpp' ):
      with MockEventNotification( MagicMock( return_value = [] ) ):
        self._server_state.OnFileReadyToParse()
        self._server_state.HandleFileParseRequest()
        vim_command.assert_has_calls( [
          UnplaceSign_Call( 2, 0 )
        ] )
        eq_( self._server_state.GetErrorCount(), 0 )
        eq_( self._server_state.GetWarningCount(), 0 )
