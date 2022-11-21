# Copyright (C) 2016-2018 YouCompleteMe contributors
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

from ycm.tests.test_utils import MockVimModule, MockVimBuffers, VimBuffer
MockVimModule()

from hamcrest import assert_that, contains_exactly, has_entries
from unittest.mock import patch
from unittest import TestCase

from ycm.tests import YouCompleteMeInstance


class CommandTest( TestCase ):
  @YouCompleteMeInstance( { 'g:ycm_extra_conf_vim_data': [ 'tempname()' ] } )
  def test_SendCommandRequest_ExtraConfVimData_Works( self, ycm ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'GoTo' ], 'aboveleft', False, 1, 1 )
        assert_that(
          # Positional arguments passed to SendCommandRequest.
          send_request.call_args[ 0 ],
          contains_exactly(
            contains_exactly( 'GoTo' ),
            'aboveleft',
            'same-buffer',
            has_entries( {
              'options': has_entries( {
                'tab_size': 2,
                'insert_spaces': True,
              } ),
              'extra_conf_data': has_entries( {
                'tempname()': '_TEMP_FILE_'
              } ),
            } )
          )
        )


  @YouCompleteMeInstance( {
    'g:ycm_extra_conf_vim_data': [ 'undefined_value' ] } )
  def test_SendCommandRequest_ExtraConfData_UndefinedValue( self, ycm ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'GoTo' ], 'belowright', False, 1, 1 )
        assert_that(
          # Positional arguments passed to SendCommandRequest.
          send_request.call_args[ 0 ],
          contains_exactly(
            contains_exactly( 'GoTo' ),
            'belowright',
            'same-buffer',
            has_entries( {
              'options': has_entries( {
                'tab_size': 2,
                'insert_spaces': True,
              } )
            } )
          )
        )


  @YouCompleteMeInstance()
  def test_SendCommandRequest_BuildRange_NoVisualMarks( self, ycm, *args ):
    current_buffer = VimBuffer( 'buffer', contents = [ 'first line',
                                                       'second line' ] )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'GoTo' ], '', True, 1, 2 )
        send_request.assert_called_once_with(
          [ 'GoTo' ],
          '',
          'same-buffer',
          {
            'options': {
              'tab_size': 2,
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


  @YouCompleteMeInstance()
  def test_SendCommandRequest_BuildRange_VisualMarks( self, ycm, *args ):
    current_buffer = VimBuffer( 'buffer',
                                contents = [ 'first line',
                                             'second line' ],
                                visual_start = [ 1, 4 ],
                                visual_end = [ 2, 8 ] )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'GoTo' ], 'tab', True, 1, 2 )
        send_request.assert_called_once_with(
          [ 'GoTo' ],
          'tab',
          'same-buffer',
          {
            'options': {
              'tab_size': 2,
              'insert_spaces': True
            },
            'range': {
              'start': {
                'line_num': 1,
                'column_num': 5
              },
              'end': {
                'line_num': 2,
                'column_num': 9
              }
            }
          }
        )


  @YouCompleteMeInstance()
  def test_SendCommandRequest_IgnoreFileTypeOption( self, ycm, *args ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      expected_args = (
        [ 'GoTo' ],
        '',
        'same-buffer',
        {
          'completer_target': 'python',
          'options': {
            'tab_size': 2,
            'insert_spaces': True
          },
        }
      )

      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'ft=python', 'GoTo' ], '', False, 1, 1 )
        send_request.assert_called_once_with( *expected_args )

      with patch( 'ycm.youcompleteme.SendCommandRequest' ) as send_request:
        ycm.SendCommandRequest( [ 'GoTo', 'ft=python' ], '', False, 1, 1 )
        send_request.assert_called_once_with( *expected_args )
