# coding: utf-8
#
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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycm.tests.test_utils import ( CurrentWorkingDirectory, ExtendedMock,
                                   MockVimModule, MockVimBuffers, VimBuffer )
MockVimModule()

from hamcrest import assert_that, contains, empty, has_entries
from mock import call, patch

from ycm.tests import PathToTestFile, YouCompleteMeInstance
from ycmd.responses import ServerError


@YouCompleteMeInstance()
def CreateCompletionRequest_UnicodeWorkingDirectory_test( ycm ):
  unicode_dir = PathToTestFile( 'uni¢𐍈d€' )
  current_buffer = VimBuffer( PathToTestFile( 'uni¢𐍈d€', 'current_buffer' ) )

  with CurrentWorkingDirectory( unicode_dir ):
    with MockVimBuffers( [ current_buffer ], current_buffer ):
      ycm.CreateCompletionRequest(),

    results = ycm.GetCompletions()

  assert_that(
    results,
    has_entries( {
      'words': empty(),
      'refresh': 'always'
    } )
  )


@YouCompleteMeInstance()
@patch( 'ycm.client.base_request._logger', autospec = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def CreateCompletionRequest_ResponseContainingError_test( ycm,
                                                          post_vim_message,
                                                          logger ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    ycm.CreateCompletionRequest(),

  response = {
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

  with patch( 'ycm.client.completion_request.JsonFromFuture',
              return_value = response ):
    results = ycm.GetCompletions()

  logger.exception.assert_called_with( 'Error while handling server response' )
  post_vim_message.assert_has_exact_calls( [
    call( 'Exception: message', truncate = True )
  ] )
  assert_that(
    results,
    has_entries( {
      'words': contains( has_entries( {
        'word': 'insertion_text',
        'abbr': 'menu_text',
        'menu': 'extra_menu_info',
        'info': 'detailed_info\ndoc_string',
        'kind': 'k',
        'dup': 1,
        'empty': 1
      } ) ),
      'refresh': 'always'
    } )
  )


@YouCompleteMeInstance()
@patch( 'ycm.client.base_request._logger', autospec = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def CreateCompletionRequest_ErrorFromServer_test( ycm,
                                                  post_vim_message,
                                                  logger ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    ycm.CreateCompletionRequest(),

  with patch( 'ycm.client.completion_request.JsonFromFuture',
              side_effect = ServerError( 'Server error' ) ):
    results = ycm.GetCompletions()

  logger.exception.assert_called_with( 'Error while handling server response' )
  post_vim_message.assert_has_exact_calls( [
    call( 'Server error', truncate = True )
  ] )
  assert_that(
    results,
    has_entries( {
      'words': empty(),
      'refresh': 'always'
    } )
  )
