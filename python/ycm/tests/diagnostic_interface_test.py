# Copyright (C) 2015-2018 YouCompleteMe contributors
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
from ycm import diagnostic_interface
from ycm.tests.test_utils import VimBuffer, MockVimModule
from hamcrest import assert_that, contains_exactly, has_entries, has_item
from unittest.mock import patch
from unittest import TestCase
MockVimModule()


def SimpleDiagnosticToJson( start_line, start_col, end_line, end_col ):
  return {
    'kind': 'ERROR',
    'location': { 'line_num': start_line, 'column_num': start_col },
    'location_extent': {
      'start': {
        'line_num': start_line,
        'column_num': start_col
      },
      'end': {
        'line_num': end_line,
        'column_num': end_col
      }
    },
    'ranges': [
      {
        'start': {
          'line_num': start_line,
          'column_num': start_col
        },
        'end': {
          'line_num': end_line,
          'column_num': end_col
        }
      }
    ]
  }


def YcmTextPropertyTupleMatcher( start_line, start_col, end_line, end_col ):
  return has_item( contains_exactly(
    start_line,
    start_col,
    'YcmErrorProperty',
    has_entries( { 'end_col': end_col, 'end_lnum': end_line } ) ) )


class DiagnosticInterfaceTest( TestCase ):
  def test_ConvertDiagnosticToTextProperties( self ):
    for diag, contents, result in [
      # Error in middle of the line
      [
        SimpleDiagnosticToJson( 1, 16, 1, 23 ),
        [ 'Highlight this error please' ],
        YcmTextPropertyTupleMatcher( 1, 16, 1, 23 )
      ],
      # Error at the end of the line
      [
        SimpleDiagnosticToJson( 1, 16, 1, 21 ),
        [ 'Highlight this warning' ],
        YcmTextPropertyTupleMatcher( 1, 16, 1, 21 )
      ],
      [
        SimpleDiagnosticToJson( 1, 16, 1, 19 ),
        [ 'Highlight unicøde' ],
        YcmTextPropertyTupleMatcher( 1, 16, 1, 19 )
      ],
      # Non-positive position
      [
        SimpleDiagnosticToJson( 0, 0, 0, 0 ),
        [ 'Some contents' ],
        YcmTextPropertyTupleMatcher( 1, 1, 1, 1 )
      ],
      [
        SimpleDiagnosticToJson( -1, -2, -3, -4 ),
        [ 'Some contents' ],
        YcmTextPropertyTupleMatcher( 1, 1, 1, 1 )
      ],
    ]:
      with self.subTest( diag = diag, contents = contents, result = result ):
        current_buffer = VimBuffer( 'some_file', contents = contents )

        with patch( 'vim.current.buffer', current_buffer ):
          actual = diagnostic_interface._ConvertDiagnosticToTextProperties(
                                          diag )
          print( actual )
          assert_that( actual, result )
