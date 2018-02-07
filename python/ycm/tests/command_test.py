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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.tests.test_utils import ( MockVimEval, MockVimModule, MockVimBuffers,
                                   VimBuffer )
MockVimModule()

from hamcrest import assert_that, equal_to
from mock import patch

from ycm.tests import YouCompleteMeInstance


@YouCompleteMeInstance( { 'extra_conf_vim_data': [ 'tempname()' ] } )
def SendCommandRequest_ExtraConfVimData_test( ycm ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
      ycm.SendCommandRequest( [ 'GoTo' ], 'python', False )
      send_request.assert_called_once_with(
        [ 'GoTo' ],
        'python',
        {
          'options': {
            'tab_size': 4,
            'insert_spaces': True
          },
          'extra_conf_data': {
            'tempname()': '_TEMP_FILE_'
          }
        }
      )
    with patch( 'ycm.client.base_request.JsonFromFuture',
                return_value = 'Some response' ):
      assert_that(
        ycm.SendCommandRequest( [ 'GoTo' ], 'python', False ),
        equal_to( 'Some response' )
      )


def MockVimEvalVisualPosition( value ):
  # getpos returns a list containing the buffer number, the 1-based line, the
  # 1-based column, and the offset.
  if value == 'getpos( "\'<" )':
    return [ 0, 1,  1, 0 ]
  if value == 'getpos( "\'>" )':
    # Vim returns the maximum 32-bit integer value as the column when the whole
    # line is visually selected.
    return [ 0, 2, 2147483647, 0 ]
  return MockVimEval( value )


@patch( 'vim.eval', side_effect = MockVimEvalVisualPosition )
@YouCompleteMeInstance()
def SendCommandRequest_VisualMode_test( ycm, *args ):
  current_buffer = VimBuffer( 'buffer', contents = [ 'first line',
                                                     'second line' ] )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
      ycm.SendCommandRequest( [ 'GoTo' ], 'python', True )
      send_request.assert_called_once_with(
        [ 'GoTo' ],
        'python',
        {
          'options': {
            'tab_size': 4,
            'insert_spaces': True
          },
          'range': {
            'start': {
              'line_num': 1,
              'column_num': 1
            },
            'end': {
              'line_num': 2,
              'column_num': 12
            }
          }
        }
      )
    with patch( 'ycm.client.base_request.JsonFromFuture',
                return_value = 'Some response' ):
      assert_that(
        ycm.SendCommandRequest( [ 'GoTo' ], 'python', True ),
        equal_to( 'Some response' )
      )
