# Copyright (C) 2016 YouCompleteMe contributors
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

from ycm.tests.test_utils import ( CurrentWorkingDirectory, ExtendedMock,
                                   MockVimModule, MockVimBuffers, VimBuffer )
MockVimModule()

import contextlib
from hamcrest import ( assert_that,
                       contains_exactly,
                       empty,
                       equal_to,
                       has_entries )
from unittest import TestCase
from unittest.mock import call, MagicMock, patch

from ycm.tests import PathToTestFile, YouCompleteMeInstance
from ycmd.responses import ServerError

import json


@contextlib.contextmanager
def MockCompletionRequest( response_method ):
  """Mock out the CompletionRequest, replacing the response handler
  JsonFromFuture with the |response_method| parameter."""

  # We don't want the requests to actually be sent to the server, just have it
  # return success.
  with patch( 'ycm.client.completer_available_request.'
              'CompleterAvailableRequest.PostDataToHandler',
              return_value = True ):
    with patch( 'ycm.client.completion_request.CompletionRequest.'
                'PostDataToHandlerAsync',
                return_value = MagicMock( return_value=True ) ):

      # We set up a fake response.
      with patch( 'ycm.client.base_request._JsonFromFuture',
                  side_effect = response_method ):
        yield


@contextlib.contextmanager
def MockResolveRequest( response_method ):
  """Mock out the CompletionRequest, replacing the response handler
  JsonFromFuture with the |response_method| parameter."""

  with patch( 'ycm.client.resolve_completion_request.ResolveCompletionRequest.'
              'PostDataToHandlerAsync',
              return_value = MagicMock( return_value=True ) ):

    # We set up a fake response.
    with patch( 'ycm.client.base_request._JsonFromFuture',
                side_effect = response_method ):
      yield


class CompletionTest( TestCase ):
  @YouCompleteMeInstance()
  def test_SendCompletionRequest_UnicodeWorkingDirectory( self, ycm ):
    unicode_dir = PathToTestFile( 'uni¢od€' )
    current_buffer = VimBuffer( PathToTestFile( 'uni¢𐍈d€', 'current_buffer' ) )

    def ServerResponse( *args ):
      return { 'completions': [], 'completion_start_column': 1 }

    with CurrentWorkingDirectory( unicode_dir ):
      with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
        with MockCompletionRequest( ServerResponse ):
          ycm.SendCompletionRequest()
          assert_that( ycm.CompletionRequestReady() )
          assert_that(
            ycm.GetCompletionResponse(),
            has_entries( {
              'completions': empty(),
              'completion_start_column': 1
            } )
          )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_SendCompletionRequest_ResponseContainingError(
      self, ycm, post_vim_message ):
    current_buffer = VimBuffer( 'buffer' )

    def ServerResponse( *args ):
      return {
        'completions': [ {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
             'doc_string': 'doc_string'
          }
        } ],
        'completion_start_column': 3,
        'errors': [ {
          'exception': {
             'TYPE': 'Exception'
          },
          'message': 'message',
          'traceback': 'traceback'
        } ]
      }

    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( ServerResponse ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()
        post_vim_message.assert_has_exact_calls( [
          call( 'Exception: message', truncate = True )
        ] )
        assert_that(
          response,
          has_entries( {
            'completions': contains_exactly( has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } ) ),
            'completion_start_column': 3
          } )
        )


  @YouCompleteMeInstance()
  @patch( 'ycm.client.base_request._logger', autospec = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_SendCompletionRequest_ErrorFromServer( self,
                                                  ycm,
                                                  post_vim_message,
                                                  logger ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( ServerError( 'Server error' ) ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()
        logger.exception.assert_called_with( 'Error while handling server '
                                             'response' )
        post_vim_message.assert_has_exact_calls( [
          call( 'Server error', truncate = True )
        ] )
        assert_that(
          response,
          has_entries( {
            'completions': empty(),
            'completion_start_column': -1
          } )
        )



  @YouCompleteMeInstance()
  @patch( 'ycm.client.base_request._logger', autospec = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_ResolveCompletionRequest_Resolves( self,
                                              ycm,
                                              post_vim_message,
                                              logger ):

    def CompletionResponse( *args ):
      return {
        'completions': [ {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
            'doc_string': 'doc_string',
            'resolve': 10
          }
        } ],
        'completion_start_column': 3,
        'errors': []
      }

    def ResolveResponse( *args ):
      return {
        'completion': {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
            'doc_string': 'doc_string with more info'
          }
        },
        'errors': []
      }

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( CompletionResponse ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        post_vim_message.assert_not_called()
        assert_that(
          response,
          has_entries( {
            'completions': contains_exactly( has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } ) ),
            'completion_start_column': 3
          } )
        )

        item = response[ 'completions' ][ 0 ]
        assert_that( json.loads( item[ 'user_data' ] ),
                     has_entries( { 'resolve': 10 } ) )

      with MockResolveRequest( ResolveResponse ):
        assert_that( ycm.ResolveCompletionItem( item ), equal_to( True ) )
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()
        post_vim_message.assert_not_called()

        assert_that(
          response,
          has_entries( {
            'completion': has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string with more info',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } )
          } )
        )

        item = response[ 'completion' ]

      with MockResolveRequest( ServerError( 'must not be called' ) ):
        assert_that( ycm.ResolveCompletionItem( item ), equal_to( False ) )
        post_vim_message.assert_not_called()


  @YouCompleteMeInstance()
  @patch( 'ycm.client.base_request._logger', autospec = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_ResolveCompletionRequest_ResponseContainsErrors( self,
                                                            ycm,
                                                            post_vim_message,
                                                            logger ):

    def CompletionResponse( *args ):
      return {
        'completions': [ {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
            'doc_string': 'doc_string',
            'resolve': 10
          }
        } ],
        'completion_start_column': 3,
        'errors': []
      }

    def ResolveResponse( *args ):
      return {
        'completion': {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
            'doc_string': 'doc_string with more info'
          }
        },
        'errors': [ {
          'exception': {
             'TYPE': 'Exception'
          },
          'message': 'message',
          'traceback': 'traceback'
        } ]
      }

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( CompletionResponse ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        post_vim_message.assert_not_called()
        assert_that(
          response,
          has_entries( {
            'completions': contains_exactly( has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } ) ),
            'completion_start_column': 3
          } )
        )

        item = response[ 'completions' ][ 0 ]
        assert_that( json.loads( item[ 'user_data' ] ),
                     has_entries( { 'resolve': 10 } ) )

      with MockResolveRequest( ResolveResponse ):
        assert_that( ycm.ResolveCompletionItem( item ), equal_to( True ) )
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        post_vim_message.assert_has_exact_calls( [
          call( 'Exception: message', truncate = True )
        ] )
        assert_that(
          response,
          has_entries( {
            'completion': has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string with more info',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } )
          } )
        )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_ResolveCompletionItem_NoUserData( self, ycm, post_vim_message ):
    def CompletionResponse( *args ):
      return {
        'completions': [ {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind'
        } ],
        'completion_start_column': 3,
        'errors': []
      }

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( CompletionResponse ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        post_vim_message.assert_not_called()
        assert_that(
          response,
          has_entries( {
            'completions': contains_exactly( has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } ) ),
            'completion_start_column': 3
          } )
        )

        item = response[ 'completions' ][ 0 ]
        item.pop( 'user_data' )

      with MockResolveRequest( ServerError( 'must not be called' ) ):
        assert_that( ycm.ResolveCompletionItem( item ), equal_to( False ) )
        post_vim_message.assert_not_called()


  @YouCompleteMeInstance()
  def test_ResolveCompletionItem_NoRequest( self, ycm ):
    assert_that( ycm.GetCurrentCompletionRequest(), equal_to( None ) )
    assert_that( ycm.ResolveCompletionItem( {} ), equal_to( False ) )


  @YouCompleteMeInstance()
  @patch( 'ycm.client.base_request._logger', autospec = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_ResolveCompletionRequest_ServerError(
      self, ycm, post_vim_message, logger ):

    def ServerResponse( *args ):
      return {
        'completions': [ {
          'insertion_text': 'insertion_text',
          'menu_text': 'menu_text',
          'extra_menu_info': 'extra_menu_info',
          'detailed_info': 'detailed_info',
          'kind': 'kind',
          'extra_data': {
            'doc_string': 'doc_string',
            'resolve': 10
          }
        } ],
        'completion_start_column': 3,
        'errors': []
      }

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with MockCompletionRequest( ServerResponse ):
        ycm.SendCompletionRequest()
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        post_vim_message.assert_not_called()
        assert_that(
          response,
          has_entries( {
            'completions': contains_exactly( has_entries( {
              'word': 'insertion_text',
              'abbr': 'menu_text',
              'menu': 'extra_menu_info',
              'info': 'detailed_info\ndoc_string',
              'kind': 'k',
              'dup': 1,
              'empty': 1
            } ) ),
            'completion_start_column': 3
          } )
        )

        item = response[ 'completions' ][ 0 ]
        assert_that( json.loads( item[ 'user_data' ] ),
                     has_entries( { 'resolve': 10 } ) )

      with MockResolveRequest( ServerError( 'Server error' ) ):
        ycm.ResolveCompletionItem( item )
        assert_that( ycm.CompletionRequestReady() )
        response = ycm.GetCompletionResponse()

        logger.exception.assert_called_with( 'Error while handling server '
                                             'response' )
        post_vim_message.assert_has_exact_calls( [
          call( 'Server error', truncate = True )
        ] )
