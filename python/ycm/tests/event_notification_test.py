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

import contextlib, os

from ycm.youcompleteme import YouCompleteMe
from ycmd import user_options_store
from ycmd.responses import UnknownExtraConf

from mock import call, MagicMock, patch


# The default options which are only relevant to the client, not the server and
# thus are not part of default_options.json, but are required for a working
# YouCompleteMe object.
DEFAULT_CLIENT_OPTIONS = {
  'server_log_level': 'info',
  'extra_conf_vim_data': [],
}

def PostVimMessage_Call( message ):
  """Return a mock.call object for a call to vimsupport.PostVimMesasge with the
  supplied message"""
  return call( 'redraw | echohl WarningMsg | echom \''
               + message +
               '\' | echohl None' )


def PresentDialog_Confirm_Call( message ):
  """Return a mock.call object for a call to vimsupport.PresentDialog, as called
  why vimsupport.Confirm with the supplied confirmation message"""
  return call( message, [ 'Ok', 'Cancel' ] )


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

      raise ValueError( 'Unexpected evaluation' )

    # Arbitrary, but valid, cursor position
    vim_current.window.cursor = (1,2)

    # Arbitrary, but valid, single buffer open
    current_buffer = MagicMock()
    current_buffer.number = 0
    current_buffer.filename = os.path.realpath( 'TEST_BUFFER' )
    current_buffer.name = 'TEST_BUFFER'

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


class EventNotification_test( object ):

  def setUp( self ):
    options = dict( user_options_store.DefaultOptions() )
    options.update ( DEFAULT_CLIENT_OPTIONS )
    user_options_store.SetAll( options )

    self.server_state = YouCompleteMe( user_options_store.GetAll() )
    pass


  def tearDown( self ):
    if self.server_state:
      self.server_state.OnVimLeave()


  @patch( 'vim.command' )
  def FileReadyToParse_NonDiagnostic_Error_test( self, vim_command ):
    # This test validates the behaviour of YouCompleteMe.ValidateParseRequest in
    # combination with YouCompleteMe.OnFileReadyToParse when the completer
    # raises an exception handling FileReadyToParse event notification
    ERROR_TEXT = 'Some completer response text'

    def ErrorResponse( *args ):
      raise RuntimeError( ERROR_TEXT )

    with MockArbitraryBuffer( 'javascript' ):
      with MockEventNotification( ErrorResponse ):
        self.server_state.OnFileReadyToParse()
        assert self.server_state.DiagnosticsForCurrentFileReady()
        self.server_state.ValidateParseRequest()

        # The first call raises a warning
        vim_command.assert_has_calls( [
          PostVimMessage_Call( ERROR_TEXT ),
        ] )

        # Subsequent calls don't re-raise the warning
        self.server_state.ValidateParseRequest()
        vim_command.assert_has_calls( [
          PostVimMessage_Call( ERROR_TEXT ),
        ] )

        # But it does if a subsequent event raises again
        self.server_state.OnFileReadyToParse()
        assert self.server_state.DiagnosticsForCurrentFileReady()
        self.server_state.ValidateParseRequest()
        vim_command.assert_has_calls( [
          PostVimMessage_Call( ERROR_TEXT ),
          PostVimMessage_Call( ERROR_TEXT ),
        ] )


  @patch( 'vim.command' )
  def FileReadyToParse_NonDiagnostic_Error_NonNative_test( self, vim_command ):
    with MockArbitraryBuffer( 'javascript' ):
      with MockEventNotification( None, False ):
        self.server_state.OnFileReadyToParse()
        self.server_state.ValidateParseRequest()
        vim_command.assert_not_called()


  @patch( 'ycm.client.event_notification._LoadExtraConfFile' )
  @patch( 'ycm.client.event_notification._IgnoreExtraConfFile' )
  def FileReadyToParse_NonDiagnostic_ConfirmExtraConf_test(
      self,
      ignore_extra_conf,
      load_extra_conf,
      *args ):

    # This test validates the behaviour of YouCompleteMe.ValidateParseRequest in
    # combination with YouCompleteMe.OnFileReadyToParse when the completer
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
                    return_value = 0 ) as present_dialog:
          self.server_state.OnFileReadyToParse()
          assert self.server_state.DiagnosticsForCurrentFileReady()
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          load_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
          ] )

          # Subsequent calls don't re-raise the warning
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE )
          ] )
          load_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
          ] )

          # But it does if a subsequent event raises again
          self.server_state.OnFileReadyToParse()
          assert self.server_state.DiagnosticsForCurrentFileReady()
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          load_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
            call( FILE_NAME ),
          ] )

        # When the user rejects the extra conf, we reject it
        with patch( 'ycm.vimsupport.PresentDialog',
                    return_value = 1 ) as present_dialog:
          self.server_state.OnFileReadyToParse()
          assert self.server_state.DiagnosticsForCurrentFileReady()
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          ignore_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
          ] )

          # Subsequent calls don't re-raise the warning
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE )
          ] )
          ignore_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
          ] )

          # But it does if a subsequent event raises again
          self.server_state.OnFileReadyToParse()
          assert self.server_state.DiagnosticsForCurrentFileReady()
          self.server_state.ValidateParseRequest()

          present_dialog.assert_has_calls( [
            PresentDialog_Confirm_Call( MESSAGE ),
            PresentDialog_Confirm_Call( MESSAGE ),
          ] )
          ignore_extra_conf.assert_has_calls( [
            call( FILE_NAME ),
            call( FILE_NAME ),
          ] )
